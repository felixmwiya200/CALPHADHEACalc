"""
pycalphad_app.core.population_balance_engine
============================================
Population Balance Model (PBM) / Kampmann-Wagner Numerical (KWN) Engine
for precipitation kinetics in multi-component alloys.

Couples CALPHAD thermodynamic outputs (chemical driving force, equilibrium
phase fractions, interfacial energies, and solute diffusion coefficients) to
solve concurrent nucleation, diffusion-controlled growth, and Ostwald coarsening.
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


class PopulationBalanceEngine:
    """
    Solves the continuous/discrete Population Balance Equation for precipitate size distribution (PSD):
        dn_i/dt + d(v * n_i)/dr = J(t) * delta(r - r*)
    coupled with solute mass conservation:
        C_matrix(t) = (C0 - f_v(t) * Cp) / (1 - f_v(t))
    """

    # Physical constants
    R_GAS = 8.314462618  # J / (mol*K)
    K_BOLTZMANN = 1.380649e-23  # J / K
    N_AVOGADRO = 6.02214076e23  # 1 / mol

    def __init__(
        self,
        phase_name: str = "Gamma_Prime",
        t_kelvin: float = 1073.15,
        matrix_c0: float = 0.12,  # Solute atomic fraction in alloy (e.g., Al+Ti in Ni)
        matrix_ce: float = 0.04,  # CALPHAD equilibrium matrix solubility at T
        precip_cp: float = 0.25,  # Solute atomic fraction in precipitate
        gamma_interfacial: float = 0.035,  # Interfacial energy J/m² (coherent/semi-coherent)
        diffusivity: Optional[float] = None,  # Solute diffusion coeff m²/s
        molar_volume: float = 1.05e-5,  # m³ / mol
        lattice_param_a: float = 3.6e-10,  # Matrix lattice parameter (m)
        shear_modulus_g: float = 78e9,  # Pa
        burgers_vector_b: float = 2.54e-10,  # m
        poisson_ratio_nu: float = 0.31,
        taylor_factor_m: float = 3.06,
        apb_energy: float = 0.160,  # J/m² (Antiphase boundary energy for cutting)
        eq_phase_fraction: float = 0.12  # CALPHAD equilibrium phase fraction
    ):
        self.phase_name = phase_name
        self.temp_k = max(300.0, float(t_kelvin))
        self.c0 = max(1e-5, min(0.99, float(matrix_c0)))
        self.ce = max(1e-6, min(self.c0 * 0.999, float(matrix_ce)))
        self.cp = max(self.c0 * 1.001, min(1.0, float(precip_cp)))
        self.gamma = max(1e-4, float(gamma_interfacial))
        self.vm = float(molar_volume)
        self.a_lat = float(lattice_param_a)
        self.g_mod = float(shear_modulus_g)
        self.b_vec = float(burgers_vector_b)
        self.nu = float(poisson_ratio_nu)
        self.taylor_m = float(taylor_factor_m)
        self.gamma_apb = float(apb_energy)
        self.f_eq = max(1e-4, min(0.85, float(eq_phase_fraction)))

        # Arrhenius diffusivity default if not provided: D = D0 * exp(-Q / RT)
        if diffusivity is not None and diffusivity > 0:
            self.diffusivity = float(diffusivity)
        else:
            # Substitutional solute diffusion in FCC/BCC (Q ~ 260 kJ/mol, D0 ~ 1.5e-4 m²/s)
            q_diff = 265000.0
            d0_diff = 1.45e-4
            self.diffusivity = d0_diff * math.exp(-q_diff / (self.R_GAS * self.temp_k))

        # Atomic volume and physical heterogeneous nucleation site density (dislocations / grain boundaries)
        self.v_atom = self.vm / self.N_AVOGADRO
        self.n0_sites = min(1.0 / self.v_atom, 5.0e24)  # Realistic physical nucleation site limit

    def compute_gibbs_thomson_solubility(self, r_meters: float) -> float:
        """Evaluates capillary-shifted solubility at particle interface: C_r = C_e * exp(2*gamma*Vm / (r*R*T))."""
        if r_meters <= 1e-11:
            return self.cp
        arg = (2.0 * self.gamma * self.vm) / (r_meters * self.R_GAS * self.temp_k)
        # Cap exponential argument to avoid numerical overflow at sub-nanometer scale
        arg = min(35.0, arg)
        return float(self.ce * math.exp(arg))

    def compute_critical_nucleus(self, c_matrix: float) -> Tuple[float, float, float]:
        """
        Evaluates critical radius r*, activation barrier Delta G*, and steady-state nucleation rate J(t)
        via Turnbull-Fisher Classical Nucleation Theory (CNT).
        """
        if c_matrix <= self.ce:
            return 1e-5, 1e20, 0.0

        # Chemical driving force per unit volume (Delta G_v in J/m³)
        delta_gv = (self.R_GAS * self.temp_k / self.vm) * math.log(max(1.0001, c_matrix / self.ce))

        # Critical radius r* = 2 * gamma / Delta G_v
        r_star = (2.0 * self.gamma) / delta_gv
        if r_star <= 0 or not math.isfinite(r_star):
            return 1e-5, 1e20, 0.0

        # Activation energy barrier Delta G* = (16 * pi * gamma^3) / (3 * Delta_Gv^2)
        delta_g_star = (16.0 * math.pi * (self.gamma ** 3)) / (3.0 * (delta_gv ** 2))

        # Zeldovich non-equilibrium factor Z
        denom = 2.0 * math.pi * (r_star ** 2) * self.N_AVOGADRO
        zeldovich = math.sqrt(self.gamma / (self.K_BOLTZMANN * self.temp_k)) * (self.vm / max(1e-25, denom))

        # Atomic impingement rate beta* = (4 * pi * r*^2 * D * c_matrix) / a^4
        beta_star = (4.0 * math.pi * (r_star ** 2) * self.diffusivity * c_matrix) / (self.a_lat ** 4)

        # Steady-state nucleation rate J = Z * beta* * N0 * exp(-Delta G* / (k_B * T))
        exp_arg = -delta_g_star / (self.K_BOLTZMANN * self.temp_k)
        exp_factor = math.exp(max(-80.0, exp_arg))
        j_rate = zeldovich * beta_star * self.n0_sites * exp_factor

        return float(r_star), float(delta_g_star), float(max(0.0, j_rate))

    def compute_growth_velocity(self, r_meters: float, c_matrix: float) -> float:
        """
        Zener-Lifshitz diffusion-controlled radial velocity:
            v(r) = dr/dt = (D / r) * (C_matrix - C_r) / (C_p - C_r)
        """
        if r_meters <= 1e-11:
            return 0.0
        c_r = self.compute_gibbs_thomson_solubility(r_meters)
        num = c_matrix - c_r
        den = max(1e-4, self.cp - c_r)
        return float((self.diffusivity / r_meters) * (num / den))

    def compute_strengthening_mechanisms(
        self,
        mean_radius_m: float,
        volume_fraction: float
    ) -> Dict[str, float]:
        """
        Evaluates yield strength enhancement:
        - Friedel weak/strong cutting for fine precipitates
        - Orowan dislocation looping bypass for coarsened particles
        - Harmonic blending for smooth transition through peak aging.
        """
        fv = max(1e-6, min(0.85, volume_fraction))
        r_bar = max(1e-10, mean_radius_m)

        # 1. Friedel cutting mechanism (Order strengthening / APB shearing)
        line_tension = 0.5 * self.g_mod * (self.b_vec ** 2)
        tau_cut = (self.gamma_apb / (2.0 * self.b_vec)) * math.sqrt(
            max(0.0, (8.0 * self.gamma_apb * r_bar * fv) / (math.pi * self.g_mod * (self.b_vec ** 2)))
        )
        sigma_cut = (self.taylor_m * tau_cut) * 1e-6  # to MPa
        sigma_cut = max(0.0, min(1400.0, sigma_cut))

        # 2. Orowan dislocation looping mechanism
        # Effective inter-particle spacing L = sqrt(2*pi / (3*fv)) * r_bar - 2*r_bar
        spacing_l = max(self.b_vec * 2.0, math.sqrt((2.0 * math.pi) / (3.0 * fv)) * r_bar - (2.0 * r_bar))
        r0_core = self.b_vec
        ln_term = math.log(max(1.01, (2.0 * r_bar) / r0_core))

        pre_orowan = (self.taylor_m * 0.81 * self.g_mod * self.b_vec) / (
            2.0 * math.pi * math.sqrt(max(0.1, 1.0 - self.nu))
        )
        sigma_orowan = (pre_orowan * (ln_term / spacing_l)) * 1e-6  # to MPa
        sigma_orowan = max(0.0, min(1800.0, sigma_orowan))

        # 3. Blended precipitation strengthening (harmonic mean / transition)
        if sigma_cut > 0 and sigma_orowan > 0:
            sigma_precip = math.pow((1.0 / (sigma_cut ** 2)) + (1.0 / (sigma_orowan ** 2)), -0.5)
        else:
            sigma_precip = max(sigma_cut, sigma_orowan)

        return {
            "sigma_shearing_cutting_mpa": float(sigma_cut),
            "sigma_orowan_looping_mpa": float(sigma_orowan),
            "sigma_precipitation_total_mpa": float(sigma_precip),
            "mean_interparticle_spacing_nm": float(spacing_l * 1e9)
        }

    def solve(
        self,
        total_time_seconds: float = 36000.0,  # 10 hours default
        n_bins: int = 60,
        r_min_nm: float = 0.15,
        r_max_nm: float = 150.0,
        n_time_steps: int = 150
    ) -> Dict[str, Any]:
        """
        Executes discrete Kampmann-Wagner Numerical (KWN) solution across spatial radius classes.
        Returns time evolution of PSD, mean radius, volume fraction, number density, and strengthening.
        """
        # Discretize radius bins in log-space to capture both nucleation nuclei and coarsened dispersoids
        r_grid = np.geomspace(r_min_nm * 1e-9, r_max_nm * 1e-9, n_bins)
        dr_grid = np.diff(r_grid)
        dr_grid = np.append(dr_grid, dr_grid[-1])

        # Particle size distribution array: n_i = number density per bin (m^-4)
        n_psd = np.zeros(n_bins, dtype=float)

        dt = total_time_seconds / max(1, n_time_steps)
        c_matrix = float(self.c0)

        # Output trajectories
        time_series_s = []
        mean_radius_nm_series = []
        volume_fraction_series = []
        number_density_series = []
        r_star_nm_series = []
        nucleation_rate_series = []
        precip_strength_series = []

        curr_t = 0.0

        for step in range(n_time_steps):
            # 1. Nucleation rate and critical radius at current supersaturation
            r_star, delta_g_star, j_nuc = self.compute_critical_nucleus(c_matrix)

            # 2. Growth velocities across all bins
            v_growth = np.array([self.compute_growth_velocity(r, c_matrix) for r in r_grid])

            # 3. Advective flux in radius space via conservative upwind scheme
            flux = np.zeros(n_bins + 1, dtype=float)
            for i in range(1, n_bins):
                if v_growth[i] >= 0.0:
                    flux[i] = v_growth[i] * n_psd[i - 1]
                else:
                    flux[i] = v_growth[i] * n_psd[i]

            # 4. Continuity update: dn/dt = - d(Flux)/dr + Nucleation Source
            dn_dt = np.zeros(n_bins, dtype=float)
            for i in range(n_bins):
                dn_dt[i] = -(flux[i + 1] - flux[i]) / max(1e-12, dr_grid[i])

            # Inject nucleated particles into the bin containing r*
            if j_nuc > 0.0 and r_star < r_grid[-1]:
                idx_nuc = int(np.searchsorted(r_grid, r_star))
                idx_nuc = max(0, min(n_bins - 1, idx_nuc))
                dn_dt[idx_nuc] += j_nuc / max(1e-12, dr_grid[idx_nuc])

            # Time integration step with non-negativity constraint
            n_psd = np.maximum(0.0, n_psd + dn_dt * dt)

            # 5. Calculate microstructural moment statistics
            # Number density: N_v = sum(n_i * dr_i) (m^-3)
            n_v = float(np.sum(n_psd * dr_grid))

            # Volume fraction: f_v = sum(4/3 * pi * r_i^3 * n_i * dr_i)
            v_particles = (4.0 / 3.0) * math.pi * np.sum((r_grid ** 3) * n_psd * dr_grid)
            if v_particles > self.f_eq and v_particles > 1e-12:
                # Conserve CALPHAD equilibrium volume fraction ceiling during coarsening
                n_psd = n_psd * (self.f_eq / v_particles)
                fv = float(self.f_eq)
                n_v = float(np.sum(n_psd * dr_grid))
            else:
                fv = float(max(0.0, min(self.f_eq, v_particles)))

            # Mean radius: r_bar = sum(r_i * n_i * dr_i) / N_v
            if n_v > 1e10:
                r_bar = float(np.sum(r_grid * n_psd * dr_grid) / n_v)
            else:
                r_bar = float(r_star)

            # 6. Matrix solute depletion update
            c_matrix = max(self.ce, (self.c0 - fv * self.cp) / max(0.15, 1.0 - fv))

            # 7. Strengthening evaluation
            mech = self.compute_strengthening_mechanisms(r_bar, fv)

            # Record trajectory
            time_series_s.append(curr_t)
            mean_radius_nm_series.append(r_bar * 1e9)
            volume_fraction_series.append(fv)
            number_density_series.append(n_v)
            r_star_nm_series.append(min(100.0, r_star * 1e9))
            nucleation_rate_series.append(j_nuc)
            precip_strength_series.append(mech["sigma_precipitation_total_mpa"])

            curr_t += dt

        # Final PSD histogram in nm
        psd_histogram = {
            "radius_nm": (r_grid * 1e9).tolist(),
            "number_density_m4": n_psd.tolist(),
            "normalized_frequency": (n_psd / max(1e-30, np.sum(n_psd))).tolist()
        }

        final_mech = self.compute_strengthening_mechanisms(
            mean_radius_nm_series[-1] * 1e-9,
            volume_fraction_series[-1]
        )

        return {
            "phase_name": self.phase_name,
            "temperature_k": self.temp_k,
            "solute_c0": self.c0,
            "solute_ce": self.ce,
            "solute_matrix_final": float(c_matrix),
            "diffusivity_m2_s": self.diffusivity,
            "interfacial_energy_j_m2": self.gamma,
            "mean_radius_nm_final": float(mean_radius_nm_series[-1]),
            "volume_fraction_final": float(volume_fraction_series[-1]),
            "number_density_m3_final": float(number_density_series[-1]),
            "critical_radius_nm_final": float(r_star_nm_series[-1]),
            "orowan_strengthening_final_mpa": float(final_mech["sigma_orowan_looping_mpa"]),
            "shearing_strengthening_final_mpa": float(final_mech["sigma_shearing_cutting_mpa"]),
            "total_precip_strengthening_mpa": float(final_mech["sigma_precipitation_total_mpa"]),
            "trajectories": {
                "time_hours": [t / 3600.0 for t in time_series_s],
                "time_seconds": time_series_s,
                "mean_radius_nm": mean_radius_nm_series,
                "volume_fraction": volume_fraction_series,
                "number_density_m3": number_density_series,
                "critical_radius_nm": r_star_nm_series,
                "nucleation_rate_m3_s": nucleation_rate_series,
                "precipitation_strength_mpa": precip_strength_series
            },
            "psd_histogram": psd_histogram
        }
