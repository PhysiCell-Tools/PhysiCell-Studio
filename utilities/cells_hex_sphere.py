"""
Generate sphere center coordinates for hexagonal close-packed (HCP) arrangement.
Sphere radius is configurable; center-to-center distance = 2 * radius.
"""

import csv
import math
import argparse


def generate_hcp_centers(nx: int, ny: int, nz: int, radius: float = 1.0, overlap: float = 0.0) -> list[tuple[float, float, float]]:
    """
    Generate HCP sphere centers for an nx x ny x nz grid of spheres.

    HCP layer structure (ABABAB...):
      - Layer A: standard 2D hexagonal grid
      - Layer B: offset by (r, r/sqrt(3)*2, sqrt(2/3)*2r) relative to A

    With sphere radius r, nearest-neighbor distance d = 2r:
      dx  = 2r                     (within a row)
      dy  = r*sqrt(3)              (between rows in same layer)
      dz  = 2r*sqrt(2/3)          (between layers)
      Row offset in x = r          (alternating rows shift by half dx)
      B-layer offset  = (r, r/sqrt(3), dz)
    """
    d   = 2.0 * radius * (1.0 - overlap)  # center-to-center distance (overlap fraction of diameter)
    dx  = d                          # x spacing within a row
    dy  = d * math.sqrt(3) / 2       # row spacing within a layer
    dz  = d * math.sqrt(2 / 3)       # layer spacing

    centers = []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                # Row offset: odd rows shift by dx/2
                row_shift = (dx / 2) * (j % 2)

                # Layer offsets for HCP (ABABAB…)
                if k % 2 == 0:          # A layer
                    layer_x_shift = row_shift
                    layer_y_shift = 0.0
                else:                   # B layer
                    layer_x_shift = row_shift + dx / 2
                    layer_y_shift = dy / 3          # = 1/sqrt(3)

                x = i * dx + layer_x_shift
                y = j * dy + layer_y_shift
                z = k * dz

                centers.append((x, y, z))

    # Center the cluster about the origin
    cx = sum(p[0] for p in centers) / len(centers)
    cy = sum(p[1] for p in centers) / len(centers)
    cz = sum(p[2] for p in centers) / len(centers)
    centers = [(x - cx, y - cy, z - cz) for x, y, z in centers]

    return centers


def write_csv(centers: list[tuple[float, float, float]], filename: str, cell_type: str = "") -> None:
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["x", "y", "z", "type"])
        for cx, cy, cz in centers:
            writer.writerow([f"{cx:.6f}", f"{cy:.6f}", f"{cz:.6f}", cell_type])
    print(f"Wrote {len(centers)} sphere centers to '{filename}'")


def main():
    parser = argparse.ArgumentParser(
        description="Generate HCP sphere centers (radius=1) and save to CSV."
    )
    parser.add_argument("--nx", type=int, default=5, help="Spheres along X (default: 5)")
    parser.add_argument("--ny", type=int, default=5, help="Spheres along Y (default: 5)")
    parser.add_argument("--nz", type=int, default=4, help="Layers along Z (default: 4)")
    parser.add_argument("--radius", type=float, default=1.0, help="Sphere radius (default: 1.0)")
    parser.add_argument("--overlap", type=float, default=0.0, help="Overlap as fraction of diameter, e.g. 0.1 = 10%% (default: 0.0)")
    parser.add_argument("--name", default="", help="Cell type name written to the 'type' column")
    parser.add_argument("--radius1", type=float, default=None, help="Minimum distance from origin (default: 0)")
    parser.add_argument("--radius2", type=float, default=None, help="Maximum distance from origin (default: no limit)")
    parser.add_argument("--output", default="my_cells.csv", help="Output CSV filename")
    args = parser.parse_args()

    centers = generate_hcp_centers(args.nx, args.ny, args.nz, args.radius, args.overlap)
    if args.radius1 is not None or args.radius2 is not None:
        r1 = args.radius1 if args.radius1 is not None else 0.0
        r2 = args.radius2 if args.radius2 is not None else math.inf
        centers = [c for c in centers if r1 <= math.sqrt(c[0]**2 + c[1]**2 + c[2]**2) <= r2]
    write_csv(centers, args.output, args.name)

    # Quick sanity check: verify nearest-neighbor distances
    if len(centers) > 1:
        sample = centers[0]
        dists = sorted(
            math.dist(sample, c) for c in centers if c != sample
        )
        expected = 2.0 * args.radius * (1.0 - args.overlap)
        print(f"Nearest-neighbor distances from first center: "
              f"{dists[0]:.4f}, {dists[1]:.4f}, {dists[2]:.4f} "
              f"(expected ≈ {expected:.4f})")


if __name__ == "__main__":
    main()
