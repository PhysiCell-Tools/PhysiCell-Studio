# Utility bash script to move PhysiCell sample project executables for the Studio
# replace this path with wherever you have your PhysiCell pgms
PGM_PATH=/Users/heiland/dev/PhysiCell_v1.10
echo $PGM_PATH
mv $PGM_PATH/biorobots .
mv $PGM_PATH/cancer_biorobots .
mv $PGM_PATH/cancer_immune_3D .
mv $PGM_PATH/celltypes3 .
mv $PGM_PATH/heterogeneity .
mv $PGM_PATH/interaction_demo .
mv $PGM_PATH/pred_prey .
mv $PGM_PATH/project .
mv $PGM_PATH/virus-sample .
mv $PGM_PATH/worm .