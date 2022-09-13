import numpy as np

cell_type_index = 0
# ncells = 1000
ncells = 100

sphere_radius = 200

# radius = 120
radius = 200
xmin = -radius
xrange = 2 * radius
ymin = -radius
yrange = 2 * radius
zmin = -radius
zrange = 2 * radius

count = 0
while True:
    xval = np.random.uniform() * xrange + xmin
    yval = np.random.uniform() * yrange + ymin
    zval = np.random.uniform() * zrange + zmin
    d = np.sqrt(xval*xval + yval*yval + zval*zval)
    if d <= sphere_radius:
        print(xval,",",yval,",",zval,",",cell_type_index)
        count += 1
        if count == ncells:
            break
