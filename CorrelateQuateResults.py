#!/usr/bin/env python

import sys
#import os
#import numpy
#import yaml
#import datetime
#from array import array
import math
from math import cos, sin, tan, acos, asin, atan, radians, degrees, pi, sqrt
import click
import ROOT
from ROOT import TTree, gROOT, gDirectory, gPad, gSystem, gStyle, kTRUE, kFALSE
ROOT.gROOT.SetBatch()
#from pMETandMJD import *


def CorrelateQuateResults(quateout, suffix, formula, sigma):
    if suffix!='':
        suffix = '_' + suffix
    file_quate = ROOT.TFile(quateout, 'READ')
    tr_quate = file_quate.Get('RunSum')
    print tr_quate.GetName(), 'is found.'
    NRUN = tr_quate.GetEntries()
    gr_Rate_DC1 = ROOT.TGraphErrors(0)
    gr_Rate_DC1.SetName("gr_Rate_DC1")
    gr_Rate_DC1.SetTitle("L3 Rate vs. DC (M1)")
    gr_Rate_Trans = ROOT.TGraphErrors(0)
    gr_Rate_Trans.SetName("gr_Rate_Trans")
    gr_Rate_Trans.SetTitle("L3 Rate vs. Transmission at 9km")
    gr_Star_DC1 = ROOT.TGraph(0)
    gr_Star_DC1.SetName("gr_Star_DC1")
    gr_Star_DC1.SetTitle("Number of stars vs. DC (M1)")
    #for irun in range(NRUN):
    for (irun,run) in enumerate(tr_quate):
        #tr_quate.GetEntry(irun)
        # gr_Rate_DC1.SetPoint(irun, tr_quate.fRate, sqrt(tr_quate.fMedianDC))
        # gr_Rate_Trans.SetPoint(irun, tr_quate.fRate, tr_quate.fAerosolTrans9km)
        # gr_Star_DC1.SetPoint(irun, tr_quate.fNumStars, tr_quate.fAerosolTrans9km)
        gr_Rate_DC1.SetPoint(irun, run.fRate, sqrt(run.fMedianDC))
        gr_Rate_Trans.SetPoint(irun, run.fRate, run.fAerosolTrans9km)
        gr_Star_DC1.SetPoint(irun, run.fNumStars, run.fAerosolTrans9km)

    file_out = ROOT.TFile('Transmission_vs_Rate{0}'.format(suffix), 'RECREATE')
    file_out.cd()
    
    fcFit = ROOT.TF1('fcFit', '[0]+[1]*TMath::Power(x, [2])', 0, 100)
    if formula!='':
        fcFit = ROOT.Tf1('fcFit', formula, 0, 100)
    else:
        fcFit.SetParameter(0, 50)
        fcFit.FixParameter(2, -1.6)
        gr_Rate_DC1.Fit(fcFit, "", "", 0, 80)
    hRateDev = ROOT.TH1D('hRateDev', 'L3 Rate deviation form the fitted value', 100, -1, 1)
    xbox, ybox = ROOT.Double(0), ROOT.Double(0) #ROOT.Double
    for jrun in NRUN:
        tr_quate.GetEntry(jrun)
        gr_Rate_DC1.GetPoint(jrun, xbox, ybox)
        vfit = fcFit.Eval(xbox)
        hRateDev.Fill(ybox-vfit-1, tr_quate.fDuration)
    ratedev_mean = hRateDev.GetMean()
    ratedev_rms = hRateDev.GetRMS()
    print "Rate/Rate_{fit}-1"
    print "Mean =", ratedev_mean
    print "S.D. =", ratedev_rms
    gr_Rate_DC1.Write()
    gr_Rate_Trans.Write()
    gr_Star_DC1.Write()

    for krun in NRUN:
        tr_quate.GetEntry(krun)
        ufit = fcFit.Eval(sqrt(tr_quate.fMedianDC))
        if abs(tr_quate.fRate/ufit-1)>ratedev_rms*sigma:
            print 'Run', tr_quate.fRunNumber, 'has Rate', tr_quate.fRate, 'Hz', '(cf. expected=', ufit, 'Hz)'
        


@click.command()
@click.argument('quateout', type=str)
@click.option('--suffix', type=str, default='')
@click.option('--formula', type=str, default='')
@click.option('--sigma', type=float, default=2)
def main(quateout, suffix, formula, sigma):
    CorrelateQuateResults(quateout, suffix, formula, sigma)


if __name__ == '__main__':
    main()
