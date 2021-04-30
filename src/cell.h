#ifndef CELLDEFINITION_H
#define CELLDEFINITION_H

#include "death.h"
#include "secretion.h"
#include "phase.h"
#include "QString"
#include "QVector"

class cell
{
public:
    //Default values
    cell();
    cell(int ID);
    QString name = "Default";
    int id;
    // Cycle
    QString cycleName = "Default";
    int cycleID = -1;
    int numCyclePhases = 0;
    QVector<phase> cyclePhases;
    void get_cycle_phases(int index);
    // Death
    death apoptosis = death(1);
    death necrosis = death(2);
    // Volume
    double totalVolume = 0;
    double nuclearVolume = 0;
    double fluidFraction = 0;
    double relativeRuptureVolume = 0;
    double nuclearBiomassChangeRate = 0;
    double cytoplasmicBiomassChangeRate = 0;
    double fluidChangeRate = 0;
    double calcifiedFraction = 0;
    double calcificationRate = 0;

    // Mechanics
    double cellAdhesionStrength = 0;
    double cellRepulsionStrength = 0;
    double relativeMaximumAdhesionStrength = 0;
    // - one or the other
    double relativeEquilibriumDistance = 0;
    double absoluteEquilibriumDistance = 0;
    // Motility
    double speed = 0;
    double persistenceTime = 0;
    double mitigationBias = 0;
    bool enableMotility = false;
    bool enableChemotaxis = false;
    bool use2D = false;
    int microenvironmentID = 0;
    int direction = 0;
    QString chemotaxisMicroenvironment = "None"; // could be a Microenvironment object w/ different implementation, but prob. not necessary

    // Secretion
    QVector<secretion> secretionModels;

};

#endif // CELLDEFINITION_H
