/**
 * Automated Verification of CALPHADHEACalc Node.js Middleware & SSE Stream
 */

const http = require('http');
const { spawn } = require('child_process');
const path = require('path');

const SERVER_PATH = path.join(__dirname, 'server.js');
const TEST_PORT = 3001;

console.log('=================================================================');
console.log('     TESTING CALPHADHEACalc BACKEND MIDDLEWARE & SSE STREAM      ');
console.log('=================================================================\n');

async function runTests() {
  // 1. Launch server on port 3001
  console.log('--- Test 1: Spawning Backend Server Process ---');
  const serverProcess = spawn('node', [SERVER_PATH], {
    env: { ...process.env, PORT: String(TEST_PORT) },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  serverProcess.stderr.on('data', d => console.error('Server err:', d.toString()));

  // Wait for server to bind
  await new Promise((resolve, reject) => {
    serverProcess.stdout.on('data', data => {
      const msg = data.toString();
      if (msg.includes('Server running at')) {
        console.log('  Server successfully listening on port ' + TEST_PORT);
        resolve();
      }
    });
    setTimeout(() => reject(new Error('Server failed to start within 5s')), 5000);
  });

  try {
    // 2. Query /api/status
    console.log('\n--- Test 2: Querying /api/status ---');
    const statusRes = await httpGet(`http://localhost:${TEST_PORT}/api/status`);
    const statusData = JSON.parse(statusRes);
    console.log(`  Engine Status  : ${statusData.status}`);
    console.log(`  Active Engine  : ${statusData.engine}`);
    console.log(`  MATLAB Path    : ${statusData.matlabPath || 'None (Fallback Mode)'}`);
    if (statusData.status !== 'online') throw new Error('Status not online');

    // 3. Connect to /api/solver-stream (SSE)
    console.log('\n--- Test 3: Subscribing to ANSYS Fluent SSE Stream (/api/solver-stream) ---');
    const streamEvents = [];
    const sseReq = http.request(`http://localhost:${TEST_PORT}/api/solver-stream`, res => {
      res.on('data', chunk => {
        const text = chunk.toString();
        const lines = text.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              streamEvents.push(data);
              if (data.line && data.line.includes('Step   T (K)   Iter')) {
                console.log('  [SSE Received] Fluent Header Table detected!');
              }
            } catch (e) {}
          }
        }
      });
    });
    sseReq.on('error', () => {});
    sseReq.end();
    await new Promise(r => setTimeout(r, 600));

    // 4. Trigger Calculation via POST /api/calculate
    console.log('\n--- Test 4: Dispatching Calculation (POST /api/calculate) ---');
    const calcPayload = {
      alloyName: 'Cantor Alloy (CoCrFeMnNi)',
      elements: ['Co', 'Cr', 'Fe', 'Mn', 'Ni'],
      fractions: [0.2, 0.2, 0.2, 0.2, 0.2],
      temperatureRange: [1000, 1600],
      temperatureStep: 100
    };

    const calcRes = await httpPost(`http://localhost:${TEST_PORT}/api/calculate`, calcPayload);
    const resultObj = JSON.parse(calcRes);

    console.log('  Calculation completed!');
    console.log(`  Success           : ${resultObj.Success}`);
    console.log(`  Thermodynamics    : Solidus ${resultObj.Thermodynamics.T_Solidus} K, Liquidus ${resultObj.Thermodynamics.T_Liquidus} K`);
    console.log(`  Mechanical        : Yield ${resultObj.Mechanical.YieldStrength_RT_MPa} MPa, Hardness ${resultObj.Mechanical.VickersHardness_HV} HV`);
    console.log(`  Corrosion         : PREN ${resultObj.Corrosion.PREN_HEA}, Rate ${resultObj.Corrosion.CR_mm_yr_NaCl} mm/yr`);
    console.log(`  Telemetry Points  : ${resultObj.Telemetry ? resultObj.Telemetry.length : 0} points`);
    console.log(`  SSE Events Streamed: ${streamEvents.length} events received`);

    if (!resultObj.Success) throw new Error('Calculation returned Success = false');
    if (!resultObj.Telemetry || resultObj.Telemetry.length === 0) throw new Error('No telemetry points returned');
    if (streamEvents.length === 0) throw new Error('No SSE stream events received');

    console.log('\n=================================================================');
    console.log('   ALL BACKEND MIDDLEWARE & SSE STREAM TESTS PASSED (100%)!      ');
    console.log('=================================================================\n');

    if (sseReq) {
      try { sseReq.destroy(); } catch (e) {}
    }
  } finally {
    serverProcess.kill();
  }
}

function httpGet(urlStr) {
  return new Promise((resolve, reject) => {
    http.get(urlStr, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

function httpPost(urlStr, bodyObj) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(bodyObj);
    const req = http.request(urlStr, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

runTests().catch(err => {
  console.error('\n[FATAL] Test failed:', err);
  process.exit(1);
});
