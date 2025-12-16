const { spawn } = require('child_process')
const path = require('path')

const vite = spawn('node', [
  path.join(__dirname, 'node_modules', 'vite', 'bin', 'vite.js'),
  '--port', '6100'
], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true
})

vite.on('close', (code) => {
  process.exit(code)
})
