const fs = require('fs');

const html = fs.readFileSync('App/ui/index.html', 'utf8');
console.log('HTML file length:', html.length);

// Extract all scripts and test syntax
const scriptRegex = /<script(?:\s+[^>]*)?>([\s\S]*?)<\/script>/gi;
let match;
let scriptCount = 0;
while ((match = scriptRegex.exec(html)) !== null) {
  scriptCount++;
  const scriptContent = match[1];
  try {
    new Function(scriptContent);
    console.log(`Script block #${scriptCount}: VALID JavaScript (length ${scriptContent.length})`);
  } catch (err) {
    console.error(`Script block #${scriptCount} SYNTAX ERROR:`, err.message);
    process.exit(1);
  }
}

// Check key DOM elements
const requiredIds = [
  'basisPillGroup', 'basisBtn_at', 'basisBtn_wt', 'basisBtn_mol',
  'basisUnitBadge', 'presetUnitBadge', 'elemHeaderComp',
  'elemTable', 'elemTbody', 'totalVal', 'heaSummaryBar',
  'summaryMolarMass', 'summaryTotalMass', 'summaryTotalMoles',
  'calcHEAThermoBtn', 'heaPredictorCard', 'thermoPhaseBadge',
  'thermoVEC', 'thermoHmix', 'thermoSmix', 'thermoOmega',
  'thermoDelta', 'thermoDeltaChi', 'thermoMelting',
  'liveRefContainer', 'plotCanvas',
  'plotTypeSelect', 'plotLineStyleSelect', 'plotLineWidthSelect',
  'plotMarkerSelect', 'plotPaletteSelect', 'plotScaleSelect',
  'plotGridSelect', 'btnZoomIn', 'btnZoomOut', 'btnZoomReset',
  'btnPlotExpand', 'btnPlotFullscreen', 'btnExportPlot',
  'plotCoordBadge', 'plotCanvasContainer', 'plotFullscreenModal',
  'plotCanvasFullscreen', 'plotTooltipHUD', 'plotZoomBox',
  // XRD Sub-graph & Fullscreen IDs
  'xrdSubgraphWrap', 'xrdPhaseSummary', 'xrdPhaseTags', 'btnXRDExpand',
  'btnXRDFullscreen', 'btnXRDExportPNG', 'btnXRDExportCSV', 'xrdSourceSelect',
  'xrdSizeSlider', 'xrdStrainSlider', 'xrdShowSticks', 'xrdShowHKL',
  'xrdShowBenchmark', 'btnXRDZoomIn', 'btnXRDZoomOut', 'btnXRDZoomReset',
  'xrdCoordBadge', 'xrdCanvasContainer', 'xrdCanvas', 'xrdZoomBox',
  'xrdTooltipHUD', 'xrdPeakCount', 'xrdTableChevron', 'xrdPeakTableContainer',
  'xrdPeaksTable', 'xrdPeaksBody', 'xrdFullscreenModal', 'fullscreenXRDContainer',
  'xrdCanvasFullscreen',
  // Corrosion Resistance Predictor IDs
  'corrosionPredictorCard', 'corrosionGradeBadge', 'corrosionPREN', 'corrosionDGox',
  'corrosionPBR', 'corrosionPrimaryOxide', 'corrosionDeltaE', 'corrosionPhaseImmunity',
  'corrosionRateSummary', 'corrosionIcorrNaCl', 'corrosionEcorr', 'corrosionIcorrAcid',
  'corrosionEW', 'corrosionBenchmarkRow', 'corrosionBenchmarkText',
  // PanHEA 2026 CALPHAD Multicomponent, Binary & Ternary IDs
  'tabPhaseFractions', 'tabIsopleth', 'tabTernary',
  'phaseFractionsWrap', 'phaseFractionsSubtitle', 'phaseFractionsLegend', 'btnPFRecompute', 'btnPFExpand',
  'phaseFractionsMetricsBar', 'badgeB2Solvus', 'badgeSigmaSolvus', 'badgeSolidus', 'badgeLiquidus',
  'pfCanvasContainer', 'phaseFractionsCanvas', 'pfTooltipHUD',
  'isoplethWrap', 'isoplethSubtitle', 'isoplethSoluteSelect', 'isoplethCanvasContainer', 'isoplethCanvas', 'isoplethTooltipHUD',
  'ternaryWrap', 'ternarySubtitle', 'ternaryElemASelect', 'ternaryElemBSelect', 'ternaryElemCSelect', 'ternaryTempInput',
  'ternaryCanvasContainer', 'ternaryCanvas', 'ternaryTooltipHUD', 'ternaryProbeHUD',
  // HEA Mechanical Properties & Oxidation Kinetics IDs
  'tabMechanical', 'tabOxidation',
  'mechanicalWrap', 'grainSizeSlider', 'grainSizeVal', 'mechTempInput',
  'mechYieldStrength', 'mechYieldSub', 'mechUTS', 'mechUTSSub',
  'mechElongation', 'mechElongationSub', 'mechHardness', 'mechHardnessSub',
  'mechToughness', 'mechToughnessSub', 'mechPughRatio', 'mechPughSub',
  'mechBreakdownBar', 'badgeSig0', 'badgeSigSS', 'badgeSigHP', 'badgeSigOrowan', 'badgeTc',
  'mechTempCanvasContainer', 'mechTempCanvas', 'mechTempTooltipHUD',
  'mechFlowCanvasContainer', 'mechFlowCanvas', 'mechFlowTooltipHUD',
  'oxidationWrap', 'oxTempSlider', 'oxTempVal', 'oxTimeSlider', 'oxTimeVal',
  'oxAlertContainer', 'oxPestingAlert', 'oxVolatileAlert', 'oxSpallationAlert',
  'oxRegime', 'oxRegimeSub', 'oxKp', 'oxKpSub',
  'oxMassGain', 'oxMassGainSub', 'oxScaleThickness', 'oxScaleThicknessSub',
  'oxSpallationStress', 'oxSpallationSub', 'oxWagnerStatus', 'oxWagnerSub',
  'oxKineticsCanvasContainer', 'oxKineticsCanvas', 'oxKineticsTooltipHUD',
  'oxArrheniusCanvasContainer', 'oxArrheniusCanvas', 'oxArrheniusTooltipHUD'
];

let missing = [];
for (const id of requiredIds) {
  if (!html.includes(`id="${id}"`)) {
    missing.push(id);
  }
}

if (missing.length > 0) {
  console.error('Missing IDs in HTML:', missing);
  process.exit(1);
} else {
  console.log(`All ${requiredIds.length} required DOM elements verified present!`);
}

console.log('HTML verification successful!');
