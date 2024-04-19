# create ICs (hex packed, random choice of 2 types) for cellsorting  (hacked from ics_tab.py)
# Assume centered at 0,0. Provide R1, R2 on command line (as used in ICs)
#
# Sample usage:
#    python cellsort_ics.py 150 150 >cellsort_rand2.csv


import sys,string
import numpy as np

argc=len(sys.argv)
# print('argc=',argc)
# print('argv=',sys.argv)
# print('argv[0]=',sys.argv[0])
r1_value = float(sys.argv[1])
r2_value = float(sys.argv[2])

x0_value = 0.
y0_value = 0.
cell_radius = 8.412710547954228   # from PhysiCell_phenotype.cpp

x_min = -r1_value
x_max =  r1_value
y_min = -r2_value
y_max =  r2_value
y_idx = -1
# hex packing constants
x_spacing = cell_radius * 2
y_spacing = cell_radius * np.sqrt(3)

y_idx = 0
z_idx = 0

print("x,y,z,type,volume,cycle entry,custom:GFP,custom:sample")  # header (v2)
# 15.232974910394432,-20.822132616487465,0.0,ctypeA


if True:  # 2D
    zval = 0.0
    for yval in np.arange(y_min,y_max, y_spacing):
        y_idx += 1
        for xval in np.arange(x_min,x_max, x_spacing):
            # xval_offset = xval + (y_idx%2) * cell_radius
            xval_offset = x0_value + xval + (y_idx%2) * cell_radius
            yval_offset = yval + y0_value

            if np.random.uniform(0,1) < 0.5:
                print(f'{xval_offset},{yval_offset},0.0,ctypeA')
            else:
                print(f'{xval_offset},{yval_offset},0.0,ctypeB')
            # xlist.append(xval_offset)
            # ylist.append(yval_offset)
            # # csv_array = np.append(csv_array,[[xval,yval,zval, cell_type_index]],axis=0)
            # csv_array = np.append(csv_array,[[xval_offset,yval_offset, zval, cell_type_index]],axis=0)
            # rlist.append(rval)
            # cell_radii.append(cell_radius)
