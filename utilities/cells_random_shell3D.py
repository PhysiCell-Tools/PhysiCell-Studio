"""
Generate random cell positions within a spherical shell defined by radius1 and radius2.
Positions are uniformly distributed in volume (not surface) between the two radii.
"""

import csv
import math
import random
import argparse


def generate_random_centers(n: int, r1: float, r2: float) -> list[tuple[float, float, float]]:
    """
    Generate n points uniformly distributed in the spherical shell r1 <= r <= r2.

    Uses the inverse-CDF method for radial sampling so density is uniform in
    volume (not biased toward the center), combined with a normalized Gaussian
    for a uniform random direction on the unit sphere.
    """
    centers = []
    r1_cubed = r1 ** 3
    r2_cubed = r2 ** 3
    while len(centers) < n:
        # Uniform radial sample by inverse CDF: r = (r1^3 + u*(r2^3 - r1^3))^(1/3)
        u = random.random()
        r = (r1_cubed + u * (r2_cubed - r1_cubed)) ** (1.0 / 3.0)
        # Uniform direction via normalized Gaussian
        x = random.gauss(0, 1)
        y = random.gauss(0, 1)
        z = random.gauss(0, 1)
        norm = math.sqrt(x*x + y*y + z*z)
        if norm == 0:
            continue
        scale = r / norm
        centers.append((x * scale, y * scale, z * scale))
    return centers


def write_csv(centers: list[tuple[float, float, float]], filename: str, cell_type: str = "") -> None:
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["x", "y", "z", "type"])
        for cx, cy, cz in centers:
            writer.writerow([f"{cx:.6f}", f"{cy:.6f}", f"{cz:.6f}", cell_type])
    print(f"Wrote {len(centers)} cell positions to '{filename}'")


def main():
    parser = argparse.ArgumentParser(
        description="Generate random cell positions within a spherical shell and save to CSV."
    )
    parser.add_argument("--count", type=int, default=100, help="Number of cells to generate (default: 100)")
    parser.add_argument("--radius1", type=float, default=0.0, help="Inner radius of spherical shell (default: 0)")
    parser.add_argument("--radius2", type=float, default=100.0, help="Outer radius of spherical shell (default: 100)")
    parser.add_argument("--name", default="", help="Cell type name written to the 'type' column")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--output", default="my_cells.csv", help="Output CSV filename")
    args = parser.parse_args()

    if args.radius1 < 0 or args.radius2 <= 0 or args.radius1 >= args.radius2:
        parser.error("Must satisfy 0 <= radius1 < radius2")

    if args.seed is not None:
        random.seed(args.seed)

    centers = generate_random_centers(args.count, args.radius1, args.radius2)
    write_csv(centers, args.output, args.name)


if __name__ == "__main__":
    main()
