#ifndef PHASE_H
#define PHASE_H


class phase
{
public:
    phase();

    int index;

    double duration = 1;

    double transition = 1;

    bool fixedDuration = false;

    bool fixedTransition = false;

    void autofillTransition(){
        if(duration != 0) transition = 1/duration;
    }

    void autofillDuration(){
        if(transition != 0) duration = 1/transition;
    }

};

#endif // PHASE_H
