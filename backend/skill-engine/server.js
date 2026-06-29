const express = require('express');
const fs = require('fs');
const path = require('path');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const app = express();

// Security: Enforce headers
app.use(helmet());

// Security: Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests, please try again later.'
});
app.use('/skills/', limiter);

app.use(express.json());

const registryPath = path.join(__dirname, 'registry');
const skillIndex = {};

// Load skills on startup
function loadSkills() {
    if (!fs.existsSync(registryPath)) {
        console.warn(`Registry path not found: ${registryPath}`);
        return;
    }

    const folders = fs.readdirSync(registryPath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);

    for (const folder of folders) {
        const skillDir = path.join(registryPath, folder);
        const jsonPath = path.join(skillDir, 'skill.json');

        if (fs.existsSync(jsonPath)) {
            try {
                const metadata = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
                // Validate required fields
                if (metadata.name && metadata.description && metadata.entrypoint) {
                    const entrypointPath = path.join(skillDir, metadata.entrypoint);
                    if (fs.existsSync(entrypointPath)) {
                        skillIndex[metadata.name] = {
                            metadata,
                            entrypointPath
                        };
                        console.log(`Loaded skill: ${metadata.name}`);
                    } else {
                        console.error(`Entrypoint not found for skill ${metadata.name}: ${entrypointPath}`);
                    }
                } else {
                    console.error(`Invalid metadata for skill in folder ${folder}`);
                }
            } catch (err) {
                console.error(`Error parsing skill.json for folder ${folder}:`, err);
            }
        }
    }
}

// Convert skillIndex to OpenAI tools format
function getOpenAITools() {
    return Object.values(skillIndex).map(skill => ({
        type: "function",
        function: {
            name: skill.metadata.name.replace(/[^a-zA-Z0-9_-]/g, '_'), // OpenAI names must match ^[a-zA-Z0-9_-]{1,64}$
            description: skill.metadata.description,
            parameters: {
                type: "object",
                properties: {
                    payload: {
                        type: "object",
                        description: `Payload for ${skill.metadata.name}. Expected input type: ${skill.metadata.input}`
                    }
                },
                required: ["payload"]
            }
        }
    }));
}

loadSkills();

app.get('/skills/index', (req, res) => {
    res.json(getOpenAITools());
});

app.post('/skills/execute', async (req, res) => {
    const { skillName, payload } = req.body;

    if (!skillName) {
        return res.status(400).json({ error: 'skillName is required' });
    }

    // Convert from OpenAI format back to our name if needed, or simply lookup directly
    // Since we sanitize names for OpenAI, let's find the matching skill
    const targetSkill = skillIndex[skillName] || Object.values(skillIndex).find(
        s => s.metadata.name.replace(/[^a-zA-Z0-9_-]/g, '_') === skillName
    );

    if (!targetSkill) {
        return res.status(404).json({ error: `Skill not found: ${skillName}` });
    }

    try {
        // Dynamically require the skill module
        // Clear require cache for development? Not for production. Let's assume production.
        const skillFunction = require(targetSkill.entrypointPath);

        // Execute the skill
        let result;
        if (typeof skillFunction === 'function') {
             result = await skillFunction(payload || {});
        } else if (skillFunction.execute && typeof skillFunction.execute === 'function') {
             result = await skillFunction.execute(payload || {});
        } else if (skillFunction.default && typeof skillFunction.default === 'function') {
             result = await skillFunction.default(payload || {});
        } else {
            throw new Error(`Skill entrypoint does not export a function.`);
        }

        res.json({ success: true, result });
    } catch (err) {
        console.error(`Error executing skill ${skillName}:`, err);
        res.status(500).json({ success: false, error: err.message });
    }
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
    console.log(`Skill Execution Engine running on port ${port}`);
});
