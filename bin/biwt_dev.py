import os
def biwt_dev_mode(biwt):

    #file_name = "/Users/marwanaji/PhysiCell-Studio.git/visium_adata.h5ad"
    file_name = "/Users/marwanaji/PhysiCell-Studio.git/visium_adata_with_probabilities.h5ad"


    file_name = os.path.expanduser(file_name)
    print(f"Importing {file_name}")
    biwt.column_line_edit.setText("mle_cell_type")
    biwt.import_file(file_name)

    window_to_stop_on = "BioinformaticsWalkthroughWindow_SpotDeconvolutionQuery"
    while biwt.window.__class__.__name__ != window_to_stop_on:
            print(f"Current window: {str(type(biwt.window))}")
            try: 
                if biwt.window.__class__.__name__ == "BioinformaticsWalkthroughWindow_PositionsWindow":
                    biwt.window.biwt_plot_window.plot_cell_pos()
                biwt.window.process_window()
            except Exception as e:
                print(f"Error reaching {window_to_stop_on}: {e}")
                break