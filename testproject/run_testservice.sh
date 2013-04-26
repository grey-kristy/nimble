#!/bin/sh

PROJECT_ROOT=$PWD
NIMBLE_ROOT=$PROJECT_ROOT/../
LOG_ROOT=$PROJECT_ROOT/logs/

export PYTHONPATH=$PYTHONPATH:$NIMBLE_ROOT

python $PROJECT_ROOT/testservice.py $1 port=11111 frontend=gevent log_dir=$LOG_ROOT spawn=None
