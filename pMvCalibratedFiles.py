#!/usr/bin/env python

import sys
import os
import subprocess
par = sys.argv

for line in open(par[1], "r"):
    run = line[9:17]
    aCmd = ['ln', '-s', '{0}/.*{1}.*'.format(par[2], run), '{0}'.format(par[3])]
    print aCmd
    subprocess.call(aCmd, shell=True)
    
