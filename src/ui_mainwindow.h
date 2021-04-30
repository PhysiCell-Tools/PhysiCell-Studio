/********************************************************************************
** Form generated from reading UI file 'mainwindow.ui'
**
** Created by: Qt User Interface Compiler version 5.9.7
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MAINWINDOW_H
#define UI_MAINWINDOW_H

#include <QtCore/QVariant>
#include <QtWidgets/QAction>
#include <QtWidgets/QApplication>
#include <QtWidgets/QButtonGroup>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QFrame>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QHeaderView>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QMenu>
#include <QtWidgets/QMenuBar>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QScrollArea>
#include <QtWidgets/QStackedWidget>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QTabWidget>
#include <QtWidgets/QToolButton>
#include <QtWidgets/QTreeWidget>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_MainWindow
{
public:
    QAction *actionNew_Substrate;
    QAction *actionLoad;
    QAction *actionSave;
    QAction *actionExport_to_XML;
    QAction *actionLink;
    QAction *actionCell_Definitions;
    QAction *actionXML_Out;
    QAction *action2D;
    QAction *action3D;
    QWidget *centralwidget;
    QTreeWidget *outline;
    QStackedWidget *pages_widget;
    QWidget *microenviornment_page;
    QScrollArea *scroll_area;
    QWidget *scroll_area_widget_contents;
    QLabel *dirichletBoundaryLabel;
    QLabel *initialConditionLabel;
    QLabel *decayRateLabel;
    QLabel *diffusionCoefficientLabel;
    QCheckBox *dirichletBoundaryCheckBox;
    QLineEdit *diffusionCoefficient;
    QLineEdit *decayRate;
    QLineEdit *initialCondition;
    QLineEdit *dirchletBoundary;
    QLabel *advancedBoundaryLabel;
    QLabel *xMaximumLabel;
    QLabel *xMinimumLabel;
    QLabel *yMaximumLabel;
    QLabel *yMinimumLabel;
    QLineEdit *xMaximum;
    QLineEdit *xMinimum;
    QLineEdit *yMaximum;
    QLineEdit *yMinimum;
    QCheckBox *xMaximumCheckBox;
    QCheckBox *xMinimumCheckBox;
    QCheckBox *yMaximumCheckBox;
    QCheckBox *yMinimumCheckBox;
    QLabel *diffusionCoefficientUnits;
    QLabel *decayRateUnits;
    QLineEdit *Name;
    QLabel *nameLabel;
    QPushButton *New;
    QPushButton *Clone;
    QPushButton *Remove;
    QWidget *cell_definitions_page;
    QTabWidget *cell_tab_widget;
    QWidget *cycle_tab;
    QWidget *layoutWidget_36;
    QHBoxLayout *CYCLENameLayout;
    QLabel *CYCLEnameLabel;
    QLineEdit *CYCLEname;
    QTabWidget *cycle_phase_tab_widget;
    QWidget *cycle_phase_duration_tab;
    QWidget *gridLayoutWidget;
    QGridLayout *CYCLEPhaseDurationLayout;
    QWidget *cycle_phase_transition_tab;
    QWidget *gridLayoutWidget_2;
    QGridLayout *CYCLEPhaseTransitionLayout;
    QComboBox *CYCLEmodel;
    QWidget *death_tab;
    QScrollArea *DEATHscrollArea;
    QWidget *scrollAreaWidgetContents;
    QVBoxLayout *verticalLayout;
    QFrame *DEATHAframe;
    QWidget *layoutWidget_48;
    QHBoxLayout *DEATHACalcificationLayout;
    QLabel *DEATHAcalcificationRateLabel;
    QLineEdit *DEATHAcalcificationRate;
    QToolButton *DEATHAcalcificationRateUnits;
    QWidget *layoutWidget_42;
    QHBoxLayout *DEATHARelativeRuptureVolumeLayout;
    QLabel *DEATHArelativeRuptureVolumeLabel;
    QLineEdit *DEATHArelativeRuptureVolume;
    QWidget *layoutWidget_43;
    QHBoxLayout *DEATHADeathRateLayout;
    QLabel *DEATHAdeathRateLabel;
    QLineEdit *DEATHAdeathRateField;
    QToolButton *DEATHAdeathRateUnits;
    QTabWidget *deathA_phase_tab_widget;
    QWidget *deathA_phase_duration_tab;
    QGridLayout *gridLayout;
    QLineEdit *DEATHAphase0Duration;
    QLabel *DEATHAphase0DurationLabel;
    QCheckBox *DEATHAphase0DurationCheckBox;
    QLabel *DEATHAphase0DurationUnits;
    QWidget *deathA_phase_transition_tab;
    QGridLayout *gridLayout_2;
    QLabel *DEATHAphase0TransitionLabel;
    QLineEdit *DEATHAphase0Transition;
    QCheckBox *DEATHAphase0TransitionCheckBox;
    QLabel *DEATHAphase0TransitionUnits;
    QWidget *layoutWidget_44;
    QHBoxLayout *DEATHAUnlysedFluidChangeRateLayout;
    QLabel *DEATHAunlysedFluidChangeRateLabel;
    QLineEdit *DEATHAunlysedFluidChangeRate;
    QToolButton *DEATHAunlysedFluidChangeRateUnits;
    QWidget *layoutWidget_47;
    QHBoxLayout *DEATHANuclearBiomassChangeRateLayout;
    QLabel *DEATHAnuclearBiomassChangeRateLabel;
    QLineEdit *DEATHAnuclearBiomassChangeRate;
    QToolButton *DEATHAnuclearBiomassChangeRateUnits;
    QWidget *layoutWidget_45;
    QHBoxLayout *DEATHALysedFluidChangeRateLayout;
    QLabel *DEATHAlysedFluidChangeRateLabel;
    QLineEdit *DEATHAlysedFluidChangeRate;
    QToolButton *DEATHAlysedFluidChangeRateUnits;
    QLabel *DEATHapoptosisLabel;
    QWidget *layoutWidget_46;
    QHBoxLayout *DEATHACytoplasmicBiomassChangeRateLayout;
    QLabel *DEATHAcytoplasmicBiomassChangeRateLabel;
    QLineEdit *DEATHAcytoplasmicBiomassChangeRate;
    QToolButton *DEATHAcytoplasmicBiomassChangeRateUnits;
    QWidget *layoutWidget_71;
    QHBoxLayout *DEATHANameLayout;
    QLabel *DEATHAnameLabel;
    QLineEdit *DEATHAname;
    QFrame *DEATHNframe;
    QTabWidget *deathN_phase_tab_widget;
    QWidget *deathN_phase_duration_tab;
    QGridLayout *gridLayout_3;
    QLabel *DEATHNphase0DurationUnits;
    QLabel *DEATHNphase0DurationLabel;
    QLineEdit *DEATHNphase0Duration;
    QCheckBox *DEATHNphase0DurationCheckBox;
    QLabel *DEATHNphase1DurationLabel;
    QLineEdit *DEATHNphase1Duration;
    QCheckBox *DEATHNphase1DurationCheckBox;
    QLabel *DEATHNphase1DurationUnits;
    QWidget *deathN_phase_transition_tab;
    QGridLayout *gridLayout_4;
    QLabel *DEATHNphase0TransitionUnits;
    QLineEdit *DEATHNphase0Transition;
    QCheckBox *DEATHNphase0TransitionCheckBox;
    QLabel *DEATHNphase0TransitionLabel;
    QLabel *DEATHNphase1TransitionLabel;
    QLineEdit *DEATHNphase1Transition;
    QCheckBox *DEATHNphase1TransitionCheckBox;
    QLabel *DEATHNphase1TransitionUnits;
    QWidget *layoutWidget_54;
    QHBoxLayout *DEATHNLysedFluidChangeRateLayout;
    QLabel *DEATHNlysedFluidChangeRateLabel;
    QLineEdit *DEATHNlysedFluidChangeRate;
    QToolButton *DEATHNlysedFluidChangeRateUnits;
    QWidget *layoutWidget_52;
    QHBoxLayout *DEATHNUnlysedFluidChangeRateLayout;
    QLabel *DEATHNunlysedFluidChangeRateLabel;
    QLineEdit *DEATHNunlysedFluidChangeRate;
    QToolButton *DEATHNunlysedFluidChangeRateUnits;
    QWidget *layoutWidget_50;
    QHBoxLayout *DEATHNDeathRateLayout;
    QLabel *DEATHNdeathRateLabel;
    QLineEdit *DEATHNdeathRateField;
    QToolButton *DEATHNdeathRateUnits;
    QWidget *layoutWidget_58;
    QHBoxLayout *DEATHNCytoplasmicBiomassChangeRateLayout;
    QLabel *DEATHNcytoplasmicBiomassChangeRateLabel;
    QLineEdit *DEATHNcytoplasmicBiomassChangeRate;
    QToolButton *DEATHNcytoplasmicBiomassChangeRateUnits;
    QWidget *layoutWidget_49;
    QHBoxLayout *DEATHNRelativeRuptureVolumeLayout;
    QLabel *DEATHNrelativeRuptureVolumeLabel;
    QLineEdit *DEATHNrelativeRuptureVolume;
    QWidget *layoutWidget_72;
    QHBoxLayout *DEATHNNameLayout;
    QLabel *DEATHNnameLabel;
    QLineEdit *DEATHNname;
    QWidget *layoutWidget_56;
    QHBoxLayout *DEATHNCalcificationLayout;
    QLabel *DEATHNcalcificationRateLabel;
    QLineEdit *DEATHNcalcificationRate;
    QToolButton *DEATHNcalcificationRateUnits;
    QLabel *DEATHnecrosisLabel;
    QWidget *layoutWidget_53;
    QHBoxLayout *DEATHNNuclearBiomassChangeRateLayout;
    QLabel *DEATHNnuclearBiomassChangeRateLabel;
    QLineEdit *DEATHNnuclearBiomassChangeRate;
    QToolButton *DEATHNnuclearBiomassChangeRateUnits;
    QWidget *volume_tab;
    QWidget *layoutWidget_51;
    QHBoxLayout *VOLUMEFluidFractionLayout;
    QLabel *VOLUMEfluidFractionLabel;
    QLineEdit *VOLUMEfluidFraction;
    QWidget *layoutWidget_55;
    QHBoxLayout *VOLUMECalcifiedFractionLayout;
    QLabel *VOLUMEcalcifiedFractionLabel;
    QLineEdit *VOLUMEcalcifiedFraction;
    QWidget *layoutWidget_57;
    QHBoxLayout *VOLUMERelativeRuptureVolumeLayout;
    QLabel *VOLUMErelativeRuptureVolumeLabel;
    QLineEdit *VOLUMErelativeRuptureVolume;
    QWidget *layoutWidget;
    QHBoxLayout *VOLUMETotalVolumeLayout;
    QLabel *VOLUMEtotalVolumeLabel;
    QLineEdit *VOLUMEtotalVolume;
    QToolButton *VOLUMEtotalVolumeUnits;
    QWidget *layoutWidget1;
    QHBoxLayout *VOLUMENuclearVolumeLayout;
    QLabel *VOLUMEnuclearVolumeLabel;
    QLineEdit *VOLUMEnuclearVolume;
    QToolButton *VOLUMEnuclearVolumeUnits;
    QWidget *layoutWidget2;
    QHBoxLayout *VOLUMECalcificationRateLayout;
    QLabel *VOLUMEcalcificationRateLabel;
    QLineEdit *VOLUMEcalcificationRate;
    QToolButton *VOLUMEcalcificationRateUnits;
    QWidget *layoutWidget3;
    QHBoxLayout *VOLUMEFluidChangeRateLayout;
    QLabel *VOLUMEfluidChangeRateLabel;
    QLineEdit *VOLUMEfluidChangeRate;
    QToolButton *VOLUMEfluidChangeRateUnits;
    QWidget *layoutWidget4;
    QHBoxLayout *VOLUMECytoplasmicBiomassChangeRateLayout;
    QLabel *VOLUMEcytoplasmicBiomassChangeRateLabel;
    QLineEdit *VOLUMEcytoplasmicBiomassChangeRate;
    QToolButton *VOLUMEcytoplasmicBiomassChangeRateUnits;
    QWidget *layoutWidget5;
    QHBoxLayout *VOLUMENuclearBiomassChangeRateLayout;
    QLabel *VOLUMEnuclearBiomassChangeRateLabel;
    QLineEdit *VOLUMEnuclearBiomassChangeRate;
    QToolButton *VOLUMEnuclearBiomassChangeRateUnits;
    QWidget *mechanics_tab;
    QWidget *layoutWidget_60;
    QHBoxLayout *MECHANICSRelativeMaximumAdhesionStrengthLayout;
    QLabel *MECHANICSrelativeMaximumAdhesionStrengthLabel;
    QLineEdit *MECHANICSrelativeMaximumAdhesionStrength;
    QTabWidget *mechanics_phase_tab_widget;
    QWidget *mechanics_relative_equilibrium_distance_tab;
    QWidget *layoutWidget6;
    QHBoxLayout *MECHANICSRelativeEquilibriumDistanceLayout;
    QLabel *MECHANICSrelativeEquilibriumDistanceLabel;
    QLineEdit *MECHANICSrelativeEquilibriumDistance;
    QWidget *mechanics_absolute_equilibrium_distance_tab;
    QWidget *layoutWidget7;
    QHBoxLayout *MECHANICSAbsoluteEquilibriumDistanceLayout;
    QLabel *MECHANICSabsoluteEquilibriumDistanceLabel;
    QLineEdit *MECHANICSabsoluteEquilibriumDistance;
    QToolButton *MECHANICSabsoluteEquilibriumDistanceUnits;
    QWidget *layoutWidget8;
    QHBoxLayout *MECHANICSCellAdhesionStrengthLayout;
    QLabel *MECHANICScellAdhesionStrengthLabel;
    QLineEdit *MECHANICScellAdhesionStrength;
    QToolButton *MECHANICScellAdhesionStrengthUnits;
    QWidget *layoutWidget9;
    QHBoxLayout *MECHANICSCellRepulsionStrengthLayout;
    QLabel *MECHANICScellRepulsionStrengthLabel;
    QLineEdit *MECHANICScellRepulsionStrength;
    QToolButton *MECHANICScellRepulsionStrengtUnits;
    QWidget *motility_tab;
    QCheckBox *MOTILITYenableCheckBox;
    QCheckBox *MOTILITYuse2dCheckBox;
    QWidget *layoutWidget10;
    QHBoxLayout *MOTILITYSpeedLayout;
    QLabel *MOTILITYspeedLabel;
    QLineEdit *MOTILITYspeed;
    QToolButton *MOTILITYspeedUnits;
    QWidget *layoutWidget11;
    QHBoxLayout *MOTILITYPersistenceTimeLayout;
    QLabel *MOTILITYpersistenceTimeLabel;
    QLineEdit *MOTILITYpersistenceTime;
    QToolButton *MOTILITYpersistenceTimeUnits;
    QWidget *layoutWidget12;
    QHBoxLayout *MOTILITYMitigationBiasLayout;
    QLabel *MOTILITYmitigationBiasLabel;
    QLineEdit *MOTILITYmitigationBias;
    QWidget *layoutWidget13;
    QHBoxLayout *MOTILITYDirectionLayout;
    QLabel *MOTILITYdirectionLabel;
    QComboBox *MOTILITYdirectionComboBox;
    QLabel *MOTILITYchemotaxisLabel;
    QCheckBox *MOTILITYenableChemotaxisCheckBox;
    QWidget *widget;
    QHBoxLayout *MOTILITYSubstrateLayout;
    QLabel *MOTILITYsubstrateLabel;
    QComboBox *MOTILITYchemotaxisComboBox;
    QWidget *secretion_tab;
    QWidget *secretion_substrate_0;
    QLabel *SECRETIONsubstrateNameLabel0;
    QWidget *layoutWidget14;
    QHBoxLayout *SECRETIONSecretionRateLayout;
    QLabel *SECRETIONsecretionRateLabel;
    QLineEdit *SECRETIONsecretionRate;
    QToolButton *SECRETIONsecretionRateUnits;
    QWidget *layoutWidget15;
    QHBoxLayout *SECRETIONSecretionTargetLayout;
    QLabel *SECRETIONsecretionTargetLabel;
    QLineEdit *SECRETIONsecretionTarget;
    QToolButton *SECRETIONsecretionTargetUnits;
    QWidget *layoutWidget16;
    QHBoxLayout *SECRETIONUptakeRateLayout;
    QLabel *SECRETIONuptakeRateLabel;
    QLineEdit *SECRETIONuptakeRate;
    QToolButton *SECRETIONUptakeRateUnits;
    QWidget *layoutWidget17;
    QHBoxLayout *SECRETIONNetExportRateLayout;
    QLabel *SECRETIONnetExportRateLabel;
    QLineEdit *SECRETIONnetExportRate;
    QToolButton *SECRETIONnetExportRateUnits;
    QLabel *cellNameLabel;
    QPushButton *newCellButton;
    QPushButton *cloneCellButton;
    QPushButton *removeCellButton;
    QLineEdit *cellName;
    QMenuBar *menubar;
    QMenu *menuFile;
    QMenu *menuNew;
    QMenu *menuEdit;
    QMenu *menuView;
    QStatusBar *statusbar;

    void setupUi(QMainWindow *MainWindow)
    {
        if (MainWindow->objectName().isEmpty())
            MainWindow->setObjectName(QStringLiteral("MainWindow"));
        MainWindow->setWindowModality(Qt::WindowModal);
        MainWindow->resize(919, 628);
        actionNew_Substrate = new QAction(MainWindow);
        actionNew_Substrate->setObjectName(QStringLiteral("actionNew_Substrate"));
        actionLoad = new QAction(MainWindow);
        actionLoad->setObjectName(QStringLiteral("actionLoad"));
        actionSave = new QAction(MainWindow);
        actionSave->setObjectName(QStringLiteral("actionSave"));
        actionSave->setCheckable(false);
        actionExport_to_XML = new QAction(MainWindow);
        actionExport_to_XML->setObjectName(QStringLiteral("actionExport_to_XML"));
        actionLink = new QAction(MainWindow);
        actionLink->setObjectName(QStringLiteral("actionLink"));
        actionCell_Definitions = new QAction(MainWindow);
        actionCell_Definitions->setObjectName(QStringLiteral("actionCell_Definitions"));
        actionXML_Out = new QAction(MainWindow);
        actionXML_Out->setObjectName(QStringLiteral("actionXML_Out"));
        action2D = new QAction(MainWindow);
        action2D->setObjectName(QStringLiteral("action2D"));
        action3D = new QAction(MainWindow);
        action3D->setObjectName(QStringLiteral("action3D"));
        centralwidget = new QWidget(MainWindow);
        centralwidget->setObjectName(QStringLiteral("centralwidget"));
        outline = new QTreeWidget(centralwidget);
        QTreeWidgetItem *__qtreewidgetitem = new QTreeWidgetItem();
        __qtreewidgetitem->setTextAlignment(0, Qt::AlignLeading|Qt::AlignVCenter);
        outline->setHeaderItem(__qtreewidgetitem);
        new QTreeWidgetItem(outline);
        new QTreeWidgetItem(outline);
        outline->setObjectName(QStringLiteral("outline"));
        outline->setGeometry(QRect(0, 0, 181, 581));
        outline->setAutoFillBackground(true);
        outline->setColumnCount(1);
        pages_widget = new QStackedWidget(centralwidget);
        pages_widget->setObjectName(QStringLiteral("pages_widget"));
        pages_widget->setGeometry(QRect(210, 10, 691, 531));
        microenviornment_page = new QWidget();
        microenviornment_page->setObjectName(QStringLiteral("microenviornment_page"));
        scroll_area = new QScrollArea(microenviornment_page);
        scroll_area->setObjectName(QStringLiteral("scroll_area"));
        scroll_area->setGeometry(QRect(130, 120, 451, 401));
        scroll_area->setWidgetResizable(true);
        scroll_area_widget_contents = new QWidget();
        scroll_area_widget_contents->setObjectName(QStringLiteral("scroll_area_widget_contents"));
        scroll_area_widget_contents->setGeometry(QRect(0, 0, 449, 399));
        dirichletBoundaryLabel = new QLabel(scroll_area_widget_contents);
        dirichletBoundaryLabel->setObjectName(QStringLiteral("dirichletBoundaryLabel"));
        dirichletBoundaryLabel->setGeometry(QRect(60, 150, 101, 21));
        initialConditionLabel = new QLabel(scroll_area_widget_contents);
        initialConditionLabel->setObjectName(QStringLiteral("initialConditionLabel"));
        initialConditionLabel->setGeometry(QRect(60, 110, 101, 21));
        decayRateLabel = new QLabel(scroll_area_widget_contents);
        decayRateLabel->setObjectName(QStringLiteral("decayRateLabel"));
        decayRateLabel->setGeometry(QRect(60, 70, 101, 21));
        diffusionCoefficientLabel = new QLabel(scroll_area_widget_contents);
        diffusionCoefficientLabel->setObjectName(QStringLiteral("diffusionCoefficientLabel"));
        diffusionCoefficientLabel->setGeometry(QRect(60, 30, 101, 21));
        dirichletBoundaryCheckBox = new QCheckBox(scroll_area_widget_contents);
        dirichletBoundaryCheckBox->setObjectName(QStringLiteral("dirichletBoundaryCheckBox"));
        dirichletBoundaryCheckBox->setGeometry(QRect(30, 150, 16, 16));
        dirichletBoundaryCheckBox->setChecked(false);
        diffusionCoefficient = new QLineEdit(scroll_area_widget_contents);
        diffusionCoefficient->setObjectName(QStringLiteral("diffusionCoefficient"));
        diffusionCoefficient->setGeometry(QRect(170, 30, 161, 20));
        diffusionCoefficient->setInputMethodHints(Qt::ImhDigitsOnly);
        decayRate = new QLineEdit(scroll_area_widget_contents);
        decayRate->setObjectName(QStringLiteral("decayRate"));
        decayRate->setGeometry(QRect(170, 70, 161, 20));
        initialCondition = new QLineEdit(scroll_area_widget_contents);
        initialCondition->setObjectName(QStringLiteral("initialCondition"));
        initialCondition->setGeometry(QRect(170, 110, 161, 20));
        dirchletBoundary = new QLineEdit(scroll_area_widget_contents);
        dirchletBoundary->setObjectName(QStringLiteral("dirchletBoundary"));
        dirchletBoundary->setEnabled(true);
        dirchletBoundary->setGeometry(QRect(170, 150, 161, 20));
        advancedBoundaryLabel = new QLabel(scroll_area_widget_contents);
        advancedBoundaryLabel->setObjectName(QStringLiteral("advancedBoundaryLabel"));
        advancedBoundaryLabel->setGeometry(QRect(130, 190, 111, 16));
        xMaximumLabel = new QLabel(scroll_area_widget_contents);
        xMaximumLabel->setObjectName(QStringLiteral("xMaximumLabel"));
        xMaximumLabel->setGeometry(QRect(130, 220, 71, 21));
        xMinimumLabel = new QLabel(scroll_area_widget_contents);
        xMinimumLabel->setObjectName(QStringLiteral("xMinimumLabel"));
        xMinimumLabel->setGeometry(QRect(130, 260, 71, 21));
        yMaximumLabel = new QLabel(scroll_area_widget_contents);
        yMaximumLabel->setObjectName(QStringLiteral("yMaximumLabel"));
        yMaximumLabel->setGeometry(QRect(130, 300, 71, 21));
        yMinimumLabel = new QLabel(scroll_area_widget_contents);
        yMinimumLabel->setObjectName(QStringLiteral("yMinimumLabel"));
        yMinimumLabel->setGeometry(QRect(130, 340, 71, 21));
        xMaximum = new QLineEdit(scroll_area_widget_contents);
        xMaximum->setObjectName(QStringLiteral("xMaximum"));
        xMaximum->setGeometry(QRect(200, 220, 161, 20));
        xMinimum = new QLineEdit(scroll_area_widget_contents);
        xMinimum->setObjectName(QStringLiteral("xMinimum"));
        xMinimum->setGeometry(QRect(200, 260, 161, 20));
        yMaximum = new QLineEdit(scroll_area_widget_contents);
        yMaximum->setObjectName(QStringLiteral("yMaximum"));
        yMaximum->setGeometry(QRect(200, 300, 161, 20));
        yMinimum = new QLineEdit(scroll_area_widget_contents);
        yMinimum->setObjectName(QStringLiteral("yMinimum"));
        yMinimum->setGeometry(QRect(200, 340, 161, 20));
        xMaximumCheckBox = new QCheckBox(scroll_area_widget_contents);
        xMaximumCheckBox->setObjectName(QStringLiteral("xMaximumCheckBox"));
        xMaximumCheckBox->setGeometry(QRect(100, 220, 16, 16));
        xMinimumCheckBox = new QCheckBox(scroll_area_widget_contents);
        xMinimumCheckBox->setObjectName(QStringLiteral("xMinimumCheckBox"));
        xMinimumCheckBox->setGeometry(QRect(100, 260, 16, 16));
        yMaximumCheckBox = new QCheckBox(scroll_area_widget_contents);
        yMaximumCheckBox->setObjectName(QStringLiteral("yMaximumCheckBox"));
        yMaximumCheckBox->setGeometry(QRect(100, 300, 16, 16));
        yMinimumCheckBox = new QCheckBox(scroll_area_widget_contents);
        yMinimumCheckBox->setObjectName(QStringLiteral("yMinimumCheckBox"));
        yMinimumCheckBox->setGeometry(QRect(100, 340, 16, 16));
        diffusionCoefficientUnits = new QLabel(scroll_area_widget_contents);
        diffusionCoefficientUnits->setObjectName(QStringLiteral("diffusionCoefficientUnits"));
        diffusionCoefficientUnits->setGeometry(QRect(340, 30, 71, 16));
        decayRateUnits = new QLabel(scroll_area_widget_contents);
        decayRateUnits->setObjectName(QStringLiteral("decayRateUnits"));
        decayRateUnits->setGeometry(QRect(340, 70, 47, 13));
        scroll_area->setWidget(scroll_area_widget_contents);
        Name = new QLineEdit(microenviornment_page);
        Name->setObjectName(QStringLiteral("Name"));
        Name->setGeometry(QRect(270, 70, 161, 20));
        nameLabel = new QLabel(microenviornment_page);
        nameLabel->setObjectName(QStringLiteral("nameLabel"));
        nameLabel->setGeometry(QRect(200, 70, 101, 21));
        New = new QPushButton(microenviornment_page);
        New->setObjectName(QStringLiteral("New"));
        New->setGeometry(QRect(40, 20, 91, 23));
        Clone = new QPushButton(microenviornment_page);
        Clone->setObjectName(QStringLiteral("Clone"));
        Clone->setGeometry(QRect(140, 20, 91, 23));
        Remove = new QPushButton(microenviornment_page);
        Remove->setObjectName(QStringLiteral("Remove"));
        Remove->setGeometry(QRect(470, 20, 111, 23));
        pages_widget->addWidget(microenviornment_page);
        cell_definitions_page = new QWidget();
        cell_definitions_page->setObjectName(QStringLiteral("cell_definitions_page"));
        cell_tab_widget = new QTabWidget(cell_definitions_page);
        cell_tab_widget->setObjectName(QStringLiteral("cell_tab_widget"));
        cell_tab_widget->setGeometry(QRect(10, 90, 681, 441));
        cell_tab_widget->setStyleSheet(QStringLiteral(""));
        cycle_tab = new QWidget();
        cycle_tab->setObjectName(QStringLiteral("cycle_tab"));
        QSizePolicy sizePolicy(QSizePolicy::Maximum, QSizePolicy::Preferred);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(cycle_tab->sizePolicy().hasHeightForWidth());
        cycle_tab->setSizePolicy(sizePolicy);
        cycle_tab->setMaximumSize(QSize(685, 16777215));
        cycle_tab->setStyleSheet(QStringLiteral("font: 12pt \"MS Shell Dlg 2\";"));
        layoutWidget_36 = new QWidget(cycle_tab);
        layoutWidget_36->setObjectName(QStringLiteral("layoutWidget_36"));
        layoutWidget_36->setGeometry(QRect(40, 30, 331, 32));
        CYCLENameLayout = new QHBoxLayout(layoutWidget_36);
        CYCLENameLayout->setObjectName(QStringLiteral("CYCLENameLayout"));
        CYCLENameLayout->setContentsMargins(0, 0, 0, 0);
        CYCLEnameLabel = new QLabel(layoutWidget_36);
        CYCLEnameLabel->setObjectName(QStringLiteral("CYCLEnameLabel"));
        CYCLEnameLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        CYCLENameLayout->addWidget(CYCLEnameLabel);

        CYCLEname = new QLineEdit(layoutWidget_36);
        CYCLEname->setObjectName(QStringLiteral("CYCLEname"));

        CYCLENameLayout->addWidget(CYCLEname);

        cycle_phase_tab_widget = new QTabWidget(cycle_tab);
        cycle_phase_tab_widget->setObjectName(QStringLiteral("cycle_phase_tab_widget"));
        cycle_phase_tab_widget->setGeometry(QRect(30, 80, 591, 311));
        cycle_phase_duration_tab = new QWidget();
        cycle_phase_duration_tab->setObjectName(QStringLiteral("cycle_phase_duration_tab"));
        gridLayoutWidget = new QWidget(cycle_phase_duration_tab);
        gridLayoutWidget->setObjectName(QStringLiteral("gridLayoutWidget"));
        gridLayoutWidget->setGeometry(QRect(10, 10, 561, 261));
        CYCLEPhaseDurationLayout = new QGridLayout(gridLayoutWidget);
        CYCLEPhaseDurationLayout->setObjectName(QStringLiteral("CYCLEPhaseDurationLayout"));
        CYCLEPhaseDurationLayout->setContentsMargins(0, 0, 0, 0);
        cycle_phase_tab_widget->addTab(cycle_phase_duration_tab, QString());
        cycle_phase_transition_tab = new QWidget();
        cycle_phase_transition_tab->setObjectName(QStringLiteral("cycle_phase_transition_tab"));
        gridLayoutWidget_2 = new QWidget(cycle_phase_transition_tab);
        gridLayoutWidget_2->setObjectName(QStringLiteral("gridLayoutWidget_2"));
        gridLayoutWidget_2->setGeometry(QRect(10, 10, 561, 261));
        CYCLEPhaseTransitionLayout = new QGridLayout(gridLayoutWidget_2);
        CYCLEPhaseTransitionLayout->setObjectName(QStringLiteral("CYCLEPhaseTransitionLayout"));
        CYCLEPhaseTransitionLayout->setContentsMargins(0, 0, 0, 0);
        cycle_phase_tab_widget->addTab(cycle_phase_transition_tab, QString());
        CYCLEmodel = new QComboBox(cycle_tab);
        CYCLEmodel->setObjectName(QStringLiteral("CYCLEmodel"));
        CYCLEmodel->setGeometry(QRect(390, 30, 231, 30));
        cell_tab_widget->addTab(cycle_tab, QString());
        death_tab = new QWidget();
        death_tab->setObjectName(QStringLiteral("death_tab"));
        sizePolicy.setHeightForWidth(death_tab->sizePolicy().hasHeightForWidth());
        death_tab->setSizePolicy(sizePolicy);
        DEATHscrollArea = new QScrollArea(death_tab);
        DEATHscrollArea->setObjectName(QStringLiteral("DEATHscrollArea"));
        DEATHscrollArea->setGeometry(QRect(0, 0, 671, 411));
        QSizePolicy sizePolicy1(QSizePolicy::Expanding, QSizePolicy::Preferred);
        sizePolicy1.setHorizontalStretch(0);
        sizePolicy1.setVerticalStretch(0);
        sizePolicy1.setHeightForWidth(DEATHscrollArea->sizePolicy().hasHeightForWidth());
        DEATHscrollArea->setSizePolicy(sizePolicy1);
        DEATHscrollArea->setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
        DEATHscrollArea->setSizeAdjustPolicy(QAbstractScrollArea::AdjustIgnored);
        DEATHscrollArea->setWidgetResizable(true);
        scrollAreaWidgetContents = new QWidget();
        scrollAreaWidgetContents->setObjectName(QStringLiteral("scrollAreaWidgetContents"));
        scrollAreaWidgetContents->setGeometry(QRect(0, 0, 652, 569));
        verticalLayout = new QVBoxLayout(scrollAreaWidgetContents);
        verticalLayout->setObjectName(QStringLiteral("verticalLayout"));
        DEATHAframe = new QFrame(scrollAreaWidgetContents);
        DEATHAframe->setObjectName(QStringLiteral("DEATHAframe"));
        DEATHAframe->setMinimumSize(QSize(615, 273));
        DEATHAframe->setFrameShape(QFrame::StyledPanel);
        DEATHAframe->setFrameShadow(QFrame::Raised);
        layoutWidget_48 = new QWidget(DEATHAframe);
        layoutWidget_48->setObjectName(QStringLiteral("layoutWidget_48"));
        layoutWidget_48->setGeometry(QRect(310, 190, 291, 24));
        DEATHACalcificationLayout = new QHBoxLayout(layoutWidget_48);
        DEATHACalcificationLayout->setObjectName(QStringLiteral("DEATHACalcificationLayout"));
        DEATHACalcificationLayout->setContentsMargins(0, 0, 0, 0);
        DEATHAcalcificationRateLabel = new QLabel(layoutWidget_48);
        DEATHAcalcificationRateLabel->setObjectName(QStringLiteral("DEATHAcalcificationRateLabel"));
        DEATHAcalcificationRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHACalcificationLayout->addWidget(DEATHAcalcificationRateLabel);

        DEATHAcalcificationRate = new QLineEdit(layoutWidget_48);
        DEATHAcalcificationRate->setObjectName(QStringLiteral("DEATHAcalcificationRate"));

        DEATHACalcificationLayout->addWidget(DEATHAcalcificationRate);

        DEATHAcalcificationRateUnits = new QToolButton(layoutWidget_48);
        DEATHAcalcificationRateUnits->setObjectName(QStringLiteral("DEATHAcalcificationRateUnits"));

        DEATHACalcificationLayout->addWidget(DEATHAcalcificationRateUnits);

        layoutWidget_42 = new QWidget(DEATHAframe);
        layoutWidget_42->setObjectName(QStringLiteral("layoutWidget_42"));
        layoutWidget_42->setGeometry(QRect(309, 219, 291, 24));
        DEATHARelativeRuptureVolumeLayout = new QHBoxLayout(layoutWidget_42);
        DEATHARelativeRuptureVolumeLayout->setObjectName(QStringLiteral("DEATHARelativeRuptureVolumeLayout"));
        DEATHARelativeRuptureVolumeLayout->setContentsMargins(0, 0, 0, 0);
        DEATHArelativeRuptureVolumeLabel = new QLabel(layoutWidget_42);
        DEATHArelativeRuptureVolumeLabel->setObjectName(QStringLiteral("DEATHArelativeRuptureVolumeLabel"));
        DEATHArelativeRuptureVolumeLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHARelativeRuptureVolumeLayout->addWidget(DEATHArelativeRuptureVolumeLabel);

        DEATHArelativeRuptureVolume = new QLineEdit(layoutWidget_42);
        DEATHArelativeRuptureVolume->setObjectName(QStringLiteral("DEATHArelativeRuptureVolume"));

        DEATHARelativeRuptureVolumeLayout->addWidget(DEATHArelativeRuptureVolume);

        layoutWidget_43 = new QWidget(DEATHAframe);
        layoutWidget_43->setObjectName(QStringLiteral("layoutWidget_43"));
        layoutWidget_43->setGeometry(QRect(9, 66, 281, 24));
        DEATHADeathRateLayout = new QHBoxLayout(layoutWidget_43);
        DEATHADeathRateLayout->setObjectName(QStringLiteral("DEATHADeathRateLayout"));
        DEATHADeathRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHAdeathRateLabel = new QLabel(layoutWidget_43);
        DEATHAdeathRateLabel->setObjectName(QStringLiteral("DEATHAdeathRateLabel"));
        DEATHAdeathRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHADeathRateLayout->addWidget(DEATHAdeathRateLabel);

        DEATHAdeathRateField = new QLineEdit(layoutWidget_43);
        DEATHAdeathRateField->setObjectName(QStringLiteral("DEATHAdeathRateField"));

        DEATHADeathRateLayout->addWidget(DEATHAdeathRateField);

        DEATHAdeathRateUnits = new QToolButton(layoutWidget_43);
        DEATHAdeathRateUnits->setObjectName(QStringLiteral("DEATHAdeathRateUnits"));

        DEATHADeathRateLayout->addWidget(DEATHAdeathRateUnits);

        deathA_phase_tab_widget = new QTabWidget(DEATHAframe);
        deathA_phase_tab_widget->setObjectName(QStringLiteral("deathA_phase_tab_widget"));
        deathA_phase_tab_widget->setGeometry(QRect(7, 104, 278, 141));
        QSizePolicy sizePolicy2(QSizePolicy::Expanding, QSizePolicy::Ignored);
        sizePolicy2.setHorizontalStretch(0);
        sizePolicy2.setVerticalStretch(0);
        sizePolicy2.setHeightForWidth(deathA_phase_tab_widget->sizePolicy().hasHeightForWidth());
        deathA_phase_tab_widget->setSizePolicy(sizePolicy2);
        deathA_phase_tab_widget->setTabShape(QTabWidget::Rounded);
        deathA_phase_duration_tab = new QWidget();
        deathA_phase_duration_tab->setObjectName(QStringLiteral("deathA_phase_duration_tab"));
        gridLayout = new QGridLayout(deathA_phase_duration_tab);
        gridLayout->setObjectName(QStringLiteral("gridLayout"));
        DEATHAphase0Duration = new QLineEdit(deathA_phase_duration_tab);
        DEATHAphase0Duration->setObjectName(QStringLiteral("DEATHAphase0Duration"));

        gridLayout->addWidget(DEATHAphase0Duration, 0, 2, 1, 1);

        DEATHAphase0DurationLabel = new QLabel(deathA_phase_duration_tab);
        DEATHAphase0DurationLabel->setObjectName(QStringLiteral("DEATHAphase0DurationLabel"));

        gridLayout->addWidget(DEATHAphase0DurationLabel, 0, 0, 1, 1);

        DEATHAphase0DurationCheckBox = new QCheckBox(deathA_phase_duration_tab);
        DEATHAphase0DurationCheckBox->setObjectName(QStringLiteral("DEATHAphase0DurationCheckBox"));

        gridLayout->addWidget(DEATHAphase0DurationCheckBox, 0, 3, 1, 1);

        DEATHAphase0DurationUnits = new QLabel(deathA_phase_duration_tab);
        DEATHAphase0DurationUnits->setObjectName(QStringLiteral("DEATHAphase0DurationUnits"));

        gridLayout->addWidget(DEATHAphase0DurationUnits, 0, 4, 1, 1);

        deathA_phase_tab_widget->addTab(deathA_phase_duration_tab, QString());
        deathA_phase_transition_tab = new QWidget();
        deathA_phase_transition_tab->setObjectName(QStringLiteral("deathA_phase_transition_tab"));
        gridLayout_2 = new QGridLayout(deathA_phase_transition_tab);
        gridLayout_2->setObjectName(QStringLiteral("gridLayout_2"));
        DEATHAphase0TransitionLabel = new QLabel(deathA_phase_transition_tab);
        DEATHAphase0TransitionLabel->setObjectName(QStringLiteral("DEATHAphase0TransitionLabel"));

        gridLayout_2->addWidget(DEATHAphase0TransitionLabel, 0, 0, 1, 1);

        DEATHAphase0Transition = new QLineEdit(deathA_phase_transition_tab);
        DEATHAphase0Transition->setObjectName(QStringLiteral("DEATHAphase0Transition"));

        gridLayout_2->addWidget(DEATHAphase0Transition, 0, 1, 1, 1);

        DEATHAphase0TransitionCheckBox = new QCheckBox(deathA_phase_transition_tab);
        DEATHAphase0TransitionCheckBox->setObjectName(QStringLiteral("DEATHAphase0TransitionCheckBox"));

        gridLayout_2->addWidget(DEATHAphase0TransitionCheckBox, 0, 2, 1, 1);

        DEATHAphase0TransitionUnits = new QLabel(deathA_phase_transition_tab);
        DEATHAphase0TransitionUnits->setObjectName(QStringLiteral("DEATHAphase0TransitionUnits"));

        gridLayout_2->addWidget(DEATHAphase0TransitionUnits, 0, 3, 1, 1);

        deathA_phase_tab_widget->addTab(deathA_phase_transition_tab, QString());
        layoutWidget_44 = new QWidget(DEATHAframe);
        layoutWidget_44->setObjectName(QStringLiteral("layoutWidget_44"));
        layoutWidget_44->setGeometry(QRect(310, 67, 291, 24));
        DEATHAUnlysedFluidChangeRateLayout = new QHBoxLayout(layoutWidget_44);
        DEATHAUnlysedFluidChangeRateLayout->setObjectName(QStringLiteral("DEATHAUnlysedFluidChangeRateLayout"));
        DEATHAUnlysedFluidChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHAunlysedFluidChangeRateLabel = new QLabel(layoutWidget_44);
        DEATHAunlysedFluidChangeRateLabel->setObjectName(QStringLiteral("DEATHAunlysedFluidChangeRateLabel"));
        DEATHAunlysedFluidChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHAUnlysedFluidChangeRateLayout->addWidget(DEATHAunlysedFluidChangeRateLabel);

        DEATHAunlysedFluidChangeRate = new QLineEdit(layoutWidget_44);
        DEATHAunlysedFluidChangeRate->setObjectName(QStringLiteral("DEATHAunlysedFluidChangeRate"));

        DEATHAUnlysedFluidChangeRateLayout->addWidget(DEATHAunlysedFluidChangeRate);

        DEATHAunlysedFluidChangeRateUnits = new QToolButton(layoutWidget_44);
        DEATHAunlysedFluidChangeRateUnits->setObjectName(QStringLiteral("DEATHAunlysedFluidChangeRateUnits"));

        DEATHAUnlysedFluidChangeRateLayout->addWidget(DEATHAunlysedFluidChangeRateUnits);

        layoutWidget_47 = new QWidget(DEATHAframe);
        layoutWidget_47->setObjectName(QStringLiteral("layoutWidget_47"));
        layoutWidget_47->setGeometry(QRect(310, 159, 291, 24));
        DEATHANuclearBiomassChangeRateLayout = new QHBoxLayout(layoutWidget_47);
        DEATHANuclearBiomassChangeRateLayout->setObjectName(QStringLiteral("DEATHANuclearBiomassChangeRateLayout"));
        DEATHANuclearBiomassChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHAnuclearBiomassChangeRateLabel = new QLabel(layoutWidget_47);
        DEATHAnuclearBiomassChangeRateLabel->setObjectName(QStringLiteral("DEATHAnuclearBiomassChangeRateLabel"));
        DEATHAnuclearBiomassChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHANuclearBiomassChangeRateLayout->addWidget(DEATHAnuclearBiomassChangeRateLabel);

        DEATHAnuclearBiomassChangeRate = new QLineEdit(layoutWidget_47);
        DEATHAnuclearBiomassChangeRate->setObjectName(QStringLiteral("DEATHAnuclearBiomassChangeRate"));

        DEATHANuclearBiomassChangeRateLayout->addWidget(DEATHAnuclearBiomassChangeRate);

        DEATHAnuclearBiomassChangeRateUnits = new QToolButton(layoutWidget_47);
        DEATHAnuclearBiomassChangeRateUnits->setObjectName(QStringLiteral("DEATHAnuclearBiomassChangeRateUnits"));

        DEATHANuclearBiomassChangeRateLayout->addWidget(DEATHAnuclearBiomassChangeRateUnits);

        layoutWidget_45 = new QWidget(DEATHAframe);
        layoutWidget_45->setObjectName(QStringLiteral("layoutWidget_45"));
        layoutWidget_45->setGeometry(QRect(310, 98, 291, 24));
        DEATHALysedFluidChangeRateLayout = new QHBoxLayout(layoutWidget_45);
        DEATHALysedFluidChangeRateLayout->setObjectName(QStringLiteral("DEATHALysedFluidChangeRateLayout"));
        DEATHALysedFluidChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHAlysedFluidChangeRateLabel = new QLabel(layoutWidget_45);
        DEATHAlysedFluidChangeRateLabel->setObjectName(QStringLiteral("DEATHAlysedFluidChangeRateLabel"));
        DEATHAlysedFluidChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHALysedFluidChangeRateLayout->addWidget(DEATHAlysedFluidChangeRateLabel);

        DEATHAlysedFluidChangeRate = new QLineEdit(layoutWidget_45);
        DEATHAlysedFluidChangeRate->setObjectName(QStringLiteral("DEATHAlysedFluidChangeRate"));

        DEATHALysedFluidChangeRateLayout->addWidget(DEATHAlysedFluidChangeRate);

        DEATHAlysedFluidChangeRateUnits = new QToolButton(layoutWidget_45);
        DEATHAlysedFluidChangeRateUnits->setObjectName(QStringLiteral("DEATHAlysedFluidChangeRateUnits"));

        DEATHALysedFluidChangeRateLayout->addWidget(DEATHAlysedFluidChangeRateUnits);

        DEATHapoptosisLabel = new QLabel(DEATHAframe);
        DEATHapoptosisLabel->setObjectName(QStringLiteral("DEATHapoptosisLabel"));
        DEATHapoptosisLabel->setGeometry(QRect(347, 14, 191, 31));
        DEATHapoptosisLabel->setTextFormat(Qt::MarkdownText);
        layoutWidget_46 = new QWidget(DEATHAframe);
        layoutWidget_46->setObjectName(QStringLiteral("layoutWidget_46"));
        layoutWidget_46->setGeometry(QRect(310, 128, 291, 24));
        DEATHACytoplasmicBiomassChangeRateLayout = new QHBoxLayout(layoutWidget_46);
        DEATHACytoplasmicBiomassChangeRateLayout->setObjectName(QStringLiteral("DEATHACytoplasmicBiomassChangeRateLayout"));
        DEATHACytoplasmicBiomassChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHAcytoplasmicBiomassChangeRateLabel = new QLabel(layoutWidget_46);
        DEATHAcytoplasmicBiomassChangeRateLabel->setObjectName(QStringLiteral("DEATHAcytoplasmicBiomassChangeRateLabel"));
        DEATHAcytoplasmicBiomassChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHACytoplasmicBiomassChangeRateLayout->addWidget(DEATHAcytoplasmicBiomassChangeRateLabel);

        DEATHAcytoplasmicBiomassChangeRate = new QLineEdit(layoutWidget_46);
        DEATHAcytoplasmicBiomassChangeRate->setObjectName(QStringLiteral("DEATHAcytoplasmicBiomassChangeRate"));

        DEATHACytoplasmicBiomassChangeRateLayout->addWidget(DEATHAcytoplasmicBiomassChangeRate);

        DEATHAcytoplasmicBiomassChangeRateUnits = new QToolButton(layoutWidget_46);
        DEATHAcytoplasmicBiomassChangeRateUnits->setObjectName(QStringLiteral("DEATHAcytoplasmicBiomassChangeRateUnits"));

        DEATHACytoplasmicBiomassChangeRateLayout->addWidget(DEATHAcytoplasmicBiomassChangeRateUnits);

        layoutWidget_71 = new QWidget(DEATHAframe);
        layoutWidget_71->setObjectName(QStringLiteral("layoutWidget_71"));
        layoutWidget_71->setGeometry(QRect(10, 20, 181, 25));
        DEATHANameLayout = new QHBoxLayout(layoutWidget_71);
        DEATHANameLayout->setObjectName(QStringLiteral("DEATHANameLayout"));
        DEATHANameLayout->setContentsMargins(0, 0, 0, 0);
        DEATHAnameLabel = new QLabel(layoutWidget_71);
        DEATHAnameLabel->setObjectName(QStringLiteral("DEATHAnameLabel"));
        DEATHAnameLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHANameLayout->addWidget(DEATHAnameLabel);

        DEATHAname = new QLineEdit(layoutWidget_71);
        DEATHAname->setObjectName(QStringLiteral("DEATHAname"));

        DEATHANameLayout->addWidget(DEATHAname);


        verticalLayout->addWidget(DEATHAframe);

        DEATHNframe = new QFrame(scrollAreaWidgetContents);
        DEATHNframe->setObjectName(QStringLiteral("DEATHNframe"));
        DEATHNframe->setMinimumSize(QSize(615, 272));
        DEATHNframe->setFrameShape(QFrame::StyledPanel);
        DEATHNframe->setFrameShadow(QFrame::Raised);
        deathN_phase_tab_widget = new QTabWidget(DEATHNframe);
        deathN_phase_tab_widget->setObjectName(QStringLiteral("deathN_phase_tab_widget"));
        deathN_phase_tab_widget->setGeometry(QRect(20, 110, 278, 141));
        deathN_phase_duration_tab = new QWidget();
        deathN_phase_duration_tab->setObjectName(QStringLiteral("deathN_phase_duration_tab"));
        gridLayout_3 = new QGridLayout(deathN_phase_duration_tab);
        gridLayout_3->setObjectName(QStringLiteral("gridLayout_3"));
        DEATHNphase0DurationUnits = new QLabel(deathN_phase_duration_tab);
        DEATHNphase0DurationUnits->setObjectName(QStringLiteral("DEATHNphase0DurationUnits"));

        gridLayout_3->addWidget(DEATHNphase0DurationUnits, 0, 3, 1, 1);

        DEATHNphase0DurationLabel = new QLabel(deathN_phase_duration_tab);
        DEATHNphase0DurationLabel->setObjectName(QStringLiteral("DEATHNphase0DurationLabel"));

        gridLayout_3->addWidget(DEATHNphase0DurationLabel, 0, 0, 1, 1);

        DEATHNphase0Duration = new QLineEdit(deathN_phase_duration_tab);
        DEATHNphase0Duration->setObjectName(QStringLiteral("DEATHNphase0Duration"));

        gridLayout_3->addWidget(DEATHNphase0Duration, 0, 1, 1, 1);

        DEATHNphase0DurationCheckBox = new QCheckBox(deathN_phase_duration_tab);
        DEATHNphase0DurationCheckBox->setObjectName(QStringLiteral("DEATHNphase0DurationCheckBox"));

        gridLayout_3->addWidget(DEATHNphase0DurationCheckBox, 0, 2, 1, 1);

        DEATHNphase1DurationLabel = new QLabel(deathN_phase_duration_tab);
        DEATHNphase1DurationLabel->setObjectName(QStringLiteral("DEATHNphase1DurationLabel"));

        gridLayout_3->addWidget(DEATHNphase1DurationLabel, 1, 0, 1, 1);

        DEATHNphase1Duration = new QLineEdit(deathN_phase_duration_tab);
        DEATHNphase1Duration->setObjectName(QStringLiteral("DEATHNphase1Duration"));

        gridLayout_3->addWidget(DEATHNphase1Duration, 1, 1, 1, 1);

        DEATHNphase1DurationCheckBox = new QCheckBox(deathN_phase_duration_tab);
        DEATHNphase1DurationCheckBox->setObjectName(QStringLiteral("DEATHNphase1DurationCheckBox"));

        gridLayout_3->addWidget(DEATHNphase1DurationCheckBox, 1, 2, 1, 1);

        DEATHNphase1DurationUnits = new QLabel(deathN_phase_duration_tab);
        DEATHNphase1DurationUnits->setObjectName(QStringLiteral("DEATHNphase1DurationUnits"));

        gridLayout_3->addWidget(DEATHNphase1DurationUnits, 1, 3, 1, 1);

        deathN_phase_tab_widget->addTab(deathN_phase_duration_tab, QString());
        deathN_phase_transition_tab = new QWidget();
        deathN_phase_transition_tab->setObjectName(QStringLiteral("deathN_phase_transition_tab"));
        gridLayout_4 = new QGridLayout(deathN_phase_transition_tab);
        gridLayout_4->setObjectName(QStringLiteral("gridLayout_4"));
        DEATHNphase0TransitionUnits = new QLabel(deathN_phase_transition_tab);
        DEATHNphase0TransitionUnits->setObjectName(QStringLiteral("DEATHNphase0TransitionUnits"));

        gridLayout_4->addWidget(DEATHNphase0TransitionUnits, 0, 3, 1, 1);

        DEATHNphase0Transition = new QLineEdit(deathN_phase_transition_tab);
        DEATHNphase0Transition->setObjectName(QStringLiteral("DEATHNphase0Transition"));

        gridLayout_4->addWidget(DEATHNphase0Transition, 0, 1, 1, 1);

        DEATHNphase0TransitionCheckBox = new QCheckBox(deathN_phase_transition_tab);
        DEATHNphase0TransitionCheckBox->setObjectName(QStringLiteral("DEATHNphase0TransitionCheckBox"));

        gridLayout_4->addWidget(DEATHNphase0TransitionCheckBox, 0, 2, 1, 1);

        DEATHNphase0TransitionLabel = new QLabel(deathN_phase_transition_tab);
        DEATHNphase0TransitionLabel->setObjectName(QStringLiteral("DEATHNphase0TransitionLabel"));

        gridLayout_4->addWidget(DEATHNphase0TransitionLabel, 0, 0, 1, 1);

        DEATHNphase1TransitionLabel = new QLabel(deathN_phase_transition_tab);
        DEATHNphase1TransitionLabel->setObjectName(QStringLiteral("DEATHNphase1TransitionLabel"));

        gridLayout_4->addWidget(DEATHNphase1TransitionLabel, 1, 0, 1, 1);

        DEATHNphase1Transition = new QLineEdit(deathN_phase_transition_tab);
        DEATHNphase1Transition->setObjectName(QStringLiteral("DEATHNphase1Transition"));

        gridLayout_4->addWidget(DEATHNphase1Transition, 1, 1, 1, 1);

        DEATHNphase1TransitionCheckBox = new QCheckBox(deathN_phase_transition_tab);
        DEATHNphase1TransitionCheckBox->setObjectName(QStringLiteral("DEATHNphase1TransitionCheckBox"));

        gridLayout_4->addWidget(DEATHNphase1TransitionCheckBox, 1, 2, 1, 1);

        DEATHNphase1TransitionUnits = new QLabel(deathN_phase_transition_tab);
        DEATHNphase1TransitionUnits->setObjectName(QStringLiteral("DEATHNphase1TransitionUnits"));

        gridLayout_4->addWidget(DEATHNphase1TransitionUnits, 1, 3, 1, 1);

        deathN_phase_tab_widget->addTab(deathN_phase_transition_tab, QString());
        layoutWidget_54 = new QWidget(DEATHNframe);
        layoutWidget_54->setObjectName(QStringLiteral("layoutWidget_54"));
        layoutWidget_54->setGeometry(QRect(323, 104, 291, 24));
        DEATHNLysedFluidChangeRateLayout = new QHBoxLayout(layoutWidget_54);
        DEATHNLysedFluidChangeRateLayout->setObjectName(QStringLiteral("DEATHNLysedFluidChangeRateLayout"));
        DEATHNLysedFluidChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHNlysedFluidChangeRateLabel = new QLabel(layoutWidget_54);
        DEATHNlysedFluidChangeRateLabel->setObjectName(QStringLiteral("DEATHNlysedFluidChangeRateLabel"));
        DEATHNlysedFluidChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHNLysedFluidChangeRateLayout->addWidget(DEATHNlysedFluidChangeRateLabel);

        DEATHNlysedFluidChangeRate = new QLineEdit(layoutWidget_54);
        DEATHNlysedFluidChangeRate->setObjectName(QStringLiteral("DEATHNlysedFluidChangeRate"));

        DEATHNLysedFluidChangeRateLayout->addWidget(DEATHNlysedFluidChangeRate);

        DEATHNlysedFluidChangeRateUnits = new QToolButton(layoutWidget_54);
        DEATHNlysedFluidChangeRateUnits->setObjectName(QStringLiteral("DEATHNlysedFluidChangeRateUnits"));

        DEATHNLysedFluidChangeRateLayout->addWidget(DEATHNlysedFluidChangeRateUnits);

        layoutWidget_52 = new QWidget(DEATHNframe);
        layoutWidget_52->setObjectName(QStringLiteral("layoutWidget_52"));
        layoutWidget_52->setGeometry(QRect(323, 73, 291, 24));
        DEATHNUnlysedFluidChangeRateLayout = new QHBoxLayout(layoutWidget_52);
        DEATHNUnlysedFluidChangeRateLayout->setObjectName(QStringLiteral("DEATHNUnlysedFluidChangeRateLayout"));
        DEATHNUnlysedFluidChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHNunlysedFluidChangeRateLabel = new QLabel(layoutWidget_52);
        DEATHNunlysedFluidChangeRateLabel->setObjectName(QStringLiteral("DEATHNunlysedFluidChangeRateLabel"));
        DEATHNunlysedFluidChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHNUnlysedFluidChangeRateLayout->addWidget(DEATHNunlysedFluidChangeRateLabel);

        DEATHNunlysedFluidChangeRate = new QLineEdit(layoutWidget_52);
        DEATHNunlysedFluidChangeRate->setObjectName(QStringLiteral("DEATHNunlysedFluidChangeRate"));

        DEATHNUnlysedFluidChangeRateLayout->addWidget(DEATHNunlysedFluidChangeRate);

        DEATHNunlysedFluidChangeRateUnits = new QToolButton(layoutWidget_52);
        DEATHNunlysedFluidChangeRateUnits->setObjectName(QStringLiteral("DEATHNunlysedFluidChangeRateUnits"));

        DEATHNUnlysedFluidChangeRateLayout->addWidget(DEATHNunlysedFluidChangeRateUnits);

        layoutWidget_50 = new QWidget(DEATHNframe);
        layoutWidget_50->setObjectName(QStringLiteral("layoutWidget_50"));
        layoutWidget_50->setGeometry(QRect(22, 72, 281, 24));
        DEATHNDeathRateLayout = new QHBoxLayout(layoutWidget_50);
        DEATHNDeathRateLayout->setObjectName(QStringLiteral("DEATHNDeathRateLayout"));
        DEATHNDeathRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHNdeathRateLabel = new QLabel(layoutWidget_50);
        DEATHNdeathRateLabel->setObjectName(QStringLiteral("DEATHNdeathRateLabel"));
        DEATHNdeathRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHNDeathRateLayout->addWidget(DEATHNdeathRateLabel);

        DEATHNdeathRateField = new QLineEdit(layoutWidget_50);
        DEATHNdeathRateField->setObjectName(QStringLiteral("DEATHNdeathRateField"));

        DEATHNDeathRateLayout->addWidget(DEATHNdeathRateField);

        DEATHNdeathRateUnits = new QToolButton(layoutWidget_50);
        DEATHNdeathRateUnits->setObjectName(QStringLiteral("DEATHNdeathRateUnits"));

        DEATHNDeathRateLayout->addWidget(DEATHNdeathRateUnits);

        layoutWidget_58 = new QWidget(DEATHNframe);
        layoutWidget_58->setObjectName(QStringLiteral("layoutWidget_58"));
        layoutWidget_58->setGeometry(QRect(323, 134, 291, 24));
        DEATHNCytoplasmicBiomassChangeRateLayout = new QHBoxLayout(layoutWidget_58);
        DEATHNCytoplasmicBiomassChangeRateLayout->setObjectName(QStringLiteral("DEATHNCytoplasmicBiomassChangeRateLayout"));
        DEATHNCytoplasmicBiomassChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHNcytoplasmicBiomassChangeRateLabel = new QLabel(layoutWidget_58);
        DEATHNcytoplasmicBiomassChangeRateLabel->setObjectName(QStringLiteral("DEATHNcytoplasmicBiomassChangeRateLabel"));
        DEATHNcytoplasmicBiomassChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHNCytoplasmicBiomassChangeRateLayout->addWidget(DEATHNcytoplasmicBiomassChangeRateLabel);

        DEATHNcytoplasmicBiomassChangeRate = new QLineEdit(layoutWidget_58);
        DEATHNcytoplasmicBiomassChangeRate->setObjectName(QStringLiteral("DEATHNcytoplasmicBiomassChangeRate"));

        DEATHNCytoplasmicBiomassChangeRateLayout->addWidget(DEATHNcytoplasmicBiomassChangeRate);

        DEATHNcytoplasmicBiomassChangeRateUnits = new QToolButton(layoutWidget_58);
        DEATHNcytoplasmicBiomassChangeRateUnits->setObjectName(QStringLiteral("DEATHNcytoplasmicBiomassChangeRateUnits"));

        DEATHNCytoplasmicBiomassChangeRateLayout->addWidget(DEATHNcytoplasmicBiomassChangeRateUnits);

        layoutWidget_49 = new QWidget(DEATHNframe);
        layoutWidget_49->setObjectName(QStringLiteral("layoutWidget_49"));
        layoutWidget_49->setGeometry(QRect(322, 225, 291, 24));
        DEATHNRelativeRuptureVolumeLayout = new QHBoxLayout(layoutWidget_49);
        DEATHNRelativeRuptureVolumeLayout->setObjectName(QStringLiteral("DEATHNRelativeRuptureVolumeLayout"));
        DEATHNRelativeRuptureVolumeLayout->setContentsMargins(0, 0, 0, 0);
        DEATHNrelativeRuptureVolumeLabel = new QLabel(layoutWidget_49);
        DEATHNrelativeRuptureVolumeLabel->setObjectName(QStringLiteral("DEATHNrelativeRuptureVolumeLabel"));
        DEATHNrelativeRuptureVolumeLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHNRelativeRuptureVolumeLayout->addWidget(DEATHNrelativeRuptureVolumeLabel);

        DEATHNrelativeRuptureVolume = new QLineEdit(layoutWidget_49);
        DEATHNrelativeRuptureVolume->setObjectName(QStringLiteral("DEATHNrelativeRuptureVolume"));

        DEATHNRelativeRuptureVolumeLayout->addWidget(DEATHNrelativeRuptureVolume);

        layoutWidget_72 = new QWidget(DEATHNframe);
        layoutWidget_72->setObjectName(QStringLiteral("layoutWidget_72"));
        layoutWidget_72->setGeometry(QRect(20, 30, 181, 25));
        DEATHNNameLayout = new QHBoxLayout(layoutWidget_72);
        DEATHNNameLayout->setObjectName(QStringLiteral("DEATHNNameLayout"));
        DEATHNNameLayout->setContentsMargins(0, 0, 0, 0);
        DEATHNnameLabel = new QLabel(layoutWidget_72);
        DEATHNnameLabel->setObjectName(QStringLiteral("DEATHNnameLabel"));
        DEATHNnameLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHNNameLayout->addWidget(DEATHNnameLabel);

        DEATHNname = new QLineEdit(layoutWidget_72);
        DEATHNname->setObjectName(QStringLiteral("DEATHNname"));

        DEATHNNameLayout->addWidget(DEATHNname);

        layoutWidget_56 = new QWidget(DEATHNframe);
        layoutWidget_56->setObjectName(QStringLiteral("layoutWidget_56"));
        layoutWidget_56->setGeometry(QRect(323, 196, 291, 24));
        DEATHNCalcificationLayout = new QHBoxLayout(layoutWidget_56);
        DEATHNCalcificationLayout->setObjectName(QStringLiteral("DEATHNCalcificationLayout"));
        DEATHNCalcificationLayout->setContentsMargins(0, 0, 0, 0);
        DEATHNcalcificationRateLabel = new QLabel(layoutWidget_56);
        DEATHNcalcificationRateLabel->setObjectName(QStringLiteral("DEATHNcalcificationRateLabel"));
        DEATHNcalcificationRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHNCalcificationLayout->addWidget(DEATHNcalcificationRateLabel);

        DEATHNcalcificationRate = new QLineEdit(layoutWidget_56);
        DEATHNcalcificationRate->setObjectName(QStringLiteral("DEATHNcalcificationRate"));

        DEATHNCalcificationLayout->addWidget(DEATHNcalcificationRate);

        DEATHNcalcificationRateUnits = new QToolButton(layoutWidget_56);
        DEATHNcalcificationRateUnits->setObjectName(QStringLiteral("DEATHNcalcificationRateUnits"));

        DEATHNCalcificationLayout->addWidget(DEATHNcalcificationRateUnits);

        DEATHnecrosisLabel = new QLabel(DEATHNframe);
        DEATHnecrosisLabel->setObjectName(QStringLiteral("DEATHnecrosisLabel"));
        DEATHnecrosisLabel->setGeometry(QRect(360, 20, 191, 31));
        DEATHnecrosisLabel->setTextFormat(Qt::MarkdownText);
        layoutWidget_53 = new QWidget(DEATHNframe);
        layoutWidget_53->setObjectName(QStringLiteral("layoutWidget_53"));
        layoutWidget_53->setGeometry(QRect(323, 165, 291, 24));
        DEATHNNuclearBiomassChangeRateLayout = new QHBoxLayout(layoutWidget_53);
        DEATHNNuclearBiomassChangeRateLayout->setObjectName(QStringLiteral("DEATHNNuclearBiomassChangeRateLayout"));
        DEATHNNuclearBiomassChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        DEATHNnuclearBiomassChangeRateLabel = new QLabel(layoutWidget_53);
        DEATHNnuclearBiomassChangeRateLabel->setObjectName(QStringLiteral("DEATHNnuclearBiomassChangeRateLabel"));
        DEATHNnuclearBiomassChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        DEATHNNuclearBiomassChangeRateLayout->addWidget(DEATHNnuclearBiomassChangeRateLabel);

        DEATHNnuclearBiomassChangeRate = new QLineEdit(layoutWidget_53);
        DEATHNnuclearBiomassChangeRate->setObjectName(QStringLiteral("DEATHNnuclearBiomassChangeRate"));

        DEATHNNuclearBiomassChangeRateLayout->addWidget(DEATHNnuclearBiomassChangeRate);

        DEATHNnuclearBiomassChangeRateUnits = new QToolButton(layoutWidget_53);
        DEATHNnuclearBiomassChangeRateUnits->setObjectName(QStringLiteral("DEATHNnuclearBiomassChangeRateUnits"));

        DEATHNNuclearBiomassChangeRateLayout->addWidget(DEATHNnuclearBiomassChangeRateUnits);


        verticalLayout->addWidget(DEATHNframe);

        DEATHscrollArea->setWidget(scrollAreaWidgetContents);
        cell_tab_widget->addTab(death_tab, QString());
        volume_tab = new QWidget();
        volume_tab->setObjectName(QStringLiteral("volume_tab"));
        sizePolicy.setHeightForWidth(volume_tab->sizePolicy().hasHeightForWidth());
        volume_tab->setSizePolicy(sizePolicy);
        layoutWidget_51 = new QWidget(volume_tab);
        layoutWidget_51->setObjectName(QStringLiteral("layoutWidget_51"));
        layoutWidget_51->setGeometry(QRect(20, 90, 281, 24));
        VOLUMEFluidFractionLayout = new QHBoxLayout(layoutWidget_51);
        VOLUMEFluidFractionLayout->setObjectName(QStringLiteral("VOLUMEFluidFractionLayout"));
        VOLUMEFluidFractionLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMEfluidFractionLabel = new QLabel(layoutWidget_51);
        VOLUMEfluidFractionLabel->setObjectName(QStringLiteral("VOLUMEfluidFractionLabel"));
        VOLUMEfluidFractionLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMEFluidFractionLayout->addWidget(VOLUMEfluidFractionLabel);

        VOLUMEfluidFraction = new QLineEdit(layoutWidget_51);
        VOLUMEfluidFraction->setObjectName(QStringLiteral("VOLUMEfluidFraction"));

        VOLUMEFluidFractionLayout->addWidget(VOLUMEfluidFraction);

        layoutWidget_55 = new QWidget(volume_tab);
        layoutWidget_55->setObjectName(QStringLiteral("layoutWidget_55"));
        layoutWidget_55->setGeometry(QRect(360, 240, 287, 24));
        VOLUMECalcifiedFractionLayout = new QHBoxLayout(layoutWidget_55);
        VOLUMECalcifiedFractionLayout->setObjectName(QStringLiteral("VOLUMECalcifiedFractionLayout"));
        VOLUMECalcifiedFractionLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMEcalcifiedFractionLabel = new QLabel(layoutWidget_55);
        VOLUMEcalcifiedFractionLabel->setObjectName(QStringLiteral("VOLUMEcalcifiedFractionLabel"));
        VOLUMEcalcifiedFractionLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMECalcifiedFractionLayout->addWidget(VOLUMEcalcifiedFractionLabel);

        VOLUMEcalcifiedFraction = new QLineEdit(layoutWidget_55);
        VOLUMEcalcifiedFraction->setObjectName(QStringLiteral("VOLUMEcalcifiedFraction"));

        VOLUMECalcifiedFractionLayout->addWidget(VOLUMEcalcifiedFraction);

        layoutWidget_57 = new QWidget(volume_tab);
        layoutWidget_57->setObjectName(QStringLiteral("layoutWidget_57"));
        layoutWidget_57->setGeometry(QRect(20, 240, 281, 24));
        VOLUMERelativeRuptureVolumeLayout = new QHBoxLayout(layoutWidget_57);
        VOLUMERelativeRuptureVolumeLayout->setObjectName(QStringLiteral("VOLUMERelativeRuptureVolumeLayout"));
        VOLUMERelativeRuptureVolumeLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMErelativeRuptureVolumeLabel = new QLabel(layoutWidget_57);
        VOLUMErelativeRuptureVolumeLabel->setObjectName(QStringLiteral("VOLUMErelativeRuptureVolumeLabel"));
        VOLUMErelativeRuptureVolumeLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMERelativeRuptureVolumeLayout->addWidget(VOLUMErelativeRuptureVolumeLabel);

        VOLUMErelativeRuptureVolume = new QLineEdit(layoutWidget_57);
        VOLUMErelativeRuptureVolume->setObjectName(QStringLiteral("VOLUMErelativeRuptureVolume"));
        VOLUMErelativeRuptureVolume->setInputMethodHints(Qt::ImhNone);

        VOLUMERelativeRuptureVolumeLayout->addWidget(VOLUMErelativeRuptureVolume);

        layoutWidget = new QWidget(volume_tab);
        layoutWidget->setObjectName(QStringLiteral("layoutWidget"));
        layoutWidget->setGeometry(QRect(22, 32, 281, 24));
        VOLUMETotalVolumeLayout = new QHBoxLayout(layoutWidget);
        VOLUMETotalVolumeLayout->setObjectName(QStringLiteral("VOLUMETotalVolumeLayout"));
        VOLUMETotalVolumeLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMEtotalVolumeLabel = new QLabel(layoutWidget);
        VOLUMEtotalVolumeLabel->setObjectName(QStringLiteral("VOLUMEtotalVolumeLabel"));
        VOLUMEtotalVolumeLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMETotalVolumeLayout->addWidget(VOLUMEtotalVolumeLabel);

        VOLUMEtotalVolume = new QLineEdit(layoutWidget);
        VOLUMEtotalVolume->setObjectName(QStringLiteral("VOLUMEtotalVolume"));

        VOLUMETotalVolumeLayout->addWidget(VOLUMEtotalVolume);

        VOLUMEtotalVolumeUnits = new QToolButton(layoutWidget);
        VOLUMEtotalVolumeUnits->setObjectName(QStringLiteral("VOLUMEtotalVolumeUnits"));

        VOLUMETotalVolumeLayout->addWidget(VOLUMEtotalVolumeUnits);

        layoutWidget1 = new QWidget(volume_tab);
        layoutWidget1->setObjectName(QStringLiteral("layoutWidget1"));
        layoutWidget1->setGeometry(QRect(22, 62, 281, 24));
        VOLUMENuclearVolumeLayout = new QHBoxLayout(layoutWidget1);
        VOLUMENuclearVolumeLayout->setObjectName(QStringLiteral("VOLUMENuclearVolumeLayout"));
        VOLUMENuclearVolumeLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMEnuclearVolumeLabel = new QLabel(layoutWidget1);
        VOLUMEnuclearVolumeLabel->setObjectName(QStringLiteral("VOLUMEnuclearVolumeLabel"));
        VOLUMEnuclearVolumeLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMENuclearVolumeLayout->addWidget(VOLUMEnuclearVolumeLabel);

        VOLUMEnuclearVolume = new QLineEdit(layoutWidget1);
        VOLUMEnuclearVolume->setObjectName(QStringLiteral("VOLUMEnuclearVolume"));

        VOLUMENuclearVolumeLayout->addWidget(VOLUMEnuclearVolume);

        VOLUMEnuclearVolumeUnits = new QToolButton(layoutWidget1);
        VOLUMEnuclearVolumeUnits->setObjectName(QStringLiteral("VOLUMEnuclearVolumeUnits"));

        VOLUMENuclearVolumeLayout->addWidget(VOLUMEnuclearVolumeUnits);

        layoutWidget2 = new QWidget(volume_tab);
        layoutWidget2->setObjectName(QStringLiteral("layoutWidget2"));
        layoutWidget2->setGeometry(QRect(362, 272, 281, 24));
        VOLUMECalcificationRateLayout = new QHBoxLayout(layoutWidget2);
        VOLUMECalcificationRateLayout->setObjectName(QStringLiteral("VOLUMECalcificationRateLayout"));
        VOLUMECalcificationRateLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMEcalcificationRateLabel = new QLabel(layoutWidget2);
        VOLUMEcalcificationRateLabel->setObjectName(QStringLiteral("VOLUMEcalcificationRateLabel"));
        VOLUMEcalcificationRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMECalcificationRateLayout->addWidget(VOLUMEcalcificationRateLabel);

        VOLUMEcalcificationRate = new QLineEdit(layoutWidget2);
        VOLUMEcalcificationRate->setObjectName(QStringLiteral("VOLUMEcalcificationRate"));

        VOLUMECalcificationRateLayout->addWidget(VOLUMEcalcificationRate);

        VOLUMEcalcificationRateUnits = new QToolButton(layoutWidget2);
        VOLUMEcalcificationRateUnits->setObjectName(QStringLiteral("VOLUMEcalcificationRateUnits"));

        VOLUMECalcificationRateLayout->addWidget(VOLUMEcalcificationRateUnits);

        layoutWidget3 = new QWidget(volume_tab);
        layoutWidget3->setObjectName(QStringLiteral("layoutWidget3"));
        layoutWidget3->setGeometry(QRect(362, 92, 301, 24));
        VOLUMEFluidChangeRateLayout = new QHBoxLayout(layoutWidget3);
        VOLUMEFluidChangeRateLayout->setObjectName(QStringLiteral("VOLUMEFluidChangeRateLayout"));
        VOLUMEFluidChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMEfluidChangeRateLabel = new QLabel(layoutWidget3);
        VOLUMEfluidChangeRateLabel->setObjectName(QStringLiteral("VOLUMEfluidChangeRateLabel"));
        VOLUMEfluidChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMEFluidChangeRateLayout->addWidget(VOLUMEfluidChangeRateLabel);

        VOLUMEfluidChangeRate = new QLineEdit(layoutWidget3);
        VOLUMEfluidChangeRate->setObjectName(QStringLiteral("VOLUMEfluidChangeRate"));

        VOLUMEFluidChangeRateLayout->addWidget(VOLUMEfluidChangeRate);

        VOLUMEfluidChangeRateUnits = new QToolButton(layoutWidget3);
        VOLUMEfluidChangeRateUnits->setObjectName(QStringLiteral("VOLUMEfluidChangeRateUnits"));

        VOLUMEFluidChangeRateLayout->addWidget(VOLUMEfluidChangeRateUnits);

        layoutWidget4 = new QWidget(volume_tab);
        layoutWidget4->setObjectName(QStringLiteral("layoutWidget4"));
        layoutWidget4->setGeometry(QRect(362, 62, 301, 24));
        VOLUMECytoplasmicBiomassChangeRateLayout = new QHBoxLayout(layoutWidget4);
        VOLUMECytoplasmicBiomassChangeRateLayout->setObjectName(QStringLiteral("VOLUMECytoplasmicBiomassChangeRateLayout"));
        VOLUMECytoplasmicBiomassChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMEcytoplasmicBiomassChangeRateLabel = new QLabel(layoutWidget4);
        VOLUMEcytoplasmicBiomassChangeRateLabel->setObjectName(QStringLiteral("VOLUMEcytoplasmicBiomassChangeRateLabel"));
        VOLUMEcytoplasmicBiomassChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMECytoplasmicBiomassChangeRateLayout->addWidget(VOLUMEcytoplasmicBiomassChangeRateLabel);

        VOLUMEcytoplasmicBiomassChangeRate = new QLineEdit(layoutWidget4);
        VOLUMEcytoplasmicBiomassChangeRate->setObjectName(QStringLiteral("VOLUMEcytoplasmicBiomassChangeRate"));

        VOLUMECytoplasmicBiomassChangeRateLayout->addWidget(VOLUMEcytoplasmicBiomassChangeRate);

        VOLUMEcytoplasmicBiomassChangeRateUnits = new QToolButton(layoutWidget4);
        VOLUMEcytoplasmicBiomassChangeRateUnits->setObjectName(QStringLiteral("VOLUMEcytoplasmicBiomassChangeRateUnits"));

        VOLUMECytoplasmicBiomassChangeRateLayout->addWidget(VOLUMEcytoplasmicBiomassChangeRateUnits);

        layoutWidget5 = new QWidget(volume_tab);
        layoutWidget5->setObjectName(QStringLiteral("layoutWidget5"));
        layoutWidget5->setGeometry(QRect(362, 32, 302, 24));
        VOLUMENuclearBiomassChangeRateLayout = new QHBoxLayout(layoutWidget5);
        VOLUMENuclearBiomassChangeRateLayout->setObjectName(QStringLiteral("VOLUMENuclearBiomassChangeRateLayout"));
        VOLUMENuclearBiomassChangeRateLayout->setContentsMargins(0, 0, 0, 0);
        VOLUMEnuclearBiomassChangeRateLabel = new QLabel(layoutWidget5);
        VOLUMEnuclearBiomassChangeRateLabel->setObjectName(QStringLiteral("VOLUMEnuclearBiomassChangeRateLabel"));
        VOLUMEnuclearBiomassChangeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        VOLUMENuclearBiomassChangeRateLayout->addWidget(VOLUMEnuclearBiomassChangeRateLabel);

        VOLUMEnuclearBiomassChangeRate = new QLineEdit(layoutWidget5);
        VOLUMEnuclearBiomassChangeRate->setObjectName(QStringLiteral("VOLUMEnuclearBiomassChangeRate"));

        VOLUMENuclearBiomassChangeRateLayout->addWidget(VOLUMEnuclearBiomassChangeRate);

        VOLUMEnuclearBiomassChangeRateUnits = new QToolButton(layoutWidget5);
        VOLUMEnuclearBiomassChangeRateUnits->setObjectName(QStringLiteral("VOLUMEnuclearBiomassChangeRateUnits"));

        VOLUMENuclearBiomassChangeRateLayout->addWidget(VOLUMEnuclearBiomassChangeRateUnits);

        cell_tab_widget->addTab(volume_tab, QString());
        mechanics_tab = new QWidget();
        mechanics_tab->setObjectName(QStringLiteral("mechanics_tab"));
        sizePolicy.setHeightForWidth(mechanics_tab->sizePolicy().hasHeightForWidth());
        mechanics_tab->setSizePolicy(sizePolicy);
        layoutWidget_60 = new QWidget(mechanics_tab);
        layoutWidget_60->setObjectName(QStringLiteral("layoutWidget_60"));
        layoutWidget_60->setGeometry(QRect(10, 90, 301, 24));
        MECHANICSRelativeMaximumAdhesionStrengthLayout = new QHBoxLayout(layoutWidget_60);
        MECHANICSRelativeMaximumAdhesionStrengthLayout->setObjectName(QStringLiteral("MECHANICSRelativeMaximumAdhesionStrengthLayout"));
        MECHANICSRelativeMaximumAdhesionStrengthLayout->setContentsMargins(0, 0, 0, 0);
        MECHANICSrelativeMaximumAdhesionStrengthLabel = new QLabel(layoutWidget_60);
        MECHANICSrelativeMaximumAdhesionStrengthLabel->setObjectName(QStringLiteral("MECHANICSrelativeMaximumAdhesionStrengthLabel"));
        MECHANICSrelativeMaximumAdhesionStrengthLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MECHANICSRelativeMaximumAdhesionStrengthLayout->addWidget(MECHANICSrelativeMaximumAdhesionStrengthLabel);

        MECHANICSrelativeMaximumAdhesionStrength = new QLineEdit(layoutWidget_60);
        MECHANICSrelativeMaximumAdhesionStrength->setObjectName(QStringLiteral("MECHANICSrelativeMaximumAdhesionStrength"));

        MECHANICSRelativeMaximumAdhesionStrengthLayout->addWidget(MECHANICSrelativeMaximumAdhesionStrength);

        mechanics_phase_tab_widget = new QTabWidget(mechanics_tab);
        mechanics_phase_tab_widget->setObjectName(QStringLiteral("mechanics_phase_tab_widget"));
        mechanics_phase_tab_widget->setGeometry(QRect(10, 130, 431, 81));
        mechanics_relative_equilibrium_distance_tab = new QWidget();
        mechanics_relative_equilibrium_distance_tab->setObjectName(QStringLiteral("mechanics_relative_equilibrium_distance_tab"));
        layoutWidget6 = new QWidget(mechanics_relative_equilibrium_distance_tab);
        layoutWidget6->setObjectName(QStringLiteral("layoutWidget6"));
        layoutWidget6->setGeometry(QRect(12, 22, 296, 24));
        MECHANICSRelativeEquilibriumDistanceLayout = new QHBoxLayout(layoutWidget6);
        MECHANICSRelativeEquilibriumDistanceLayout->setObjectName(QStringLiteral("MECHANICSRelativeEquilibriumDistanceLayout"));
        MECHANICSRelativeEquilibriumDistanceLayout->setContentsMargins(0, 0, 0, 0);
        MECHANICSrelativeEquilibriumDistanceLabel = new QLabel(layoutWidget6);
        MECHANICSrelativeEquilibriumDistanceLabel->setObjectName(QStringLiteral("MECHANICSrelativeEquilibriumDistanceLabel"));
        MECHANICSrelativeEquilibriumDistanceLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MECHANICSRelativeEquilibriumDistanceLayout->addWidget(MECHANICSrelativeEquilibriumDistanceLabel);

        MECHANICSrelativeEquilibriumDistance = new QLineEdit(layoutWidget6);
        MECHANICSrelativeEquilibriumDistance->setObjectName(QStringLiteral("MECHANICSrelativeEquilibriumDistance"));

        MECHANICSRelativeEquilibriumDistanceLayout->addWidget(MECHANICSrelativeEquilibriumDistance);

        mechanics_phase_tab_widget->addTab(mechanics_relative_equilibrium_distance_tab, QString());
        mechanics_absolute_equilibrium_distance_tab = new QWidget();
        mechanics_absolute_equilibrium_distance_tab->setObjectName(QStringLiteral("mechanics_absolute_equilibrium_distance_tab"));
        layoutWidget7 = new QWidget(mechanics_absolute_equilibrium_distance_tab);
        layoutWidget7->setObjectName(QStringLiteral("layoutWidget7"));
        layoutWidget7->setGeometry(QRect(12, 22, 312, 24));
        MECHANICSAbsoluteEquilibriumDistanceLayout = new QHBoxLayout(layoutWidget7);
        MECHANICSAbsoluteEquilibriumDistanceLayout->setObjectName(QStringLiteral("MECHANICSAbsoluteEquilibriumDistanceLayout"));
        MECHANICSAbsoluteEquilibriumDistanceLayout->setContentsMargins(0, 0, 0, 0);
        MECHANICSabsoluteEquilibriumDistanceLabel = new QLabel(layoutWidget7);
        MECHANICSabsoluteEquilibriumDistanceLabel->setObjectName(QStringLiteral("MECHANICSabsoluteEquilibriumDistanceLabel"));
        MECHANICSabsoluteEquilibriumDistanceLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MECHANICSAbsoluteEquilibriumDistanceLayout->addWidget(MECHANICSabsoluteEquilibriumDistanceLabel);

        MECHANICSabsoluteEquilibriumDistance = new QLineEdit(layoutWidget7);
        MECHANICSabsoluteEquilibriumDistance->setObjectName(QStringLiteral("MECHANICSabsoluteEquilibriumDistance"));

        MECHANICSAbsoluteEquilibriumDistanceLayout->addWidget(MECHANICSabsoluteEquilibriumDistance);

        MECHANICSabsoluteEquilibriumDistanceUnits = new QToolButton(layoutWidget7);
        MECHANICSabsoluteEquilibriumDistanceUnits->setObjectName(QStringLiteral("MECHANICSabsoluteEquilibriumDistanceUnits"));

        MECHANICSAbsoluteEquilibriumDistanceLayout->addWidget(MECHANICSabsoluteEquilibriumDistanceUnits);

        mechanics_phase_tab_widget->addTab(mechanics_absolute_equilibrium_distance_tab, QString());
        layoutWidget8 = new QWidget(mechanics_tab);
        layoutWidget8->setObjectName(QStringLiteral("layoutWidget8"));
        layoutWidget8->setGeometry(QRect(12, 22, 301, 24));
        MECHANICSCellAdhesionStrengthLayout = new QHBoxLayout(layoutWidget8);
        MECHANICSCellAdhesionStrengthLayout->setObjectName(QStringLiteral("MECHANICSCellAdhesionStrengthLayout"));
        MECHANICSCellAdhesionStrengthLayout->setContentsMargins(0, 0, 0, 0);
        MECHANICScellAdhesionStrengthLabel = new QLabel(layoutWidget8);
        MECHANICScellAdhesionStrengthLabel->setObjectName(QStringLiteral("MECHANICScellAdhesionStrengthLabel"));
        MECHANICScellAdhesionStrengthLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MECHANICSCellAdhesionStrengthLayout->addWidget(MECHANICScellAdhesionStrengthLabel);

        MECHANICScellAdhesionStrength = new QLineEdit(layoutWidget8);
        MECHANICScellAdhesionStrength->setObjectName(QStringLiteral("MECHANICScellAdhesionStrength"));

        MECHANICSCellAdhesionStrengthLayout->addWidget(MECHANICScellAdhesionStrength);

        MECHANICScellAdhesionStrengthUnits = new QToolButton(layoutWidget8);
        MECHANICScellAdhesionStrengthUnits->setObjectName(QStringLiteral("MECHANICScellAdhesionStrengthUnits"));

        MECHANICSCellAdhesionStrengthLayout->addWidget(MECHANICScellAdhesionStrengthUnits);

        layoutWidget9 = new QWidget(mechanics_tab);
        layoutWidget9->setObjectName(QStringLiteral("layoutWidget9"));
        layoutWidget9->setGeometry(QRect(12, 52, 301, 24));
        MECHANICSCellRepulsionStrengthLayout = new QHBoxLayout(layoutWidget9);
        MECHANICSCellRepulsionStrengthLayout->setObjectName(QStringLiteral("MECHANICSCellRepulsionStrengthLayout"));
        MECHANICSCellRepulsionStrengthLayout->setContentsMargins(0, 0, 0, 0);
        MECHANICScellRepulsionStrengthLabel = new QLabel(layoutWidget9);
        MECHANICScellRepulsionStrengthLabel->setObjectName(QStringLiteral("MECHANICScellRepulsionStrengthLabel"));
        MECHANICScellRepulsionStrengthLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MECHANICSCellRepulsionStrengthLayout->addWidget(MECHANICScellRepulsionStrengthLabel);

        MECHANICScellRepulsionStrength = new QLineEdit(layoutWidget9);
        MECHANICScellRepulsionStrength->setObjectName(QStringLiteral("MECHANICScellRepulsionStrength"));

        MECHANICSCellRepulsionStrengthLayout->addWidget(MECHANICScellRepulsionStrength);

        MECHANICScellRepulsionStrengtUnits = new QToolButton(layoutWidget9);
        MECHANICScellRepulsionStrengtUnits->setObjectName(QStringLiteral("MECHANICScellRepulsionStrengtUnits"));

        MECHANICSCellRepulsionStrengthLayout->addWidget(MECHANICScellRepulsionStrengtUnits);

        cell_tab_widget->addTab(mechanics_tab, QString());
        motility_tab = new QWidget();
        motility_tab->setObjectName(QStringLiteral("motility_tab"));
        sizePolicy.setHeightForWidth(motility_tab->sizePolicy().hasHeightForWidth());
        motility_tab->setSizePolicy(sizePolicy);
        MOTILITYenableCheckBox = new QCheckBox(motility_tab);
        MOTILITYenableCheckBox->setObjectName(QStringLiteral("MOTILITYenableCheckBox"));
        MOTILITYenableCheckBox->setGeometry(QRect(20, 20, 101, 17));
        MOTILITYuse2dCheckBox = new QCheckBox(motility_tab);
        MOTILITYuse2dCheckBox->setObjectName(QStringLiteral("MOTILITYuse2dCheckBox"));
        MOTILITYuse2dCheckBox->setGeometry(QRect(140, 20, 70, 17));
        layoutWidget10 = new QWidget(motility_tab);
        layoutWidget10->setObjectName(QStringLiteral("layoutWidget10"));
        layoutWidget10->setGeometry(QRect(20, 60, 291, 24));
        MOTILITYSpeedLayout = new QHBoxLayout(layoutWidget10);
        MOTILITYSpeedLayout->setObjectName(QStringLiteral("MOTILITYSpeedLayout"));
        MOTILITYSpeedLayout->setContentsMargins(0, 0, 0, 0);
        MOTILITYspeedLabel = new QLabel(layoutWidget10);
        MOTILITYspeedLabel->setObjectName(QStringLiteral("MOTILITYspeedLabel"));
        MOTILITYspeedLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MOTILITYSpeedLayout->addWidget(MOTILITYspeedLabel);

        MOTILITYspeed = new QLineEdit(layoutWidget10);
        MOTILITYspeed->setObjectName(QStringLiteral("MOTILITYspeed"));

        MOTILITYSpeedLayout->addWidget(MOTILITYspeed);

        MOTILITYspeedUnits = new QToolButton(layoutWidget10);
        MOTILITYspeedUnits->setObjectName(QStringLiteral("MOTILITYspeedUnits"));

        MOTILITYSpeedLayout->addWidget(MOTILITYspeedUnits);

        layoutWidget11 = new QWidget(motility_tab);
        layoutWidget11->setObjectName(QStringLiteral("layoutWidget11"));
        layoutWidget11->setGeometry(QRect(20, 90, 291, 24));
        MOTILITYPersistenceTimeLayout = new QHBoxLayout(layoutWidget11);
        MOTILITYPersistenceTimeLayout->setObjectName(QStringLiteral("MOTILITYPersistenceTimeLayout"));
        MOTILITYPersistenceTimeLayout->setContentsMargins(0, 0, 0, 0);
        MOTILITYpersistenceTimeLabel = new QLabel(layoutWidget11);
        MOTILITYpersistenceTimeLabel->setObjectName(QStringLiteral("MOTILITYpersistenceTimeLabel"));
        MOTILITYpersistenceTimeLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MOTILITYPersistenceTimeLayout->addWidget(MOTILITYpersistenceTimeLabel);

        MOTILITYpersistenceTime = new QLineEdit(layoutWidget11);
        MOTILITYpersistenceTime->setObjectName(QStringLiteral("MOTILITYpersistenceTime"));

        MOTILITYPersistenceTimeLayout->addWidget(MOTILITYpersistenceTime);

        MOTILITYpersistenceTimeUnits = new QToolButton(layoutWidget11);
        MOTILITYpersistenceTimeUnits->setObjectName(QStringLiteral("MOTILITYpersistenceTimeUnits"));

        MOTILITYPersistenceTimeLayout->addWidget(MOTILITYpersistenceTimeUnits);

        layoutWidget12 = new QWidget(motility_tab);
        layoutWidget12->setObjectName(QStringLiteral("layoutWidget12"));
        layoutWidget12->setGeometry(QRect(20, 120, 291, 24));
        MOTILITYMitigationBiasLayout = new QHBoxLayout(layoutWidget12);
        MOTILITYMitigationBiasLayout->setObjectName(QStringLiteral("MOTILITYMitigationBiasLayout"));
        MOTILITYMitigationBiasLayout->setContentsMargins(0, 0, 0, 0);
        MOTILITYmitigationBiasLabel = new QLabel(layoutWidget12);
        MOTILITYmitigationBiasLabel->setObjectName(QStringLiteral("MOTILITYmitigationBiasLabel"));
        MOTILITYmitigationBiasLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MOTILITYMitigationBiasLayout->addWidget(MOTILITYmitigationBiasLabel);

        MOTILITYmitigationBias = new QLineEdit(layoutWidget12);
        MOTILITYmitigationBias->setObjectName(QStringLiteral("MOTILITYmitigationBias"));

        MOTILITYMitigationBiasLayout->addWidget(MOTILITYmitigationBias);

        layoutWidget13 = new QWidget(motility_tab);
        layoutWidget13->setObjectName(QStringLiteral("layoutWidget13"));
        layoutWidget13->setGeometry(QRect(20, 240, 271, 21));
        MOTILITYDirectionLayout = new QHBoxLayout(layoutWidget13);
        MOTILITYDirectionLayout->setObjectName(QStringLiteral("MOTILITYDirectionLayout"));
        MOTILITYDirectionLayout->setContentsMargins(0, 0, 0, 0);
        MOTILITYdirectionLabel = new QLabel(layoutWidget13);
        MOTILITYdirectionLabel->setObjectName(QStringLiteral("MOTILITYdirectionLabel"));
        MOTILITYdirectionLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        MOTILITYDirectionLayout->addWidget(MOTILITYdirectionLabel);

        MOTILITYdirectionComboBox = new QComboBox(layoutWidget13);
        MOTILITYdirectionComboBox->setObjectName(QStringLiteral("MOTILITYdirectionComboBox"));

        MOTILITYDirectionLayout->addWidget(MOTILITYdirectionComboBox);

        MOTILITYchemotaxisLabel = new QLabel(motility_tab);
        MOTILITYchemotaxisLabel->setObjectName(QStringLiteral("MOTILITYchemotaxisLabel"));
        MOTILITYchemotaxisLabel->setGeometry(QRect(20, 170, 191, 31));
        MOTILITYchemotaxisLabel->setTextFormat(Qt::MarkdownText);
        MOTILITYenableChemotaxisCheckBox = new QCheckBox(motility_tab);
        MOTILITYenableChemotaxisCheckBox->setObjectName(QStringLiteral("MOTILITYenableChemotaxisCheckBox"));
        MOTILITYenableChemotaxisCheckBox->setGeometry(QRect(190, 180, 121, 17));
        widget = new QWidget(motility_tab);
        widget->setObjectName(QStringLiteral("widget"));
        widget->setGeometry(QRect(20, 210, 271, 22));
        MOTILITYSubstrateLayout = new QHBoxLayout(widget);
        MOTILITYSubstrateLayout->setObjectName(QStringLiteral("MOTILITYSubstrateLayout"));
        MOTILITYSubstrateLayout->setContentsMargins(0, 0, 0, 0);
        MOTILITYsubstrateLabel = new QLabel(widget);
        MOTILITYsubstrateLabel->setObjectName(QStringLiteral("MOTILITYsubstrateLabel"));

        MOTILITYSubstrateLayout->addWidget(MOTILITYsubstrateLabel);

        MOTILITYchemotaxisComboBox = new QComboBox(widget);
        MOTILITYchemotaxisComboBox->setObjectName(QStringLiteral("MOTILITYchemotaxisComboBox"));

        MOTILITYSubstrateLayout->addWidget(MOTILITYchemotaxisComboBox);

        cell_tab_widget->addTab(motility_tab, QString());
        secretion_tab = new QWidget();
        secretion_tab->setObjectName(QStringLiteral("secretion_tab"));
        QSizePolicy sizePolicy3(QSizePolicy::Ignored, QSizePolicy::Preferred);
        sizePolicy3.setHorizontalStretch(0);
        sizePolicy3.setVerticalStretch(0);
        sizePolicy3.setHeightForWidth(secretion_tab->sizePolicy().hasHeightForWidth());
        secretion_tab->setSizePolicy(sizePolicy3);
        secretion_substrate_0 = new QWidget(secretion_tab);
        secretion_substrate_0->setObjectName(QStringLiteral("secretion_substrate_0"));
        secretion_substrate_0->setGeometry(QRect(20, 20, 641, 171));
        secretion_substrate_0->setAutoFillBackground(true);
        SECRETIONsubstrateNameLabel0 = new QLabel(secretion_substrate_0);
        SECRETIONsubstrateNameLabel0->setObjectName(QStringLiteral("SECRETIONsubstrateNameLabel0"));
        SECRETIONsubstrateNameLabel0->setGeometry(QRect(270, 10, 91, 16));
        layoutWidget14 = new QWidget(secretion_substrate_0);
        layoutWidget14->setObjectName(QStringLiteral("layoutWidget14"));
        layoutWidget14->setGeometry(QRect(12, 42, 291, 24));
        SECRETIONSecretionRateLayout = new QHBoxLayout(layoutWidget14);
        SECRETIONSecretionRateLayout->setObjectName(QStringLiteral("SECRETIONSecretionRateLayout"));
        SECRETIONSecretionRateLayout->setContentsMargins(0, 0, 0, 0);
        SECRETIONsecretionRateLabel = new QLabel(layoutWidget14);
        SECRETIONsecretionRateLabel->setObjectName(QStringLiteral("SECRETIONsecretionRateLabel"));
        SECRETIONsecretionRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        SECRETIONSecretionRateLayout->addWidget(SECRETIONsecretionRateLabel);

        SECRETIONsecretionRate = new QLineEdit(layoutWidget14);
        SECRETIONsecretionRate->setObjectName(QStringLiteral("SECRETIONsecretionRate"));

        SECRETIONSecretionRateLayout->addWidget(SECRETIONsecretionRate);

        SECRETIONsecretionRateUnits = new QToolButton(layoutWidget14);
        SECRETIONsecretionRateUnits->setObjectName(QStringLiteral("SECRETIONsecretionRateUnits"));

        SECRETIONSecretionRateLayout->addWidget(SECRETIONsecretionRateUnits);

        layoutWidget15 = new QWidget(secretion_substrate_0);
        layoutWidget15->setObjectName(QStringLiteral("layoutWidget15"));
        layoutWidget15->setGeometry(QRect(12, 72, 291, 24));
        SECRETIONSecretionTargetLayout = new QHBoxLayout(layoutWidget15);
        SECRETIONSecretionTargetLayout->setObjectName(QStringLiteral("SECRETIONSecretionTargetLayout"));
        SECRETIONSecretionTargetLayout->setContentsMargins(0, 0, 0, 0);
        SECRETIONsecretionTargetLabel = new QLabel(layoutWidget15);
        SECRETIONsecretionTargetLabel->setObjectName(QStringLiteral("SECRETIONsecretionTargetLabel"));
        SECRETIONsecretionTargetLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        SECRETIONSecretionTargetLayout->addWidget(SECRETIONsecretionTargetLabel);

        SECRETIONsecretionTarget = new QLineEdit(layoutWidget15);
        SECRETIONsecretionTarget->setObjectName(QStringLiteral("SECRETIONsecretionTarget"));

        SECRETIONSecretionTargetLayout->addWidget(SECRETIONsecretionTarget);

        SECRETIONsecretionTargetUnits = new QToolButton(layoutWidget15);
        SECRETIONsecretionTargetUnits->setObjectName(QStringLiteral("SECRETIONsecretionTargetUnits"));

        SECRETIONSecretionTargetLayout->addWidget(SECRETIONsecretionTargetUnits);

        layoutWidget16 = new QWidget(secretion_substrate_0);
        layoutWidget16->setObjectName(QStringLiteral("layoutWidget16"));
        layoutWidget16->setGeometry(QRect(12, 102, 291, 24));
        SECRETIONUptakeRateLayout = new QHBoxLayout(layoutWidget16);
        SECRETIONUptakeRateLayout->setObjectName(QStringLiteral("SECRETIONUptakeRateLayout"));
        SECRETIONUptakeRateLayout->setContentsMargins(0, 0, 0, 0);
        SECRETIONuptakeRateLabel = new QLabel(layoutWidget16);
        SECRETIONuptakeRateLabel->setObjectName(QStringLiteral("SECRETIONuptakeRateLabel"));
        SECRETIONuptakeRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        SECRETIONUptakeRateLayout->addWidget(SECRETIONuptakeRateLabel);

        SECRETIONuptakeRate = new QLineEdit(layoutWidget16);
        SECRETIONuptakeRate->setObjectName(QStringLiteral("SECRETIONuptakeRate"));

        SECRETIONUptakeRateLayout->addWidget(SECRETIONuptakeRate);

        SECRETIONUptakeRateUnits = new QToolButton(layoutWidget16);
        SECRETIONUptakeRateUnits->setObjectName(QStringLiteral("SECRETIONUptakeRateUnits"));

        SECRETIONUptakeRateLayout->addWidget(SECRETIONUptakeRateUnits);

        layoutWidget17 = new QWidget(secretion_substrate_0);
        layoutWidget17->setObjectName(QStringLiteral("layoutWidget17"));
        layoutWidget17->setGeometry(QRect(12, 132, 291, 24));
        SECRETIONNetExportRateLayout = new QHBoxLayout(layoutWidget17);
        SECRETIONNetExportRateLayout->setObjectName(QStringLiteral("SECRETIONNetExportRateLayout"));
        SECRETIONNetExportRateLayout->setContentsMargins(0, 0, 0, 0);
        SECRETIONnetExportRateLabel = new QLabel(layoutWidget17);
        SECRETIONnetExportRateLabel->setObjectName(QStringLiteral("SECRETIONnetExportRateLabel"));
        SECRETIONnetExportRateLabel->setStyleSheet(QStringLiteral("font: 8pt \"MS Shell Dlg 2\";"));

        SECRETIONNetExportRateLayout->addWidget(SECRETIONnetExportRateLabel);

        SECRETIONnetExportRate = new QLineEdit(layoutWidget17);
        SECRETIONnetExportRate->setObjectName(QStringLiteral("SECRETIONnetExportRate"));

        SECRETIONNetExportRateLayout->addWidget(SECRETIONnetExportRate);

        SECRETIONnetExportRateUnits = new QToolButton(layoutWidget17);
        SECRETIONnetExportRateUnits->setObjectName(QStringLiteral("SECRETIONnetExportRateUnits"));

        SECRETIONNetExportRateLayout->addWidget(SECRETIONnetExportRateUnits);

        cell_tab_widget->addTab(secretion_tab, QString());
        cellNameLabel = new QLabel(cell_definitions_page);
        cellNameLabel->setObjectName(QStringLiteral("cellNameLabel"));
        cellNameLabel->setGeometry(QRect(180, 60, 47, 21));
        newCellButton = new QPushButton(cell_definitions_page);
        newCellButton->setObjectName(QStringLiteral("newCellButton"));
        newCellButton->setGeometry(QRect(20, 10, 91, 23));
        cloneCellButton = new QPushButton(cell_definitions_page);
        cloneCellButton->setObjectName(QStringLiteral("cloneCellButton"));
        cloneCellButton->setGeometry(QRect(120, 10, 91, 23));
        removeCellButton = new QPushButton(cell_definitions_page);
        removeCellButton->setObjectName(QStringLiteral("removeCellButton"));
        removeCellButton->setGeometry(QRect(574, 10, 101, 23));
        cellName = new QLineEdit(cell_definitions_page);
        cellName->setObjectName(QStringLiteral("cellName"));
        cellName->setGeometry(QRect(220, 60, 161, 20));
        pages_widget->addWidget(cell_definitions_page);
        MainWindow->setCentralWidget(centralwidget);
        menubar = new QMenuBar(MainWindow);
        menubar->setObjectName(QStringLiteral("menubar"));
        menubar->setGeometry(QRect(0, 0, 919, 21));
        menuFile = new QMenu(menubar);
        menuFile->setObjectName(QStringLiteral("menuFile"));
        menuNew = new QMenu(menuFile);
        menuNew->setObjectName(QStringLiteral("menuNew"));
        menuEdit = new QMenu(menubar);
        menuEdit->setObjectName(QStringLiteral("menuEdit"));
        menuView = new QMenu(menubar);
        menuView->setObjectName(QStringLiteral("menuView"));
        MainWindow->setMenuBar(menubar);
        statusbar = new QStatusBar(MainWindow);
        statusbar->setObjectName(QStringLiteral("statusbar"));
        MainWindow->setStatusBar(statusbar);

        menubar->addAction(menuFile->menuAction());
        menubar->addAction(menuEdit->menuAction());
        menubar->addAction(menuView->menuAction());
        menuFile->addAction(menuNew->menuAction());
        menuFile->addAction(actionLoad);
        menuFile->addSeparator();
        menuFile->addAction(actionSave);
        menuNew->addAction(action2D);
        menuNew->addAction(action3D);
        menuView->addAction(actionXML_Out);

        retranslateUi(MainWindow);

        pages_widget->setCurrentIndex(1);
        cell_tab_widget->setCurrentIndex(4);
        cycle_phase_tab_widget->setCurrentIndex(0);
        deathA_phase_tab_widget->setCurrentIndex(0);
        deathN_phase_tab_widget->setCurrentIndex(1);
        mechanics_phase_tab_widget->setCurrentIndex(0);


        QMetaObject::connectSlotsByName(MainWindow);
    } // setupUi

    void retranslateUi(QMainWindow *MainWindow)
    {
        MainWindow->setWindowTitle(QApplication::translate("MainWindow", "MainWindow", Q_NULLPTR));
        actionNew_Substrate->setText(QApplication::translate("MainWindow", "New Substrate", Q_NULLPTR));
        actionLoad->setText(QApplication::translate("MainWindow", "Load", Q_NULLPTR));
        actionSave->setText(QApplication::translate("MainWindow", "Save", Q_NULLPTR));
        actionExport_to_XML->setText(QApplication::translate("MainWindow", "Export to XML", Q_NULLPTR));
        actionLink->setText(QApplication::translate("MainWindow", "Microenvironments", Q_NULLPTR));
        actionCell_Definitions->setText(QApplication::translate("MainWindow", "Cell Definitions", Q_NULLPTR));
        actionXML_Out->setText(QApplication::translate("MainWindow", "XML Out", Q_NULLPTR));
        action2D->setText(QApplication::translate("MainWindow", "2D", Q_NULLPTR));
        action3D->setText(QApplication::translate("MainWindow", "3D", Q_NULLPTR));
        QTreeWidgetItem *___qtreewidgetitem = outline->headerItem();
        ___qtreewidgetitem->setText(0, QApplication::translate("MainWindow", "New Config", Q_NULLPTR));

        const bool __sortingEnabled = outline->isSortingEnabled();
        outline->setSortingEnabled(false);
        QTreeWidgetItem *___qtreewidgetitem1 = outline->topLevelItem(0);
        ___qtreewidgetitem1->setText(0, QApplication::translate("MainWindow", "Microenvironment", Q_NULLPTR));
        QTreeWidgetItem *___qtreewidgetitem2 = outline->topLevelItem(1);
        ___qtreewidgetitem2->setText(0, QApplication::translate("MainWindow", "Cell Definitions", Q_NULLPTR));
        outline->setSortingEnabled(__sortingEnabled);

        dirichletBoundaryLabel->setText(QApplication::translate("MainWindow", "Dirichlet Boundary", Q_NULLPTR));
        initialConditionLabel->setText(QApplication::translate("MainWindow", "Initial Condition", Q_NULLPTR));
        decayRateLabel->setText(QApplication::translate("MainWindow", "Decay Rate", Q_NULLPTR));
        diffusionCoefficientLabel->setText(QApplication::translate("MainWindow", "Diffusion Coefficient", Q_NULLPTR));
        dirichletBoundaryCheckBox->setText(QString());
        diffusionCoefficient->setPlaceholderText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        decayRate->setPlaceholderText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        initialCondition->setPlaceholderText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        dirchletBoundary->setPlaceholderText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        advancedBoundaryLabel->setText(QApplication::translate("MainWindow", "Advanced Boundary", Q_NULLPTR));
        xMaximumLabel->setText(QApplication::translate("MainWindow", "X Maximum", Q_NULLPTR));
        xMinimumLabel->setText(QApplication::translate("MainWindow", "X Minimum", Q_NULLPTR));
        yMaximumLabel->setText(QApplication::translate("MainWindow", "Y Maximum", Q_NULLPTR));
        yMinimumLabel->setText(QApplication::translate("MainWindow", "Y Minimum", Q_NULLPTR));
        xMaximum->setPlaceholderText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        xMinimum->setPlaceholderText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        yMaximum->setPlaceholderText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        yMinimum->setPlaceholderText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        xMaximumCheckBox->setText(QString());
        xMinimumCheckBox->setText(QString());
        yMaximumCheckBox->setText(QString());
        yMinimumCheckBox->setText(QString());
        diffusionCoefficientUnits->setText(QApplication::translate("MainWindow", "micron^2/min", Q_NULLPTR));
        decayRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        Name->setPlaceholderText(QApplication::translate("MainWindow", "Default", Q_NULLPTR));
        nameLabel->setText(QApplication::translate("MainWindow", "Name", Q_NULLPTR));
        New->setText(QApplication::translate("MainWindow", "New Substrate", Q_NULLPTR));
        Clone->setText(QApplication::translate("MainWindow", "Clone Substrate", Q_NULLPTR));
        Remove->setText(QApplication::translate("MainWindow", "Remove Substrate", Q_NULLPTR));
        CYCLEnameLabel->setText(QApplication::translate("MainWindow", "Cycle Name", Q_NULLPTR));
        CYCLEname->setText(QApplication::translate("MainWindow", "Default", Q_NULLPTR));
        cycle_phase_tab_widget->setTabText(cycle_phase_tab_widget->indexOf(cycle_phase_duration_tab), QApplication::translate("MainWindow", "Phase as Durations", Q_NULLPTR));
        cycle_phase_tab_widget->setTabText(cycle_phase_tab_widget->indexOf(cycle_phase_transition_tab), QApplication::translate("MainWindow", "Phase as Transitions", Q_NULLPTR));
        CYCLEmodel->clear();
        CYCLEmodel->insertItems(0, QStringList()
         << QApplication::translate("MainWindow", "Select a Model", Q_NULLPTR)
         << QApplication::translate("MainWindow", "advanced_Ki67_cycle_model", Q_NULLPTR)
         << QApplication::translate("MainWindow", "basic_Ki67_cycle_model", Q_NULLPTR)
         << QApplication::translate("MainWindow", "flow_cytometry_cycle_model", Q_NULLPTR)
         << QApplication::translate("MainWindow", "live_apoptotic_cycle_model", Q_NULLPTR)
         << QApplication::translate("MainWindow", "total_cells_cycle_model", Q_NULLPTR)
         << QApplication::translate("MainWindow", "live_cells_cycle_model", Q_NULLPTR)
         << QApplication::translate("MainWindow", "flow_cytometry_separated_cycle_model", Q_NULLPTR)
         << QApplication::translate("MainWindow", "cycling_quiescent_model", Q_NULLPTR)
        );
        cell_tab_widget->setTabText(cell_tab_widget->indexOf(cycle_tab), QApplication::translate("MainWindow", "Cycle", Q_NULLPTR));
        DEATHAcalcificationRateLabel->setText(QApplication::translate("MainWindow", "Calcification Rate", Q_NULLPTR));
        DEATHAcalcificationRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHAcalcificationRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHArelativeRuptureVolumeLabel->setText(QApplication::translate("MainWindow", "Relative Rupture Volume", Q_NULLPTR));
        DEATHArelativeRuptureVolume->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHAdeathRateLabel->setText(QApplication::translate("MainWindow", "Death Rate", Q_NULLPTR));
        DEATHAdeathRateField->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHAdeathRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHAphase0Duration->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHAphase0DurationLabel->setText(QApplication::translate("MainWindow", "Phase 0", Q_NULLPTR));
        DEATHAphase0DurationCheckBox->setText(QApplication::translate("MainWindow", "Fixed", Q_NULLPTR));
        DEATHAphase0DurationUnits->setText(QApplication::translate("MainWindow", "min", Q_NULLPTR));
        deathA_phase_tab_widget->setTabText(deathA_phase_tab_widget->indexOf(deathA_phase_duration_tab), QApplication::translate("MainWindow", "Phase as Durations", Q_NULLPTR));
        DEATHAphase0TransitionLabel->setText(QApplication::translate("MainWindow", "Phase 0 -> 1", Q_NULLPTR));
        DEATHAphase0TransitionCheckBox->setText(QApplication::translate("MainWindow", "Fixed", Q_NULLPTR));
        DEATHAphase0TransitionUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        deathA_phase_tab_widget->setTabText(deathA_phase_tab_widget->indexOf(deathA_phase_transition_tab), QApplication::translate("MainWindow", "Phase as Transitions", Q_NULLPTR));
        DEATHAunlysedFluidChangeRateLabel->setText(QApplication::translate("MainWindow", "Unlysed Fluid Change Rate", Q_NULLPTR));
        DEATHAunlysedFluidChangeRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHAunlysedFluidChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHAnuclearBiomassChangeRateLabel->setText(QApplication::translate("MainWindow", "Nuclear Biomass Change Rate", Q_NULLPTR));
        DEATHAnuclearBiomassChangeRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHAnuclearBiomassChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHAlysedFluidChangeRateLabel->setText(QApplication::translate("MainWindow", "Lysed Fluid Change Rate", Q_NULLPTR));
        DEATHAlysedFluidChangeRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHAlysedFluidChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHapoptosisLabel->setText(QApplication::translate("MainWindow", "# Apoptosis Model", Q_NULLPTR));
        DEATHAcytoplasmicBiomassChangeRateLabel->setText(QApplication::translate("MainWindow", "Cytoplasmic Biomass Change Rate", Q_NULLPTR));
        DEATHAcytoplasmicBiomassChangeRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHAcytoplasmicBiomassChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHAnameLabel->setText(QApplication::translate("MainWindow", "Name", Q_NULLPTR));
        DEATHAname->setText(QApplication::translate("MainWindow", "Apoptosis", Q_NULLPTR));
        DEATHNphase0DurationUnits->setText(QApplication::translate("MainWindow", "min", Q_NULLPTR));
        DEATHNphase0DurationLabel->setText(QApplication::translate("MainWindow", "Phase 0", Q_NULLPTR));
        DEATHNphase0Duration->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNphase0DurationCheckBox->setText(QApplication::translate("MainWindow", "Fixed", Q_NULLPTR));
        DEATHNphase1DurationLabel->setText(QApplication::translate("MainWindow", "Phase 1", Q_NULLPTR));
        DEATHNphase1Duration->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNphase1DurationCheckBox->setText(QApplication::translate("MainWindow", "Fixed", Q_NULLPTR));
        DEATHNphase1DurationUnits->setText(QApplication::translate("MainWindow", "min", Q_NULLPTR));
        deathN_phase_tab_widget->setTabText(deathN_phase_tab_widget->indexOf(deathN_phase_duration_tab), QApplication::translate("MainWindow", "Phase as Durations", Q_NULLPTR));
        DEATHNphase0TransitionUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHNphase0TransitionCheckBox->setText(QApplication::translate("MainWindow", "Fixed", Q_NULLPTR));
        DEATHNphase0TransitionLabel->setText(QApplication::translate("MainWindow", "Phase 0 -> 1", Q_NULLPTR));
        DEATHNphase1TransitionLabel->setText(QApplication::translate("MainWindow", "Phase 1 -> 2", Q_NULLPTR));
        DEATHNphase1TransitionCheckBox->setText(QApplication::translate("MainWindow", "Fixed", Q_NULLPTR));
        DEATHNphase1TransitionUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        deathN_phase_tab_widget->setTabText(deathN_phase_tab_widget->indexOf(deathN_phase_transition_tab), QApplication::translate("MainWindow", "Phase as Transitions", Q_NULLPTR));
        DEATHNlysedFluidChangeRateLabel->setText(QApplication::translate("MainWindow", "Lysed Fluid Change Rate", Q_NULLPTR));
        DEATHNlysedFluidChangeRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNlysedFluidChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHNunlysedFluidChangeRateLabel->setText(QApplication::translate("MainWindow", "Unlysed Fluid Change Rate", Q_NULLPTR));
        DEATHNunlysedFluidChangeRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNunlysedFluidChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHNdeathRateLabel->setText(QApplication::translate("MainWindow", "Death Rate", Q_NULLPTR));
        DEATHNdeathRateField->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNdeathRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHNcytoplasmicBiomassChangeRateLabel->setText(QApplication::translate("MainWindow", "Cytoplasmic Biomass Change Rate", Q_NULLPTR));
        DEATHNcytoplasmicBiomassChangeRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNcytoplasmicBiomassChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHNrelativeRuptureVolumeLabel->setText(QApplication::translate("MainWindow", "Relative Rupture Volume", Q_NULLPTR));
        DEATHNrelativeRuptureVolume->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNnameLabel->setText(QApplication::translate("MainWindow", "Name", Q_NULLPTR));
        DEATHNname->setText(QApplication::translate("MainWindow", "Necrosis", Q_NULLPTR));
        DEATHNcalcificationRateLabel->setText(QApplication::translate("MainWindow", "Calcification Rate", Q_NULLPTR));
        DEATHNcalcificationRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNcalcificationRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        DEATHnecrosisLabel->setText(QApplication::translate("MainWindow", "# Necrosis Model", Q_NULLPTR));
        DEATHNnuclearBiomassChangeRateLabel->setText(QApplication::translate("MainWindow", "Nuclear Biomass Change Rate", Q_NULLPTR));
        DEATHNnuclearBiomassChangeRate->setText(QApplication::translate("MainWindow", "0", Q_NULLPTR));
        DEATHNnuclearBiomassChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        cell_tab_widget->setTabText(cell_tab_widget->indexOf(death_tab), QApplication::translate("MainWindow", "Death", Q_NULLPTR));
        VOLUMEfluidFractionLabel->setText(QApplication::translate("MainWindow", "Fluid Fraction", Q_NULLPTR));
        VOLUMEcalcifiedFractionLabel->setText(QApplication::translate("MainWindow", "Calcified Fraction", Q_NULLPTR));
        VOLUMErelativeRuptureVolumeLabel->setText(QApplication::translate("MainWindow", "Relative Rupture Volume", Q_NULLPTR));
        VOLUMEtotalVolumeLabel->setText(QApplication::translate("MainWindow", "Total Volume", Q_NULLPTR));
        VOLUMEtotalVolumeUnits->setText(QApplication::translate("MainWindow", "um^3", Q_NULLPTR));
        VOLUMEnuclearVolumeLabel->setText(QApplication::translate("MainWindow", "Nuclear Volume", Q_NULLPTR));
        VOLUMEnuclearVolumeUnits->setText(QApplication::translate("MainWindow", "um^3", Q_NULLPTR));
        VOLUMEcalcificationRateLabel->setText(QApplication::translate("MainWindow", "Calcification Rate", Q_NULLPTR));
        VOLUMEcalcificationRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        VOLUMEfluidChangeRateLabel->setText(QApplication::translate("MainWindow", "Fluid Change Rate", Q_NULLPTR));
        VOLUMEfluidChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        VOLUMEcytoplasmicBiomassChangeRateLabel->setText(QApplication::translate("MainWindow", "Cytoplasmic Biomass Change Rate", Q_NULLPTR));
        VOLUMEcytoplasmicBiomassChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        VOLUMEnuclearBiomassChangeRateLabel->setText(QApplication::translate("MainWindow", "Nuclear Biomass Change Rate", Q_NULLPTR));
        VOLUMEnuclearBiomassChangeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        cell_tab_widget->setTabText(cell_tab_widget->indexOf(volume_tab), QApplication::translate("MainWindow", "Volume", Q_NULLPTR));
        MECHANICSrelativeMaximumAdhesionStrengthLabel->setText(QApplication::translate("MainWindow", "Relative Maximum Adhesion Strength", Q_NULLPTR));
        MECHANICSrelativeEquilibriumDistanceLabel->setText(QApplication::translate("MainWindow", "Set Relative Equilibrium Distance", Q_NULLPTR));
        mechanics_phase_tab_widget->setTabText(mechanics_phase_tab_widget->indexOf(mechanics_relative_equilibrium_distance_tab), QApplication::translate("MainWindow", "Relative Equilibrium Distance", Q_NULLPTR));
        MECHANICSabsoluteEquilibriumDistanceLabel->setText(QApplication::translate("MainWindow", "Set Abs. Equilibrium Distance", Q_NULLPTR));
        MECHANICSabsoluteEquilibriumDistanceUnits->setText(QApplication::translate("MainWindow", "um", Q_NULLPTR));
        mechanics_phase_tab_widget->setTabText(mechanics_phase_tab_widget->indexOf(mechanics_absolute_equilibrium_distance_tab), QApplication::translate("MainWindow", "Absolute Equilibrium Distance", Q_NULLPTR));
        MECHANICScellAdhesionStrengthLabel->setText(QApplication::translate("MainWindow", "Cell Adhesion Strength", Q_NULLPTR));
        MECHANICScellAdhesionStrengthUnits->setText(QApplication::translate("MainWindow", "um/min", Q_NULLPTR));
        MECHANICScellRepulsionStrengthLabel->setText(QApplication::translate("MainWindow", "Cell Repulsion Strength", Q_NULLPTR));
        MECHANICScellRepulsionStrengtUnits->setText(QApplication::translate("MainWindow", "um/min", Q_NULLPTR));
        cell_tab_widget->setTabText(cell_tab_widget->indexOf(mechanics_tab), QApplication::translate("MainWindow", "Mechanics", Q_NULLPTR));
        MOTILITYenableCheckBox->setText(QApplication::translate("MainWindow", "Enable Motility", Q_NULLPTR));
        MOTILITYuse2dCheckBox->setText(QApplication::translate("MainWindow", "Use 2D", Q_NULLPTR));
        MOTILITYspeedLabel->setText(QApplication::translate("MainWindow", "Speed", Q_NULLPTR));
        MOTILITYspeedUnits->setText(QApplication::translate("MainWindow", "um/min", Q_NULLPTR));
        MOTILITYpersistenceTimeLabel->setText(QApplication::translate("MainWindow", "Persistence Time", Q_NULLPTR));
        MOTILITYpersistenceTimeUnits->setText(QApplication::translate("MainWindow", "min", Q_NULLPTR));
        MOTILITYmitigationBiasLabel->setText(QApplication::translate("MainWindow", "Mitigation Bias", Q_NULLPTR));
        MOTILITYdirectionLabel->setText(QApplication::translate("MainWindow", "Direction", Q_NULLPTR));
        MOTILITYdirectionComboBox->clear();
        MOTILITYdirectionComboBox->insertItems(0, QStringList()
         << QApplication::translate("MainWindow", "Towards Gradient", Q_NULLPTR)
         << QApplication::translate("MainWindow", "Against Gradient", Q_NULLPTR)
        );
        MOTILITYchemotaxisLabel->setText(QApplication::translate("MainWindow", "# CHEMOTAXIS", Q_NULLPTR));
        MOTILITYenableChemotaxisCheckBox->setText(QApplication::translate("MainWindow", "Enable Chemotaxis", Q_NULLPTR));
        MOTILITYsubstrateLabel->setText(QApplication::translate("MainWindow", "Substrate", Q_NULLPTR));
        cell_tab_widget->setTabText(cell_tab_widget->indexOf(motility_tab), QApplication::translate("MainWindow", "Motility", Q_NULLPTR));
        SECRETIONsubstrateNameLabel0->setText(QApplication::translate("MainWindow", "SUBSTRATE-NAME", Q_NULLPTR));
        SECRETIONsecretionRateLabel->setText(QApplication::translate("MainWindow", "Secreation Rate", Q_NULLPTR));
        SECRETIONsecretionRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        SECRETIONsecretionTargetLabel->setText(QApplication::translate("MainWindow", "Secretion Target", Q_NULLPTR));
        SECRETIONsecretionTargetUnits->setText(QApplication::translate("MainWindow", "Substrate Density", Q_NULLPTR));
        SECRETIONuptakeRateLabel->setText(QApplication::translate("MainWindow", "Uptake Rate", Q_NULLPTR));
        SECRETIONuptakeRate->setText(QString());
        SECRETIONUptakeRateUnits->setText(QApplication::translate("MainWindow", "1/min", Q_NULLPTR));
        SECRETIONnetExportRateLabel->setText(QApplication::translate("MainWindow", "Net Export Rate", Q_NULLPTR));
        SECRETIONnetExportRate->setText(QString());
        SECRETIONnetExportRateUnits->setText(QApplication::translate("MainWindow", "Total Substrate/min", Q_NULLPTR));
        cell_tab_widget->setTabText(cell_tab_widget->indexOf(secretion_tab), QApplication::translate("MainWindow", "Secretion", Q_NULLPTR));
        cellNameLabel->setText(QApplication::translate("MainWindow", "Name", Q_NULLPTR));
        newCellButton->setText(QApplication::translate("MainWindow", "New Cell", Q_NULLPTR));
        cloneCellButton->setText(QApplication::translate("MainWindow", "Clone Cell", Q_NULLPTR));
        removeCellButton->setText(QApplication::translate("MainWindow", "Remove Cell", Q_NULLPTR));
        cellName->setText(QApplication::translate("MainWindow", "Default", Q_NULLPTR));
        menuFile->setTitle(QApplication::translate("MainWindow", "File", Q_NULLPTR));
        menuNew->setTitle(QApplication::translate("MainWindow", "New", Q_NULLPTR));
        menuEdit->setTitle(QApplication::translate("MainWindow", "Edit", Q_NULLPTR));
        menuView->setTitle(QApplication::translate("MainWindow", "View", Q_NULLPTR));
    } // retranslateUi

};

namespace Ui {
    class MainWindow: public Ui_MainWindow {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINWINDOW_H
