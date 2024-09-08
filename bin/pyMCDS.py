#########
# title: pyMCDS.py
#
# language: python3
# date: 2022-08-22
# license: BSD-3-Clause
# authors: Patrick Wall, Randy Heiland, Paul Macklin, Elmar Bucher
#
# description:
#     pyMCDS.py definds an object class, able to load and access
#     within python a single time step from the PhysiCell model output folder.
#     pyMCDS.py was forked from the original PhysiCell-Tools python-loader
#     implementation and further developed.
#########


# load library
import numpy as np
import pandas as pd
import pathlib
from scipy import io
import sys
import xml.etree.ElementTree as ET

# functions
def graphfile_parser(s_pathfile):
    """
    input:
        s_pathfile: string
            path to and file name from graph.txt file.

    output:
        dei_graph: dictionary of sets of integers.
            object maps each cell ID to connected cell IDs.

    description:
        code parses PhysiCell's own graphs format and
        returns the content in a dictionary object.
    """
    # processing
    dei_graph = {}
    f = open(s_pathfile)
    for i, s_line in enumerate(f):
        #print('processing line:', s_line.strip())
        s_key, s_value = s_line.strip().split(':')
        ei_value = set()
        if len(s_value.strip()) :
            ei_value = set([int(s_id) for s_id in s_value.split(',')])
        dei_graph.update({int(s_key): ei_value})
    f.close()

    # output
    return(dei_graph)


# object classes
class pyMCDS:
    """
    input:
        xmlfile: string
            name of the xml file with or without path.
            in the with path case, output_path has to be set to the default!

        output_path: string; default '.'
            relative or absolute path to the directory where
            the PhysiCell output files are stored.

        microenv: booler; default True
            should the microenvironment be extracted?
            setting microenv to False will use less memory and speed up
            processing, similar to the original pyMCDS_cells.py script.

        graph: boole; default True
            should the graphs be extracted?
            setting graph to False will use less memory and speed up processing.

        verbose: boole; default True
            setting verbose to False for less text output, while processing.

    output:
        mcds: pyMCDS class instance
            all fetched content is stored at mcds.data.

    description:
        pyMCDS.__init__ will generate a class instance with a
        dictionary of dictionaries data structure that contains all
        output from a single PhysiCell model time step. furthermore,
        this class, and as such it's instances, offers functions
        to access the stored data.
        the code assumes that all related output files are stored in
        the same directory. data is loaded by reading the xml file
        for a particular time step and the therein referenced files.
    """
    def __init__(self, xmlfile, output_path='.', microenv=True, graph=True, verbose=True):
        self.microenv = microenv
        self.graph = graph
        self.verbose = verbose
        self.data = self._read_xml(xmlfile, output_path)


    ## METADATA RELATED FUNCTIONS ##

    def get_multicellds_version(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            s_version : sting
            MultiCellDS xml version which stored the data.

        description:
            function returns as a string the MultiCellDS xml version
            that was used to store this data.
        """
        return self.data['metadata']['multicellds_version']

    def get_physicell_version(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            s_version : sting
            PhysiCell version which generated the data.

        description:
            function returns as a string the PhysiCell version
            that was used to generate this data.
        """
        return self.data['metadata']['physicell_version']


    def get_timestamp(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            s_timestap : sting
            timestamp from when this data was generated.

        description:
            function returns as a string the timestamp from when
            this data was generated.
        """
        return self.data['metadata']['created']


    def get_time(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            r_time : floating point number
            simulation time in [min].

        description:
            function returns as a real number
            the simulation time in minutes.
        """
        return self.data['metadata']['current_time']


    def get_runtime(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            r_time : floating point number
            wall time in [sec].

        description:
            function returns as a real number, the wall time in seconds
            the simulation took to run up to this time step.
        """
        return self.data['metadata']['current_runtime']


    ## MESH RELATED FUNCTIONS  ##

    def get_voxel_ijk_range(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            lti_i : list of tuple of 2 integer numbers
            i-axis, j-aixs, and k-axis voxel range.

        decritpion:
            function returns in a list of tuples the lowest and highest
            i-axis, j-axis, and k-axis voxel value.
        """
        return self.data['mesh']['ijk_range']


    def get_mesh_mnp_range(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            ltr_mnp : list of tuple of 2 floating point numbers
            m-axis, n-axis, and p-axis  mesh center range.

        decritpion:
            function returns in a list of tuples the lowest and highest
            m-axis, n-axis, and p-axis mesh center value.
        """
        return self.data['mesh']['mnp_range']


    def get_xyz_range(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            ltr_xyz : list of tuple of 2 floating point numbers
            x-axis, y-axis, and z-axis position range.

        decritpion:
            function returns in a list of tuples the lowest and highest
            x-axis, y-axis, and z-axis position value.
        """
        return self.data['mesh']['xyz_range']


    def get_voxel_ijk_axis(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            lai_ijk : list of 3 numpy arrays of integer numbers
            i-axis, j-axis, and k-axis voxel coordinates axis.

        description:
            function returns a list of voxel coordinate vectors,
            one for the i-axis, j-axis, and k-axis.
        """
        return self.data['mesh']['ijk_axis']


    def get_mesh_mnp_axis(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            lar_mnp : list of 3 numpy arrays of floating point numbers
            m-axis, n-axis, and p-axis mesh center axis coordinates.

        description:
            function returns a list of mesh center vectors,
            one for the m-axis, n-axis, and p-axis.
        """
        return self.data['mesh']['mnp_axis']


    def get_mesh(self, flat=False):
        """
        input:
            self: pyMCDS class instance.

            flat : bool; default False
                if flat is True, only the m-axis mesh center
                and n-axis mesh center meshgrids will be returned.
                else the m, n, and p mesh center meshgrids will be returned.

        output:
            aar_meshgrid : 4-way (3D) or 3-way (2D) numpy arrays tensor of floating point numbers
                meshgrid shaped object, with the mesh center
                coordinate values from the m, n, p-axis or m, n-axis.

        description:
            function returns a numpy array of meshgrids each stores the
            mesh center coordinate values from one particular axis.
            the function can either return meshgrids for the full
            m, n, p 3D cube, or only the 2D planes along the p-axis.
        """
        if flat:
            ar_m = self.data['mesh']['mnp_grid'][0][:, :, 0]
            ar_n = self.data['mesh']['mnp_grid'][1][:, :, 0]
            return np.array([ar_m, ar_n])

        else:
            return self.data['mesh']['mnp_grid']


    def get_mesh_2D(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            aar_meshgrid : 3-way numpy arrays tensor of floating point numbers
                meshgrid shaped objects, with the mesh center
                coordinate values from the m and n-axis.

        description:
            function is identical to the self.get_mesh(self, flat=True)
            function call.
        """
        return self.get_mesh(flat=True)


    def get_mesh_coordinate(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            aar_meshaxis : numpy array of 3 one dimensional numpy floating point number arrays
                n, m, and p-axis mesh center coordinate vectors.

        description:
            function returns three vectors with mesh center coordinate values,
            one for each axis.
        """
        return self.data['mesh']['mnp_coordinate']


    def get_voxel_volume(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            r_volume: floating point number
            voxel volume value related to the spacial unit
            defined in the PhysiCell_settings.xml file.

        description:
            function returns the volume value for a single voxel, related
            to the spacial unit defined in the PhysiCell_settings.xml file.
        """
        ar_volume = np.unique(self.data['mesh']['volumes'])
        if ar_volume.shape != (1,):
            sys.exit(f'Error @ pyMCDS.get_voxel_volume : mesh is not built out of a unique voxel volume {ar_volume}.')
        r_volume = ar_volume[0]
        return(r_volume)


    def get_mesh_spacing(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            lr_mnp_spacing: list of 3 floating point numbers
                mesh spacing in m, n, and p direction.

        description:
            function returns the distance in between mesh centers,
            in the spacial unit defined in the PhysiCell_settings.xml file.
        """
        tr_m_range, tr_n_range, tr_p_range = self.get_mesh_mnp_range()
        ar_m_axis, ar_n_axis, ar_p_axis = self.get_mesh_mnp_axis()

        dm = (tr_m_range[1] - tr_m_range[0]) / (ar_m_axis.shape[0] - 1)
        dn = (tr_n_range[1] - tr_n_range[0]) / (ar_n_axis.shape[0] - 1)
        if (len(set(tr_p_range)) == 1):
            dp = 1
        else:
            dp = (tr_p_range[1] - tr_p_range[0]) / (ar_p_axis.shape[0] - 1)
        return [dm, dn, dp]


    def get_voxel_spacing(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            lr_ijk_spacing: list of 3 floating point numbers
                voxel spacing in i, j, and k direction.

        description:
            function returns the voxel width, height, depth measurement,
            in the spacial unit defined in the PhysiCell_settings.xml file.
        """
        r_volume = self.get_voxel_volume()
        dm, dn, _ = self.get_mesh_spacing()
        dp  = r_volume / (dm * dn)
        return [dm, dn, dp]


    def is_in_mesh(self, x, y, z, halt=False):
        """
        input:
            self: pyMCDS class instance.

            x: floating point number
                position x-coordinate.

            y: floating point number
                position y-coordinate.

            z: floating point number
                position z-coordinate.

            halt: boolean; default is False
                should program execution break or just spit out a warning,
                if position is not in mesh?

        output:
            b_isinmesh: boolean
            states if the given coordinate is inside the mesh.

        description:
            function evaluates, if the given position coordinate
            is inside the boundaries. if the coordinate is outside the
            mesh, a warning will be printed. if additionally
            halt is set to True, program execution will break.
        """
        b_isinmesh = True

        # check against boundary box
        tr_x, tr_y, tr_z = self.get_xyz_range()

        if (x < tr_x[0]) or (x > tr_x[1]):
            print(f'Warning @ pyMCDS.is_in_mesh : x = {x} out of bounds: x-range is {tr_x}.')
            b_isinmesh = False
        elif (y < tr_y[0]) or (y > tr_y[1]):
            print(f'Warning @ pyMCDS.is_in_mesh : y = {y} out of bounds: y-range is {tr_y}.')
            b_isinmesh = False
        elif (z < tr_z[0]) or (z > tr_z[1]):
            print(f'Warning @ pyMCDS.is_in_mesh : z = {z} out of bounds: z-range is {tr_z}.')
            b_isinmesh = False

        # output
        if halt and not b_isinmesh:
            sys.exit('Processing stopped!')
        return(b_isinmesh)


    def get_voxel_ijk(self, x, y, z, is_in_mesh=True):
        """
        input:
            self: pyMCDS class instance.

            x: floating point number
                position x-coordinate.

            y: floating point number
                position y-coordinate.

            z: floating point number
                position z-coordinate.

            is_in_mesh: boolean; default is True
                should function check, if the given coordinate is in the mesh,
                and only calculate ijk values if is so?

        output:
            li_ijk : list of 3 integers
                i, j, k indices for the voxel
                containing the x, y, z position.

        description:
            function returns the meshgrid indices i, j, k
            for the given position x, y, z.
        """
        lr_ijk = None
        b_calc = True

        if is_in_mesh:
            b_calc = self.is_in_mesh(x=x, y=y, z=z, halt=False)

        if b_calc:
            tr_m, tr_n, tr_p = self.get_mesh_mnp_range()
            dm, dn, dp = self.get_voxel_spacing()

            i = int(np.round((x - tr_m[0]) / dm))
            j = int(np.round((y - tr_n[0]) / dn))
            k = int(np.round((z - tr_p[0]) / dp))

            lr_ijk = [i, j, k]

        return lr_ijk


    ## MICROENVIRONMENT RELATED FUNCTIONS ##

    def get_substrate_names(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            ls_substrat: list of stings
            alphabetically ordered list of all tracked substrates.

        description:
            function returns all chemical species names,
            modeled in the microenvironment.
        """
        ls_substrat = sorted(self.data['continuum_variables'].keys())
        return ls_substrat


    def get_substrate_df(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            df_substare: pandas dataframe
            one substrate per row and decay_rate and difusion_coefficient
            factors as columns.

        description:
            function returns a dataframe with each substrate's
            decay_rate and difusion_coefficient.
        """
        # extract data
        ls_column = ['substrate','decay_rate','diffusion_coefficient']
        ll_sub = []
        for s_substrate in self.get_substrate_names():
            s_decay_value = self.data['continuum_variables'][s_substrate]['decay_rate']['value']
            s_diffusion_value = self.data['continuum_variables'][s_substrate]['diffusion_coefficient']['value']
            ll_sub.append([s_substrate, s_decay_value, s_diffusion_value])

        # generate dataframe
        df_substrate = pd.DataFrame(ll_sub, columns=ls_column)
        df_substrate.set_index('substrate', inplace=True)
        df_substrate.columns.name = 'parameter'

        # output
        return(df_substrate)


    def get_concentration(self, substrate, z_slice=None, halt=False):
        """
        input:
            self: pyMCDS class instance.

            substrate: string
                substrate name.

            z_slice: floating point number; default is None
                z-axis position to slice a 2D xy-plain out of the
                3D substrate concentration mesh. if None the
                whole 3D mesh will be returned.

            halt: boolean; default is False
                should program execution break or just spit out a warning,
                if z_slize position is not an exact mesh center coordinate?
                if False, z_slice will be adjusted to the nearest
                mesh center value, the smaller one, if the coordinate
                lies on a saddle point.

        output:
            ar_conc: numpy array of floating point numbers
                substrate concentration meshgrid or xy-plain slice
                through the meshgrid.

        description:
            function returns the concentration meshgrid, or a xy-plain slice
            out of the whole meshgrid, for the specified chemical species.
        """
        ar_conc = self.data['continuum_variables'][substrate]['data']

        # check if z_slice is a mesh center or None
        if not (z_slice is None):
            _, _, ar_p_axis = self.get_mesh_mnp_axis()
            if not (z_slice in ar_p_axis):
                print(f'Warning @ pyMCDS.get_concentration : specified z_slice {z_slice} is not an element of the z-axis mesh centers set {ar_p_axis}.')
                if halt:
                    sys.exit('Processing stopped!')
                else:
                    z_slice = ar_p_axis[(ar_p_axis - z_slice).argmin()]
                    print(f'z_slice set to {z_slice}.')

            # filter by z_slice
            _, _, ar_p_grid = self.get_mesh()
            mask = ar_p_grid == z_slice
            ar_conc = ar_conc[mask].reshape((ar_p_grid.shape[0], ar_p_grid.shape[1]))

        # output
        return ar_conc


    def get_concentration_at(self, x, y, z=0):
        """
        input:
            self: pyMCDS class instance.

            x: floating point number
                position x-coordinate.

            y: floating point number
                position y-coordinate.

            z: floating point number; default is 0
                position z-coordinate.

        output:
            ar_concs: numpy array of floating point numbers
            array of substrate concentrations in the order
            given by get_substrate_names().

        description:
            function return concentrations of each chemical species
            inside a particular voxel that contains the point specified
            in the arguments.
        """
        ar_concs = None

        # is coordinate inside the domain?
        b_calc = self.is_in_mesh(x=x, y=y, z=z, halt=False)
        if b_calc:

            # get voxel coordinate and substrate names
            i, j, k = self.get_voxel_ijk(x, y, z, is_in_mesh=False)
            ls_substrate = self.get_substrate_names()
            ar_concs = np.zeros(len(ls_substrate))

            # get substrate concentrations
            for n, s_substrate in enumerate(ls_substrate):
                ar_concs[n] = self.get_concentration(s_substrate)[j, i, k]
                if self.verbose:
                    print(f'pyMCD.get_concentration_at(x={x},y={y},z={z}) > jkl: [{i},{j},{k}] > substrate: {s_substrate} {ar_concs[n]}')

        # output
        return ar_concs


    def get_concentration_df(self, z_slice=None, halt=False):
        """
        input:
            self: pyMCDS class instance.

            z_slice: floating point number; default is None
                z-axis position to slice a 2D xy-plain out of the
                3D substrate concentration mesh. if None the
                whole 3D mesh will be returned.

            halt: boolean; default is False
                should program execution break or just spit out a warning,
                if z_slize position is not an exact mesh center coordinate?
                if False, z_slice will be adjusted to the nearest
                mesh center value, the smaller one, if the coordinate
                lies on a saddle point.

        output:
            df_conc : pandas dataframe
                dataframe with all substrate concentrations in each voxel.

        description:
            function returns a dataframe with concentration values
            for all chemical species in all voxels. additionally, this
            dataframe lists voxel and mesh center coordinates.
        """
        # check if z_slice is a mesh center or None
        if not (z_slice is None):
            _, _, ar_p_axis = self.get_mesh_mnp_axis()
            if not (z_slice in ar_p_axis):
                print(f'Warning @ pyMCDS.get_concentration_df : specified z_slice {z_slice} is not an element of the z-axis mesh centers set {ar_p_axis}.')
                if halt:
                    sys.exit('Processing stopped!')
                else:
                    z_slice = ar_p_axis[(ar_p_axis - z_slice).argmin()]
                    print(f'z_slice set to {z_slice}.')

        # flatten mesh coordnates
        ar_m, ar_n, ar_p = self.get_mesh()
        ar_m = ar_m.flatten(order='C')
        ar_n = ar_n.flatten(order='C')
        ar_p = ar_p.flatten(order='C')

        # get mesh spacing
        dm, dn, dp = self.get_voxel_spacing()

        # get voxel coordinates
        ai_i = ((ar_m - ar_m.min()) / dm)
        ai_j = ((ar_n - ar_n.min()) / dn)
        ai_k = ((ar_p - ar_p.min()) / dp)

        # handle coordinates
        ls_column = [
            'voxel_i','voxel_j','voxel_k',
            'mesh_center_m','mesh_center_n','mesh_center_p'
        ]
        la_data = [ai_i, ai_j, ai_k, ar_m, ar_n, ar_p]

        # handle concentrations
        for s_substrate in self.get_substrate_names():
            ls_column.append(s_substrate)
            ar_conc = self.get_concentration(substrate=s_substrate, z_slice=None)
            la_data.append(ar_conc.flatten(order='C'))

        # generate dataframe
        aa_data  = np.array(la_data)
        df_conc = pd.DataFrame(aa_data.T, columns=ls_column)
        d_dtype = {'voxel_i': int, 'voxel_j': int, 'voxel_k': int}
        df_conc = df_conc.astype(d_dtype)

        # filter
        if not (z_slice is None):
           df_conc = df_conc.loc[df_conc.mesh_center_p == z_slice, :]

        # output
        return df_conc


    ## CELL RELATED FUNCTIONS ##

    def get_cell_variables(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            ls_variables: list of strings
            alphabetically ordered list of all tracked cell variable names.


        description:
            function returns all modeled cell variable names.
        """
        ls_variables = sorted(self.data['discrete_cells']['data'].keys())
        return ls_variables


    def get_cell_df(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            df_cell: pandas dataframe
            dataframe lists, one cell per row, all tracked variables
            values related to this cell. the variables are cell_position,
            mesh_center, and voxel coordinates, all cell_variables,
            all substrate rates and concentrations, and additional
            the surrounding cell density.

        description:
            function returns a dataframe with a cell centric view
            of the simulation.
        """

        # get cell position and more
        df_cell = pd.DataFrame(self.data['discrete_cells']['data'])
        df_voxel = df_cell.loc[:,['position_x','position_y','position_z']].copy()

        # get mesh spacing
        dm, dn, dp = self.get_voxel_spacing()

        # get mesh and voxel min max values
        tr_m_range, tr_n_range, tr_p_range = self.get_mesh_mnp_range()
        tr_i_range, tr_j_range, tr_k_range = self.get_voxel_ijk_range()

        # get voxel for each cell
        df_voxel.loc[:,'voxel_i'] = np.round((df_voxel.loc[:,'position_x'] - tr_m_range[0]) / dm).astype(int)
        df_voxel.loc[:,'voxel_j'] = np.round((df_voxel.loc[:,'position_y'] - tr_n_range[0]) / dn).astype(int)
        df_voxel.loc[:,'voxel_k'] = np.round((df_voxel.loc[:,'position_z'] - tr_p_range[0]) / dp).astype(int)
        df_voxel.loc[(df_voxel.voxel_i > tr_i_range[1]), 'voxel_i'] = tr_i_range[1]  # i_max
        df_voxel.loc[(df_voxel.voxel_i < tr_i_range[0]), 'voxel_i'] = tr_i_range[0]  # i_min
        df_voxel.loc[(df_voxel.voxel_j > tr_j_range[1]), 'voxel_j'] = tr_j_range[1]  # j_max
        df_voxel.loc[(df_voxel.voxel_j < tr_j_range[0]), 'voxel_j'] = tr_j_range[0]  # j_min
        df_voxel.loc[(df_voxel.voxel_k > tr_k_range[1]), 'voxel_k'] = tr_k_range[1]  # k_max
        df_voxel.loc[(df_voxel.voxel_k < tr_k_range[0]), 'voxel_k'] = tr_k_range[0]  # k_min

        # merge voxel (inner join)
        df_cell = pd.merge(df_cell, df_voxel, on=['position_x', 'position_y', 'position_z'])

        # merge cell_density (left join)
        df_cellcount = df_cell.loc[:,['voxel_i','voxel_j','voxel_k','ID']].groupby(['voxel_i','voxel_j','voxel_k']).count().reset_index()
        ls_column = list(df_cellcount.columns)
        ls_column[-1] = 'cell_count_voxel'
        df_cellcount.columns = ls_column
        s_density = f"cell_density_{self.data['metadata']['spatial_units']}3"
        df_cellcount[s_density] = df_cellcount.loc[:,'cell_count_voxel'] / self.get_voxel_volume()
        df_cell = pd.merge(
            df_cell,
            df_cellcount,
            on = ['voxel_i', 'voxel_j', 'voxel_k'],
            how = 'left',
        )

        # microenvironment
        if self.microenv:
            # merge substrate (left join)
            df_sub = self.get_substrate_df()
            for s_sub in df_sub.index:
                 for s_rate in df_sub.columns:
                     s_var = f'{s_sub}_{s_rate}'
                     df_cell[s_var] = df_sub.loc[s_sub,s_rate]

            # merge concentration (left join)
            df_conc = self.get_concentration_df(z_slice=None)
            df_cell = pd.merge(
                df_cell,
                df_conc,
                on = ['voxel_i', 'voxel_j', 'voxel_k'],
                how = 'left',
            )

        # output
        df_cell = df_cell.loc[:, sorted(df_cell.columns)]
        df_cell.set_index('ID', inplace=True)
        return df_cell


    def get_cell_df_at(self, x, y, z=0):
        """
        input:
            self: pyMCDS class instance.

            x: floating point number
                position x-coordinate.

            y: floating point number
                position y-coordinate.

            z: floating point number; default is 0
                position z-coordinate.

        output:
            df_voxel: pandas dataframe
            x, y, z voxel filtered cell dataframe.

        description:
            function returns the cell dataframe for the voxel
            specified with the x, y, z position coordinate.
        """
        df_voxel = None

        # is coordinate inside the domain?
        b_calc = self.is_in_mesh(x=x, y=y, z=z, halt=False)
        if b_calc:

            # get mesh and mesh spacing
            dm, dn, dp = self.get_voxel_spacing()
            ar_m, ar_n, ar_p = self.get_mesh()

            # get voxel coordinate
            i, j, k = self.get_voxel_ijk(x, y, z, is_in_mesh=False)
            m = ar_m[j, i, k]
            n = ar_n[j, i, k]
            p = ar_p[j, i, k]

            # get voxel
            df_cell = self.get_cell_df()
            inside_voxel = (
                (df_cell['position_x'] <= m + dm / 2) &
                (df_cell['position_x'] >= m - dm / 2) &
                (df_cell['position_y'] <= n + dn / 2) &
                (df_cell['position_y'] >= n - dn / 2) &
                (df_cell['position_z'] <= p + dp / 2) &
                (df_cell['position_z'] >= p - dp / 2)
            )
            df_voxel = df_cell[inside_voxel]

        # output
        return df_voxel


    ## GRAPH RELATED FUNCTIONS ##

    def get_attached_graph_dict(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            dei_graph: dictionary of sets of integers
            maps each cell ID to the attached connected cell IDs.

        description:
            function returns the attached cell graph as a dictionary object.
        """
        return self.data['discrete_cells']['graph']['attached_cells']


    def get_neighbor_graph_dict(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            dei_graph: dictionary of sets of integers
            maps each cell ID to the connected neighbor cell IDs.

        description:
            function returns the cell neighbor graph as a dictionary object.
        """
        return self.data['discrete_cells']['graph']['neighbor_cells']


    ## UNIT OVERVIEW RELATED FUNCTION ##

    def get_unit_df(self):
        """
        input:
            self: pyMCDS class instance.

        output:
            df_unit: pandas dataframe
            dataframe lists all tracked variables from metadata,
            cell, and microenvironment and maps them to their unit.

        description:
            function returns a dataframe that lists all tracked variables
            and their units.
        """
        # extract data
        ds_unit = {}
        # units for metadata parameters
        ds_unit.update({'time': [self.data['metadata']['time_units']]})
        ds_unit.update({'runtime': [self.data['metadata']['runtime_units']]})
        ds_unit.update({'spatial_unit': [self.data['metadata']['spatial_units']]})

        # microenvironment
        if self.microenv:
            for s_substrate in self.get_substrate_names():
                # unit from substrate parameters
                s_unit = self.data['continuum_variables'][s_substrate]['units']
                ds_unit.update({s_substrate: [s_unit]})

                # units from microenvironment parameters
                s_diffusion_key = f'{s_substrate}_diffusion_coefficient'
                s_diffusion_unit = self.data['continuum_variables'][s_substrate]['diffusion_coefficient']['units']
                ds_unit.update({s_diffusion_key: [s_diffusion_unit]})

                s_decay_key = f'{s_substrate}_decay_rate'
                s_decay_unit = self.data['continuum_variables'][s_substrate]['decay_rate']['units']
                ds_unit.update({s_decay_key: [s_decay_unit]})

        # units from cell parameters
        ds_unit.update(self.data['discrete_cells']['units'])

        # output
        del ds_unit['ID']
        df_unit= pd.DataFrame(ds_unit, index=['unit']).T
        df_unit.index.name = 'parameter'
        df_unit.sort_index(inplace=True)
        return(df_unit)


    ## LOAD DATA  ##

    def _read_xml(self, xmlfile, output_path='.'):
        """
        input:
            self: pyMCDS class instance.

            xmlfile: string
                name of the xml file with or without path
                in the with path case, output_path has to be set to the default!

            output_path: string; default '.'
                relative or absolute path to the directory where
                the PhysiCell output files are stored.

        output:
            self: pyMCDS class instance with loaded data.

        description:
            internal function to load the data from the PhysiCell output files
            into the pyMCDS instance.
        """
        xmlpathfile, output_path = xmlfile_to_xmlpathfile(xmlfile, output_path)

        # read xml path/file
        # 20221027 juliano: d = xmltodict.parse(open('PhysiCell_settings.xml').read(), process_namespaces=True)
        tree = ET.parse(xmlpathfile)
        if self.verbose:
            print(f'reading: {xmlpathfile}')

        root = tree.getroot()
        MCDS = {}


        ###################
        # handle metadata #
        ###################

        if self.verbose:
            print('working on metadata ...')

        ### find the metadata node ###
        metadata_node = root.find('metadata')
        MCDS['metadata'] = {}

        # get multicellds xml version
        MCDS['metadata']['multicellds_version'] = f"MultiCellDS_{root.get('version')}"

        # get physicell software version
        software_node = metadata_node.find('software')
        physicelln_node = software_node.find('name')
        physicellv_node = software_node.find('version')
        MCDS['metadata']['physicell_version'] = f'{physicelln_node.text}_{physicellv_node.text}'

        # get timestamp
        time_node = metadata_node.find('created')
        MCDS['metadata']['created'] = time_node.text

        # get current simulated time
        time_node = metadata_node.find('current_time')
        MCDS['metadata']['current_time'] = float(time_node.text)
        MCDS['metadata']['time_units'] = time_node.get('units')

        # get current runtime
        time_node = metadata_node.find('current_runtime')
        MCDS['metadata']['current_runtime'] = float(time_node.text)
        MCDS['metadata']['runtime_units'] = time_node.get('units')

        # find the microenvironment node
        me_node = root.find('microenvironment')
        me_node = me_node.find('domain')


        ####################
        # handle mesh data #
        ####################

        if self.verbose:
            print('working on mesh data ...')

        ### find the mesh node ###
        mesh_node = me_node.find('mesh')
        MCDS['metadata']['spatial_units'] = mesh_node.get('units')
        MCDS['mesh'] = {}

        # while we're at it, find the mesh
        s_x_coor = mesh_node.find('x_coordinates').text
        s_delim = mesh_node.find('x_coordinates').get('delimiter')
        ar_x_coor = np.array(s_x_coor.split(s_delim), dtype=np.float64)

        s_y_coor = mesh_node.find('y_coordinates').text
        s_delim = mesh_node.find('y_coordinates').get('delimiter')
        ar_y_coor = np.array(s_y_coor.split(s_delim), dtype=np.float64)

        s_z_coor = mesh_node.find('z_coordinates').text
        s_delim = mesh_node.find('z_coordinates').get('delimiter')
        ar_z_coor = np.array(s_z_coor.split(s_delim), dtype=np.float64)

        # reshape into a meshgrid
        MCDS['mesh']['mnp_grid'] = np.array(np.meshgrid(ar_x_coor, ar_y_coor, ar_z_coor, indexing='xy'))

        # get mesh center axis
        MCDS['mesh']['mnp_axis'] = [
            np.unique(ar_x_coor),
            np.unique(ar_y_coor),
            np.unique(ar_z_coor),
        ]

        # get mesh center range
        MCDS['mesh']['mnp_range'] = [
           (MCDS['mesh']['mnp_axis'][0].min(), MCDS['mesh']['mnp_axis'][0].max()),
           (MCDS['mesh']['mnp_axis'][1].min(), MCDS['mesh']['mnp_axis'][1].max()),
           (MCDS['mesh']['mnp_axis'][2].min(), MCDS['mesh']['mnp_axis'][2].max()),
        ]

        # get voxel range
        MCDS['mesh']['ijk_range'] = [
            (0, len(MCDS['mesh']['mnp_axis'][0]) - 1),
            (0, len(MCDS['mesh']['mnp_axis'][1]) - 1),
            (0, len(MCDS['mesh']['mnp_axis'][2]) - 1),
        ]

        # get voxel axis
        MCDS['mesh']['ijk_axis'] = [
            np.array(range(MCDS['mesh']['ijk_range'][0][1] + 1)),
            np.array(range(MCDS['mesh']['ijk_range'][1][1] + 1)),
            np.array(range(MCDS['mesh']['ijk_range'][2][1] + 1)),
        ]

        # get mesh bounding box range [xmin, ymin, zmin, xmax, ymax, zmax]
        bboxcoor_str = mesh_node.find('bounding_box').text
        delimiter = mesh_node.find('bounding_box').get('delimiter')
        ar_bboxcoor = np.array(bboxcoor_str.split(delimiter), dtype=np.float64)

        MCDS['mesh']['xyz_range'] = [
            (ar_bboxcoor[0], ar_bboxcoor[3]),
            (ar_bboxcoor[1], ar_bboxcoor[4]),
            (ar_bboxcoor[2], ar_bboxcoor[5]),
        ]

        # voxel data must be loaded from .mat file
        voxelfile = mesh_node.find('voxels').find('filename').text
        voxelpathfile = output_path / voxelfile
        try:
            initial_mesh = io.loadmat(voxelpathfile)['mesh']
            if self.verbose:
                print(f'reading: {voxelpathfile}')
        except:
            raise FileNotFoundError(f'Error @ pyMCDS._read_xml : no such file or directory: {voxelpathfile}\nreferenced in: {xmlpathfile}.')
            sys.exit(1)


        # center of voxel specified by first three rows [ x, y, z ]
        # volume specified by fourth row
        MCDS['mesh']['mnp_coordinate'] = initial_mesh[:3, :]
        MCDS['mesh']['volumes'] = initial_mesh[3, :]


        ################################
        # handle microenvironment data #
        ################################

        if self.microenv:
            if self.verbose:
                print('working on microenvironment data ...')

            # micro environment data is shape [4+n, len(voxels)] where n is the number
            # of species being tracked. the first 3 rows represent (x, y, z) of voxel
            # centers. The fourth row contains the voxel volume. The 5th row and up will
            # contain values for that species in that voxel.
            file_node = me_node.find('data').find('filename')
            mefile = file_node.text
            mepathfile = output_path / mefile
            # Changes here
            try:
                me_data = io.loadmat(mepathfile)['multiscale_microenvironment']
                if self.verbose:
                    print(f'reading: {mepathfile}')
            except:
                raise FileNotFoundError(f'Error @ pyMCDS._read_xml : no such file or directory: {mepathfile,}\nreferenced in: {xmlpathfile}.')
                sys.exit(1)

            # continuum_variables, unlike in the matlab version the individual chemical
            # species will be primarily accessed through their names e.g.
            # MCDS['continuum_variables']['oxygen']['units']
            # MCDS['continuum_variables']['glucose']['data']
            variables_node = me_node.find('variables')
            var_children = variables_node.findall('variable')
            MCDS['continuum_variables'] = {}

            # substrate loop
            for i_s, chemspecies in enumerate(var_children):
                # i don't like spaces in species names!
                s_substrate = chemspecies.get('name').replace(' ', '_')

                MCDS['continuum_variables'][s_substrate] = {}
                MCDS['continuum_variables'][s_substrate]['units'] = chemspecies.get('units')

                if self.verbose:
                    print(f'parsing: {s_substrate} data')

                # initialize meshgrid shaped array for concentration data
                MCDS['continuum_variables'][s_substrate]['data'] = np.zeros(MCDS['mesh']['mnp_grid'][0].shape)

                # travel down one level on tree
                chemspecies = chemspecies.find('physical_parameter_set')

                # diffusion data for each species
                MCDS['continuum_variables'][s_substrate]['diffusion_coefficient'] = {}
                MCDS['continuum_variables'][s_substrate]['diffusion_coefficient']['value'] = float(chemspecies.find('diffusion_coefficient').text)
                MCDS['continuum_variables'][s_substrate]['diffusion_coefficient']['units'] = chemspecies.find('diffusion_coefficient').get('units')

                # decay data for each species
                MCDS['continuum_variables'][s_substrate]['decay_rate'] = {}
                MCDS['continuum_variables'][s_substrate]['decay_rate']['value']  = float(chemspecies.find('decay_rate').text)
                MCDS['continuum_variables'][s_substrate]['decay_rate']['units']  = chemspecies.find('decay_rate').get('units')

                # store data from microenvironment file as numpy array
                # iterate over each voxel
                # bue: i have a hunch this could be faster reimplemented.
                for vox_idx in range(MCDS['mesh']['mnp_coordinate'].shape[1]):

                    # find the voxel coordinate
                    ar_center = MCDS['mesh']['mnp_coordinate'][:, vox_idx]
                    i = np.where(np.abs(ar_center[0] - MCDS['mesh']['mnp_axis'][0]) < 1e-10)[0][0]
                    j = np.where(np.abs(ar_center[1] - MCDS['mesh']['mnp_axis'][1]) < 1e-10)[0][0]
                    k = np.where(np.abs(ar_center[2] - MCDS['mesh']['mnp_axis'][2]) < 1e-10)[0][0]

                    # store value
                    MCDS['continuum_variables'][s_substrate]['data'][j, i, k] = me_data[4+i_s, vox_idx]


        ####################
        # handle cell data #
        ####################

        if self.verbose:
            print('working on discrete cell data ...')

        # in order to get to the good stuff, we have to pass through a few different hierarchical levels
        cell_node = root.find('cellular_information')
        cell_node = cell_node.find('cell_populations')
        cell_node = cell_node.find('cell_population')
        cell_node = cell_node.find('custom')
        # we want the PhysiCell data, there is more of it
        for child in cell_node.findall('simplified_data'):
            if child.get('source') == 'PhysiCell':
                cellchild_node = child
                break

        MCDS['discrete_cells'] = {}

        # iterate over labels which are children of labels these will be used to label data arrays
        data_labels = []
        ds_unit = {}
        for label in cellchild_node.find('labels').findall('label'):
            # I don't like spaces in my dictionary keys!
            fixed_label = label.text.replace(' ', '_')
            nlabels = int(label.get('size'))
            s_unit = label.get('units')
            if nlabels > 1:
                # tags to differentiate repeated labels (usually space related)
                # print("n=",n)
                spatial_type = False
                if( fixed_label == 'position' ):
                    spatial_type = True
                elif( fixed_label == 'orientation' ):
                    spatial_type = True
                elif( fixed_label == 'velocity' ):
                    spatial_type = True
                elif( fixed_label == 'migration_bias_direction' ):
                    spatial_type = True
                elif( fixed_label == 'motility_vector' ):
                    spatial_type = True

                if( nlabels == 3 and spatial_type == True ):
                    dir_label = ['_x', '_y', '_z']
                else:
                    dir_label = [];
                    for nn in range(100):
                        dir_label.append( '_%u' % nn )
                # print( dir_label )
                for i in range(int(label.get('size'))):
                    s_label = fixed_label + dir_label[i]
                    # print(s_label)
                    data_labels.append(s_label)
                    ds_unit.update({s_label : s_unit})
            else:
                # print(fixed_label)
                data_labels.append(fixed_label)
                ds_unit.update({fixed_label : s_unit})

        # store unit
        MCDS['discrete_cells']['units'] = ds_unit

        # load the file
        cellfile = cellchild_node.find('filename').text
        cellpathfile = output_path / cellfile
        try:
            cell_data = io.loadmat(cellpathfile)['cells']
            if self.verbose:
                print(f'reading: {cellpathfile}')
        except:
            raise FileNotFoundError(f'Error @ pyMCDS._read_xml : no such file or directory: {cellpathfile}\nreferenced in: {xmlpathfile}.')
            sys.exit(1)

        # store data
        MCDS['discrete_cells']['data'] = {}
        for col in range(len(data_labels)):
            MCDS['discrete_cells']['data'][data_labels[col]] = cell_data[col, :]


        #####################
        # handle graph data #
        #####################

        if self.graph:

            if self.verbose:
                print('working on graph data ...')

            MCDS['discrete_cells']['graph'] = {}

            # neighborhood cell graph
            cellgraph_node = cell_node.find('neighbor_graph')
            cellfile = cellgraph_node.find('filename').text
            cellpathfile = output_path / cellfile
            try:
                dei_graph = graphfile_parser(s_pathfile=cellpathfile)
                if self.verbose:
                    print(f'reading: {cellpathfile}')
            except:
                raise FileNotFoundError(f'Error @ pyMCDS._read_xml : no such file or directory: {cellpathfile}\nreferenced in: {xmlpathfile}.')
                sys.exit(1)

            # store data
            MCDS['discrete_cells']['graph'].update({'neighbor_cells': dei_graph})

            # attached cell graph
            cellgraph_node = cell_node.find('attached_cells_graph')
            cellfile = cellgraph_node.find('filename').text
            cellpathfile = output_path / cellfile
            try:
                dei_graph = graphfile_parser(s_pathfile=cellpathfile)
                if self.verbose:
                    print(f'reading: {cellpathfile}')
            except:
                raise FileNotFoundError(f'Error @ pyMCDS._read_xml : no such file or directory: {cellpathfile}\nreferenced in: {xmlpathfile}.')
                sys.exit(1)

            # store data
            MCDS['discrete_cells']['graph'].update({'attached_cells': dei_graph})

        # output
        if self.verbose:
            print('done!')
        return MCDS

def xmlfile_to_xmlpathfile(xmlfile, output_path):
    xmlfile = xmlfile.replace('\\','/')
    if (xmlfile.find('/') > -1) and (output_path == '.'):
        ls_xmlfile = xmlfile.split('/')
        xmlfile = ls_xmlfile.pop(-1)
        output_path = '/'.join(ls_xmlfile)
    output_path = pathlib.Path(output_path)
    xmlpathfile = output_path / xmlfile
    return xmlpathfile, output_path