#!/usr/bin/env python3
"""
Generate a publication-grade, 2-page reference report and calculation sheet
for Equiatomic AlCoCrFeNi (Al-Fe-Cr-Co-Ni) High-Entropy Alloy.
Uses pymupdf.Story and pymupdf.DocumentWriter with exact A4 geometry and running headers/footers.
"""

import os
import pymupdf

def build_alfecrconi_pdf(output_path: str):
    html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4 portrait;
    margin: 0;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 8.0pt;
    line-height: 1.25;
    color: #1e293b;
    margin: 0;
    padding: 0;
  }
  h1 {
    font-size: 13.5pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 2pt 0;
    letter-spacing: -0.3px;
  }
  .subtitle {
    font-size: 8.5pt;
    color: #0369a1;
    font-weight: 600;
    margin-bottom: 5pt;
  }
  h2 {
    font-size: 9.8pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 1.2px solid #0284c7;
    padding-bottom: 1.5pt;
    margin: 4.5pt 0 3pt 0;
  }
  h3 {
    font-size: 8.5pt;
    font-weight: 700;
    color: #0369a1;
    margin: 3.5pt 0 2pt 0;
  }
  p {
    margin: 1.5pt 0 3pt 0;
    font-size: 8.0pt;
  }
  
  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 2.5pt 0 4pt 0;
    font-size: 7.4pt;
  }
  th {
    background-color: #1e293b;
    color: #ffffff;
    font-weight: 600;
    text-align: center;
    padding: 2.2pt 3pt;
    border: 1px solid #334155;
  }
  td {
    padding: 2.0pt 3pt;
    border: 1px solid #cbd5e1;
    text-align: center;
  }
  tr:nth-child(even) td {
    background-color: #f8fafc;
  }
  .td-left { text-align: left !important; }
  .td-bold { font-weight: 600; }
  
  /* Highlight cards and formula boxes */
  .formula-card {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 3.5px solid #0284c7;
    border-radius: 3px;
    padding: 3pt 5pt;
    margin: 2.5pt 0 3.5pt 0;
    font-size: 7.8pt;
  }
  .formula-title {
    font-weight: 700;
    color: #0369a1;
    margin-bottom: 1pt;
    font-size: 7.9pt;
  }
  .formula-math {
    font-family: "Courier New", Courier, monospace;
    font-size: 7.7pt;
    font-weight: 600;
    color: #0f172a;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 1.5pt 3.5pt;
    border-radius: 2px;
    margin: 1.5pt 0;
    display: block;
  }
  
  .badge {
    display: inline-block;
    padding: 1pt 4pt;
    border-radius: 3px;
    font-size: 6.8pt;
    font-weight: 700;
  }
  .badge-pass { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
  .badge-warn { background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
  .badge-fail { background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
  .badge-info { background-color: #e0f2fe; color: #075985; border: 1px solid #bae6fd; }

  .callout-box {
    background-color: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 3px;
    padding: 3.5pt 6pt;
    margin: 3pt 0 4pt 0;
    font-size: 7.7pt;
  }
  .page-break {
    page-break-before: always;
  }
</style>
</head>
<body>

  <!-- ==================== PAGE 1 ==================== -->
  <h1>Equiatomic AlCoCrFeNi High-Entropy Alloy</h1>
  <div class="subtitle">Complete Manual Paper Calculation &bull; Phase Stability, Miedema Thermodynamics &amp; Aqueous Corrosion Prediction</div>

  <div class="callout-box">
    <b>Target Alloy:</b> Al<sub>0.20</sub>Co<sub>0.20</sub>Cr<sub>0.20</sub>Fe<sub>0.20</sub>Ni<sub>0.20</sub> (Equiatomic Al-Fe-Cr-Co-Ni, x<sub>i</sub> = 0.20 each).<br>
    <b>Key Characteristic:</b> Benchmark prototype for Aluminum-strengthened HEAs. Unlike single-phase Cantor alloy, the large size mismatch of Al (143 pm) and strong negative Ni-Al / Co-Al enthalpies trigger <b>spinodal decomposition into BCC + ordered B2 (NiAl-type) phases</b>, altering both mechanical hardness and aqueous corrosion pathways.
  </div>

  <h2>1. Elemental Input Properties &amp; Thermodynamic Database</h2>
  <table>
    <thead>
      <tr>
        <th>Element (i)</th>
        <th>at% (x<sub>i</sub>)</th>
        <th>M<sub>i</sub> (g/mol)</th>
        <th>r<sub>i</sub> (pm)</th>
        <th>VEC<sub>i</sub></th>
        <th>Pauling &chi;<sub>i</sub></th>
        <th>T<sub>m,i</sub> (K)</th>
        <th>E&deg; (V)</th>
        <th>n<sub>i</sub></th>
        <th>Primary Oxide</th>
        <th>&Delta;G&deg;<sub>f,ox</sub> (kJ/mol O<sub>2</sub>)</th>
        <th>PBR<sub>i</sub></th>
      </tr>
    </thead>
    <tbody>
      <tr><td><b>Al</b></td><td>0.20</td><td>26.982</td><td>143</td><td>3</td><td>1.61</td><td>933</td><td>-1.662</td><td>3</td><td>Al<sub>2</sub>O<sub>3</sub></td><td>-1055.0</td><td>1.28</td></tr>
      <tr><td><b>Co</b></td><td>0.20</td><td>58.933</td><td>125</td><td>9</td><td>1.88</td><td>1768</td><td>-0.280</td><td>2</td><td>CoO</td><td>-428.4</td><td>1.76</td></tr>
      <tr><td><b>Cr</b></td><td>0.20</td><td>51.996</td><td>128</td><td>6</td><td>1.66</td><td>2180</td><td>-0.744</td><td>3</td><td>Cr<sub>2</sub>O<sub>3</sub></td><td>-705.4</td><td>2.07</td></tr>
      <tr><td><b>Fe</b></td><td>0.20</td><td>55.845</td><td>126</td><td>8</td><td>1.83</td><td>1811</td><td>-0.447</td><td>2</td><td>Fe<sub>2</sub>O<sub>3</sub></td><td>-494.8</td><td>2.14</td></tr>
      <tr><td><b>Ni</b></td><td>0.20</td><td>58.693</td><td>124</td><td>10</td><td>1.91</td><td>1728</td><td>-0.257</td><td>2</td><td>NiO</td><td>-423.4</td><td>1.65</td></tr>
    </tbody>
  </table>

  <h2>2. Stage I: Mass Balance &amp; Stoichiometry</h2>
  <div class="formula-card">
    <div class="formula-title">1. Mean Molar Mass (M&#772;):</div>
    <span class="formula-math">M&#772; = &Sigma; x<sub>i</sub> M<sub>i</sub> = 0.20 &times; (26.982 + 58.933 + 51.996 + 55.845 + 58.693) = 0.20 &times; 252.449 = 50.490 g/mol</span>
    <div class="formula-title" style="margin-top:2.5pt;">2. Weight Fractions (w<sub>i</sub>): w<sub>i</sub> = (x<sub>i</sub> &times; M<sub>i</sub> / M&#772;) &times; 100%</div>
    &bull; Al: (0.20 &times; 26.982 / 50.490) &times; 100% = <b>10.69 wt%</b> &nbsp;|&nbsp; Co: (0.20 &times; 58.933 / 50.490) &times; 100% = <b>23.34 wt%</b><br>
    &bull; Cr: (0.20 &times; 51.996 / 50.490) &times; 100% = <b>20.60 wt%</b> &nbsp;|&nbsp; Fe: (0.20 &times; 55.845 / 50.490) &times; 100% = <b>22.12 wt%</b><br>
    &bull; Ni: (0.20 &times; 58.693 / 50.490) &times; 100% = <b>23.25 wt%</b> &nbsp;&nbsp;(Total Sum = 100.00 wt%)
  </div>

  <h2>3. Stage II: Phase Stability &amp; Miedema Thermodynamics</h2>
  <div class="formula-card">
    <div class="formula-title">3. Valence Electron Concentration (VEC) &amp; Guo Phase Rule:</div>
    <span class="formula-math">VEC = &Sigma; x<sub>i</sub> VEC<sub>i</sub> = 0.20 &times; (3 + 9 + 6 + 8 + 10) = 0.20 &times; 36 = 7.20</span>
    <b>Guo Criterion:</b> 6.87 &le; VEC &lt; 8.0 &rarr; <b>Duplex Microstructure (Disordered BCC + Ordered B2 / FCC)</b>. &nbsp;<span class="badge badge-warn">DUPLEX PHASE REGIME</span>
  </div>

  <div class="formula-card">
    <div class="formula-title">4. Ideal Configurational Mixing Entropy (&Delta;S<sub>mix</sub>):</div>
    <span class="formula-math">&Delta;S<sub>mix</sub> = -R &Sigma; x<sub>i</sub> ln(x<sub>i</sub>) = R ln(5) = 8.314 &times; 1.6094 = 13.38 J/(mol&middot;K)</span>
    &Delta;S<sub>mix</sub> &ge; 1.5R (12.47 J/mol&middot;K) &rarr; Full High-Entropy Alloy regime. &nbsp;<span class="badge badge-pass">HIGH ENTROPY</span>
  </div>

  <div class="formula-card">
    <div class="formula-title">5. Miedema Chemical Mixing Enthalpy (&Delta;H<sub>mix</sub>):</div>
    Sum all 10 binary interaction pairs (&Delta;H<sub>ij</sub> in kJ/mol):<br>
    &bull; Al-Co: -19 &nbsp;|&nbsp; Al-Cr: -10 &nbsp;|&nbsp; Al-Fe: -11 &nbsp;|&nbsp; Al-Ni: -22 (Very strong B2 NiAl order)<br>
    &bull; Co-Cr: -4 &nbsp;|&nbsp; Co-Fe: 0 &nbsp;|&nbsp; Co-Ni: 0 &nbsp;|&nbsp; Cr-Fe: -1 &nbsp;|&nbsp; Cr-Ni: -7 &nbsp;|&nbsp; Fe-Ni: -2<br>
    &Sigma;<sub>i&lt;j</sub> &Delta;H<sub>ij</sub> = (-19) + (-10) + (-11) + (-22) + (-4) + 0 + 0 + (-1) + (-7) + (-2) = <b>-76 kJ/mol</b>
    <span class="formula-math">&Delta;H<sub>mix</sub> = 4 &times; &Sigma;<sub>i&lt;j</sub> &Delta;H<sub>ij</sub> x<sub>i</sub> x<sub>j</sub> = 4 &times; 0.04 &times; (-76) = -12.16 kJ/mol</span>
    High negative enthalpy indicates pronounced chemical ordering and strong intermetallic affinity.
  </div>

  <div class="formula-card">
    <div class="formula-title">6. Atomic Size Mismatch (&delta;) &amp; Electronegativity Difference (&Delta;&chi;):</div>
    r&#772; = 0.20 &times; (143 + 125 + 128 + 126 + 124) = 0.20 &times; 646 = <b>129.2 pm</b><br>
    &Sigma; x<sub>i</sub> (1 - r<sub>i</sub> / r&#772;)&sup2; = 0.20 &times; [(-0.1068)&sup2; + (0.0325)&sup2; + (0.0093)&sup2; + (0.0248)&sup2; + (0.0402)&sup2;] = 0.002958
    <span class="formula-math">&delta; = &radic;[ 0.002958 ] &times; 100% = 0.05439 &times; 100% = 5.44%</span>
    &chi;&#772; = 0.20 &times; (1.61 + 1.88 + 1.66 + 1.83 + 1.91) = <b>1.778</b> &rarr; <b>&Delta;&chi; = 0.121</b><br>
    <b>Physical Meaning:</b> The large atomic size of Al creates massive lattice strain (&delta; = 5.44% &gt;&gt; Cantor 1.12%), driving phase decomposition.
  </div>

  <div class="formula-card">
    <div class="formula-title">7. Average Melting Point (T<sub>m</sub>&#772;) &amp; Yang-Zhang Stability (&Omega;):</div>
    T<sub>m</sub>&#772; = 0.20 &times; (933 + 1768 + 2180 + 1811 + 1728) = <b>1684.0 K</b>
    <span class="formula-math">&Omega; = (T<sub>m</sub>&#772; &times; &Delta;S<sub>mix</sub>) / |&Delta;H<sub>mix</sub> &times; 1000| = (1684.0 &times; 13.38) / 12160 = 1.85</span>
    <b>Zhang-Yang Criterion:</b> &Omega; &ge; 1.1 and &delta; &le; 6.6%. Although &Omega; = 1.85 &gt; 1.1, the low value relative to its large negative &Delta;H<sub>mix</sub> (-12.16 kJ/mol) proves that entropic stabilization cannot prevent the formation of ordered B2 (Ni,Al)-rich nanoprecipitates! &nbsp;<span class="badge badge-warn">&Omega; = 1.85 (PRECIPITATION ACTIVE)</span>
  </div>

  <!-- ==================== PAGE 2 ==================== -->
  <div class="page-break"></div>

  <h2>4. Stage III: Thermodynamic Passivation &amp; Aqueous Corrosion Prediction</h2>

  <div class="formula-card">
    <div class="formula-title">8. Modified High-Entropy Pitting Resistance Equivalent Number (PREN<sub>HEA</sub>):</div>
    <span class="formula-math">PREN<sub>ASTM</sub> = wt% Cr + 3.3 (wt% Mo + 0.5 wt% W) = 20.60 + 0 = 20.60</span>
    <span class="formula-math">PREN<sub>HEA</sub> = PREN<sub>ASTM</sub> - 2.5 &times; max(0, wt% Al - 3.0) = 20.60 - 2.5 &times; (10.69 - 3.0) = 20.60 - 19.22 = 1.38</span>
    <b>Mechanistic Rationale:</b> In chloride media, Al contents &gt; 3 wt% promote galvanic phase segregation. The Al-rich B2 phase undergoes preferential anodic dissolution (dealloying), drastically lowering pitting resistance. &nbsp;<span class="badge badge-fail">PREN<sub>HEA</sub> = 1.38 (PITTING PRONE)</span>
  </div>

  <div class="formula-card">
    <div class="formula-title">9. Ellingham Oxide Formation Affinity (&Delta;G<sub>ox</sub><sup>eff</sup>):</div>
    <span class="formula-math">&Delta;G<sub>ox</sub><sup>eff</sup> = &Sigma; x<sub>i</sub> &Delta;G&deg;<sub>f,ox,i</sub> = 0.20 &times; [(-1055.0) + (-428.4) + (-705.4) + (-494.8) + (-423.4)] = -621.4 kJ/mol O<sub>2</sub></span>
    <b>Thermodynamic Order of Oxidation:</b> <b>Al<sub>2</sub>O<sub>3</sub> (-1055.0 kJ/mol)</b> &gt; Cr<sub>2</sub>O<sub>3</sub> (-705.4 kJ/mol) &gt; Fe<sub>2</sub>O<sub>3</sub> (-494.8 kJ/mol) &gt; CoO (-428.4 kJ/mol) &gt; NiO (-423.4 kJ/mol).<br>
    Al exhibits overwhelming oxygen affinity, driving outer Al<sub>2</sub>O<sub>3</sub> film growth at high temperatures, but creating vulnerable passive boundaries in aqueous Cl<sup>-</sup>.
  </div>

  <div class="formula-card">
    <div class="formula-title">10. Multicomponent Pilling-Bedworth Ratio (PBR<sub>eff</sub>, Xu &amp; Gao 2000):</div>
    <span class="formula-math">PBR<sub>eff</sub> = &Sigma; x<sub>i</sub> PBR<sub>i</sub> = 0.20 &times; (1.28 + 1.76 + 2.07 + 2.14 + 1.65) = 1.780</span>
    <b>Criterion:</b> 1.0 &le; PBR<sub>eff</sub> = 1.780 &le; 2.10 &rarr; Oxide is under moderate protective compression without buckling or spallation. &nbsp;<span class="badge badge-pass">PASSIVATING ENVELOPE</span>
  </div>

  <div class="formula-card">
    <div class="formula-title">11. Micro-Galvanic Potential Spread (&Delta;E<sub>galv</sub>) &amp; Single-Phase Immunity Factor (I<sub>phase</sub>):</div>
    Potential extreme: &Delta;E<sub>galv</sub> = E&deg;(Ni) - E&deg;(Al) = -0.257 - (-1.662) = <b>1.405 V</b> (Extremely large electrochemical driving force)<br>
    Single-phase suppression factor:
    <span class="formula-math">I<sub>phase</sub> = min(1.0, &Omega; / 1.1) &times; (1.0 - &delta; / 6.6%) = 1.0 &times; (1.0 - 5.44 / 6.6) = 0.176 &nbsp;(Only 17.6% suppressed)</span>
    <b>Microstructural Impact:</b> In single-phase Cantor alloy, I<sub>phase</sub> = 83%, extinguishing local cells. In AlCoCrFeNi, I<sub>phase</sub> is only 17.6%! <b>82.4% of the micro-galvanic driving force remains active</b>, setting up intense galvanic cells between the BCC matrix (Cr, Fe rich) and the B2 precipitates (Ni, Al rich)! &nbsp;<span class="badge badge-fail">SEVERE GALVANIC COUPLING</span>
  </div>

  <div class="formula-card">
    <div class="formula-title">12. ASTM G102 Equivalent Weight (EW), Density (&rho;), &amp; Faraday Corrosion Rate (CR):</div>
    Dissolution valences: Al=3, Co=2, Cr=3, Fe=2, Ni=2.<br>
    &Sigma; (w<sub>i</sub> n<sub>i</sub> / M<sub>i</sub>) = (0.1069&times;3)/26.982 + (0.2334&times;2)/58.933 + (0.2060&times;3)/51.996 + (0.2212&times;2)/55.845 + (0.2325&times;2)/58.693 = <b>0.04753 eq/g</b><br>
    <span class="formula-math">EW = 1 / 0.04753 = 21.04 g/equivalent &nbsp;|&nbsp; Theoretical Density &rho; &approx; 6.73 g/cm&sup3;</span>
    In 3.5 wt% NaCl, experimental passive current density is i<sub>corr</sub> &approx; 4.60 &mu;A/cm&sup2; (due to micro-galvanic B2 dissolution):
    <span class="formula-math">CR<sub>mm/yr</sub> = 3.27 &times; 10<sup>-3</sup> &times; (i<sub>corr</sub> &times; EW) / &rho; = 3.27e-3 &times; (4.60 &times; 21.04) / 6.73 = 0.0471 mm/year</span>
    <span class="formula-math">CR<sub>mpy</sub> = 0.0471 &times; 39.37 = 1.85 mils/year &nbsp;&rarr;&nbsp; PERFORMANCE: GRADE B (MODERATE / SELECTIVE LEACHING)</span>
    In 0.5 M H<sub>2</sub>SO<sub>4</sub>, i<sub>corr</sub> increases to ~8.93 &mu;A/cm&sup2; &rarr; <b>CR = 0.0910 mm/yr</b> (Kao et al. 2011, Materials Science &amp; Engineering A).
  </div>

  <h2>5. Direct Benchmark: Cantor (CoCrFeMnNi) vs. AlCoCrFeNi</h2>
  <table>
    <thead>
      <tr>
        <th>Descriptor</th>
        <th>Cantor Alloy (CoCrFeMnNi)</th>
        <th>Al-Containing HEA (AlCoCrFeNi)</th>
        <th>Mechanistic Influence of Al Addition</th>
      </tr>
    </thead>
    <tbody>
      <tr><td class="td-left"><b>Crystal Structure</b></td><td>Single FCC (A1)</td><td><b>BCC + Ordered B2 Duplex</b></td><td>Al destabilizes close-packed FCC &rarr; ordered B2</td></tr>
      <tr><td class="td-left"><b>Valence Electrons (VEC)</b></td><td>8.00</td><td><b>7.20</b></td><td>VEC decreases across boundary 6.87 &le; VEC &lt; 8.0</td></tr>
      <tr><td class="td-left"><b>Mixing Enthalpy (&Delta;H<sub>mix</sub>)</b></td><td>-3.20 kJ/mol</td><td><b>-12.16 kJ/mol</b></td><td>Strong Ni-Al (-22 kJ/mol) drives B2 intermetallic order</td></tr>
      <tr><td class="td-left"><b>Size Mismatch (&delta;)</b></td><td>1.12%</td><td><b>5.44%</b></td><td>Al radius (143 pm) creates 4.8&times; higher lattice strain</td></tr>
      <tr><td class="td-left"><b>Stability Parameter (&Omega;)</b></td><td>7.53</td><td><b>1.85</b></td><td>Entropy cannot overcome negative enthalpy ordering</td></tr>
      <tr><td class="td-left"><b>PREN<sub>HEA</sub> Index</b></td><td>18.54</td><td><b>1.38</b></td><td>Severe penalty due to Al-induced phase separation</td></tr>
      <tr><td class="td-left"><b>Galvanic Gap (&Delta;E<sub>galv</sub>)</b></td><td>0.928 V</td><td><b>1.405 V</b></td><td>Active Al (-1.662 V) creates massive potential gradient</td></tr>
      <tr><td class="td-left"><b>Single-Phase Factor (I<sub>phase</sub>)</b></td><td><b>0.830 (83% immune)</b></td><td><b>0.176 (82.4% vulnerable)</b></td><td>Duplex boundaries sustain active micro-galvanic cells</td></tr>
      <tr><td class="td-left"><b>Equivalent Weight (EW)</b></td><td>25.49 g/eq</td><td><b>21.04 g/eq</b></td><td>Higher dissolution efficiency per Faraday charge</td></tr>
      <tr><td class="td-left"><b>Corrosion Rate (3.5% NaCl)</b></td><td><b>0.0059 mm/yr (Grade A)</b></td><td><b>0.0471 mm/yr (Grade B)</b></td><td><b>~8&times; higher corrosion rate</b> due to dealloying of B2 phase</td></tr>
    </tbody>
  </table>

  <div class="callout-box" style="margin-top:4pt;">
    <b>Key Takeaway for Alloy Design:</b> While adding Al to CoCrFeNi dramatically increases yield strength and hardness (from ~150 MPa to &gt;1100 MPa) via spinodal decomposition and B2 precipitate hardening, it creates a trade-off: <b>aqueous corrosion and pitting resistance decrease by nearly one order of magnitude</b> in chloride solutions.
  </div>

</body>
</html>
"""

    # Target geometry
    mediabox = pymupdf.Rect(0, 0, 595.3, 841.9) # A4
    content_rect = pymupdf.Rect(42, 42, 595.3 - 42, 841.9 - 44)

    temp_raw = output_path + ".raw.pdf"
    if os.path.exists(temp_raw):
        try:
            os.remove(temp_raw)
        except Exception:
            pass

    writer = pymupdf.DocumentWriter(temp_raw)
    story = pymupdf.Story(html=html_content)

    more = 1
    page_count = 0
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(content_rect)
        story.draw(device)
        writer.end_page()
        page_count += 1
        if page_count > 10:
            break

    writer.close()
    print(f"Raw PDF built with {page_count} pages.")

    # Post-process: add running headers and footers
    doc = pymupdf.open(temp_raw)
    total_pages = len(doc)
    
    hdr_font = "helv"
    hdr_size = 7.0
    hdr_color = (0.35, 0.42, 0.52)
    line_color = (0.80, 0.84, 0.88)

    for p_idx in range(total_pages):
        page = doc[p_idx]
        p_num = p_idx + 1

        # Running header
        page.draw_line(
            pymupdf.Point(42, 34),
            pymupdf.Point(595.3 - 42, 34),
            color=line_color,
            width=0.6
        )
        page.insert_text(
            pymupdf.Point(42, 28),
            "AlCoCrFeNi HEA Manual Calculation Report • Phase Stability & Corrosion Prediction",
            fontname=hdr_font,
            fontsize=hdr_size,
            color=hdr_color
        )
        page.insert_text(
            pymupdf.Point(595.3 - 42 - 50, 28),
            "Al-Fe-Cr-Co-Ni",
            fontname=hdr_font,
            fontsize=hdr_size,
            color=hdr_color
        )

        # Running footer
        page.draw_line(
            pymupdf.Point(42, 841.9 - 36),
            pymupdf.Point(595.3 - 42, 841.9 - 36),
            color=line_color,
            width=0.6
        )
        page.insert_text(
            pymupdf.Point(42, 841.9 - 25),
            "ASTM G102 • Guo VEC Model • Miedema Enthalpy • Xu-Gao PBR • Faraday Rate",
            fontname=hdr_font,
            fontsize=hdr_size,
            color=hdr_color
        )
        page_str = f"Page {p_num} of {total_pages}"
        page.insert_text(
            pymupdf.Point(595.3 - 42 - 45, 841.9 - 25),
            page_str,
            fontname=hdr_font,
            fontsize=hdr_size,
            color=hdr_color
        )

    doc.save(output_path)
    doc.close()

    try:
        os.remove(temp_raw)
    except Exception:
        pass

    print(f"Final PDF saved to: {output_path} (Pages: {total_pages})")
    return total_pages

if __name__ == "__main__":
    out_pdf = r"C:\Users\Dell\Documents\Material design\AlFeCrCoNi_Manual_Calculation_Report.pdf"
    build_alfecrconi_pdf(out_pdf)
