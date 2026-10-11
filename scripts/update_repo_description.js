const fs = require('fs');
const path = require('path');
const { chromium } = require('C:/Users/Dell/.gemini/config/skills/playwright-skill/node_modules/playwright');

async function main() {
  try {
    const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE, 'AppData', 'Local');
    const portFile = path.join(localAppData, 'Google', 'Chrome', 'User Data', 'DevToolsActivePort');
    if (!fs.existsSync(portFile)) {
      console.error('Chrome DevToolsActivePort file not found');
      return;
    }
    const [port, browserPath] = fs.readFileSync(portFile, 'utf8').trim().split(/\r?\n/);
    const endpoint = `ws://127.0.0.1:${port}${browserPath}`;
    
    console.log('Connecting to Chrome over CDP...');
    const browser = await chromium.connectOverCDP(endpoint);
    const contexts = browser.contexts();
    if (!contexts.length) {
      console.error('No browser contexts found');
      return;
    }
    
    const context = contexts[0];
    const pages = context.pages();
    let page = pages.find(p => p.url().includes('github.com/felixmwiya200/CALPHADHEACalc'));
    if (!page) {
      console.log('Repo page not found among open tabs, creating a new tab...');
      page = await context.newPage();
      await page.goto('https://github.com/felixmwiya200/CALPHADHEACalc', { waitUntil: 'load' });
    } else {
      console.log('Found open repo page:', page.url());
      await page.bringToFront();
    }
    
    await page.waitForTimeout(1000);
    
    // Look for the gear icon next to About (Edit repository details)
    console.log('Looking for About edit button...');
    const editBtn = page.locator('button[aria-label="Edit repository details"], button:has-text("Edit repository details"), button.btn-octicon[aria-label*="repository details"], [data-target="modal-dialog.show-modal-dialog-btn"]').first();
    
    let clicked = false;
    if (await editBtn.isVisible()) {
      await editBtn.click();
      clicked = true;
      console.log('Clicked edit button directly');
    } else {
      // Try finding by svg or aria label or text
      const gearBtn = page.locator('.BorderGrid-cell button svg.octicon-gear').locator('..').first();
      if (await gearBtn.isVisible()) {
        await gearBtn.click();
        clicked = true;
        console.log('Clicked gear button');
      }
    }
    
    if (!clicked) {
      // Look for any button within the About container
      const aboutSection = page.locator('.BorderGrid-row:has-text("About")');
      const aboutGear = aboutSection.locator('button').first();
      if (await aboutGear.isVisible()) {
        await aboutGear.click();
        clicked = true;
        console.log('Clicked About section button');
      }
    }
    
    await page.waitForTimeout(1500);
    
    // In the modal dialog, find the description input
    const descInput = page.locator('input#repo_description, input[name="repo[description]"], input[name="description"]').first();
    if (await descInput.isVisible()) {
      const currentDesc = await descInput.inputValue();
      console.log('Current description:', currentDesc);
      
      const newDesc = currentDesc.replace(/Thermodynamic & Property/g, 'Thermodynamic properties')
                                 .replace(/Thermodynamic and Property/g, 'Thermodynamic properties');
      console.log('New description to set:', newDesc);
      
      await descInput.fill(newDesc);
      await page.waitForTimeout(500);
      
      // Click Save changes
      const saveBtn = page.locator('button:has-text("Save changes")').first();
      if (await saveBtn.isVisible()) {
        await saveBtn.click();
        console.log('Clicked Save changes button!');
        await page.waitForTimeout(2000);
      }
    } else {
      console.log('Description input not found in dialog');
    }
    
    // Reload page to reflect changes
    await page.reload({ waitUntil: 'load' });
    console.log('Page reloaded successfully');
    
    // Take screenshot to verify
    await page.screenshot({ path: 'C:/Users/Dell/Documents/Material design/github_about_updated.png' });
    console.log('Screenshot saved to github_about_updated.png');
    
  } catch (err) {
    console.error('Error in main:', err.message);
  }
}

main();
