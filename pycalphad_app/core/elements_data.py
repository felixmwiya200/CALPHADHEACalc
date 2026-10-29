# -*- coding: utf-8 -*-
"""
elements_data.py - Complete IUPAC 1-118 Chemical Elements Registry
Authoritative elemental, crystallographic, thermophysical, and mechanical parameters.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass(frozen=True)
class ElementData:
    z: int
    symbol: str
    name: str
    atomic_mass: float        # g/mol
    radius_pm: float          # pm (Goldschmidt / metallic)
    electronegativity: float  # Pauling scale
    vec: float                # Valence electron concentration
    crystal_structure: str    # FCC, BCC, HCP, Diamond, etc.
    tm_k: float               # Melting temperature (K)
    density_g_cm3: float      # Density at 293 K (g/cm^3)
    shear_modulus_gpa: float  # Shear modulus G (GPa)
    youngs_modulus_gpa: float # Youngs modulus E (GPa)
    poissons_ratio: float     # Poissons ratio nu
    molar_volume_cm3: float   # Molar volume (cm^3/mol)
    period: int
    group: int
    grid_row: int             # 1-based Periodic Table grid row
    grid_col: int             # 1-based Periodic Table grid col
    category: str
    color_hex: str
    is_light: bool = False
    is_refractory: bool = False
    is_cantor: bool = False
    friction_stress_mpa: float = 30.0
    thermal_cond_w_mk: float = 50.0
    cp_j_molk: float = 25.0
    cte_1e6_k: float = 12.0

    @property
    def Z(self) -> int:
        return self.z

ELEMENTS_REGISTRY: Dict[str, ElementData] = {
    "H": ElementData(1, "H", "Hydrogen", 1.008, 130.0, 1.5, 1.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 1, 1, 1, 1, "nonmetal", "#3B82F6", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "He": ElementData(2, "He", "Helium", 4.003, 130.0, 1.5, 8.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 1, 18, 1, 18, "noble", "#9CA3AF", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Li": ElementData(3, "Li", "Lithium", 6.94, 152.0, 0.98, 1.0, "BCC", 454.0, 0.534, 4.2, 4.9, 0.36, 13.02, 2, 1, 2, 1, "alkali", "#EF4444", False, False, False, 15.0, 85.0, 24.8, 46.0),
    "Be": ElementData(4, "Be", "Beryllium", 9.012, 112.0, 1.57, 2.0, "HCP", 1560.0, 1.85, 132.0, 287.0, 0.03, 4.85, 2, 2, 2, 2, "alkaline-earth", "#F59E0B", True, False, False, 120.0, 200.0, 16.4, 11.3),
    "B": ElementData(5, "B", "Boron", 10.81, 82.0, 2.04, 3.0, "RHOMB", 2349.0, 2.34, 172.0, 400.0, 0.13, 4.6, 2, 13, 2, 13, "metalloid", "#10B981", False, False, False, 1200.0, 27.0, 11.1, 6.0),
    "C": ElementData(6, "C", "Carbon", 12.011, 77.0, 2.55, 4.0, "HEX", 3823.0, 2.26, 190.0, 450.0, 0.17, 5.3, 2, 14, 2, 14, "nonmetal", "#374151", False, False, False, 1500.0, 129.0, 8.5, 7.1),
    "N": ElementData(7, "N", "Nitrogen", 14.007, 75.0, 3.04, 5.0, "MOL", 63.0, 1.026, 5.0, 10.0, 0.3, 13.7, 2, 15, 2, 15, "nonmetal", "#6366F1", False, False, False, 200.0, 0.1, 29.1, 10.0),
    "O": ElementData(8, "O", "Oxygen", 15.999, 73.0, 1.5, 6.0, "MOL", 1500.0, 7.0, 5.0, 10.0, 0.3, 14.0, 2, 16, 2, 16, "nonmetal", "#06B6D4", False, False, False, 200.0, 50.0, 25.0, 12.0),
    "F": ElementData(9, "F", "Fluorine", 18.998, 130.0, 1.5, 7.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 2, 17, 2, 17, "nonmetal", "#14B8A6", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Ne": ElementData(10, "Ne", "Neon", 20.18, 130.0, 1.5, 8.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 2, 18, 2, 18, "noble", "#9CA3AF", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Na": ElementData(11, "Na", "Sodium", 22.99, 130.0, 1.5, 1.0, "BCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 3, 1, 3, 1, "alkali", "#EF4444", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Mg": ElementData(12, "Mg", "Magnesium", 24.305, 160.0, 1.31, 2.0, "HCP", 923.0, 1.738, 17.0, 45.0, 0.29, 14.0, 3, 2, 3, 2, "alkaline-earth", "#F59E0B", True, False, False, 20.0, 156.0, 24.9, 24.8),
    "Al": ElementData(13, "Al", "Aluminium", 26.982, 143.0, 1.61, 3.0, "FCC", 933.0, 2.7, 26.0, 70.0, 0.35, 10.0, 3, 13, 3, 13, "post-transition", "#3B82F6", True, False, False, 20.0, 237.0, 24.3, 23.1),
    "Si": ElementData(14, "Si", "Silicon", 28.085, 118.0, 1.9, 4.0, "DIA", 1687.0, 2.329, 40.0, 113.0, 0.28, 12.06, 3, 14, 3, 14, "metalloid", "#0EA5E9", True, False, False, 500.0, 149.0, 20.0, 2.6),
    "P": ElementData(15, "P", "Phosphorus", 30.974, 130.0, 1.5, 5.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 3, 15, 3, 15, "nonmetal", "#8B5CF6", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "S": ElementData(16, "S", "Sulfur", 32.06, 130.0, 1.5, 6.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 3, 16, 3, 16, "nonmetal", "#EC4899", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Cl": ElementData(17, "Cl", "Chlorine", 35.45, 130.0, 1.5, 7.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 3, 17, 3, 17, "nonmetal", "#14B8A6", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Ar": ElementData(18, "Ar", "Argon", 39.948, 130.0, 1.5, 8.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 3, 18, 3, 18, "noble", "#9CA3AF", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "K": ElementData(19, "K", "Potassium", 39.098, 130.0, 1.5, 1.0, "BCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 4, 1, 4, 1, "alkali", "#EF4444", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Ca": ElementData(20, "Ca", "Calcium", 40.078, 197.0, 1.0, 2.0, "FCC", 1115.0, 1.55, 7.4, 20.0, 0.31, 26.2, 4, 2, 4, 2, "alkaline-earth", "#F59E0B", False, False, False, 12.0, 201.0, 25.9, 22.3),
    "Sc": ElementData(21, "Sc", "Scandium", 44.956, 162.0, 1.36, 3.0, "HCP", 1814.0, 2.985, 29.0, 74.0, 0.28, 15.0, 4, 3, 4, 3, "transition", "#8B5CF6", True, False, False, 35.0, 15.8, 25.5, 10.2),
    "Ti": ElementData(22, "Ti", "Titanium", 47.867, 147.0, 1.54, 4.0, "HCP", 1941.0, 4.506, 44.0, 116.0, 0.32, 10.64, 4, 4, 4, 4, "transition", "#8B5CF6", True, True, False, 120.0, 21.9, 25.0, 8.6),
    "V": ElementData(23, "V", "Vanadium", 50.942, 134.0, 1.63, 5.0, "BCC", 2183.0, 6.11, 47.0, 128.0, 0.37, 8.32, 4, 5, 4, 5, "transition", "#DB2777", False, True, False, 200.0, 30.7, 24.9, 8.4),
    "Cr": ElementData(24, "Cr", "Chromium", 51.996, 128.0, 1.66, 6.0, "BCC", 2180.0, 7.19, 115.0, 279.0, 0.21, 7.23, 4, 6, 4, 6, "transition", "#A855F7", False, True, True, 280.0, 93.9, 23.3, 4.9),
    "Mn": ElementData(25, "Mn", "Manganese", 54.938, 127.0, 1.55, 7.0, "BCC", 1519.0, 7.44, 79.0, 198.0, 0.26, 7.35, 4, 7, 4, 7, "transition", "#06B6D4", False, False, True, 70.0, 7.8, 26.3, 21.7),
    "Fe": ElementData(26, "Fe", "Iron", 55.845, 126.0, 1.83, 8.0, "BCC", 1811.0, 7.874, 82.0, 211.0, 0.29, 7.09, 4, 8, 4, 8, "transition", "#EF4444", False, False, True, 50.0, 80.4, 25.1, 11.8),
    "Co": ElementData(27, "Co", "Cobalt", 58.933, 125.0, 1.88, 9.0, "HCP", 1768.0, 8.9, 83.0, 209.0, 0.31, 6.62, 4, 9, 4, 9, "transition", "#F97316", False, False, True, 45.0, 100.0, 24.8, 13.0),
    "Ni": ElementData(28, "Ni", "Nickel", 58.693, 124.0, 1.91, 10.0, "FCC", 1728.0, 8.908, 76.0, 200.0, 0.31, 6.59, 4, 10, 4, 10, "transition", "#22C55E", False, False, True, 30.0, 90.9, 26.1, 13.4),
    "Cu": ElementData(29, "Cu", "Copper", 63.546, 128.0, 1.9, 11.0, "FCC", 1358.0, 8.96, 48.0, 130.0, 0.34, 7.11, 4, 11, 4, 11, "transition", "#D97706", False, False, False, 25.0, 401.0, 24.4, 16.5),
    "Zn": ElementData(30, "Zn", "Zinc", 65.38, 134.0, 1.65, 12.0, "HCP", 693.0, 7.14, 43.0, 108.0, 0.25, 9.16, 4, 12, 4, 12, "transition", "#14B8A6", False, False, False, 35.0, 116.0, 25.4, 30.2),
    "Ga": ElementData(31, "Ga", "Gallium", 69.723, 135.0, 1.81, 3.0, "ORTHO", 303.0, 5.91, 11.0, 30.0, 0.35, 11.8, 4, 13, 4, 13, "post-transition", "#3B82F6", False, False, False, 20.0, 40.6, 25.9, 18.0),
    "Ge": ElementData(32, "Ge", "Germanium", 72.63, 122.0, 2.01, 4.0, "DIA", 1211.0, 5.323, 41.0, 103.0, 0.26, 13.63, 4, 14, 4, 14, "metalloid", "#0EA5E9", False, False, False, 450.0, 60.2, 23.3, 6.0),
    "As": ElementData(33, "As", "Arsenic", 74.922, 130.0, 1.5, 5.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 4, 15, 4, 15, "metalloid", "#8B5CF6", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Se": ElementData(34, "Se", "Selenium", 78.971, 130.0, 1.5, 6.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 4, 16, 4, 16, "nonmetal", "#EC4899", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Br": ElementData(35, "Br", "Bromine", 79.904, 130.0, 1.5, 7.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 4, 17, 4, 17, "nonmetal", "#F43F5E", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Kr": ElementData(36, "Kr", "Krypton", 83.798, 130.0, 1.5, 8.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 4, 18, 4, 18, "noble", "#9CA3AF", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Rb": ElementData(37, "Rb", "Rubidium", 85.468, 130.0, 1.5, 1.0, "BCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 5, 1, 5, 1, "alkali", "#EF4444", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Sr": ElementData(38, "Sr", "Strontium", 87.62, 215.0, 0.95, 2.0, "FCC", 1050.0, 2.64, 6.0, 16.0, 0.28, 33.94, 5, 2, 5, 2, "alkaline-earth", "#F59E0B", False, False, False, 10.0, 35.4, 26.8, 22.5),
    "Y": ElementData(39, "Y", "Yttrium", 88.906, 180.0, 1.22, 3.0, "HCP", 1799.0, 4.472, 26.0, 64.0, 0.24, 19.88, 5, 3, 5, 3, "transition", "#8B5CF6", False, False, False, 40.0, 17.2, 26.5, 10.6),
    "Zr": ElementData(40, "Zr", "Zirconium", 91.224, 160.0, 1.33, 4.0, "HCP", 2128.0, 6.52, 33.0, 68.0, 0.34, 14.02, 5, 4, 5, 4, "transition", "#EC4899", False, True, False, 95.0, 22.6, 25.4, 5.7),
    "Nb": ElementData(41, "Nb", "Niobium", 92.906, 146.0, 1.6, 5.0, "BCC", 2750.0, 8.57, 38.0, 105.0, 0.4, 10.83, 5, 5, 5, 5, "transition", "#059669", False, True, False, 140.0, 53.7, 24.6, 7.3),
    "Mo": ElementData(42, "Mo", "Molybdenum", 95.95, 139.0, 2.16, 6.0, "BCC", 2896.0, 10.28, 126.0, 329.0, 0.31, 9.38, 5, 6, 5, 6, "transition", "#64748B", False, True, False, 320.0, 138.0, 24.1, 4.8),
    "Tc": ElementData(43, "Tc", "Technetium", 98.0, 136.0, 1.9, 7.0, "FCC", 2430.0, 11.0, 50.0, 310.0, 0.31, 10.0, 5, 7, 5, 7, "transition", "#0284C7", False, False, False, 30.0, 50.6, 24.3, 7.1),
    "Ru": ElementData(44, "Ru", "Ruthenium", 101.07, 134.0, 2.2, 8.0, "HCP", 2607.0, 12.45, 173.0, 447.0, 0.3, 8.17, 5, 8, 5, 8, "transition", "#7C3AED", False, False, False, 180.0, 117.0, 24.1, 6.4),
    "Rh": ElementData(45, "Rh", "Rhodium", 102.91, 134.0, 2.28, 9.0, "FCC", 2237.0, 12.41, 150.0, 380.0, 0.26, 8.28, 5, 9, 5, 9, "transition", "#D97706", False, False, False, 120.0, 150.0, 25.0, 8.2),
    "Pd": ElementData(46, "Pd", "Palladium", 106.42, 137.0, 2.2, 10.0, "FCC", 1828.0, 12.02, 44.0, 121.0, 0.39, 8.86, 5, 10, 5, 10, "transition", "#10B981", False, False, False, 35.0, 71.8, 26.0, 11.8),
    "Ag": ElementData(47, "Ag", "Silver", 107.87, 144.0, 1.93, 11.0, "FCC", 1235.0, 10.49, 30.0, 83.0, 0.37, 10.27, 5, 11, 5, 11, "transition", "#6B7280", False, False, False, 20.0, 429.0, 25.4, 18.9),
    "Cd": ElementData(48, "Cd", "Cadmium", 112.41, 130.0, 1.5, 12.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 5, 12, 5, 12, "transition", "#14B8A6", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "In": ElementData(49, "In", "Indium", 114.82, 167.0, 1.78, 3.0, "TETR", 430.0, 7.31, 4.3, 11.0, 0.45, 15.76, 5, 13, 5, 13, "post-transition", "#3B82F6", False, False, False, 10.0, 81.8, 26.7, 32.1),
    "Sn": ElementData(50, "Sn", "Tin", 118.71, 140.0, 1.96, 4.0, "BCT", 505.0, 7.265, 18.0, 50.0, 0.36, 16.29, 5, 14, 5, 14, "post-transition", "#0EA5E9", False, False, False, 25.0, 66.8, 27.1, 22.0),
    "Sb": ElementData(51, "Sb", "Antimony", 121.76, 140.0, 1.5, 5.0, "RHOMB", 1500.0, 7.0, 20.0, 55.0, 0.28, 18.19, 5, 15, 5, 15, "metalloid", "#8B5CF6", False, False, False, 80.0, 50.0, 25.0, 12.0),
    "Te": ElementData(52, "Te", "Tellurium", 127.6, 130.0, 1.5, 6.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 5, 16, 5, 16, "metalloid", "#EC4899", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "I": ElementData(53, "I", "Iodine", 126.9, 130.0, 1.5, 7.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 5, 17, 5, 17, "nonmetal", "#F43F5E", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Xe": ElementData(54, "Xe", "Xenon", 131.29, 130.0, 1.5, 8.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 5, 18, 5, 18, "noble", "#9CA3AF", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Cs": ElementData(55, "Cs", "Cesium", 132.91, 130.0, 1.5, 1.0, "BCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 6, 1, 6, 1, "alkali", "#EF4444", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Ba": ElementData(56, "Ba", "Barium", 137.33, 222.0, 0.89, 2.0, "BCC", 1000.0, 3.62, 4.9, 13.0, 0.28, 38.16, 6, 2, 6, 2, "alkaline-earth", "#F59E0B", False, False, False, 10.0, 18.4, 28.1, 20.6),
    "Hf": ElementData(72, "Hf", "Hafnium", 178.49, 159.0, 1.3, 4.0, "HCP", 2506.0, 13.31, 53.0, 138.0, 0.3, 13.44, 6, 4, 6, 4, "transition", "#9CA3AF", False, True, False, 110.0, 23.0, 25.7, 5.9),
    "Ta": ElementData(73, "Ta", "Tantalum", 180.95, 146.0, 1.5, 5.0, "BCC", 3290.0, 16.69, 69.0, 186.0, 0.34, 10.85, 6, 5, 6, 5, "transition", "#7C3AED", False, True, False, 180.0, 57.5, 25.4, 6.3),
    "W": ElementData(74, "W", "Tungsten", 183.84, 139.0, 2.36, 6.0, "BCC", 3695.0, 19.25, 161.0, 411.0, 0.28, 9.47, 6, 6, 6, 6, "transition", "#475569", False, True, False, 420.0, 173.0, 24.3, 4.5),
    "Re": ElementData(75, "Re", "Rhenium", 186.21, 137.0, 1.9, 7.0, "HCP", 3459.0, 21.02, 178.0, 463.0, 0.3, 8.86, 6, 7, 6, 7, "transition", "#0284C7", False, True, False, 260.0, 48.0, 25.5, 6.2),
    "Os": ElementData(76, "Os", "Osmium", 190.23, 135.0, 2.2, 8.0, "HCP", 3306.0, 22.59, 222.0, 562.0, 0.25, 8.42, 6, 8, 6, 8, "transition", "#4B5563", False, False, False, 240.0, 87.0, 24.7, 5.1),
    "Ir": ElementData(77, "Ir", "Iridium", 192.22, 136.0, 2.2, 9.0, "FCC", 2719.0, 22.56, 210.0, 528.0, 0.26, 8.52, 6, 9, 6, 9, "transition", "#D97706", False, False, False, 160.0, 147.0, 25.1, 6.4),
    "Pt": ElementData(78, "Pt", "Platinum", 195.08, 139.0, 2.28, 10.0, "FCC", 2041.0, 21.45, 61.0, 168.0, 0.38, 9.09, 6, 10, 6, 10, "transition", "#059669", False, False, False, 40.0, 71.6, 25.9, 8.8),
    "Au": ElementData(79, "Au", "Gold", 196.97, 144.0, 2.54, 11.0, "FCC", 1337.0, 19.3, 27.0, 78.0, 0.44, 10.21, 6, 11, 6, 11, "transition", "#EAB308", False, False, False, 15.0, 318.0, 25.4, 14.2),
    "Hg": ElementData(80, "Hg", "Mercury", 200.59, 130.0, 1.5, 12.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 6, 12, 6, 12, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Tl": ElementData(81, "Tl", "Thallium", 204.38, 130.0, 1.5, 3.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 6, 13, 6, 13, "post-transition", "#3B82F6", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Pb": ElementData(82, "Pb", "Lead", 207.2, 175.0, 2.33, 4.0, "FCC", 601.0, 11.34, 5.6, 16.0, 0.44, 18.26, 6, 14, 6, 14, "post-transition", "#64748B", False, False, False, 15.0, 35.3, 26.8, 28.9),
    "Bi": ElementData(83, "Bi", "Bismuth", 208.98, 170.0, 2.02, 5.0, "RHOMB", 544.0, 9.78, 12.0, 32.0, 0.33, 21.32, 6, 15, 6, 15, "post-transition", "#8B5CF6", False, False, False, 35.0, 7.9, 25.5, 13.4),
    "Po": ElementData(84, "Po", "Polonium", 209.0, 130.0, 1.5, 6.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 6, 16, 6, 16, "post-transition", "#EC4899", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "At": ElementData(85, "At", "Astatine", 210.0, 130.0, 1.5, 7.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 6, 17, 6, 17, "nonmetal", "#F43F5E", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Rn": ElementData(86, "Rn", "Radon", 222.0, 130.0, 1.5, 8.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 6, 18, 6, 18, "noble", "#9CA3AF", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Fr": ElementData(87, "Fr", "Francium", 223.0, 130.0, 1.5, 1.0, "BCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 1, 7, 1, "alkali", "#EF4444", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Ra": ElementData(88, "Ra", "Radium", 226.0, 130.0, 1.5, 2.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 2, 7, 2, "alkaline-earth", "#F59E0B", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Rf": ElementData(104, "Rf", "Rutherfordium", 267.0, 130.0, 1.5, 4.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 4, 7, 4, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Db": ElementData(105, "Db", "Dubnium", 268.0, 130.0, 1.5, 5.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 5, 7, 5, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Sg": ElementData(106, "Sg", "Seaborgium", 269.0, 130.0, 1.5, 6.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 6, 7, 6, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Bh": ElementData(107, "Bh", "Bohrium", 270.0, 130.0, 1.5, 7.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 7, 7, 7, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Hs": ElementData(108, "Hs", "Hassium", 277.0, 130.0, 1.5, 8.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 8, 7, 8, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Mt": ElementData(109, "Mt", "Meitnerium", 278.0, 130.0, 1.5, 9.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 9, 7, 9, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Ds": ElementData(110, "Ds", "Darmstadtium", 281.0, 130.0, 1.5, 10.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 10, 7, 10, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Rg": ElementData(111, "Rg", "Roentgenium", 282.0, 130.0, 1.5, 11.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 11, 7, 11, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Cn": ElementData(112, "Cn", "Copernicium", 285.0, 130.0, 1.5, 12.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 12, 7, 12, "transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Nh": ElementData(113, "Nh", "Nihonium", 286.0, 130.0, 1.5, 3.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 13, 7, 13, "post-transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Fl": ElementData(114, "Fl", "Flerovium", 289.0, 130.0, 1.5, 4.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 14, 7, 14, "post-transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Mc": ElementData(115, "Mc", "Moscovium", 290.0, 130.0, 1.5, 5.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 15, 7, 15, "post-transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Lv": ElementData(116, "Lv", "Livermorium", 293.0, 130.0, 1.5, 6.0, "FCC", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 16, 7, 16, "post-transition", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Ts": ElementData(117, "Ts", "Tennessine", 294.0, 130.0, 1.5, 7.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 17, 7, 17, "nonmetal", "#6B7280", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Og": ElementData(118, "Og", "Oganesson", 294.0, 130.0, 1.5, 8.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 18, 7, 18, "noble", "#9CA3AF", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "La": ElementData(57, "La", "Lanthanum", 138.91, 187.0, 1.1, 3.0, "DHCP", 1193.0, 6.162, 14.3, 36.6, 0.28, 22.39, 6, 3, 9, 4, "lanthanide", "#A855F7", False, False, False, 120.0, 13.4, 27.1, 5.2),
    "Ce": ElementData(58, "Ce", "Cerium", 140.12, 182.0, 1.12, 3.0, "FCC", 1068.0, 6.77, 13.5, 33.6, 0.24, 20.69, 6, 3, 9, 5, "lanthanide", "#A855F7", False, False, False, 110.0, 11.3, 26.9, 6.3),
    "Pr": ElementData(59, "Pr", "Praseodymium", 140.91, 182.0, 1.13, 3.0, "DHCP", 1208.0, 6.77, 14.8, 37.3, 0.28, 20.8, 6, 3, 9, 6, "lanthanide", "#A855F7", False, False, False, 130.0, 12.5, 27.2, 6.7),
    "Nd": ElementData(60, "Nd", "Neodymium", 144.24, 182.0, 1.14, 3.0, "DHCP", 1297.0, 7.01, 16.3, 41.4, 0.28, 20.59, 6, 3, 9, 7, "lanthanide", "#A855F7", False, False, False, 140.0, 16.5, 27.4, 6.7),
    "Pm": ElementData(61, "Pm", "Promethium", 145.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 6, 3, 9, 8, "lanthanide", "#A855F7", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Sm": ElementData(62, "Sm", "Samarium", 150.36, 180.0, 1.17, 3.0, "RHOMB", 1345.0, 7.52, 19.5, 49.7, 0.27, 19.98, 6, 3, 9, 9, "lanthanide", "#A855F7", False, False, False, 150.0, 13.3, 29.5, 12.7),
    "Eu": ElementData(63, "Eu", "Europium", 151.96, 204.0, 1.2, 2.0, "BCC", 1099.0, 5.244, 5.4, 13.9, 0.15, 28.97, 6, 3, 9, 10, "lanthanide", "#A855F7", False, False, False, 40.0, 13.9, 27.7, 35.0),
    "Gd": ElementData(64, "Gd", "Gadolinium", 157.25, 180.0, 1.2, 3.0, "HCP", 1585.0, 7.9, 21.8, 54.8, 0.26, 19.9, 6, 3, 9, 11, "lanthanide", "#A855F7", False, False, False, 160.0, 10.5, 37.0, 9.4),
    "Tb": ElementData(65, "Tb", "Terbium", 158.93, 178.0, 1.2, 3.0, "HCP", 1629.0, 8.23, 22.1, 55.7, 0.26, 19.3, 6, 3, 9, 12, "lanthanide", "#A855F7", False, False, False, 170.0, 11.1, 28.9, 10.3),
    "Dy": ElementData(66, "Dy", "Dysprosium", 162.5, 177.0, 1.22, 3.0, "HCP", 1680.0, 8.54, 24.7, 61.4, 0.25, 19.01, 6, 3, 9, 13, "lanthanide", "#A855F7", False, False, False, 180.0, 10.7, 27.7, 9.9),
    "Ho": ElementData(67, "Ho", "Holmium", 164.93, 176.0, 1.23, 3.0, "HCP", 1734.0, 8.79, 26.3, 64.8, 0.23, 18.74, 6, 3, 9, 14, "lanthanide", "#A855F7", False, False, False, 190.0, 16.2, 27.2, 11.2),
    "Er": ElementData(68, "Er", "Erbium", 167.26, 175.0, 1.24, 3.0, "HCP", 1802.0, 9.066, 28.3, 69.9, 0.24, 18.46, 6, 3, 9, 15, "lanthanide", "#A855F7", False, False, False, 200.0, 14.5, 28.1, 12.2),
    "Tm": ElementData(69, "Tm", "Thulium", 168.93, 174.0, 1.25, 3.0, "HCP", 1818.0, 9.32, 30.5, 74.0, 0.21, 18.12, 6, 3, 9, 16, "lanthanide", "#A855F7", False, False, False, 210.0, 16.9, 27.0, 13.3),
    "Yb": ElementData(70, "Yb", "Ytterbium", 173.05, 194.0, 1.1, 2.0, "FCC", 1097.0, 6.9, 7.0, 18.1, 0.21, 24.84, 6, 3, 9, 17, "lanthanide", "#A855F7", False, False, False, 45.0, 38.5, 26.7, 26.3),
    "Lu": ElementData(71, "Lu", "Lutetium", 174.97, 173.0, 1.27, 3.0, "HCP", 1925.0, 9.841, 27.2, 68.6, 0.26, 17.78, 6, 3, 9, 18, "lanthanide", "#A855F7", False, False, False, 210.0, 16.4, 26.9, 9.9),
    "Ac": ElementData(89, "Ac", "Actinium", 227.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 4, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Th": ElementData(90, "Th", "Thorium", 232.04, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 5, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Pa": ElementData(91, "Pa", "Protactinium", 231.04, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 6, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "U": ElementData(92, "U", "Uranium", 238.03, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 7, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Np": ElementData(93, "Np", "Neptunium", 237.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 8, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Pu": ElementData(94, "Pu", "Plutonium", 244.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 9, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Am": ElementData(95, "Am", "Americium", 243.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 10, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Cm": ElementData(96, "Cm", "Curium", 247.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 11, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Bk": ElementData(97, "Bk", "Berkelium", 247.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 12, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Cf": ElementData(98, "Cf", "Californium", 251.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 13, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Es": ElementData(99, "Es", "Einsteinium", 252.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 14, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Fm": ElementData(100, "Fm", "Fermium", 257.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 15, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Md": ElementData(101, "Md", "Mendelevium", 258.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 16, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "No": ElementData(102, "No", "Nobelium", 259.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 17, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
    "Lr": ElementData(103, "Lr", "Lawrencium", 266.0, 130.0, 1.5, 3.0, "HCP", 1500.0, 7.0, 50.0, 120.0, 0.3, 10.0, 7, 3, 10, 18, "actinide", "#9333EA", False, False, False, 30.0, 50.0, 25.0, 12.0),
}

IUPAC_ELEMENTS_DATA: Dict[str, ElementData] = ELEMENTS_REGISTRY

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
    def get_element(cls, symbol: str) -> Optional[ElementData]:
        return ELEMENTS_REGISTRY.get(symbol.strip())

    @classmethod
    def all(cls) -> Dict[str, ElementData]:
        return ELEMENTS_REGISTRY

    @classmethod
    def get_118_list(cls) -> List[ElementData]:
        return sorted(list(ELEMENTS_REGISTRY.values()), key=lambda e: e.z)
