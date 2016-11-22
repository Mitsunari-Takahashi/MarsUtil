#!/usr/bin/env python

import ROOT
from ROOT import TMultiGraph
from ROOT import TF1
import click
from Fermi.pLsList import ls_list
ROOT.gROOT.SetBatch()


@click.command()
@click.argument('listfiles', type=str)
@click.argument('output', type=str)
def main(listfiles, output):
    """Make a csv table of Chi^2 and NDF from your Light curves."""
    li_lc = ls_list(listfiles)
    path_output = open(output, 'w')
    path_output.write("""MJD/I,Constant/F,ConstantError/F,ChiSq/F,NDF/I
""")
    for line in li_lc:
        print '---------------------'
        print line
        file_lc = ROOT.TFile(line, 'READ')
        file_lc.cd()
        mgrlc = file_lc.Get('mgrLC')
        print mgrlc.GetName(), 'is found.'
        grinitial = mgrlc.GetListOfGraphs().At(0)
        print grinitial.GetName(), 'is found.'
        fconst = mgrlc.GetListOfFunctions().At(0)
        print fconst.GetName(), 'is found.'
        mjd = int(grinitial.GetXaxis().GetXmin()+0.5)
        path_output.write("""{0},{1},{2},{3},{4}
""".format(mjd, fconst.GetParameter(0), fconst.GetParError(0), fconst.GetChisquare(), fconst.GetNDF()))
    path_output.close()

if __name__ == '__main__':
    main()
