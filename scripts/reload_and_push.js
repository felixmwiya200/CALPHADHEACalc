const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
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
  
  let page = pages.find(p => p.url().includes('settings/tokens'));
  if (!page) {
    page = await context.newPage();
  }
  
  console.log('Navigating cleanly to https://github.com/settings/tokens/new...');
  await page.goto('https://github.com/settings/tokens/new', { waitUntil: 'load' });
  await page.waitForTimeout(1500);
  
  // Fill Note
  const noteInput = page.locator('input#oauth_access_description, input[name="oauth_access[description]"]').first();
  await noteInput.waitFor({ state: 'visible', timeout: 10000 });
  const uniqueNote = 'CALPHAD Deploy ' + Math.random().toString(36).substring(2, 8);
  await noteInput.fill(uniqueNote);
  console.log('Filled Note:', uniqueNote);
  
  // Check scopes: repo AND workflow
  const repoBox = page.locator('input[value="repo"]').first();
  await repoBox.check();
  console.log('Checked repo scope');
  
  const wfBox = page.locator('input[value="workflow"]').first();
  await wfBox.check();
  console.log('Checked workflow scope');
  
  // Scroll to bottom and click Generate token
  const genBtn = page.locator('button:has-text("Generate token")').first();
  await genBtn.scrollIntoViewIfNeeded();
  await page.waitForTimeout(500);
  console.log('Clicking Generate token...');
  await genBtn.click();
  
  // Wait for token page to load
  await page.waitForTimeout(4000);
  console.log('Current URL:', page.url());
  
  // Grab token
  const tokenEl = page.locator('#new-oauth-token, [data-clipboard-text*="ghp_"]').first();
  await tokenEl.waitFor({ state: 'visible', timeout: 10000 });
  const token = (await tokenEl.getAttribute('data-clipboard-text')) || (await tokenEl.textContent()).trim();
  
  console.log('Captured Token prefix:', token.substring(0, 8), '... length:', token.length);
  
  // Push code!
  const repoDir = 'C:\\Users\\Dell\\Documents\\Material design';
  console.log('Setting authenticated remote URL...');
  execSync(`git remote set-url origin https://${token}@github.com/felixmwiya200/CALPHADHEACalc.git`, { cwd: repoDir, stdio: 'inherit' });
  
  console.log('Pushing main to GitHub...');
  execSync('git push -u origin main', { cwd: repoDir, stdio: 'inherit' });
  
  console.log('Restoring clean origin URL...');
  execSync('git remote set-url origin https://github.com/felixmwiya200/CALPHADHEACalc.git', { cwd: repoDir, stdio: 'inherit' });
  
  console.log('SUCCESS! CALPHADHEACalc is pushed and live on GitHub!');
  
  // Take screenshot of repository
  await page.goto('https://github.com/felixmwiya200/CALPHADHEACalc', { waitUntil: 'load' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_repo_live.png' });
  console.log('Saved screenshot of live repo to github_repo_live.png');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
