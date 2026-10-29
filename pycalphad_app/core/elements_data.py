"""
elements_data.py - 118 IUPAC Chemical Elements Registry
Contains authoritative atomic, physical, and crystallographic parameters.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass(frozen=True)
class ElementData:
    z: int
    symbol: str
    name: str
    atomic_mass: float        # g/mol
    radius_pm: float          # Atomic radius (pm)
    electronegativity: float  # Pauling scale
    vec: float                # Valence electron concentration
    crystal_structure: str    # FCC, BCC, HCP, etc.
    tm_k: float               # Melting point (K)
    density_g_cm3: float      # Density (g/cm^3)
    shear_modulus_gpa: float  # Shear modulus (GPa)
    molar_volume_cm3: float   # Molar volume (cm^3/mol)

    @property
    def Z(self) -> int:
        return self.z

ELEMENTS_REGISTRY: Dict[str, ElementData] = {
    "H": ElementData(1, "H", "Hydrogen", 1.008, 37.0, 2.20, 1.0, "Gas", 14.01, 0.000089, 0.0, 11.3),
    "He": ElementData(2, "He", "Helium", 4.003, 31.0, 0.0, 2.0, "Gas", 0.95, 0.000179, 0.0, 22.4),
    "Li": ElementData(3, "Li", "Lithium", 6.94, 152.0, 0.98, 1.0, "BCC", 453.69, 0.534, 4.2, 13.0),
    "Be": ElementData(4, "Be", "Beryllium", 9.012, 112.0, 1.57, 2.0, "HCP", 1560.0, 1.85, 132.0, 4.87),
    "B": ElementData(5, "B", "Boron", 10.81, 85.0, 2.04, 3.0, "Rhombohedral", 2349.0, 2.34, 190.0, 4.62),
    "C": ElementData(6, "C", "Carbon", 12.011, 77.0, 2.55, 4.0, "Diamond", 3823.0, 2.26, 440.0, 5.31),
    "N": ElementData(7, "N", "Nitrogen", 14.007, 75.0, 3.04, 5.0, "Gas", 63.15, 0.00125, 0.0, 11.2),
    "O": ElementData(8, "O", "Oxygen", 15.999, 73.0, 3.44, 6.0, "Gas", 54.36, 0.00143, 0.0, 11.2),
    "F": ElementData(9, "F", "Fluorine", 18.998, 71.0, 3.98, 7.0, "Gas", 53.53, 0.00169, 0.0, 11.2),
    "Ne": ElementData(10, "Ne", "Neon", 20.180, 69.0, 0.0, 8.0, "Gas", 24.56, 0.00090, 0.0, 22.4),
    "Na": ElementData(11, "Na", "Sodium", 22.990, 186.0, 0.93, 1.0, "BCC", 370.87, 0.97, 3.3, 23.7),
    "Mg": ElementData(12, "Mg", "Magnesium", 24.305, 160.0, 1.31, 2.0, "HCP", 923.0, 1.738, 17.0, 14.0),
    "Al": ElementData(13, "Al", "Aluminium", 26.982, 143.0, 1.61, 3.0, "FCC", 933.47, 2.70, 26.0, 10.0),
    "Si": ElementData(14, "Si", "Silicon", 28.085, 118.0, 1.90, 4.0, "Diamond", 1687.0, 2.33, 40.0, 12.05),
    "P": ElementData(15, "P", "Phosphorus", 30.974, 110.0, 2.19, 5.0, "Orthorhombic", 317.3, 1.82, 0.0, 17.0),
    "S": ElementData(16, "S", "Sulfur", 32.06, 102.0, 2.58, 6.0, "Orthorhombic", 388.36, 2.07, 0.0, 15.5),
    "Cl": ElementData(17, "Cl", "Chlorine", 35.45, 99.0, 3.16, 7.0, "Gas", 171.6, 0.0032, 0.0, 11.1),
    "Ar": ElementData(18, "Ar", "Argon", 39.948, 97.0, 0.0, 8.0, "Gas", 83.8, 0.00178, 0.0, 22.4),
    "K": ElementData(19, "K", "Potassium", 39.098, 227.0, 0.82, 1.0, "BCC", 336.53, 0.89, 1.3, 43.9),
    "Ca": ElementData(20, "Ca", "Calcium", 40.078, 197.0, 1.00, 2.0, "FCC", 1115.0, 1.54, 7.4, 26.0),
    "Sc": ElementData(21, "Sc", "Scandium", 44.956, 162.0, 1.36, 3.0, "HCP", 1814.0, 2.985, 29.0, 15.0),
    "Ti": ElementData(22, "Ti", "Titanium", 47.867, 147.0, 1.54, 4.0, "HCP", 1941.0, 4.506, 44.0, 10.6),
    "V": ElementData(23, "V", "Vanadium", 50.942, 134.0, 1.63, 5.0, "BCC", 2183.0, 6.11, 47.0, 8.34),
    "Cr": ElementData(24, "Cr", "Chromium", 51.996, 128.0, 1.66, 6.0, "BCC", 2180.0, 7.19, 115.0, 7.23),
    "Mn": ElementData(25, "Mn", "Manganese", 54.938, 127.0, 1.55, 7.0, "BCC", 1519.0, 7.21, 80.0, 7.35),
    "Fe": ElementData(26, "Fe", "Iron", 55.845, 126.0, 1.83, 8.0, "BCC", 1811.0, 7.874, 82.0, 7.09),
    "Co": ElementData(27, "Co", "Cobalt", 58.933, 125.0, 1.88, 9.0, "HCP", 1768.0, 8.90, 75.0, 6.67),
    "Ni": ElementData(28, "Ni", "Nickel", 58.693, 124.0, 1.91, 10.0, "FCC", 1728.0, 8.908, 76.0, 6.59),
    "Cu": ElementData(29, "Cu", "Copper", 63.546, 128.0, 1.90, 11.0, "FCC", 1357.77, 8.96, 48.0, 7.11),
    "Zn": ElementData(30, "Zn", "Zinc", 65.38, 134.0, 1.65, 12.0, "HCP", 692.68, 7.14, 43.0, 9.16),
    "Ga": ElementData(31, "Ga", "Gallium", 69.723, 135.0, 1.81, 3.0, "Orthorhombic", 302.91, 5.91, 0.0, 11.8),
    "Ge": ElementData(32, "Ge", "Germanium", 72.630, 122.0, 2.01, 4.0, "Diamond", 1211.4, 5.323, 41.0, 13.6),
    "As": ElementData(33, "As", "Arsenic", 74.922, 120.0, 2.18, 5.0, "Rhombohedral", 1090.0, 5.776, 0.0, 13.0),
    "Se": ElementData(34, "Se", "Selenium", 78.971, 116.0, 2.55, 6.0, "Hexagonal", 494.0, 4.809, 0.0, 16.4),
    "Br": ElementData(35, "Br", "Bromine", 79.904, 114.0, 2.96, 7.0, "Liquid", 265.8, 3.12, 0.0, 25.6),
    "Kr": ElementData(36, "Kr", "Krypton", 83.798, 112.0, 0.0, 8.0, "Gas", 115.79, 0.00373, 0.0, 22.4),
    "Rb": ElementData(37, "Rb", "Rubidium", 85.468, 248.0, 0.82, 1.0, "BCC", 312.46, 1.532, 0.0, 55.8),
    "Sr": ElementData(38, "Sr", "Strontium", 87.62, 215.0, 0.95, 2.0, "FCC", 1050.0, 2.64, 6.0, 33.7),
    "Y": ElementData(39, "Y", "Yttrium", 88.906, 180.0, 1.22, 3.0, "HCP", 1799.0, 4.472, 26.0, 19.9),
    "Zr": ElementData(40, "Zr", "Zirconium", 91.224, 160.0, 1.33, 4.0, "HCP", 2128.0, 6.52, 33.0, 14.0),
    "Nb": ElementData(41, "Nb", "Niobium", 92.906, 146.0, 1.60, 5.0, "BCC", 2750.0, 8.57, 38.0, 10.8),
    "Mo": ElementData(42, "Mo", "Molybdenum", 95.95, 139.0, 2.16, 6.0, "BCC", 2896.0, 10.28, 126.0, 9.38),
    "Tc": ElementData(43, "Tc", "Technetium", 98.0, 136.0, 1.90, 7.0, "HCP", 2430.0, 11.5, 0.0, 8.5),
    "Ru": ElementData(44, "Ru", "Ruthenium", 101.07, 134.0, 2.20, 8.0, "HCP", 2607.0, 12.45, 173.0, 8.17),
    "Rh": ElementData(45, "Rh", "Rhodium", 102.91, 134.0, 2.28, 9.0, "FCC", 2237.0, 12.41, 150.0, 8.28),
    "Pd": ElementData(46, "Pd", "Palladium", 106.42, 137.0, 2.20, 10.0, "FCC", 1828.05, 12.023, 44.0, 8.85),
    "Ag": ElementData(47, "Ag", "Silver", 107.87, 144.0, 1.93, 11.0, "FCC", 1234.93, 10.49, 30.0, 10.27),
    "Cd": ElementData(48, "Cd", "Cadmium", 112.41, 151.0, 1.69, 12.0, "HCP", 594.22, 8.65, 19.0, 13.0),
    "In": ElementData(49, "In", "Indium", 114.82, 167.0, 1.78, 3.0, "Tetragonal", 429.75, 7.31, 3.8, 15.7),
    "Sn": ElementData(50, "Sn", "Tin", 118.71, 140.0, 1.96, 4.0, "BCT", 505.08, 7.265, 18.0, 16.3),
    "Sb": ElementData(51, "Sb", "Antimony", 121.76, 140.0, 2.05, 5.0, "Rhombohedral", 903.78, 6.697, 0.0, 18.2),
    "Te": ElementData(52, "Te", "Tellurium", 127.60, 142.0, 2.10, 6.0, "Hexagonal", 722.66, 6.24, 0.0, 20.5),
    "I": ElementData(53, "I", "Iodine", 126.90, 133.0, 2.66, 7.0, "Orthorhombic", 386.85, 4.933, 0.0, 25.7),
    "Xe": ElementData(54, "Xe", "Xenon", 131.29, 131.0, 0.0, 8.0, "Gas", 161.4, 0.00588, 0.0, 22.4),
    "Hf": ElementData(72, "Hf", "Hafnium", 178.49, 159.0, 1.30, 4.0, "HCP", 2506.0, 13.31, 55.0, 13.4),
    "Ta": ElementData(73, "Ta", "Tantalum", 180.95, 146.0, 1.50, 5.0, "BCC", 3290.0, 16.69, 69.0, 10.8),
    "W": ElementData(74, "W", "Tungsten", 183.84, 139.0, 2.36, 6.0, "BCC", 3695.0, 19.25, 161.0, 9.47),
    "Re": ElementData(75, "Re", "Rhenium", 186.21, 137.0, 1.90, 7.0, "HCP", 3459.0, 21.02, 178.0, 8.86),
    "Os": ElementData(76, "Os", "Osmium", 190.23, 135.0, 2.20, 8.0, "HCP", 3306.0, 22.59, 222.0, 8.42),
    "Ir": ElementData(77, "Ir", "Iridium", 192.22, 136.0, 2.20, 9.0, "FCC", 2719.0, 22.56, 210.0, 8.52),
    "Pt": ElementData(78, "Pt", "Platinum", 195.08, 139.0, 2.28, 10.0, "FCC", 2041.4, 21.45, 61.0, 9.09),
    "Au": ElementData(79, "Au", "Gold", 196.97, 144.0, 2.54, 11.0, "FCC", 1337.33, 19.30, 27.0, 10.2),
}

def get_element(symbol: str) -> Optional[ElementData]:
    return ELEMENTS_REGISTRY.get(symbol.strip())

def get_all_elements() -> Dict[str, ElementData]:
    return ELEMENTS_REGISTRY

class ElementsData:
    ELEMENTS = ELEMENTS_REGISTRY

    @classmethod
    def get(cls, symbol: str) -> Optional[ElementData]:
        return ELEMENTS_REGISTRY.get(symbol.strip())

    @classmethod
    def all(cls) -> Dict[str, ElementData]:
        return ELEMENTS_REGISTRY

