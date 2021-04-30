#ifndef DEATH_H
#define DEATH_H

#include "QVector"
#include "QString"
#include "phase.h"

class death
{
public:
    death();
    death(int i);
    int deathIndex;
    int deathCode = 0;
    QString deathName = "";
    QVector<phase> deathPhases;
    double deathRate = 0;
    double deathUnlysedFluidChangeRate = 0;
    double deathLysedFluidChangeRate = 0;
    double deathCytoplasmicBiomassChangeRate = 0;
    double deathNuclearBiomassChangeRate = 0;
    double deathCalcificationRate = 0;
    double deathRelativeRuptureVolume = 0;
};

#endif // DEATH_H
