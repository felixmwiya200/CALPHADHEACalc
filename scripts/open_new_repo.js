const fs = require('fs');
const path = require('path');
const { chromium } = require('C:/Users/Dell/.gemini/config/skills/playwright-skill/node_modules/playwright');

async function main() {
  const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE, 'AppData', 'Local');
  const portFile = path.join(localAppData, 'Google', 'Chrome', 'User Data', 'DevToolsActivePort');
  const [port, browserPath] = fs.readFileSync(portFile, 'utf8').trim().split(/\r?\n/);
  const endpoint = `ws://127.0.0.1:${port}${browserPath}`;
  
  console.log('Connecting to Chrome...');
  const browser = await chromium.connectOverCDP(endpoint);
  const context = browser.contexts()[0];
  
  // Open a fresh tab in the authenticated session
  const page = await context.newPage();
  console.log('Opening https://github.com/new in new tab...');
  await page.goto('https://github.com/new', { waitUntil: 'networkidle', timeout: 30000 });
  
  console.log('Current URL in new tab:', page.url());
  console.log('Page Title:', await page.title());
  
  await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_new_tab.png' });
  console.log('Saved screenshot to github_new_tab.png');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
