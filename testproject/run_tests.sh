#!/bin/bash

PROJECT_ROOT=$PWD
NIMBLE_ROOT=$PROJECT_ROOT/../

export PYTHONPATH=$PYTHONPATH:$NIMBLE_ROOT

cd $PROJECT_ROOT/tests

for i in *.py
do
    echo ---------------------------------------
    echo TESTING:$i
    python $i
done

