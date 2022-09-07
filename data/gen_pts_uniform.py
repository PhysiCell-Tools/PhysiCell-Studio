import numpy as np

cell_type_index = 0
ncells = 10
ncells = 1000
# recall radius of cell = 5
delta = 5.0
xmin = -120 + delta
xmax = 120 - delta
xrange = xmax - xmin
ymin = -120 + delta
ymax = 120 - delta
yrange = ymax - ymin
zmin = -120 + delta
zmax = 120 - delta
zrange = zmax - zmin

zdel = zrange / 10.
ydel = yrange / 10.
xdel = xrange / 10.
num_pts = 0
for zval in np.arange(zmin,zmax,zdel):
    for yval in np.arange(ymin,ymax,ydel):
        for xval in np.arange(xmin,xmax,xdel):
            print(xval,",",yval,",",zval,",",cell_type_index)
            num_pts += 1
print("num_pts = ",num_pts)
