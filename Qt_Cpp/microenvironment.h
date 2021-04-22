#ifndef MICROENVIRONMENT_H
#define MICROENVIRONMENT_H

#include "QString"


class microenvironment
{
public:
    //Default values
    microenvironment();
    microenvironment(int ID);
    double diffCoeff = 0.0;
    double decayR = 0.0;
    double initialC = 0.0;
    double dirch [7][2] = {{0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,0}};
    QString name = "Default";
    int id;
};

#endif // MICROENVIRONMENT_H
