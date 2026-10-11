const fs = require('fs');
const path = require('path');
const { chromium } = require('C:/Users/Dell/.gemini/config/skills/playwright-skill/node_modules/playwright');

async function main() {
  const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE, 'AppData', 'Local');
  const portFile = path.join(localAppData, 'Google', 'Chrome', 'User Data', 'DevToolsActivePort');
  if (!fs.existsSync(portFile)) {
    console.error('DevToolsActivePort not found');
    process.exit(1);
  }
  const [port, browserPath] = fs.readFileSync(portFile, 'utf8').trim().split(/\r?\n/);
  const endpoint = `ws://127.0.0.1:${port}${browserPath}`;
  
  console.log('Connecting to Chrome at', endpoint);
  const browser = await chromium.connectOverCDP(endpoint);
  const context = browser.contexts()[0];
  const pages = context.pages();
  
  let page = pages.find(p => p.url().includes('github.com'));
  if (!page) {
    page = await context.newPage();
  }
  
  console.log('Navigating to https://github.com/new...');
  await page.goto('https://github.com/new', { waitUntil: 'load', timeout: 30000 });
  console.log('Current URL:', page.url());
  
  // Wait a moment for page rendering
  await page.waitForTimeout(2000);
  
  const currentUrl = page.url();
  console.log('Page title:', await page.title());
  
  // Check if we are on the login page or repo creation page
  if (currentUrl.includes('/login')) {
    console.log('STATUS: LOGIN_REQUIRED');
  } else if (currentUrl.includes('/new')) {
    console.log('STATUS: LOGGED_IN_NEW_REPO');
    
    // Fill in repository name
    // GitHub's new repo UI typically uses: input[data-testid="repository-name-input"] or #repository_name or input[name="repository[name]"]
    const nameInput = page.locator('input[data-testid="repository-name-input"], input[aria-label="Repository name"], input#repository_name, input[name="repository[name]"]').first();
    if (await nameInput.isVisible()) {
      console.log('Found repository name input');
      await nameInput.fill('CALPHADHEACalc');
      console.log('Filled repository name: CALPHADHEACalc');
    } else {
      console.log('Repository name input not directly found, searching all inputs...');
    }
  }
  
  const screenshotPath = 'C:/Users/Dell/Documents/Material design/github_new_page.png';
  await page.screenshot({ path: screenshotPath, fullPage: false });
  console.log('Screenshot saved to:', screenshotPath);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
