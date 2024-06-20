import os
def biwt_dev_mode(biwt):
    # file_name = "./data/visium_adata.h5ad"
    # file_name = "./data/Zhuang-ABCA-1-1.064_raw_wClusterAnnots.h5ad"
    # file_name "./data/pbmc3k_clustered.h5ad"
    # file_name = "./data/abc/metadata/Zhuang-ABCA-1/20231215/views/cell_metadata_with_cluster_annotation.csv"
    # file_name = "./data/cells.csv"
    # file_name = "/Users/danielbergman/seq-to-ic-test/data_all/inputdata_download.Rds"
    file_name = "/Users/danielbergman/pdac-ecm/image_data/j1568sobj_2.rds"
    if "Zhuang" in file_name:
        biwt.column_line_edit.setText("subclass")
    elif file_name.lower().endswith(".rds"):
        biwt.column_line_edit.setText("celltype")
    else:
        biwt.column_line_edit.setText("cluster")
    biwt.import_file(file_name)
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