"""Core physics and CALPHAD calculation engines."""
from pycalphad_app.core.elements_data import ElementsData, ElementData, get_element, get_all_elements, IUPAC_ELEMENTS_DATA
from pycalphad_app.core.thermo_engine import CALPHADThermoEngine, ThermoEngine
from pycalphad_app.core.coating_engine import ThermalSprayCoatingEngine, HEACoatingEngine, CoatingProperties
CoatingEngine = HEACoatingEngine  # Alias for backward compatibility
from pycalphad_app.core.mechanical_engine import MechanicalEngine
from pycalphad_app.core.oxidation_engine import OxidationEngine
from pycalphad_app.core.corrosion_engine import CorrosionEngine
from pycalphad_app.core.xrd_engine import XRDEngine
from pycalphad_app.core.application_scorer import ApplicationScorer, ApplicationDatabase
from pycalphad_app.core.lattice_distortion_engine import LatticeDistortionEngine
from pycalphad_app.core.pycalphad_embed import PyCalphadEmbed, DynamicTDBGenerator

__all__ = [
    "ElementsData",
    "ElementData",
    "get_element",
    "get_all_elements",
    "IUPAC_ELEMENTS_DATA",
    "CALPHADThermoEngine",
    "ThermoEngine",
    "ThermalSprayCoatingEngine",
    "HEACoatingEngine",
    "CoatingEngine",
    "CoatingProperties",
    "MechanicalEngine",
    "OxidationEngine",
    "CorrosionEngine",
    "XRDEngine",
    "ApplicationScorer",
    "ApplicationDatabase",
    "LatticeDistortionEngine",
    "PyCalphadEmbed",
    "DynamicTDBGenerator"
]
