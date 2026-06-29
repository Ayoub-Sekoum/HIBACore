const http = require('http');
const fs = require('fs');
const path = require('path');
const port = process.env.PORT || 8080;

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2'
};

const server = http.createServer((req, res) => {
  const urlPath = req.url.split('?')[0];
  let filePath = path.join(__dirname, urlPath === '/' ? 'index.html' : urlPath);
  
  console.log('Request URL:', req.url, '-> Target Path:', filePath);

  fs.access(filePath, fs.constants.F_OK, (err) => {
    if (err) {
      console.log('File not found, falling back to index.html');
      filePath = path.join(__dirname, 'index.html');
    }
    
    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'text/plain';
    
    fs.readFile(filePath, (err, data) => {
      if (err) {
        console.error('Error reading file:', filePath, err);
        res.writeHead(500);
        res.end('Error loading file: ' + filePath);
        return;
      }
      res.writeHead(200, { 
        'Content-Type': contentType,
        'Cross-Origin-Opener-Policy': 'same-origin-allow-popups',
        'Cross-Origin-Embedder-Policy': 'unsafe-none'
      });
      res.end(data);
    });
  });
});

server.listen(port, () => {
  console.log('Server in ascolto sulla porta ' + port);
});
