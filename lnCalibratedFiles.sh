#!/bin/sh

FILENAME=$1
DIRSRC=$2
DIRTGT=$3
while read line; do
    lineCut=`echo $line | cut -c 10-17`
    echo $lineCut
    ln -s "${DIRSRC}/"*"${lineCut}"*".root" $DIRTGT
done < $FILENAME