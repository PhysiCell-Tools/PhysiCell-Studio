import sys
from numpy import genfromtxt
import matplotlib.pyplot as plt

csv_file = sys.argv[1]

# cell = genfromtxt('cells_5um.csv', delimiter=',')
# cell = genfromtxt('glom_cells.csv', delimiter=',')
# cell = genfromtxt('ftu_cells.csv', delimiter=',')
cell = genfromtxt(csv_file, delimiter=',')
print(cell.shape)
#p = p1[0:9,:]
n = len(cell[:,0])
print("# cells = ",n)
#plt.plot(cell[:,0],p1[:,1],'r.')
xmin=80
xmax=290
ymin=-200
ymax=0
# for idx in range(n):
#     if cell[idx,0]>xmin and cell[idx,0]<xmax and cell[idx,1]>ymin and cell[idx,1]<ymax and cell[idx,3]==5 and cell[idx,4]==7:
#         plt.plot(cell[idx,0],cell[idx,1],'r.')
#         if cell[idx,0]>150 and cell[idx,0]<160 and cell[idx,1]>-100 and cell[idx,1]<-75:
#             print(idx,cell[idx,:])
plt.plot(cell[:,0],cell[:,1],'.')
plt.show()
