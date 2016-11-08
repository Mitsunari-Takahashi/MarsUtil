#!/usr/bin/env python
import os
import os.path as path
from datetime import datetime
import shutil
import subprocess
import re
from pSubmitPJ import SubmitPJ
import click


@click.command()
@click.argument('dirorg', type=str)
@click.argument('suffix', type=str)
@click.option('--dirtgt', '-t', default="")
@click.option('--rscgrp', '-g', default="B")
def main(dirorg, dirtgt, suffix, rscgrp):
    if dirtgt=="" or dirtgt==None:
        dirtgt = os.getcwd()
    if path.exists(dirtgt)==False:
        os.makedirs(dirtgt)
    os.chdir(dirtgt)
    theTime = datetime.now()
    nameHtml = '{0}{1}{2}{3}{4}{5}.html'.format(theTime.year, theTime.month,theTime.day,theTime.hour,theTime.minute,theTime.second)
    aCmd = [ 'wget', '-O{0}'.format(nameHtml), dirorg ]
    print aCmd
    subprocess.call(aCmd)
    fileHtml = open(nameHtml)
    dataHtml = fileHtml.read()
    strFind = 'FERMI_POINTING_FINAL_\d\d\d_20\d\d\d\d\d_20\d\d\d\d\d_\d\d.fits'
    print "Search for", strFind
    aRootFile = re.findall(strFind, dataHtml)
    aRootFile = list(set(aRootFile))
    print aRootFile
    aProc = []
#    for rootFile in aRootFile:
    for (iRF, rootfile) in enumerate(aRootFile):
#        bCmd = [ 'wget', '-O{0}'.format(rootFile), '-nc', '-nv', '{0}/{1}'.format(dirorg, rootFile) ]
        bCmd = 'wget -O{1} -nc -nv {0}/{1}'.format(dirorg, rootFile)
        SubmitPJ(bCmd, dirtgt, "{0}_{1}".format(suffix, iRF), rscgrp)
        #print bCmd
        #pRet = subprocess.Popen(bCmd)
        #aProc.append(pRet)


if __name__ == '__main__':
    main()
