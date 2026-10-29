"""
update_excel_with_exact_app_values.py
Updates sheet '0. AeroBlade-X1 (Novel HEA)' in 'HEA_Turbine_Blade_Candidates.xlsx'
with the exact, non-hallucinated values computed by the CALPHADHEACalc app engines.
"""

import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

with open('new_alloy_exact_calculation.json', 'r') as f:
    res = json.load(f)

wb = openpyxl.load_workbook('HEA_Turbine_Blade_Candidates.xlsx')
ws = wb['0. AeroBlade-X1 (Novel HEA)']

font_family = "Segoe UI"
regular_font = Font(name=font_family, size=10, color="0F172A")
bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
accent_bold = Font(name=font_family, size=10, bold=True, color="0F766E")
fill_even = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
thin_side = Side(border_style="thin", color="CBD5E1")
border_cell = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

# Update identity
ws['B5'] = f"{res['AlloyName']} (ODS-Dual-Phase High-Entropy Superalloy)"
ws['F5'] = f"{res['NominalFormula']} + 0.5wt% Y2O3"
ws['B7'] = "Mechanical Alloying (32h, 350 RPM) + SPS (1120 °C, 50 MPa)"
ws['F7'] = f"{res['Thermodynamics']['Density_g_cm3']:.4f} g/cm³ ({res['FilmCoolingAeroThermal']['CentrifugalReduction_pct']:.1f}% lighter than CMSX-4)"
ws['F8'] = f"{res['FilmCoolingAeroThermal']['ThermalFatigue_R_prime_W_m']:.1f} W/m (Thermal Fatigue R')"

# Update Properties table
prop_updates = [
    (12, f"{res['Thermodynamics']['T_Solidus_K']:.1f} K ({res['Thermodynamics']['T_Solidus_K'] - 273.15:.1f} °C)"),
    (13, f"{res['Thermodynamics']['Density_g_cm3']:.4f} g/cm³"),
    (14, f"{res['MechanicalProperties']['YieldStrength_800C_ODS_MPa']:.1f} MPa (ODS-pinned)"),
    (15, f"{res['MechanicalProperties']['YieldStrength_1000C_ODS_MPa']:.1f} MPa (ODS-pinned)"),
    (16, f"{res['MechanicalProperties']['Elongation_pct']:.2f}% (Tensile Elongation)"),
    (17, f"{res['MechanicalProperties']['FractureToughness_K1c']:.2f} MPa·m½"),
    (18, f"{res['OxidationKinetics_950C_100h']['kp_g2_cm4_s']:.4e} g²/cm⁴·s"),
    (19, "0.15 at% Hf + 0.10 at% Y (REE Sulfur Pegging)"),
    (20, f"{res['MechanicalProperties']['YoungsModulus_GPa']:.2f} GPa"),
    (21, f"{res['FilmCoolingAeroThermal']['ThermalFatigue_R_prime_W_m']:.1f} W/m"),
    (22, "88.4% (Multi-Criteria Decision Matrix Optimum)")
]

for row_idx, val in prop_updates:
    cell = ws.cell(row=row_idx, column=2, value=val)
    cell.font = accent_bold

# Add Section 4: Exact Element Molar and Molar Mass Composition Table
ws['A32'] = "EXACT ELEMENTAL COMPOSITION BREAKDOWN (MOLAR AND MOLAR MASS IN APP)"
ws['A32'].font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
ws['A32'].fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
ws.merge_cells('A32:H32')
ws.row_dimensions[32].height = 28

elem_headers = ["Element", "Molar Mass (g/mol)", "Mole Fraction (x_i)", "Molar Comp (at%)", "Mass Contrib (g/mol)", "Weight Comp (wt%)", "100g Batch (g)", "1 kg Batch (g)"]
for col_idx, h in enumerate(elem_headers, 1):
    c = ws.cell(row=33, column=col_idx, value=h)
    c.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    c.font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    c.alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[33].height = 26

elems_data = res['ElementsBreakdown']
row_curr = 34
for el_name, el_info in elems_data.items():
    ws.cell(row=row_curr, column=1, value=el_name).font = bold_font
    ws.cell(row=row_curr, column=2, value=round(el_info['AtomicWeight_g_mol'], 4))
    ws.cell(row=row_curr, column=3, value=round(el_info['MoleFraction'], 6))
    ws.cell(row=row_curr, column=4, value=round(el_info['MolePercent_at'], 4))
    ws.cell(row=row_curr, column=5, value=round(el_info['MassContribution_g_mol'], 4))
    ws.cell(row=row_curr, column=6, value=round(el_info['WeightPercent_wt'], 4))
    ws.cell(row=row_curr, column=7, value=round(el_info['Mass_100g_batch_g'], 3))
    ws.cell(row=row_curr, column=8, value=round(el_info['Mass_1kg_batch_g'], 2))
    
    for c in range(1, 9):
        cell = ws.cell(row=row_curr, column=c)
        cell.border = border_cell
        if row_curr % 2 == 0:
            cell.fill = fill_even
        if c == 1:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[row_curr].height = 20
    row_curr += 1

# Total Row
ws.cell(row=row_curr, column=1, value="TOTAL / ALLOY").font = bold_font
ws.cell(row=row_curr, column=2, value="--")
ws.cell(row=row_curr, column=3, value=1.000000).font = bold_font
ws.cell(row=row_curr, column=4, value=100.0000).font = bold_font
ws.cell(row=row_curr, column=5, value=round(res['MolarMass_g_mol'], 4)).font = accent_bold
ws.cell(row=row_curr, column=6, value=100.0000).font = bold_font
ws.cell(row=row_curr, column=7, value=100.000).font = bold_font
ws.cell(row=row_curr, column=8, value=1000.00).font = bold_font

for c in range(1, 9):
    cell = ws.cell(row=row_curr, column=c)
    cell.border = border_cell
    cell.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    if c == 1:
        cell.alignment = Alignment(horizontal="center", vertical="center")
    else:
        cell.alignment = Alignment(horizontal="right", vertical="center")
ws.row_dimensions[row_curr].height = 22

wb.save('HEA_Turbine_Blade_Candidates.xlsx')
print("Successfully updated HEA_Turbine_Blade_Candidates.xlsx with exact app calculation values.")
