#
# Extract cell (type) clusters as graph connected components 
#  - this module requires the networkx Python module (in addition to others for plotting) 
#
__author__ = "Randy Heiland"

import sys
import os
# import pathlib
from pyMCDS import pyMCDS
import networkx as nx

try:
  import matplotlib
  import matplotlib.colors as mplc
  from matplotlib.patches import Circle, Ellipse, Rectangle
  from matplotlib.collections import PatchCollection
except:
  print("\n---Error: cannot import matplotlib")
  print("---Try: python -m pip install matplotlib")
#  print("---Consider installing Anaconda's Python 3 distribution.\n")
  raise
try:
  import numpy as np  # if mpl was installed, numpy should have been too.
except:
  print("\n---Error: cannot import numpy")
  print("---Try: python -m pip install numpy\n")
  raise
from collections import deque
try:
  # apparently we need mpl's Qt backend to do keypresses 
#  matplotlib.use("Qt5Agg")
  matplotlib.use("TkAgg")
  import matplotlib.pyplot as plt
except:
  print("\n---Error: cannot use matplotlib's TkAgg backend")
  raise

out_dir = 'output'
current_idx = 0
print("# args=",len(sys.argv))
# if (len(sys.argv) < 2):
#     # print(f'Usage: {sys.argv[0]}  <frame0> <frameN>')
#     print(f'Missing args: <start_frame>')
#     exit(-1)
# else:
#     kdx = 1
#     current_idx = int(sys.argv[1])
#     # iframe1 = int(sys.argv[2])
#     print("out_dir= ", out_dir)

# fig, ax = plt.subplots()

# ------- 1st plot all computed values (at every 10 hours)
hr_delta = 20
#hr_delta = 10
# for idx in range(0,615, hr_delta):

time_delay = 0.1

fig = plt.figure(figsize=(7,7))
ax = fig.gca()
ax.set_aspect("equal")

#-----------------------------------------------------
def circles(x, y, s, c='b', vmin=None, vmax=None, **kwargs):
    """
    See https://gist.github.com/syrte/592a062c562cd2a98a83 

    Make a scatter plot of circles. 
    Similar to plt.scatter, but the size of circles are in data scale.
    Parameters
    ----------
    x, y : scalar or array_like, shape (n, )
        Input data
    s : scalar or array_like, shape (n, ) 
        Radius of circles.
    c : color or sequence of color, optional, default : 'b'
        `c` can be a single color format string, or a sequence of color
        specifications of length `N`, or a sequence of `N` numbers to be
        mapped to colors using the `cmap` and `norm` specified via kwargs.
        Note that `c` should not be a single numeric RGB or RGBA sequence 
        because that is indistinguishable from an array of values
        to be colormapped. (If you insist, use `color` instead.)  
        `c` can be a 2-D array in which the rows are RGB or RGBA, however. 
    vmin, vmax : scalar, optional, default: None
        `vmin` and `vmax` are used in conjunction with `norm` to normalize
        luminance data.  If either are `None`, the min and max of the
        color array is used.
    kwargs : `~matplotlib.collections.Collection` properties
        Eg. alpha, edgecolor(ec), facecolor(fc), linewidth(lw), linestyle(ls), 
        norm, cmap, transform, etc.
    Returns
    -------
    paths : `~matplotlib.collections.PathCollection`
    Examples
    --------
    a = np.arange(11)
    circles(a, a, s=a*0.2, c=a, alpha=0.5, ec='none')
    plt.colorbar()
    License
    --------
    This code is under [The BSD 3-Clause License]
    (http://opensource.org/licenses/BSD-3-Clause)
    """

    if np.isscalar(c):
        kwargs.setdefault('color', c)
        c = None

    if 'fc' in kwargs:
        kwargs.setdefault('facecolor', kwargs.pop('fc'))
    if 'ec' in kwargs:
        kwargs.setdefault('edgecolor', kwargs.pop('ec'))
    if 'ls' in kwargs:
        kwargs.setdefault('linestyle', kwargs.pop('ls'))
    if 'lw' in kwargs:
        kwargs.setdefault('linewidth', kwargs.pop('lw'))
    # You can set `facecolor` with an array for each patch,
    # while you can only set `facecolors` with a value for all.

    zipped = np.broadcast(x, y, s)
    patches = [Circle((x_, y_), s_)
               for x_, y_, s_ in zipped]
    collection = PatchCollection(patches, **kwargs)
    if c is not None:
        c = np.broadcast_to(c, zipped.shape).ravel()
        collection.set_array(c)
        collection.set_clim(vmin, vmax)

    ax = plt.gca()
    ax.add_collection(collection)
    ax.autoscale_view()
    plt.draw_if_interactive()
    if c is not None:
        plt.sci(collection)
    return collection

#----------------------------------------------
# iframe = 6
# print("----- finding clusters for frame # ",iframe)
# for idx in [iframe]:
# for idx in range(iframe0,iframe1):
def plot_nbrs():
    global current_idx, axes_max
    xml_file_root = "output%08d.xml" % current_idx
    print("----------------------------------plot_nbrs():  current_idx= ",current_idx)
    # print("xml_file_root = ",xml_file_root)
    xml_file = os.path.join(out_dir, xml_file_root)

    # if not Path(xml_file).is_file():
    #     print("ERROR: file not found",xml_file)
    #     return

    try:
        mcds = pyMCDS(xml_file, microenv=False, graph=True, verbose=False)
    except:
        print("invalid file: ",xml_file)
        return

    current_time = mcds.get_time()
    # print('time (min)= ', current_time )

    xv = mcds.data['discrete_cells']['data']['position_x']
    yv = mcds.data['discrete_cells']['data']['position_y']
    r = mcds.data['discrete_cells']['data']['radius']
    ctypes = mcds.data['discrete_cells']['data']['cell_type']
    nbrs = mcds.data['discrete_cells']['graph']['neighbor_cells']
    # print("# cells= ",ctypes.shape[0])
    # print("ctypes= ",ctypes)

    rgb_list = deque()
    ctcolor = deque()
    for ct in ctypes:
        rgb = [1,0,0]
        # if ct == 0:
            # rgb = [0.6,0.6,0.6]
        # rgb_list.append(rgb)
        ctcolor.append('C' + str(int(ct)))   # use random colors from matplotlib; 
    # rgbs =  np.array(rgb_list)
    rgbs =  np.array(ctcolor)
    # print("nbrs= ",nbrs)

    # for cell_type in [0,1]:
    for cell_type in set(ctypes):
        print("\n------ int(cell_type) = ",int(cell_type))
        id_ctype = np.where(ctypes == cell_type)
        # print("id_ctype= ",id_ctype)
        # id_ctype = id_ctype[0]
        # print(id_ctype)
        max_idx = len(id_ctype)

        G = nx.Graph()

        kdx = 0
        kmax = len(id_ctype)
        # print("kmax= ",kmax)

        nbrs = mcds.data['discrete_cells']['graph']['neighbor_cells']
        # print("len(nbrs)= ",len(nbrs))
        # print("xv= ",xv)

        # for id in nbrs.keys():
        for id in id_ctype[0]:
            # print("-------- nbr id= ",id)
            nbr_ids = list(nbrs[id])
            # print("nbr_ids= ",nbr_ids)
            for jd in nbr_ids:
                # print("jd= ",jd)
                # if jd in id_ctype.any():
                if jd in id_ctype[0]:
                    # print(f'yes, {jd} is in {id_ctype[0]}')
                    G.add_edge(id,jd)
                    # print(f'    ------- edge: {id} -- {jd}')
                else:
                    # print(f'no, {jd} is NOT in {id_ctype[0]}')
                    pass

        # print(f'type(nx.connected_components(G)= {type(nx.connected_components(G))}') # <class 'generator'>
        lcc = list(nx.connected_components(G))
        print(f'   --->  lcc= {lcc}')
        # print(f'type(lcc[0])= {type(lcc[0])}')
        # print(f'{type(nx.connected_components(G))}')

        uset=set()  # universal set
        for iset in lcc:
            uset = uset.union(iset)
        # print("total set - lcc = ",set(id_ctype[0]) - lcc[0])
        # print("total set - lcc = ",set(id_ctype[0]) - uset)
        isolated_cells = list(set(id_ctype[0]) - uset)
        print("isolated_cells= ",isolated_cells)


    plt.cla()
    title_str = "time " + str(current_time) + " mins"
    plt.title(title_str)
    # plt.xlim(axes_min,axes_max)
    # plt.ylim(axes_min,axes_max)

    try:
    #circles(xvals,yvals, s=rvals, color=rgbs)
    # circles(xv,yv, s=r, color=ctype)
        circles(xv,yv, s=r, color=rgbs)

        # show IDs at cell centers
        for id in nbrs.keys():
            ax.text(xv[id], yv[id], int(id), fontsize=12)
    except:
        print("invalid frame")

    #plt.xlim(0,2000)  # TODO - get these values from width,height in .svg at top
    #plt.ylim(0,2000)
    plt.pause(time_delay)

plot_nbrs()

step_value = 1
def press(event):
  global current_idx, step_value
#    print('press', event.key)
  sys.stdout.flush()
  if event.key == 'escape':
    sys.exit(1)
  elif event.key == 'h':  # help
    print('esc: quit')
    print('right arrow: increment by step_value')
    print('left arrow:  decrement by step_value')
    print('up arrow:   increment step_value by 1')
    print('down arrow: decrement step_value by 1')
    print('0: reset to 0th frame')
    print('h: help')
  elif event.key == 'left':  # left arrow key
#    print('go backwards')
#    fig.canvas.draw()
    current_idx -= step_value
    if (current_idx < 0):
      current_idx = 0
    plot_nbrs()
  elif event.key == 'right':  # right arrow key
#        print('go forwards')
#        fig.canvas.draw()
    current_idx += step_value
    plot_nbrs()
  elif event.key == 'up':  # up arrow key
    step_value += 1
    print('step_value=',step_value)
  elif event.key == 'down':  # down arrow key
    step_value -= 1
    if (step_value <= 0):
      step_value = 1
    print('step_value=',step_value)
  elif event.key == '0':  # reset to 0th frame/file
    current_idx = 0
    plot_nbrs()
  else:
    print('press', event.key)


#for current_idx in range(40):
#  fname = "snapshot%08d.svg" % current_idx
#  plot_nbrs(fname)
# plot_nbrs()
print("\nNOTE: click in plot window to give it focus before using keys.")

fig.canvas.mpl_connect('key_press_event', press)

# keep last plot displayed
#plt.ioff()
plt.show()