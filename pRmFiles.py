#!/usr/bin/env python

import sys
from array import array
import os
par = sys.argv

f = open(par[1], 'r')
line = f.readline()
while line:
    line = line.rstrip()
    os.remove(line)
    line = f.readline()
f.close
