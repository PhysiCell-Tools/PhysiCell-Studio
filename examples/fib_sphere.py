# Uniformly distribute points on a sphere using the Fibonnaci sphere alg.
#
# Usage:
#    python fib_sphere.py <sphere-radius>  <# of pts>  <name-of-celltype>
#    e.g., confirm working
#    python fib_sphere.py 400.0 100 epi
#
#    then, save to a file in PhysiCell cells.csv format:
#    python fib_sphere.py 400.0 100 epi > fib3D.csv

import sys,string
import math

argc=len(sys.argv)
# print('argc=',argc)
# print('argv=',sys.argv)
# print('argv[0]=',sys.argv[0])
if argc < 4:
    print("Usage: <sphere-radius> <# of pts> <name-of-celltype>")
    sys.exit(-1)

#R = string.atof(sys.argv[1])
R = float(sys.argv[1])
npts = int(sys.argv[2])
celltype_name = sys.argv[3]

def fibonacci_sphere(samples=1000):
    # points = []
    phi = math.pi * (math.sqrt(5.) - 1.)  # golden angle in radians

#    R = 150.  # large sphere radius

    print(f"x,y,z,type,volume,cycle entry,custom:GFP,custom:sample")
    for i in range(samples):
        # generates points on a sphere of radius=1, centered at origin
        y = 1.0 - (i / float(samples - 1)) * 2.0  # y goes from 1 to -1
        radius = math.sqrt(1 - y * y)  # radius at y

        theta = phi * i  # golden angle increment

        x = math.cos(theta) * radius
        z = math.sin(theta) * radius
        # points.append((x, y, z))

        # scale points by R (again, assuming centered at origin)
        print(f"{R*x},{R*y},{R*z},{celltype_name}")  # as .csv: x,y,z,celltype

#    return points

fibonacci_sphere(npts)