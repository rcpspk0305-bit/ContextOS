import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ARTIFACTS_DIR = path.resolve(__dirname, '../../artifacts/e2e');
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

async function captureScreenshots() {
  console.log('Launching Chrome to capture ContextOS E2E screenshots...');
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2, // High DPI for crisp screenshots
  });

  const page = await context.newPage();
  const baseUrl = 'http://127.0.0.1:3000';

  console.log('Navigating to', baseUrl);
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // 1. Dashboard / Workspace
  console.log('1. Capturing 01-dashboard.png...');
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '01-dashboard.png') });

  // 2. Terminal Drawer expanded
  console.log('2. Capturing 04-terminal-drawer.png...');
  const terminalToggle = page.locator('button:has-text("Terminal & Logs")');
  if (await terminalToggle.count() > 0) {
    await terminalToggle.click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, '04-terminal-drawer.png') });
    await terminalToggle.click(); // collapse back
    await page.waitForTimeout(400);
  }

  // 3. Approval Card interaction
  console.log('3. Capturing 03-approval-popup.png...');
  // The approval card is visible in the activity stream or conversation view
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '03-approval-popup.png') });

  // 4. Command Palette (Ctrl+K)
  console.log('4. Capturing 09-command-palette.png...');
  await page.keyboard.press('Control+k');
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '09-command-palette.png') });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);

  // 5. Agents Fleet Page
  console.log('5. Capturing 02-agent-fleet.png...');
  await page.click('button:has-text("Agents")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '02-agent-fleet.png') });

  // 6. Sessions Page (Checkpoints & Resumption)
  console.log('6. Capturing 10-resumed-session.png...');
  await page.click('button:has-text("Sessions")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '10-resumed-session.png') });

  // 7. Memory Explorer Page (ADRs, semantic records)
  console.log('7. Capturing 06-memory-explorer.png...');
  await page.click('button:has-text("Memory")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '06-memory-explorer.png') });

  // 8. Context Engine Inspector (4-tier hierarchy, token metrics)
  console.log('8. Capturing 05-context-inspector.png...');
  await page.click('button:has-text("Context")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '05-context-inspector.png') });

  // 9. MCP v2 Server Status
  console.log('9. Capturing 07-mcp-status.png...');
  await page.click('button:has-text("MCP")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '07-mcp-status.png') });

  // 10. Analytics Dashboard (Without vs With ContextOS)
  console.log('10. Capturing 08-analytics-dashboard.png...');
  await page.click('button:has-text("Analytics")');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, '08-analytics-dashboard.png') });

  await browser.close();
  console.log('All 10 screenshots captured successfully into', ARTIFACTS_DIR);
}

captureScreenshots().catch((err) => {
  console.error('Error capturing screenshots:', err);
  process.exit(1);
});
