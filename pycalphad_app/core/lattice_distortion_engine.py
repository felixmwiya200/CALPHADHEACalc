"""
lattice_distortion_engine.py - High-Entropy Alloy Lattice Distortion & Soft Sphere Model Engine
Comprehensive translation of App/HEALatticeDistortionEngine.m.

References:
  1. Q. He & Y. Yang, "On Lattice Distortion in High Entropy Alloys", Front. Mater. 5:42 (2018).
  2. Y. F. Ye, Q. Wang, J. Lu, C. T. Liu, Y. Yang, "The 'soft-sphere' model for local lattice
     distortion in high entropy alloys", Mater. Today 19, 349-355 (2016).
  3. Y. F. Ye, Q. F. He, M. F. Lu, et al., "Atomic-scale local strain fluctuations in chemically
     complex alloys", Acta Mater. 150, 182-194 (2018).
"""

import math
import numpy as np
from typing import Dict, List, Any, Optional
from pycalphad_app.core.elements_data import IUPAC_ELEMENTS_DATA

class LatticeDistortionEngine:
    @staticmethod
    def compute_distortion_metrics(elements: List[str], at_fractions: List[float],
                                  thermo_metrics: Optional[Dict[str, Any]] = None,
                                  user_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if thermo_metrics is None:
            thermo_metrics = {}
        if user_opts is None:
            user_opts = {}

        c_raw = np.array(at_fractions, dtype=float)
        c_sum = np.sum(c_raw)
        c = c_raw / c_sum if c_sum > 0 else np.ones(len(elements)) / len(elements)
        n = len(elements)

        # Atomic radii in pm
        r = np.zeros(n)
        for i, sym in enumerate(elements):
            el_data = IUPAC_ELEMENTS_DATA.get(sym)
            if hasattr(el_data, "radius_pm"):
                r[i] = float(el_data.radius_pm)
            elif isinstance(el_data, dict):
                r[i] = float(el_data.get("radius_pm", 130.0))
            else:
                r[i] = 130.0

        r_bar = float(np.sum(c * r))
        delta_hard_sphere_pct = float(np.sqrt(np.sum(c * ((1.0 - (r / r_bar)) ** 2)))) * 100.0

        # Phase, coordination number and packing efficiency
        phase_str = str(thermo_metrics.get("Phase", "FCC"))
        if "BCC" in phase_str:
            crystal_structure = "BCC"
            n_coord = 8
            eta_pack = 0.680
            b_nm = 0.286 * math.sqrt(3.0) / 2.0
        elif "HCP" in phase_str:
            crystal_structure = "HCP"
            n_coord = 12
            eta_pack = 0.7405
            b_nm = 0.265
        else:
            crystal_structure = "FCC"
            n_coord = 12
            eta_pack = 0.7405
            b_nm = 0.360 / math.sqrt(2.0)

        # Soft-sphere local radial strains eps_i
        eps_i = np.zeros(n)
        a_matrix = np.zeros((n, n))
        omega_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                x_ij = r[i] / max(1.0, r[j])
                denom_a = ((x_ij + 1.0) ** 2) * math.sqrt(x_ij * (x_ij + 2.0))
                a_matrix[i, j] = (2.0 * math.pi * x_ij) / max(1e-6, denom_a)
                omega_matrix[i, j] = 2.0 * math.pi * (1.0 - math.sqrt(x_ij * (x_ij + 2.0)) / (x_ij + 1.0))

        for i in range(n):
            sum_omega = float(np.sum(omega_matrix[i, :] * c))
            sum_a = float(np.sum(a_matrix[i, :] * c))
            if sum_a > 0:
                eps_i[i] = (sum_omega / sum_a) - (4.0 * math.pi * eta_pack) / (n_coord * sum_a)
            else:
                eps_i[i] = (r[i] - r_bar) / r_bar

        mean_eps = float(np.sum(c * eps_i))
        eps_i_zero_mean = eps_i - mean_eps
        eps_rms = float(np.sqrt(np.sum(c * (eps_i_zero_mean ** 2))))
        eps_rms_pct = eps_rms * 100.0

        # Critical effective shear strain gamma_th
        mech = thermo_metrics.get("Mechanical", {})
        nu_alloy = float(mech.get("PoissonRatio", thermo_metrics.get("nu0", 0.31)))
        g_alloy_gpa = float(mech.get("ShearModulus_GPa", 80.0))

        nu_clamped = max(0.15, min(0.46, nu_alloy))
        poisson_factor = math.sqrt((2.0 * (1.0 + nu_clamped)) / max(0.01, 1.0 - 2.0 * nu_clamped))
        gamma_th = 0.485 * poisson_factor * (delta_hard_sphere_pct / 100.0)

        c11_gpa = g_alloy_gpa * 2.0 * (1.0 - nu_clamped) / max(0.01, 1.0 - 2.0 * nu_clamped)
        c12_gpa = c11_gpa * nu_clamped / (1.0 - nu_clamped)
        c44_gpa = g_alloy_gpa

        delta_ep_mpa = 0.75 * (c11_gpa - c12_gpa) * (gamma_th ** 2)

        if eps_rms_pct < 5.0:
            structural_regime = "Single-Phase Solid Solution (Low Strain Fluctuation)"
            stability_class = "Stable Solid Solution"
            amorphization_risk = "Negligible (Crystalline Lattice Preserved)"
        elif eps_rms_pct <= 10.0:
            structural_regime = "Multi-Phase / Ordered Intermetallic Precursor"
            stability_class = "Intermediate Lattice Strain"
            amorphization_risk = "Moderate (Local Phase Separation Likely)"
        else:
            structural_regime = "Amorphous Destabilization / Metallic Glass Regime"
            stability_class = "Severe Lattice Distortion"
            amorphization_risk = "High (Topological Amorphization Triggered)"

        if gamma_th < 0.020:
            glide_mech = "Peierls Kink-Pair Glide (Planar Straight Slip)"
            pinning_regime = "Weak Peierls Lattice Friction (Hirth & Lothe 1982)"
            act_vol_b3 = round(8.0 + 150.0 * gamma_th, 1)
            wavy_tortuosity = 1.0 + 1.2 * gamma_th
        else:
            glide_mech = "Labusch Collective Weak Pinning (Wavy Tortuous Slip)"
            pinning_regime = "Labusch Statistical Forest Pinning (Labusch 1970, 1972)"
            act_vol_b3 = round(30.0 + 1200.0 * (gamma_th - 0.02), 1)
            wavy_tortuosity = 1.0 + 3.5 * gamma_th

        delta_sigma_labusch_mpa = 0.5 * (g_alloy_gpa * 1e3) * (gamma_th ** (4.0 / 3.0)) * (1.0 + nu_clamped)

        target_angles = [43.5, 50.8, 74.7, 90.7]
        xrd_splitting = [round(gamma_th * math.tan(math.radians(ang / 2.0)) * (180.0 / math.pi), 3) for ang in target_angles]

        return {
            "Delta_HardSphere_pct": round(delta_hard_sphere_pct, 3),
            "Eps_RMS_SoftSphere_pct": round(eps_rms_pct, 3),
            "MeanAtomicRadius_pm": round(r_bar, 2),
            "ElementalResidualStrains": eps_i_zero_mean.tolist(),
            "PackingEfficiency_eta": eta_pack,
            "CoordinationNumber": n_coord,
            "PoissonRatio": round(nu_clamped, 3),
            "CriticalEffectiveShearStrain_gamma_th": round(gamma_th, 4),
            "ElasticShearEnergy_DeltaEp_MPa": round(delta_ep_mpa, 2),
            "C11_GPa": round(c11_gpa, 1),
            "C12_GPa": round(c12_gpa, 1),
            "C44_GPa": round(c44_gpa, 1),
            "StructuralRegime": structural_regime,
            "StabilityClass": stability_class,
            "AmorphizationRisk": amorphization_risk,
            "DislocationGlideMechanism": glide_mech,
            "PinningRegime": pinning_regime,
            "ActivationVolume_b3": act_vol_b3,
            "WavyDislocationTortuosity": round(wavy_tortuosity, 3),
            "LabuschStrengthening_MPa": round(delta_sigma_labusch_mpa, 1),
            "XRDAngles_2Theta_deg": target_angles,
            "XRDAngularSplitting_deg": xrd_splitting,
            "HasHighAnglePeakSplitting": (gamma_th >= 0.020)
        }
