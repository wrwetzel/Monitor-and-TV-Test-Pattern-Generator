#!/bin/bash
# ----------------------------------------------------------------------------------------------
#   This script runs mk-patterns.py on all available cores of a multi-core system.
#       mk-pattern.py options used here:
#           -v - verbose
#           -f - index to starting pattern in 'shapes' table
#           -s - step in 'shapes' table to next pattern

CORES=$(nproc)
# let CORES=CORES/2
COUNTER=0

echo "Starting $CORES processes"

while [ $COUNTER -lt $CORES ]
do
    mk-patterns.py -v -f $COUNTER -s $CORES &
    let COUNTER=COUNTER+1
done
wait

# ----------------------------------------------------------------------------------------------
