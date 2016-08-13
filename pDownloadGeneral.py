#!/usr/bin/env python
import os
import os.path as path
from datetime import datetime
import shutil
import subprocess

def Download(strPicDir, strDirTgt):
    if path.exists(strDirTgt)==False:
        os.makedirs(strDirTgt)
    os.chdir(strDirTgt)
    theTime = datetime.now()
    nameHtml = '{0}{1}{2}{3}{4}{5}.html'.format(theTime.year, theTime.month,theTime.day,theTime.hour,theTime.minute,theTime.second)
    aCmd = [ 'wget', '-O{0}'.format(nameHtml), strPicDir ]
    print aCmd
    subprocess.call(aCmd)
    fileHtml = open(nameHtml)
    dataHtml = fileHtml.read()
    strFind = ' lat_spacecraft_weekly_w???_p???_v???.fits'
    print "Search for", strFind
    aRootFile = re.findall(strFind, dataHtml)
    print aRootFile
    aProc = []
    for rootFile in aRootFile:
        bCmd = [ 'wget', '-O{0}'.format(rootFile), '-nc', '-nv', '{0}/{1}'.format(strPicDir, rootFile) ]
        print bCmd
        pRet = subprocess.Popen(bCmd)
        aProc.append(pRet)
