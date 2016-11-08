#!/usr/bin/env python

import sys
import numpy as np
import datetime
from array import array
import math
import ROOT
from ROOT import TGraphErrors
ROOT.gROOT.SetBatch()
par = sys.argv

def GetLC_bins(pathFileIn, minBinWidth=3.0):
    fileIn = ROOT.TFile(pathFileIn, 'READ')
    print fileIn.GetName(), "is opened."
    greLC = fileIn.Get("LightCurve")
    print greLC.GetName(), "is found."
    ax = np.zeros(1, dtype=float)
    ay = np.zeros(1, dtype=float)
    aMjdItvTgt = [[], []]
    for i in range(greLC.GetN()):
        print "==========="
        greLC.GetPoint(i, ax, ay);
        xerr = greLC.GetErrorX(i)
        mjdStartOrg = ax[0]-xerr
        mjdStopOrg = ax[0]+xerr
        minItvOrg = 2.*xerr*24.*60.
        nBinTgt = max(1, int(minItvOrg / minBinWidth))
        minBinTgt = minItvOrg/nBinTgt
        while minBinTgt>=minBinWidth+0.5:
            nBinTgt = nBinTgt+1
            minBinTgt = minItvOrg/nBinTgt
        print "Divided bin number:", nBinTgt
        print "Divided bin interval:", minBinTgt, "min"
        dayBinTgt = minBinTgt/24./60.
        for j in range(nBinTgt):
            aMjdItvTgt[0].append(mjdStartOrg+j*dayBinTgt)
            aMjdItvTgt[1].append(mjdStartOrg+(j+1)*dayBinTgt)
    return aMjdItvTgt

