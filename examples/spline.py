from PyQt5 import QtWidgets
from PyQt5.Qt import Qt

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
import matplotlib.colors as mplc
from scipy.special import comb

__author__ = "Randy Heiland, Intelligent Systems Engineering, Luddy SICE, Indiana University"

class MplWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MplWidget, self).__init__(parent)
        self.canvas = FigureCanvas(Figure())

        vertical_layout = QtWidgets.QVBoxLayout(self)
        vertical_layout.addWidget(self.canvas)

        self.instructions = f"'n' new celltype, 'u' undo, 's' save, 'c' clear"
        self.cell_type_name = "default"
        self.cell_volume = 2494.0
        self.cell_radius = (self.cell_volume * 0.75 / np.pi) ** (1./3)
        print(f"default self.cell_radius= {self.cell_radius}")
        # self.cell_radius = 8.412710547954228   # from PhysiCell_phenotype.cpp
        self.color_by_celltype = ['gray','red','green','yellow','cyan','magenta','blue','brown','black','orange','seagreen','gold']
        self.cell_type_color = 'gray'

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.ax0 = self.canvas.axes
        self.ax0.set_title(self.instructions, fontsize=10)
        self.ax0.grid(True)

        self.num_pts = 0
        self.bezpts = np.zeros((4,2))
        self.bez_plot = []
        self.bplot_name = []
        self.bplot_color = ['gray']
        print("self.bezpts=",self.bezpts)
        self.num_eval = 100  # for Bezier curve

        self.plot_xmin = -500
        self.plot_xmax = 500
        self.plot_ymin = -500
        self.plot_ymax = 500

        self.xv = None  # xvalues of points along Bezier curve
        self.yv = None  # yvalues of points along Bezier curve

        self.ax0.set_aspect(1.0)
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)

        self.canvas.mpl_connect("button_press_event", self.button_press)
        # self.canvas.mpl_connect("button_release_event", self.on_release)
        # self.canvas.mpl_connect("motion_notify_event", self.on_move)

    def keyPressEvent(self, event):
        # if event.key() == Qt.Key_Space:
            # self.test_method()

        if event.key() == Qt.Key_N:
            # print("----- New cell type ...")
            self.cell_type_name = input("\nEnter cell type name:    (disregard this--> ")
            print("-- new cell type name is ", self.cell_type_name)
            # self.bplot_name.append(self.cell_type_name)
            # self.bplot_name[-1] = self.cell_type_name

            print()
            volume = input("Enter cell type volume:     (disregard this--> ")
            try:
                self.cell_volume = float(volume)
            except:
                print("ERROR converting to float. Setting to default volume.")
                self.cell_volume = 2494.0
            self.cell_radius = (self.cell_volume * 0.75 / np.pi) ** (1./3)
            print(f"-- its volume is {self.cell_volume} (--> r={self.cell_radius})")

            print()
            # self.color_by_celltype = ['gray','red','green','yellow','cyan','magenta','blue','brown','black','orange','seagreen','gold']
            print(f"color suggestions: {self.color_by_celltype}")
            self.cell_type_color = input("Enter color (no quotes):     (disregard this--> ")
            # self.bplot_color.append(self.cell_type_color)
            self.bplot_color[-1] = self.cell_type_color

            print("\n Got it! Now return to the plot to create more cells on curved boundaries.")

        elif event.key() == Qt.Key_U:
            # print("----- Undo is TBD...")
            print("# plots= ",len(self.bez_plot))
            # print(type(self.bez_plot))
            print(self.bez_plot)
            # self.bez_plot = self.bez_plot.pop()
            try:
                self.bez_plot.pop()
                self.bplot_name.pop()
                self.bplot_color.pop()
            except:
                return
            # self.bplot_color.pop()
            # self.bez_plot.del[-1]
            print("# plots= ",len(self.bez_plot))
            if len(self.bez_plot) == 0:
                self.cell_type_name = "default"
                self.bplot_color.append('gray')
            self.update_plots()

        elif event.key() == Qt.Key_S:   # save to .csv file
            fname = "curvy.csv"
            print(f"----- Writing to {fname}...")
            with open(fname, 'w') as f:
                f.write('x,y,z,type,volume,cycle entry,custom:GFP,custom:sample\n')
                for idx in range(len(self.bez_plot)):
                    xvals, yvals= self.bezier_curve2(self.bez_plot[idx],200)  # eval Bezier
                    for jdx in range(len(xvals)):
                        # f.write(f"{xvals[jdx]},{yvals[jdx]},0,{self.cell_type_name}\n")
                        f.write(f"{xvals[jdx]},{yvals[jdx]},0,{self.bplot_name[idx]}\n")
                        # print(f"{xvals[jdx]},{yvals[jdx]},0,{self.bplot_name[idx]}")

        elif event.key() == Qt.Key_C:
            self.bez_plot.clear()
            self.bplot_name.clear()
            self.bplot_color = ['gray']
            self.cell_type_name = "default"
            self.cell_volume = 2494.0
            self.cell_radius = (self.cell_volume * 0.75 / np.pi) ** (1./3)

            self.ax0.cla()
            self.ax0.set_aspect(1.0)
            self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
            self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
            self.ax0.set_title(self.instructions, fontsize=10)
            self.ax0.grid(True)
            self.canvas.update()
            self.canvas.draw()

    #---------------------------------------------------------------------------
    # def circles(self, x, y, s, c='b', ec='b',vmin=None, vmax=None, **kwargs):
    def circles(self, x, y, s, c='b', vmin=None, vmax=None, **kwargs):
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

        # ax = plt.gca()
        # ax.add_collection(collection)
        # ax.autoscale_view()
        self.ax0.add_collection(collection)
        self.ax0.autoscale_view()
        # plt.draw_if_interactive()
        if c is not None:
            # plt.sci(collection)
            self.ax0.sci(collection)
        # return collection

    #-----------------------------------------
    def update_plots(self):
        print("----------------  update_plots -----------------")
        self.ax0.cla()

        # print(f"------- update_plots(): type(xvals)={type(xvals)}")
        # print(f"        type(xvals)={type(xvals)}")
        # print(f"        xvals.shape={xvals.shape}")
        # print(f"        self.bezpts={self.bezpts}")

        print(f"        len(self.bez_plot={len(self.bez_plot)}")
        rval = 12.0
        for idx in range(len(self.bez_plot)):
            xvals = self.bez_plot[idx][:,0]
            yvals = self.bez_plot[idx][:,1]
            # print("xvals=", xvals)
            # print("yvals=", yvals)
            self.ax0.plot(xvals, yvals)   # plot 4-pt control polygon

            # xvals, yvals= self.bezier_curve(self.bez_plot[idx],100)  # eval Bezier
            # xvals, yvals= self.bezier_curve2(self.bez_plot[idx],20)  # eval Bezier
            xvals, yvals= self.bezier_curve2(self.bez_plot[idx],200)  # eval Bezier
            print("========   len(xvals) from bezier_curve2:  ",len(xvals))

            # self.circles(self.xv,self.yv, s=rval, c='r', edgecolor='red')
            # self.circles(xvals,yvals, s=rval, c='r', edgecolor='red')
            # self.circles(xvals,yvals, s=rval, c=self.cell_type_color)
            # print("\n>>>>>>>>>>>>  bplot_color=",self.bplot_color)
            try:
                # self.circles(xvals,yvals, s=rval, c=self.bplot_color[idx], edgecolor='k')  # why doesn't edgecolor work?!
                self.circles(xvals,yvals, s=rval, c=self.bplot_color[idx])
            except:
                print("\n>>>>>>>>>>>>  bplot_color=",self.bplot_color)
                print("ERROR plotting circles(). Maybe invalid color name? Try to 'undo' last plot and continue.")
                return

            # self.xv2, self.yv2= self.cell_spacing(self.xv,self.yv)  # eval Bezier

            # self.ax0.plot(xvals, yvals)   # plot 4-pt control polygon

        # self.ax0.set_xlabel('time (mins)')
        # self.ax0.set_ylabel('# of cells')
        # self.ax0.set_title("'c' to clear all.", fontsize=10)
        self.ax0.set_title(self.instructions, fontsize=10)

        self.ax0.set_aspect(1.0)
        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        # self.ax0.legend(loc='center right', prop={'size': 8})
        self.canvas.update()
        self.ax0.grid(True)
        self.canvas.draw()
        return

    #-----------------------------------------
    def eval_bernstein(self, i, n, t):
        # Bernstein polynomial of n, i as a function of t
        return comb(n, i) * ( t**(n-i) ) * (1 - t)**i


    def bezier_curve(self, points, num_tsteps=99):
        """
        Given a set of control points, return the
        Bezier curve defined by its control points.

        points should be a list of lists, or list of tuples
        such as [ [1,1], 
                    [2,3], 
                    [4,5], ..[Xn, Yn] ]
            num_tsteps is the number of time steps

            See http://processingjs.nihongoresources.com/bezierinfo/
        """

        nPoints = len(points)
        xPoints = np.array([p[0] for p in points])
        yPoints = np.array([p[1] for p in points])

        t = np.linspace(0.0, 1.0, num_tsteps)

        polynomial_array = np.array([ self.eval_bernstein(i, nPoints-1, t) for i in range(0, nPoints)   ])

        xvals = np.dot(xPoints, polynomial_array)
        yvals = np.dot(yPoints, polynomial_array)

        return xvals, yvals

    #--------------------------------------------------------
    def bezier_curve2(self, points, num_tsteps=99):
        """
        Given a set of control points, return the
        Bezier curve defined by its control points.

        points should be a list of lists, or list of tuples
        such as [ [1,1], 
                    [2,3], 
                    [4,5], ..[Xn, Yn] ]
            num_tsteps is the number of time steps

            Rf. http://processingjs.nihongoresources.com/bezierinfo/
        """

        nPoints = len(points)
        xPoints = np.array([p[0] for p in points])
        yPoints = np.array([p[1] for p in points])

        t = np.linspace(0.0, 1.0, num_tsteps)

        polynomial_array = np.array([ self.eval_bernstein(i, nPoints-1, t) for i in range(0, nPoints)   ])

        xvals = np.dot(xPoints, polynomial_array)
        yvals = np.dot(yPoints, polynomial_array)

        # print(f"bezier_curve2():   type(xvals)={type(xvals)}, len(xvals)={len(xvals)}")
        # print("xvals=",xvals)

        i0 = 0
        rx2 = 2.0 * self.cell_radius  # desired distance between cells
        dist2_min = rx2 * rx2  # square of distance 
        # print(f"\n\n >>>>>>  r={self.cell_radius},  rx2={rx2}, dist2_min={dist2_min}")
        xnew = np.array([])
        ynew = np.array([])
        # print("empty xnew=",xnew)
        xnew = np.append(xnew, xvals[0])
        ynew = np.append(ynew, yvals[0])
        # print("0) append: xnew=",xnew)

        # We step through ALL pts on the Bezier curve and only return those who are ~2*cell_radius apart
        for idx in range(1,len(xvals)-1):
            xdiff = xvals[idx] - xvals[i0]
            ydiff = yvals[idx] - yvals[i0]
            d2 = xdiff*xdiff + ydiff*ydiff  # square of distance
            if d2 > dist2_min:
                xnew = np.append(xnew, xvals[idx])
                ynew = np.append(ynew, yvals[idx])
                # print("after append: xnew=",xnew)
                i0 = idx

        return xnew, ynew

    #---------------------------------------------------------------------------
    def cell_spacing(self, xv,yv):  # eval Bezier
        return xv, yv

    #---------------------------------------------------------------------------
    def button_press(self, event):
        print("----------------  button_press -----------------")
        xval = event.xdata
        yval = event.ydata
        if xval is None:
            return
        # print("xval,yval=", xval,yval)
        self.bezpts[self.num_pts] = [xval,yval]
        # print("self.bezpts=",self.bezpts)

        # xvals = self.bezpts[self.num_pts][0]
        # yvals = self.bezpts[self.num_pts][1]
        xvals = self.bezpts[:,0]
        yvals = self.bezpts[:,1]
        # print("xvals=", xvals)
        # print("yvals=", yvals)

        self.num_pts += 1

        # if self.num_pts > 1:
        #     self.ax0.plot(xvals, yvals)

        rval = 8.0
        if self.num_pts == 4:
            rval = 12.0
            self.circles(xval,yval, s=rval, c='r', edgecolor='red')
            print("------- plot Bezier!")

            self.bez_plot.append(self.bezpts.copy())
            # print(f"        type(self.bez_plot)={type(self.bez_plot)}")
            # print(f"        len(self.bez_plot)={len(self.bez_plot)}")
            # print(f"        self.bez_plot={self.bez_plot}")

            self.bplot_name.append(self.cell_type_name)
            # print("-------- self.bplot_name=",self.bplot_name)

            # print("xv=",xv)
            # print("yv=",yv)
            # print("len(xv)=",len(self.xv))
            # self.csv_array = np.empty([1,4])  # should probably *just* np.delete, but meh
            # self.csv_array = np.delete(self.csv_array,0,0)
            # for idx in range(len(xv)):
            #     print("idx=",idx)
            self.num_pts = 0

            # self.population_plot[self.discrete_scalar].ax0.plot(xv, yv, label=ctname, linewidth=lw, color=ctcolor)
            # self.ax0.plot(xv, yv, 'o')

            # self.circles(self.xv,self.yv, s=rval, c='r', edgecolor='red')
            # self.xv2, self.yv2= self.cell_spacing(self.xv,self.yv)  # eval Bezier

            # self.ax0.plot(xvals, yvals)   # plot 4-pt control polygon
            # # self.ax0.set_xlabel('time (mins)')
            # # self.ax0.set_ylabel('# of cells')
            # self.ax0.set_title("Press 'c' to clear all.", fontsize=10)
            # # self.ax0.legend(loc='center right', prop={'size': 8})
            # self.canvas.update()
            # self.canvas.draw()
            # # self.population_plot[self.discrete_scalar].ax0.legend(loc='center right', prop={'size': 8})
            # # self.show()

            # self.update_plots(xvals,yvals)
            self.update_plots()

            self.bplot_color.append(self.cell_type_color)
            # self.bplot_name.append(self.cell_type_name)
            return

        # self.circles(xvals,yvals, s=rvals, color=self.color_by_celltype[cell_type_index], alpha=self.alpha_value)
        self.circles(xval,yval, s=rval, c='k')

        self.ax0.set_aspect(1.0)

        self.ax0.set_xlim(self.plot_xmin, self.plot_xmax)
        self.ax0.set_ylim(self.plot_ymin, self.plot_ymax)
        self.ax0.grid(True)

        self.canvas.update()
        self.canvas.draw()

        # print("event.inaxes", event.inaxes)
        # print("x", event.x)
        # print("y", event.y)

    # def on_release(self, event):
    #     print("release:")
    #     print("event.xdata", event.xdata)
    #     print("event.ydata", event.ydata)
    #     print("event.inaxes", event.inaxes)
    #     print("x", event.x)
    #     print("y", event.y)

    # def on_move(self, event):
    #     print("move")
    #     print("event.xdata", event.xdata)
    #     print("event.ydata", event.ydata)
    #     print("event.inaxes", event.inaxes)
    #     print("x", event.x)
    #     print("y", event.y)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = MplWidget()
    w.show()
    sys.exit(app.exec_())
