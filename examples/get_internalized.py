#
# M1P~/git/tumor3D_ML/output$ python plot_substrate3D_slice.py 16 4
#
# Dependencies include matplotlib and numpy. We recommend installing the Anaconda Python3 distribution.
#
# Author: Randy Heiland (except for the circles() function)
#
#
__author__ = "Randy Heiland"

import sys,pathlib
import xml.etree.ElementTree as ET
import math
# import scipy.io
from pyMCDS import pyMCDS
import matplotlib
import numpy as np
from numpy.random import randn
import matplotlib.pyplot as plt

# print(len(sys.argv))
if (len(sys.argv) < 2):
  frame_idx = 0
else:
  kdx = 1
  frame_idx = int(sys.argv[kdx])

# print('frame, field = ',frame_idx, field_index)

xml_file = "output%08d.xml" % frame_idx
# print("plot_cells3D: xml_file = ",xml_file)
# mcds = pyMCDS_cells(xml_file, '.')  

# if not os.path.exists("tmpdir/" + xml_file):
# if not os.path.exists("output/" + xml_file):
    # return

# print("\n\n------------- plot_cells3D: pyMCDS reading info from ",xml_file)
# mcds = pyMCDS(xml_file, 'output')   # will read in BOTH cells and substrates info
mcds = pyMCDS(xml_file, '.')   # will read in BOTH cells and substrates info
current_time = mcds.get_time()
# print('time=', current_time )

# for template model:
# print("mcds.data['discrete_cells'].keys()= ",mcds.data['discrete_cells'].keys())
# mcds.data['discrete_cells'].keys()=  dict_keys(['ID', 'position_x', 'position_y', 'position_z', 'total_volume', 'cell_type', 'cycle_model', 'current_phase', 'elapsed_time_in_phase', 'nuclear_volume', 'cytoplasmic_volume', 'fluid_fraction', 'calcified_fraction', 'orientation_x', 'orientation_y', 'orientation_z', 'polarity', 'velocity_x', 'velocity_y', 'velocity_z', 'pressure', 'number_of_nuclei', 'damage', 'total_attack_time', 'contact_with_basement_membrane', 'current_cycle_phase_exit_rate', 'dead', 'current_death_model', 'death_rates_0', 'death_rates_1', 'cytoplasmic_biomass_change_rate', 'nuclear_biomass_change_rate', 'fluid_change_rate', 'calcification_rate', 'target_solid_cytoplasmic', 'target_solid_nuclear', 'target_fluid_fraction', 'radius', 'nuclear_radius', 'surface_area', 'cell_cell_adhesion_strength', 'cell_BM_adhesion_strength', 'cell_cell_repulsion_strength', 'cell_BM_repulsion_strength', 'cell_adhesion_affinities', 'relative_maximum_adhesion_distance', 'maximum_number_of_attachments', 'attachment_elastic_constant', 'attachment_rate', 'detachment_rate', 'is_motile', 'persistence_time', 'migration_speed', 'migration_bias_direction_x', 'migration_bias_direction_y', 'migration_bias_direction_z', 'migration_bias', 'motility_vector_x', 'motility_vector_y', 'motility_vector_z', 'chemotaxis_index', 'chemotaxis_direction', 'chemotactic_sensitivities', 'secretion_rates', 'uptake_rates', 'saturation_densities', 'net_export_rates', 'internalized_total_substrates', 'fraction_released_at_death', 'fraction_transferred_when_ingested', 'apoptotic_phagocytosis_rate', 'necrotic_phagocytosis_rate', 'other_dead_phagocytosis_rate', 'live_phagocytosis_rates', 'attack_rates', 'damage_rate', 'fusion_rates', 'transformation_rates', 'sample'])

ncells = len(mcds.data['discrete_cells']['ID'])
# print('ncells=', ncells)

# xyz = np.zeros((ncells, 3))
# xyz[:, 0] = mcds.data['discrete_cells']['position_x']
# xyz[:, 1] = mcds.data['discrete_cells']['position_y']
# xyz[:, 2] = mcds.data['discrete_cells']['position_z']

intern_sub = mcds.data['discrete_cells']['internalized_total_substrates']
print("time= ",current_time,"  intern_sub= ",intern_sub)
