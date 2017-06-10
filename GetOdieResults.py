#!/usr/bin/env python

import sys
#import os
#import numpy
#import yaml
#import datetime
#from array import array
import math
from math import cos, sin, tan, acos, asin, atan, radians, degrees, pi
import click
import ROOT
from ROOT import gROOT, gDirectory, gPad, gSystem, gStyle, kTRUE, kFALSE, TCanvas, TPaveText
ROOT.gROOT.SetBatch()


def GetOdieResults(path_file_odie, path_fileout, tag):
    file_odie = ROOT.TFile(path_file_odie, 'READ')
    print '--------------------'
    print file_odie.GetName(), 'is opened.'
    cvs_th2OnAndOff = file_odie.Get('th2OnAndOffCan')
    if cvs_th2OnAndOff!=None:
        print cvs_th2OnAndOff.GetName(), 'is found.'
    else:
        print 'th2OnAndOffCan is not found!!!'
        exit(0)
    pt = cvs_th2OnAndOff.FindObject('TPave')
    cvs_line = """Time:N_{on}:N_{off}:N_{off}Error:N_{ex}:Significance
"""
    if tag!=None:
        cvs_line = 'Tag:' + cvs_line + tag + ','
    for iline in range(pt.GetListOfLines().GetEntries()):
        strLine = pt.GetListOfLines().At(iline).GetTitle()
        print strLine
        if strLine[:4] == 'Time':
            obstime = strLine[7:strLine.find(' h')]
            cvs_line = cvs_line + obstime + ','
        elif strLine[:4] == 'N_{o':
            index_semicolon = strLine.find('; N_{off} = ')
            index_pm = strLine.find(' #pm ')
            non = strLine[9:index_semicolon]
            noff = strLine[index_semicolon+12:index_pm]
            noff_err = strLine[index_pm+6:]
            cvs_line = cvs_line + non + ',' + noff + ',' + noff_err + ','
        elif strLine[:4] == 'N_{e':
            nex = strLine[9:]
            cvs_line = cvs_line + nex + ','
        elif strLine[:4] == 'Sign':
            sgnf = strLine[23:strLine.find('#sigma')]
            cvs_line = cvs_line + sgnf + """
"""
    if path_fileout!=None:
        with open(path_fileout, 'a') as text:
            text.write(cvs_line)


@click.command()
@click.argument('odie', type=str)
@click.option('--output', '-o', type=str, default=None)
@click.option('--tag', '-t', type=str, default=None)
def main(odie, output, tag):
    GetOdieResults(path_file_odie=odie, path_fileout=output, tag=tag)


if __name__ == '__main__':
    main()
