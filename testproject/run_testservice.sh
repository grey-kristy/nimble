#!/bin/sh

PROJECT_ROOT=$PWD
NIMBLE_ROOT=$PROJECT_ROOT/../

export PYTHONPATH=$PYTHONPATH:$NIMBLE_ROOT

python $PROJECT_ROOT/testservice.py $1 $2
