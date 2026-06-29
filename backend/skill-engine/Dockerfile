FROM node:20

WORKDIR /skills

# Copy package files
COPY package*.json ./

# Copy registry first
COPY registry ./registry

# Install dependencies (in real scenario, we'd also install skills' dependencies here)
RUN npm install

# Copy application code
COPY server.js .

EXPOSE 3000

CMD ["node", "server.js"]
