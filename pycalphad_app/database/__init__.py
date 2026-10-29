"""Database modules for PyCALPHAD Suite."""
from pycalphad_app.database.material_selector import MaterialDatabaseSelector
from pycalphad_app.database.unified_hea_database import UnifiedHEADatabase
from pycalphad_app.database.thermal_spray_database import ThermalSprayCoatingDatabase
from pycalphad_app.database.aluminium_database import AluminiumAlloyDatabase
from pycalphad_app.database.magnesium_database import MagnesiumAlloyDatabase
from pycalphad_app.database.cast_iron_database import CastIronDatabase
from pycalphad_app.database.general_steel_database import GeneralSteelDatabase
from pycalphad_app.database.stainless_steel_database import StainlessSteelDatabase
from pycalphad_app.database.cobalt_database import CobaltAlloyDatabase
from pycalphad_app.database.nickel_superalloy_database import NickelSuperalloyDatabase
from pycalphad_app.database.nife_superalloy_database import NiFeSuperalloyDatabase
from pycalphad_app.database.single_crystal_database import SingleCrystalDatabase
from pycalphad_app.database.titanium_database import TitaniumAlloyDatabase
from pycalphad_app.database.zirconium_database import ZirconiumAlloyDatabase
from pycalphad_app.database.solder_database import SolderAlloyDatabase
from pycalphad_app.database.published_data_repository import PublishedDataRepository
from pycalphad_app.database.oxide_database import HEAOxideDatabase
from pycalphad_app.database.application_database import HEAApplicationDatabase
from pycalphad_app.database.literature_hea_repository import LiteratureHEARepository

__all__ = [
    "MaterialDatabaseSelector",
    "UnifiedHEADatabase",
    "ThermalSprayCoatingDatabase",
    "AluminiumAlloyDatabase",
    "MagnesiumAlloyDatabase",
    "CastIronDatabase",
    "GeneralSteelDatabase",
    "StainlessSteelDatabase",
    "CobaltAlloyDatabase",
    "NickelSuperalloyDatabase",
    "NiFeSuperalloyDatabase",
    "SingleCrystalDatabase",
    "TitaniumAlloyDatabase",
    "ZirconiumAlloyDatabase",
    "SolderAlloyDatabase",
    "PublishedDataRepository",
    "HEAOxideDatabase",
    "HEAApplicationDatabase",
    "LiteratureHEARepository"
]
