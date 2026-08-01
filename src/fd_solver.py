"""Finite-difference ground-truth generator for 2D transient heat conduction.

Plate with a fixed Gaussian heat source and insulated (zero-flux) edges:

    dT/dt = alpha * (d2T/dx2 + d2T/dy2) + Q(x, y) / (rho * cp)

T is reported as temperature rise above a uniform ambient initial condition
(T=0 at t=0). This solver is the ground truth against which the PINN
(sensors-only, camera-only, fused) will later be compared.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from tqdm import trange


@dataclass
class Config:
    # Domain
    Lx: float = 0.10   # plate width [m]
    Ly: float = 0.10   # plate height [m]
    nx: int = 101       # grid points in x
    ny: int = 101       # grid points in y

    # Material (loosely stainless-steel-like)
    k: float = 15.0       # thermal conductivity [W/(m*K)]
    rho: float = 8000.0   # density [kg/m^3]
    cp: float = 500.0     # specific heat [J/(kg*K)]

    # Heat source: fixed position, Gaussian in space, constant in time
    source_x: float = 0.05
    source_y: float = 0.05
    source_sigma: float = 0.008          # Gaussian std dev [m]
    source_power_density: float = 5.0e7  # peak volumetric power [W/m^3]

    # Time stepping
    t_end: float = 60.0          # total simulated time [s]
    safety_factor: float = 0.4   # fraction of the explicit stability limit

    # Output
    save_every: int = 10  # keep every Nth timestep in the saved field history

    @property
    def alpha(self) -> float:
        """Thermal diffusivity [m^2/s]."""
        return self.k / (self.rho * self.cp)


def gaussian_source(cfg: Config, X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Source contribution to dT/dt [K/s], fixed in time."""
    r2 = (X - cfg.source_x) ** 2 + (Y - cfg.source_y) ** 2
    q = cfg.source_power_density * np.exp(-r2 / (2 * cfg.source_sigma ** 2))
    return q / (cfg.rho * cfg.cp)


def laplacian_neumann(T: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """5-point Laplacian with zero-flux boundaries (edge-padded ghost nodes)."""
    Tp = np.pad(T, 1, mode="edge")
    d2Tdx2 = (Tp[1:-1, 2:] - 2 * Tp[1:-1, 1:-1] + Tp[1:-1, :-2]) / dx ** 2
    d2Tdy2 = (Tp[2:, 1:-1] - 2 * Tp[1:-1, 1:-1] + Tp[:-2, 1:-1]) / dy ** 2
    return d2Tdx2 + d2Tdy2


def run_simulation(cfg: Config):
    """Explicit FD time-stepping. Returns (times, x, y, T_history)."""
    x = np.linspace(0, cfg.Lx, cfg.nx)
    y = np.linspace(0, cfg.Ly, cfg.ny)
    dx, dy = x[1] - x[0], y[1] - y[0]
    X, Y = np.meshgrid(x, y)

    dt_stable = dx ** 2 * dy ** 2 / (2 * cfg.alpha * (dx ** 2 + dy ** 2))
    dt = cfg.safety_factor * dt_stable
    n_steps = int(np.ceil(cfg.t_end / dt))

    T = np.zeros((cfg.ny, cfg.nx))
    S = gaussian_source(cfg, X, Y)

    times, snapshots = [0.0], [T.copy()]
    for step in trange(1, n_steps + 1, desc="FD solve"):
        T = T + dt * (cfg.alpha * laplacian_neumann(T, dx, dy) + S)
        if step % cfg.save_every == 0 or step == n_steps:
            times.append(step * dt)
            snapshots.append(T.copy())

    return np.array(times), x, y, np.stack(snapshots)


def plot_sanity_check(times, x, y, T_hist, out_path: Path):
    import matplotlib.pyplot as plt

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    for ax, frac in zip(axes[:2], (0.25, 1.0)):
        idx = int((len(times) - 1) * frac)
        im = ax.pcolormesh(x, y, T_hist[idx], shading="auto", cmap="inferno")
        ax.set_title(f"T field, t={times[idx]:.1f}s")
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        ax.set_aspect("equal")
        fig.colorbar(im, ax=ax, label="delta T [K]")

    cy, cx = T_hist.shape[1] // 2, T_hist.shape[2] // 2
    axes[2].plot(times, T_hist[:, cy, cx])
    axes[2].set_xlabel("time [s]")
    axes[2].set_ylabel("delta T at center [K]")
    axes[2].set_title("Center point time series")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t-end", type=float, default=60.0)
    parser.add_argument("--nx", type=int, default=101)
    parser.add_argument("--ny", type=int, default=101)
    parser.add_argument("--out", type=str, default="data/fd_ground_truth.npz")
    parser.add_argument("--plot", type=str, default="results/fd_sanity_check.png")
    args = parser.parse_args()

    cfg = Config(t_end=args.t_end, nx=args.nx, ny=args.ny)
    print(f"alpha = {cfg.alpha:.3e} m^2/s")

    times, x, y, T_hist = run_simulation(cfg)
    print(f"saved {len(times)} snapshots, final max delta T = {T_hist[-1].max():.2f} K")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, times=times, x=x, y=y, T=T_hist)
    print(f"wrote ground truth to {out_path}")

    plot_path = Path(args.plot)
    plot_sanity_check(times, x, y, T_hist, plot_path)
    print(f"wrote sanity plot to {plot_path}")


if __name__ == "__main__":
    main()
