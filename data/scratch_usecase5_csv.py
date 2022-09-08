import sys
from numpy import genfromtxt
import math
import matplotlib.pyplot as plt

csv_file = sys.argv[1]
scratch_delta = float(sys.argv[2])

# cell = genfromtxt('cells_5um.csv', delimiter=',')
# cell = genfromtxt('glom_cells.csv', delimiter=',')
# cell = genfromtxt('ftu_cells.csv', delimiter=',')
cell = genfromtxt(csv_file, delimiter=',')
print(cell.shape)
#p = p1[0:9,:]
n = len(cell[:,0])
print("# cells = ",n)
# scratch_delta = 25
for idx in range(n):
    if math.fabs(cell[idx,0]) > scratch_delta:
        print(cell[idx,0], cell[idx,1], cell[idx,2], cell[idx,3])
        plt.plot(cell[idx,0],cell[idx,1],'.')
plt.show()
