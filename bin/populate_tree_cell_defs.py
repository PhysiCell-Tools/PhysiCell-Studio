"""

Parse the .xml config file and create the appropriate data structures that contain the info needed for cell defs.

Authors:
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
and rf. Credits.md

"""

import sys
import logging
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5 import QtCore
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QLineEdit


def invertf2s(sval):  # takes a numeric string, converts to float, returns string with num_dec decimal places.
    num_dec = 5
    if float(sval) < 1.e-6:   # e.g., necrosis duration=0 for index=0 (in biorobots, etc)
        return('9.e9')
    else:
        return f'{1.0/float(sval):{num_dec}f}' # invert

def validate_cell_defs(cell_defs_elm, skip_validate):
    logging.debug(f'\n\n=======================  validate_cell_defs(): ======================= ')

    # pheno_names = ['cycle','death','volume','mechanics','motility','secretion','cell_interactions','cell_transformations']

    # Since we provide default values for interactions & transformations, let's skip them.
    pheno_names = ['cycle','death','volume','mechanics','motility','secretion']
    valid = True
    for cd in cell_defs_elm.findall('cell_definition'):  # for each cell def
        logging.debug(f'Checking {cd.attrib["name"]}')
        for pn in pheno_names:
            phenotype = "phenotype//" + pn
            if cd.find(phenotype) == None:
                valid = False
                logging.debug(f'Validation Error: Missing {phenotype}')
    if not valid:
        if skip_validate:
            logging.debug(f'Continuing in spite of these missing elements.')
        else:
            # logging.debug(f'\n A configuration file (.xml) for the Studio needs to explicitly \nprovide all required parameters for each <cell_definition>.\nIt cannot use the legacy hierarchical format where only\n partial parameters are provided and the rest are inherited from a parent.")
            warn_user = """
            A configuration file (.xml) for the Studio needs to explicitly 
            provide all required parameters for each <cell_definition>.
            It cannot use the legacy hierarchical format where only 
            partial parameters are provided and the rest are inherited from a parent.

            Please fix your .xml config file to provide the missing information.

            """
            print(warn_user)
            sys.exit(-1)
    logging.debug(f'=======================  end validate_cell_defs(): =======================\n\n')

def handle_parse_error(section_str):
    msg = f'\npopulate_tree_cell_defs.py:\nError: parsing {section_str} params.\nYou are probably trying to use an older config file\nthat does not meet the Studio requirements. Each\ncell_definition needs to provide ALL parameters.\nTry to fix the config file.\n'
    print(msg)
    logging.error(msg)
    # msgBox = QMessageBox()
    # msgBox.setText(msg)
    # msgBox.setStandardButtons(QMessageBox.Ok)
    # returnValue = msgBox.exec()
    sys.exit(-1)

def populate_tree_cell_defs(cell_def_tab, skip_validate):
    logging.debug(f'=======================  populate_tree_cell_defs(): ======================= ')
    logging.debug(f'    cell_def_tab.param_d = {cell_def_tab.param_d}')
    # cell_def_tab.master_custom_varname.clear()
    cell_def_tab.master_custom_var_d.clear()
    cell_def_tab.clear_all_var_name_prev()

    cell_def_tab.new_cell_def_count = 0   # reset the somewhat artificial # of cell defs

    uep = cell_def_tab.xml_root.find(".//cell_definitions")
    validate_cell_defs(uep, skip_validate)

    uep = cell_def_tab.xml_root.find(".//cell_definitions")
    if uep:
        cell_def_tab.tree.clear()
        for idx, cell_def in enumerate(uep):
            # <cell_definition name="default" ID="0">
            logging.debug(f'----- cell_def.tag= {cell_def.tag}')
            if cell_def.tag != "cell_definition":
                logging.debug(f'-------- found unexpected child <cell_definitions>; skip over {cell_def}')
                continue
            if cell_def.tag == "cell_rules":
                logging.debug(f'-------- found cell_rules child; break out on {cell_def}')
                break
            cell_def_tab.new_cell_def_count += 1
            # print(cell_def.attrib['name'])
            cell_def_name = cell_def.attrib['name']

            if idx == 0:
                cell_def_0th = cell_def_name
                cell_def_tab.live_phagocytosis_celltype = cell_def_0th 
                cell_def_tab.attack_rate_celltype = cell_def_0th 
                cell_def_tab.fusion_rate_celltype = cell_def_0th 
                cell_def_tab.transformation_rate_celltype = cell_def_0th 

            # create master dict for this cell_def
            cell_def_tab.param_d[cell_def_name] = {}

            # create additional sub-dicts
            cell_def_tab.param_d[cell_def_name]["secretion"] = {}
            cell_def_tab.param_d[cell_def_name]['chemotactic_sensitivity'] = {}
            cell_def_tab.param_d[cell_def_name]["cell_adhesion_affinity"] = {}
            cell_def_tab.param_d[cell_def_name]["live_phagocytosis_rate"] = {}
            cell_def_tab.param_d[cell_def_name]["attack_rate"] = {}
            cell_def_tab.param_d[cell_def_name]["fusion_rate"] = {}
            cell_def_tab.param_d[cell_def_name]["transformation_rate"] = {}

            # fill this cell_def with default params (rf. C++ values)
            cell_def_tab.init_default_phenotype_params(cell_def_name, False)  #rwh 8/23/23: reset_mapping flag 
            # print("populate_(): ",cell_def_tab.param_d)
            # print("------   after populate ----------\n\n")


            cell_def_tab.param_d[cell_def_name]['ID'] = cell_def.attrib['ID']  # e.g., "0"
            # cell_def_tab.param_d[cell_def_name]["name"] = cell_def_name
            cell_def_tab.current_cell_def = cell_def_name  # do this for the callback methods?

            # cellname = QTreeWidgetItem([cell_def_name])
            cellname = QTreeWidgetItem([cell_def_name, cell_def.attrib['ID']])
            cellname.setFlags(cellname.flags() | QtCore.Qt.ItemIsEditable)
            cell_def_tab.tree.insertTopLevelItem(idx,cellname)
            if idx == 0:  # select the 1st (0th) entry
                cell_def_tab.tree.setCurrentItem(cellname)

            cell_def_tab.tree.resizeColumnToContents(idx)  # rwh (after adding ID column)

            # Now fill the param dict for each substrate and the Qt widget values for the 0th

            logging.debug(f'\n===== populate_tree():  cycle')

            cell_definition_path = f".//cell_definition[" + str(idx+1) + "]" # xml indexing starts at 1, python starts at 0
            phenotype_path = f"{cell_definition_path}//phenotype"
            cycle_path = f"{phenotype_path}//cycle"
            cycle_code = int(uep.find(cycle_path).attrib['code'])
            logging.debug(f' >> cycle_path= {cycle_path}')
            logging.debug(f'   cycle code= {cycle_code}')
                

            # NOTE: we don't seem to use 3 or 4
            # static const int advanced_Ki67_cycle_model= 0;
            # static const int basic_Ki67_cycle_model=1;
            # static const int flow_cytometry_cycle_model=2;
            # static const int live_apoptotic_cycle_model=3;
            # static const int total_cells_cycle_model=4;
            # static const int live_cells_cycle_model = 5; 
            # static const int flow_cytometry_separated_cycle_model = 6; 
            # static const int cycling_quiescent_model = 7; 

            # cell_def_tab.cycle_dropdown.addItem("live cells")  # 5
            # cell_def_tab.cycle_dropdown.addItem("basic Ki67")  # 1
            # cell_def_tab.cycle_dropdown.addItem("advanced Ki67")  # 0
            # cell_def_tab.cycle_dropdown.addItem("flow cytometry")  # 2
            # cell_def_tab.cycle_dropdown.addItem("flow cytometry separated")  # 6
            # cell_def_tab.cycle_dropdown.addItem("cycling quiescent")  # 7

            cycle_code_dict = {
                0: {'full_name': 'advanced Ki67', 'short_name': 'advancedKi67', 'idx': 2, 'num_phases': 3},
                1: {'full_name': 'basic Ki67', 'short_name': 'Ki67', 'idx': 1, 'num_phases': 2},
                2: {'full_name': 'flow cytometry', 'short_name': 'flowcyto', 'idx': 3, 'num_phases': 3},
                5: {'full_name': 'live cells', 'short_name': 'live', 'idx': 0, 'num_phases': 1},
                6: {'full_name': 'flow cytometry separated', 'short_name': 'flowcytosep', 'idx': 4, 'num_phases': 4},
                7: {'full_name': 'cycling quiescent', 'short_name': 'quiescent', 'idx': 5, 'num_phases': 2}
            }
            cell_def_tab.cycle_tab.cycle_dropdown.setCurrentIndex(cycle_code_dict[cycle_code]['idx'])
            cell_def_tab.param_d[cell_def_name]['cycle'] = cycle_code_dict[cycle_code]['full_name']
            cell_def_tab.param_d[cell_def_name]['cycle_choice_idx'] = cycle_code_dict[cycle_code]['idx']

        # rwh: We only use cycle code=5 or 6 in ALL sample projs?!
            # <cell_definition name="cargo cell" ID="2" visible="true">
            # 	<phenotype>
            # 		<cycle code="5" name="live">  
            # 			<phase_transition_rates units="1/min"> 
            # 				<rate start_index="0" end_index="0" fixed_duration="false">0.0</rate>
            # 			</phase_transition_rates>

            # <cycle code="6" name="Flow cytometry model (separated)">  
            # 	<phase_transition_rates units="1/min"> 
            # 		<rate start_index="0" end_index="1" fixed_duration="false">0</rate>
            # 		<rate start_index="1" end_index="2" fixed_duration="true">0.00208333</rate>
            # 		<rate start_index="2" end_index="3" fixed_duration="true">0.00416667</rate>
            # 		<rate start_index="3" end_index="0" fixed_duration="true">0.0166667</rate>

            possible_paths = [
                cycle_path + "//phase_transition_rates",
                cycle_path + "//transition_rates",
                cycle_path + "//phase_durations"
            ]

            # Search for the first existing path
            pt_uep = None
            for path in possible_paths:
                pt_uep = uep.find(path)
                if pt_uep:
                    break
            if path.endswith("//transition_rates"):
                logging.debug(f'\n\n--------------------- NOTE -----------------------------')
                logging.debug(f'populate_tree_cell_defs():\nFound deprecated cycle transition_rates')
                logging.debug(f'Update to use phase_transition_rates \n\n')
                logging.debug(f'-------------------------------------------------------\n\n')
                # sys.exit(1)

            is_duration = path.endswith("phase_durations")
            if is_duration:
                cell_def_tab.cycle_tab.cycle_rb2.setChecked(True)
                cell_def_tab.param_d[cell_def_name]['cycle_duration_flag'] = True
                cell_def_tab.cycle_tab.cycle_duration_flag = True   # rwh: TODO - why do this??
            else:
                cell_def_tab.cycle_tab.cycle_rb1.setChecked(True)
                cell_def_tab.param_d[cell_def_name]['cycle_duration_flag'] = False
                cell_def_tab.cycle_tab.cycle_duration_flag = False
            cell_def_tab.cycle_tab.customize_cycle_choices()

            key_base_name = f"cycle_{cycle_code_dict[cycle_code]['short_name']}"
            for phase_element in pt_uep: 
                logging.debug(f'{phase_element}')
                if is_duration:
                    phase_start_index = phase_element.attrib['index']
                    phase_end_index = (int(phase_start_index) + 1) % cycle_code_dict[cycle_code]['num_phases']
                else:
                    phase_start_index = phase_element.attrib['start_index']
                    phase_end_index = phase_element.attrib['end_index']
                key_with_phase = f"{key_base_name}_{phase_start_index}{phase_end_index}"

                sval = phase_element.text
                if is_duration:
                    cell_def_tab.param_d[cell_def_name][f"{key_with_phase}_trate"] = invertf2s(sval)
                    cell_def_tab.param_d[cell_def_name][f"{key_with_phase}_duration"] = sval
                else:
                    cell_def_tab.param_d[cell_def_name][f"{key_with_phase}_trate"] = sval
                    cell_def_tab.param_d[cell_def_name][f"{key_with_phase}_duration"] = invertf2s(sval)

                bval = phase_element.attrib['fixed_duration'].lower() == "true"
                cell_def_tab.param_d[cell_def_name][f"{key_with_phase}_fixed_trate"] = bval
                cell_def_tab.param_d[cell_def_name][f"{key_with_phase}_fixed_duration"] = bval

            # # --------- cell_asymmetric_divisions
            asymmetric_division_probabilities_path = f"{cycle_path}//standard_asymmetric_division"
            logging.debug(f'---- asymmetric_division_probabilities_path = {asymmetric_division_probabilities_path}')
            print(f'\n\n-----------\npopulate*.py: ---- asymmetric_division_probabilities_path = {asymmetric_division_probabilities_path}')
            # cell_def_tab.param_d[cell_def_name]['transformation_rate'] = {}

            cell_def_tab.param_d[cell_def_name]["asymmetric_division_probability"] = {}
            cds_uep = cell_def_tab.xml_root.find('.//cell_definitions')  # find unique entry point
            if cds_uep is None:
                logging.error(f'---- Error: cell_definitions is not defined.')
                sys.exit(-1)
            cell_def_tab.param_d[cell_def_name]["asymmetric_division_enabled"] = False
            for var in cds_uep.findall('cell_definition'):
                name = var.attrib['name']
                cell_def_tab.param_d[cell_def_name]["asymmetric_division_probability"][name] = '0' if name != cell_def_name else '1.0'
            adp_uep = uep.find(asymmetric_division_probabilities_path)
            if adp_uep is not None:
                # enable it if the enabled attribute is not present or is true
                cell_def_tab.param_d[cell_def_name]["asymmetric_division_enabled"] = ('enabled' not in adp_uep.attrib.keys() or adp_uep.attrib['enabled'].lower() == 'true')
                for adp in adp_uep.findall('asymmetric_division_probability'):
                    other_celltype_name = adp.attrib['name']
                    val = adp.text
                    cell_def_tab.param_d[cell_def_name]["asymmetric_division_probability"][other_celltype_name] = val
            val = cell_def_tab.param_d[cell_def_0th]["asymmetric_division_probability"][cell_def_name]
            cell_def_tab.cycle_tab.add_row_to_asym_div_table(cell_def_name, val)

            # ---------  death 
            logging.debug(f'\n===== populate_tree():  death')
            try:
                    #------ using transition_rates
                    #------ using durations
                death_path = f"{phenotype_path}//death"
                death_uep = uep.find(death_path)
                logging.debug(f'death_uep={death_uep}')

                for death_model in death_uep.findall('model'):
                    #-----------------------------------
                    # apoptosis only has 1 rate | duration (necrosis has 2) -------------------------
                    if "apoptosis" in death_model.attrib["name"].lower():
                        logging.debug(f'-------- parsing apoptosis!')
                        cell_def_tab.param_d[cell_def_name]["apoptosis_death_rate"] = death_model.find('death_rate').text

                        pd_uep = death_model.find("phase_durations")
                        if pd_uep is not None:
                            logging.debug(f' >> pd_uep ={pd_uep}')
                            cell_def_tab.param_d[cell_def_name]['apoptosis_duration_flag'] = True

                            for pd in pd_uep:   # <duration index= ... >
                                logging.debug(f'phase_duration= {pd}')
                                logging.debug(f'index= {pd.attrib["index"]}')
                                if  pd.attrib['index'] == "0":
                                    cell_def_tab.param_d[cell_def_name]["apoptosis_01_duration"] = pd.text
                                    cell_def_tab.param_d[cell_def_name]["apoptosis_01_trate"] = invertf2s(pd.text)
                                    if  pd.attrib['fixed_duration'].lower() == "true":
                                        cell_def_tab.param_d[cell_def_name]["apoptosis_01_fixed_duration"] = True
                                        cell_def_tab.param_d[cell_def_name]["apoptosis_01_fixed_trate"] = True
                                    else:
                                        cell_def_tab.param_d[cell_def_name]["apoptosis_01_fixed_duration"] = False
                                        cell_def_tab.param_d[cell_def_name]["apoptosis_01_fixed_trate"] = False

                        else:  #  apoptosis transition rate
                            tr_uep = death_model.find("phase_transition_rates")
                            if tr_uep is not None:
                                logging.debug(f' >> tr_uep ={tr_uep}')

                                for tr in tr_uep:   # <rate start_index= ... >
                                    logging.debug(f'death: phase_transition_rates= {tr}')
                                    logging.debug(f'start_index= {tr.attrib["start_index"]}')

                                    if  tr.attrib['start_index'] == "0":
                                        cell_def_tab.param_d[cell_def_name]["apoptosis_01_trate"] = tr.text
                                        cell_def_tab.param_d[cell_def_name]["apoptosis_01_duration"] = invertf2s(tr.text)
                                        if  tr.attrib['fixed_duration'].lower() == "true":
                                            cell_def_tab.param_d[cell_def_name]["apoptosis_01_fixed_trate"] = True
                                            cell_def_tab.param_d[cell_def_name]["apoptosis_01_fixed_duration"] = True
                                        else:
                                            cell_def_tab.param_d[cell_def_name]["apoptosis_01_fixed_trate"] = False
                                            cell_def_tab.param_d[cell_def_name]["apoptosis_01_fixed_duration"] = False

                        params_uep = death_model.find("parameters")

                        if params_uep is None:
                            print(f'\npopulate_tree_cell_defs.py: Error: missing death params.\nYou are probably trying to use an older config file that does not meet the Studio requirements.\nExiting.\n')
                            logging.error(f'\npopulate_tree_cell_defs.py: Error: missing death params.\nIt is possible your .xml is the old hierarchical format\nand not the flattened, explicit format.  \nExiting.\n')
                            # sys.exit(1)
                        cell_def_tab.param_d[cell_def_name]["apoptosis_unlysed_rate"] = params_uep.find("unlysed_fluid_change_rate").text
                        cell_def_tab.param_d[cell_def_name]["apoptosis_lysed_rate"] = params_uep.find("lysed_fluid_change_rate").text
                        cell_def_tab.param_d[cell_def_name]["apoptosis_cyto_rate"] = params_uep.find("cytoplasmic_biomass_change_rate").text
                        cell_def_tab.param_d[cell_def_name]["apoptosis_nuclear_rate"] = params_uep.find("nuclear_biomass_change_rate").text
                        cell_def_tab.param_d[cell_def_name]["apoptosis_calcif_rate"] = params_uep.find("calcification_rate").text
                        cell_def_tab.param_d[cell_def_name]["apoptosis_rel_rupture_volume"] = params_uep.find("relative_rupture_volume").text

                #-----------------------------------
                # necrosis_params_path = necrosis_path + "parameters//"
                    elif "necrosis" in death_model.attrib["name"].lower():
                        logging.debug(f'-------- parsing necrosis!')
                        cell_def_tab.param_d[cell_def_name]["necrosis_death_rate"] = death_model.find('death_rate').text

                        # necrosis has 2 rates | durations (apoptosis only has 1) -------------------------
                        pd_uep = death_model.find("phase_durations")
                        #------------------------
                        if pd_uep is not None:   # necrosis durations
                            logging.debug(f' >> pd_uep ={pd_uep}')
                            # cell_def_tab.necrosis_rb2.setChecked(True)  # duration
                            cell_def_tab.param_d[cell_def_name]['necrosis_duration_flag'] = True

                            for pd in pd_uep:   # <duration index= ... >
                                logging.debug(f'{pd}')
                                logging.debug(f'index= {pd.attrib["index"]}')
                                if  pd.attrib['index'] == "0":
                                    cell_def_tab.param_d[cell_def_name]["necrosis_01_duration"] = pd.text
                                    cell_def_tab.param_d[cell_def_name]["necrosis_01_trate"] = invertf2s(pd.text)
                                    if  pd.attrib['fixed_duration'].lower() == "true":
                                        cell_def_tab.param_d[cell_def_name]["necrosis_01_fixed_duration"] = True
                                        cell_def_tab.param_d[cell_def_name]["necrosis_01_fixed_trate"] = True
                                    else:
                                        cell_def_tab.param_d[cell_def_name]["necrosis_01_fixed_duration"] = False
                                        cell_def_tab.param_d[cell_def_name]["necrosis_01_fixed_trate"] = False

                                elif  pd.attrib['index'] == "1":
                                    cell_def_tab.param_d[cell_def_name]["necrosis_12_duration"] = pd.text
                                    cell_def_tab.param_d[cell_def_name]["necrosis_12_trate"] = invertf2s(pd.text)
                                    if  pd.attrib['fixed_duration'].lower() == "true":
                                        cell_def_tab.param_d[cell_def_name]["necrosis_12_fixed_duration"] = True
                                        cell_def_tab.param_d[cell_def_name]["necrosis_12_fixed_trate"] = True
                                    else:
                                        cell_def_tab.param_d[cell_def_name]["necrosis_12_fixed_duration"] = False
                                        cell_def_tab.param_d[cell_def_name]["necrosis_12_fixed_trate"] = False

                        #------------------------
                        else:  # necrosis transition rates
                            tr_uep = death_model.find("phase_transition_rates")
                            if tr_uep is not None:
                                logging.debug(f' >> tr_uep ={tr_uep}')
                                for tr in tr_uep:  # transition rate 
                                    logging.debug(f'death: phase_transition_rates= {tr}')
                                    logging.debug(f'start_index= {tr.attrib["start_index"]}')
                                    if  tr.attrib['start_index'] == "0":
                                        rate = float(tr.text)
                                        if abs(rate) < 1.e-6:   # rwh: necessary??
                                            rate = 1.e-6
                                            # dval = 9.e99
                                        # else:
                                            # dval = rate * 60.0
                                        logging.debug(f' --- transition rate 01 (float) = {rate}')
                                        cell_def_tab.param_d[cell_def_name]["necrosis_01_trate"] = str(rate)
                                        cell_def_tab.param_d[cell_def_name]["necrosis_01_duration"] = invertf2s(str(rate))
                                        if  tr.attrib['fixed_duration'].lower() == "true":
                                            cell_def_tab.param_d[cell_def_name]["necrosis_01_fixed_trate"] = True
                                            cell_def_tab.param_d[cell_def_name]["necrosis_01_fixed_duration"] = True
                                        else:
                                            cell_def_tab.param_d[cell_def_name]["necrosis_01_fixed_trate"] = False
                                            cell_def_tab.param_d[cell_def_name]["necrosis_01_fixed_duration"] = False

                                    elif  tr.attrib['start_index'] == "1":
                                        rate = float(tr.text)
                                        if abs(rate) < 1.e-6:
                                            rate = 1.e-6
                                        logging.debug(f' --- transition rate 12 (float) = {rate}')
                                        cell_def_tab.param_d[cell_def_name]["necrosis_12_trate"] = str(rate)
                                        cell_def_tab.param_d[cell_def_name]["necrosis_12_duration"] = invertf2s(str(rate))
                                        if  tr.attrib['fixed_duration'].lower() == "true":
                                            cell_def_tab.param_d[cell_def_name]["necrosis_12_fixed_trate"] = True
                                            cell_def_tab.param_d[cell_def_name]["necrosis_12_fixed_duration"] = True
                                        else:
                                            cell_def_tab.param_d[cell_def_name]["necrosis_12_fixed_trate"] = False
                                            cell_def_tab.param_d[cell_def_name]["necrosis_12_fixed_duration"] = False

                        params_uep = death_model.find("parameters")

                        cell_def_tab.param_d[cell_def_name]["necrosis_unlysed_rate"] = params_uep.find("unlysed_fluid_change_rate").text
                        cell_def_tab.param_d[cell_def_name]["necrosis_lysed_rate"] = params_uep.find("lysed_fluid_change_rate").text
                        cell_def_tab.param_d[cell_def_name]["necrosis_cyto_rate"] = params_uep.find("cytoplasmic_biomass_change_rate").text
                        cell_def_tab.param_d[cell_def_name]["necrosis_nuclear_rate"] = params_uep.find("nuclear_biomass_change_rate").text
                        cell_def_tab.param_d[cell_def_name]["necrosis_calcif_rate"] = params_uep.find("calcification_rate").text
                        cell_def_tab.param_d[cell_def_name]["necrosis_rel_rupture_rate"] = params_uep.find("relative_rupture_volume").text
            except:
                handle_parse_error('death')

            # # ---------  volume 
            volume_path = f"{phenotype_path}//volume//"
            logging.debug(f'volume_path={volume_path}')
            try:
                cell_def_tab.param_d[cell_def_name]["volume_total"] = uep.find(volume_path+"total").text
                cell_def_tab.param_d[cell_def_name]["volume_fluid_fraction"] = uep.find(volume_path+"fluid_fraction").text
                cell_def_tab.param_d[cell_def_name]["volume_nuclear"] = uep.find(volume_path+"nuclear").text
                cell_def_tab.param_d[cell_def_name]["volume_fluid_change_rate"] = uep.find(volume_path+"fluid_change_rate").text
                cell_def_tab.param_d[cell_def_name]["volume_cytoplasmic_rate"] = uep.find(volume_path+"cytoplasmic_biomass_change_rate").text
                cell_def_tab.param_d[cell_def_name]["volume_nuclear_rate"] = uep.find(volume_path+"nuclear_biomass_change_rate").text
                cell_def_tab.param_d[cell_def_name]["volume_calcif_fraction"] = uep.find(volume_path+"calcified_fraction").text
                cell_def_tab.param_d[cell_def_name]["volume_calcif_rate"] = uep.find(volume_path+"calcification_rate").text
                cell_def_tab.param_d[cell_def_name]["volume_rel_rupture_vol"] = uep.find(volume_path+"relative_rupture_volume").text
            except:
                handle_parse_error('volume')

            # # ---------  mechanics 
            logging.debug(f'\n===== populate_tree():  mechanics')

            mechanics_path = f"{phenotype_path}//mechanics//"
            logging.debug(f'mechanics_path={mechanics_path}')
            try:
                is_movable_tag =  uep.find(mechanics_path+"is_movable")
                if is_movable_tag:
                    val =  uep.find(mechanics_path+"is_movable").text
                    if val.lower() == 'true':
                        cell_def_tab.param_d[cell_def_name]["is_movable"] = True
                    else:
                        cell_def_tab.param_d[cell_def_name]["is_movable"] = False
                else:
                    cell_def_tab.param_d[cell_def_name]["is_movable"] = True

                val =  uep.find(mechanics_path+"cell_cell_adhesion_strength").text
                cell_def_tab.param_d[cell_def_name]["mechanics_adhesion"] = val

                val =  uep.find(mechanics_path+"cell_cell_repulsion_strength").text
                cell_def_tab.param_d[cell_def_name]["mechanics_repulsion"] = val

                val =  uep.find(mechanics_path+"relative_maximum_adhesion_distance").text
                cell_def_tab.param_d[cell_def_name]["mechanics_adhesion_distance"] = val

                # <<< new (June 2022) mechanics params
                mypath =  uep.find(mechanics_path+"cell_BM_adhesion_strength")
                if mypath is not None:
                    cell_def_tab.param_d[cell_def_name]["mechanics_BM_adhesion"] = mypath.text
                else:
                    cell_def_tab.param_d[cell_def_name]["mechanics_BM_adhesion"] = '4.0'

                mypath =  uep.find(mechanics_path+"cell_BM_repulsion_strength")
                if mypath is not None:
                    cell_def_tab.param_d[cell_def_name]["mechanics_BM_repulsion"] = mypath.text
                else:
                    cell_def_tab.param_d[cell_def_name]["mechanics_BM_repulsion"] = '10.0'

                #----------
                cell_adhesion_affinities_path = f"{mechanics_path}cell_adhesion_affinities"
                logging.debug(f'---- cell_interactions_path= {cell_adhesion_affinities_path}')
                cap = uep.find(cell_adhesion_affinities_path)
                if cap is None:
                    logging.debug(f'---- No cell_adhesion_affinities_path found. Setting to default.')
                    cds_uep = cell_def_tab.xml_root.find('.//cell_definitions')  # find unique entry point
                    if cds_uep is None:
                        logging.debug(f'---- Error: cell_definitions is not defined.')
                        # sys.exit(-1)

                    sval = '1.0'
                    for var in cds_uep.findall('cell_definition'):
                        logging.debug(f' --> {var.attrib["name"]}')
                        name = var.attrib['name']
                        cell_def_tab.param_d[cell_def_name]["cell_adhesion_affinity"][name] = sval

                else:
                    logging.debug(f'---- found cell_adhesion_affinities_path:')
                    cell_def_tab.param_d[cell_def_name]["cell_adhesion_affinity"] = {}
                    for var in cap.findall('cell_adhesion_affinity'):
                        other_celltype_name = var.attrib['name']
                        val = var.text
                        cell_def_tab.param_d[cell_def_name]["cell_adhesion_affinity"][other_celltype_name] = val
                        logging.debug(f'--> {cell_def_tab.param_d[cell_def_name]["cell_adhesion_affinity"]}')

                #----------
                mechanics_options_path = f"{mechanics_path}options//"

                val =  uep.find(mechanics_options_path+"set_relative_equilibrium_distance").text
                cell_def_tab.param_d[cell_def_name]["mechanics_relative_equilibrium_distance"] = val

                val =  uep.find(mechanics_options_path+"set_absolute_equilibrium_distance").text
                cell_def_tab.param_d[cell_def_name]["mechanics_absolute_equilibrium_distance"] = val

                rel_eq_bval = uep.find(mechanics_options_path+"set_relative_equilibrium_distance").attrib['enabled'].lower() == 'true'
                cell_def_tab.param_d[cell_def_name]["mechanics_relative_equilibrium_distance_enabled"] = rel_eq_bval

                abs_eq_bval = uep.find(mechanics_options_path+"set_absolute_equilibrium_distance").attrib['enabled'].lower() == 'true'
                cell_def_tab.param_d[cell_def_name]["mechanics_absolute_equilibrium_distance_enabled"] = abs_eq_bval

                if cell_def_name==cell_def_0th:
                    print(f"populate_tree_cell_defs.py: cell_def_name= {cell_def_name},  rel_eq_bval= {rel_eq_bval}, abs_eq_bval= {abs_eq_bval}")
                    cell_def_tab.set_relative_equilibrium_distance_enabled.setChecked(rel_eq_bval)
                    cell_def_tab.set_relative_equilibrium_distance_enabled.stateChanged.emit(rel_eq_bval)
                    cell_def_tab.set_absolute_equilibrium_distance_enabled.setChecked(abs_eq_bval)
                    cell_def_tab.set_absolute_equilibrium_distance_enabled.stateChanged.emit(abs_eq_bval)

                # <<< new (June 2022) mechanics params
                mypath =  uep.find(mechanics_path+"attachment_elastic_constant")
                if mypath is not None:
                    cell_def_tab.param_d[cell_def_name]["mechanics_elastic_constant"] = mypath.text
                else:
                    cell_def_tab.param_d[cell_def_name]["mechanics_elastic_constant"] = '0.01'

                mypath =  uep.find(mechanics_path+"attachment_rate")
                if mypath is not None:
                    cell_def_tab.param_d[cell_def_name]["attachment_rate"] = mypath.text
                else:
                    cell_def_tab.param_d[cell_def_name]["attachment_rate"] = '0.0'

                mypath =  uep.find(mechanics_path+"detachment_rate")
                if mypath is not None:
                    cell_def_tab.param_d[cell_def_name]["detachment_rate"] = mypath.text
                else:
                    cell_def_tab.param_d[cell_def_name]["detachment_rate"] = '0.0'

                mypath =  uep.find(mechanics_path+"maximum_number_of_attachments")
                if mypath is not None:
                    cell_def_tab.param_d[cell_def_name]["mechanics_max_num_attachments"] = mypath.text
                else:
                    cell_def_tab.param_d[cell_def_name]["mechanics_max_num_attachments"] = '12'

            except:
                handle_parse_error('mechanics')

            # # ---------  motility 
            logging.debug(f'\n===== populate_tree():  motility')

            motility_path = f"{phenotype_path}//motility//"
            logging.debug(f'motility_path={motility_path}')
            try:
                val = uep.find(motility_path+"speed").text
                cell_def_tab.param_d[cell_def_name]["speed"] = val

                val = uep.find(motility_path+"persistence_time").text
                cell_def_tab.param_d[cell_def_name]["persistence_time"] = val

                val = uep.find(motility_path+"migration_bias").text
                cell_def_tab.param_d[cell_def_name]["migration_bias"] = val

                motility_options_path = f"{motility_path}options//"

                if uep.find(motility_options_path +'enabled').text.lower() == 'true':
                    cell_def_tab.param_d[cell_def_name]["motility_enabled"] = True
                else:
                    cell_def_tab.param_d[cell_def_name]["motility_enabled"] = False

                if uep.find(motility_options_path +'use_2D').text.lower() == 'true':
                    cell_def_tab.param_d[cell_def_name]["motility_use_2D"] = True
                else:
                    cell_def_tab.param_d[cell_def_name]["motility_use_2D"] = False

                motility_chemotaxis_path = motility_options_path + "chemotaxis//"
                if uep.find(motility_chemotaxis_path) is None:
                    cell_def_tab.param_d[cell_def_name]["motility_chemotaxis"] = False
                    cell_def_tab.param_d[cell_def_name]["motility_chemotaxis_substrate"] = ""
                    cell_def_tab.param_d[cell_def_name]["motility_chemotaxis_towards"] = True
                else:
                    if uep.find(motility_chemotaxis_path +'enabled').text.lower() == 'true':
                        cell_def_tab.param_d[cell_def_name]["motility_chemotaxis"] = True
                    else:
                        cell_def_tab.param_d[cell_def_name]["motility_chemotaxis"] = False

                    val = uep.find(motility_chemotaxis_path +'substrate').text
                    cell_def_tab.param_d[cell_def_name]["motility_chemotaxis_substrate"] = val
                    logging.debug(f'\n----------- populate_tree_cell_defs.py: cell_def_name= {cell_def_name},  cell_def_tab.param_d[cell_def_name]["motility_chemotaxis_substrate"] = {cell_def_tab.param_d[cell_def_name]["motility_chemotaxis_substrate"]}')

                    val = uep.find(motility_chemotaxis_path +'direction').text
                    if val == '1':
                        cell_def_tab.param_d[cell_def_name]["motility_chemotaxis_towards"] = True
                    else:
                        cell_def_tab.param_d[cell_def_name]["motility_chemotaxis_towards"] = False

                motility_advanced_chemotaxis_path = motility_options_path + "advanced_chemotaxis//"
                logging.debug(f'motility_advanced_chemotaxis_path= {motility_advanced_chemotaxis_path}')


                # Just initialize sensitivities to default value (0) for all substrates
                uep_microenv = cell_def_tab.xml_root.find(".//microenvironment_setup")
                for subelm in uep_microenv.findall('variable'):
                    substrate_name = subelm.attrib['name']
                    cell_def_tab.param_d[cell_def_name]["chemotactic_sensitivity"][substrate_name] = '0.0'
                logging.debug(f'chemotactic_sensitivity= {cell_def_tab.param_d[cell_def_name]["chemotactic_sensitivity"]}')

                if uep.find(motility_advanced_chemotaxis_path) is None:  # advanced_chemotaxis not present in .xml
                    logging.debug(f'---- no motility_advanced_chemotaxis_path found. Setting to default values')
                    cell_def_tab.param_d[cell_def_name]["motility_advanced_chemotaxis"] = False
                    cell_def_tab.param_d[cell_def_name]["motility_advanced_chemotaxis_substrate"] = ""
                    cell_def_tab.param_d[cell_def_name]["normalize_each_gradient"] = False

                else:    # advanced_chemotaxis IS present in .xml
                    if uep.find(motility_advanced_chemotaxis_path +'enabled').text.lower() == 'true':
                        cell_def_tab.param_d[cell_def_name]["motility_advanced_chemotaxis"] = True
                    else:
                        cell_def_tab.param_d[cell_def_name]["motility_advanced_chemotaxis"] = False

                    if uep.find(motility_advanced_chemotaxis_path +'normalize_each_gradient').text.lower() == 'true':
                        cell_def_tab.param_d[cell_def_name]["normalize_each_gradient"] = True
                    else:
                        cell_def_tab.param_d[cell_def_name]["normalize_each_gradient"] = False

                    # rwh: todo - why am I doing this? Is it necessary?
                    cell_def_tab.param_d[cell_def_name]["motility_advanced_chemotaxis_substrate"] = "foobar"

                    if uep.find(motility_advanced_chemotaxis_path +'normalize_each_gradient').text.lower() == 'true':
                        cell_def_tab.param_d[cell_def_name]["normalize_each_gradient"] = True
                    else:
                        cell_def_tab.param_d[cell_def_name]["normalize_each_gradient"] = False

                    cell_def_tab.param_d[cell_def_name]['chemotactic_sensitivity'] = {}
                    for substrate in cell_def_tab.substrate_list:
                        # cell_def_tab.chemotactic_sensitivity_dict[substrate] = 0.0
                        cell_def_tab.param_d[cell_def_name]["chemotactic_sensitivity"][substrate] = '0.0'

                    #-----
                    sensitivity_path = motility_options_path + "advanced_chemotaxis//chemotactic_sensitivities"
                    logging.debug(f'sensitivity_path= {sensitivity_path}')
                    if uep.find(sensitivity_path) is None:
                        logging.debug(f'---- chemotactic_sensitivities not found. Set to defaults (0). ')
                    else:
                        logging.debug(f'---- found chemotactic_sensitivities: {uep.find(sensitivity_path)}')
                        for subelm in uep.find(sensitivity_path).findall('chemotactic_sensitivity'):
                            subname = subelm.attrib['substrate']
                            subval = subelm.text # float?
                            logging.debug(f'subelm={subelm}')
                            logging.debug(f' chemotactic_sensitivity--> {subname} = {subval}')
                            cell_def_tab.param_d[cell_def_name]['chemotactic_sensitivity'][subname] = subval
                    logging.debug(f'{cell_def_tab.param_d[cell_def_name]["chemotactic_sensitivity"]}')

                    cell_def_tab.motility2_substrate_changed_cb(0)  # update the sensitivity value in the widget
            except:
                handle_parse_error('motility')

            # # ---------  secretion 
            logging.debug(f'\n===== populate_tree():  secretion')

            secretion_path = f"{phenotype_path}//secretion"
            logging.debug(f'secretion_path = {secretion_path}')
            secretion_sub1_path = f"{secretion_path}//substrate[1]//"

            uep_secretion = cell_def_tab.xml_root.find(secretion_path)
            logging.debug(f'uep_secretion = {uep_secretion}')
            try:
                jdx = 0
                for sub in uep_secretion.findall('substrate'):
                    substrate_name = sub.attrib['name']
                    if jdx == 0:
                        cell_def_tab.current_secretion_substrate = substrate_name

                    logging.debug(f'{jdx}) -- secretion substrate = {substrate_name}')
                    # cell_def_tab.param_d[cell_def_tab.current_cell_def]["secretion"][substrate_name]["secretion_rate"] = {}
                    cell_def_tab.param_d[cell_def_name]["secretion"][substrate_name] = {}

                    tptr = sub.find("secretion_rate")
                    if tptr is not None:
                        val = tptr.text
                    else:
                        val = "0.0"
                    cell_def_tab.param_d[cell_def_name]["secretion"][substrate_name]["secretion_rate"] = val
                    # print(cell_def_tab.param_d[cell_def_name]["secretion"][substrate_name] )

                    tptr = sub.find("secretion_target")
                    if tptr is not None:
                        val = tptr.text
                    else:
                        val = "0.0"
                    cell_def_tab.param_d[cell_def_name]["secretion"][substrate_name]["secretion_target"] = val

                    tptr = sub.find("uptake_rate")
                    if tptr is not None:
                        val = tptr.text
                    else:
                        val = "0.0"
                    cell_def_tab.param_d[cell_def_name]["secretion"][substrate_name]["uptake_rate"] = val

                    tptr = sub.find("net_export_rate")
                    if tptr is not None:
                        val = tptr.text
                    else:
                        val = "0.0"
                    cell_def_tab.param_d[cell_def_name]["secretion"][substrate_name]["net_export_rate"] = val

                    jdx += 1

                logging.debug(f'------ done parsing secretion:')
            except:
                handle_parse_error('secretion')
            

            # # --------- cell_interactions  
            logging.debug(f'\n===== populate_tree():  cell_interactions')
            cell_interactions_path = f"{phenotype_path}//cell_interactions"
            logging.debug(f'---- cell_interactions_path= {cell_interactions_path}')
            cep = uep.find(cell_interactions_path)
            if cep is None:
                logging.debug(f'---- no cell_interactions found. Setting to default values')

                cell_def_tab.param_d[cell_def_name]["apoptotic_phagocytosis_rate"] = '0.0'
                cell_def_tab.param_d[cell_def_name]["necrotic_phagocytosis_rate"] = '0.0'
                cell_def_tab.param_d[cell_def_name]["other_dead_phagocytosis_rate"] = '0.0'
                cell_def_tab.param_d[cell_def_name]["attack_damage_rate"] = '1.0'
                cell_def_tab.param_d[cell_def_name]["attack_duration"] = '0.1'
                cell_def_tab.param_d[cell_def_name]["damage_rate"] = '0.0'
                cell_def_tab.param_d[cell_def_name]["damage_repair_rate"] = '0.0'

                cds_uep = cell_def_tab.xml_root.find('.//cell_definitions')  # find unique entry point
                if cds_uep is None:
                    logging.debug(f'---- Error: cell_definitions is not defined.')
                    # sys.exit(-1)

                sval = '0.0'
                for var in cds_uep.findall('cell_definition'):
                    logging.debug(f' --> {var.attrib["name"]}')
                    name = var.attrib['name']
                    cell_def_tab.param_d[cell_def_name]["live_phagocytosis_rate"][name] = sval
                    cell_def_tab.param_d[cell_def_name]["attack_rate"][name] = sval
                    cell_def_tab.param_d[cell_def_name]["fusion_rate"][name] = sval
            else:
                logging.debug(f'---- found cell_interactions:')
                dead_phagocytosis_rate_names = ["apoptotic_phagocytosis_rate", "necrotic_phagocytosis_rate", "other_dead_phagocytosis_rate"]
                dead_phagocytosis_rates = ['0.0'] * 3
                pre_v1_14_0_phagocytosis = cep.find("dead_phagocytosis_rate") is not None
                if pre_v1_14_0_phagocytosis:
                    dead_phagocytosis_rates = [cep.find("dead_phagocytosis_rate").text] * 3
                for index, name in enumerate(dead_phagocytosis_rate_names):
                    if cep.find(name) is not None: # DRB: I had thought we would enter this block if the name was found, but we have to compare to None I guess
                        dead_phagocytosis_rates[index] = cep.find(name).text
                    cell_def_tab.param_d[cell_def_name][name] = dead_phagocytosis_rates[index]

                cell_def_tab.pre_v1_14_0_damage_rate = cep.find("damage_rate") is not None
                if cell_def_tab.pre_v1_14_0_damage_rate:
                    val = cep.find("damage_rate").text
                elif cep.find("attack_damage_rate") is not None: # change tag - 1.14.0
                    val = cep.find("attack_damage_rate").text
                else: # no attack damage rate found, default to 1.0
                    val = '1.0'
                cell_def_tab.param_d[cell_def_name]["attack_damage_rate"] = val

                if cep.find("attack_duration") is not None:  # 1.14.0
                    val = cep.find("attack_duration").text
                else:
                    val = '0.1'
                cell_def_tab.param_d[cell_def_name]["attack_duration"] = val

                uep2 = uep.find(cell_interactions_path + "//live_phagocytosis_rates")
                logging.debug(f'uep2= {uep2}')
                cell_def_tab.param_d[cell_def_name]["live_phagocytosis_rate"] = {}
                for pr in uep2.findall('phagocytosis_rate'):
                    other_celltype_name = pr.attrib['name']
                    val = pr.text
                    cell_def_tab.param_d[cell_def_name]["live_phagocytosis_rate"][other_celltype_name] = val

                uep2 = uep.find(cell_interactions_path + "//attack_rates")
                cell_def_tab.param_d[cell_def_name]["attack_rate"] = {}
                for ar in uep2.findall('attack_rate'):
                    other_celltype_name = ar.attrib['name']
                    val = ar.text
                    cell_def_tab.param_d[cell_def_name]["attack_rate"][other_celltype_name] = val

                uep2 = uep.find(cell_interactions_path + "//fusion_rates")
                cell_def_tab.param_d[cell_def_name]["fusion_rate"] = {}
                for ar in uep2.findall('fusion_rate'):
                    other_celltype_name = ar.attrib['name']
                    val = ar.text
                    cell_def_tab.param_d[cell_def_name]["fusion_rate"][other_celltype_name] = val

            logging.debug(f' live_phagocytosis_rate= {cell_def_tab.param_d[cell_def_name]["live_phagocytosis_rate"]}')
            logging.debug(f' attack_rate= {cell_def_tab.param_d[cell_def_name]["attack_rate"]}')
            logging.debug(f' fusion_rate= {cell_def_tab.param_d[cell_def_name]["fusion_rate"]}')
            logging.debug(f'------ done parsing cell_interactions:')


            # # --------- cell_transformations  
            transformation_rates_path = f"{phenotype_path}//cell_transformations//transformation_rates"
            logging.debug(f'---- transformation_rates_path = {transformation_rates_path}')
            print(f'\n\n-----------\npopulate*.py: l. 1255 ---- transformation_rates_path = {transformation_rates_path}')
            trp = uep.find(transformation_rates_path)
            if trp is None:
                print("---- No cell_transformations found.")
                logging.debug(f'---- No cell_transformations found. Setting to default values')
                print(f'---- No cell_transformations found. Setting to default values')
                cell_def_tab.param_d[cell_def_name]['transformation_rate'] = {}

                cds_uep = cell_def_tab.xml_root.find('.//cell_definitions')  # find unique entry point
                if cds_uep is None:
                    logging.error(f'---- Error: cell_definitions is not defined.')
                    # sys.exit(-1)

                sval = '0.0'
                for var in cds_uep.findall('cell_definition'):
                    logging.debug(f' --> {var.attrib["name"]}')
                    print(f"ugh!---- setting {cell_def_name}'s cell_transformations for {name} = default=0.0")
                    name = var.attrib['name']
                    cell_def_tab.param_d[cell_def_name]["transformation_rate"][name] = sval
            else:
                print(f"---- found cell_transformations for {cell_def_name}, now loop thru them:")
                for tr in trp.findall('transformation_rate'):
                    other_celltype_name = tr.attrib['name']
                    val = tr.text
                    cell_def_tab.param_d[cell_def_name]['transformation_rate'][other_celltype_name] = val


            logging.debug(f' transformation_rate= {cell_def_tab.param_d[cell_def_name]["transformation_rate"]}')
            print(f'populate_tree_cell_defs.py: {cell_def_name}----> transformation_rate= {cell_def_tab.param_d[cell_def_name]["transformation_rate"]}')
            logging.debug(f'------ done parsing cell_transformations:')

            # # --------- cell_integrity  
            cell_integrity_path = f"{phenotype_path}//cell_integrity"
            logging.debug(f'---- cell_integrity_path = {cell_integrity_path}')
            print(f'\n\n-----------\npopulate*.py: ---- cell_integrity_path = {cell_integrity_path}')
            cip = uep.find(cell_integrity_path)

            if cip is None:
                print("---- No cell_integrity found.")
                logging.debug(f'---- No cell_integrity found. Setting to default values')
                print(f'---- No cell_integrity found. Setting to default values')
                cell_def_tab.param_d[cell_def_name]["damage_rate"] = '0.0'
                cell_def_tab.param_d[cell_def_name]["damage_repair_rate"] = '0.0'
            else:
                print(f"---- found cell_integrity for {cell_def_name}")
                val = cip.find("damage_rate").text
                cell_def_tab.param_d[cell_def_name]["damage_rate"] = val
                val = cip.find("damage_repair_rate").text
                cell_def_tab.param_d[cell_def_name]["damage_repair_rate"] = val

            logging.debug(f' damage_rate= {cell_def_tab.param_d[cell_def_name]["damage_rate"]}')
            print(f'populate_tree_cell_defs.py: {cell_def_name}----> damage_rate= {cell_def_tab.param_d[cell_def_name]["damage_rate"]}')
            logging.debug(f'------ done parsing cell_integrity:')

            # # ---------  molecular 
            logging.debug(f'\n===== populate_tree():  molecular')


            # # ---------  intracellular 
            logging.debug(f'\n===== populate_tree():  intracellular')
            intracellular_path = f"{phenotype_path}//intracellular"
         
            uep_intracellular = cell_def_tab.xml_root.find(intracellular_path)
            cell_def_tab.param_d[cell_def_name]["intracellular"] = None

            if uep_intracellular is not None and "type" in uep_intracellular.attrib:  # also check for <intracellular />
                cell_def_tab.param_d[cell_def_name]["intracellular"] = {}
                if uep_intracellular.attrib["type"] == "maboss":
                    # --------- PhysiBoSS specific code
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["type"] = "maboss" 
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["bnd_filename"] = uep_intracellular.find("bnd_filename").text if uep_intracellular.find("bnd_filename") is not None else None
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["cfg_filename"] = uep_intracellular.find("cfg_filename").text if uep_intracellular.find("cfg_filename") is not None else None

                    # default values
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["time_step"] = "12.0"
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["scaling"] = "1.0"
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["time_stochasticity"] = "0.0"
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["start_time"] = "0.0"
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["global_inheritance"] = "False"
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["node_inheritance"] = []
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["mutants"] = []
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["parameters"] = []

                    uep_settings = uep_intracellular.find("settings")
                    if uep_settings is not None:
                        cell_def_tab.param_d[cell_def_name]["intracellular"]["time_step"] = uep_settings.find("intracellular_dt").text if uep_settings.find("intracellular_dt") is not None else "12.0"
                        cell_def_tab.param_d[cell_def_name]["intracellular"]["scaling"] = uep_settings.find("scaling").text if uep_settings.find("scaling") is not None else "1.0"
                        cell_def_tab.param_d[cell_def_name]["intracellular"]["time_stochasticity"] = uep_settings.find("time_stochasticity").text if uep_settings.find("time_stochasticity") is not None else "0.0"
                        cell_def_tab.param_d[cell_def_name]["intracellular"]["start_time"] = uep_settings.find("start_time").text if uep_settings.find("start_time") is not None else "0.0"
                        cell_def_tab.param_d[cell_def_name]["intracellular"]["global_inheritance"] = uep_settings.find("inheritance").attrib["global"] if uep_settings.find("inheritance") is not None and uep_settings.find("inheritance").attrib["global"] else "False"
                        cell_def_tab.param_d[cell_def_name]["intracellular"]["node_inheritance"] = []
                        uep_intracellular_nodes_inheritance = uep_settings.find("inheritance")
                        if uep_intracellular_nodes_inheritance is not None:
                            for node_inheritance in uep_intracellular_nodes_inheritance:
                                cell_def_tab.param_d[cell_def_name]["intracellular"]["node_inheritance"].append({
                                    "node": node_inheritance.attrib["intracellular_name"], "flag": node_inheritance.text
                                })

                        cell_def_tab.param_d[cell_def_name]["intracellular"]["mutants"] = []
                        uep_intracellular_mutants = uep_settings.find("mutations")
                        if uep_intracellular_mutants is not None:
                            for mutant in uep_intracellular_mutants:
                                cell_def_tab.param_d[cell_def_name]["intracellular"]["mutants"].append({"node": mutant.attrib["intracellular_name"], "value": mutant.text})

                        cell_def_tab.param_d[cell_def_name]["intracellular"]["parameters"] = []
                        uep_intracellular_parameters = uep_settings.find("parameters")
                        if uep_intracellular_parameters is not None:
                            for parameter in uep_intracellular_parameters:
                                cell_def_tab.param_d[cell_def_name]["intracellular"]["parameters"].append({"name": parameter.attrib["intracellular_name"], "value": parameter.text})                    

                    cell_def_tab.param_d[cell_def_name]["intracellular"]["initial_values"] = []
                    uep_intracellular_iv = uep_intracellular.find("initial_values")
                    if uep_intracellular_iv is not None:
                        for initial_value in uep_intracellular_iv:
                            cell_def_tab.param_d[cell_def_name]["intracellular"]["initial_values"].append({"node": initial_value.attrib["intracellular_name"], "value": initial_value.text})
                  
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["inputs"] = []
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["outputs"] = []
                    uep_intracellular_mappings = uep_intracellular.find("mapping")
                    if uep_intracellular_mappings is not None:
                        for mapping in uep_intracellular_mappings:
                            if mapping.tag == "input":

                                input_settings = mapping.find("settings")
                                if input_settings is not None and input_settings.find("action") is not None and input_settings.find("threshold") is not None:


                                    cell_def_tab.param_d[cell_def_name]["intracellular"]["inputs"].append({
                                        'name': mapping.attrib["physicell_name"],
                                        'node': mapping.attrib["intracellular_name"],
                                        'action': input_settings.find("action").text,
                                        'threshold': input_settings.find("threshold").text,
                                        'inact_threshold': input_settings.find("inact_threshold").text if input_settings.find("inact_threshold") is not None else input_settings.find("threshold").text,
                                        'smoothing': input_settings.find("smoothing").text if input_settings.find("smoothing") is not None else "0",
                                    })
                                

                            elif mapping.tag == "output":
                                output_settings = mapping.find("settings")
                                if output_settings is not None and output_settings.find("action") is not None and output_settings.find("value") is not None:
                                    
                                    
                                    cell_def_tab.param_d[cell_def_name]["intracellular"]["outputs"].append({
                                        'name': mapping.attrib["physicell_name"],
                                        'node': mapping.attrib["intracellular_name"],
                                        'action': output_settings.find("action").text,
                                        'value': output_settings.find("value").text,
                                        'basal_value': output_settings.find("base_value").text if output_settings.find("base_value") is not None else output_settings.find("value").text,
                                        'smoothing': output_settings.find("smoothing").text if output_settings.find("smoothing") is not None else "0",
                                    })
                                    
                    # Update widget values
                    cell_def_tab.physiboss_clear_initial_values()
                    cell_def_tab.physiboss_clear_parameters()
                    cell_def_tab.physiboss_clear_mutants()
                    cell_def_tab.physiboss_clear_node_inheritance()
                    cell_def_tab.physiboss_clear_inputs()
                    cell_def_tab.physiboss_clear_outputs()
                    
                    cell_def_tab.physiboss_update_list_signals()
                    cell_def_tab.physiboss_update_list_behaviours()
                    cell_def_tab.physiboss_update_list_nodes()
                    cell_def_tab.physiboss_update_list_parameters()

                elif uep_intracellular.attrib["type"] == "roadrunner":
                    # <intracellular type="roadrunner">
                    #     <sbml_filename>./config/demo.xml</sbml_filename>
                    #     <intracellular_dt>0.01</intracellular_dt>
                    #     <map PC_substrate="oxygen" sbml_species="Oxygen"/>
                    #     <map PC_substrate="NADH" sbml_species="NADH"/>
                    #     <map PC_phenotype="da" sbml_species="apoptosis_rate"/>
                    #     <map PC_phenotype="mms" sbml_species="migration_speed"/>
                    #     <map PC_phenotype="ssr_lactate" sbml_species="Lac_Secretion_Rate"/>
                    #     <map PC_phenotype="ctr_0_0" sbml_species="Transition_Rate"/>
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["type"] = "roadrunner" 

                    cell_def_tab.param_d[cell_def_name]["intracellular"]["sbml_filename"] = uep_intracellular.find("sbml_filename").text if uep_intracellular.find("sbml_filename") is not None else None
                    cell_def_tab.param_d[cell_def_name]["intracellular"]["intracellular_dt"] = uep_intracellular.find("intracellular_dt").text if uep_intracellular.find("intracellular_dt") is not None else None

                    cell_def_tab.param_d[cell_def_name]["intracellular"]["sbml_maps"] = []
                    for mymap in uep_intracellular.findall('map'):
                        # save triplets 
                        if 'PC_substrate' in mymap.attrib.keys():
                            cell_def_tab.param_d[cell_def_name]["intracellular"]["sbml_maps"].append(['PC_substrate',mymap.attrib['PC_substrate'], mymap.attrib['sbml_species'] ])
                        elif 'PC_phenotype' in mymap.attrib.keys():
                            cell_def_tab.param_d[cell_def_name]["intracellular"]["sbml_maps"].append(['PC_phenotype',mymap.attrib['PC_phenotype'], mymap.attrib['sbml_species'] ])
                        elif 'PC_custom_data' in mymap.attrib.keys():
                            cell_def_tab.param_d[cell_def_name]["intracellular"]["sbml_maps"].append(['PC_custom_data',mymap.attrib['PC_custom_data'], mymap.attrib['sbml_species'] ])

                    print("\n--> ",cell_def_tab.param_d[cell_def_name]["intracellular"]["sbml_maps"])

                    # msg = f"WARNING: a roadrunner intracellular model was detected, but it is not currently possible to modify its parameters from the Studio."
                    # print(msg)
                    # msgBox = QMessageBox()
                    # # msgBox.setTextFormat(Qt.RichText)
                    # msgBox.setText(msg)
                    # msgBox.setStandardButtons(QMessageBox.Ok)
                    # returnValue = msgBox.exec()
            

            logging.debug(f'------ done parsing intracellular:')

            # # ---------  custom data 
            logging.debug(f'\n===== populate_tree():  custom data')

            uep_custom_data = cell_def_tab.xml_root.find(f"{cell_definition_path}//custom_data")
            logging.debug(f'uep_custom_data= {uep_custom_data}')

            jdx = 0
            # rwh/TODO: if we have more vars than we initially created rows for, we'll need
            # to call 'append_more_cb' for the excess.
            cell_def_tab.custom_var_count = 0
            cell_def_tab.param_d[cell_def_name]['custom_data'] = {}
            if uep_custom_data:
                logging.debug(f'--------------- populate_tree: (empty)custom_data = {cell_def_tab.param_d[cell_def_name]["custom_data"]}')
                for var in uep_custom_data:
                    val = var.text
                    if var.tag not in cell_def_tab.master_custom_var_d.keys():
                        cell_def_tab.master_custom_var_d[var.tag] = [cell_def_tab.custom_var_count, '', '']  # [row#, units, desc]

                    conserved_flag = False
                    logging.debug(f'var.attrib.keys() = {var.attrib.keys()}')
                    if 'conserved' in var.attrib.keys() and var.attrib['conserved'].lower() == 'true':
                        logging.debug(f'-------- conserved is true for {var}')
                        conserved_flag = True

                    if 'units' in var.attrib.keys():
                        units_str = var.attrib['units']
                        # for multiple cell types, use longest "units" string
                        if len(units_str) > len(cell_def_tab.master_custom_var_d[var.tag][1]):
                            cell_def_tab.master_custom_var_d[var.tag][1] = units_str  # hack: hard-coded index

                    if 'description' in var.attrib.keys():
                        desc_str = var.attrib['description']
                        # for multiple cell types, use longest "description" string
                        if len(desc_str) > len(cell_def_tab.master_custom_var_d[var.tag][2]):
                            cell_def_tab.master_custom_var_d[var.tag][2] = desc_str  # hack: hard-coded index

                    cell_def_tab.param_d[cell_def_name]['custom_data'][var.tag] = [val, conserved_flag]
                    logging.debug(f'populate: cell_def_name= {cell_def_name} --> custom_data: {cell_def_tab.param_d[cell_def_name]["custom_data"]}')

                    cell_def_tab.custom_var_count += 1
                
            cell_def_tab.param_d[cell_def_name]["par_dists"] = {}
            uep_par_dists = cell_def_tab.xml_root.find(f"{cell_definition_path}//initial_parameter_distributions")
            if uep_par_dists:
                cell_def_tab.param_d[cell_def_name]["par_dists_disabled"] = uep_par_dists.attrib["enabled"].lower() != "true"
                for par_dist in uep_par_dists:
                    # get behavior element of par_dist
                    enabled = par_dist.attrib["enabled"].lower() == "true"
                    dist_type = par_dist.attrib["type"]
                    dist_type = dist_type.replace(" ", "").lower()
                    if dist_type == "uniform":
                        dist_type = "Uniform"
                    elif dist_type == "loguniform":
                        dist_type = "Log Uniform"
                    elif dist_type == "normal":
                        dist_type = "Normal"
                    elif dist_type == "lognormal":
                        dist_type = "Log Normal"
                    elif dist_type == "log10normal":
                        dist_type = "Log10 Normal"

                    enforce_base = par_dist.attrib["check_base"].lower() == "true"
                    behavior_uep = par_dist.find('behavior')
                    if behavior_uep is not None:
                        behavior = behavior_uep.text
                    else:
                        continue
                    
                    cell_def_tab.param_d[cell_def_name]["par_dists"][behavior] = {}
                    cell_def_tab.param_d[cell_def_name]["par_dists"][behavior]["enabled"] = enabled
                    cell_def_tab.param_d[cell_def_name]["par_dists"][behavior]["distribution"] = dist_type
                    cell_def_tab.param_d[cell_def_name]["par_dists"][behavior]["enforce_base"] = enforce_base
                    cell_def_tab.param_d[cell_def_name]["par_dists"][behavior]["parameters"] = {}

                    for tag in par_dist:
                        if tag.tag == "behavior":
                            continue
                        cell_def_tab.param_d[cell_def_name]["par_dists"][behavior]["parameters"][tag.tag] = tag.text
            else:
                cell_def_tab.param_d[cell_def_name]["par_dists_disabled"] = True

    print("populate_tree_cell_defs.py:  Setting 0th cell")
    cell_def_tab.current_cell_def = cell_def_0th
    cell_def_tab.tree.setCurrentItem(cell_def_tab.tree.topLevelItem(0))  # select the top (0th) item
    cell_def_tab.tree_item_clicked_cb(cell_def_tab.tree.topLevelItem(0), 0)  # and have its params shown
    print("populate_tree_cell_defs.py:  Set 0th cell")


    #----------------------------------
    # at the end of <cell_definitions>
    uep_cell_rules = cell_def_tab.xml_root.find(".//cell_definitions//cell_rules")
    if uep_cell_rules:
        rules_folder = uep_cell_rules.find(".//folder").text 
        rules_file = uep_cell_rules.find(".//filename").text 
        logging.debug(f'------- populate_tree_cell_defs.py: setting rules.csv folder = {rules_folder}')
        logging.debug(f'------- populate_tree_cell_defs.py: setting rules.csv file = {rules_file}')

    # print("\n\n=======================  leaving cell_def populate_tree  ======================= ")