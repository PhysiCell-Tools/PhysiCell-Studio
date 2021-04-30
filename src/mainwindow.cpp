#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QFile>
#include <QXmlStreamWriter>
#include <QDebug>
#include <QMessageBox>
#include <QFileDialog>
MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    //Setting up menu actions
    connect(ui->actionSave, SIGNAL(triggered()), this, SLOT(save()));
    connect(ui->actionLoad, SIGNAL(triggered()), this, SLOT(load()));

    //Setting up default substrate, eventually do the same with cell definitions
    currentSub = 0;
    microenvironment sub0 = microenvironment(currentSub);
    substrates.append(sub0);

    currentCell = 0;
    cell cell0 = cell(currentCell);
    cells.append(cell0);

    //Add object to represent the default substrate
    environmentIndex = ui->outline->findItems("Microenvironment",Qt::MatchExactly,0)[0];
    environmentIndex->addChild(new QTreeWidgetItem(0));
    environmentIndex->child(0)->setText(0, substrates[currentSub].name);

    //Add default cell definition
    cellIndex = ui->outline->findItems("Cell Definitions", Qt::MatchExactly,0)[0];
    cellIndex->addChild(new QTreeWidgetItem(0));
    cellIndex->child(0)->setText(0, cells[currentCell].name);
}

MainWindow::~MainWindow()
{
    delete ui;
}

//Save the XML file to output.txt
//Uses QXmlStreamWriter to format in XML
void MainWindow::save()
{
    QFile data(QFileDialog::getSaveFileName());
    if (!data.open(QIODevice::WriteOnly | QIODevice::Text)){
        qDebug() << "Whelp"; //Sanity check
        return;
    }

    QXmlStreamWriter output;
    output.setDevice(&data);
    output.setAutoFormatting(true);
    output.writeStartDocument();

    //This section writes all the different substrates in XML format
    output.writeStartElement("microenvironment_setup");
    int i;
    for(i = 0;i < substrates.size(); i++){
        output.writeStartElement("variable");
        output.writeAttribute("name", substrates[i].name);
        output.writeAttribute("ID", QString::number(substrates[i].id));
        output.writeStartElement("physical_parameter_set");
        output.writeTextElement("diffusion_coefficient", QString::number(substrates[i].diffCoeff));
        output.writeTextElement("decay_rate", QString::number(substrates[i].decayR));
        output.writeEndElement();
        output.writeTextElement("initial_condition", QString::number(substrates[i].initialC));
        output.writeStartElement("Dirichlet_boundary_condition");
        output.writeAttribute("enabled", "false");
        output.writeCharacters(QString::number(substrates[i].dirch[0][0]));
        output.writeEndElement();
        output.writeEndElement();
    }
    //end of microenvironment section

    output.writeEndDocument();

    qDebug() << "Yay"; //Sanity check
}

void MainWindow::load()
{
    QFile file(QFileDialog::getOpenFileName());
    if(!file.open(QIODevice::ReadOnly)) {
        QMessageBox::information(0, "error", file.errorString());
    }
    QXmlStreamReader reader(&file);
    while(substrates.size() > 0) {
        substrates.remove(0);
        environmentIndex->removeChild(environmentIndex->child(0));
    }

    if (reader.readNextStartElement()) {
        if (reader.name().toString() == "microenvironment_setup"){
            while(reader.readNextStartElement()){
                if(reader.name().toString() == "variable"){
                    microenvironment newSub = microenvironment(substrates.size());
                    currentSub = substrates.size();
                    substrates.append(newSub);
                    environmentIndex->addChild(new QTreeWidgetItem(0));
                    environmentIndex->child(currentSub)->setText(0, substrates[currentSub].name);
                    QXmlStreamAttributes attr = reader.attributes();
                    on_Name_textEdited(attr.value("name").toString());
                    while(reader.readNextStartElement()){
                        if(reader.name().toString() == "physical_parameter_set"){
                            while(reader.readNextStartElement()){
                                if(reader.name().toString() == "diffusion_coefficient"){
                                    QString s = reader.readElementText();
                                    on_diffusionCoefficient_textEdited(s.toLatin1());
                                } else if(reader.name().toString() == "decay_rate"){
                                    QString s = reader.readElementText();
                                    on_decayRate_textEdited(s.toLatin1());
                                }
                            }
                        } else if(reader.name().toString() == "initial_condition"){
                            QString s = reader.readElementText();
                            on_initialCondition_textEdited(s.toLatin1());
                        }
                        else
                            reader.skipCurrentElement();
                    }
                }
                else
                    reader.skipCurrentElement();
            }
        }
        
        else
            reader.raiseError(QObject::tr("Incorrect file"));
    }
    loadValues(1);
}
//Loads the values of the current substrate or cell definition into the text fields to then be edited by the user
void MainWindow::loadValues(int n)
{
    if (n == 0){
        ui->Name->setText(substrates[currentSub].name);
        ui->diffusionCoefficient->setText(QString::number(substrates[currentSub].diffCoeff));
        ui->decayRate->setText(QString::number(substrates[currentSub].decayR));
        ui->initialCondition->setText(QString::number(substrates[currentSub].initialC));
    }
    else if (n == 1){
        // cycle
        ui->cellName->setText(cells[currentCell].name);
        ui->CYCLEname->setText(cells[currentCell].cycleName);
        ui->CYCLEmodel->setCurrentIndex(cells[currentCell].cycleID + 1);
        for(int c = 0; c < cells[currentCell].numCyclePhases; c++){
           CPDLineEdits[c]->setText(QString::number(cells[currentCell].cyclePhases[c].duration));
           CPDCheckBoxes[c]->setChecked(cells[currentCell].cyclePhases[c].fixedDuration);
        }
        for(int c = 0; c < cells[currentCell].numCyclePhases; c++){
            CPTLineEdits[c]->setText(QString::number(cells[currentCell].cyclePhases[c].transition));
            CPTCheckBoxes[c]->setChecked(cells[currentCell].cyclePhases[c].fixedTransition);
        }
        // death - need to set values for each of the death models there are
            ui->DEATHAunlysedFluidChangeRate->setText(QString::number(cells[currentCell].apoptosis.deathUnlysedFluidChangeRate));
            ui->DEATHAlysedFluidChangeRate->setText(QString::number(cells[currentCell].apoptosis.deathLysedFluidChangeRate));
            ui->DEATHAcytoplasmicBiomassChangeRate->setText(QString::number(cells[currentCell].apoptosis.deathCytoplasmicBiomassChangeRate));
            ui->DEATHAnuclearBiomassChangeRate->setText(QString::number(cells[currentCell].apoptosis.deathNuclearBiomassChangeRate));
            ui->DEATHAcalcificationRate->setText(QString::number(cells[currentCell].apoptosis.deathCalcificationRate));
            ui->DEATHArelativeRuptureVolume->setText(QString::number(cells[currentCell].apoptosis.deathRelativeRuptureVolume));
            ui->DEATHAdeathRateField->setText(QString::number(cells[currentCell].apoptosis.deathRate));
            ui->DEATHAphase0Duration->setText(QString::number(cells[currentCell].apoptosis.deathPhases[0].duration));
            ui->DEATHAphase0Transition->setText(QString::number(cells[currentCell].apoptosis.deathPhases[0].transition));
            ui->DEATHAphase0DurationCheckBox->setChecked(cells[currentCell].apoptosis.deathPhases[0].fixedDuration);
            ui->DEATHAphase0TransitionCheckBox->setChecked(cells[currentCell].apoptosis.deathPhases[0].fixedTransition);

            ui->DEATHNunlysedFluidChangeRate->setText(QString::number(cells[currentCell].necrosis.deathUnlysedFluidChangeRate));
            ui->DEATHNlysedFluidChangeRate->setText(QString::number(cells[currentCell].necrosis.deathLysedFluidChangeRate));
            ui->DEATHNcytoplasmicBiomassChangeRate->setText(QString::number(cells[currentCell].necrosis.deathCytoplasmicBiomassChangeRate));
            ui->DEATHNnuclearBiomassChangeRate->setText(QString::number(cells[currentCell].necrosis.deathNuclearBiomassChangeRate));
            ui->DEATHNcalcificationRate->setText(QString::number(cells[currentCell].necrosis.deathCalcificationRate));
            ui->DEATHNrelativeRuptureVolume->setText(QString::number(cells[currentCell].necrosis.deathRelativeRuptureVolume));
            ui->DEATHNdeathRateField->setText(QString::number(cells[currentCell].necrosis.deathRate));
            ui->DEATHNphase0Duration->setText(QString::number(cells[currentCell].necrosis.deathPhases[0].duration));
            ui->DEATHNphase0Transition->setText(QString::number(cells[currentCell].necrosis.deathPhases[0].transition));
            ui->DEATHNphase1Duration->setText(QString::number(cells[currentCell].necrosis.deathPhases[1].duration));
            ui->DEATHNphase1Transition->setText(QString::number(cells[currentCell].necrosis.deathPhases[1].transition));
            ui->DEATHNphase0DurationCheckBox->setChecked(cells[currentCell].necrosis.deathPhases[0].fixedDuration);
            ui->DEATHNphase0TransitionCheckBox->setChecked(cells[currentCell].necrosis.deathPhases[0].fixedTransition);
            ui->DEATHNphase1DurationCheckBox->setChecked(cells[currentCell].necrosis.deathPhases[1].fixedDuration);
            ui->DEATHNphase1TransitionCheckBox->setChecked(cells[currentCell].necrosis.deathPhases[1].fixedTransition);


        // volume
        ui->VOLUMEtotalVolume->setText(QString::number(cells[currentCell].totalVolume));
        ui->VOLUMEnuclearVolume->setText(QString::number(cells[currentCell].nuclearVolume));
        ui->VOLUMEfluidFraction->setText(QString::number(cells[currentCell].fluidFraction));
        ui->VOLUMErelativeRuptureVolume->setText(QString::number(cells[currentCell].relativeRuptureVolume));
        ui->VOLUMEnuclearBiomassChangeRate->setText(QString::number(cells[currentCell].nuclearBiomassChangeRate));
        ui->VOLUMEcytoplasmicBiomassChangeRate->setText(QString::number(cells[currentCell].cytoplasmicBiomassChangeRate));
        ui->VOLUMEfluidChangeRate->setText(QString::number(cells[currentCell].fluidChangeRate));
        ui->VOLUMEcalcifiedFraction->setText(QString::number(cells[currentCell].calcifiedFraction));
        ui->VOLUMEcalcificationRate->setText(QString::number(cells[currentCell].calcificationRate));
        // mechanics
        ui->MECHANICScellAdhesionStrength->setText(QString::number(cells[currentCell].cellAdhesionStrength));
        ui->MECHANICScellRepulsionStrength->setText(QString::number(cells[currentCell].cellRepulsionStrength));
        ui->MECHANICSrelativeMaximumAdhesionStrength->setText(QString::number(cells[currentCell].relativeMaximumAdhesionStrength));
        // need to work in distance as relative/absolute

        // motility
        ui->MOTILITYspeed->setText(QString::number(cells[currentCell].speed));
        ui->MOTILITYpersistenceTime->setText(QString::number(cells[currentCell].persistenceTime));
        ui->MOTILITYmitigationBias->setText(QString::number(cells[currentCell].mitigationBias));
        ui->MOTILITYenableCheckBox->setChecked(cells[currentCell].enableChemotaxis);
        ui->MOTILITYuse2dCheckBox->setChecked(cells[currentCell].use2D);

        // remove all comboBox options and reinsert
        // chemotaxis comboBox
        ui->MOTILITYchemotaxisComboBox->clear();
        for(int i = 0; i < substrates.size(); i++){
            ui->MOTILITYchemotaxisComboBox->addItem(substrates[i].name);
        }
        //qDebug() << cells[currentCell].microenvironmentID;
        ui->MOTILITYchemotaxisComboBox->setCurrentIndex(cells[currentCell].microenvironmentID);
        // direction comboBox
        ui->MOTILITYdirectionComboBox->setCurrentIndex((cells[currentCell].direction) == 1 ? 0 : 1);

        // secretion
        for(int s = 0; s < cells[currentCell].secretionModels.size(); s++){
            ui->SECRETIONsecretionRate->setText(QString::number(cells[currentCell].secretionModels[s].secretionRate));
            ui->SECRETIONsecretionTarget->setText(QString::number(cells[currentCell].secretionModels[s].secretionTarget));
            ui->SECRETIONuptakeRate->setText(QString::number(cells[currentCell].secretionModels[s].uptakeRate));
            ui->SECRETIONnetExportRate->setText(QString::number(cells[currentCell].secretionModels[s].netExportRate));
        }
    }
}

//When a new substrate or cell definition is made this fuction empties the text fields for more convenient typing
void MainWindow::loadNew(int n)
{
    if (n == 0){
        ui->Name->setText("");
        ui->diffusionCoefficient->setText("");
        ui->decayRate->setText("");
        ui->initialCondition->setText("");
    }
    else if (n == 1){
        ui->cellName->setText("");
        ui->CYCLEname->setText("");
        ui->CYCLEmodel->setCurrentIndex(0);
    }
}

//Checks the names of substrates and cell definitions to ensure they do not have the same name
void MainWindow::checkName(QString name, int n)
{
    if (n == 0){
        int i;
        for (i = 0; i < substrates.size(); i++){

        }
    }
}

//Determines what the user clicked and changes the screen accordingly
void MainWindow::on_outline_itemClicked(QTreeWidgetItem *item, int column)
{
    if(item->parent() == environmentIndex){
        ui->pages_widget->setCurrentIndex(0);
        currentSub = environmentIndex->indexOfChild(item); //The index of the item in the outline is the same as the index in the substrate list as well as the id of the substrate
        loadValues(0);
    }
    else if(item->parent() == cellIndex){
        ui->pages_widget->setCurrentIndex(1);
        currentCell = cellIndex->indexOfChild(item);
        for(int c = 0; c < cells[currentCell].cyclePhases.size(); c++){
           qDebug() << cells[currentCell].cyclePhases[c].duration;
        }
        loadValues(1);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//The following fuctions are for the microenvironment substrates

//Updates the name inside the microenvironment object for the current substrate, as well as in the Ouline on the left
void MainWindow::on_Name_textEdited(const QString &arg1)
{
    if(arg1 == ""){
        substrates[currentSub].name = "Default";
        environmentIndex->child(currentSub)->setText(0, "Default");
    }
    else{
        substrates[currentSub].name = arg1;
        environmentIndex->child(currentSub)->setText(0, arg1);
    }
    qDebug() << substrates[currentSub].name;
}

//Updates the diffusion coefficient inside the microenvironment object for the current substrate
void MainWindow::on_diffusionCoefficient_textEdited(const QString &arg1)
{
    substrates[currentSub].diffCoeff = arg1.toDouble();
    qDebug() << substrates[currentSub].diffCoeff;
}

//Updates the decay rate inside the microenvironment object for the current substrate
void MainWindow::on_decayRate_textEdited(const QString &arg1)
{
    substrates[currentSub].decayR = arg1.toDouble();
    qDebug() << substrates[currentSub].decayR;
}

//Updates the initial condition inside the microenvironment object for the current substrate
void MainWindow::on_initialCondition_textEdited(const QString &arg1)
{
    substrates[currentSub].initialC = arg1.toDouble();
    qDebug() << substrates[currentSub].initialC;
}

//Creates a new object in the Outline and calls loadNew()
void MainWindow::on_New_clicked()
{
    currentSub = substrates.size();
    microenvironment newSub = microenvironment(currentSub);
    substrates.append(newSub);
    environmentIndex->addChild(new QTreeWidgetItem(0));
    environmentIndex->child(currentSub)->setText(0, substrates[currentSub].name);
    checkName(substrates[currentSub].name, 0);
    loadNew(0);
}

//Creates a clone of the current substrate but changes the id to the next avaliable value, then displays the cloned values with loadValues()
void MainWindow::on_Clone_clicked()
{
    microenvironment newSub = microenvironment(substrates.size());
    newSub = substrates[currentSub];
    currentSub = substrates.size();
    newSub.id = currentSub;
    substrates.append(newSub);
    environmentIndex->addChild(new QTreeWidgetItem(0));
    environmentIndex->child(currentSub)->setText(0, substrates[currentSub].name);
    checkName(substrates[currentSub].name, 0);
    loadValues(0);
}

//Removes the current substrate from the substrate list and the Outline, then reassigns the IDs of the remaining substrates. This function ensures there is at least 1 substrate
void MainWindow::on_Remove_clicked()
{
    if(substrates.size() == 1){
        qDebug() << "Thats the last one!! You cannot remove it!";
        return;
    }
    substrates.remove(currentSub);
    environmentIndex->removeChild(environmentIndex->child(currentSub));
    int i;
    for(i=0;i<substrates.size();i++){
        substrates[i].id = i;
    }
    currentSub = 0;
    loadValues(0);
}
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//The following functions are for the cell definitions


//CYCLE Text Getters
void MainWindow::on_newCellButton_clicked()
{
    currentCell = cells.size();
    cell newCell = cell(currentCell);
    cells.append(newCell);
    cellIndex->addChild(new QTreeWidgetItem(0));
    cellIndex->child(currentCell)->setText(0, cells[currentCell].name);
    checkName(cells[currentCell].name, 1);
    loadNew(1);
}

void MainWindow::on_cloneCellButton_clicked()
{
    cell newCell = cell(cells.size());
    newCell = cells[currentCell];
    currentCell = cells.size();
    newCell.id = currentCell;
    cells.append(newCell);
    cellIndex->addChild(new QTreeWidgetItem(0));
    cellIndex->child(currentCell)->setText(0, cells[currentCell].name);
    checkName(cells[currentCell].name, 1);
    loadValues(1);
}

void MainWindow::on_removeCellButton_clicked()
{
    if(cells.size() == 1){
        qDebug() << "Thats the last one!! You cannot remove it!";
        return;
    }
    cells.remove(currentCell);
    cellIndex->removeChild(cellIndex->child(currentCell));
    int i;
    for(i=0;i<cells.size();i++){
        cells[i].id = i;
    }
    currentCell = 0;
    loadValues(1);
}

void MainWindow::on_cellName_textEdited(const QString &arg1)
{
    if(arg1 == ""){
        cells[currentCell].name = "Default";
        cellIndex->child(currentCell)->setText(0, "Default");
    }
    else{
        cells[currentCell].name = arg1;
        cellIndex->child(currentCell)->setText(0, arg1);
    }
    checkName(cells[currentCell].name, 1);
}

void MainWindow::on_CYCLEname_textEdited(const QString &arg1)
{
    if(arg1 == ""){
        cells[currentCell].cycleName = ui->CYCLEmodel->currentText();
    }
    else{
        cells[currentCell].cycleName = arg1;
    }
}

void MainWindow::on_CYCLEmodel_currentIndexChanged(int index)
{
    index = index - 1;
    cells[currentCell].cycleID = index;
    cells[currentCell].get_cycle_phases(index);
    QLayoutItem *child;
    while ((child = ui->CYCLEPhaseDurationLayout->takeAt(0)) != nullptr) {
        delete child->widget(); // delete the widget
        delete child;   // delete the layout item
    }
    while ((child = ui->CYCLEPhaseTransitionLayout->takeAt(0)) != nullptr) {
        delete child->widget(); // delete the widget
        delete child;   // delete the layout item
    }
    while(CPDLineEdits.size() != 0){
        CPDLineEdits.remove(0);
        CPDCheckBoxes.remove(0);
    }
    while(CPTLineEdits.size() != 0){
        CPTLineEdits.remove(0);
        CPTCheckBoxes.remove(0);
    }

    for(int i = 0; i < cells[currentCell].numCyclePhases; i++){
        QString durationText = "Phase " + QString::number(i);
        QString transitionText;
        if (cells[currentCell].numCyclePhases == 1)
            transitionText = "Phase " + QString::number(i) + " -> " + QString::number(i);
        else if (i == cells[currentCell].numCyclePhases - 1)
            transitionText = "Phase " + QString::number(i) + " -> " + QString::number(0);
        else
            transitionText = "Phase " + QString::number(i) + " -> " + QString::number(i + 1);

        ui->CYCLEPhaseDurationLayout->addWidget(new QLabel(durationText), i, 0);
        QLineEdit *phaseDurationLineEdit = new QLineEdit;
        ui->CYCLEPhaseDurationLayout->addWidget(phaseDurationLineEdit, i, 1);
        QCheckBox *phaseDurationCheckBox = new QCheckBox;
        phaseDurationCheckBox->setText("Fixed");
        ui->CYCLEPhaseDurationLayout->addWidget(phaseDurationCheckBox, i, 2);
        ui->CYCLEPhaseDurationLayout->addWidget(new QLabel("min"), i, 3);
        CPDLineEdits.append(phaseDurationLineEdit);
        CPDCheckBoxes.append(phaseDurationCheckBox);
        connect(phaseDurationLineEdit, SIGNAL(editingFinished()), this, SLOT(getPhaseDuration()));
        connect(phaseDurationCheckBox, SIGNAL(stateChanged(int state)), this, SLOT(checkFixedDuration()));

        ui->CYCLEPhaseTransitionLayout->addWidget(new QLabel(transitionText), i, 0);
        QLineEdit *phaseTransitionLineEdit = new QLineEdit;
        ui->CYCLEPhaseTransitionLayout->addWidget(phaseTransitionLineEdit, i, 1);
        QCheckBox *phaseTransitionCheckBox = new QCheckBox;
        phaseTransitionCheckBox->setText("Fixed");
        ui->CYCLEPhaseTransitionLayout->addWidget(phaseTransitionCheckBox, i, 2);
        ui->CYCLEPhaseTransitionLayout->addWidget(new QLabel("1/min"), i, 3);
        CPTLineEdits.append(phaseTransitionLineEdit);
        CPTCheckBoxes.append(phaseTransitionCheckBox);
        connect(phaseTransitionLineEdit, SIGNAL(editingFinished()), this, SLOT(getPhaseTransition()));
        connect(phaseTransitionCheckBox, SIGNAL(stateChanged(int state)), this, SLOT(checkFixedTransition()));
    }
    loadValues(1);
}

void MainWindow::getPhaseDuration()
{
    for(int i = 0; i < cells[currentCell].numCyclePhases; i++){
        if (CPDLineEdits[i]->text() == "")
            cells[currentCell].cyclePhases[i].duration = 0.0;
        else
            cells[currentCell].cyclePhases[i].duration = CPDLineEdits[i]->text().toDouble();
    }
}

void MainWindow::getPhaseTransition()
{
    for(int i = 0; i < cells[currentCell].numCyclePhases; i++){
        if (CPTLineEdits[i]->text() == "")
            cells[currentCell].cyclePhases[i].transition = 0.0;
        else
            cells[currentCell].cyclePhases[i].transition = CPTLineEdits[i]->text().toDouble();
    }
}

void MainWindow::checkFixedDuration(){
    for(int i = 0; i < cells[currentCell].numCyclePhases; i++){
        cells[currentCell].cyclePhases[i].fixedDuration = CPDCheckBoxes[i]->checkState();
    }
}

void MainWindow::checkFixedTransition(){
    for(int i = 0; i < cells[currentCell].numCyclePhases; i++){
        cells[currentCell].cyclePhases[i].fixedTransition = CPTCheckBoxes[i]->checkState();
    }
}


// VOLUME Text Getters
void MainWindow::on_VOLUMEtotalVolume_textEdited(const QString &arg1)
{
    cells[currentCell].totalVolume = arg1.toDouble();
    qDebug() << cells[currentCell].totalVolume;
}

void MainWindow::on_VOLUMEnuclearVolume_textEdited(const QString &arg1)
{
    cells[currentCell].nuclearVolume = arg1.toDouble();
    qDebug() << cells[currentCell].nuclearVolume;
}

void MainWindow::on_VOLUMEfluidFraction_textEdited(const QString &arg1)
{
    cells[currentCell].fluidFraction = arg1.toDouble();
    qDebug() << cells[currentCell].fluidFraction;
}

void MainWindow::on_VOLUMErelativeRuptureVolume_textEdited(const QString &arg1)
{
    cells[currentCell].relativeRuptureVolume = arg1.toDouble();
    qDebug() << cells[currentCell].relativeRuptureVolume;
}

void MainWindow::on_VOLUMEnuclearBiomassChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].nuclearBiomassChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].nuclearBiomassChangeRate;
}

void MainWindow::on_VOLUMEcytoplasmicBiomassChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].cytoplasmicBiomassChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].cytoplasmicBiomassChangeRate;
}

void MainWindow::on_VOLUMEfluidChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].fluidChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].fluidChangeRate;
}

void MainWindow::on_VOLUMEcalcifiedFraction_textEdited(const QString &arg1)
{
    cells[currentCell].calcifiedFraction = arg1.toDouble();
    qDebug() << cells[currentCell].calcifiedFraction;
}

void MainWindow::on_VOLUMEcalcificationRate_textEdited(const QString &arg1)
{
    cells[currentCell].calcificationRate = arg1.toDouble();
    qDebug() << cells[currentCell].calcificationRate;
}

// MECHANICS Text getters

void MainWindow::on_MECHANICScellAdhesionStrength_textEdited(const QString &arg1)
{
    cells[currentCell].cellAdhesionStrength = arg1.toDouble();
    qDebug() << cells[currentCell].cellAdhesionStrength;
}

void MainWindow::on_MECHANICScellRepulsionStrength_textEdited(const QString &arg1)
{
    cells[currentCell].cellRepulsionStrength = arg1.toDouble();
    qDebug() << cells[currentCell].cellRepulsionStrength;
}

void MainWindow::on_MECHANICSrelativeMaximumAdhesionStrength_textEdited(const QString &arg1)
{
    cells[currentCell].relativeMaximumAdhesionStrength = arg1.toDouble();
    qDebug() << cells[currentCell].relativeMaximumAdhesionStrength;
}

// TODO: Relative vs. Maximum equilibrium distance

// MOTILITY Text Getters

void MainWindow::on_MOTILITYspeed_textEdited(const QString &arg1)
{
    cells[currentCell].speed = arg1.toDouble();
    qDebug() << cells[currentCell].speed;
}

void MainWindow::on_MOTILITYpersistenceTime_textEdited(const QString &arg1)
{
    cells[currentCell].persistenceTime = arg1.toDouble();
    qDebug() << cells[currentCell].persistenceTime;
}

void MainWindow::on_MOTILITYmitigationBias_textEdited(const QString &arg1)
{
    cells[currentCell].mitigationBias = arg1.toDouble();
    qDebug() << cells[currentCell].mitigationBias;
}

void MainWindow::on_MOTILITYenableCheckBox_toggled(bool arg1)
{
    cells[currentCell].enableMotility = arg1;
    qDebug() << cells[currentCell].enableMotility;
}

void MainWindow::on_MOTILITYenableChemotaxisCheckBox_toggled(bool arg1)
{
    cells[currentCell].enableChemotaxis = arg1;
    qDebug() << cells[currentCell].enableChemotaxis;
}

void MainWindow::on_MOTILITYuse2dCheckBox_toggled(bool arg1)
{
    cells[currentCell].use2D = arg1;
    qDebug() << cells[currentCell].use2D;
}

void MainWindow::on_MOTILITYchemotaxisComboBox_currentIndexChanged(int i)
{
    cells[currentCell].chemotaxisMicroenvironment = substrates[i].name;
    cells[currentCell].microenvironmentID = i;
    qDebug() << cells[currentCell].chemotaxisMicroenvironment;
}

void MainWindow::on_MOTILITYdirectionComboBox_currentIndexChanged(int i)
{
    cells[currentCell].direction = (i == 0) ? 1 : -1;
    qDebug() << cells[currentCell].direction;
}
//DEATH Text Getters

void MainWindow::on_DEATHAname_textEdited(const QString &arg1)
{
    if(arg1 == ""){
        cells[currentCell].apoptosis.deathName = "Default";
    }
    else{
        cells[currentCell].apoptosis.deathName = arg1;
    }
}

void MainWindow::on_DEATHAdeathRateField_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathRate = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathRate;
}

void MainWindow::on_DEATHAunlysedFluidChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathUnlysedFluidChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathUnlysedFluidChangeRate;
}

void MainWindow::on_DEATHAlysedFluidChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathLysedFluidChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathLysedFluidChangeRate;
}

void MainWindow::on_DEATHAcytoplasmicBiomassChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathCytoplasmicBiomassChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathCytoplasmicBiomassChangeRate;
}

void MainWindow::on_DEATHAnuclearBiomassChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathNuclearBiomassChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathNuclearBiomassChangeRate;
}

void MainWindow::on_DEATHAcalcificationRate_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathCalcificationRate = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathCalcificationRate;
}

void MainWindow::on_DEATHArelativeRuptureVolume_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathRelativeRuptureVolume = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathRelativeRuptureVolume;
}

void MainWindow::on_DEATHAphase0Duration_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathPhases[0].duration = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathPhases[0].duration;
}

void MainWindow::on_DEATHAphase0DurationCheckBox_toggled(bool checked)
{
    cells[currentCell].apoptosis.deathPhases[0].fixedDuration = checked;
    qDebug() << cells[currentCell].apoptosis.deathPhases[0].fixedDuration;
}

void MainWindow::on_DEATHAphase0Transition_textEdited(const QString &arg1)
{
    cells[currentCell].apoptosis.deathPhases[0].transition = arg1.toDouble();
    qDebug() << cells[currentCell].apoptosis.deathPhases[0].transition;
}

void MainWindow::on_DEATHAphase0TransitionCheckBox_toggled(bool checked)
{
    cells[currentCell].apoptosis.deathPhases[0].fixedTransition = checked;
    qDebug() << cells[currentCell].apoptosis.deathPhases[0].fixedTransition;
}

void MainWindow::on_DEATHNname_textEdited(const QString &arg1)
{
    if(arg1 == ""){
        cells[currentCell].necrosis.deathName = "Default";
    }
    else{
        cells[currentCell].necrosis.deathName = arg1;
    }
}

void MainWindow::on_DEATHNdeathRateField_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathRate = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathRate;
}

void MainWindow::on_DEATHNunlysedFluidChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathUnlysedFluidChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathUnlysedFluidChangeRate;
}

void MainWindow::on_DEATHNlysedFluidChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathLysedFluidChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathLysedFluidChangeRate;
}

void MainWindow::on_DEATHNcytoplasmicBiomassChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathCytoplasmicBiomassChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathCytoplasmicBiomassChangeRate;
}

void MainWindow::on_DEATHNnuclearBiomassChangeRate_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathNuclearBiomassChangeRate = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathNuclearBiomassChangeRate;
}

void MainWindow::on_DEATHNcalcificationRate_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathCalcificationRate = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathCalcificationRate;
}

void MainWindow::on_DEATHNrelativeRuptureVolume_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathRelativeRuptureVolume = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathRelativeRuptureVolume;
}

void MainWindow::on_DEATHNphase0Duration_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathPhases[0].duration = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathPhases[0].duration;
}

void MainWindow::on_DEATHNphase1Duration_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathPhases[1].duration = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathPhases[1].duration;
}

void MainWindow::on_DEATHNphase0DurationCheckBox_toggled(bool checked)
{
    cells[currentCell].necrosis.deathPhases[0].fixedDuration = checked;
    qDebug() << cells[currentCell].necrosis.deathPhases[0].fixedDuration;
}

void MainWindow::on_DEATHNphase1DurationCheckBox_toggled(bool checked)
{
    cells[currentCell].necrosis.deathPhases[1].fixedDuration = checked;
    qDebug() << cells[currentCell].necrosis.deathPhases[1].fixedDuration;
}

void MainWindow::on_DEATHNphase0Transition_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathPhases[0].transition = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathPhases[0].transition;
}

void MainWindow::on_DEATHNphase1Transition_textEdited(const QString &arg1)
{
    cells[currentCell].necrosis.deathPhases[1].transition = arg1.toDouble();
    qDebug() << cells[currentCell].necrosis.deathPhases[1].transition;
}

void MainWindow::on_DEATHNphase0TransitionCheckBox_toggled(bool checked)
{
    cells[currentCell].necrosis.deathPhases[0].fixedTransition = checked;
    qDebug() << cells[currentCell].necrosis.deathPhases[0].fixedTransition;
}

void MainWindow::on_DEATHNphase1TransitionCheckBox_toggled(bool checked)
{
    cells[currentCell].necrosis.deathPhases[1].fixedTransition = checked;
    qDebug() << cells[currentCell].necrosis.deathPhases[1].fixedTransition;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// GENERAL LOGICAL HELPER FUNCTIONS
