#!/bin/env python
import os
import subprocess


def SubmitPJ(strCmd, pathDirWork, strSuffix="", strRscGrp="B", verROOT="5.34.24", jobname=""):
    os.chdir(pathDirWork)
    print strCmd
    nameFilePJ = "{0}.csh".format(strSuffix)
    filePJ = open(nameFilePJ,"w")
    strPJ = """#!/bin/tcsh
#------ pjsub option --------#
#PJM -L "rscunit=common"
#PJM -L "rscgrp={0}"
#PJM -L "vnode=1"
#------- Program execution -------#""".format(strRscGrp)
    if verROOT=="5.34.24":
        strPJ = strPJ + """
setenv ROOTSYS /home/takhsm/app/root_v5.34.24
setenv MARSSYS /home/takhsm/app/Mars/Mars_V2-16-2_ROOT53424
setenv PATH /home/takhsm/app/Mars/Mars_V2-16-2_ROOT53424:/home/takhsm/app/ROOT_v53424/bin:/home/takhsm/app/anaconda2/bin:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/home/takhsm/CTA_MC/Chimp/Chimp:/usr/include/mysql:/home/takhsm/app/cmake/3.3.0:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/home/takhsm/CTA_MC/corsika_simtelarray_Prod3/hessioxxx/bin:/home/takhsm/CTA_MC/corsika_simtelarray_Prod3/std:/usr/local/bin:/bin:/usr/bin
setenv LD_LIBRARY_PATH /home/takhsm/app/root_v5.34.24/lib:/home/takhsm/app/root_v5.34.24/lib/root:/home/takhsm/app/lib:/home/takhsm/app/root_v5.34.24:/home/takhsm/app/Mars/Mars_V2-16-2_ROOT53424:/home/takhsm/lib/libPNG/lib:/home/takhsm/lib/lib:/home/takhsm/lib/libJPEG/lib:/home/takhsm/CTA_MC/Chimp/Chimp:/home/takhsm/CTA_MC/Chimp/Chimp/hessioxxx/lib:/home/takhsm/charaPMT:/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/usr/lib64"""
    elif verROOT=="5.34.14":
        strPJ = strPJ + """
setenv ROOTSYS /usr/local/gcc473/root_v5.34.14
setenv MARSSYS /home/takhsm/app/Mars/Mars_V2-15-8
setenv PATH /usr/local/gcc473/root_v5.34.14/bin:/usr/local/gcc473/bin:/home/takhsm/app/Mars/Mars_V2-15-8:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/usr/lib64/qt-3.3/bin:/usr/local/bin:/bin:/usr/bin
setenv LD_LIBRARY_PATH /usr/local/gcc473/lib64:/usr/local/gcc473/lib:/usr/local/gcc473/root_v5.34.14/lib:/usr/local/gcc473/root_v5.34.14/lib/root:/home/takhsm/app/lib:/usr/local/gcc473/root_v5.34.14:/home/takhsm/app/Mars/Mars_V2-15-8:/home/takhsm/lib/lib
"""

    strPJ = strPJ + """
cd {0}
{1}
""".format(pathDirWork, strCmd)
    filePJ.write(strPJ)
    filePJ.close()
    os.chmod(nameFilePJ, 0744)
    if jobname=="":
        aCmd = ['pjsub', './{0}'.format(nameFilePJ)]
    else:
        aCmd = ['pjsub', './{0}'.format(nameFilePJ), '-N', '{0}'.format(jobname)]
    print aCmd
    subprocess.call(aCmd)
