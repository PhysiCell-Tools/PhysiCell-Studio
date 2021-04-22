#include "cell.h"
#include "QDebug"

cell::cell()
{

}

cell::cell(int ID)
{
    id = ID;
    phase newPhase;
    for(int i = 0; i < 4; i++){
        cyclePhases.append(newPhase);
    }
}

void cell::get_cycle_phases(int index)
{
    phase newPhase;
    switch(index){
    case -1: break;
    case 0:
        numCyclePhases = 3; break;
    case 1:
        numCyclePhases = 2; break;
    case 2:
        numCyclePhases = 3; break;
    case 3:
        numCyclePhases = 0;
        break;
    case 4:
        numCyclePhases = 0;
        break;
    case 5:
        numCyclePhases = 1; break;
    case 6:
        numCyclePhases = 4; break;
    case 7:
        numCyclePhases = 2; break;
    }
}
