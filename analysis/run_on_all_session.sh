#!/bin/bash
# Arg 1 : The name of directory where all data is stored.
# Arg 2 : Pattern to filter. This is optional. If not given, all sessions are
# processed.
set -e
set -x

if [ $# -lt 2 ]; then
    echo "USAGE: $0 data_dir result_dir"
    exit
fi

PAT="*SessionType*Session*"
RESULTDIR="$2"

echo "Using pattern: $PAT"
DIRS=`find $1 -type d -name "${PAT}"`
for d in $DIRS; do
    echo "Processing $d"
    python ./analyze_dir.py -d $d -o ${RESULTDIR}/`basename $d` 
done

