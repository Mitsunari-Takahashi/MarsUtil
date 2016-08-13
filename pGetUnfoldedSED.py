#!/usr/bin/env python

import sys
import numpy as np
from array import array
import math
import ROOT
from ROOT import TFile, TGraphAsymmErrors
ROOT.gROOT.SetBatch()
par = sys.argv

pathFileIn = par[1]
fileIn = ROOT.TFile(pathFileIn, 'READ')
print fileIn.GetName(), 'is opened.'
aNameTgt = ['fGraph1E2', 'fGraph2E2']
aResults = []
for iTgt in aNameTgt:
    grae = fileIn.Get(iTgt)
    print "#", grae.GetTitle()
    print "# Point, ", grae.GetXaxis().GetTitle(), ", XErrorHigh, XErrorLow, ", grae.GetYaxis().GetTitle(), ", YErrorHigh, YErrorLow"
    nGrae1E2 = grae.GetN()
    ax = np.zeros(3, dtype=float)
    ay = np.zeros(3, dtype=float)
    aPoints = []
    for iPot in range(nGrae1E2):
        aPoints.append([])
        grae.GetPoint(iPot, ax, ay)
        ax[1] = grae.GetErrorXhigh(iPot)
        ax[2] = grae.GetErrorXlow(iPot)
        aPoints[-1].append(ax)
        ay[1] = grae.GetErrorYhigh(iPot)
        ay[2] = grae.GetErrorYlow(iPot)
        aPoints[-1].append(ay)
        print '{0}, {1}, {2}, {3}, {4}, {5}, {6}'.format(iPot, ax[0], ax[1], ax[2], ay[0], ay[1], ay[2])
    aResults.append(aPoints)
#return aResults
