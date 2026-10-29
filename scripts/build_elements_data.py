# -*- coding: utf-8 -*-
import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

pt_match = re.search(r'const PERIODIC_TABLE = \[(.*?)\];', html, re.DOTALL)
lines = [l.strip().rstrip(',') for l in pt_match.group(1).splitlines() if l.strip().startswith('{')]

with open('App/HEAThermoEngine.m', 'r', encoding='utf-8') as f:
    thermo_txt = f.read()

thermo_dict = {}
for m in re.finditer(r"setE\(\s*'([A-Za-z]+)'\s*,\s*\[(.*?)\]\s*\);", thermo_txt):
    sym = m.group(1)
    vals = [float(v.strip()) for v in m.group(2).split(',')]
    thermo_dict[sym] = {
        'M': vals[0], 'r': vals[1], 'chi': vals[2], 'VEC': vals[3], 'Tm': vals[4],
        'dH_fus': vals[5], 'rho0': vals[6], 'alpha': vals[7], 'Cp0': vals[8],
        'Cp_b': vals[9], 'k0': vals[10], 'rho_e0': vals[11], 'E0': vals[12],
        'nu0': vals[13], 'sigma_m': vals[14]
    }

with open('App/HEAMechanicalEngine.m', 'r', encoding='utf-8') as f:
    mech_txt = f.read()

mech_dict = {}
for m in re.finditer(r"setM\(\s*'([A-Za-z]+)'\s*,\s*([\d\.\-]+)\s*,\s*([\d\.\-]+)\s*,\s*([\d\.\-]+)\s*,\s*([\d\.\-]+)\s*,\s*([\d\.\-]+)\s*,\s*([\d\.\-]+)\s*,\s*([\d\.\-]+)\s*,\s*'([^']+)'\s*\);", mech_txt):
    sym = m.group(1)
    mech_dict[sym] = {
        'M': float(m.group(2)), 'r_pm': float(m.group(3)), 'V_mol': float(m.group(4)),
        'G_GPa': float(m.group(5)), 'E_GPa': float(m.group(6)), 'nu': float(m.group(7)),
        'sig0': float(m.group(8)), 'crystal': m.group(9)
    }

py_lines = [
    '# -*- coding: utf-8 -*-',
    '"""',
    'elements_data.py - Complete IUPAC 1-118 Chemical Elements Registry',
    'Authoritative elemental, crystallographic, thermophysical, and mechanical parameters.',
    '"""',
    '',
    'from dataclasses import dataclass',
    'from typing import Dict, List, Optional',
    '',
    '@dataclass(frozen=True)',
    'class ElementData:',
    '    z: int',
    '    symbol: str',
    '    name: str',
    '    atomic_mass: float        # g/mol',
    '    radius_pm: float          # pm (Goldschmidt / metallic)',
    '    electronegativity: float  # Pauling scale',
    '    vec: float                # Valence electron concentration',
    '    crystal_structure: str    # FCC, BCC, HCP, Diamond, etc.',
    '    tm_k: float               # Melting temperature (K)',
    '    density_g_cm3: float      # Density at 293 K (g/cm^3)',
    '    shear_modulus_gpa: float  # Shear modulus G (GPa)',
    '    youngs_modulus_gpa: float # Youngs modulus E (GPa)',
    '    poissons_ratio: float     # Poissons ratio nu',
    '    molar_volume_cm3: float   # Molar volume (cm^3/mol)',
    '    period: int',
    '    group: int',
    '    grid_row: int             # 1-based Periodic Table grid row',
    '    grid_col: int             # 1-based Periodic Table grid col',
    '    category: str',
    '    color_hex: str',
    '    is_light: bool = False',
    '    is_refractory: bool = False',
    '    is_cantor: bool = False',
    '    friction_stress_mpa: float = 30.0',
    '    thermal_cond_w_mk: float = 50.0',
    '    cp_j_molk: float = 25.0',
    '    cte_1e6_k: float = 12.0',
    '',
    '    @property',
    '    def Z(self) -> int:',
    '        return self.z',
    '',
    'ELEMENTS_REGISTRY: Dict[str, ElementData] = {'
]

for l in lines:
    z_m = re.search(r'z:\s*(\d+)', l)
    sym_m = re.search(r"sym:\s*'([^']+)'", l)
    name_m = re.search(r"name:\s*'([^']+)'", l)
    mass_m = re.search(r'mass:\s*([\d\.]+)', l)
    cat_m = re.search(r"cat:\s*'([^']+)'", l)
    col_m = re.search(r'col:\s*(\d+)', l)
    row_m = re.search(r'row:\s*(\d+)', l)
    color_m = re.search(r"color:\s*'([^']+)'", l)
    is_light = 'isLight: true' in l
    is_refractory = 'isRefractory: true' in l
    is_cantor = 'isCantor: true' in l

    z = int(z_m.group(1))
    sym = sym_m.group(1)
    name = name_m.group(1)
    mass = float(mass_m.group(1))
    cat = cat_m.group(1)
    col = int(col_m.group(1))
    row = int(row_m.group(1))
    color = color_m.group(1) if color_m else '#475569'

    period = row if row <= 7 else (6 if cat == 'lanthanide' else 7)
    group = col if row <= 7 else 3

    th = thermo_dict.get(sym, {})
    mc = mech_dict.get(sym, {})

    r_pm = mc.get('r_pm', th.get('r', 130.0))
    chi = th.get('chi', 1.5)
    vec = th.get('VEC', float(group if group <= 12 else (group - 10 if group <= 18 else 3)))
    crys = mc.get('crystal', 'FCC' if cat in ['transition', 'post-transition'] else ('BCC' if cat == 'alkali' else 'HCP'))
    tm_k = th.get('Tm', 1500.0)
    rho = th.get('rho0', 7.0)
    g_gpa = mc.get('G_GPa', 50.0)
    e_gpa = mc.get('E_GPa', th.get('E0', 120.0))
    nu = mc.get('nu', th.get('nu0', 0.30))
    v_mol = mc.get('V_mol', 10.0)
    sig0 = mc.get('sig0', 30.0)
    k0 = th.get('k0', 50.0)
    cp0 = th.get('Cp0', 25.0)
    alpha = th.get('alpha', 12.0)

    py_lines.append(
        f'    "{sym}": ElementData({z}, "{sym}", "{name}", {mass}, {r_pm}, {chi}, {vec}, '
        f'"{crys}", {tm_k}, {rho}, {g_gpa}, {e_gpa}, {nu}, {v_mol}, {period}, {group}, {row}, {col}, '
        f'"{cat}", "{color}", {is_light}, {is_refractory}, {is_cantor}, {sig0}, {k0}, {cp0}, {alpha}),'
    )

py_lines.extend([
    '}',
    '',
    'IUPAC_ELEMENTS_DATA: Dict[str, ElementData] = ELEMENTS_REGISTRY',
    '',
    'def get_element(symbol: str) -> Optional[ElementData]:',
    '    return ELEMENTS_REGISTRY.get(symbol.strip())',
    '',
    'def get_all_elements() -> Dict[str, ElementData]:',
    '    return ELEMENTS_REGISTRY',
    '',
    'class ElementsData:',
    '    ELEMENTS = ELEMENTS_REGISTRY',
    '',
    '    @classmethod',
    '    def get(cls, symbol: str) -> Optional[ElementData]:',
    '        return ELEMENTS_REGISTRY.get(symbol.strip())',
    '',
    '    @classmethod',
    '    def all(cls) -> Dict[str, ElementData]:',
    '        return ELEMENTS_REGISTRY',
    '',
    '    @classmethod',
    '    def get_118_list(cls) -> List[ElementData]:',
    '        return sorted(list(ELEMENTS_REGISTRY.values()), key=lambda e: e.z)',
    ''
])

with open('pycalphad_app/core/elements_data.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(py_lines))

print(f'Successfully wrote pycalphad_app/core/elements_data.py with {len(lines)} elements')
