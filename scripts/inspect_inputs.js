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
  const pages = context.pages();
  let page = pages.find(p => p.url().includes('github.com/new'));
  if (!page) {
    console.log('No /new page found, available pages:', pages.map(p => p.url()));
    return;
  }
  
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input, button, [contenteditable]')).map(el => ({
      tag: el.tagName,
      id: el.id,
      name: el.name,
      type: el.type,
      placeholder: el.placeholder,
      ariaLabel: el.getAttribute('aria-label'),
      dataTestId: el.getAttribute('data-testid'),
      text: el.innerText || el.textContent || '',
      classes: el.className
    }));
  });
  
  console.log('Found elements:', JSON.stringify(inputs.filter(el => el.tag === 'INPUT' || el.text.includes('Create') || el.text.includes('repository')), null, 2));
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
