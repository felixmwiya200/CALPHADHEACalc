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
  const page = await context.newPage();
  
  console.log('Navigating to GitHub Pages settings...');
  await page.goto('https://github.com/felixmwiya200/CALPHADHEACalc/settings/pages', { waitUntil: 'load' });
  await page.waitForTimeout(2000);
  
  // Option 1: Select "GitHub Actions" as the source dropdown
  console.log('Looking for Source dropdown...');
  const sourceDropdown = page.locator('button:has-text("Deploy from a branch"), button:has-text("GitHub Actions")').first();
  if (await sourceDropdown.isVisible()) {
    console.log('Clicking source dropdown...');
    await sourceDropdown.click();
    await page.waitForTimeout(1000);
    
    const actionsOption = page.locator('li:has-text("GitHub Actions"), span:has-text("GitHub Actions"), [role="menuitem"]:has-text("GitHub Actions")').first();
    if (await actionsOption.isVisible()) {
      console.log('Selecting GitHub Actions...');
      await actionsOption.click();
      await page.waitForTimeout(2000);
    }
  }
  
  await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_pages_after_fix.png' });
  console.log('Screenshot saved.');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
