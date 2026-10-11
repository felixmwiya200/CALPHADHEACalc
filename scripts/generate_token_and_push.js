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
  await page.goto('https://github.com/settings/tokens/new', { waitUntil: 'load' });
  
  // 1. Fill Note
  const noteInput = page.locator('input#oauth_access_description, input[name="oauth_access[description]"], input[placeholder*="token"]').first();
  await noteInput.fill(`CALPHADHEACalc Push ${Date.now()}`);
  console.log('Filled unique Token Note');
  
  // 2. Select 'repo' and 'workflow' scopes
  const repoCheckbox = page.locator('input[value="repo"], input#oauth_access_scopes_repo').first();
  await repoCheckbox.check();
  console.log('Checked repo scope');

  const workflowCheckbox = page.locator('input[value="workflow"], input#oauth_access_scopes_workflow').first();
  await workflowCheckbox.check();
  console.log('Checked workflow scope');
  
  // 3. Click Generate token
  const genBtn = page.locator('button:has-text("Generate token")').first();
  await genBtn.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);
  console.log('Clicking Generate token...');
  await genBtn.click();
  
  // Wait for navigation / token display
  await page.waitForTimeout(4000);
  console.log('Current URL after generation:', page.url());
  
  // Extract token
  const tokenElement = page.locator('#new-oauth-token, code#new-oauth-token, [data-clipboard-text*="ghp_"]').first();
  let token = '';
  if (await tokenElement.isVisible()) {
    token = (await tokenElement.textContent()).trim();
  } else {
    // Try finding by clipboard attribute
    const clipEl = page.locator('[data-clipboard-text]').first();
    if (await clipEl.isVisible()) {
      token = await clipEl.getAttribute('data-clipboard-text');
    }
  }
  
  if (!token || !token.startsWith('ghp_')) {
    console.error('Could not find generated token on page');
    await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/token_failed.png' });
    process.exit(1);
  }
  
  console.log('Successfully acquired token: ghp_... (length: ' + token.length + ')');
  
  // 4. Push local repository using token
  const repoDir = 'C:\\Users\\Dell\\Documents\\Material design';
  console.log('Setting authenticated remote URL...');
  execSync(`git remote set-url origin https://${token}@github.com/felixmwiya200/CALPHADHEACalc.git`, { cwd: repoDir, stdio: 'inherit' });
  
  console.log('Pushing main branch to GitHub...');
  execSync('git push -u origin main', { cwd: repoDir, stdio: 'inherit' });
  
  console.log('Restoring clean origin URL...');
  execSync('git remote set-url origin https://github.com/felixmwiya200/CALPHADHEACalc.git', { cwd: repoDir, stdio: 'inherit' });
  
  console.log('PUSH COMPLETE! Repository is live on GitHub!');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
