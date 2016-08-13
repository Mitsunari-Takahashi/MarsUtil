#!/usr/bin/env python

import sys
import numpy
import yaml
from pMETandMJD import *
import datetime
from array import array
import math
import ROOT
from ROOT import TString, TObjArray, TObjString
ROOT.gROOT.SetBatch()

def getIntPedEx(aFileIn=[], strSuffix=""):
    nFile = len(aFileIn)
    if nFile<1:
        print 'No input files!'
        return 1
    aSA = []
    aNameFileIn = []
    aCan = []
    aPadMean = []
    aPadRms = []
    aGreMean = []
    aGreRms = []
    mgrMean = ROOT.TMultiGraph("mgrMean", "IntPedExtr_Mean")
    mgrRms = ROOT.TMultiGraph("mgrRMs", "IntPedExtr_RMS")
    for pathFile in aFileIn:
        fileIn = ROOT.TFile(pathFile, 'READ')
        print fileIn.GetName(), "is opened."
        aSA.append(fileIn.Get)
