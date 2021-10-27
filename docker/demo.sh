#!/bin/bash


supervisord -n &

echo "Running TangoDB"

sleep 10

$HOME/anaconda/bin/conda run -n sardana-jupyter --no-capture-output Sardana demo &

echo "Running Sardana"

$HOME/anaconda/bin/conda run --no-capture-output -n sardana-jupyter jupyter lab --allow-root --no-browser --ip 0.0.0.0 --NotebookApp.token="" --NotebookApp.password=""