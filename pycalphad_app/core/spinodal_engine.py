"""
Spinodal Decomposition and Symmetric Regular-Solution Thermodynamic Engine.

Implements:
1. Symmetric regular-solution Gibbs free energy of mixing Delta G_mix(x, T).
2. Analytical spinodal curve d^2G/dx^2 = 0: x_s(T) = 0.5 +/- sqrt(0.25 - RT/(2*Omega)).
3. Equilibrium binodal miscibility gap via common-tangent bisection dG/dx = 0.
4. Cahn-Hilliard characteristic wavelength lambda_max and amplification spectrum R(q).
5. Phase stability classification (stable, metastable, unstable/spinodal).
"""

from typing import Dict, Any, List, Tuple, Optional
import math
import numpy as np


class SpinodalEngine:
    """
    Thermodynamic solver for regular-solution miscibility gaps,
    spinodal decomposition limits, and Cahn-Hilliard phase separation kinetics.
    """

    R_GAS = 8.314462618  # Universal gas constant (J/(mol*K))

    def __init__(
        self,
        tc_c: float = 900.0,
        omega: Optional[float] = None,
        kappa: float = 1.8e-15,  # Gradient energy coefficient (J*m^2/mol)
        mobility: float = 1.0e-20  # Atomic mobility (m^2*mol/(J*s))
    ):
        self.tc_c = float(tc_c)
        self.tc_k = self.tc_c + 273.15
        if omega is not None and omega > 0:
            self.omega = float(omega)
            self.tc_k = self.omega / (2.0 * self.R_GAS)
            self.tc_c = self.tc_k - 273.15
        else:
            self.omega = 2.0 * self.R_GAS * self.tc_k

        self.kappa = float(kappa)
        self.mobility = float(mobility)

    @staticmethod
    def c_to_k(t_c: float) -> float:
        return float(t_c) + 273.15

    @staticmethod
    def k_to_c(t_k: float) -> float:
        return float(t_k) - 273.15

    def free_energy_of_mixing(self, x: float, t_c: float) -> Dict[str, float]:
        """
        Calculates Delta G_mix(x, T), dG/dx, and d^2G/dx^2 for symmetric regular solution:
        Delta G_mix = Omega * x * (1 - x) + R * T * [x * ln(x) + (1 - x) * ln(1 - x)]
        """
        x_clamped = max(1e-7, min(1.0 - 1e-7, float(x)))
        t_k = max(1.0, self.c_to_k(t_c))

        s_id = -self.R_GAS * (x_clamped * math.log(x_clamped) + (1.0 - x_clamped) * math.log(1.0 - x_clamped))
        g_id = -t_k * s_id
        g_ex = self.omega * x_clamped * (1.0 - x_clamped)
        g_mix = g_ex + g_id

        # First derivative: d(Delta G)/dx = Omega * (1 - 2x) + R * T * ln(x / (1 - x))
        dg_dx = self.omega * (1.0 - 2.0 * x_clamped) + self.R_GAS * t_k * (math.log(x_clamped) - math.log(1.0 - x_clamped))

        # Second derivative: d^2(Delta G)/dx^2 = -2 * Omega + R * T / [x * (1 - x)]
        d2g_dx2 = -2.0 * self.omega + (self.R_GAS * t_k) / (x_clamped * (1.0 - x_clamped))

        return {
            "x": x_clamped,
            "T_C": t_c,
            "T_K": t_k,
            "G_mix_J_mol": float(g_mix),
            "G_id_J_mol": float(g_id),
            "G_ex_J_mol": float(g_ex),
            "dG_dx_J_mol": float(dg_dx),
            "d2G_dx2_J_mol": float(d2g_dx2)
        }

    def compute_spinodal(self, t_c: float) -> Tuple[float, float]:
        """
        Calculates spinodal boundaries where d^2G/dx^2 = 0:
        x_s = 0.5 +/- sqrt(0.25 - R*T/(2*Omega))
        """
        t_k = self.c_to_k(t_c)
        if t_k >= self.tc_k:
            return 0.5, 0.5

        radicand = 0.25 - (self.R_GAS * t_k) / (2.0 * self.omega)
        if radicand <= 0.0:
            return 0.5, 0.5

        delta = math.sqrt(radicand)
        x_s1 = max(0.0, 0.5 - delta)
        x_s2 = min(1.0, 0.5 + delta)
        return float(x_s1), float(x_s2)

    def compute_binodal(self, t_c: float) -> Tuple[float, float]:
        """
        Calculates binodal miscibility limits via common tangent / root-finding:
        dG/dx = 0 in x in (0, 0.5).
        For T < Tc, dG/dx has a root at xb < xs:
        dG/dx < 0 for x < xb, and dG/dx > 0 for xb < x < 0.5.
        """
        t_k = self.c_to_k(t_c)
        if t_k >= self.tc_k:
            return 0.5, 0.5

        xs1, _ = self.compute_spinodal(t_c)
        if xs1 >= 0.5:
            return 0.5, 0.5

        def d1(x_val: float) -> float:
            return self.omega * (1.0 - 2.0 * x_val) + self.R_GAS * t_k * (math.log(x_val) - math.log(1.0 - x_val))

        lo = 1e-7
        hi = xs1

        # At lo, d1 is negative (-inf); at xs1, d1 is positive (local maximum)
        if d1(hi) <= 0.0:
            return xs1, 1.0 - xs1

        for _ in range(80):
            mid = 0.5 * (lo + hi)
            val = d1(mid)
            if val < 0.0:
                lo = mid
            else:
                hi = mid

        x_b1 = 0.5 * (lo + hi)
        x_b2 = 1.0 - x_b1
        return float(x_b1), float(x_b2)

    def classify_stability(self, x: float, t_c: float) -> str:
        """
        Determines thermodynamic stability state:
        - 'stable_single_phase': Homogeneous solid solution (outside binodal or T >= Tc).
        - 'metastable': Nucleation and growth regime (between binodal and spinodal).
        - 'unstable_spinodal': Spontaneous spinodal decomposition (inside spinodal, d^2G/dx^2 < 0).
        """
        if t_c >= self.tc_c:
            return "stable_single_phase"

        xb1, xb2 = self.compute_binodal(t_c)
        xs1, xs2 = self.compute_spinodal(t_c)

        if x < xb1 or x > xb2:
            return "stable_single_phase"
        if (xb1 <= x < xs1) or (xs2 < x <= xb2):
            return "metastable"
        return "unstable_spinodal"

    def compute_cahn_hilliard_kinetics(self, x: float, t_c: float) -> Dict[str, Any]:
        """
        Calculates Cahn-Hilliard characteristic wavelength and amplification rate:
        lambda_max = 2*pi * sqrt(2*kappa / (-d^2G/dx^2))
        """
        res = self.free_energy_of_mixing(x, t_c)
        d2g = res["d2G_dx2_J_mol"]

        if d2g >= 0.0:
            return {
                "is_spinodal": False,
                "d2G_dx2": d2g,
                "lambda_max_nm": None,
                "q_max_inv_nm": None,
                "max_amplification_rate_s": 0.0,
                "spectrum_q_inv_nm": [],
                "spectrum_R_s": []
            }

        # Negative curvature: spontaneous uphill diffusion occurs
        driving_force = -d2g
        q_max_m = math.sqrt(driving_force / (4.0 * self.kappa))
        lambda_max_m = (2.0 * math.pi) / q_max_m if q_max_m > 0 else 0.0
        lambda_max_nm = lambda_max_m * 1e9
        q_max_inv_nm = q_max_m * 1e-9

        # Maximum amplification rate: R_max = M * (q_max^2) * (driving_force - 2*kappa*q_max^2) = M * (driving_force^2) / (8*kappa)
        r_max = self.mobility * (driving_force ** 2) / (8.0 * self.kappa)

        # Amplification spectrum R(q) up to critical cutoff q_c = sqrt(driving_force / (2*kappa))
        q_c_m = math.sqrt(driving_force / (2.0 * self.kappa))
        q_vec = np.linspace(0.0, 1.2 * q_c_m, 60)
        r_vec = self.mobility * (q_vec ** 2) * (driving_force - 2.0 * self.kappa * (q_vec ** 2))

        return {
            "is_spinodal": True,
            "d2G_dx2": d2g,
            "lambda_max_nm": float(lambda_max_nm),
            "q_max_inv_nm": float(q_max_inv_nm),
            "max_amplification_rate_s": float(r_max),
            "spectrum_q_inv_nm": (q_vec * 1e-9).tolist(),
            "spectrum_R_s": r_vec.tolist()
        }

    def generate_diagram_data(
        self,
        t_min_c: float = 200.0,
        t_max_c: float = 1050.0,
        n_points: int = 150
    ) -> Dict[str, Any]:
        """
        Generates full T-x miscibility gap and spinodal boundary coordinates.
        """
        t_eval = np.linspace(t_min_c, min(self.tc_c, t_max_c), n_points)

        binodal_left: List[float] = []
        binodal_right: List[float] = []
        spinodal_left: List[float] = []
        spinodal_right: List[float] = []
        t_curve: List[float] = []

        for t in t_eval:
            xb1, xb2 = self.compute_binodal(float(t))
            xs1, xs2 = self.compute_spinodal(float(t))
            binodal_left.append(xb1)
            binodal_right.append(xb2)
            spinodal_left.append(xs1)
            spinodal_right.append(xs2)
            t_curve.append(float(t))

        return {
            "critical_point": {
                "x": 0.5,
                "T_C": self.tc_c,
                "T_K": self.tc_k,
                "Omega_J_mol": self.omega
            },
            "boundaries": {
                "T_C": t_curve,
                "binodal_left": binodal_left,
                "binodal_right": binodal_right,
                "spinodal_left": spinodal_left,
                "spinodal_right": spinodal_right
            },
            "temperature_range_C": [t_min_c, t_max_c]
        }
