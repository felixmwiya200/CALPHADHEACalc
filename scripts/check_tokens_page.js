const fs = require('fs');
const path = require('path');
const { chromium } = require('C:/Users/Dell/.gemini/config/skills/playwright-skill/node_modules/playwright');

async function main() {
  const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE, 'AppData', 'Local');
  const portFile = path.join(localAppData, 'Google', 'Chrome', 'User Data', 'DevToolsActivePort');
  const [port, browserPath] = fs.readFileSync(portFile, 'utf8').trim().split(/\r?\n/);
  const endpoint = `ws://127.0.0.1:${port}${browserPath}`;
  
  const browser = await chromium.connectOverCDP(endpoint);
  const context = browser.contexts()[0];
  const page = await context.newPage();
  
  console.log('Navigating to https://github.com/settings/tokens/new...');
  await page.goto('https://github.com/settings/tokens/new', { waitUntil: 'load', timeout: 30000 });
  
  console.log('Current URL:', page.url());
  console.log('Title:', await page.title());
  
  await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_tokens_page.png' });
  console.log('Saved screenshot to github_tokens_page.png');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
