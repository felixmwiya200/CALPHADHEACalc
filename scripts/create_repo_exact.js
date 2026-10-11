const fs = require('fs');
const path = require('path');
const { chromium } = require('C:/Users/Dell/.gemini/config/skills/playwright-skill/node_modules/playwright');

async function main() {
  const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE, 'AppData', 'Local');
  const portFile = path.join(localAppData, 'Google', 'Chrome', 'User Data', 'DevToolsActivePort');
  const [port, browserPath] = fs.readFileSync(portFile, 'utf8').trim().split(/\r?\n/);
  const endpoint = `ws://127.0.0.1:${port}${browserPath}`;
  
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP(endpoint);
  const context = browser.contexts()[0];
  const pages = context.pages();
  let page = pages.find(p => p.url().includes('github.com/new'));
  if (!page) {
    page = await context.newPage();
    await page.goto('https://github.com/new', { waitUntil: 'load' });
  }
  
  // 1. Fill repository name
  const nameInput = page.locator('#repository-name-input');
  await nameInput.fill('CALPHADHEACalc');
  console.log('Filled repo name: CALPHADHEACalc');
  
  // 2. Fill description
  const descInput = page.locator('input[name="Description"]');
  if (await descInput.isVisible()) {
    await descInput.fill('High-Entropy Alloy Multi-Physics Thermodynamic Properties Software (CALPHAD, Miedema, Varvenne-Curtin, Wagner, ASTM G102, XRD)');
    console.log('Filled Description');
  }
  
  // Wait 2.5s for GitHub availability check to validate
  await page.waitForTimeout(2500);
  
  await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_filled_exact.png' });
  console.log('Saved screenshot to github_filled_exact.png');
  
  // 3. Click "Create repository" button
  const createBtn = page.locator('button[type="submit"]:has-text("Create repository")');
  await createBtn.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);
  
  const isEnabled = await createBtn.isEnabled();
  console.log('Create repository button isEnabled:', isEnabled);
  
  if (isEnabled) {
    console.log('Clicking "Create repository"...');
    await createBtn.click();
    
    // Wait for creation & navigation
    await page.waitForTimeout(6000);
    console.log('New URL after click:', page.url());
    await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_after_create.png' });
    console.log('Saved screenshot to github_after_create.png');
  }
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
