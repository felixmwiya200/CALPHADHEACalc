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
  const pages = context.pages();
  
  // Find the /new repository tab
  let page = pages.find(p => p.url().includes('github.com/new'));
  if (!page) {
    page = await context.newPage();
    await page.goto('https://github.com/new', { waitUntil: 'networkidle' });
  }
  
  console.log('Current page URL:', page.url());
  
  // Fill repository name
  const repoNameInput = page.locator('input[data-testid="repository-name-input"], input[aria-label="Repository name*"], input[aria-label="Repository name"], input#repository_name, input[placeholder*="repository name"]').first();
  await repoNameInput.waitFor({ state: 'visible', timeout: 10000 });
  await repoNameInput.fill('CALPHADHEACalc');
  console.log('Filled Repository name: CALPHADHEACalc');
  
  // Small pause for GitHub availability check
  await page.waitForTimeout(1500);
  
  // Fill description
  const descInput = page.locator('input[aria-label="Description"], input[name="Description"], input#repository_description, input[placeholder*="Description"]').first();
  if (await descInput.isVisible()) {
    await descInput.fill('High-Entropy Alloy Multi-Physics Thermodynamic Properties Software (CALPHAD, Miedema, Varvenne-Curtin, Wagner, ASTM G102, XRD)');
    console.log('Filled Description');
  }
  
  // Verify visibility is Public
  // GitHub new UI uses a dropdown or radio buttons for visibility
  const visibilityPublic = page.locator('button:has-text("Public"), input[value="public"]').first();
  if (await visibilityPublic.isVisible()) {
    console.log('Visibility is Public');
  }
  
  // Take screenshot before clicking create
  await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_form_filled.png' });
  console.log('Saved screenshot to github_form_filled.png');
  
  // Find Create repository button
  // Typically: button:has-text("Create repository") or button[type="submit"]
  const createBtn = page.locator('button:has-text("Create repository"), button[type="submit"]:has-text("Create")').first();
  await createBtn.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);
  
  // Check if button is enabled
  const isEnabled = await createBtn.isEnabled();
  console.log('Create repository button enabled:', isEnabled);
  
  if (isEnabled) {
    console.log('Clicking "Create repository" button...');
    await createBtn.click();
    
    // Wait for navigation
    await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }).catch(e => console.log('Navigation event:', e.message));
    console.log('New page URL:', page.url());
    
    await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_repo_created.png' });
    console.log('Saved screenshot to github_repo_created.png');
  } else {
    console.log('Create button is not yet enabled, checking page status...');
  }
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
