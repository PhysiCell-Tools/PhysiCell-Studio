#include "death.h"
#include <qdebug.h>

death::death()
{
}

death::death(int i)
{
    phase newPhase;
    for(int k = 0; k < i; k++){
        deathPhases.append(newPhase);
    }
}
