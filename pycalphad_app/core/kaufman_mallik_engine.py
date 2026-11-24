# -*- coding: utf-8 -*-
"""
kaufman_mallik_engine.py - Kaufman-Bernstein & Mallik (1986) Phase Diagram Engine

Implements the classical analytical computational metallurgy formalism from:
A. K. Mallik, 'Computer calculations of phase diagrams',
Bulletin of Materials Science, Vol. 8, No. 2, May 1986, pp. 107-121.
(Indian Institute of Technology, Bombay).

Key Capabilities:
  1. 2D Newton-Raphson Common Tangent Solver (Mallik Eqs. 10-15):
     Calculates equilibrium compositions (X_alpha, X_beta) from pure element
     lattice stabilities (Delta G_A, Delta G_B) and regular solution interaction
     parameters (E_alpha, E_beta) with exact analytical Jacobian.
  2. Interaction Parameter Inversion (Mallik Appendix 1):
     Derives regular solution interaction parameters (E_alpha, E_beta) directly
     from experimentally observed phase boundaries (X_alpha, X_beta) at temperature T.
  3. Miscibility Gap and Spinodal Decomposition:
     Analytical solver for symmetrical and asymmetrical miscibility gaps when E > 2RT.
  4. Ternary 3D Newton-Raphson Solver (Mallik Eqs. 21-24 & Appendix 2):
     Calculates isothermal sections and tie-lines across ternary systems (e.g. Mo-V-W, Cd-Pb-Sn).
  5. Nelder-Mead Simplex Gibbs Minimizer (Mallik Section 9):
     Derivative-free direct search minimization for multi-component Gibbs surfaces.
  6. Historical Benchmark Presets:
     Reproduces the peritectic (E=4500 cal/mol), monotectic (E=6000 cal/mol),
     and allotropic eutectoid reactions from Balakrishna & Mallik (1979, 1980).
"""

import math
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

# Universal Gas Constant in J / (mol * K) and cal / (mol * K)
R_J_MOL_K: float = 8.314462618
R_CAL_MOL_K: float = 1.987204
CAL_TO_JOULE: float = 4.184


class KaufmanMallikEngine:
    """
    Thermodynamic computational core implementing Kaufman-Bernstein and Mallik (1986)
    regular solution phase diagram calculations.
    """

    @staticmethod
    def solve_binary_common_tangent(
        t_kelvin: float,
        delta_g_a: float,
        delta_g_b: float,
        e_alpha: float,
        e_beta: float,
        initial_guess: Tuple[float, float] = (0.1, 0.9),
        max_iter: int = 150,
        tol: float = 1e-7,
        use_calories: bool = False,
    ) -> Dict[str, Any]:
        """
        Solves Mallik (1986) Equations (10) and (11) via the 2D Newton-Raphson
        iteration method (Equations 12-15) with exact analytical Jacobian.

        Parameters:
            t_kelvin: Absolute temperature in Kelvin.
            delta_g_a: Lattice stability of element A (G_A^beta - G_A^alpha).
            delta_g_b: Lattice stability of element B (G_B^beta - G_B^alpha).
            e_alpha: Regular solution interaction parameter of alpha phase.
            e_beta: Regular solution interaction parameter of beta phase.
            initial_guess: Tuple of (X_alpha_init, X_beta_init).
            max_iter: Maximum number of Newton-Raphson iterations.
            tol: Convergence tolerance for residual norm ||(F, G)||.
            use_calories: If True, input energies and parameters are in cal/mol,
                          otherwise J/mol.

        Returns:
            Dictionary containing:
                - converged: Boolean
                - iterations: int
                - x_alpha: float (equilibrium atomic fraction of B in alpha)
                - x_beta: float (equilibrium atomic fraction of B in beta)
                - residual_norm: float
                - f_residual: float
                - g_residual: float
        """
        if t_kelvin <= 0.0:
            raise ValueError(f"Temperature must be strictly positive: {t_kelvin} K")

        r_const = R_CAL_MOL_K if use_calories else R_J_MOL_K
        rt = r_const * t_kelvin

        x_a = max(1e-5, min(0.99999, float(initial_guess[0])))
        x_b = max(1e-5, min(0.99999, float(initial_guess[1])))

        converged = False
        iteration_count = 0
        res_norm = 1.0
        f_val = 0.0
        g_val = 0.0

        for it in range(1, max_iter + 1):
            iteration_count = it

            # Boundary safety clamp
            x_a = max(1e-6, min(1.0 - 1e-6, x_a))
            x_b = max(1e-6, min(1.0 - 1e-6, x_b))

            # Equation (10): F(X_b, X_a) = Delta G_A + RT * ln((1 - X_b) / (1 - X_a)) - E_alpha * X_a^2 + E_beta * X_b^2 = 0
            f_val = delta_g_a + rt * math.log((1.0 - x_b) / (1.0 - x_a)) - e_alpha * (x_a ** 2) + e_beta * (x_b ** 2)

            # Equation (11): G(X_b, X_a) = Delta G_B + RT * ln(X_b / X_a) - E_alpha * (1 - X_a)^2 + E_beta * (1 - X_b)^2 = 0
            g_val = delta_g_b + rt * math.log(x_b / x_a) - e_alpha * ((1.0 - x_a) ** 2) + e_beta * ((1.0 - x_b) ** 2)

            res_norm = math.hypot(f_val, g_val)
            if res_norm < tol:
                converged = True
                break

            # Analytical Jacobian components (Equations 12-15):
            # J = [[dF/dX_b, dF/dX_a], [dG/dX_b, dG/dX_a]]
            f_xb = -rt / (1.0 - x_b) + 2.0 * e_beta * x_b
            f_xa = rt / (1.0 - x_a) - 2.0 * e_alpha * x_a

            g_xb = rt / x_b - 2.0 * e_beta * (1.0 - x_b)
            g_xa = -rt / x_a + 2.0 * e_alpha * (1.0 - x_a)

            det_j = f_xb * g_xa - f_xa * g_xb

            if abs(det_j) < 1e-15:
                # Regularize singular Jacobian
                det_j = 1e-15 if det_j >= 0 else -1e-15

            # Newton-Raphson step: delta = - J^{-1} * [F, G]^T
            delta_xb = -(g_xa * f_val - f_xa * g_val) / det_j
            delta_xa = -(-g_xb * f_val + f_xb * g_val) / det_j

            # Damped line-search update to stay within physical domain (0, 1)
            damping = 1.0
            for _ in range(5):
                next_xb = x_b + damping * delta_xb
                next_xa = x_a + damping * delta_xa
                if 1e-6 < next_xa < (1.0 - 1e-6) and 1e-6 < next_xb < (1.0 - 1e-6):
                    break
                damping *= 0.5

            x_b = max(1e-6, min(1.0 - 1e-6, x_b + damping * delta_xb))
            x_a = max(1e-6, min(1.0 - 1e-6, x_a + damping * delta_xa))

        return {
            "converged": converged,
            "iterations": iteration_count,
            "t_kelvin": round(t_kelvin, 3),
            "x_alpha": round(x_a, 6),
            "x_beta": round(x_b, 6),
            "residual_norm": float(res_norm),
            "f_residual": float(f_val),
            "g_residual": float(g_val),
            "unit": "cal/mol" if use_calories else "J/mol",
        }

    @staticmethod
    def invert_interaction_parameters(
        t_kelvin: float,
        x_alpha: float,
        x_beta: float,
        delta_g_a: float,
        delta_g_b: float,
        use_calories: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculates regular solution interaction parameters (E_alpha, E_beta)
        from experimentally measured phase boundaries (X_alpha, X_beta) at temperature T,
        inverting Mallik (1986) Equations (10) and (11) as described in Appendix 1.

        System:
            [ X_alpha^2        -X_beta^2       ] [ E_alpha ]   [ Delta G_A + RT*ln((1-X_beta)/(1-X_alpha)) ]
            [ (1-X_alpha)^2   -(1-X_beta)^2    ] [ E_beta  ] = [ Delta G_B + RT*ln(X_beta/X_alpha)         ]

        Parameters:
            t_kelvin: Temperature in Kelvin.
            x_alpha: Measured atomic fraction of solute in alpha phase.
            x_beta: Measured atomic fraction of solute in beta phase.
            delta_g_a: Pure element A lattice stability (G_A^beta - G_A^alpha).
            delta_g_b: Pure element B lattice stability (G_B^beta - G_B^alpha).
            use_calories: Unit convention flag.

        Returns:
            Dictionary with computed E_alpha, E_beta, condition number, and validation residuals.
        """
        if t_kelvin <= 0.0:
            raise ValueError(f"Temperature must be strictly positive: {t_kelvin} K")
        if not (0.0 < x_alpha < 1.0) or not (0.0 < x_beta < 1.0):
            raise ValueError(f"Phase compositions must lie strictly in (0, 1): x_alpha={x_alpha}, x_beta={x_beta}")
        if abs(x_alpha - x_beta) < 1e-5:
            raise ValueError(f"Phase boundaries cannot be identical (x_alpha={x_alpha}, x_beta={x_beta})")

        r_const = R_CAL_MOL_K if use_calories else R_J_MOL_K
        rt = r_const * t_kelvin

        # Right-hand side constants b1 and b2
        b1 = delta_g_a + rt * math.log((1.0 - x_beta) / (1.0 - x_alpha))
        b2 = delta_g_b + rt * math.log(x_beta / x_alpha)

        # Coefficient matrix:
        # M = [[a11, a12], [a21, a22]]
        # a11 = x_alpha^2,         a12 = -x_beta^2
        # a21 = (1 - x_alpha)^2,   a22 = -(1 - x_beta)^2
        a11 = x_alpha ** 2
        a12 = -(x_beta ** 2)
        a21 = (1.0 - x_alpha) ** 2
        a22 = -((1.0 - x_beta) ** 2)

        det_m = a11 * a22 - a12 * a21

        if abs(det_m) < 1e-12:
            raise ValueError("Degenerate linear system: determinant near zero. Insufficient compositional divergence.")

        # Analytical inversion
        e_alpha = (a22 * b1 - a12 * b2) / det_m
        e_beta = (-a21 * b1 + a11 * b2) / det_m

        # Validation check by re-evaluating residuals
        f_check = delta_g_a + rt * math.log((1.0 - x_beta) / (1.0 - x_alpha)) - e_alpha * a11 - e_beta * a12
        g_check = delta_g_b + rt * math.log(x_beta / x_alpha) - e_alpha * a21 - e_beta * a22

        return {
            "t_kelvin": round(t_kelvin, 3),
            "x_alpha": round(x_alpha, 6),
            "x_beta": round(x_beta, 6),
            "e_alpha": round(e_alpha, 3),
            "e_beta": round(e_beta, 3),
            "determinant": float(det_m),
            "residual_f": float(f_check),
            "residual_g": float(g_check),
            "unit": "cal/mol" if use_calories else "J/mol",
        }

    @staticmethod
    def calculate_miscibility_gap(
        interaction_parameter: float,
        t_kelvin: float,
        use_calories: bool = False,
        tol: float = 1e-7,
        max_iter: int = 100,
    ) -> Optional[Dict[str, float]]:
        """
        Solves symmetrical miscibility gap boundaries and spinodal points for a single phase
        with positive interaction parameter E when E > 2RT (Mallik Section 8.2).

        Critical Temperature:
            T_c = E / (2R)
        Binodal (Solvus) condition:
            RT * ln(X / (1 - X)) + E * (1 - 2X) = 0
        Spinodal condition:
            d^2 G / dX^2 = 0 => X * (1 - X) = RT / (2E)
        """
        r_const = R_CAL_MOL_K if use_calories else R_J_MOL_K
        t_crit = interaction_parameter / (2.0 * r_const)

        if t_kelvin >= t_crit:
            # Completely miscible single-phase solid/liquid solution
            return None

        rt = r_const * t_kelvin

        # Spinodal analytical limits: X^2 - X + RT/(2E) = 0
        disc = 1.0 - 4.0 * (rt / (2.0 * interaction_parameter))
        spinodal_1 = 0.5 - 0.5 * math.sqrt(max(0.0, disc))
        spinodal_2 = 0.5 + 0.5 * math.sqrt(max(0.0, disc))

        # Binodal iteration starting from dilute solution
        x = max(1e-5, spinodal_1 * 0.5)
        for _ in range(max_iter):
            x = max(1e-6, min(0.5 - 1e-6, x))
            f_val = rt * math.log(x / (1.0 - x)) + interaction_parameter * (1.0 - 2.0 * x)
            if abs(f_val) < tol:
                break
            df_dx = rt / (x * (1.0 - x)) - 2.0 * interaction_parameter
            if abs(df_dx) < 1e-12:
                break
            step = f_val / df_dx
            x = max(1e-6, min(0.5 - 1e-6, x - step))

        binodal_1 = x
        binodal_2 = 1.0 - x

        return {
            "t_kelvin": round(t_kelvin, 3),
            "t_critical": round(t_crit, 3),
            "binodal_x1": round(binodal_1, 6),
            "binodal_x2": round(binodal_2, 6),
            "spinodal_x1": round(spinodal_1, 6),
            "spinodal_x2": round(spinodal_2, 6),
            "gap_width": round(binodal_2 - binodal_1, 6),
            "unit": "cal/mol" if use_calories else "J/mol",
        }

    @staticmethod
    def calculate_binary_phase_boundaries(
        delta_g_a_fn: Callable[[float], float],
        delta_g_b_fn: Callable[[float], float],
        e_alpha: float,
        e_beta: float,
        t_min: float = 600.0,
        t_max: float = 1600.0,
        num_temperatures: int = 50,
        use_calories: bool = False,
    ) -> Dict[str, Any]:
        """
        Traces phase boundaries across a temperature range using sequential Newton-Raphson
        continuation starting from the melting points or boundary extremes.

        Parameters:
            delta_g_a_fn: Function of temperature returning Delta G_A(T).
            delta_g_b_fn: Function of temperature returning Delta G_B(T).
            e_alpha: Interaction parameter of alpha phase.
            e_beta: Interaction parameter of beta phase.
            t_min: Lower temperature bound in Kelvin.
            t_max: Upper temperature bound in Kelvin.
            num_temperatures: Number of temperature sampling points.
            use_calories: Unit flag.
        """
        temps = np.linspace(t_max, t_min, num_temperatures).tolist()
        t_results = []
        x_alpha_series = []
        x_beta_series = []

        curr_guess = (0.2, 0.8)

        for t_k in temps:
            dg_a = delta_g_a_fn(t_k)
            dg_b = delta_g_b_fn(t_k)

            res = KaufmanMallikEngine.solve_binary_common_tangent(
                t_kelvin=t_k,
                delta_g_a=dg_a,
                delta_g_b=dg_b,
                e_alpha=e_alpha,
                e_beta=e_beta,
                initial_guess=curr_guess,
                max_iter=100,
                tol=1e-6,
                use_calories=use_calories,
            )

            if res["converged"]:
                t_results.append(round(t_k, 2))
                x_alpha_series.append(res["x_alpha"])
                x_beta_series.append(res["x_beta"])
                # Warm-start next step with converged points
                curr_guess = (res["x_alpha"], res["x_beta"])

        return {
            "temperatures": t_results,
            "x_alpha": x_alpha_series,
            "x_beta": x_beta_series,
            "count": len(t_results),
            "e_alpha": e_alpha,
            "e_beta": e_beta,
            "unit": "cal/mol" if use_calories else "J/mol",
        }

    @staticmethod
    def solve_ternary_isothermal_tie_lines(
        t_kelvin: float,
        g_pure_1: Tuple[float, float, float],
        g_pure_2: Tuple[float, float, float],
        e1_ij: float,
        e1_ik: float,
        e1_jk: float,
        e2_ij: float,
        e2_ik: float,
        e2_jk: float,
        num_tie_lines: int = 15,
        use_calories: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculates isothermal ternary phase boundaries and tie-lines between phase 1 (e.g. Liquid)
        and phase 2 (e.g. Solid) according to Mallik (1986) Section 8 and Appendix 2.

        Parameters:
            t_kelvin: Isothermal temperature in Kelvin.
            g_pure_1: (G_I^1, G_J^1, G_K^1) free energies of pure elements in phase 1.
            g_pure_2: (G_I^2, G_J^2, G_K^2) free energies of pure elements in phase 2.
            e1_ij, e1_ik, e1_jk: Binary interaction parameters in phase 1.
            e2_ij, e2_ik, e2_jk: Binary interaction parameters in phase 2.
            num_tie_lines: Number of tie-line rays to trace across the ternary section.
            use_calories: Unit convention flag.

        Returns:
            Dictionary with tie-line endpoints (X1, Y1, Z1) and (X2, Y2, Z2) on ternary Gibbs triangle.
        """
        r_const = R_CAL_MOL_K if use_calories else R_J_MOL_K
        rt = r_const * t_kelvin

        # Lattice stability Delta G_i^{1->2} = G_i^2 - G_i^1
        dg_i = g_pure_2[0] - g_pure_1[0]
        dg_j = g_pure_2[1] - g_pure_1[1]
        dg_k = g_pure_2[2] - g_pure_1[2]

        delta_e1 = e1_ij + e1_ik - e1_jk
        delta_e2 = e2_ij + e2_ik - e2_jk

        tie_lines = []

        # Sweep independent coordinate X1 along the IJ binary edge towards JK
        x1_steps = np.linspace(0.05, 0.90, num_tie_lines)

        x2_guess = 0.5
        y1_guess = 0.1
        y2_guess = 0.1

        for x1 in x1_steps:
            z1 = max(1e-5, 1.0 - x1 - y1_guess)

            # Solve the 3x3 non-linear system (Mallik Eq. 21) for (X2, Y1, Y2) via Newton-Raphson
            x2 = x2_guess
            y1 = y1_guess
            y2 = y2_guess

            converged = False
            for _ in range(80):
                z1 = max(1e-6, 1.0 - x1 - y1)
                z2 = max(1e-6, 1.0 - x2 - y2)

                x1 = max(1e-6, min(1.0 - 1e-6, x1))
                x2 = max(1e-6, min(1.0 - 1e-6, x2))
                y1 = max(1e-6, min(1.0 - 1e-6, y1))
                y2 = max(1e-6, min(1.0 - 1e-6, y2))

                # Mallik Eq. (21):
                # A_i = Delta G_i + RT*ln(Z2/Z1) + (E2_ij*X2^2 - E1_ij*X1^2) + (E2_ik*Y2^2 - E1_ik*Y1^2) + (Delta_E2*X2*Y2 - Delta_E1*X1*Y1)
                a_i = (
                    dg_i
                    + rt * math.log(z2 / z1)
                    + (e2_ij * (x2 ** 2) - e1_ij * (x1 ** 2))
                    + (e2_ik * (y2 ** 2) - e1_ik * (y1 ** 2))
                    + (delta_e2 * x2 * y2 - delta_e1 * x1 * y1)
                )

                # A_j = Delta G_j + RT*ln(X2/X1) + [E2_ij*(1-X2)^2 - E1_ij*(1-X1)^2] + (E2_jk*Y2^2 - E1_jk*Y1^2) - [Delta_E2*Y2*(1-X2) - Delta_E1*Y1*(1-X1)]
                a_j = (
                    dg_j
                    + rt * math.log(x2 / x1)
                    + (e2_ij * ((1.0 - x2) ** 2) - e1_ij * ((1.0 - x1) ** 2))
                    + (e2_jk * (y2 ** 2) - e1_jk * (y1 ** 2))
                    - (delta_e2 * y2 * (1.0 - x2) - delta_e1 * y1 * (1.0 - x1))
                )

                # A_k = Delta G_k + RT*ln(Y2/Y1) + (E2_jk*X2^2 - E1_jk*X1^2) + [E2_ik*(1-Y2)^2 - E1_ik*(1-Y1)^2] - [Delta_E2*X2*(1-Y2) - Delta_E1*X1*(1-Y1)]
                a_k = (
                    dg_k
                    + rt * math.log(y2 / y1)
                    + (e2_jk * (x2 ** 2) - e1_jk * (x1 ** 2))
                    + (e2_ik * ((1.0 - y2) ** 2) - e1_ik * ((1.0 - y1) ** 2))
                    - (delta_e2 * x2 * (1.0 - y2) - delta_e1 * x1 * (1.0 - y1))
                )

                res = math.sqrt(a_i ** 2 + a_j ** 2 + a_k ** 2)
                if res < 1e-6:
                    converged = True
                    break

                # 3x3 Jacobian with respect to (X2, Y1, Y2)
                # d/dX2
                da_i_dx2 = -rt / z2 + 2.0 * e2_ij * x2 + delta_e2 * y2
                da_j_dx2 = rt / x2 - 2.0 * e2_ij * (1.0 - x2) + delta_e2 * y2
                da_k_dx2 = 2.0 * e2_jk * x2 - delta_e2 * (1.0 - y2)

                # d/dY1
                da_i_dy1 = rt / z1 - 2.0 * e1_ik * y1 - delta_e1 * x1
                da_j_dy1 = -2.0 * e1_jk * y1 + delta_e1 * (1.0 - x1)
                da_k_dy1 = -rt / y1 - 2.0 * e1_ik * (1.0 - y1) + delta_e1 * x1

                # d/dY2
                da_i_dy2 = -rt / z2 + 2.0 * e2_ik * y2 + delta_e2 * x2
                da_j_dy2 = 2.0 * e2_jk * y2 - delta_e2 * (1.0 - x2)
                da_k_dy2 = rt / y2 - 2.0 * e2_ik * (1.0 - y2) + delta_e2 * x2

                jac = np.array(
                    [
                        [da_i_dx2, da_i_dy1, da_i_dy2],
                        [da_j_dx2, da_j_dy1, da_j_dy2],
                        [da_k_dx2, da_k_dy1, da_k_dy2],
                    ],
                    dtype=float,
                )

                rhs = -np.array([a_i, a_j, a_k], dtype=float)

                try:
                    delta = np.linalg.solve(jac, rhs)
                except np.linalg.LinAlgError:
                    break

                step_size = 1.0
                for _ in range(4):
                    nx2 = x2 + step_size * delta[0]
                    ny1 = y1 + step_size * delta[1]
                    ny2 = y2 + step_size * delta[2]
                    if (
                        0.001 < nx2 < 0.99
                        and 0.001 < ny1 < 0.99
                        and 0.001 < ny2 < 0.99
                        and (nx2 + ny2 < 0.999)
                        and (x1 + ny1 < 0.999)
                    ):
                        x2, y1, y2 = nx2, ny1, ny2
                        break
                    step_size *= 0.5
                else:
                    x2 = max(0.001, min(0.99, x2 + step_size * delta[0]))
                    y1 = max(0.001, min(0.99, y1 + step_size * delta[1]))
                    y2 = max(0.001, min(0.99, y2 + step_size * delta[2]))

            if converged and (x1 + y1 < 1.0) and (x2 + y2 < 1.0):
                z1 = 1.0 - x1 - y1
                z2 = 1.0 - x2 - y2
                tie_lines.append(
                    {
                        "phase1": {"X": round(float(x1), 4), "Y": round(float(y1), 4), "Z": round(float(z1), 4)},
                        "phase2": {"X": round(float(x2), 4), "Y": round(float(y2), 4), "Z": round(float(z2), 4)},
                        "residual": round(float(res), 7),
                    }
                )
                x2_guess, y1_guess, y2_guess = x2, y1, y2

        return {
            "t_kelvin": round(t_kelvin, 2),
            "tie_lines": tie_lines,
            "count": len(tie_lines),
            "unit": "cal/mol" if use_calories else "J/mol",
        }

    @staticmethod
    def nelder_mead_gibbs_minimizer(
        gibbs_function: Callable[[np.ndarray], float],
        initial_simplex: np.ndarray,
        max_iter: int = 250,
        tol: float = 1e-6,
    ) -> Dict[str, Any]:
        """
        Nelder-Mead simplex optimization on the Gibbs free energy surface
        as outlined by Mallik (1986) Section 9 (Nelder & Mead 1965, Counsell et al. 1971).
        Performs direct search reflection, expansion, contraction, and shrinkage without gradients.

        Parameters:
            gibbs_function: Callable accepting composition vector and returning Gibbs energy.
            initial_simplex: (N+1, N) array of starting vertex compositions.
            max_iter: Max iterations.
            tol: Standard deviation of vertex function values termination criterion.

        Returns:
            Dictionary with optimal composition vector, minimum energy, and iteration count.
        """
        simplex = np.copy(initial_simplex)
        n_verts, n_dim = simplex.shape
        if n_verts != n_dim + 1:
            raise ValueError(f"Simplex must have N+1 vertices for N dimensions: {n_verts} != {n_dim + 1}")

        alpha = 1.0  # Reflection
        gamma = 2.0  # Expansion
        rho = 0.5    # Contraction
        sigma = 0.5  # Shrink

        f_vals = np.array([gibbs_function(v) for v in simplex], dtype=float)

        iterations = 0
        for it in range(1, max_iter + 1):
            iterations = it

            # Sort vertices by energy value
            order = np.argsort(f_vals)
            simplex = simplex[order]
            f_vals = f_vals[order]

            # Termination test: std dev of vertex function values
            if np.std(f_vals) < tol:
                break

            # Centroid of best N vertices (excluding worst vertex N+1)
            x_bar = np.mean(simplex[:-1], axis=0)
            x_worst = simplex[-1]
            f_worst = f_vals[-1]

            # 1. Reflection
            x_r = x_bar + alpha * (x_bar - x_worst)
            f_r = gibbs_function(x_r)

            if f_vals[0] <= f_r < f_vals[-2]:
                simplex[-1] = x_r
                f_vals[-1] = f_r
                continue

            # 2. Expansion
            if f_r < f_vals[0]:
                x_e = x_bar + gamma * (x_r - x_bar)
                f_e = gibbs_function(x_e)
                if f_e < f_r:
                    simplex[-1] = x_e
                    f_vals[-1] = f_e
                else:
                    simplex[-1] = x_r
                    f_vals[-1] = f_r
                continue

            # 3. Contraction
            if f_r < f_worst:
                # Outside contraction
                x_c = x_bar + rho * (x_r - x_bar)
                f_c = gibbs_function(x_c)
                if f_c <= f_r:
                    simplex[-1] = x_c
                    f_vals[-1] = f_c
                    continue
            else:
                # Inside contraction
                x_c = x_bar - rho * (x_bar - x_worst)
                f_c = gibbs_function(x_c)
                if f_c < f_worst:
                    simplex[-1] = x_c
                    f_vals[-1] = f_c
                    continue

            # 4. Shrink
            for i in range(1, n_verts):
                simplex[i] = simplex[0] + sigma * (simplex[i] - simplex[0])
                f_vals[i] = gibbs_function(simplex[i])

        best_idx = np.argmin(f_vals)
        return {
            "converged": bool(np.std(f_vals) < tol),
            "iterations": iterations,
            "min_gibbs_energy": float(f_vals[best_idx]),
            "optimal_composition": simplex[best_idx].tolist(),
            "vertex_spread": float(np.std(f_vals)),
        }

    @classmethod
    def get_classic_presets(cls) -> Dict[str, Dict[str, Any]]:
        """
        Returns verified historical reference presets evaluated in Mallik (1986).
        """
        return {
            "isomorphous_ideal": {
                "name": "Ideal Isomorphous Binary System (Mallik 1986 Fig. 2a)",
                "description": "Lens-shaped continuous liquid-solid equilibrium with zero interaction parameters.",
                "t_m_a": 1000.0,
                "t_m_b": 1500.0,
                "delta_s_f_a": 10.0,
                "delta_s_f_b": 10.0,
                "e_liquid": 0.0,
                "e_solid": 0.0,
                "unit": "cal/mol",
                "topology": "Isomorphous",
            },
            "miscibility_gap_solid": {
                "name": "Solid State Miscibility Gap (Mallik 1986 Fig. 2b)",
                "description": "Enlarged solidification interval with symmetrical alpha1 + alpha2 decomposition.",
                "t_m_a": 1000.0,
                "t_m_b": 1500.0,
                "delta_s_f_a": 10.0,
                "delta_s_f_b": 10.0,
                "e_liquid": 0.0,
                "e_solid": 2500.0,
                "unit": "cal/mol",
                "topology": "Miscibility Gap",
            },
            "peritectic_positive_E": {
                "name": "Invariant Peritectic Reaction (Mallik 1986 Fig. 2d)",
                "description": "Peritectic invariant reaction appearing between 4250 and 4500 cal/mol.",
                "t_m_a": 1000.0,
                "t_m_b": 1500.0,
                "delta_s_f_a": 10.0,
                "delta_s_f_b": 10.0,
                "e_liquid": 4500.0,
                "e_solid": 4500.0,
                "unit": "cal/mol",
                "topology": "Peritectic",
            },
            "monotectic_high_E": {
                "name": "Invariant Monotectic Reaction (Mallik 1986 Fig. 2f)",
                "description": "Liquid immiscibility gap (L1 + L2) and monotectic reaction at E >= 5500 cal/mol.",
                "t_m_a": 1000.0,
                "t_m_b": 1500.0,
                "delta_s_f_a": 10.0,
                "delta_s_f_b": 10.0,
                "e_liquid": 6000.0,
                "e_solid": 6000.0,
                "unit": "cal/mol",
                "topology": "Monotectic",
            },
            "allotropy_eutectoid": {
                "name": "Allotropic Invariant Eutectoid Reaction (Mallik 1986 Fig. 3b)",
                "description": "Three competing phases (Liquid, alpha, beta) with azeotropic minima and eutectoid reaction.",
                "t_m_a": 1700.0,
                "t_m_b": 1600.0,
                "e_liquid": 100.0,
                "e_beta": 1000.0,
                "e_alpha": 3000.0,
                "unit": "cal/mol",
                "topology": "Eutectoid",
            },
            "ternary_mo_v_w": {
                "name": "Mo-V-W Isomorphous Ternary System (Bhansali & Mallik 1984)",
                "description": "Refractory BCC ternary system where all three binary subsystems exhibit complete solid solubility.",
                "components": ["Mo", "V", "W"],
                "isotherms": [2500.0, 3000.0],
                "unit": "cal/mol",
                "topology": "Ternary Isomorphous",
            },
            "ternary_cd_pb_sn": {
                "name": "Cd-Pb-Sn Ternary Eutectic System (Bhansali & Mallik 1984)",
                "description": "Low-melting eutectic ternary system with liquidus projection matching thermal analysis.",
                "components": ["Cd", "Pb", "Sn"],
                "eutectic_temperature_k": 418.0,
                "unit": "cal/mol",
                "topology": "Ternary Eutectic",
            },
        }
