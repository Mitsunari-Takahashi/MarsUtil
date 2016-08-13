#!/bin/sh
NAME_SRC=$1
DATE=$2
CUT=$3
TGT=$PATH_MARS_BASE/$NAME_SRC/$DATE/$CUT
mkdir -p $TGT
for dir in "quate" "odie" "flute"; do
    scp -r takhsm@icrhome02:/disk/gamma/cta/store/takhsm/MAGIC/${NAME_SRC}/${DATE}/${CUT}/${dir} ${TGT}
done
open $TGT
