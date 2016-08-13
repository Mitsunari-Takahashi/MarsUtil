#!/bin/env python
"""General utility file of classes and methods for MAGIC data analysis. 
Start with : python -i pMyMarsUtil.py
Make an object of QuickMARS or SlowMARS
QuickMARS: For daily anlaysis, flare advocate.
SlowMARS: For analysis in detail. You should know your data's DC level.
"""
from astropy.time import Time
import os
import os.path as path
import shutil
import subprocess
from datetime import datetime
import re
import string
import glob
from pGetLC_bins import GetLC_bins


class SettingsDC:
"""Class for settings of quate, image cleaning and tuning of MC, depending on DC.
SettingsDC(naDC=<DC in nA>, bReducedHV=False)
"""
    def __init__(self, naDC=2000., bReducedHV=False):
        self.naDC = naDC
        self.bReducedHV = bReducedHV
        if self.bReducedHV==False:
            if self.naDC<=2000:
                self.aCleaning = [6.0, 3.5]
            elif self.naDC<=3000:
                self.aCleaning = [7.0, 4.5]
            elif self.naDC<=5000:
                self.aCleaning = [8.0, 5.0]
            elif self.naDC<=8000:
                self.aCleaning = [9.0, 5.5]
            else:
                print 'The DC is not acceptable for this class.'
        else:
            if self.naDC<=5000:
                self.aCleaning = [10.0, 6.0]
            elif self.naDC<=8000:
                self.aCleaning = [11.0, 7.0]
            elif self.naDC<=12000:
                self.aCleaning = [13.0, 8.0]
            elif self.naDC<=20000:
                self.aCleaning = [14.0, 9.0]
            else:
                print 'The DC is not acceptable for this class.'
        if bReducedHV==True or naDC>4000:
            self.bTunedTrain = True
        else:
            self.bTunedTrain = False
        if bReducedHV==True or naDC>2000:
            self.bTunedTest = True
        else:
            self.bTunedTest = False
    def getName(self):
        strName = "DC{0}".format(int(self.naDC))
        if self.bReducedHV==True:
            strName = strName + "_ReducedHV"
        return strName
    def getNaDC(self, nForm='float'):
        """Get the cut value for DC in nA
.getNaDC(nForm='int')
nForm: int, float, str"""
        if nForm=='int':
            return int(self.naDC)
        elif nForm=='float':
            return self.naDC
        elif nForm=='str':
            return str(int(self.naDC))
        else:
            print "Wrong format."
            return -1
    def getBoolReducedHV(self):
        return self.bReducedHV
    def getLVsCleaning(self):
        return self.aCleaning
    def getBoolTunedTrain(self):
        return self.bTunedTrain
    def getBoolTunedTest(self):
        return self.bTunedTest

class QuickMARS:
    """Class for slow analysis. You should know which data file is corresponding to each cut condition.
QuickMARS(nameSrc, strNight, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=3000., bReducedHV=False)
  Ex) qma = QuickMARS('1ES1959+650', '2016-04-29', ZenithCut='35to50', TransCut9km='No', CloudCut='45', DcCut='4500')
1) qma = SlowMARS(nameSrc, strTitle, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=2000., bReducedHV=False)
2) qma.makeDirs()
== No Moon ==
3) Put your superstar files to the created directories
4) qma.downloadData(password, "S")
5) qma.quate()
6) qma.melibea()
7) qma.odie(bLE=True, bFR=True, bHE=False)
8) qma.flute(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc=False, bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1)
== Moderate Moon ==
3) Put your superstar files to the created directories
4) qma.downloadData(password, "S")
5) qma.quate()
6) qma.melibea()
7) qma.odie(bLE=True, bFR=True, bHE=False)
8) qma.downloadData(password, "ssignal")
9) qma.ssignal()
10) qma.starMC(bTrain=False, bTest=True)
11) qma.superstarMC(bTrain=False, bTest=True)
12) qma.selectmc(False, True)
13) qma.melibeaMC(False, True)
14) qma.flute(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc=True, bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1)
== Decent Moon ==
3) Put your calibrated files to the created directories
4) qma.downloadData(password, "ssignal")
5) qma.downloadData(password, "Y", 1, bPjsub=True)
6) qma.ssignal()
7) qma.starMC(bTrain=True, bTest=True)
8) qma.star()
9) qma.starOFF()
10) qma.superstar()
11) qma.superstarMC(bTrain=True, bTest=True)
12) qma.superstarOFF()
13) qma.selectmc(True, True)
14) qma.coach()
15) qma.melibea(True)
15) qma.melibeaMC(False, True)
16) qma.odie(bLE=True, bFR=True, bHE=False)
17) qma.flute(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc=True, bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1)
"""
    def __init__(self, nameSrc, strNight, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=3000., bReducedHV=False):
        self.PATH_MARSSYS = os.environ['MARSSYS']
        self.PATH_PYTHON_MODULE_MINE = os.environ['PATH_PYTHON_MODULE_MINE']
        #self.PATH_BASE = "/Volumes/SHUNZEI/MAGIC" #"/Volumes/KARYU/MAGIC"
        self.PATH_BASE = os.environ['PATH_MARS_BASE']
        #self.PATH_DIR_RC = "/Users/Mitsunari/MAGIC/RC"
        self.PATH_DIR_RC = os.environ['PATH_MARS_RC_MINE']
        self.nameSrc = nameSrc
        self.timeThisNight = Time(strNight, format='iso', in_subfmt='date', out_subfmt='date', scale='utc')
        self.titleAnalysis = self.timeThisNight
        self.isoThisNight = self.timeThisNight.value
        #self.mjdThisNight = int(self.timeThisNight.mjd)
        #self.ZenithCut = ZenithCut
        self.setZenithCut(ZenithCut)
        self.TransCut9km = TransCut9km
        self.CloudCut = CloudCut
        self.DcCut = str(int(naCutDC))
        self.settingsDC = SettingsDC(naCutDC, bReducedHV)
        self.nameCfg = 'ZenithCut{0}_TransCut9km{1}_CloudCut{2}_{3}'.format(self.getZenithCut(), self.getTransCut9km(), self.getCloudCut(), self.settingsDC.getName())
        #self.nameCfg = 'ZenithCut{0}_TransCut9km{1}_CloudCut{2}_DcCut{3}'.format(self.getZenithCut(), self.getTransCut9km(), self.getCloudCut(), self.getDcCut())
        self.pathDirSpot = '{0}/{1}/{2}'.format(self.getPathBase(), self.getSourceName(), self.getTitleAnalysis())
        self.pathDirCondition = '{0}/{1}'.format(self.getPathDirSpot(), self.getConfigName())
        self.setSubDirs()

    def setSubDirs(self):
        """Set paths of sub-directories.
.setSubDirs()
"""
        self.pathDirSsignal = '{0}/ssignal'.format(self.getPathDirSpot())
        self.pathDirStar = '{0}/star'.format(self.getPathDirSpot())
        self.pathDirStarMC = '{0}/starMC'.format(self.getPathDirSpot())
        self.pathDirSuperstarOFF = '{0}/superstarOFF'.format(self.getPathDirSpot())
        self.pathDirSuperstarCrab = '{0}/superstarCrab'.format(self.getPathDirSpot())
        self.pathDirStarOFF = '{0}/starOFF'.format(self.getPathDirSpot())
        self.pathDirStarCrab = '{0}/starCrab'.format(self.getPathDirSpot())
        self.pathDirCalibrated = '{0}/calibrated'.format(self.getPathDirSpot())
        self.pathDirCalibratedOFF = '{0}/standard/OFF/calibrated'.format(self.getPathBase())
        self.pathDirSuperstarMC = '{0}/superstarMC'.format(self.getPathDirSpot())
        self.pathDirMelibeaMC = '{0}/standard/melibeaMC/za{1}'.format(self.getPathBase(), self.getZenithCut())
        self.pathDirMelibeaNonStdMC = '{0}/melibeaMC'.format(self.getPathDirSpot())
        self.pathDirSuperstar = '{0}/superstar'.format(self.getPathDirSpot())
        self.pathDirQuate = '{0}/quate'.format(self.getPathDirCondition())
#        self.pathDirQuateOFF = '{0}/{1}/{2}/{3}/quateOFF'.format(self.getPathDirSpot(), self.getConfigName())
        self.pathDirQuateCrab = '{0}/quateCrab'.format(self.getPathDirCondition())
        self.pathDirMelibea = '{0}/melibea'.format(self.getPathDirCondition())
        self.pathDirMelibeaCrab = '{0}/melibeaCrab'.format(self.getPathDirCondition())
        self.pathDirOdie = '{0}/odie'.format(self.getPathDirCondition())
        self.pathDirOdieCrab = '{0}/odieCrab'.format(self.getPathDirCondition())
        self.pathDirCaspar = '{0}/caspar'.format(self.getPathDirCondition())
        self.pathDirFlute = '{0}/flute'.format(self.getPathDirCondition())
        self.pathDirFluteCrab = '{0}/fluteCrab'.format(self.getPathDirCondition())
        self.pathDirCoach = '{0}/standard/coach/za{1}'.format(self.getPathBase(), self.getZenithCut())
        self.pathDirCoachNonStd = '{0}/coachNonStd'.format(self.getPathDirSpot())
        
    def help(self, strCmd=""):
        if strCmd=="makeDirs" or strCmd=="":
            print ".makeDirs(bSuperstar=True, bQuate=True, bMelibea=True, bOdie=True, bOdieCrab=True, bCaspar=False, bFlute=True, bStarMC=False, bSuperstarMC=False, bMelibeaMC=False, bMelibeaCrab=False, bFluteCrab=False, bQuateCrab=False, bSsignal=False, bStarOFF=False, bCoachNonStd=False)"
        if strCmd=="downloadData" or strCmd=="":
            print ".downloadData(password, cDataType='S', verData=1)"
        if strCmd=="quate" or strCmd=="":
            print ".quate()"
        if strCmd=="quateCrab" or strCmd=="":
            print ".quateCrab()"
        if strCmd=="ssignal" or strCmd=="":
            print ".ssignal(self, bTighterCleaning=False)"
        if strCmd=="star" or strCmd=="":
            print ".star()"
        if strCmd=="starMC" or strCmd=="":
            print ".starMC(bTrain=False, bTest=True)"
        if strCmd=="starOFF" or strCmd=="":
            print ".starOFF()"
        if strCmd=="starCrab" or strCmd=="":
            print ".starCrab()"
        if strCmd=="superstarMC" or strCmd=="":
            print ".superstarMC(bTrain=False, bTest=True))"
        if strCmd=="superstarOFF" or strCmd=="":
            print ".superstarOFF()"
        if strCmd=="superstarCrab" or strCmd=="":
            print ".superstarCrab()"
        if strCmd=="coach" or strCmd=="":
            print ".coach()"
        if strCmd=="melibea" or strCmd=="":
            print ".melibea(pathCoachNonStd=self.getPathDirCoach())"
        if strCmd=="melibeaMC" or strCmd=="":
            print ".melibeaMC(bTrain=False, bTest=True, pathCoachNonStd=self.getPathDirCoach())"
        if strCmd=="melibeaCrab" or strCmd=="":
            print ".melibeaCrab()"
        if strCmd=="odie" or strCmd=="":
            print ".odie(bLE=True, bFR=True, bHE=False)"
        if strCmd=="odieCrab" or strCmd=="":
            print ".odieCrab(bLE=True, bFR=True, bHE=False)"
        if strCmd=="flute" or strCmd=="":
            print ".flute(eth=300, assumedSpectrum="", redshift="", bNightWise=True, bRunWise=True, bSingleBin=False)"
        if strCmd=="fluteCrab" or strCmd=="":
            print ".fluteCrab(eth=300, bMelibeaNonStdMc=False)"

    def setTitle(self, strTitle):
        self.title = strTitle
    def getTitle(self):
        return self.title
    def setZenithCut(self, strCut):
        if strCut=='No' or strCut=='no':
            self.ZenithCut = 'No'
            self.ZenithCutLow = 0
            self.ZenithCutUp = 70
            return 0
        elif len(strCut)==6 and strCut[2:4]=="to" and int(strCut[0:2])>=0 and int(strCut[4:6])<=70 and int(strCut[0:2])<int(strCut[4:6]) :
            self.ZenithCut = strCut
            self.ZenithCutLow = int(strCut[0:2])
            self.ZenithCutUp = int(strCut[4:6])
        else:
            print strCut, "cannot be set as ZenithCut."
            return 1
    # def setZenithCut(self, nCutLow, nCutUp):
    #     if nCutLow>=0 and nCutUp<=100 and nCutLow<nCutUp:
    #         self.ZenithCut = '{0}to{1}'.format(nCutLow, nCutUp)
    #         self.ZenithCutLow = float(nCutLow)
    #         self.ZenithCutUp = float(nCutUp)
    #         return 0
    #     else:
    #         print nCutLow, 'to', nCutUp, "cannot be set as ZenithCut."
    #         return 1
    def getZenithCut(self):
        return self.ZenithCut
    def getZenithCutLow(self):
        return self.ZenithCutLow
    def getZenithCutUp(self):
        return self.ZenithCutUp
    def setTransCut9km(self, nCutVal):
        if nCutVal=='No' or nCutVal=='no':
            self.TransCut9km = 'No'
            return 0            
        elif nCutVal>=0 and nCutVal<=100:
            self.TransCut9km = '{0}'.format(nCutVal)
            return 0
        else:
            print nCutVal, "cannot be set as TransCut9km."
            return 1
    def setCloudCut(self, nCutVal):
        if nCutVal=='No' or nCutVal=='no':
            self.CloudCut = 'No'
            return 0            
        elif nCutVal>=0 and nCutVal<=100:
            self.CloudCut = '{0}'.format(nCutVal)
            return 0
        else:
            print nCutVal, "cannot be set as CloudCut."
            return 1
    def setDcCut(self, nCutVal):
        if nCutVal=='No' or nCutVal=='no':
            self.DcCut = 'No'
            return 0            
        elif nCutVal>=0:
            self.DcCut = '{0}'.format(nCutVal)
            return 0
        else:
            print nCutVal, "cannot be set as DcCut."
            return 1
    def getTransCut9km(self):
        return self.TransCut9km
    def getCloudCut(self):
        return self.CloudCut
    def getSettingsDC(self):
        return self.settingsDC
    def getDcCut(self):
        return self.DcCut
    def getPathBase(self):
        return self.PATH_BASE
    def getPathMarssys(self):
        return self.PATH_MARSSYS
    def getPathPythonModuleMine(self):
        return self.PATH_PYTHON_MODULE_MINE
    def getPathDirRc(self):
        return self.PATH_DIR_RC
    def getConfigName(self):
        return self.nameCfg
    def getSourceName(self):
        return self.nameSrc
    def getTimeThisNight(self, strFmt='', bInt=False):
        timeTmp = self.timeThisNight
        if strFmt=='':
            return timeTmp
        elif strFmt=='short':
            strTemp = timeTmp.value
            strShort = '{0}{1}{2}'.format(strTemp[:4], strTemp[5:7], strTemp[8:])
            return strShort
        else:
            timeTmp.format = strFmt
            if bInt==True:
                return int(timeTmp.value)
            else:
                return timeTmp.value
    def getIsoThisNight(self):
        return self.isoThisNight
    def getTitleAnalysis(self):
        return self.titleAnalysis
#    def getMjdThisNight(self):
#       return self.mjdThisNight
    def getPathDirSpot(self):
        return self.pathDirSpot
    def getPathDirCondition(self):
        return self.pathDirCondition
    def getPathDirSsignal(self):
        return self.pathDirSsignal
    def getPathDirCalibrated(self):
        return self.pathDirCalibrated
    def getPathDirCalibratedOFF(self):
        return self.pathDirCalibratedOFF
    def getPathDirStar(self):
        return self.pathDirStar
    def getPathDirStarMC(self):
        return self.pathDirStarMC
    def getPathDirStarOFF(self):
        return self.pathDirStarOFF
    def getPathDirStarCrab(self):
        return self.pathDirStarCrab
    def getPathDirSuperstarOFF(self):
        return self.pathDirSuperstarOFF
    def getPathDirSuperstarCrab(self):
        return self.pathDirSuperstarCrab
    def getPathDirSuperstarMC(self):
        return self.pathDirSuperstarMC
    def getPathDirMelibeaMC(self):
        return self.pathDirMelibeaMC
    def getPathDirMelibeaNonStdMC(self):
        return self.pathDirMelibeaNonStdMC
    def getPathDirSuperstar(self):
        return self.pathDirSuperstar
    def getPathDirQuate(self):
        return self.pathDirQuate
    def getPathDirQuateOFF(self):
        return self.pathDirQuateOFF
    def getPathDirQuateCrab(self):
        return self.pathDirQuateCrab
    def getPathDirMelibea(self):
        return self.pathDirMelibea
    def getPathDirMelibeaCrab(self):
        return self.pathDirMelibeaCrab
    def getPathDirOdie(self):
        return self.pathDirOdie
    def getPathDirOdieCrab(self):
        return self.pathDirOdieCrab
    def getPathDirCaspar(self):
        return self.pathDirCaspar
    def getPathDirFlute(self):
        return self.pathDirFlute
    def getPathDirFluteCrab(self):
        return self.pathDirFluteCrab
    def getPathDirCoach(self):
        return self.pathDirCoach
    def getPathDirCoachNonStd(self):
        return self.pathDirCoachNonStd

    def makeDirs(self, bSuperstar=True, bQuate=True, bQuateCrab=True, bMelibea=True, bOdie=True, bOdieCrab=True, bCaspar=True, bFlute=True, bSuperstarCrab=True, bStarCrab=True, bStar=True, bStarMC=True, bSuperstarMC=True, bMelibeaNonStdMC=True, bMelibeaCrab=True, bFluteCrab=True, bSsignal=True, bStarOFF=True, bSuperstarOFF=True, bCoachNonStd=True):
        """Make directories for analysis, following the configuration set by setSubDirs.
.makeDirs(bSuperstar=True, bQuate=True, bQuateCrab=True, bMelibea=True, bOdie=True, bOdieCrab=True, bCaspar=True, bFlute=True, bSuperstarCrab=True, bStarCrab=True, bStar=True, bStarMC=True, bSuperstarMC=True, bMelibeaNonStdMC=True, bMelibeaCrab=True, bFluteCrab=True, bSsignal=True, bStarOFF=True, bSuperstarOFF=True, bCoachNonStd=True):
"""
        if bSsignal==True:
            #os.makedirs('{0}'.format(self.getPathDirSsignal())) 
            aTel = ['M1', 'M2']
            for tel in aTel:
                pathDirWork = '{0}/{1}'.format(self.getPathDirSsignal(), tel)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
        if bStar==True:
            aTel = ['M1', 'M2']
            for tel in aTel:
                pathDirWork = '{0}/{1}'.format(self.getPathDirStar(), tel)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
                os.chdir(pathDirWork)
                print os.getcwd()
        if bStarMC==True:
            aTel = ['M1', 'M2']
            aSet = ['TRAIN', 'TEST']
            for tel in aTel:
                for dset in aSet:
                    pathDirWork = '{0}/{1}/{2}'.format(self.getPathDirStarMC(), tel, dset)
                    if path.exists(pathDirWork)==False:
                        os.makedirs(pathDirWork)
                    os.chdir(pathDirWork)
                    print os.getcwd()
                    #os.makedirs('TRAIN')
                    #os.makedirs('TEST')
#                shutil.copy('{0}/star_{1}_OSA.rc'.format(self.getPathDirRc(), tel), './star_{0}_{1}.rc'.format(tel, self.getTimeThisNight('short', True)))
                #pathDirWork = '{0}/{1}'.format(self.getPathDirStarMC(), tel)
        if bStarOFF==True:
#            os.makedirs('{0}'.format(self.getPathDirStarOFF())) 
            aTel = ['M1', 'M2']
            for tel in aTel:
                pathDirWork = '{0}/{1}'.format(self.getPathDirStarOFF(), tel)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
        if bStarCrab==True:
            #os.makedirs('{0}'.format(self.getPathDirStarCrab())) 
            aTel = ['M1', 'M2']
            for tel in aTel:
                pathDirWork = '{0}/{1}'.format(self.getPathDirStarCrab(), tel)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
        if bSuperstarMC==True:
            aSet = ['TRAIN', 'TEST']
            for dset in aSet:
                pathDirWork = '{0}/{1}'.format(self.getPathDirSuperstarMC(), dset)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
                    os.chdir(pathDirWork)
                    print os.getcwd()
        if bSuperstarOFF==True:
            pathDirWork = self.getPathDirSuperstarOFF()
            if path.exists(pathDirWork)==False:
                os.makedirs(pathDirWork)
                os.chdir(pathDirWork)
                print os.getcwd()
        if bSuperstarCrab==True:
            pathDirWork = self.getPathDirSuperstarCrab()
            if path.exists(pathDirWork)==False:
                os.makedirs(pathDirWork)
                os.chdir(pathDirWork)
                print os.getcwd()
        if bCoachNonStd==True:
            pathDirWork = self.getPathDirCoachNonStd()
            if path.exists(pathDirWork)==False:
                os.makedirs(pathDirWork)
                os.chdir(pathDirWork)
                print os.getcwd()
        if bMelibeaNonStdMC==True:
            aSet = ['TRAIN', 'TEST']
            for dset in aSet:
            #os.makedirs('{0}'.format(self.getPathDirMelibeaMC())) 
                pathDirWork = '{0}/{1}'.format(self.getPathDirMelibeaNonStdMC(), dset)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
                    os.chdir(pathDirWork)
                    print os.getcwd()
                    #os.makedirs('TRAIN')
                    #os.makedirs('TEST')
        if bSuperstar==True and path.exists('{0}'.format(self.getPathDirSuperstar()))==False:
            os.makedirs('{0}'.format(self.getPathDirSuperstar())) 
        if bQuate==True and path.exists('{0}'.format(self.getPathDirQuate()))==False:
            os.makedirs('{0}'.format(self.getPathDirQuate()))
        if bQuateCrab==True and path.exists('{0}'.format(self.getPathDirQuateCrab()))==False:
            os.makedirs('{0}'.format(self.getPathDirQuateCrab()))
        if bMelibea==True and path.exists('{0}'.format(self.getPathDirMelibea()))==False:
            os.makedirs('{0}'.format(self.getPathDirMelibea())) 
        if bMelibeaCrab==True and path.exists('{0}'.format(self.getPathDirMelibeaCrab()))==False:
            os.makedirs('{0}'.format(self.getPathDirMelibeaCrab())) 
        if bOdie==True and path.exists('{0}'.format(self.getPathDirOdie()))==False:
            os.makedirs('{0}'.format(self.getPathDirOdie())) 
        if bOdieCrab==True and path.exists('{0}'.format(self.getPathDirOdieCrab()))==False:
            os.makedirs('{0}'.format(self.getPathDirOdieCrab())) 
        if bCaspar==True and path.exists('{0}'.format(self.getPathDirCaspar()))==False:
            os.makedirs('{0}'.format(self.getPathDirCaspar()))
        if bFlute==True:
            #os.makedirs('{0}'.format(self.getPathDirFlute()))
            pathDirWork = ''
            aBinning = ['single-bin', 'run-wise', 'night-wise', 'custom']
            for wise in aBinning:
                pathDirWork = '{0}/{1}'.format(self.getPathDirFlute(), wise)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
                os.chdir(pathDirWork)
                print os.getcwd()
            os.chdir('..')
        if bFluteCrab==True:
            pathDirWork = ''
            aBinning = ['single-bin']
            for wise in aBinning:
                pathDirWork = '{0}/{1}'.format(self.getPathDirFluteCrab(), wise)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
                os.chdir(pathDirWork)
                print os.getcwd()
            os.chdir('..')

    def quate(self):
        SetEnvironForMARS("5.34.24")
        os.chdir(self.getPathDirQuate())
        print os.getcwd()
        #if path.exists('{0}/quate_{1}.rc'.format(self.getPathDirRc(), self.getConfigName()))==False:
         #   print '{0}/quate_{1}.rc'.format(self.getPathDirRc(), self.getConfigName()), 'does not exist.'
          #  return 1
        #shutil.copy('{0}/quate_{1}.rc'.format(self.getPathDirRc(), self.getConfigName()), './quate.rc')

        if self.getTransCut9km()!='No':
            bTransCut = 'yes'
            vTransCut = float(self.getTransCut9km())/100.
        else:
            bTransCut = 'no'
            vTransCut = 1.00
        if self.getCloudCut()!='No':
            bCloudCut = 'yes'
            vCloudCut = int(self.getCloudCut())
        else:
            bCloudCut = 'no'
            vCloudCut = 100
        strQuate="""
UseDCCuts: yes
DCMax: {0} // for stereo and MAGIC-II, while 1500. for only MAGIC-I
ZdMin: {1}
ZdMax: {2}
UseAerosolTrans9km: {3}
MinAerosolTrans9km: {4}
UseCloudCuts: {5}
CloudinessMax: {6}
""".format(self.getDcCut(), self.getZenithCutLow(), self.getZenithCutUp(), bTransCut, vTransCut, bCloudCut, vCloudCut)
        pathRcNew = '{0}/quate.rc'.format(self.getPathDirQuate())
        rcNew = open(pathRcNew, 'w') 
        rcNew.write(strQuate)
        rcOrig = open('{0}/mrcfiles/quate.rc'.format(self.getPathMarssys()), 'r')
        rcCopied = rcOrig.read()
        rcNew.write(rcCopied)
        rcOrig.close()
        rcNew.close()
        subprocess.call(['head', pathRcNew])
        aCmd = [ 'quate', '-b', '--stereo', '-f', '--config={0}'.format(pathRcNew), '--ind={0}'.format(self.getPathDirSuperstar()), '--out=.', '--times' ]
#        aCmd = [ 'quate', '-b', '--stereo', '-f', '--config={0}'.format(pathRcNew), '--ind={0}'.format(self.getPathDirSuperstar()), '--out=.' ]
        print aCmd
        subprocess.call(aCmd)
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', 'Overview.pdf'])
            subprocess.call(['open', '.'])
        elif os.environ['OSTYPE']=='linux':
            subprocess.call(['evince', 'Overview.pdf'])
        print "M1 excluded:"
        subprocess.call(['cat', '{0}/excluded_1.times'.format(self.getPathDirQuate())])
        print "M2 excluded:"
        subprocess.call(['cat', '{0}/excluded_2.times'.format(self.getPathDirQuate())])

    def quateOFF(self):
        SetEnvironForMARS("5.34.24")
        os.chdir(self.getPathDirSuperstarOFF())
        print os.getcwd()
        #if path.exists('{0}/quate_{1}.rc'.format(self.getPathDirRc(), self.getConfigName()))==False:
         #   print '{0}/quate_{1}.rc'.format(self.getPathDirRc(), self.getConfigName()), 'does not exist.'
          #  return 1
        #shutil.copy('{0}/quate_{1}.rc'.format(self.getPathDirRc(), self.getConfigName()), './quate.rc')
        aCmd = [ 'quate', '-b', '--stereo', '-f', '--config={0}/quate.rc'.format(self.getPathDirQuate()), '--ind={0}'.format(self.getPathDirSuperstarOFF()), '--out={0}'.format(self.getPathDirSuperstarOFF()) ]
        print aCmd
        subprocess.call(aCmd)
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', 'Overview.pdf'])
            subprocess.call(['open', '.'])
        elif os.environ['OSTYPE']=='linux':
            subprocess.call(['evince', 'Overview.pdf'])
        #print "M1 excluded:"
        #subprocess.call(['cat', '{0}/excluded_1.times'.format(self.getPathDirQuate())])
        #print "M2 excluded:"
        #subprocess.call(['cat', '{0}/excluded_2.times'.format(self.getPathDirQuate())])

    def quateCrab(self):
        SetEnvironForMARS("5.34.24")
        os.chdir(self.getPathDirQuateCrab())
        print os.getcwd()
        aCmd = [ 'quate', '-b', '--stereo', '-f', '--config={0}/quate.rc'.format(self.getPathDirQuate()), '--ind={0}'.format(self.getPathDirSuperstarCrab()), '--out=.', '--times' ]
        print aCmd
        subprocess.call(aCmd)
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', 'Overview.pdf'])
            subprocess.call(['open', '.'])
        elif os.environ['OSTYPE']=='linux':
            subprocess.call(['evince', 'Overview.pdf'])
        print "M1 excluded:"
        subprocess.call(['cat', '{0}/excluded_1.times'.format(self.getPathDirQuateCrab())])
        print "M2 excluded:"
        subprocess.call(['cat', '{0}/excluded_2.times'.format(self.getPathDirQuateCrab())])

    def coach(self):
        pathDirWork = self.getPathDirCoachNonStd()
        os.chdir(pathDirWork)
        print os.getcwd()
       # Modify RC file
        strRcAdd = """RF.mcdata: {0}/TRAIN/GA_za{1}_TRAIN_S_wr.root
RF.data:  {2}/good/20*_S_*.root
RF.outpath: {3}
RF.outname: coach_{4}
RF.zdmin: {5}
RF.zdmax: {6}
""".format(self.getPathDirSuperstarMC(), self.getZenithCut(), self.getPathDirSuperstarOFF(), self.getPathDirCoachNonStd(), self.getConfigName(), self.getZenithCutLow(), self.getZenithCutUp())
        pathRcNew = './coach_{0}.rc'.format(self.getConfigName())
        rcNew = open(pathRcNew, 'w') 
        rcNew.write(strRcAdd)
        rcOrig = open('{0}/mrcfiles/coach.rc'.format(self.getPathMarssys()), 'r')
        rcCopied = rcOrig.read()
        #print rcCopied
        rcNew.write(rcCopied)
        rcOrig.close()
        rcNew.close()
        subprocess.call(['head', pathRcNew])
        SetEnvironForMARS("5.34.24")
        aCmd = [ 'coach', '--config=./coach_{0}.rc'.format(self.getConfigName()), '-RFgh', '-RFdisp', '-LUTs', '-q', '-b' ]
        print aCmd
        subprocess.call(aCmd)
        aCmd =  'coach --config=./coach_{0}.rc -RFgh -RFdisp -LUTs -q -b'.format(self.getConfigName())
        #SubmitPJ(aCmd, pathDirWork, 'Coach')
        #bCmd =  'coach --config=./coach_{0}.rc -RFdisp -q -b'.format(self.getConfigName())
        #SubmitPJ(bCmd, pathDirWork, 'RFdisp')
        #cCmd =  'coach --config=./coach_{0}.rc -LUTs -q -b'.format(self.getConfigName())
        #SubmitPJ(cCmd, pathDirWork, 'LUTs')
        
    def melibea(self, bCoachNonStd=""):
        if not isinstance(bCoachNonStd, bool):
            bCoachNonStd=self.getSettingsDC().getBoolTunedTrain()
        if bCoachNonStd==True:
            pathCoachNonStd = self.getPathDirCoachNonStd()
        else:
            pathCoachNonStd=self.getPathDirCoach()
#        if pathCoachNonStd=="":
#           pathCoachNonStd = self.getPathDirCoach()
        os.chdir(self.getPathDirMelibea())
        print os.getcwd()
        SetEnvironForMARS("5.34.24")
        strZd = """
# Zenith Cuts
RF.zdmin: default: {0}
RF.zdmax: default: {1}
""".format(self.getZenithCutLow(), self.getZenithCutUp())
        pathRcNew = '{0}/melibea_stereo.rc'.format(self.getPathDirMelibea())
        rcNew = open(pathRcNew, 'w') 
        rcNew.write(strZd)
        rcOrig = open('{0}/mrcfiles/melibea_stereo.rc'.format(self.getPathMarssys()), 'r')
        rcCopied = rcOrig.read()
        rcNew.write(rcCopied)
        rcOrig.close()
        rcNew.close()
        aCmd = [ 'melibea', '-b', '-q', '-f', '--config={0}'.format(pathRcNew), '--ind={0}/20*_S_*.root'.format(self.getPathDirSuperstar()), '--out=./', '--stereo', '--rf', '--rftree={0}/RF.root'.format(pathCoachNonStd), '--calc-disp-rf', '--rfdisptree={0}/disp1/DispRF.root'.format(pathCoachNonStd), '--calc-disp2-rf', '--rfdisp2tree={0}/disp2/DispRF.root'.format(pathCoachNonStd), '--calcstereodisp', '--disp-rf-sstrained', '-erec', '--etab={0}/Energy_Table.root'.format(pathCoachNonStd), '--timeslices={0}/excluded.times'.format(self.getPathDirQuate()) ]
        print aCmd
        subprocess.call(aCmd)

    def melibeaCrab(self, bCoachNonStd=False):
        if bCoachNonStd==True:
            pathCoachNonStd = self.getPathDirCoachNonStd()
        else:
            pathCoachNonStd=self.getPathDirCoach()
#        if pathCoachNonStd=="":
#            pathCoachNonStd = self.getPathDirCoach()
        os.chdir(self.getPathDirMelibeaCrab())
        print os.getcwd()
        SetEnvironForMARS("5.34.24")
        aCmd = [ 'melibea', '-b', '-q', '-f', '--config={0}/melibea_stereo.rc'.format(self.getPathDirMelibea()), '--ind={0}/20*_S_*.root'.format(self.getPathDirSuperstarCrab()), '--out=./', '--stereo', '--rf', '--rftree={0}/RF.root'.format(pathCoachNonStd), '--calc-disp-rf', '--rfdisptree={0}/disp1/DispRF.root'.format(pathCoachNonStd), '--calc-disp2-rf', '--rfdisp2tree={0}/disp2/DispRF.root'.format(pathCoachNonStd), '--calcstereodisp', '--disp-rf-sstrained', '-erec', '--etab={0}/Energy_Table.root'.format(pathCoachNonStd), '--timeslices={0}/excluded.times'.format(self.getPathDirQuateCrab()) ]
        print aCmd
        subprocess.call(aCmd)

#    def melibeaMC(self, bTrain=False, bTest=True, bCoachNonStd=False):
    def melibeaMC(self, bTrain="", bTest="", bCoachNonStd=""):
        if not isinstance(bTrain, bool):
            bTrain=self.getSettingsDC().getBoolTunedTrain() 
        if not isinstance(bTest, bool):
            bTest=self.getSettingsDC().getBoolTunedTest()
        if not isinstance(bCoachNonStd, bool):
            bCoachNonStd=self.getSettingsDC().getBoolTunedTrain()
        SetEnvironForMARS("5.34.24")
        #if pathCoachNonStd=="":
        #    pathCoachNonStd=self.getPathDirCoach()
        if bCoachNonStd==True:
            pathCoachNonStd = self.getPathDirCoachNonStd()
        else:
            pathCoachNonStd=self.getPathDirCoach()
        aDSet=[]
        if bTrain==True:
            aDSet.append('TRAIN')
        if bTest==True:
            aDSet.append('TEST')
        for dset in aDSet:
            pathDirWork = '{0}/{1}'.format(self.getPathDirMelibeaNonStdMC(), dset)
            os.chdir(pathDirWork)
            print os.getcwd()
            aCmd = [ 'melibea', '-b', '-q', '-f', '--config={0}/melibea_stereo.rc'.format(self.getPathDirMelibea()), '--ind={0}/{1}/GA_za{2}_*{1}_S_wr.root'.format(self.getPathDirSuperstarMC(), dset, self.getZenithCut()), '--out=./', '--stereo', '--rf', '--rftree={0}/RF.root'.format(pathCoachNonStd), '--calc-disp-rf', '--rfdisptree={0}/disp1/DispRF.root'.format(pathCoachNonStd), '--calc-disp2-rf', '--rfdisp2tree={0}/disp2/DispRF.root'.format(pathCoachNonStd), '--calcstereodisp', '--disp-rf-sstrained', '-erec', '--etab={0}/Energy_Table.root'.format(pathCoachNonStd), '-mc' ]
            print aCmd
            subprocess.call(aCmd)

    def melibeaNonStdMC(self, bCoachNonStd=True):
        if bCoachNonStd==True:
            pathCoachNonStd = self.getPathDirCoachNonStd()
        else:
            pathCoachNonStd=self.getPathDirCoach()
        #if pathCoachNonStd=="":
        #    pathCoachNonStd = self.getPathDirCoach()
        os.chdir(self.getPathDirMelibeaNonStdMC())
        print os.getcwd()
        SetEnvironForMARS("5.34.24")
        aCmd = [ 'melibea', '-mc', '-b', '-q', '-f', '--config={0}/melibea_stereo.rc'.format(self.getPathDirMelibea()), '--ind={0}/GA_*_S_*.root'.format(self.getPathDirSuperstarMC()), '--out=./', '--stereo', '--rf', '--rftree={0}/RF.root'.format(pathCoachNonStd), '--calc-disp-rf', '--rfdisptree={0}/disp1/DispRF.root'.format(pathCoachNonStd), '--calc-disp2-rf', '--rfdisp2tree={0}/disp2/DispRF.root'.format(pathCoachNonStd), '--calcstereodisp', '--disp-rf-sstrained', '-erec', '--etab={0}/Energy_Table.root'.format(pathCoachNonStd) ]
        print aCmd
        subprocess.call(aCmd)

    def odie(self, bLE=True, bFR=True, bHE=False):
        pathDirWork = ''
        aER = []
        if bLE==True:
            aER.append('LE')
        if bFR==True:
            aER.append('FR')
        if bHE==True:
            aER.append('HE')
        for er in aER:
            pathDirWork = '{0}/{1}'.format(self.getPathDirOdie(), er)
            if path.exists(pathDirWork)==False:
                os.makedirs(pathDirWork)
            os.chdir(pathDirWork)
            print os.getcwd()
            SetEnvironForMARS("5.34.24")
            #shutil.copy('{0}/odie_{1}_{2}.rc'.format(self.getPathDirRc(), self.getConfigName(), er), './odie.rc')
            strData = """Odie.dataName: {0}/20*_Q_*.root
Odie.outFileName: Output_odie_{1}_{2}.root
Odie.deadTime: 26.e-6
""".format(self.getPathDirMelibea(), self.getConfigName(), er)
            strCut = ""
            if er == "LE":
                strCut = """
# For low energy (LE) analysis
# Sensitivity ~ 1.2% Crab 
Odie.analysisEpoch: Jul13
Odie.eRange: LE
Odie.signalCut: 0.02
Odie.psf40: 0.056
Odie.psftailfract: 0.462
Odie.psftailsigma: 0.115
"""
            elif er == "FR":
                strCut = """
# For full range (FR) analysis
# Sensitivity ~ 0.7% Crab 
Odie.analysisEpoch: Jul13
Odie.eRange: FR
Odie.signalCut: 0.009
Odie.psf40: 0.046
Odie.psftailfract: 0.356
Odie.psftailsigma: 0.084
"""
            elif er == "HE":
                strCut = """
# For high energy (HE) analysis
# Sensitivity ~ 1.% Crab
Odie.analysisEpoch: Jul13
Odie.eRange: HE
Odie.signalCut: 0.007
Odie.psf40: 0.037
Odie.psftailfract: 0.356
Odie.psftailsigma: 0.070
"""
            strZenith = """
Odie.minZenith: {0}
Odie.maxZenith: {1}
""".format(self.getZenithCutLow(), self.getZenithCutUp())
            strAdd = strData + strCut + strZenith
            AddToRcFile(strAdd, "{0}/mrcfiles/odie.rc".format(self.getPathMarssys()), "{0}/odie.rc".format(pathDirWork))
            aCmd = [ 'odie', '-b', '-q', '--config=./odie.rc', '--ind={0}/20*_Q_*.root'.format(self.getPathDirMelibea()) ]
            print aCmd
            subprocess.call(aCmd)
            SetEnvironForMARS("5.34.14")
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/SaveTh2OnAndOffCan.C("Output_odie_{1}_{2}.root", "{3}", "{4}_{2}")'.format(self.getPathPythonModuleMine(), self.getConfigName(), er, self.getSourceName(), self.getTimeThisNight('short'))])
            pathImage = '{0}/th2OnAndOffCan_{1}_{2}_{3}.png'.format(pathDirWork, self.getSourceName(), self.getTimeThisNight('short'), er)
            print pathImage
            catchImage(pathImage)
#            if os.environ['OSTYPE'][:6]=='darwin':
#                subprocess.call(['open', 'th2OnAndOffCan_{0}_{1}_{2}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), er)])
#            else:
#                subprocess.call(['eog', 'th2OnAndOffCan_{0}_{1}_{2}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), er)])
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', '..'])

    def odieCrab(self, bLE=True, bFR=True, bHE=False):
        pathDirWork = ''
        aER = []
        if bLE==True:
            aER.append('LE')
        if bFR==True:
            aER.append('FR')
        if bHE==True:
            aER.append('HE')
        for er in aER:
            pathDirWork = '{0}/{1}'.format(self.getPathDirOdieCrab(), er)
            if path.exists(pathDirWork)==False:
                os.makedirs(pathDirWork)
            os.chdir(pathDirWork)
            print os.getcwd()
            os.symlink('{0}/{1}/odie.rc'.format(self.getPathDirOdie(), er), "{0}/odie.rc".format(pathDirWork))
            SetEnvironForMARS("5.34.24")
            #shutil.copy('{0}/odie_{1}_{2}.rc'.format(self.getPathDirRc(), self.getConfigName(), er), './odie.rc')
            #aCmd = [ 'odie', '-b', '-q', '--config={0}/{1}/odie.rc'.format(self.getPathDirOdie(), er), '--ind={0}/20*_Q_*.root'.format(self.getPathDirMelibeaCrab()) ]
            aCmd = [ 'odie', '-b', '-q', '--config=./odie.rc', '--ind={0}/20*_Q_*.root'.format(self.getPathDirMelibeaCrab()) ]
            print aCmd
            subprocess.call(aCmd)
            SetEnvironForMARS("5.34.14")
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/SaveTh2OnAndOffCan.C("Output_odie.root", "{1}", "CrabSanityCheck_{2}_{3}")'.format(self.getPathPythonModuleMine(), self.getSourceName(), self.getTimeThisNight('short'), er)])
            if os.environ['OSTYPE'][:6]=='darwin':
                subprocess.call(['open', 'th2OnAndOffCan_{0}_CrabSanityCheck_{1}_{2}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), er)])
            else:
                subprocess.call(['eog', 'th2OnAndOffCan_{0}_CrabSanityCheck_{1}_{2}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), er)])
            #subprocess.call(['imgcat', 'th2OnAndOffCan_{0}_CrabSanityCheck_{1}_{2}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), er)])
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', '..'])

    def flute(self, eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc="", bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1):
        #subprocess.call( 'source ~/.tcshrc_MARS', shell=True ) # ROOT 5.34.24
        if not isinstance(bMelibeaNonStdMc, bool):
            bMelibeaNonStdMc=self.getSettingsDC().getBoolTunedTest()
        if bMelibeaNonStdMc==True:
            pathMelibeaMC = self.getPathDirMelibeaNonStdMC()
        else:
            pathMelibeaMC = self.getPathDirMelibeaMC()
        strRcData="""
flute.mcdata:  {0}/TEST/GA_za{1}*_Q_*.root
flute.data:    ../../melibea/20*_Q_*.root
""".format(pathMelibeaMC, self.getZenithCut())
        strRcZd="""flute.minZd: {0}
flute.maxZd: {1}
""".format(self.getZenithCutLow(), self.getZenithCutUp())
        strRcSize = ""
        if float(self.getDcCut())>=4000 or eth>=500:
            strRcSize = """flute.minSize: 100.
"""
        if redshift=="":
            redshift = GetRedshift(self.getSourceName())
        strRcRedshift = """flute.SourceRedshift: {0}
""".format(redshift)
        strRcAssumedSpectrum = ""
        if assumedSpectrum != "":
            strRcAssumedSpectrum = """flute.AssumedSpectrum: {0}
""".format(assumedSpectrum)
        pathDirWork = ''
        aBinning = []
        if bSingleBin==True:
            aBinning.append('single-bin')
        if bRunWise==True:
            aBinning.append('run-wise')
        if bNightWise==True:
            aBinning.append('night-wise')
        if bCustom==True:
            aBinning.append('custom')
        for wise in aBinning:
            pathDirWork = '{0}/{1}'.format(self.getPathDirFlute(), wise)
            #if path.exists(pathDirWork)==False:
             #   os.makedirs(pathDirWork)
            os.chdir(pathDirWork)
            print os.getcwd()
            strRcLc = """flute.EminLC: {0}
flute.LCbinning: {1}
""".format(eth, wise)
            if wise=="custom":
                aBinCustom = GetLC_bins("{0}/night-wise/Output_flute_{1}_{2}GeV_night-wise.root".format(self.getPathDirFlute(), self.getConfigName(), int(eth)))
                strRcLc = strRcLc + """
flute.LCbinlowedge: {0}""".format(aBinCustom[0][0])
                for itv in aBinCustom[0][1:]:
                    strRcLc = strRcLc + ", {0}".format(itv)
                strRcLc = strRcLc + """
flute.LCbinupedge: {0}""".format(aBinCustom[1][0])
                for jtv in aBinCustom[1][1:]:
                    strRcLc = strRcLc + ", {0}".format(jtv)
                strRcLc = strRcLc + """
"""
            # Modify RC file
            strRcAdd = strRcData + strRcZd + strRcSize + strRcRedshift + strRcAssumedSpectrum + strRcLc
            pathRcNew = './flute_{0}_{1}GeV_{2}.rc'.format(self.getConfigName(), int(eth), wise)
            rcNew = open(pathRcNew, 'w') 
            rcNew.write(strRcAdd)
            rcOrig = open('{0}/mrcfiles/flute.rc'.format(self.getPathMarssys()), 'r')
            rcCopied = rcOrig.read()
            rcNew.write(rcCopied)
            rcOrig.close()
            rcNew.close()
            subprocess.call(['head', pathRcNew])

            SetEnvironForMARS("5.34.24")
            aCmd = [ 'flute', '-q', '-b', '--config={0}'.format(pathRcNew) ]
            print aCmd
            subprocess.call(aCmd)
            SetEnvironForMARS("5.34.14")
            subprocess.call([ 'root', '-b', '-q', '{5}/MarsUtil/SaveFlutePlots.C("Status_flute_{2}_{3}GeV_{4}.root", "{0}", "{1}_{2}_{3}GeV_{4}", "png", {6})'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth), wise, self.getPathPythonModuleMine(), fluxMaxInCrab)])
            if os.environ['OSTYPE'][:6]=='darwin':
                subprocess.call(['open', 'SED_{0}_{1}_{2}_{3}GeV_{4}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth), wise)])    
                subprocess.call(['open', 'LightCurve_{0}_{1}_{2}_{3}GeV_{4}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth), wise)])
            elif os.environ['OSTYPE']=='linux':
                subprocess.call(['eog', 'SED_{0}_{1}_{2}_{3}GeV_{4}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth), wise)])    
                subprocess.call(['eog', 'LightCurve_{0}_{1}_{2}_{3}GeV_{4}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth), wise)])
            #subprocess.call(['imgcat', 'SED_{0}_{1}_{2}_{3}GeV_{4}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth), wise)])    
            #subprocess.call(['imgcat', 'LightCurve_{0}_{1}_{2}_{3}GeV_{4}.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth), wise)])
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/GetLC_values.C("Output_flute_{1}_{2}GeV_{3}.root")'.format(self.getPathPythonModuleMine(), self.getConfigName(), int(eth), wise)])
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', '..'])

    def fluteCrab(self, eth=300, bMelibeaNonStdMc=""):
        if not isinstance(bMelibeaNonStdMc, bool):
            bMelibeaNonStdMc=self.getSettingsDC().getBoolTunedTest()
        if bMelibeaNonStdMc==True:
            pathMelibeaMC = self.getPathDirMelibeaNonStdMC()
        else:
            pathMelibeaMC = self.getPathDirMelibeaMC()
        strRcData="""
flute.mcdata:  {0}/TEST/GA_za{1}*_Q_*.root
flute.data:    {2}/20*_Q_*.root
""".format(pathMelibeaMC,self.getZenithCut(), self.getPathDirMelibeaCrab())
        strRcRedshift = """
flute.SourceRedshift: 0"""
        strRcAssumedSpectrum = """
flute.AssumedSpectrum: pow(x/300.,-2.31-0.26*log10(x/300.))"""
        pathDirWork = ''
        aBinning = []
        aBinning.append('night-wise')
        aBinning.append('single-bin')
        for wise in aBinning:
            pathDirWork = '{0}/{1}'.format(self.getPathDirFluteCrab(), wise)
            if path.exists(pathDirWork)==False:
                os.makedirs(pathDirWork)
            os.chdir(pathDirWork)
            print os.getcwd()
            strRcLc = """
flute.EminLC: {0}
flute.LCbinning: {1}
""".format(eth, wise)
            # Modify RC file
            strRcAdd = strRcData + strRcRedshift + strRcAssumedSpectrum + strRcLc
            pathRcNew = '{0}/fluteCrab_{1}_{2}GeV.rc'.format(pathDirWork, self.getConfigName(), int(eth))
            rcNew = open(pathRcNew, 'w') 
            rcNew.write(strRcAdd)
            rcOrig = open('{0}/night-wise/flute_{1}_{2}GeV_night-wise.rc'.format(self.getPathDirFlute(), self.getConfigName(), int(eth)), 'r')
            rcCopied = rcOrig.read()
            rcNew.write(rcCopied)
            rcOrig.close()
            rcNew.close()
            subprocess.call(['head', pathRcNew])

            SetEnvironForMARS("5.34.24")
            aCmd = [ 'flute', '-q', '-b', '--config={0}'.format(pathRcNew) ]
            print aCmd
            subprocess.call(aCmd)
            SetEnvironForMARS("5.34.14")
            subprocess.call([ 'root', '-b', '-q', '{4}/MarsUtil/SaveFlutePlots.C("Status_fluteCrab_{2}_{3}GeV.root", "{0}", "CrabSanityCheck_{1}_{2}_{3}GeV")'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth), self.getPathPythonModuleMine())])
            if os.environ['OSTYPE'][:6]=='darwin':
                subprocess.call(['open', 'SED_{0}_CrabSanityCheck_{1}_{2}_{3}GeV.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth))]) 
                subprocess.call(['open', 'LightCurve_{0}_CrabSanityCheck_{1}_{2}_{3}GeV.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth))])
            elif os.environ['OSTYPE']=='linux':
                subprocess.call(['eog', 'SED_{0}_CrabSanityCheck_{1}_{2}_{3}GeV.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth))])  
                subprocess.call(['eog', 'LightCurve_{0}_CrabSanityCheck_{1}_{2}_{3}GeV.png'.format(self.getSourceName(), self.getTimeThisNight('short'), self.getConfigName(), int(eth))])
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/GetLC_values.C("Output_fluteCrab_{1}_{2}GeV.root")'.format(self.getPathPythonModuleMine(), self.getConfigName(), int(eth))])
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', '..'])

    def ssignal(self): #, bTighterCleaning=False):
        confDC= self.getSettingsDC()
        pathDirWork = ''
        aTel = ['M1', 'M2']
        for tel in aTel:
            pathDirWork = '{0}/{1}'.format(self.getPathDirSsignal(), tel)
            os.chdir(pathDirWork)
            aFile = glob.glob("{0}/{1}/ssignal*".format(self.getPathDirSsignal(), tel))
            strLiFile = ""
            strLiFile = aFile[0]
            for iFile in aFile[1:]:
                strLiFile = strLiFile + " " + iFile
            pathRcNew = '{0}/{1}/star_{1}_noise{2}.rc'.format(self.getPathDirStar(), tel, self.getTimeThisNight('short', True))
            pathRcNewMC = '{0}/{1}/star_{1}_noise{2}_MC.rc'.format(self.getPathDirStarMC(), tel, self.getTimeThisNight('short', True))
            SetEnvironForMARS("5.34.14")
            aCmd = [ 'root', '-b', '-q', '{0}/MarsUtil/GetIntPedEx.C("{1}", "{2}", "{3}")'.format(self.getPathPythonModuleMine(), strLiFile, pathRcNewMC, tel)]
            print aCmd
            subprocess.call(aCmd)
            if os.environ['OSTYPE'][:6]=='darwin':
                subprocess.call(['open', '{0}/IntPedEx_{1}.png'.format(pathDirWork, tel)])
            else:
                subprocess.call(['eog', '{0}/IntPedEx_{1}.png'.format(pathDirWork, tel)])

            #Modify Star RC file
            strAddNoise = """MJStar.UseAddNoise: yes
MJStar.MAddNoise.Method:2
"""
            strNoStarGuider = """MJStar.CalibStarguider: no
MJStar.UseStarguider: no
"""
            strClean = """MJStar.MImgCleanStd.CleanMethod: Absolute
MJStar.MImgCleanStd.CleanLevel1: {0}
MJStar.MImgCleanStd.CleanLevel2: {1}
""".format(confDC.getLVsCleaning[0], confDC.getLVsCleaning[1])
            rcNew = open(pathRcNew, 'a')
            rcNewMC = open(pathRcNewMC, 'a')
            rcNewMC.write(strAddNoise)
            rcNew.write(strNoStarGuider)
            rcNewMC.write(strNoStarGuider)
            #if bTighterCleaning==True:
            if confDC.getNaDC()>2000:
                rcNew.write(strClean)
                rcNewMC.write(strClean)
            rcOrig = open('{0}/mrcfiles/star_{1}_OSA.rc'.format(self.getPathMarssys(), tel), 'r')
            rcCopied = rcOrig.read()
            rcNew.write(rcCopied)
            rcNewMC.write(rcCopied)
            rcOrig.close()
            rcNew.close()
            rcNewMC.close()
            print "==", pathRcNew, "=="
            subprocess.call(['head', pathRcNew])
            print "==", pathRcNewMC, "=="
            subprocess.call(['head', pathRcNewMC])

    def starMC(self, bTrain="", bTest=""):
        # This method may not work well.
        #subprocess.call( 'source /Users/Mitsunari/.bash_profile_Root53420_private', shell=True ) # Use ROOT 5.34.23 in order to avoide Star's segmentation violation
        if not isinstance(bTrain, bool):
            bTrain=self.getSettingsDC().getBoolTunedTrain() 
        if not isinstance(bTest, bool):
            bTest=self.getSettingsDC().getBoolTunedTest()
        pathDirWork = ''
        aDSet = []
        if bTrain==True:
            aDSet.append('TRAIN')
        if bTest==True:
            aDSet.append('TEST')
        aTel = ['M1', 'M2']
        for dset in aDSet:
            for tel in aTel:
                pathDirWork = '{0}/{1}/{2}'.format(self.getPathDirStarMC(), tel, dset)
                os.chdir(pathDirWork)
                print os.getcwd()
                strCmd = 'star -mc -b -f --config={0}/{1}/star_{1}_noise{2}_MC.rc --ind="{3}/standard/MC/ST.03.06-Mmcs699/{4}/calibrated/{1}/GA_*_Y_*.root" --out=./ --log=LogStarMC_{4}_{1}.txt'.format(self.getPathDirStarMC(), tel, self.getTimeThisNight('short'), self.getPathBase(), dset)
                SubmitPJ(strCmd, pathDirWork, 'StarMC_{0}_{1}'.format(dset, tel))
                # aCmd = [ 'star', '-b', '-f', '-mc', '--config=../star_{0}_noise{1}.rc'.format(tel, self.getTimeThisNight('short')), '--ind={0}/standard/MC/ST.03.06-Mmcs699/{1}/calibrated/{2}/GA_*_Y_*.root'.format(self.getPathBase(), dset, tel), '--out=./', '--log=LogStarMC.txt' ]
                # print aCmd
                # subprocess.call(aCmd)

        #subprocess.call( 'source /Users/Mitsunari/.bash_profile', shell=True ) # Back to ROOT 5.34.20

    def star(self):
        pathDirWork = ''
        aTel = ['M1', 'M2']
        for tel in aTel:
            pathDirWork = '{0}/{1}'.format(self.getPathDirStar(), tel)
            os.chdir(pathDirWork)

            # Make a list of #RUN
            aFile = glob.glob('{0}/{1}/20*root'.format(self.getPathDirCalibrated(), tel))
            aRun = []
            for fileY in aFile:
                fileZ = os.path.basename(fileY)
                aRun.append(fileZ[12:20])
            aRunUiq = list(set(aRun))
            #print aRunUiq
            os.chdir(pathDirWork)
            print os.getcwd()
            for runUiq in aRunUiq:
                strCmd = 'star -b --config={0}/{1}/star_{1}_noise{2}.rc --ind="{3}/{1}/20*_{1}_{4}*_Y_*.root" --out=./ --outname={4} --log=LogStar{4}.txt'.format(self.getPathDirStar(), tel, self.getTimeThisNight('short'), self.getPathDirCalibrated(), runUiq)
                #print strCmd
                SubmitPJ(strCmd, pathDirWork, 'Star{0}{1}'.format(runUiq, tel))

    def starOFF(self):
        pathDirWork = ''
        aTel = ['M1', 'M2']
        for tel in aTel:
            pathDirWork = '{0}/{1}'.format(self.getPathDirStarOFF(), tel)
            # Make a list of #RUN
            aFile = os.listdir('{0}/{1}/za{2}'.format(self.getPathDirCalibratedOFF(), tel, self.getZenithCut()))
            aRun = []
            for fileY in aFile:
                aRun.append(fileY[12:20])
            aRunUiq = list(set(aRun))
            #print aRunUiq
            os.chdir(pathDirWork)
            print os.getcwd()
            for runUiq in aRunUiq:
                #aCmd = [ 'star', '-b', '-f', '--config={0}/{1}/star_{2}_noise{3}.rc'.format(self.getPathDirStarMC(), tel, tel, self.getTimeThisNight('short')), '--ind={0}/standard/OFF/calibrated/{1}/20*_{2}_{3}*_Y_*.root'.format(self.getPathBase(), tel, tel, runUiq), '--out=./', '--log=LogStarOFF{0}.txt'.format(runUiq) ]
                strCmd = 'star -b --config={0}/{1}/star_{1}_noise{2}_MC.rc --ind="{3}/{1}/za{5}/20*_{1}_{4}*_Y_*.root" --out=./ --log=LogStarOFF{4}.txt --outname=starOFF{4}'.format(self.getPathDirStarMC(), tel, self.getTimeThisNight('short'), self.getPathDirCalibratedOFF(), runUiq, self.getZenithCut())
                SubmitPJ(strCmd, pathDirWork, 'StarOFF{0}{1}'.format(runUiq, tel))

    def starCrab(self, aPathCalibratedCrab):
        pathDirWork = ''
        aTel = ['M1', 'M2']
        for pathCalibratedCrab in aPathCalibratedCrab:
            for tel in aTel:
                pathDirWork = '{0}/{1}'.format(self.getPathDirStarCrab(), tel)
                # Make a list of #RUN
                #aFile = os.listdir('{0}/{1}'.format(pathCalibratedCrab, tel))
                aFile = glob.glob('{0}/{1}/20*_Y_*.root'.format(pathCalibratedCrab, tel))
                aRun = []
                for fileY in aFile:
                    fileZ = os.path.basename(fileY)
                    aRun.append(fileZ[12:20])
                aRunUiq = list(set(aRun))
                os.chdir(pathDirWork)
                print os.getcwd()
                for runUiq in aRunUiq:
                    strCmd = 'star -b --config={0}/{1}/star_{1}_noise{2}_MC.rc --ind="{3}/{1}/20*_{1}_{4}*_Y_*.root" --out=./ --outname=starCrab{4} --log=LogStarCrab{4}.txt'.format(self.getPathDirStarMC(), tel, self.getTimeThisNight('short'), pathCalibratedCrab, runUiq)
                    SubmitPJ(strCmd, pathDirWork, 'StarCrab{0}{1}'.format(runUiq, tel))

    def superstar(self):
        #shutil.copy('{0}/mrcfiles/superstar.rc'.format(self.getPathMarssys()), self.getPathDirSuperstarOFF())
        pathDirWork = self.getPathDirSuperstar()
        os.chdir(pathDirWork)
        print os.getcwd()
        # Make a list of #RUN
        aFile = glob.glob('{0}/M2/20*root'.format(self.getPathDirStar()))
        aRun = []
        for fileY in aFile:
            fileZ = os.path.basename(fileY)
            aRun.append(fileZ[12:20])
        aRunUiq = list(set(aRun))
        print aRunUiq
        for runUiq in aRunUiq:
            strCmd = 'superstar -f -q -b --config={0}/superstar.rc --ind1="{1}/M1/20*_M1_{2}*_I_*root" --ind2="{1}/M2/20*_M2_{2}*_I_*.root" --out=./ --log=LogSuperStar_{2}.log --outname=superstar_{2}'.format(self.getPathDirSuperstarMC(), self.getPathDirStar(), runUiq)
            SubmitPJ(strCmd, pathDirWork, 'Superstar{0}'.format(runUiq))

    def superstarMC(self, bTrain="", bTest=""):
        if not isinstance(bTrain, bool):
            bTrain=self.getSettingsDC().getBoolTunedTrain() 
        if not isinstance(bTest, bool):
            bTest=self.getSettingsDC().getBoolTunedTest()
        shutil.copy('{0}/mrcfiles/superstar.rc'.format(self.getPathMarssys()), self.getPathDirSuperstarMC())
        aDSet = []
        if bTrain==True:
            aDSet.append('TRAIN')
        if bTest==True:
            aDSet.append('TEST')
        for dset in aDSet:
            pathDirWork = '{0}/{1}'.format(self.getPathDirSuperstarMC(), dset)
            os.chdir(pathDirWork)
            print os.getcwd()
            #aCmd = [ 'superstar', '-f', '-q', '-b', '-mc', '--config={0}/superstar.rc'.format(self.getPathDirSuperstarMC()), '--ind1={0}/M1/{1}/GA_M1*root'.format(self.getPathDirStarMC(), dset), '--ind2={0}/M2/{1}/GA_M2*root'.format(self.getPathDirStarMC(), dset), '--out=./', '--log=LogSuperStarMC.log' ]
            #print aCmd
            #subprocess.call(aCmd)
            strCmd = 'superstar -f -q -b -mc --config={0}/superstar.rc --ind1="{1}/M1/{2}/GA_M1*_I_*root" --ind2="{1}/M2/{2}/GA_M2*_I_*.root" --out=./ --log=LogSuperStarMC.log'.format(self.getPathDirSuperstarMC(), self.getPathDirStarMC(), dset)
            #print strCmd
            SubmitPJ(strCmd, pathDirWork, "SuperstarMC{0}".format(dset))

    def selectmc(self, bTrain="", bTest=""): #bTrain=False, bTest=True):
        if not isinstance(bTrain, bool):
            bTrain=self.getSettingsDC().getBoolTunedTrain() 
        if not isinstance(bTest, bool):
            bTest=self.getSettingsDC().getBoolTunedTest()
        SetEnvironForMARS()
        aDSet = []
        if bTrain==True:
            aDSet.append('TRAIN')
        if bTest==True:
            aDSet.append('TEST')
        for dset in aDSet:
            pathDirWork = '{0}/{1}'.format(self.getPathDirSuperstarMC(), dset)
            os.chdir(pathDirWork)
            print os.getcwd()
            bCmd = ['selectmc', '-f', '-q', '-b', '-joinmc', '--pathMC={0}/GA_*{1}*_S_*.root'.format(pathDirWork, self.getZenithCut()), '--out=./', '--outname=GA_za{0}_{1}_S_wr.root'.format(self.getZenithCut(), dset), '--log=LogSelectMc.txt' ]
            subprocess.call(bCmd)

    def superstarOFF(self):
        pathDirWork = self.getPathDirSuperstarOFF()
        os.chdir(pathDirWork)
        print os.getcwd()
        # Make a list of #RUN
        aFile = glob.glob('{0}/M2/20*root'.format(self.getPathDirStarOFF()))
        aRun = []
        for fileY in aFile:
            fileZ = os.path.basename(fileY)
            aRun.append(fileZ[12:20])
        aRunUiq = list(set(aRun))
        print aRunUiq
        for runUiq in aRunUiq:
            strCmd = 'superstar -f -q -b --config={0}/superstar.rc --ind1="{1}/M1/20*_M1_{2}*_I_*root" --ind2="{1}/M2/20*_M2_{2}*_I_*.root" --out=./ --log=LogSuperStarOFF_{2}.log --outname=superstar_OFF{2}'.format(self.getPathDirSuperstarMC(), self.getPathDirStarOFF(), runUiq)
            SubmitPJ(strCmd, pathDirWork, 'SuperstarOFF{0}'.format(runUiq))

    def superstarCrab(self):
        pathDirWork = self.getPathDirSuperstarCrab()
        os.chdir(pathDirWork)
        print os.getcwd()
        # Make a list of #RUN
        aFile = glob.glob('{0}/M2/20*root'.format(self.getPathDirStarCrab()))
        aRun = []
        for fileY in aFile:
            fileZ = os.path.basename(fileY)
            aRun.append(fileZ[12:20])
        aRunUiq = list(set(aRun))
        print aRunUiq
        for runUiq in aRunUiq:
            strCmd = 'superstar -f -q -b --config={0}/superstar.rc --ind1="{1}/M1/20*_M1_{2}*_I_*root" --ind2="{1}/M2/20*_M2_{2}*_I_*.root" --out=./ --log=LogSuperStarCrab_{2}.log --outname=superstar_Crab{2}'.format(self.getPathDirSuperstarMC(), self.getPathDirStarCrab(), runUiq)
            SubmitPJ(strCmd, pathDirWork, 'SuperstarCrab{0}'.format(runUiq))

    def downloadData(self, password, cDataType="S", verData=1, bPjsub=False):
        strDataType = ""
        pathDirTgt = ""
        dateDir = self.getTimeThisNight().value
        if cDataType=="S":
            strDataType = "SuperStar"
            pathDirTgt = self.getPathDirSuperstar()
            DownloadPicData("http://data.magic.pic.es/Data/{0}/v{1}/{2}/{3}".format(strDataType, verData, self.getSourceName(), dateDir.translate(string.maketrans('-', '_'))), pathDirTgt, password, cDataType, "", "", bPjsub)
        elif cDataType=="I":
            strDataType = "Star"
            aTel = [1, 2]
            for tel in aTel:
                pathDirTgt = "{0}/M{1}".format(self.getPathDirStar(), tel)
                DownloadPicData("http://data.magic.pic.es/Data/{0}/v{1}/{2}/{3}".format(strDataType, verData, self.getSourceName(), dateDir.translate(string.maketrans('-', '_'))), pathDirTgt, password, cDataType, tel, "", bPjsub)
        elif cDataType=="Y":
            strDataType = "Calibrated"
            aTel = [1, 2]
            for tel in aTel:
                pathDirTgt = "{0}/M{1}".format(self.getPathDirCalibrated(), tel)
                DownloadPicData("http://data.magic.pic.es/Data/{0}/v{1}/{2}/{3}".format(strDataType, verData, self.getSourceName(), dateDir.translate(string.maketrans('-', '_'))), pathDirTgt, password, cDataType, tel, "", bPjsub)
        elif cDataType=="ssignal":
            strDataType = "ssignal"
            aTel = [1, 2]
            for tel in aTel:
                pathDirTgt = "{0}/M{1}".format(self.getPathDirSsignal(), tel)
                DownloadPicData("http://data.magic.pic.es/Data/Calibrated/v{0}/{1}/{2}".format(verData, self.getSourceName(), dateDir.translate(string.maketrans('-', '_'))), pathDirTgt, password, cDataType, tel, "", bPjsub)
        else:
            print cDataType, "is not supported."
        #print dateDir.translate(string.maketrans('-', '_'))        

class SlowMARS(QuickMARS):
    """Class for slow analysis. You should know which data file is corresponding to each cut condition.
1) sma = SlowMARS(nameSrc, strTitle, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=2000., bReducedHV=False)
2) sma.makeDirs()
== No Moon ==
3) Put your superstar files to the created directories
5) sma.quate()
6) sma.melibea()
7) sma.odie(bLE=True, bFR=True, bHE=False)
8) sma.flute(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc=False, bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1)
== Moderate Moon ==
3) Put your superstar and ssignal files to the created directories
4) sma.quate()
5) sma.melibea()
6) sma.odie(bLE=True, bFR=True, bHE=False)
7) sma.ssignal()
8) sma.starMC(bTrain=False, bTest=True)
9) sma.superstarMC(bTrain=False, bTest=True)
10) sma.selectmc(False, True)
11) sma.melibeaMC(False, True)
12) sma.flute(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc=True, bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1)
== Decent Moon ==
3) Put your calibrated and ssignal files to the created directories
4) sma.ssignal()
5) sma.starMC(bTrain=True, bTest=True)
6) sma.star()
7) sma.starOFF()
8) sma.superstar()
9) sma.superstarMC(bTrain=True, bTest=True)
10) sma.superstarOFF()
11) sma.selectmc(True, True)
12) sma.coach()
13) sma.melibea(True)
14) sma.melibeaMC(False, True)
15) sma.odie(bLE=True, bFR=True, bHE=False)
16) sma.flute(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc=True, bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1)
"""
    def __init__(self, nameSrc, strTitle, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=2000., bReducedHV=False):
        QuickMARS.__init__(self, nameSrc, '1960-01-01', ZenithCut, TransCut9km, CloudCut, naCutDC)
        self.title = strTitle
        self.pathDirSpot = '{0}/{1}/{2}/{3}'.format(self.getPathBase(), self.getSourceName(), self.getTitle(), self.nameCfg)
        self.pathDirCondition = self.getPathDirSpot()
        self.setSubDirs()

def DownloadPicData(strPicDir, strDirTgt, password, cDataType="S", nTel="", nRun="", bPjsub=False):
    if path.exists(strDirTgt)==False:
        os.makedirs(strDirTgt)
    os.chdir(strDirTgt)
    theTime = datetime.now()
    nameHtml = '{0}{1}{2}{3}{4}{5}.html'.format(theTime.year, theTime.month,theTime.day,theTime.hour,theTime.minute,theTime.second)
    aCmd = [ 'wget', '-O{0}'.format(nameHtml), '--user=MAGIC', '--password={0}'.format(password), strPicDir ]
    print aCmd
    subprocess.call(aCmd)
    fileHtml = open(nameHtml)
    dataHtml = fileHtml.read()
    if cDataType=="ssignal":
        if nTel=="":
            strFind = 'ssignal.*?root'
        else:
            strFind = 'ssignal.*?_M{0}.root'.format(nTel)
    elif nTel=="" and nRun=="":
        strFind = '20\d\d\d\d\d\d.*?_{0}_.*?root'.format(cDataType)
    elif nTel=="":
        strFind = '20\d\d\d\d\d\d.*?_{1}.*?_{0}_.*?root'.format(cDataType, nRun)
    elif nRun=="":
        strFind = '20\d\d\d\d\d\d_M{1}_.*?_{0}_.*?root'.format(cDataType, nTel)
    else:
        strFind = '20\d\d\d\d\d\d_M{1}_{2}.*?_{0}_.*?root'.format(cDataType, nTel, nRun)
    print "Search for", strFind
    aRootFile = re.findall(strFind, dataHtml)
    aRootFile = list(set(aRootFile))
    print aRootFile
    aProc = []
    for rootFile in aRootFile:
        if bPjsub==False:
            bCmd = [ 'wget', '-O{0}'.format(rootFile), '-nc', '-nv', '--user=MAGIC', '--password={0}'.format(password), '{0}/{1}'.format(strPicDir, rootFile) ]
            print bCmd
            pRet = subprocess.Popen(bCmd)
            aProc.append(pRet)
        else:
            strCmd = 'wget -O{0} -nc -nv --user=MAGIC --password={1} {2}/{3}'.format(rootFile, password, strPicDir, rootFile)
            nameSub,extSub = os.path.splitext( os.path.basename(rootFile) )
            SubmitPJ(strCmd, strDirTgt, 'wget{0}'.format(nameSub))

def SubmitPJ(strCmd, pathDirWork, strSuffix=""):
    os.chdir(pathDirWork)
    print strCmd
    nameFilePJ = "pj{0}.csh".format(strSuffix)
    filePJ = open(nameFilePJ,"w")
    strPJ = """#!/bin/tcsh
#------ pjsub option --------#
#PJM -L "rscunit=common"
#PJM -L "rscgrp=B"
#PJM -L "vnode=1"
#------- Program execution -------#
setenv ROOTSYS /home/takhsm/app/root_v5.34.24
setenv MARSSYS /home/takhsm/app/Mars/Mars_V2-15-8_oldROOT
setenv PATH /home/takhsm/app/Mars/Mars_V2-15-8_oldROOT:/home/takhsm/app/oldROOT/bin:/home/takhsm/app/anaconda2/bin:/home/takhsm/CTA_MC/Chimp/Chimp:/usr/include/mysql:/home/takhsm/app/cmake/3.3.0:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/home/takhsm/CTA_MC/corsika_simtelarray_Prod3/hessioxxx/bin:/home/takhsm/CTA_MC/corsika_simtelarray_Prod3/std:/usr/local/bin:/bin:/usr/bin
setenv LD_LIBRARY_PATH /home/takhsm/app/root_v5.34.24/lib:/home/takhsm/app/Mars/Mars_V2-15-8_oldROOT:/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/home/takhsm/app/lib
cd {0}
{1}
""".format(pathDirWork, strCmd)
    filePJ.write(strPJ)
    filePJ.close()
    os.chmod(nameFilePJ, 0744)
    aCmd = ['pjsub', './{0}'.format(nameFilePJ)]
    print aCmd
    subprocess.call(aCmd)

def SetEnvironForMARS(verRoot = "5.34.24"):
    if verRoot == "5.34.24":
        os.environ["ROOTSYS"] = "/home/takhsm/app/root_v5.34.24"
        os.environ["MARSSYS"] = "/home/takhsm/app/Mars/Mars_V2-15-8_oldROOT"
        os.environ["PATH"] = "/home/takhsm/app/Mars/Mars_V2-15-8_oldROOT:/home/takhsm/app/oldROOT/bin:/home/takhsm/app/anaconda2/bin:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/usr/local/bin:/bin:/usr/bin"
#        os.environ["LD_LIBRARY_PATH"] = "/home/takhsm/app/root_v5.34.24/lib:/home/takhsm/app/Mars/Mars_V2-15-8_oldROOT:/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/home/takhsm/app/lib:/home/takhsm/lib/lib"
        os.environ["LD_LIBRARY_PATH"] = "/home/takhsm/lib/libPNG/lib:/home/takhsm/lib/lib:/home/takhsm/lib/libJPEG/lib:/home/takhsm/CTA_MC/Chimp/Chimp:/home/takhsm/CTA_MC/Chimp/Chimp/hessioxxx/lib:/home/takhsm/charaPMT:/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/home/takhsm/app/root_v5.34.24/lib:/home/takhsm/app/root_v5.34.24/lib/root:/home/takhsm/app/lib:/home/takhsm/app/root_v5.34.24:/home/takhsm/app/Mars/Mars_V2-15-8_oldROOT:/usr/lib64"
    if verRoot == "5.34.14":
        os.environ["ROOTSYS"] = "/usr/local/gcc473/root_v5.34.14"
        os.environ["MARSSYS"] = "/home/takhsm/app/Mars/Mars_V2-15-8"
        os.environ["PATH"] = "/usr/local/gcc473/root_v5.34.14/bin:/usr/local/gcc473/bin:/home/takhsm/app/Mars/Mars_V2-15-8:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/usr/lib64/qt-3.3/bin:/usr/local/bin:/bin:/usr/bin"
        os.environ["LD_LIBRARY_PATH"] = "/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/usr/local/gcc473/root_v5.34.14/lib:/usr/local/gcc473/root_v5.34.14/lib/root:/home/takhsm/app/lib:/usr/local/gcc473/root_v5.34.14:/home/takhsm/app/Mars/Mars_V2-15-8:/home/takhsm/lib/lib"
        
def GetRedshift(nameSource):
    if nameSource=='1ES1959+650':
        return 0.048
    else:
        return 0

def AddToRcFile(strAdd, pathFileOriginal, pathFileTarget):
    rcNew = open(pathFileTarget, 'a')
    rcNew.write(strAdd)
    rcOrig = open(pathFileOriginal, 'r')
    rcCopied = rcOrig.read()
    rcNew.write(rcCopied)
    rcOrig.close()
    rcNew.close()
    print "==", pathFileTarget, "=="
    subprocess.call(['head', pathFileTarget])

def catchImage(pathImage):
#    subprocess.call(['/home/takhsm/.iterm2/imgcat', pathImage], shell=True)
    if os.environ['OSTYPE'][:6]=='darwin':
        subprocess.call(['open', pathImage])
    else:
        subprocess.call(['eog', pathImage])
    
