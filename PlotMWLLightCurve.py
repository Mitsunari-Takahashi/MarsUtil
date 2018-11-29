#!/usr/bin/env python
"""Module for making light curves of multi-wavelength data of 1ES1959+650.
The authour: Mitsunari Takahashi
"""
import sys
import os
import os.path
path_upstairs = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(path_upstairs)
path_moduls_for_fermi = os.path.join(os.path.dirname(__file__), '../Fermi/')
sys.path.append(path_moduls_for_fermi)
import logging
import pickle
import datetime
import numpy as np
import numpy.ma as ma
import math
from math import log10, log, sqrt, ceil, isnan, pi, factorial
from collections import OrderedDict
from astropy.io import fits
from astropy.time import Time
from astropy.io import ascii
from astropy import units as u
from astropy.table import Table, Column, MaskedColumn
import click
import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
#import pickle_utilities
import pMatplot
import pMETandMJD

mpl.rcParams['text.usetex'] = True
mpl.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}']
plt.rcParams["font.size"] = 10
# pgf_with_rc_fonts = {"pgf.texsystem": "pdflatex"}
# mpl.rcParams.update(pgf_with_rc_fonts)
NMARKER_STYLE = 10

##### VERSION OF THIS MACRO #####
VERSION = 0.1


##### Conversion from MeV to erg ######
MEVtoERG = 1.6021766208E-6


class LightCurve:
    def __init__(self, inst='MAGIC', erange='>300 GeV', ylabel=u'Flux [cm^{-2} s^{-1}]', yquant='flux'):
        self.inst = inst
        print self.inst
        self.str_erange = erange
        self.ylabel = ylabel
        self.yquant = yquant
        self.data = None
        self.path_data = None

    
    def load(self, path):
        self.path_data = path
        tb_data = Table(ascii.read(self.path_data), masked=True)
#        tb_data = Table(ascii.read(self.path_data, delimiter=',' if self.path_data[-4]=='.csv' else ' '), masked=True)
        print tb_data
        if self.inst is 'MAGIC':
            tb_data['mjd'] = (tb_data['mjd_min']+tb_data['mjd_max'])/2.
            tb_data['mjd'].unit = u.d
            tb_data['mjd_width'] = -tb_data['mjd_min']+tb_data['mjd_max']
            tb_data['mjd_width'].unit = u.d
            tb_data['flux'].unit = u.cm**-2 * u.s**-1
            tb_data['flux_err'].unit = u.cm**-2 * u.s**-1
            self.emin = 300 * u.GeV
            self.emax = None
            
        elif self.inst is 'LAT':
            if min(tb_data['emin'])==max(tb_data['emin']):
                self.emin = tb_data['emin'] * u.MeV
            if min(tb_data['emax'])==max(tb_data['emax']):
                self.emax = tb_data['emax'] * u.MeV
            tb_data['mjd'] = [pMETandMJD.ConvertMetToMjd(t) for t in (tb_data['tmin']+tb_data['tmax'])/2.]
            tb_data['mjd'].unit = u.d
            tb_data['mjd_width'] = (tb_data['tmax']-tb_data['tmin'])/86400.
            tb_data['mjd_width'].unit = u.d
            tb_data['tmin'].unit = u.s
            tb_data['tmax'].unit = u.s
            tb_data['emin'].unit = u.MeV
            tb_data['emax'].unit = u.MeV
            data_mask = tb_data['flux']<tb_data['flux_err']*2
            tb_data['flux'].mask = data_mask  #tb_data['ts']<9
            tb_data['flux_err'].mask = data_mask #tb_data['ts']<9
            tb_data['flux_ul'].mask = 1 - data_mask #tb_data['ts']>=9
            tb_data['flux'].unit = u.cm**-2 * u.s**-1
            tb_data['flux_err'].unit = u.cm**-2 * u.s**-1
            tb_data['flux_ul'].unit = u.cm**-2 * u.s**-1

        elif self.inst is 'XRT':
            self.emin = 0.5 * u.keV
            self.emax = 5 * u.MeV
            tb_data['mjd'] = tb_data['(mjd-55000)'] + 55000
            tb_data['mjd'].unit = u.d
            tb_data['mjd_width'] = tb_data['(mjd_err)'] * 2
            tb_data['mjd_width'].unit = u.d
            tb_data['flux'] = tb_data['flux[0.5-5]']*1e-12
            tb_data['flux_err_m'] = tb_data['ferr_m[0.5-5]']*1e-12
            tb_data['flux_err_p'] = tb_data['ferr_p[0.5-5]']*1e-12
            tb_data['flux'].unit = u.erg * u.cm**-2 * u.s**-1
            tb_data['flux_err_m'].unit = u.erg * u.cm**-2 * u.s**-1
            tb_data['flux_err_p'].unit = u.erg * u.cm**-2 * u.s**-1

        elif self.inst is 'UVOT':
            tb_data['mjd'] = tb_data['(mjd-55000)'] + 55000
            tb_data['mjd'].unit = u.d
            tb_data['mjd_width'] = tb_data['(mjd_err)'] * 2
            tb_data['mjd_width'].unit = u.d
            tb_data['flux'] = tb_data['deabs_flux[mJy]']
            tb_data['flux_err'] = tb_data['deabs_f_err']
            tb_data['flux'].unit = u.mJy
            tb_data['flux_err'].unit = u.mJy
            
            
        self.data = tb_data
        self.title = '{inst} ({erange})'.format(inst=self.inst, erange=self.str_erange)


    def plot(self, ax, iplot=0, xoffset=0, trange=(None, None)):
        ax.set_title(self.title)
        DICT_COLOR = {'MAGIC': 'r', 'LAT': 'hotpink', 'XRT': 'g', 'UVOT': 'g'}
        DICT_MARKER = {'MAGIC': 'x', 'LAT': 'o', 'XRT': '.', 'UVOT': 'x'}
        if self.inst is not 'XRT':
            ax.errorbar(self.data['mjd']-xoffset, self.data[self.yquant], xerr=self.data['mjd_width']/2., yerr=self.data[self.yquant+'_err'], c=DICT_COLOR[self.inst], ms=3, lw=1, fmt=DICT_MARKER[self.inst])#pMatplot.TPL_MARKER[iplot+1])
        else:
            ax.errorbar(self.data['mjd']-xoffset, self.data[self.yquant], xerr=self.data['mjd_width']/2., yerr=(self.data[self.yquant+'_err_m'],self.data[self.yquant+'_err_p']), c=DICT_COLOR[self.inst], ms=3, lw=1, fmt=DICT_MARKER[self.inst])#pMatplot.TPL_MARKER[iplot+1])
        if self.inst is 'LAT':
            ax.errorbar(self.data['mjd']-xoffset, self.data[self.yquant+'_ul'], xerr=self.data['mjd_width']/2., fmt='v', markerfacecolor='w', markeredgecolor=DICT_COLOR[self.inst], ms=4, lw=1, ecolor=DICT_COLOR[self.inst])
        # if xoffset==0:
        #     ax.set_xlabel('MJD [days]')
        # elif xoffset>0:
        #     ax.set_xlabel('MJD - {0} [days]'.format(xoffset))
        # else:
        #     ax.set_xlabel('MJD + {0} [days]'.format(-xoffset))
        if trange[0] is not None and trange[1] is not None:
            ax.set_xlim(trange)
        ax.set_ylabel(self.ylabel)
        ax.set_ylim((0, ax.get_ylim()[1]))
        ax.grid()
        if self.inst is 'MAGIC':
            ax2 = ax.twinx()
            FLUX_Crab = 1.19882048732478097e-10
            ax2.set_ylim(np.array(ax.get_ylim())/FLUX_Crab)
            ax2.grid(axis='y', ls=':', c='b')
            ax2.set_ylabel('[Crab]')
            ax2.yaxis.label.set_color('b')
            ax2.tick_params(axis='y', colors='b')



class MWL_LightCurves:
    def __init__(self, title='MWL Light Curves', xoffset=0, trange=(None, None)):
        self.title = title
        self.list_curve = []
        self.xoffset = xoffset
        self.trange = trange


    def plot(self, sharex=True):
        nplot = len(self.list_curve)
        self.fig, self.ax = plt.subplots(nplot, 1, figsize=(8, 8), sharex=sharex)
        iplot = 0
        for curve in self.list_curve:
            print curve.title
            curve.plot(self.ax[iplot], iplot=iplot, xoffset=self.xoffset, trange=self.trange)
            iplot+=1            
        if self.xoffset==0:
            self.ax[-1].set_xlabel('MJD [days]')
        elif self.xoffset>0:
            self.ax[-1].set_xlabel('MJD - {0} [days]'.format(self.xoffset))
        else:
            self.ax[-1].set_xlabel('MJD + {0} [days]'.format(-self.xoffset))
        self.fig.tight_layout()
             

    def add(self, curve):
        self.list_curve.append(curve)


    def savefig(self, pathout='./FIG_MWL_LightCurve', figforms=['png', 'pdf']):
        for ff in figforms:
            self.fig.savefig('{0}.{1}'.format(pathout, ff))

                

@click.command()
#@click.argument('name', type=str)
#@click.argument('csv', type=str)
@click.option('--title', '-t', type=str, default='MWL light curves', help='Title of the combined plot')
@click.option('--magic', '-m', type=str, default=None, help='Path of the MAGIC data CSV file')
@click.option('--lat', '-l', type=str, default=None, help='Path of the LAT data CSV file')
@click.option('--xrt', '-x', type=str, default=None, help='Path of the XRT data CSV file')
@click.option('--uvot', '-u', type=str, default=None, help='Path of the UVOT data CSV file')
@click.option('--offset', '-0', type=float, default=0, help='Offset of time in MJD')
@click.option('--trange', type=(float, float), default=(None,None), help='Offset of time in MJD')
@click.option('--pathout', '-o', type=str, default='./FIG_LightCurve_1ES1959+650_MWL_2016')
@click.option('--figform', '-f', type=str, default=('png','pdf'), multiple=True)
def main(title, magic, lat, xrt, uvot, offset, trange, pathout, figform):
    mlc = MWL_LightCurves(title=title, xoffset=offset, trange=trange)
    # MAGIC
    if magic is not None:
        if os.path.isfile(magic):
            curve_magic = LightCurve('MAGIC', erange=u'$> 300\\, \\rm{GeV}$', ylabel=u'$\\rm{[cm^{-2} \cdot s^{-1}]}$')
            curve_magic.load(magic)
            mlc.add(curve_magic)
        else:
            print magic, ' does NOT exist!!'
    # LAT
    if lat is not None:
        if os.path.isfile(lat):
            curve_lat = LightCurve('LAT', erange='$0.3 - 300\\, \\rm{GeV}$', ylabel=u'$\\rm{[cm^{-2} \cdot s^{-1}]}$')
            curve_lat.load(lat)
            mlc.add(curve_lat)
        else:
            print lat, ' does NOT exist!!'

    # XRT
    if xrt is not None:
        if os.path.isfile(xrt):
            curve_xrt = LightCurve('XRT', erange='$0.5 - 5\\, \\rm{keV}$', ylabel=u'$\\rm{[erg \cdot cm^{-2} \cdot s^{-1}]}$')
            curve_xrt.load(xrt)
            mlc.add(curve_xrt)
        else:
            print xrt, ' does NOT exist!!'

    # UVOT
    if uvot is not None:
        if os.path.isfile(uvot):
            curve_uvot = LightCurve('UVOT', erange='W1', ylabel=u'$\\rm{[mJy]}$')
            curve_uvot.load(uvot)
            mlc.add(curve_uvot)
        else:
            printuvot, ' does NOT exist!!'

    mlc.plot(sharex=True)
    mlc.savefig(pathout, figforms=figform)


if __name__ == '__main__':
    main()
