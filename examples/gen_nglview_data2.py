import nglview as nv
import numpy as np
t2 = nv.NGLWidget()
N = 1000
for idx in range(N):
#     t2.shape.add_sphere([6.16871824,5.46533263,4.98082383],[0.74180055,0.75457795,0.26040795], 2.5)
#     p = np.random.random(3)*10
    p = np.random.uniform(low=-100., high=100, size=3)
    c = np.random.random(3)
    t2.shape.add_sphere([p[0],p[1],p[2]], [c[0],c[1],c[2]], 2.5)

t2

