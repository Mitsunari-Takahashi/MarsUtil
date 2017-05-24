#!/usr/bin/env python

import sys
import os
import os.path
import click
import ROOT
from ROOT import gROOT, gDirectory, gPad, gSystem, gStyle, kTRUE, kFALSE, TGraphErrors, TF1
ROOT.gROOT.SetBatch()
from Fermi.pColor import *


def SetGraphStyle(graph, title, ised):
    graph.SetTitle(title)
    graph.SetLineColor(akColor(ised))
    graph.SetMarkerColor(akColor(ised))
    graph.SetFillStyle(0)


def CampareSEDs(tpl_seds, str_output, title, absorbed, yrange):
    file_out = ROOT.TFile('{0}.root'.format(str_output), 'RECREATE')
    files_sed = []
    graphs_sed = []
    fc_sed = []
    mgr = ROOT.TMultiGraph('mgr', title)
    graphname = 'sed'
    fcname = 'FuncE2'
    for (ised, sed) in enumerate(tpl_seds):
        print 'No.', ised, sed[0]
        print 'File:', sed[1]
        files_sed.append(ROOT.TFile(sed[1], 'READ'))
        if os.path.basename(sed[1])[:11]=='Output_fold':
            if absorbed==True:
                graphname = 'observed_sed'
                fcname = 'abs_sed'
            else:
                graphname = 'deabsorbed_sed'
                fcname = 'fsed'
            graphs_sed.append(files_sed[-1].Get(graphname))
            SetGraphStyle(graphs_sed[-1], sed[0], ised)
            mgr.Add(graphs_sed[-1])
            fc_sed.append(files_sed[-1].Get(fcname))
            print fc_sed[-1].GetName(), 'is found.'
            fc_sed[-1].SetLineColor(akColor(ised))
        elif os.path.basename(sed[1])[:16]=='Unfolding_Output':
            if absorbed==True:
                print 'Absorbed SED is unavilable for', os.path.basename(sed[1])
                return 1
            else:
                fcname = 'FuncE2'
                graphs_sed.append(files_sed[-1].Get('fGraph1E2'))
                print graphs_sed[-1].GetName(), 'is found.'
                SetGraphStyle(graphs_sed[-1], '{0} (used)'.format(sed[0]), ised)
                mgr.Add(graphs_sed[-1])
                graphs_sed.append(files_sed[-1].Get('fGraph2E2'))
                print graphs_sed[-1].GetName(), 'is found.'
                SetGraphStyle(graphs_sed[-1], '{0} (unused)'.format(sed[0]), ised)
                mgr.Add(graphs_sed[-1])
                print fcname
                fc_sed.append(files_sed[-1].Get(fcname))
                print fc_sed[-1].GetName(), 'is found.'
                fc_sed[-1].SetLineColor(akColor(ised))
        elif os.path.basename(sed[1])[:12]=='Output_flute':
            if absorbed==True:
                graphname = 'SED'
            else:
                graphname = 'DeabsorbedSED'
            graphs_sed.append(files_sed[-1].Get(graphname))
            print graphs_sed[-1].GetName(), 'is found.'
            SetGraphStyle(graphs_sed[-1], sed[0], ised)
            mgr.Add(graphs_sed[-1])
        elif os.path.basename(sed[1])[:4]=='Foam':
            if absorbed==True:
                graphname = 'sed'
                graphs_sed.append(files_sed[-1].Get(graphname))
                print graphs_sed[-1].GetName(), 'is found.'
                SetGraphStyle(graphs_sed[-1], sed[0], ised)
                mgr.Add(graphs_sed[-1])
            else:
                print 'Deabsorbed SED is unavailable for', os.path.basename(sed[1])
                return 1
        else:
            print os.path.basename(sed[1]), 'is unavailable.'
            return 1
            
    file_out.cd()
    ccmpr = ROOT.TCanvas('ccmpr', 'SED Comparison', 1200, 850)
    ccmpr.cd()
    ccmpr.SetLogx()
    ccmpr.SetGridy()
    mgr.Draw("AP")
    if yrange[0]>=0 and yrange[1]>yrange[0]:
        mgr.GetYaxis().SetRangeUser(yrange[0], yrange[1])
    if graphs_sed[0].GetXaxis().GetTitle()!='':
        mgr.GetXaxis().SetTitle(graphs_sed[0].GetXaxis().GetTitle())
        mgr.GetYaxis().SetTitle(graphs_sed[0].GetYaxis().GetTitle())
    elif len(graphs_sed)>2:
        mgr.GetXaxis().SetTitle(graphs_sed[-2].GetXaxis().GetTitle())
        mgr.GetYaxis().SetTitle(graphs_sed[-2].GetYaxis().GetTitle())
    else:
        mgr.GetXaxis().SetTitle(graphs_sed[-1].GetXaxis().GetTitle())
        mgr.GetYaxis().SetTitle(graphs_sed[-1].GetYaxis().GetTitle())
    mgr.Write()
    ccmpr.BuildLegend()
    for fc in fc_sed:
        fc.Draw("same")
    ccmpr.Write()
    ccmpr.SaveAs('{0}.png'.format(str_output))


@click.command()
@click.option('--seds', multiple=True, type=(str, str), help='Title Path of file')
@click.argument('outname', type=str)
@click.option('--title', type=str, default='Comparison of SED graphs')
@click.option('--absorbed', is_flag=True)
@click.option('--yrange', type=(float, float), default=(0, 0))
def main(seds, outname, title, absorbed, yrange):
    CampareSEDs(seds, outname, title, absorbed, yrange)

if __name__ == '__main__':
    main()
