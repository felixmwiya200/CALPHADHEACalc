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
  
  // ==========================================
  // 1. CONFIGURE GITHUB PAGES
  // ==========================================
  console.log('Navigating to GitHub Pages settings...');
  await page.goto('https://github.com/felixmwiya200/CALPHADHEACalc/settings/pages', { waitUntil: 'load' });
  await page.waitForTimeout(2000);
  
  try {
    // Select branch 'main'
    const branchBtn = page.locator('button#pages_select_branch-button, button:has-text("None"), button:has-text("Select branch")').first();
    if (await branchBtn.isVisible()) {
      await branchBtn.click();
      await page.waitForTimeout(800);
      
      // Click 'main'
      const mainOption = page.locator('li:has-text("main"), button:has-text("main"), span:has-text("main")').first();
      await mainOption.click();
      await page.waitForTimeout(800);
      console.log('Selected branch main for Pages');
    }
    
    // Select folder '/docs'
    const dirBtn = page.locator('button#pages_select_dir-button, button:has-text("/(root)"), button:has-text("/docs")').first();
    if (await dirBtn.isVisible()) {
      await dirBtn.click();
      await page.waitForTimeout(800);
      
      const docsOption = page.locator('li:has-text("/docs"), button:has-text("/docs"), span:has-text("/docs")').first();
      if (await docsOption.isVisible()) {
        await docsOption.click();
        await page.waitForTimeout(800);
        console.log('Selected folder /docs for Pages');
      }
    }
    
    // Click Save
    const savePagesBtn = page.locator('button:has-text("Save")').first();
    if (await savePagesBtn.isVisible() && await savePagesBtn.isEnabled()) {
      await savePagesBtn.click();
      await page.waitForTimeout(2500);
      console.log('Saved GitHub Pages settings!');
    }
  } catch (err) {
    console.warn('Note on Pages setup:', err.message);
  }
  
  await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_pages_configured.png' });
  console.log('Saved screenshot to github_pages_configured.png');
  
  // ==========================================
  // 2. CONFIGURE BRANCH PROTECTION FOR 'main'
  // ==========================================
  console.log('Navigating to Branch Protection setup...');
  await page.goto('https://github.com/felixmwiya200/CALPHADHEACalc/settings/branch_protection_rules/new', { waitUntil: 'load' });
  await page.waitForTimeout(2000);
  
  try {
    // Branch name pattern: main
    const patternInput = page.locator('input#rule_field, input[name="rule"], input[placeholder*="pattern"]').first();
    await patternInput.fill('main');
    console.log('Filled branch pattern: main');
    
    // Require pull request before merging
    const prBox = page.locator('input#has_required_reviews, input#has_required_reviews_reviews').first();
    if (await prBox.isVisible()) {
      await prBox.check();
      console.log('Checked: Require pull request before merging');
    }
    
    // Enforce for administrators
    const adminBox = page.locator('input#enforce_all_for_admins, input#include_administrators').first();
    if (await adminBox.isVisible()) {
      await adminBox.check();
      console.log('Checked: Do not allow bypassing');
    }
    
    // Click Create
    const createRuleBtn = page.locator('button[type="submit"]:has-text("Create")').first();
    await createRuleBtn.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    if (await createRuleBtn.isEnabled()) {
      await createRuleBtn.click();
      await page.waitForTimeout(3000);
      console.log('Saved Branch Protection Rule for main!');
    }
  } catch (err) {
    console.warn('Note on Branch Protection setup:', err.message);
  }
  
  await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_branches_configured.png' });
  console.log('Saved screenshot to github_branches_configured.png');
  
  console.log('ALL GITHUB AUTOMATION STEPS COMPLETE!');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
