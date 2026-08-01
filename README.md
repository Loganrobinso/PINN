# Multimodal PINN for Transient Heat Conduction

A physics-informed neural network (PINN) that reconstructs a full 2D transient
temperature field by fusing two synthetic sensor modalities:

1. **Sparse point sensors** — a handful of thermocouple-like time series
2. **Sparse-in-time full-field snapshots** — noisy, low-resolution "camera" frames

The heat equation is used as a physics loss term, letting the network infer
temperature structure that neither modality alone fully captures.

## Status
🚧 Week 1 — FD ground-truth solver done; baseline 1D PINN up next.

## Project Plan

- **Week 1** — Classical FD solver (ground truth) + basic 1D PINN sanity check
- **Week 2** — Generate synthetic multimodal dataset; train sensor-only PINN baseline
- **Week 3** — Add field-snapshot modality; compare sensors-only vs. camera-only vs. fused
- **Week 4** — Error analysis, ablations, writeup, visualizations

## Repo Structure

```
.
├── entrypoint.sh            # builds the image (if needed) and runs a command in it
├── docker/
│   ├── Dockerfile
│   └── build_docker.sh
├── requirements.txt
├── src/
│   └── fd_solver.py         # ground-truth finite-difference solver
├── notebooks/                # exploratory notebooks
├── data/                     # generated synthetic datasets (gitignored)
├── results/                   # figures, metrics, checkpoints (gitignored)
└── README.md
```

## Setup

### With Docker (recommended)
`entrypoint.sh` builds the image on first run (and rebuilds automatically if
`docker/Dockerfile` or `requirements.txt` change), then runs your command
inside the container with the repo mounted at `/app`. GPU passthrough is
used automatically if `nvidia-smi` and Docker's NVIDIA runtime are available,
otherwise it falls back to CPU.

```bash
./entrypoint.sh python src/fd_solver.py
```

Drop into an interactive shell with no arguments:
```bash
./entrypoint.sh
```

### Without Docker
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the finite-difference solver to generate ground truth:
```bash
./entrypoint.sh python src/fd_solver.py
```

This writes the full spatiotemporal field to `data/fd_ground_truth.npz`
(`times`, `x`, `y`, `T`) and a sanity-check plot to
`results/fd_sanity_check.png`.

## Physics Setup (Week 1)

- Domain: 2D plate, 10cm x 10cm
- Boundary conditions: insulated (Neumann, zero-flux) edges
- Heat source: fixed-position Gaussian flux at the plate center
- Governing equation: 2D transient heat conduction,
  `∂T/∂t = α * (∂²T/∂x² + ∂²T/∂y²) + Q(x,y,t)`
