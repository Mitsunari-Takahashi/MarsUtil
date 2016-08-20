#!/bin/env python
import os
import subprocess


def SubmitPJ(strCmd, pathDirWork, strSuffix="", strRscGrp="B"):
    os.chdir(pathDirWork)
    print strCmd
    nameFilePJ = "pj{0}.csh".format(strSuffix)
    filePJ = open(nameFilePJ,"w")
    strPJ = """#!/bin/tcsh
#------ pjsub option --------#
#PJM -L "rscunit=common"
#PJM -L "rscgrp={0}"
#PJM -L "vnode=1"
#------- Program execution -------#
setenv ROOTSYS /home/takhsm/app/root_v5.34.24
setenv MARSSYS /home/takhsm/app/Mars/Mars_V2-15-8_oldROOT
setenv PATH /home/takhsm/app/Mars/Mars_V2-15-8_oldROOT:/home/takhsm/app/oldROOT/bin:/home/takhsm/app/anaconda2/bin:/home/takhsm/CTA_MC/Chimp/Chimp:/usr/include/mysql:/home/takhsm/app/cmake/3.3.0:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/home/takhsm/CTA_MC/corsika_simtelarray_Prod3/hessioxxx/bin:/home/takhsm/CTA_MC/corsika_simtelarray_Prod3/std:/usr/local/bin:/bin:/usr/bin
setenv LD_LIBRARY_PATH /home/takhsm/app/root_v5.34.24/lib:/home/takhsm/app/Mars/Mars_V2-15-8_oldROOT:/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/home/takhsm/app/lib
cd {1}
{2}
""".format(strRscGrp, pathDirWork, strCmd)
    filePJ.write(strPJ)
    filePJ.close()
    os.chmod(nameFilePJ, 0744)
    aCmd = ['pjsub', './{0}'.format(nameFilePJ)]
    print aCmd
    subprocess.call(aCmd)
