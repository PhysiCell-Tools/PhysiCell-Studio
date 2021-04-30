#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <microenvironment.h>
#include <cell.h>
#include <QTreeWidgetItem>
#include <QGridLayout>
#include <QCheckBox>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

    QVector<microenvironment> substrates; //List of substrates
    QTreeWidgetItem *environmentIndex; //Used to hold the pointer to the Microenvironment item in the Outline. Used to add more substrates
    int currentSub = 0; //Index of the substrate currently shown on screen

    //Cell equivalents of the substrates variables above
    QVector<cell> cells;
    QTreeWidgetItem *cellIndex;
    int currentCell = 0;

    //Line Edit objects for the dynamic phases. Both durations and transitions
    QVector<QLineEdit *> CPDLineEdits;
    QVector<QLineEdit *> CPTLineEdits;

    //Check Box objects for the dynamic phases
    QVector<QCheckBox *> CPDCheckBoxes;
    QVector<QCheckBox *> CPTCheckBoxes;

private slots:
    void save();

    void load();

    void loadValues(int n);

    void loadNew(int n);

    void checkName(QString name, int n);

    void on_Name_textEdited(const QString &arg1);

    void on_diffusionCoefficient_textEdited(const QString &arg1);

    void on_decayRate_textEdited(const QString &arg1);

    void on_initialCondition_textEdited(const QString &arg1);

    void on_outline_itemClicked(QTreeWidgetItem *item, int column);

    void on_New_clicked();

    void on_Clone_clicked();

    void on_Remove_clicked();

    void on_cellName_textEdited(const QString &arg1);

    void on_newCellButton_clicked();

    void on_cloneCellButton_clicked();

    void on_removeCellButton_clicked();

    void on_CYCLEname_textEdited(const QString &arg1);

    void on_CYCLEmodel_currentIndexChanged(int index);

    void getPhaseDuration();

    void getPhaseTransition();

    void checkFixedDuration();

    void checkFixedTransition();

    // Volume

    void on_VOLUMEtotalVolume_textEdited(const QString &arg1);

    void on_VOLUMEnuclearVolume_textEdited(const QString &arg1);

    void on_VOLUMEfluidFraction_textEdited(const QString &arg1);

    void on_VOLUMErelativeRuptureVolume_textEdited(const QString &arg1);

    void on_VOLUMEnuclearBiomassChangeRate_textEdited(const QString &arg1);

    void on_VOLUMEcytoplasmicBiomassChangeRate_textEdited(const QString &arg1);

    void on_VOLUMEfluidChangeRate_textEdited(const QString &arg1);

    void on_VOLUMEcalcifiedFraction_textEdited(const QString &arg1);

    void on_VOLUMEcalcificationRate_textEdited(const QString &arg1);

    // MECHANICS

    void on_MECHANICScellAdhesionStrength_textEdited(const QString &arg1);

    void on_MECHANICScellRepulsionStrength_textEdited(const QString &arg1);

    void on_MECHANICSrelativeMaximumAdhesionStrength_textEdited(const QString &arg1);

    // MOTILITY

    void on_MOTILITYspeed_textEdited(const QString &arg1);

    void on_MOTILITYpersistenceTime_textEdited(const QString &arg1);

    void on_MOTILITYmitigationBias_textEdited(const QString &arg1);

    void on_MOTILITYenableCheckBox_toggled(bool arg1);

    void on_MOTILITYenableChemotaxisCheckBox_toggled(bool arg1);

    void on_MOTILITYuse2dCheckBox_toggled(bool arg1);

    void on_MOTILITYchemotaxisComboBox_currentIndexChanged(int i);

    void on_MOTILITYdirectionComboBox_currentIndexChanged(int i);

    //DEATH

    void on_DEATHAname_textEdited(const QString &arg1);

    void on_DEATHAdeathRateField_textEdited(const QString &arg1);

    void on_DEATHAunlysedFluidChangeRate_textEdited(const QString &arg1);

    void on_DEATHAlysedFluidChangeRate_textEdited(const QString &arg1);

    void on_DEATHAcytoplasmicBiomassChangeRate_textEdited(const QString &arg1);

    void on_DEATHAnuclearBiomassChangeRate_textEdited(const QString &arg1);

    void on_DEATHAcalcificationRate_textEdited(const QString &arg1);

    void on_DEATHArelativeRuptureVolume_textEdited(const QString &arg1);

    void on_DEATHAphase0Duration_textEdited(const QString &arg1);

    void on_DEATHAphase0DurationCheckBox_toggled(bool checked);

    void on_DEATHAphase0Transition_textEdited(const QString &arg1);

    void on_DEATHAphase0TransitionCheckBox_toggled(bool checked);

    void on_DEATHNname_textEdited(const QString &arg1);

    void on_DEATHNdeathRateField_textEdited(const QString &arg1);

    void on_DEATHNunlysedFluidChangeRate_textEdited(const QString &arg1);

    void on_DEATHNlysedFluidChangeRate_textEdited(const QString &arg1);

    void on_DEATHNcytoplasmicBiomassChangeRate_textEdited(const QString &arg1);

    void on_DEATHNnuclearBiomassChangeRate_textEdited(const QString &arg1);

    void on_DEATHNcalcificationRate_textEdited(const QString &arg1);

    void on_DEATHNrelativeRuptureVolume_textEdited(const QString &arg1);

    void on_DEATHNphase0Duration_textEdited(const QString &arg1);

    void on_DEATHNphase1Duration_textEdited(const QString &arg1);

    void on_DEATHNphase0DurationCheckBox_toggled(bool checked);

    void on_DEATHNphase1DurationCheckBox_toggled(bool checked);

    void on_DEATHNphase0Transition_textEdited(const QString &arg1);

    void on_DEATHNphase1Transition_textEdited(const QString &arg1);

    void on_DEATHNphase0TransitionCheckBox_toggled(bool checked);

    void on_DEATHNphase1TransitionCheckBox_toggled(bool checked);

private:
    Ui::MainWindow *ui;
};
#endif // MAINWINDOW_H
