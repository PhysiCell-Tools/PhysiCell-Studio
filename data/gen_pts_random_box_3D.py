import numpy as np

cell_type_index = 0
# ncells = 1000
ncells = 100

# radius = 120
radius = 200
xmin = -radius
xrange = 2 * radius
ymin = -radius
yrange = 2 * radius
zmin = -radius
zrange = 2 * radius

for idx in range(ncells):
    xval = np.random.uniform() * xrange + xmin
    yval = np.random.uniform() * yrange + ymin
    zval = np.random.uniform() * zrange + zmin
    print(xval,",",yval,",",zval,",",cell_type_index)
