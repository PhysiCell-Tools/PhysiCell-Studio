import os
def biwt_dev_mode(biwt):
    BIWT_SPATIAL_DEV = os.getenv('BIWT_SPATIAL_DEV', 'False')
    BIWT_SPATIAL_DEV = BIWT_SPATIAL_DEV=='True'
    if BIWT_SPATIAL_DEV:
        # file_name = "./data/visium_adata.h5ad"
        # file_name = "./data/Zhuang-ABCA-1-1.064_raw_wClusterAnnots.h5ad"
        file_name = "./data/abc/metadata/Zhuang-ABCA-1/20231215/views/cell_metadata_with_cluster_annotation.csv"
        if "Zhuang" in file_name:
            biwt.column_line_edit.setText("subclass")
        else:
            biwt.column_line_edit.setText("cluster")
        biwt.import_file(file_name)
        # biwt.continue_from_import()
        # biwt.window.process_window() # process spatial y/n window
        # biwt.window.process_window() # process edit window
        # biwt.window.process_window() # process rename window
        # biwt.continue_from_spatial_query()
        # biwt.continue_from_edit()
        # biwt.window.process_window() # process rename window
        # biwt.set_cell_positions()
        # biwt.import_file("./data/visium_adata.h5ad")
        # biwt.continue_from_import()
        # biwt.continue_from_spatial_query()
        # biwt.continue_from_edit()
        # biwt.window.process_window() # process rename window
        # biwt.set_cell_positions()
    else:
        biwt.import_file("./data/pbmc3k_clustered.h5ad")
        biwt.continue_from_edit()
        biwt.window.process_window() # process rename window
        biwt.window.process_window() # process cell count window
        # biwt.continue_from_rename()
        # biwt.set_cell_positions()