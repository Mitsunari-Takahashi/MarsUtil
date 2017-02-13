#!/bin/env python
"""General utility file of classes and methods for MAGIC data analysis. 
Start with : python -i pMyMarsUtil.py
Make an object of QuickMARS or SlowMARS
QuickMARS: For daily anlaysis, flare advcoate.
SlowMARS: For analysis in detail. You should know your data's DC level.
"""
from astropy.time import Time
import time
import ROOT
from ROOT import std, TParameter
import os
import os.path as path
import shutil
import subprocess
from datetime import datetime
import re
import string
from math import log10
import glob
from pGetLC_bins import GetLC_bins
from pSubmitPJ import *
from Fermi.pLsList import ls_list
from pCommon import *
from pShellCom import *


class SettingsDC:
    """Class for settings of quate, image cleaning and tuning of MC, depending on DC.
SettingsDC(naDC=<DC in nA>, bReducedHV=False)"""
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
        if bReducedHV==True or naDC>2000:
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
    def getLowerLVsCleaning(self):
        return self.aCleaning[1]
    def getHigherLVsCleaning(self):
        return self.aCleaning[0]
    def getBoolTunedTrain(self):
        return self.bTunedTrain
    def getBoolTunedTest(self):
        return self.bTunedTest

class QuickMARS:
    """Class for slow analysis. You should know which data file is corresponding to each cut condition.
QuickMARS(nameSrc, strNight, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=3000., bReducedHV=False, bTimesOption=True, strTypeMC='', strPeriodMC=''):
  Ex) qma = QuickMARS('1ES1959+650', '2016-04-29', ZenithCut='35to50', TransCut9km='No', CloudCut='45', naCutDC='4500', bReducedHV=False, bTimesOption=True)
1) qma = QuickMARS(nameSrc, strTitle, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=2000., bReducedHV=False, bTimesOption=True)
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
    def __init__(self, nameSrc, strNight, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=3000., bReducedHV=False, bTimesOption=True, strTypeMC='', strPeriodMC='', bForce=True):
        SetEnvironForMARS(verRoot = "5.34.24")
        self.PATH_MARSSYS = os.environ['MARSSYS']
        self.PATH_PYTHON_MODULE_MINE = os.environ['PATH_PYTHON_MODULE_MINE']
        #self.PATH_BASE = "/Volumes/SHUNZEI/MAGIC" #"/Volumes/KARYU/MAGIC"
        self.PATH_BASE = os.environ['PATH_MARS_BASE']
        #self.PATH_DIR_RC = "/Users/Mitsunari/MAGIC/RC"
        self.PATH_DIR_RC = os.environ['PATH_MARS_RC_MINE']
        self.nameSrc = nameSrc
        self.timeThisNight = Time(strNight, format='iso', in_subfmt='date', out_subfmt='date', scale='utc')
        if strPeriodMC=='':
            self.strVersionMC = '{0}{1}'.format(getPeriodMC(self.timeThisNight), strTypeMC)
        else:
            self.strVersionMC = '{0}{1}'.format(strPeriodMC, strTypeMC)
#        self.versionMC = ''
        self.titleAnalysis = self.timeThisNight
        self.isoThisNight = self.timeThisNight.value
        self.bTimesOption = bTimesOption
        self.bForce = bForce
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
        self.PATH_DIR_MC = '{0}/standard/{1}'.format(self.getPathBase(), self.getVersionMC())
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
        self.pathDirQuate = '{0}/quate'.format(self.getPathDirCondition())
#        self.pathDirQuateOFF = '{0}/{1}/{2}/{3}/quateOFF'.format(self.getPathDirSpot(), self.getConfigName())
        self.pathDirQuateCrab = '{0}/quateCrab'.format(self.getPathDirCondition())
        self.pathDirSuperstarMC = '{0}/superstarMC'.format(self.getPathDirSpot())
        self.pathDirMelibeaMC = '{0}/melibeaMC/za{1}'.format(self.getPathDirMC(), self.getZenithCut())
        self.pathDirMelibeaNonStdMC = '{0}/melibeaMC'.format(self.getPathDirSpot())
        self.pathDirSuperstar = '{0}/superstar'.format(self.getPathDirSpot())
        if self.getTimesOption()==True:
            self.pathDirSuperstarUsed = '{0}/superstar'.format(self.getPathDirSpot())
        else:
            self.pathDirSuperstarUsed = '{0}/good'.format(self.getPathDirQuate())
        self.pathDirMelibea = '{0}/melibea'.format(self.getPathDirCondition())
        self.pathDirMelibeaCrab = '{0}/melibeaCrab'.format(self.getPathDirCondition())
        self.pathDirOdie = '{0}/odie'.format(self.getPathDirCondition())
        self.pathDirOdieCrab = '{0}/odieCrab'.format(self.getPathDirCondition())
        self.pathDirCaspar = '{0}/caspar'.format(self.getPathDirCondition())
        self.pathDirFlute = '{0}/flute'.format(self.getPathDirCondition())
        self.pathDirFluteCrab = '{0}/fluteCrab'.format(self.getPathDirCondition())
        self.pathDirCoach = '{0}/coach/za{1}'.format(self.getPathDirMC(), self.getZenithCut())
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

    def setTitleAnalysis(self, strTitle):
        self.titleAnalysis = strTitle
    def getTitleAnalysis(self):
        return self.titleAnalysis
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
    def getTimesOption(self):
        return self.bTimesOption
    def getVersionMC(self):
        return self.strVersionMC
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
    def getPathDirMC(self):
        return self.PATH_DIR_MC
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
            #strShort = '{0}{1}{2}'.format(strTemp[:4], strTemp[5:7], strTemp[8:])
            strShort = MakeShortDateExpression(strTemp)
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
    def getPathDirSuperstarUsed(self):
        return self.pathDirSuperstarUsed
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
        if self.getTimesOption()==True:
            aCmd = [ 'quate', '-b', '--stereo', '-f', '--config={0}'.format(pathRcNew), '--ind={0}'.format(self.getPathDirSuperstar()), '--out=.', '--times' ]
        else:
            aCmd = [ 'quate', '-b', '--stereo', '-f', '--config={0}'.format(pathRcNew), '--ind={0}'.format(self.getPathDirSuperstar()), '--out=.' ]
        print aCmd
        subprocess.call(aCmd)
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', 'Overview.pdf'])
            subprocess.call(['open', '.'])
        elif os.environ['OSTYPE']=='linux':
            subprocess.call(['evince', 'Overview.pdf'])
        if self.getTimesOption()==True:        
            print "M1 excluded:"
            subprocess.call(['cat', '{0}/excluded_1.times'.format(self.getPathDirQuate())])
            print "M2 excluded:"
            subprocess.call(['cat', '{0}/excluded_2.times'.format(self.getPathDirQuate())])
        else:
            print "good:"
            subprocess.call(['ls', '{0}/good'.format(self.getPathDirQuate())])
            print "bad:"
            subprocess.call(['ls', '{0}/bad'.format(self.getPathDirQuate())])
            print "out-of-zd:"
            subprocess.call(['ls', '{0}/out-of-zd'.format(self.getPathDirQuate())])

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
        SetEnvironForMARS("5.34.24")
       # Modify RC file
        strRcAdd = """RF.mcdata: {0}/TRAIN/GA_za*_TRAIN_S_wr.root
RF.data:  {1}/good/20*_S_*.root
RF.outpath: {2}
RF.outname: coach_{3}
RF.zdmin: {4}
RF.zdmax: {5}
""".format(self.getPathDirSuperstarMC(), self.getPathDirSuperstarOFF(), self.getPathDirCoachNonStd(), self.getConfigName(), self.getZenithCutLow(), self.getZenithCutUp())
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
        if self.getTimesOption()==True:
            aCmd = [ 'melibea', '-b', '-q', '--config={0}'.format(pathRcNew), '--ind={0}/20*_S_*.root'.format(self.getPathDirSuperstarUsed()), '--out=./', '--stereo', '--rf', '--rftree={0}/RF.root'.format(pathCoachNonStd), '--calc-disp-rf', '--rfdisptree={0}/disp1/DispRF.root'.format(pathCoachNonStd), '--calc-disp2-rf', '--rfdisp2tree={0}/disp2/DispRF.root'.format(pathCoachNonStd), '--calcstereodisp', '--disp-rf-sstrained', '-erec', '--etab={0}/Energy_Table.root'.format(pathCoachNonStd), '--timeslices={0}/excluded.times'.format(self.getPathDirQuate()) ]
        else:
            aCmd = [ 'melibea', '-b', '-q', '--config={0}'.format(pathRcNew), '--ind={0}/20*_S_*.root'.format(self.getPathDirSuperstarUsed()), '--out=./', '--stereo', '--rf', '--rftree={0}/RF.root'.format(pathCoachNonStd), '--calc-disp-rf', '--rfdisptree={0}/disp1/DispRF.root'.format(pathCoachNonStd), '--calc-disp2-rf', '--rfdisp2tree={0}/disp2/DispRF.root'.format(pathCoachNonStd), '--calcstereodisp', '--disp-rf-sstrained', '-erec', '--etab={0}/Energy_Table.root'.format(pathCoachNonStd) ]
        if self.bForce==True:
            aCmd.append('-f')
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
            aCmd = [ 'melibea', '-b', '-q', '-f', '--config={0}/melibea_stereo.rc'.format(self.getPathDirMelibea()), '--ind={0}/{1}/GA_za*{1}_S_wr.root'.format(self.getPathDirSuperstarMC(), dset), '--out=./', '--stereo', '--rf', '--rftree={0}/RF.root'.format(pathCoachNonStd), '--calc-disp-rf', '--rfdisptree={0}/disp1/DispRF.root'.format(pathCoachNonStd), '--calc-disp2-rf', '--rfdisp2tree={0}/disp2/DispRF.root'.format(pathCoachNonStd), '--calcstereodisp', '--disp-rf-sstrained', '-erec', '--etab={0}/Energy_Table.root'.format(pathCoachNonStd), '-mc' ]
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
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/SaveTh2OnAndOffCan.C("Output_odie_{1}_{2}.root", "{3}", "{4}_{2}")'.format(self.getPathPythonModuleMine(), self.getConfigName(), er, self.getSourceName(), self.getTitleAnalysis())])
            pathImage = '{0}/th2OnAndOffCan_{1}_{2}_{3}.png'.format(pathDirWork, self.getSourceName(), self.getTitleAnalysis(), er)
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
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/SaveTh2OnAndOffCan.C("Output_odie.root", "{1}", "CrabSanityCheck_{2}_{3}")'.format(self.getPathPythonModuleMine(), self.getSourceName(), self.getTitleAnalysis(), er)])
            if os.environ['OSTYPE'][:6]=='darwin':
                subprocess.call(['open', 'th2OnAndOffCan_{0}_CrabSanityCheck_{1}_{2}.png'.format(self.getSourceName(), self.getTitleAnalysis(), er)])
            else:
                subprocess.call(['eog', 'th2OnAndOffCan_{0}_CrabSanityCheck_{1}_{2}.png'.format(self.getSourceName(), self.getTitleAnalysis(), er)])
        if os.environ['OSTYPE'][:6]=='darwin':
            subprocess.call(['open', '..'])

    def flute(self, eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc="", bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1, nightDesignate='', runDesignate='', bDisplay=True, nameSubDirWork='', emin=10., emax=100000, nebin=0, nbinAz=1, pathCustomBinRefer="", bForce=False):
        SetEnvironForMARS("5.34.24")
        if not isinstance(bMelibeaNonStdMc, bool):
            bMelibeaNonStdMc=self.getSettingsDC().getBoolTunedTest()
        if bMelibeaNonStdMc==True:
            pathMelibeaMC = self.getPathDirMelibeaNonStdMC()
        else:
            pathMelibeaMC = self.getPathDirMelibeaMC()
        if nightDesignate=='':
            if runDesignate=='':
                strInDesignate = '20'
                strOutDesignate = ''
            else:
                strInDesignate = '20*_{0}'.format(runDesignate)
                strOutDesignate = 'run{0}_'.format(runDesignate)
        else:
            if runDesignate=='':
                strInDesignate = nightDesignate
                strOutDesignate = '{0}_'.format(nightDesignate)
            else:
                strInDesignate = '{0}_{1}'.format(nightDesignate, runDesignate)
                strOutDesignate = '{0}run{1}_'.format(nightDesignate, runDesignate)

        strRcData="""
flute.mcdata:  {0}/TEST/GA_*_Q_*.root
flute.data:    {1}/{2}*_Q_*.root
""".format(pathMelibeaMC, self.getPathDirMelibea(), strInDesignate)
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
        
        if nebin==0:
            nebin = int((log10(emax) - log10(emin)) * 6)
        strRcEnergyRange = """flute.nBinsEnergyEst: {0}
flute.minEnergyEst: {1}
flute.maxEnergyEst: {2}
""".format(nebin, emin, emax)

        strRcNbinAz = """flute.nBinsAz: {0}
""".format(nbinAz)

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
            SetEnvironForMARS("5.34.24")
            if nameSubDirWork=='':
                pathDirWork = '{0}/{1}'.format(self.getPathDirFlute(), wise)
            else:
                pathDirWork = '{0}'.format(nameSubDirWork)
                if path.exists(pathDirWork)==False:
                    os.makedirs(pathDirWork)
            os.chdir(pathDirWork)
            print os.getcwd()
            strRcLc = """flute.EminLC: {0}
flute.LCbinning: {1}
""".format(eth, wise)
            #strSuffixAzBin = ''
            #if nbinAz != 1:
            strSuffixAzBin = '_{0}AzBins'.format(nbinAz)
            strOutput = '{0}_{1}{2}GeV{3}_{4}'.format(self.getConfigName(), strOutDesignate, int(eth), strSuffixAzBin, wise)
            pathLogfile = '{0}/Log_flute_{1}.log'.format(pathDirWork, strOutput)
            if bForce==False:
                if path.exists(pathLogfile)==True:
                    with open(pathLogfile, 'r') as logfile:
                        loglines = logfile.readlines()
                        if loglines[len(loglines)-1] == 'Flute finished!\n':
                            print 'Flute had already done. Skipping it.'
                            continue
                        else:
                            print 'Flute had not finished. Processing it.'
            if wise=="custom":
                if pathCustomBinRefer=="":
                    pathCustomBinRefer = "{0}/night-wise/Output_flute_{1}_{2}GeV_night-wise.root".format(self.getPathDirFlute(), self.getConfigName(), int(eth))
                if path.exists(pathCustomBinRefer)==False:
                    print "{0} does not exist!!!".format(pathCustomBinRefer)
                aBinCustom = GetLC_bins(pathCustomBinRefer) #Output_flute file

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
            strRcAdd = strRcData + strRcZd + strRcEnergyRange + strRcNbinAz + strRcSize + strRcRedshift + strRcAssumedSpectrum + strRcLc
#            pathRcNew = './flute_{0}_{1}{2}GeV_{3}.rc'.format(self.getConfigName(), strOutDesignate, int(eth), wise)
            pathRcNew = './flute_{0}.rc'.format(strOutput)
            rcNew = open(pathRcNew, 'w') 
            rcNew.write(strRcAdd)
            rcOrig = open('{0}/mrcfiles/flute.rc'.format(self.getPathMarssys()), 'r')
            rcCopied = rcOrig.read()
            rcNew.write(rcCopied)
            rcOrig.close()
            rcNew.close()
            subprocess.call(['head', pathRcNew])

            aCmd = [ 'flute', '-q', '-b', '--config={0}'.format(pathRcNew) ]
            print aCmd
            subprocess.call(aCmd)
            SetEnvironForMARS("5.34.14")
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/SaveFlutePlots.C("Status_flute_{3}.root", "{1}", "{2}_{3}", "png", {4})'.format(self.getPathPythonModuleMine(), self.getSourceName(), self.getTitleAnalysis(), strOutput, fluxMaxInCrab)])
            if bDisplay==True:
                if os.environ['OSTYPE'][:6]=='darwin':
                    subprocess.call(['open', 'SED_{0}_{1}_{2}.png'.format(self.getSourceName(), self.getTitleAnalysis(), strOutput)])
                    subprocess.call(['open', 'LightCurve_{0}_{1}_{2}.png'.format(self.getSourceName(), self.getTitleAnalysis(), strOutput)])
                    subprocess.call(['open', '..'])
                elif os.environ['OSTYPE']=='linux':
                    subprocess.call(['eog', 'SED_{0}_{1}_{2}.png'.format(self.getSourceName(), self.getTitleAnalysis(), strOutput)])    
                    subprocess.call(['eog', 'LightCurve_{0}_{1}_{2}.png'.format(self.getSourceName(), self.getTitleAnalysis(), strOutput)])
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/GetLC_values.C("Output_flute_{1}.root")'.format(self.getPathPythonModuleMine(), strOutput)])

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
            subprocess.call([ 'root', '-b', '-q', '{4}/MarsUtil/SaveFlutePlots.C("Status_fluteCrab_{2}_{3}GeV.root", "{0}", "CrabSanityCheck_{1}_{2}_{3}GeV")'.format(self.getSourceName(), self.getTitleAnalysis(), self.getConfigName(), int(eth), self.getPathPythonModuleMine())])
            if os.environ['OSTYPE'][:6]=='darwin':
                subprocess.call(['open', 'SED_{0}_CrabSanityCheck_{1}_{2}_{3}GeV.png'.format(self.getSourceName(), self.getTitleAnalysis(), self.getConfigName(), int(eth))]) 
                subprocess.call(['open', 'LightCurve_{0}_CrabSanityCheck_{1}_{2}_{3}GeV.png'.format(self.getSourceName(), self.getTitleAnalysis(), self.getConfigName(), int(eth))])
            elif os.environ['OSTYPE']=='linux':
                subprocess.call(['eog', 'SED_{0}_CrabSanityCheck_{1}_{2}_{3}GeV.png'.format(self.getSourceName(), self.getTitleAnalysis(), self.getConfigName(), int(eth))])  
                subprocess.call(['eog', 'LightCurve_{0}_CrabSanityCheck_{1}_{2}_{3}GeV.png'.format(self.getSourceName(), self.getTitleAnalysis(), self.getConfigName(), int(eth))])
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
            pathListSsignal = '{0}/List_ssignal_files_temporal-{1}.root'.format(pathDirWork, tel)
            fileListSsignal = ROOT.TFile(pathListSsignal, 'RECREATE')
            fileListSsignal.cd()
            trListSsignal = ROOT.TTree('ListSsignal', 'List of ssignal files for {0}, DC<{1}'.format(self.getTitleAnalysis(), confDC.getNaDC()))
            strPathListSsignal = ROOT.TString(256)
            trListSsignal.Branch('PathListSsignal', strPathListSsignal)
            trListSsignal.Write()
            #fileListSsignal = open(pathListSsignal, 'w') 
            for iFileSsignal in range(len(aFile)):
                strPathListSsignal.Clear()
                strPathListSsignal.Append(aFile[iFileSsignal])
                print strPathListSsignal.Data()
                trListSsignal.Fill()
            trListSsignal.Write()
            fileListSsignal.Close()
            pathRcNew = '{0}/{1}/star_{1}_noise{2}.rc'.format(self.getPathDirStar(), tel, self.getTitleAnalysis())
            pathRcNewMC = '{0}/{1}/star_{1}_noise{2}_MC.rc'.format(self.getPathDirStarMC(), tel, self.getTitleAnalysis())
            SetEnvironForMARS("5.34.14")
            aCmd = [ 'root', '-b', '-q', '{0}/MarsUtil/GetIntPedEx.C("{1}", "{2}", "{3}")'.format(self.getPathPythonModuleMine(), pathListSsignal, pathRcNewMC, tel)]
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
""".format(confDC.getHigherLVsCleaning(), confDC.getLowerLVsCleaning())
            rcNew = open(pathRcNew, 'a')
            rcNewMC = open(pathRcNewMC, 'a')
            rcNewMC.write(strAddNoise)
            rcNew.write(strNoStarGuider)
            rcNewMC.write(strNoStarGuider)
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
                strCmd = 'star -mc -b -f --config={0}/{1}/star_{1}_noise{2}_MC.rc --ind="{3}/MC/{4}/calibrated/za{5}/{1}/GA_*_Y_*.root" --out=./ --log=LogStarMC_{4}_{1}.log'.format(self.getPathDirStarMC(), tel, self.getTitleAnalysis(), self.getPathDirMC(), dset, self.getZenithCut())
                SubmitPJ(strCmd, pathDirWork, 'StarMC_{0}_{1}'.format(dset, tel), strRscGrp="B", verROOT="5.34.24", jobname='SrM{0}{1}'.format(dset[:2], tel))
                # aCmd = [ 'star', '-b', '-f', '-mc', '--config=../star_{0}_noise{1}.rc'.format(tel, self.getTimeThisNight('short')), '--ind={0}/standard/MC/ST.03.06-Mmcs699/{1}/calibrated/{2}/GA_*_Y_*.root'.format(self.getPathBase(), dset, tel), '--out=./', '--log=LogStarMC.txt' ]
                # print aCmd
                # subprocess.call(aCmd)
        #subprocess.call( 'source /Users/Mitsunari/.bash_profile', shell=True ) # Back to ROOT 5.34.20

    def tailStarMC(self, tel='M2', dataset='TEST', nLine=20):
        """Read the tail of star MC log file for trailing the progress.
sma.tailStarMC('M1 or M2', 'TRAIN or TEST', #Line to be showed)       
"""
        pathLogFile = '{0}/{1}/{2}/LogStarMC_{2}_{1}.log'.format(self.getPathDirStarMC(), tel, dataset)
        tailFile(pathLogFile, nLine)


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
            print aRunUiq
            os.chdir(pathDirWork)
            print os.getcwd()
            for runUiq in aRunUiq:
                strCmd = 'star -b -f --config={0}/{1}/star_{1}_noise{2}.rc --ind="{3}/{1}/20*_{1}_{4}*_Y_*.root" --out=./ --outname={4} --log=LogStar{4}.txt'.format(self.getPathDirStar(), tel, self.getTitleAnalysis(), self.getPathDirCalibrated(), runUiq)
                SubmitPJ(strCmd, pathDirWork, 'Star{0}{1}'.format(runUiq, tel), strRscGrp="A", verROOT="5.34.24", jobname='Sr{0}{1}'.format(runUiq[-6:], tel))

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
                strCmd = 'star -f -b --config={0}/{1}/star_{1}_noise{2}_MC.rc --ind="{3}/{1}/za{5}/20*_{1}_{4}*_Y_*.root" --out=./ --log=LogStarOFF{4}.txt --outname=OFF{4}'.format(self.getPathDirStarMC(), tel, self.getTitleAnalysis(), self.getPathDirCalibratedOFF(), runUiq, self.getZenithCut())
                SubmitPJ(strCmd, pathDirWork, 'StarOFF{0}{1}'.format(runUiq, tel), strRscGrp="A", verROOT="5.34.24", jobname='SrF{0}{1}'.format(runUiq[-5:], tel))

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
                    strCmd = 'star -b -f --config={0}/{1}/star_{1}_noise{2}_MC.rc --ind="{3}/{1}/20*_{1}_{4}*_Y_*.root" --out=./ --outname=starCrab{4} --log=LogStarCrab{4}.txt'.format(self.getPathDirStarMC(), tel, self.getTitleAnalysis(), pathCalibratedCrab, runUiq)
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
            SubmitPJ(strCmd, pathDirWork, 'Superstar{0}'.format(runUiq), strRscGrp="A", verROOT="5.34.24", jobname='SSr{0}'.format(runUiq[-7:]))

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
            strCmd = 'superstar -f -q -b -mc --config={0}/superstar.rc --ind1="{1}/M1/{2}/GA_M1*_I_*root" --ind2="{1}/M2/{2}/GA_M2*_I_*.root" --out=./ --log=LogSuperStarMC_{2}.log'.format(self.getPathDirSuperstarMC(), self.getPathDirStarMC(), dset)
            #print strCmd
            SubmitPJ(strCmd, pathDirWork, "SuperstarMC{0}".format(dset), strRscGrp="B", verROOT="5.34.24", jobname='SSrMC{0}'.format(dset))


    def tailSuperstarMC(self, dataset='TEST', nLine=20):
        """Read the tail of superstar MC log file for trailing the progress.
sma.tailSuperstarMC('TRAIN or TEST', #Line to be showed)       
"""
        pathLogFile = '{0}/{1}/LogSuperStarMC_{1}.log'.format(self.getPathDirSuperstarMC(), dataset)
        tailFile(pathLogFile, nLine)


    def selectmc(self, bTrain="", bTest=""): #bTrain=False, bTest=True):
        li_zenith = ['za05to35', 'za35to50', 'za50to62', 'za62to70']
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
            for zset in li_zenith:
                if len(ls_list('{0}/GA_{1}_*_S_*.root'.format(pathDirWork, zset)))>1:
                    print zset
                    bCmd = ['selectmc', '-f', '-q', '-b', '-joinmc', '--pathMC={0}/GA_{1}_*_S_*.root'.format(pathDirWork, zset), '--out=./', '--outname=GA_{0}_{1}_S_wr.root'.format(zset, dset), '--log=LogSelectMc_{0}.txt'.format(zset) ]
                    print bCmd
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
            SubmitPJ(strCmd, pathDirWork, 'SSrF{0}'.format(runUiq[1:]), strRscGrp="A", verROOT="5.34.24")

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
            SubmitPJ(strCmd, pathDirWork, 'SuperstarCrab{0}'.format(runUiq), strRscGrp="A", verROOT="5.34.24")

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


def Foam(name_source, li_path_input, path_dir_work='.', strSuffix=''):
    """For running foam.
"""
    SetEnvironForMARS()
    if strSuffix!='':
        strSuffix = '_' + strSuffix
    ninput = len(li_path_input)
    print ninput, 'input files.'
    aCmd = [ 'foam', '-b', '-q', '--outputfile={0}/Foam_{1}{2}.root'.format(path_dir_work, name_source, strSuffix)]
    for path_input in li_path_input:
        aCmd.append(path_input)
    print aCmd
    subprocess.call(aCmd)    


def Fold(name_source, path_file_input, path_dir_work='.', strSuffix='', li_func=['PWL', 'LP', 'EPWL', 'ELP'], eFitMin=100, eFitMax=100000, eNorm=300):
    """For running fold. 
Available fitting function: PWL, LP, EPWL, ELP, SEPWL
The input is one output file of flute or foam.
"""
    os.chdir(path_dir_work)
    if strSuffix!='':
        strSuffix = '_' + strSuffix
    dict_func_par = {}
    dict_chiSq_red = {}
    chiSq_ed_min = float(sys.maxsize)
    func_chiSq_ed_min = ''
    for func in li_func:
        print '----------'
        print func
        dict_func_par[func] = [] # Add an empty list to the mother dictionary
        SetEnvironForMARS("5.34.24")
        str_title_output = '{0}_{1}_{2}-{3}GeV'.format(strSuffix, func, eFitMin, eFitMax)
        aCmd = ['fold', '-b', '--inputfile={0}'.format(path_file_input), '--function={0}'.format(func), '--log=Log_Fold_{0}{1}.log'.format(name_source, str_title_output), '--redshift={0}'.format(GetRedshift(name_source)), '--minEest={0}'.format(eFitMin), '--maxEest={0}'.format(eFitMax), '--NormalizationE={0}'.format(eNorm)]
        print aCmd
        subprocess.call(aCmd)
        SetEnvironForMARS("5.34.14")
        subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/SaveFoldPlots.C("{1}/Status_fold.root", "{2}", "{3}")'.format(os.environ['PATH_PYTHON_MODULE_MINE'], path_dir_work, name_source, str_title_output)])
        shutil.move('{0}/Output_fold.root'.format(path_dir_work), '{0}/Output_fold_{1}{2}.root'.format(path_dir_work, name_source, str_title_output))
        shutil.move('{0}/Status_fold.root'.format(path_dir_work), '{0}/Status_fold_{1}{2}.root'.format(path_dir_work, name_source, str_title_output))
        file_Fold_out = ROOT.TFile('{0}/Output_fold_{1}{2}.root'.format(path_dir_work, name_source, str_title_output), 'READ')
        chiSq = file_Fold_out.Get('chisquare')
        ndof = file_Fold_out.Get('ndof')
        sed = file_Fold_out.Get('SpectralModel')
        dict_chiSq_red[func] = chiSq.GetVal()/ndof.GetVal()
        if dict_chiSq_red[func] < chiSq_ed_min:
            chiSq_ed_min = dict_chiSq_red[func]
            func_chiSq_ed_min = func
        print 'Chi^2/ndof =', dict_chiSq_red[func]
        dict_func_par[func].append([chiSq.GetVal(), ndof.GetVal()])
        for jpar in range(sed.GetNpar()):
            dict_func_par[func].append([sed.GetParameter(jpar), sed.GetParError(jpar)])
    print '=========='
    print dict_chiSq_red
    print 'Minimum chi^2/ndof function:', func_chiSq_ed_min
    print 'Chi^2/ndof =', chiSq_ed_min
    return dict_func_par


def Unfold(name_source, li_path_input, path_dir_work='.', strSuffix='', li_func=[1, 2, 3, 4, 5], li_method = [3, 6], eFitMin=100, eFitMax=10000, deabsorption=True):
    """For running CombUnfold.C
unfold(name_source, li_path_input, path_dir_work='.', strSuffix='', li_func = [1, 2, 3, 4, 5], li_method = [3, 6], eFitMin=150, eFitMax=10000)
Methods: {1:'Schmelling-GaussNewton', 2:'Tikhonov', 3:'Bertero', 4:'ForwardUnfolding', 5:'Schmelling-MINUIT', 6:'BerteroW'}
Functions: {1:'PL', 2:'PLwCutoff', 3:'PLwVariableIndex', 4:'PLwVariableIndexAndCutoff', 5:'BPL', 6:'BPLwVariableAlpha1', 7:'BPLwVariableAlpha1AndCutoff'}
"""
    if strSuffix!='':
        strSuffix = '_' + strSuffix
    #if path_file_csv!="":
     #   file_csv = open(path_file_csv, 'a')

    ninput = len(li_path_input)
    print ninput, 'input files.'
    str_rc_input = """MCombineDataForUnfolding.NumFiles: {0}
""".format(ninput)
    for iinput in range(ninput):
        str_rc_input = str_rc_input + """MCombineDataForUnfolding.InputFiles[{0}]: {1}
""".format(iinput, li_path_input[iinput])
    redshift = GetRedshift(name_source)
    str_rc_redshift = ""
    if redshift==0.047 and deabsorption==True:
        str_rc_redshift = """MCallUnfold.AttFactorFile: {0}/ebl-model/exptau_z{1}_modelFranceschini.dat
""".format(os.environ['PATH_MARS_BASE'], redshift)
    os.chdir(path_dir_work)

    LI_NTRIAL = [0, 1]
    DICT_METHOD = {1:'Schmelling-GaussNewton', 2:'Tikhonov', 3:'Bertero', 4:'ForwardUnfolding', 5:'Schmelling-MINUIT', 6:'BerteroW'}
    DICT_FUNC = {1:'PL', 2:'PLwCutoff', 3:'PLwVariableIndex', 4:'PLwVariableIndexAndCutoff', 5:'BPL', 6:'BPLwVariableAlpha1', 7:'BPLwVariableAlpha1AndCutoff'}
    DICT_FUNC_PAR = {1:"""# these are values for Type 1
#                          f0      alpha     r
MCallUnfold.Npar: 3
MCallUnfold.ParamVinit: 0.4e-10     -2.0    0.4
MCallUnfold.ParamStep:  1.e-12      0.2    0.0
MCallUnfold.ParamLimlo: 1.e-15    -10.0    0.0
MCallUnfold.ParamLimup: 1.e-7      10.0    0.0
MCallUnfold.ParamFix:   0           0      1
""",
2:"""# these are values for Type 2
#                          f0      alpha    Ecut     r
MCallUnfold.Npar: 4
MCallUnfold.ParamVinit: 60.0e-12   -2.0     3.0    0.4
MCallUnfold.ParamStep:  1.e-12      0.2     0.08   0.0
MCallUnfold.ParamLimlo: 1.e-15    -10.0     0.1    0.0
MCallUnfold.ParamLimup: 1.e-7      10.0   100.     0.0
MCallUnfold.ParamFix:   0           0         0    1
""",
3:"""# these are values for Type 3
#                          f0         a      b      r
#                                                   alpha = a+b*log10(E/r)
MCallUnfold.Npar: 4
MCallUnfold.ParamVinit: 2.86e-12   -2.212  0.0    0.4
MCallUnfold.ParamStep:  1.e-12      0.26   0.01   0.0
MCallUnfold.ParamLimlo: 1.e-15    -10.0   -2.0    0.0
MCallUnfold.ParamLimup: 1.e-7      10.0    2.0    0.0
MCallUnfold.ParamFix:   0           0      0      1
""",
4:"""# these are values for Type 4
#                          f0         a      b    Ecut   r
#                                                   alpha = a+b*log10(E/r)
MCallUnfold.Npar: 5
MCallUnfold.ParamVinit: 8.0e-11    -3.4   -1.46  3.0   0.4
MCallUnfold.ParamStep:  1.e-12      0.3    0.1   0.1   0.0
MCallUnfold.ParamLimlo: 1.e-15    -10.0   -2.0    0.1  0.0
MCallUnfold.ParamLimup: 1.e-7      10.0    2.0  100.0  0.0
MCallUnfold.ParamFix:   0           0      0      0    1
""",
5:"""# these are values for Type 5
#                          f0      alpha1 alpha2  E0    beta   r
MCallUnfold.Npar: 6
MCallUnfold.ParamVinit: 2.7e-11    -2.35 -3.51   0.6    2.0  0.4
MCallUnfold.ParamStep:  1.e-12      0.2    0.4   0.06   0.6  0.0
MCallUnfold.ParamLimlo: 1.e-15    -10.0  -10.0   0.01   0.0  0.0
MCallUnfold.ParamLimup: 1.e-7      -1.0   -1.0 100.0  100.0  0.0
MCallUnfold.ParamFix:   0           0      0     0      1    1
""",
6:"""# these are values for Type 6
#                          f0         a   alpha2  E0    beta   b    r
#                                                   alpha1 = a+b*log10(E/r)
MCallUnfold.Npar: 7
MCallUnfold.ParamVinit: 2.7e-11    -2.35 -3.51   0.6    6.0  0.0  0.4
MCallUnfold.ParamStep:  1.e-12      0.2    0.4   0.06   0.6  0.01 0.0
MCallUnfold.ParamLimlo: 1.e-15    -10.0  -10.0   0.01   0.0 -3.0  0.0
MCallUnfold.ParamLimup: 1.e-7      -1.0   -1.0 100.0  100.0  3.0  0.0
MCallUnfold.ParamFix:   0           0      0     1      1    0    1
""",
7:"""# these are values for Type 7
#                          f0   alpha1 alpha2  E0   beta   Ecut   r
MCallUnfold.Npar: 7
MCallUnfold.ParamVinit: 2.7e-11 -2.35 -3.51   0.6    6.0    3.0  0.4
MCallUnfold.ParamStep:  1.e-12   0.2    0.4   0.06   0.6   10.0  0.0
MCallUnfold.ParamLimlo: 1.e-15 -10.0  -10.0   0.01   0.0    0.1  0.0
MCallUnfold.ParamLimup: 1.e-7   -1.0   -1.0 100.0  100.0 1000.0  0.0
MCallUnfold.ParamFix:   0        0      0     1      1      0    1
""",
8:"""# these are values for Type 8
#                          f0     a   alpha2  E0     beta   Ecut    b    r
#                                                   alpha1 = a+b*log10(E/r)
MCallUnfold.Npar: 8
MCallUnfold.ParamVinit: 2.7e-11 -2.35 -3.51   0.6    6.0    3.0   0.0  0.4
MCallUnfold.ParamStep:  1.e-12   0.2    0.4   0.06   0.6    0.1   0.01 0.0
MCallUnfold.ParamLimlo: 1.e-15 -10.0  -10.0   0.01   0.0    0.1 -10.0  0.0
MCallUnfold.ParamLimup: 1.e-7   -1.0   -1.0 100.0  100.0 1000.0  10.0  0.0
MCallUnfold.ParamFix:   0        0      0     1      1      0     1    1
"""}
    dict_func_par = {}
        # Modify RC file
    str_rc_title = ""
    str_rc_fitrange = """MCallUnfold.FitMinUser: {0}
MCallUnfold.FitMaxUser: {1}
""".format(eFitMin, eFitMax)
    for nmethod in li_method:
        dict_func_par[nmethod] = {}
        str_rc_method = """MCallUnfold.FlagUnfold: {0}
""".format(nmethod)
        for nfunc in li_func:
            print "*", DICT_FUNC[nfunc]
            dict_func_par[nmethod][nfunc] = []
            str_rc_func = """MCallUnfold.F1Type: {0}
""".format(nfunc) + DICT_FUNC_PAR[nfunc]
            for ntrial in LI_NTRIAL:
                SetEnvironForMARS("5.34.14")
                str_rc_range = """MCallUnfold.RangeAutoSelectA: {0}
MCallUnfold.RangeAutoSelectB: {0}
""".format(int(ntrial==0))
                str_rc_energy = ""
                if ntrial>0:
                    li_bin_energy = SelectEnergyBins(path_outdata, eFitMin, eFitMax)
                    str_rc_energy = """MCallUnfold.nminAnmaxA: {0} {1}
MCallUnfold.nminBnmaxB: {2} {3}
""".format(li_bin_energy[0][0], li_bin_energy[0][1], li_bin_energy[1][0], li_bin_energy[1][1])
                str_rc_title = "combunfold{0}_{1}_{2}-{3}GeV_{4}_{5}".format(strSuffix, DICT_FUNC[nfunc], eFitMin, eFitMax, DICT_METHOD[nmethod], ntrial)
                path_outdata = '{0}/Combined_Data_{1}.root'.format(path_dir_work, str_rc_title)
                path_unfold_rc1 = '{0}/{1}.rc'.format(path_dir_work, str_rc_title)
                strRcAdd = str_rc_input + str_rc_fitrange + str_rc_energy + str_rc_redshift + str_rc_range + str_rc_method + str_rc_func
                file_unfold_rc1 = open(path_unfold_rc1, 'w') 
                file_unfold_rc1.write(strRcAdd)
                rcOrig = open('{0}/mrcfiles/combunfold.rc'.format(os.environ['MARSSYS']), 'r')
                rcCopied = rcOrig.read()
                file_unfold_rc1.write(rcCopied)
                rcOrig.close()
                file_unfold_rc1.close()
                print '=====', path_unfold_rc1, '====='
                subprocess.call(['head', '-n', '30', path_unfold_rc1])
                liCmd = ['root', '{0}/macros/CombUnfold.C("{1}")'.format(os.environ['MARSSYS'], path_unfold_rc1)]
                #if ntrial==0:
                liCmd.append('-b')
                liCmd.append('-q')
                subprocess.call(liCmd)
            path_outplots = path_outdata.replace("Combined_Data", "Unfolding_Output", 1)
            subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/SaveUnfoldPlots.C("{1}", "{2}", "{3}")'.format(os.environ['PATH_PYTHON_MODULE_MINE'], path_outplots, name_source, str_rc_title)])

            file_plots = ROOT.TFile(path_outplots, 'READ')
            func = file_plots.Get('Func')
            nFuncPar = func.GetNpar()
            dict_func_par[nmethod][nfunc].append([func.GetChisquare(), func.GetNDF()])
            for ipar in range(nFuncPar):
                dict_func_par[nmethod][nfunc].append([func.GetParameter(ipar), func.GetParError(ipar)])
                print "Parameter No.{0}: {1} +/- {2}".format(ipar, dict_func_par[nmethod][nfunc][-1][0], dict_func_par[nmethod][nfunc][-1][1])
            print "Chi^2 / NDF =", dict_func_par[nmethod][nfunc][-1][0], "/", dict_func_par[nmethod][nfunc][-1][1]
            #if path_file_csv!="":
             #   str_csv = """{0}, {1}, {2}
#""".format())
              #  file_csv.write(
 #   if path_file_csv!="":
  #      file_csv.close()
    return dict_func_par        


def SelectEnergyBins(path_file_data, erangemin=0, erangemax=1000000):
    """Return a list of Eest and Etrue bin boundaries for the second CombUnfold.C run.
Input the output file of the first run.
"""
    file_data = ROOT.TFile(path_file_data, "READ")
    print file_data.GetName(), "is opened."

    #Eest
    htg_excess = file_data.Get("ExcessEnergy")
    print htg_excess.GetName(), "is found."
    bin_max = htg_excess.GetMaximumBin()
    # Lower bound
    binEest_min = bin_max
    for ibin in range(bin_max, 0, -1):
        if htg_excess.GetBinContent(ibin)<=0:
            break
        else:
            binEest_min = ibin
    binEest_min = max(binEest_min, htg_excess.FindBin(erangemin)-2) # No events or outside of your energy range
    # Upper bound
    binEest_max = bin_max
    for jbin in range(bin_max, htg_excess.GetNbinsX()+1):
        if htg_excess.GetBinContent(jbin)<=0:
            break
        else:
            binEest_max = jbin
    binEest_max = min(binEest_max, htg_excess.FindBin(erangemax)+2) # No events or outside of your energy range

    #Etrue
    htg_area = file_data.Get("CollectionArea")
    print htg_area.GetName(), "is found."
    binEtrue_min = max(htg_area.FindFirstBinAbove(10000.), htg_area.FindBin(erangemin)-1)
    binEtrue_max = min(htg_area.FindLastBinAbove(10000.)-1, htg_area.FindBin(erangemax)+1)
    #binEtrue_min = htg_area.FindFirstBinAbove(10000.)
    #binEtrue_max = htg_area.FindLastBinAbove(10000.)-1

    return [[binEest_min, binEest_max], [binEtrue_min, binEtrue_max]]


class SlowMARS(QuickMARS):
    """Class for slow analysis. You should know which data file is corresponding to each cut condition.
1) sma = SlowMARS(nameSrc, strTitle, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=2000., bReducedHV=False, bTimesOption=True, strTypeMC='', strPeriodMC=''):
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
12) sma.odie(bLE=True, bFR=True, bHE=False)
13) sma.flute(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc=True, bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1)
== Decent Moon ==
3) Put your calibrated and ssignal files to the created directories
4) sma.ssignal()
5) sma.starMC(bTrain=True, bTest=True)
6) sma.star()
7) sma.starOFF()
8) sma.superstar()
9) sma.superstarMC(bTrain=True, bTest=True)
10) sma.superstarOFF()
11) sma.quateOFF()
12) sma.selectmc(True, True)
13) sma.coach()
14) sma.melibea(True)
15) sma.melibeaMC(False, True)
16) sma.odie(bLE=True, bFR=True, bHE=False)
17) sma.flute(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc=True, bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1)
"""
    def __init__(self, nameSrc, strTitle, ZenithCut='35to50', TransCut9km='55', CloudCut='No', naCutDC=2000., bReducedHV=False, bTimesOption=True, strTypeMC='', strPeriodMC='', bForce=True):
        SetEnvironForMARS(verRoot = "5.34.24")
        QuickMARS.__init__(self, nameSrc, '1960-01-01', ZenithCut, TransCut9km, CloudCut, naCutDC, bReducedHV, bTimesOption, strTypeMC, strPeriodMC, bForce)
        self.titleAnalysis = strTitle
        self.pathDirSpot = '{0}/{1}/{2}/{3}'.format(self.getPathBase(), self.getSourceName(), self.getTitleAnalysis(), self.getConfigName())
        self.pathDirAnalysis = '{0}/{1}/{2}'.format(self.getPathBase(), self.getSourceName(), self.getTitleAnalysis())
        self.pathDirCondition = self.getPathDirSpot()
        self.setSubDirs()


    def fluteAllRunByRun(self, eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc="",bSingleBin=True, bCustom=False, fluxMaxInCrab=1.1, strFileInitial="20", nBinAz=1):
        """Run flute for all runs in the melibea directory run by run.
        .fluteAllRunByRun(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc="", bCustom=False, fluxMaxInCrab=1.1)
        """
        # Make a list of #RUN
        aFile = glob.glob('{0}/{1}*_Q_*.root'.format(self.getPathDirMelibea(), strFileInitial))
        aRun = []
        dictNight = {}
        for fileQ in aFile:
            fileR = os.path.basename(fileQ)
            aRun.append(fileR[9:17])
            dictNight[aRun[-1]] = fileR[:8]
        aRunUiq = list(set(aRun))
        print len(aRunUiq), 'runs.'
        print aRunUiq
        for runUiq in aRunUiq:
            print '=====', runUiq, '====='
            pathDirOut = '{0}/{1}'.format(self.pathDirAnalysis, dictNight[runUiq])
            self.flute(eth, assumedSpectrum, redshift, bMelibeaNonStdMc, False, False, bSingleBin, bCustom, fluxMaxInCrab, runDesignate=runUiq, bDisplay=False, nameSubDirWork=pathDirOut, pathCustomBinRefer="{0}/Output_flute_{1}_run{2}_{3}GeV_single-bin.root".format(pathDirOut, self.getConfigName(), runUiq, int(eth)), nbinAz=nBinAz)


    def fluteAllNightByNight(self, strNight, eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc="",bNightWise=True, bRunWise=True, bSingleBin=False, bCustom=False, fluxMaxInCrab=1.1, nBinAz=1):
        """Run flute night by night but for only runs which satisfy the condition of this class.
        .fluteAllNightByNight(eth=300, assumedSpectrum="", redshift="", bMelibeaNonStdMc="", bCustom=False, fluxMaxInCrab=1.1)
        """
        print strNight
        if len(strNight)==10:
            strNightShort = MakeShortDateExpression(strNight)
        elif len(strNight)==8:
            strNightShort = strNight
        else:
            print "Wring night input!!!"
            return 1
        pathDirOut = '{0}/{1}'.format(self.pathDirAnalysis, strNight)
        self.flute(eth, assumedSpectrum, redshift, bMelibeaNonStdMc, bNightWise, bRunWise, bSingleBin, bCustom, fluxMaxInCrab, nightDesignate=strNightShort, bDisplay=False, nameSubDirWork=pathDirOut, pathCustomBinRefer="{0}/Output_flute_{1}_{2}_{3}GeV_night-wise.root".format(pathDirOut, self.getConfigName(), strNightShort, int(eth)), nbinAz=nBinAz)


    def createAllNightCard(self, eth=300, erangemin=100, erangemax=1000, binning="run-wise", bFoam=True, bCombineLC=True, bUnfoldPL=True, bFoldPL=True, strFileInitial="20??????"):
        """Execute the post-flute analysis night by night. Flute output files should be in the night directories before running.
"""
        # Make a list of nights
        li_dir_Night = glob.glob('{0}/{1}'.format(self.pathDirAnalysis, strFileInitial))
        print li_dir_Night
        for path_night in li_dir_Night:
            print "*", path_night
            strNightShort = path_night[-8:]
            aFile = glob.glob('{0}/Output_flute_{1}_{2}_{3}GeV_{4}.root'.format(path_night, self.getConfigName(), strNightShort, int(eth), binning))
            night = NightCard(source=self.getSourceName(), night='{0}-{1}-{2}'.format(strNightShort[:4], strNightShort[4:6],strNightShort[6:8]), li_path_fluteoutput=aFile, path_output=path_night, emin=eth, efitmin=erangemin, efitmax=erangemax, bin_src=binning)
            if bFoam==True:
                night.foam()
            if bCombineLC==True:
                night.combineLC()
            if bUnfoldPL==True:
                night.unfoldPL()
            if bFoldPL==True:
                night.foldPL()

            
class NightCard:
    """1) Combined SED (foam)
2) Night-range LC
3) Unfolding with PL
4) Fine binning LC (future)
5) Night flux value (future)
"""
    def __init__(self, source, night, li_path_fluteoutput, path_output, emin=300, efitmin=100, efitmax=10000, bin_src="run-wise", enorm=300):
        self.NAMESRC = source
        self.TIMETHISNIGHT = Time(night, format='iso', in_subfmt='date', out_subfmt='date', scale='utc')
        self.TIMETHISNIGHT_SHORT = MakeShortDateExpression(self.TIMETHISNIGHT.value)
        self.LI_PATH_FLUTEOUTPUT = li_path_fluteoutput
        self.NFLUTEOUTPUT = len(self.LI_PATH_FLUTEOUTPUT)
        self.PATH_OUTPUT = path_output
        self.EMIN=emin
        self.EFITMIN=efitmin
        self.EFITMAX=efitmax
        self.ENORM=enorm
        self.BINSRC=bin_src
        self.PATH_FOAMOUT = "{0}/Foam_{1}_{2}.root".format(self.PATH_OUTPUT, self.NAMESRC, self.TIMETHISNIGHT_SHORT)


    def foam(self):
        if self.NFLUTEOUTPUT>1:
            Foam(name_source=self.NAMESRC, li_path_input=self.LI_PATH_FLUTEOUTPUT, path_dir_work=self.PATH_OUTPUT, strSuffix=self.TIMETHISNIGHT_SHORT)


    def combineLC(self):
        file_list = open('list_LC_temp.txt', 'w')
        for file_input in self.LI_PATH_FLUTEOUTPUT:
            file_list.write("""{0}
""".format(file_input))
        file_list.close()
        SetEnvironForMARS("5.34.14")
        subprocess.call([ 'root', '-b', '-q', '{0}/MarsUtil/CombineLCs.C("list_LC_temp.txt", "{1}/LightCurve_{2}_{3}_{4}GeV_{5}.root", "{2}_{3}")'.format(os.environ['PATH_PYTHON_MODULE_MINE'], self.PATH_OUTPUT, self.NAMESRC, self.TIMETHISNIGHT_SHORT, int(self.EMIN), self.BINSRC)])


    def foldPL(self):
        if self.NFLUTEOUTPUT>1:
            dict_par = Fold(name_source=self.NAMESRC, path_file_input=self.PATH_FOAMOUT, path_dir_work=self.PATH_OUTPUT, strSuffix=self.TIMETHISNIGHT_SHORT, li_func = ['PWL'], eFitMin=self.EFITMIN, eFitMax=self.EFITMAX, eNorm=self.ENORM)
        else:
            dict_par = Fold(name_source=self.NAMESRC, path_file_input=self.LI_PATH_FLUTEOUTPUT[0], path_dir_work=self.PATH_OUTPUT, strSuffix=self.TIMETHISNIGHT_SHORT, li_func = ['PWL'], eFitMin=self.EFITMIN, eFitMax=self.EFITMAX)
        file_csv = open('{0}/FoldFitPars_{1}_{2}_{3}-{4}GeV_PWL.csv'.format(self.PATH_OUTPUT, self.NAMESRC, self.TIMETHISNIGHT_SHORT, self.EFITMIN, self.EFITMAX), 'w')
        str_descript = "#MJD/I:Function/C:ChiSquare/F:NDF/I"
        for ipar in range(2):
            str_descript = str_descript + ":Par{0}/F:Par{0}Err/F".format(ipar)
        str_descript = str_descript + """
"""
        for key_func, li_func in dict_par.items():
            str_descript = str_descript + "{0},{1}".format(int(self.TIMETHISNIGHT.mjd+0.5), key_func)
            for li_par in li_func:
                str_descript = str_descript + ",{0},{1}".format(li_par[0],li_par[1]) 
            str_descript = str_descript + """
"""
        file_csv.write(str_descript)
        file_csv.close()


    def unfoldPL(self):
        dict_par = Unfold(name_source=self.NAMESRC, li_path_input=self.LI_PATH_FLUTEOUTPUT, path_dir_work=self.PATH_OUTPUT, strSuffix=self.TIMETHISNIGHT_SHORT, li_func = [1], li_method = [3, 6], eFitMin=self.EFITMIN, eFitMax=self.EFITMAX)
        file_csv = open('{0}/CorrFitPars_{1}_{2}_{3}-{4}GeV_PWL.csv'.format(self.PATH_OUTPUT, self.NAMESRC, self.TIMETHISNIGHT_SHORT, self.EFITMIN, self.EFITMAX), 'w')
        str_descript = "#MJD/I:Function/I:Method/I:ChiSquare/F:NDF/I"
        for ipar in range(3):
            str_descript = str_descript + ":Par{0}/F:Par{0}Err/F".format(ipar)
        str_descript = str_descript + """
"""
        for key_method, dict_method in dict_par.items():
            for key_func, li_func in dict_method.items():
                str_descript = str_descript + "{0},{1},{2}".format(int(self.TIMETHISNIGHT.mjd+0.5), key_func, key_method)
                for li_par in li_func:
                    str_descript = str_descript + ",{0},{1}".format(li_par[0],li_par[1]) 
                str_descript = str_descript + """
"""
        file_csv.write(str_descript)
        file_csv.close()


def DownloadPicData(strPicDir, strDirTgt, password, cDataType="S", nTel="", nRun="", bPjsub=False, bMC=False, strRscGrp="A"):
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
    elif bMC==True:
        if nTel=="" and nRun=="":
            strFind = 'GA_.*?_{0}_.*?root'.format(cDataType)
        elif nTel=="":
            strFind = 'GA.*?_{1}.*?_{0}_.*?root'.format(cDataType, nRun)
        elif nRun=="":
            strFind = 'GA_M{1}_.*?_{0}_.*?root'.format(cDataType, nTel)
        else:
            strFind = 'GA_M{1}_{2}.*?_{0}_.*?root'.format(cDataType, nTel, nRun)
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
            time.sleep(30)
        else:
            strCmd = 'wget -O{0} -nc -nv --user=MAGIC --password={1} {2}/{3}'.format(rootFile, password, strPicDir, rootFile)
            nameSub,extSub = os.path.splitext( os.path.basename(rootFile) )
            SubmitPJ(strCmd, strDirTgt, 'wg{0}'.format(nameSub), strRscGrp)


def SetEnvironForMARS(verRoot = "5.34.24"):
    if verRoot == "5.34.24":
        os.environ["ROOTSYS"] = "/home/takhsm/app/root_v5.34.24"
#        os.environ["MARSSYS"] = "/home/takhsm/app/Mars/Mars_V2-16-2_ROOT53424"
        os.environ["MARSSYS"] = "/home/takhsm/app/Mars/Mars_V2-17-0_ROOT53424"
        os.environ["PATH"] = "/home/takhsm/app/Mars/Mars_V2-17-0_ROOT53424:/home/takhsm/app/ROOT_v53424/bin:/home/takhsm/app/anaconda2/bin:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/usr/local/bin:/bin:/usr/bin"
        os.environ["LD_LIBRARY_PATH"] = "/home/takhsm/app/root_v5.34.24/lib:/home/takhsm/app/root_v5.34.24/lib/root:/home/takhsm/app/lib:/home/takhsm/app/root_v5.34.24:/home/takhsm/app/Mars/Mars_V2-17-0_ROOT53424:/home/takhsm/lib/libPNG/lib:/home/takhsm/lib/lib:/home/takhsm/lib/libJPEG/lib:/home/takhsm/CTA_MC/Chimp/Chimp:/home/takhsm/CTA_MC/Chimp/Chimp/hessioxxx/lib:/home/takhsm/charaPMT:/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/usr/lib64"
    if verRoot == "5.34.14":
        os.environ["ROOTSYS"] = "/usr/local/gcc473/root_v5.34.14"
        os.environ["MARSSYS"] = "/home/takhsm/app/Mars/Mars_V2-15-8"
        os.environ["PATH"] = "/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/usr/local/gcc473/root_v5.34.14/bin:/home/takhsm/app/Mars/Mars_V2-15-8:/usr/lib64/qt-3.3/bin:/usr/local/bin:/bin:/usr/bin" #"/home/takhsm/app/Mars/Mars_V2-15-8:/usr/local/gcc473/root_v5.34.14/bin:/usr/local/gcc473/bin:/home/takhsm/app/Python2/bin:/usr/local/gcc473/bin:/usr/lib64/qt-3.3/bin:/usr/local/bin:/bin:/usr/bin"
        os.environ["LD_LIBRARY_PATH"] = "/home/takhsm/lib/lib:/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/usr/local/gcc473/root_v5.34.14/lib:/usr/local/gcc473/root_v5.34.14/lib/root:/home/takhsm/app/lib:/usr/local/gcc473/root_v5.34.14:/home/takhsm/app/Mars/Mars_V2-15-8"
#"/usr/local/gcc473/lib64:/usr/local/gcc473/lib:/usr/local/gcc473/root_v5.34.14/lib:/usr/local/gcc473/root_v5.34.14/lib/root:/home/takhsm/app/lib:/usr/local/gcc473/root_v5.34.14:/home/takhsm/app/Mars/Mars_V2-15-8:/home/takhsm/lib/lib"
        os.environ["PYTHONPATH"] = "/usr/local/gcc473/ROOT/lib/root:/home/takhsm/app/yaml/lib64/python:/home/takhsm/app/lib/python2.7/site-packages:/home/takhsm/app/Python2/lib/python2.7/site-packages:/home/takhsm/PythonModuleMine"
def GetRedshift(nameSource):
    if nameSource=='1ES1959+650':
        return 0.047
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

    
def getPeriodMC(timeNightIso):
    """Return an exprssion of MC period corresponding to the input night"""
    if timeNightIso >= Time('2016-04-29', format='iso', in_subfmt='date', out_subfmt='date', scale='utc'):
        return 'ST.03.07'
    elif timeNightIso >= Time('2014-11-24', format='iso', in_subfmt='date', out_subfmt='date', scale='utc'):
        return 'ST.03.06'
    elif timeNightIso >= Time('2014-08-31', format='iso', in_subfmt='date', out_subfmt='date', scale='utc'):
        return 'ST.03.05'
    else:
        print 'pMyMarsUtil is not available for this night!!!'
        return 1


def pjstat():
    shellCom('pjstat')
