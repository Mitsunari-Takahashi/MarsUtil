#!/usr/bin/env python

import sys
import os
import os.path
import click
import numpy as np
import numpy.ma as ma
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import ROOT
from ROOT import gROOT, gDirectory, gPad, gSystem, gStyle, kTRUE, kFALSE, TGraphErrors, TGraphAsymmErrors, TF1
ROOT.gROOT.SetBatch()
from Fermi.pColor import *


mpl.rcParams['text.usetex'] = True
mpl.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}']
plt.rcParams["font.size"] = 14


class SED:
    def __init__(self, name, ised=1, path_file=None, deabsorbed=False):
        self.ISED = ised
        self.name = name
        self.path_file = path_file
        self.deabsorbed = deabsorbed
        print 'No.', self.ISED
        print 'Name:', self.name
        self.name_graph = None
        self.name_func = None
        self.graph = None
        self.function = None
        if self.path_file is not None:
            self.load(self.path_file, self.deabsorbed)
            print 'File:', self.path_file
            print 'Deabsorbed:', self.deabsorbed


    def load(self, path_file, deabsorbed):
        self.file_data = ROOT.TFile(self.path_file, 'READ')
        if os.path.basename(self.path_file)[:11]=='Output_fold':
            if self.deabsorbed==False:
                self.name_graph = 'observed_sed'
                self.name_func = 'abs_sed'
            else:
                self.name_graph = 'deabsorbed_sed'
                self.name_func = 'fsed'
        elif os.path.basename(self.path_file)[:16]=='Unfolding_Output':
            if self.deabsorbed is False:
                print 'Absorbed SED is unavilable for', os.path.basename(self.path_file)
                return 1
            else:
                self.name_graph = 'fGraph1E2'
                self.name_function = 'FuncE2'
        elif os.path.basename(self.path_file)[:12]=='Output_flute':
            if self.deabsorbed is False:
                self.name_graph = 'SED'
            else:
                self.name_graph = 'DeabsorbedSED'
        elif os.path.basename(self.path_file)[:4]=='Foam':
            if self.deabsorbed is False:
                self.name_graph = 'sed'
            else:
                print 'Deabsorbed SED is unavailable for', os.path.basename(self.path_file)
                return 1
        else:
            print os.path.basename(self.path_file), 'is unavailable.'
            return 1

        if self.name_graph is not None:
            self.graph = self.file_data.Get(self.name_graph)
            print 'ROOT graph object {0} has been found.'.format(self.graph.GetName())
        if self.name_function is not None:
            self.function = self.file_data.Get(self.name_function)

        # Graph
        x, y = ROOT.Double(0), ROOT.Double(0)
        if self.graph is not None and self.graph.GetName()==self.name_graph:
            NPOINTS = self.graph.GetN()
            self.xvals = np.zeros(NPOINTS)
            self.xerrs = {'low':np.zeros(NPOINTS), 'high':np.zeros(NPOINTS)}
            self.yvals = np.zeros(NPOINTS)
            self.yerrs = {'low':np.zeros(NPOINTS), 'high':np.zeros(NPOINTS)}
            for ipoint in range(NPOINTS):
                self.graph.GetPoint(ipoint, x, y)
                self.xvals[ipoint] = x
                self.yvals[ipoint] = y
                self.xerrs['low'][ipoint] = self.graph.GetErrorXlow(ipoint)
                self.xerrs['high'][ipoint] = self.graph.GetErrorXhigh(ipoint)
                self.yerrs['low'][ipoint] = self.graph.GetErrorYlow(ipoint)
                self.yerrs['high'][ipoint] = self.graph.GetErrorYhigh(ipoint)
        else:
            print 'ROOT graph object {0} is NOT loaded!!!'.format(self.graph.GetName())
            return 1
        # Function is not plotted with this version


    def plot(self, ax):
        LIST_MARKER = ['o', 's', 'D']
        LIST_COLOR = ['k', 'r', 'b', 'hotpink', 'g']
        ax.errorbar(self.xvals, self.yvals, xerr=(self.xerrs['low'], self.xerrs['high']), yerr=(self.yerrs['low'], self.yerrs['high']), fmt=LIST_MARKER[self.ISED], c=LIST_COLOR[self.ISED], label=self.name, lw=2)



def PlotSEDs(tpl_seds, str_output, title, xlim, ylim):
    nplot = len(tpl_seds)
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title(title)
    ised = 0
    for sedin in tpl_seds:
        sed = SED(name=sedin[0], ised=ised, path_file=sedin[1], deabsorbed=sedin[2])
        sed.plot(ax)
        ax.legend(loc=0)
        ised+=1
    ax.set_xlabel(r'$E \, \rm{[GeV]}$')
    ax.set_ylabel(r'$E^{2}dN/dEdAdt\,\rm{[TeV\cdot cm^{-2}\cdot s^{-1}]}$')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.grid(which='major', ls='-', alpha=0.8)
    ax.grid(which='minor', ls='--', alpha=0.4)
    if xlim is not [None]*2:
        ax.set_xlim(xlim)
    if ylim is not [None]*2:
        ax.set_ylim(ylim)
    fig.tight_layout()
    fig.savefig(str_output)


@click.command()
@click.option('--sed', '-s', multiple=True, type=(str, str, bool), help='"Title" "Path of file" "True/False whether deabsorbed"')
@click.argument('outname', type=str)
@click.option('--title', '-t', type=str, default='Comparison of SED graphs')
#@click.option('--absorbed', is_flag=True)
@click.option('--xlim', '-x', type=(float, float), default=(None, None))
@click.option('--ylim', '-y', type=(float, float), default=(None, None))
def main(sed, outname, title, xlim, ylim):
    PlotSEDs(sed, outname, title, xlim, ylim)

if __name__ == '__main__':
    main()
