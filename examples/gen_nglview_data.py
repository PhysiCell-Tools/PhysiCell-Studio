# This works on nanoHUB latest Jupyter notebook, but does it scale to tens of thousands of spheres?
#    import nglview as nv
#    t1 = nv.NGLWidget()
#    t1.shape.add_sphere([5, 2, 0], [1., 0., 0.], 2.5)
#    t1.shape.add_sphere([-5, 2, -1], [0., 1, 0.0], 3.5)
#    t1

import numpy as np

N=10
rscale=10
N=1000
for idx in range(N):
    p=np.random.random(3)
    c=np.random.random(3)
    # print(f't1.shape.add_sphere({500*p},{c}, 2.5)')
    p=str(p*rscale).replace(" ",",")
    p=p.replace("[,","[")
    p=p.replace(",]","]")

    c=str(c).replace(" ",",")
    c=c.replace("[,","[")
    c=c.replace(",]","]")
    # print(f't1.shape.add_sphere({p},{c}, 2.5)')

    p=p.replace(",,",",")
    p=p.replace(",,",",")

    c=c.replace(",,",",")
    c=c.replace(",,",",")
    print(f't1.shape.add_sphere({p},{c}, 2.5)')
    # print("------")