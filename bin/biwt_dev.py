import os
def biwt_dev_mode(biwt):
    # file_name = "./data/visium_adata.h5ad"
    # file_name = "./data/Zhuang-ABCA-1-1.064_raw_wClusterAnnots.h5ad"
    # file_name "./data/pbmc3k_clustered.h5ad"
    # file_name = "./data/abc/metadata/Zhuang-ABCA-1/20231215/views/cell_metadata_with_cluster_annotation.csv"
    # file_name = "./data/cells.csv"
    # file_name = "/Users/danielbergman/seq-to-ic-test/data_all/inputdata_download.Rds"
    # file_name = "/Users/danielbergman/pdac-ecm/image_data/j1568sobj_2.rds"
    file_name = "./config/cell_000.csv"
    file_name = os.path.expanduser(file_name)
    print(f"Importing {file_name}")
    biwt.column_line_edit.setText("CCq25")
    biwt.import_file(file_name)
    window_to_stop_on = "BioinformaticsWalkthroughWindow_PositionsWindow"
    while biwt.window.__class__.__name__ != window_to_stop_on:
        print(f"Current window: {str(type(biwt.window))}")
        try: 
            if biwt.window.__class__.__name__ == "BioinformaticsWalkthroughWindow_PositionsWindow":
                biwt.window.biwt_plot_window.plot_cell_pos()
            biwt.window.process_window()
        except Exception as e:
            print(f"Error reaching {window_to_stop_on}: {e}")
            break