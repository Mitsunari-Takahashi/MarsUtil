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
from math import log10, log, sqrt, ceil, isnan, pi, factorial, floor
from collections import OrderedDict
from astropy.io import fits
from astropy.time import Time
from astropy.io import ascii
from astropy import units as u
from astropy.table import Table, Column, MaskedColumn
import ROOT
from ROOT import TMath, TGraphAsymmErrors, TFile, TGraph, TCanvas, TF1
import click
import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
#import pickle_utilities
#import pMatplot
import pMETandMJD
from scipy.odr import ODR, Model, Data

mpl.rcParams['text.usetex'] = True
mpl.rcParams['text.latex.preamble'] = [r'\usepackage{amsmath}']
plt.rcParams["font.size"] = 15
#plt.tick_params(labelsize=6)
# pgf_with_rc_fonts = {"pgf.texsystem": "pdflatex"}
# mpl.rcParams.update(pgf_with_rc_fonts)
NMARKER_STYLE = 10

##### VERSION OF THIS MACRO #####
VERSION = 0.1


##### Conversion from MeV to erg ######
MEVtoERG = 1.6021766208E-6


class DataSet:
    def __init__(self, title, name_src):
        self.title = title
        self.name_src = name_src
        self.table = None


class XRT_Data(DataSet):
    def __init__(self, title, name_src):
        DataSet.__init__(self, title, name_src)
        self.tables = {}
        print self.tables


    def load_table(self, name, path_input):
        #self.tables = {}
        self.tables[name] = Table(ascii.read(path_input), masked=True)
#        print self.tables[name]

    def write_table(self, name, path_output):
        if name in self.tables.keys():
            ascii.write(self.tables[name], path_output, format='csv')
        else:
            print self.table, 'does NOT have', name, '!!'
        

    def plot_index_vs_flux(self, ax, iax=0, dchi2_cut=0):
        if dchi2_cut is None:
            dchi2_cut = 0

        time_start = Time(57506, format='mjd')
        time_end = Time(57721, format='mjd')
        ax.set_title(self.title)
        ax.set_xscale('log')
        ax.set_xlabel(r'Flux $\rm{(erg \cdot cm^{-2}\cdot s^{-1})}$ for 0.5-10 keV')
        #ax.set_ylabel(r'Photon spectral index for $>$ 0.5 keV')
        ax.grid()

        #mask_badPWL = np.array([ np.sqrt(max(rchi2_pwl*dof_pwl-rchi2_lp*dof_lp,0))>dchi2_cut for rchi2_pwl, rchi2_lp, dof_pwl, dof_lp in zip(self.tables['PWL']['r_chi'], self.tables['LP']['r_chi'], self.tables['PWL']['NDF'], self.tables['LP']['NDF']) ])
        #mask_badPWL = np.array([TMath.Prob(rchi2_pwl*dof_pwl, dof_pwl)/TMath.Prob(rchi2_lp*dof_lp, dof_lp)<0.68 for rchi2_pwl, rchi2_lp, dof_pwl, dof_lp in zip(self.tables['PWL']['r_chi'], self.tables['LP']['r_chi'], self.tables['PWL']['NDF'], self.tables['LP']['NDF'])])
        mask_badPWL = np.array([TMath.Prob(rchi2_pwl*dof_pwl, dof_pwl)<0.32 for rchi2_pwl, rchi2_lp, dof_pwl, dof_lp in zip(self.tables['PWL']['r_chi'], self.tables['LP']['r_chi'], self.tables['PWL']['NDF'], self.tables['LP']['NDF'])])
        #mask_badPWL = np.array([pwl>lp+dchi2_cut for pwl, lp in zip(self.tables['PWL']['r_chi'], self.tables['LP']['r_chi'])])
        mask_date = np.array([ Time(t+55000, format='mjd')<time_start or Time(t+55000, format='mjd')>time_end for t in self.tables['PWL']['(mjd-55000)'] ]) #Time(self.tables['(mjd-55000)']+55000, format='mjd')>time_start and Time(self.tables['(mjd-55000)']+55000, format='mjd')<time_end
        print mask_date
        
        self.tables['PWL']['index'].mask = mask_badPWL + mask_date
        self.tables['PWL']['ferr_m[0.5-5]'].mask = self.tables['PWL']['index'].mask #mask_badPWL + mask_date
        self.tables['PWL']['ferr_p[0.5-5]'].mask = self.tables['PWL']['index'].mask #mask_badPWL + mask_date
        ax.errorbar(self.tables['PWL']['flux[0.5-5]'], self.tables['PWL']['index'], xerr=(self.tables['PWL']['ferr_m[0.5-5]'], self.tables['PWL']['ferr_p[0.5-5]']), yerr=(self.tables['PWL']['inderr_m'], self.tables['PWL']['inderr_p']), fmt='o', c='k', lw=1, ms=3, alpha=0.8)

        if plot_unhighlighted is True:
            mask_goodPWL = np.array([ 1 - d for d in self.tables['PWL']['index'].mask ])
            #mask_goodPWL = [pwl<=lp+dchi2_cut for pwl, lp in zip(self.tables['PWL']['r_chi'], self.tables['LP']['r_chi'])]
            self.tables['PWL']['index'].mask = mask_goodPWL
            self.tables['PWL']['ferr_m[0.5-5]'].mask = mask_goodPWL
            self.tables['PWL']['ferr_p[0.5-5]'].mask = mask_goodPWL
            ax.errorbar(self.tables['PWL']['flux[0.5-5]'], self.tables['PWL']['index'], xerr=(self.tables['PWL']['ferr_m[0.5-5]'], self.tables['PWL']['ferr_p[0.5-5]']), yerr=(self.tables['PWL']['inderr_m'], self.tables['PWL']['inderr_p']), fmt='.', c='k', lw=1, alpha=0.1)


    def plot_index_vs_flux_logP(self, ax, iax=0, alpha_cut=0.05, plot_unhighlighted=False):
        time_start = Time(57506, format='mjd')
        time_end = Time(57721, format='mjd')
        ax.set_title(self.title)
        ax.set_xscale('linear') #log')
        ax.set_xlabel(r'Differential flux density $\rm{(keV^{-1}\cdot cm^{-2}\cdot s^{-1})}$ at $\rm{E_0} = 1$ keV')
        #ax.set_xlim((1e-2, ax.get_xlim()[1]))
        ax.set_ylim((1.6, 2.4))
        #ax.set_ylabel(r'Photon spectral index at 1 keV $(\alpha)$')
        ax.grid()

        mask_badLP = np.array([ TMath.Prob(rchi*ndf, ndf)<alpha_cut or ndf<1 for rchi, ndf in zip(self.tables['LP']['r_chi'], self.tables['LP']['NDF']) ])
        mask_date = np.array([ Time(t+55000, format='mjd')<time_start or Time(t+55000, format='mjd')>time_end for t in self.tables['PWL']['(mjd-55000)'] ]) #Time(self.tables['(mjd-55000)']+55000, format='mjd')>time_start and Time(self.tables['(mjd-55000)']+55000, format='mjd')<time_end
        print mask_date
        
        self.tables['LP']['alpha'].mask = mask_badLP + mask_date
        self.tables['LP']['a_err_m'].mask = self.tables['LP']['alpha'].mask #mask_badPWL + mask_date
        self.tables['LP']['a_err_p'].mask = self.tables['LP']['alpha'].mask #mask_badPWL + mask_date
        ax.errorbar(self.tables['LP']['norm[1keV](1e-2ph/cm2/s/kev)']*1e-2, self.tables['LP']['alpha'], xerr=(self.tables['LP']['norm_em']*1e-2, self.tables['LP']['norm_ep']*1e-2), yerr=(self.tables['LP']['a_err_m'], self.tables['LP']['a_err_p']), fmt='o', c='k', lw=1, ms=3, alpha=0.8)

        if plot_unhighlighted is True:
            mask_goodLP = np.array([ 1 - d for d in self.tables['LP']['alpha'].mask ])
            self.tables['LP']['alpha'].mask = mask_goodLP
            self.tables['LP']['a_err_m'].mask = mask_goodLP
            self.tables['LP']['a_err_p'].mask = mask_goodLP
            ax.errorbar(self.tables['LP']['norm[1keV](1e-2ph/cm2/s/kev)']*1e-2, self.tables['LP']['alpha'], xerr=(self.tables['LP']['norm_em']*1e-2, self.tables['LP']['norm_ep']*1e-2), yerr=(self.tables['LP']['a_err_m'], self.tables['LP']['a_err_p']), fmt='.', c='k', lw=1, alpha=0.1)
    

    def fit_root_LP_alpha_vs_norm(self):
        grae = TGraphAsymmErrors()
        grae.SetName("grae_xrt_alpha_vs_norm")
        grae.SetTitle("XRT alpha vs. flux")
        can = TCanvas("xrt_LP_alpha_vs_flux", "XRT alpha vs. flux")
        can.cd()
        can.SetLogx()
        #for inight in :
        inight = 0
        for masked, alpha, a_err_m, a_err_p, norm, norm_em, norm_ep in zip(self.tables['LP']['alpha'].mask, self.tables['LP']['alpha'], self.tables['LP']['a_err_m'], self.tables['LP']['a_err_p'], self.tables['LP']['norm[1keV](1e-2ph/cm2/s/kev)']*1e-2, self.tables['LP']['norm_em']*1e-2, self.tables['LP']['norm_ep']*1e-2):
            #grae = TGraphAsymmErrors(range(len(self.tables['LP']['alpha'])), self.tables['LP']['norm[1keV](1e-2ph/cm2/s/kev)', self.tables['LP']['alpha'], )
            print masked, alpha, norm
            if bool(masked) == False:
                print inight
                grae.SetPoint(inight, norm, alpha)
                grae.SetPointError(inight, norm_em, norm_ep, a_err_m, a_err_p)
                inight+=1
        print "Number of data point:", grae.GetN()
        grae.Draw("AP")
        f_const = TF1("f_const", "[0]")
        f_const.SetParameter(0, 2)
        f_pl = TF1("f_pl", "[0]+[1]*TMath::Log10(x)")
        f_pl.SetParameter(0, -8)
        f_pl.SetParameter(1, -1)
        print "===== Constant fit ====="
        grae.Fit(f_const, "+", "goff")
        print "chi^2/dof = {0}/{1} = {2}".format(f_const.GetChisquare(), f_const.GetNDF(), f_const.GetChisquare()/f_const.GetNDF())
        print "===== Powerlaw fit ====="
        grae.Fit(f_pl, "+", "goff")
        print "chi^2/dof = {0}/{1}".format(f_pl.GetChisquare(), f_pl.GetNDF(), f_pl.GetChisquare()/f_pl.GetNDF())
        can.SaveAs("XRT_flux_vs_alpha_fit.png")
                


    def fit_LP_alpha_vs_norm(self):
        def func_constant(P, x):
            return P[0] + 0*x

        def func_powerlaw(P, x):
            return P[0] + P[1]*np.log10(x)

        constant = Model(func_constant)
        powerlaw = Model(func_powerlaw)
        data = Data(self.tables['LP']['norm[1keV](1e-2ph/cm2/s/kev)'], y=self.tables['LP']['alpha'], wd=self.tables['LP']['norm[1keV](1e-2ph/cm2/s/kev)']/(self.tables['LP']['norm_em']+self.tables['LP']['norm_ep']), we=1./(self.tables['LP']['a_err_m']+self.tables['LP']['a_err_p']))
        odr = {}
        output = {}

        print '===== Constant fit ====='
        odr['constant'] = ODR(data, constant, beta0=[-2.2])
        odr['constant'].set_job(fit_type=2) # chi-square
        output['constant'] = odr['constant'].run()
        output['constant'].pprint()

        print '===== Power-law fit ====='
        odr['powerlaw'] = ODR(data, powerlaw, beta0=[1, 8])
        output['powerlaw'] = odr['powerlaw'].run()
        output['powerlaw'].pprint()
                        


class MAGIC_Data(DataSet):
    def __init(self, title, name_src):
        DataSet.__init__(self, title, name_src)
        

    def load_flux(self, path_input):
        self.table = Table(ascii.read(path_input), masked=True)


    def write_table(self, path_output):
        ascii.write(self.table, path_output, format='csv', fill_values=[(ascii.masked, 'N/A')])
        

    def find_nightly_index(self, path_dir_search='.', str_suffix='150-1000GeV_F08_checkBestFit', list_func=['PWL', 'LP', 'EPWL']):
        self.table['FuncBestFit'] = None
        DICT_COL = {'PWL': ['redChi2', 'Chi2', 'norm', 'norm_err', 'dof', 'index', 'index_err'],
                    'LP': ['redChi2', 'Chi2', 'norm', 'norm_err', 'norm_err_pos', 'norm_err_neg', 'dof', 'alpha', 'alpha_err', 'alpha_err_pos', 'alpha_err_neg', 'beta', 'beta_err_pos', 'beta_err_neg'],
                    'EPWL': ['redChi2', 'Chi2', 'norm', 'norm_err', 'dof', 'index', 'index_err', 'cutoff', 'cutoff_err']
                }
        DICT_PARAMETERS = {'PWL': ['norm', 'index'],
                           'LP': ['norm', 'alpha', 'beta'],
                           'EPWL': ['norm', 'index', 'cutoff']
                       }
        for func in list_func:
            for col in DICT_COL[func]:
                self.table['_'.join([func, col])] = np.nan
        self.table['Date'] = None
        self.table['npoints'] = None
        for inight, mjd_cen in enumerate((self.table['mjd_min']+self.table['mjd_max'])/2.):
            time_cen = Time(floor(mjd_cen+0.5), format='mjd')
            time_cen.format = 'iso'
            self.table['Date'][inight] = time_cen
            str_night = time_cen.value[0:4] + time_cen.value[5:7] + time_cen.value[8:10]
            str_filename = 'NightlyFlux_{src}_{night}_{suf}.{fmt}'.format(src=self.name_src, night=str_night, suf=str_suffix, fmt='csv')
            path_input = '/'.join([path_dir_search, str_night, str_filename])

            if not os.path.exists(path_input):
                print path_input, 'does NOT exist!!'
                continue

            with open(path_input, 'r') as f:
                reader = csv.reader(f)
                #header = next(reader)
                for row in reader:
                    str_func = row[0]
                    list_col = ['redChi2', 'Chi2', 'norm', 'norm_err', 'dof']
                    if str_func is 'PWL':
                        list_col += []
                    elif str_func is 'LP':
                        list_col += ['alpha', 'alpha_err', 'beta', 'beta_err']
                    elif str_func is 'EPWL':
                        list_col += ['index', 'index_err', 'cutoff', 'cutoff_err']
                    for icol, col in enumerate(list_col):  #DICT_COL[str_func]):
                        if not col[-7:] in ('err_pos', 'err_neg'):
                            self.table['_'.join([str_func, col])][inight] = row[icol+1]
            min_redChi2 = sys.maxint
            func_min_redChi2 = None
            for func in list_func:
                if self.table['_'.join([func, 'redChi2'])][inight] < min_redChi2:
                    min_redChi2 = self.table['_'.join([func, 'redChi2'])][inight]
                    func_min_redChi2 = func
            self.table['FuncBestFit'][inight] = func_min_redChi2
            #print func_min_redChi2
            if min_redChi2>3:
                print mjd_cen
                print 'Minimum chi^2:', min_redChi2
            if self.table['LP_alpha'][inight]>-1.5:
                print 'LogP alpha = {0} +/- {1}'.format(self.table['LP_alpha'][inight], self.table['LP_alpha_err'][inight])
                print 'LogP beta = {0} +/- {1}'.format(self.table['LP_beta'][inight], self.table['LP_beta_err'][inight])

            # LogP
            for func in ('LP', ):
                str_logname = 'Log_Fold_{src}_forCalcFlux_{func}_150-1000GeV_F08.log'.format(src=self.name_src, func=func)
                path_log = '/'.join([path_dir_search, str_night, str_logname])
                list_par_val = None
                list_par_err = [ None for ipar in range(len(DICT_PARAMETERS[func])) ]
                with open(path_log, 'r') as file_log:
                    for line in file_log:
                        if line[:30] == 'Intrinsic spectral parameters:':
                            list_par_val = [float(str_val) for str_val in line[30:].split(',')]
                            if not len(list_par_val)==len(DICT_PARAMETERS[func]):
                                print 'Number of the parameters in the log file is {0}!! It should be {1} for {2}!!'.format(len(list_par_val), len(DICT_PARAMETERS[func]), func)
                                sys.exit(1)
                        elif line[:27] == 'Uncertainties of parameter ':
                            list_par_err[int(line[28])] = [ float(str_err) for str_err in line[30:].split() ]
                    for ipar, par in enumerate(DICT_PARAMETERS[func]):
                        if not par in ('index', 'alpha'):
                            self.table['_'.join([func, par])][inight] = list_par_val[ipar] 
                            self.table['_'.join([func, par, 'err_pos'])][inight] = list_par_err[ipar][0]
                            self.table['_'.join([func, par, 'err_neg'])][inight] = -list_par_err[ipar][1]
                        else:
                            self.table['_'.join([func, par])][inight] = -list_par_val[ipar] 
                            self.table['_'.join([func, par, 'err_pos'])][inight] = -list_par_err[ipar][1]
                            self.table['_'.join([func, par, 'err_neg'])][inight] = list_par_err[ipar][0]
                print 'LogP norm = {0} + {1} - {2}'.format(self.table['LP_norm'][inight], self.table['LP_norm_err_pos'][inight], self.table['LP_norm_err_neg'][inight])
                print 'LogP alpha = {0} + {1} - {2}'.format(self.table['LP_alpha'][inight], self.table['LP_alpha_err_pos'][inight], self.table['LP_alpha_err_neg'][inight])
                print 'LogP beta = {0} + {1} - {2}'.format(self.table['LP_beta'][inight], self.table['LP_beta_err_pos'][inight], self.table['LP_beta_err_neg'][inight])                        
                            

            str_rootname = 'Output_fold_{src}_forCalcFlux_LP_150-1000GeV_F08.root'.format(src=self.name_src)
            path_root = '/'.join([path_dir_search, str_night, str_rootname])
            if not os.path.exists(path_root):
                print path_root, 'does NOT exist!!'
                continue
            gr_spec = ROOT.TFile(path_root).Get('observed_sed')
            self.table['npoints'][inight] = gr_spec.GetN()
            print 'Number of spectral points:', self.table['npoints'][inight]

        print self.table
        

    def plot_index_vs_flux(self, ax, iax=0, dchi2_cut=0., list_periods=None, plot_unhighlighted=False): #[[57500, 57525], [57525, 57560], [57560, 57590], [57590, 57675], [57675, 57725]]):
        if dchi2_cut is None:
            dchi2_cut = 0
        ax.set_title(self.title)
        ax.set_xscale('log')
        ax.set_xlabel(r'Flux $\rm{(cm^{-2}\cdot s^{-1})}$ for $>$300 GeV')
        #ax.set_ylabel('Photon spectral index for 150-1000 GeV')
        ax.grid()

        mask_badPWL = np.array([ np.sqrt(max(p-l,0))>dchi2_cut or np.sqrt(max(p-e,0))>dchi2_cut for p,l,e in zip(self.table['PWL_Chi2'], self.table['LP_Chi2'], self.table['EPWL_Chi2'])]) 
        #mask_badPWL = np.array([p>l+dchi2_cut or p>e+dchi2_cut for p,l,e in zip(self.table['PWL_redChi2'], self.table['LP_redChi2'], self.table['EPWL_redChi2'])]) 
        if list_periods is not None:
            for period in list_periods:
                print period
                time_start, time_end = period
                mask_outperiod = np.array([ t<time_start or t>time_end for t in self.table['mjd_min'] ])
                self.table['PWL_index'].mask = mask_badPWL+mask_outperiod
                self.table['PWL_index_err'].mask = self.table['PWL_index'].mask
                print self.table['PWL_index'].mask
                ax.errorbar(self.table['flux'], -self.table['PWL_index'], xerr=self.table['flux_err'], yerr=self.table['PWL_index_err'], fmt='o-', lw=0.5, ms=3, alpha=0.8, label='MJD{0}-{1}'.format(period[0], period[1]))
            ax.legend(loc=0)
        else:
            self.table['PWL_index'].mask = mask_badPWL
            self.table['PWL_index_err'].mask = mask_badPWL
            ax.errorbar(self.table['flux'], -self.table['PWL_index'], xerr=self.table['flux_err'], yerr=self.table['PWL_index_err'], fmt='o', c='k', lw=1, ms=3, alpha=0.8)

            if plot_unhighlighted is True:
                mask_goodPWL = 1-mask_badPWL
                self.table['PWL_index'].mask = mask_goodPWL
                self.table['PWL_index_err'].mask = mask_goodPWL
                ax.errorbar(self.table['flux'], -self.table['PWL_index'], xerr=self.table['flux_err'], yerr=self.table['PWL_index_err'], fmt='o', alpha=0.1, c='k', lw=1, ms=3)


    def plot_index_vs_flux_logP(self, ax, iax=0, alpha_cut=0., list_periods=None, plot_unhighlighted=False):
        ax.set_title(self.title)
        ax.set_xscale('linear') #log')
        #ax.set_ylim((1.0, 3.0))
        ax.set_xlabel(r'Flux $\rm{(cm^{-2}\cdot s^{-1})}$ for $>$300 GeV')
        #ax.set_ylabel(r'Photon spectral index at 300 GeV $(\alpha)$')
        ax.grid()

        mask_badLP = np.array([ TMath.Prob(chi2, int(dof+0.5))<alpha_cut if chi2==chi2 and dof==dof and npoi>3 else True for chi2, dof, npoi in zip(self.table['LP_Chi2'], self.table['LP_dof'], self.table['npoints']) ]) 
        print self.table['Date']
        print mask_badLP
        iused = 0
        for night, masking in zip(self.table['Date'], mask_badLP):
            if masking == False:
                print night.value[0:10],',',
                iused+=1
        print iused, 'nights.'
        if list_periods is not None:
            for period in list_periods:
                print period
                time_start, time_end = period
                mask_outperiod = np.array([ t<time_start or t>time_end for t in self.table['mjd_min'] ])
                self.table['LP_alpha'].mask = mask_badLP+mask_outperiod
                self.table['LP_alpha_err'].mask = self.table['LP_alpha'].mask
                self.table['LP_alpha_err_pos'].mask = self.table['LP_alpha'].mask
                self.table['LP_alpha_err_neg'].mask = self.table['LP_alpha'].mask
                print self.table['LP_alpha'].mask
                ax.errorbar(self.table['flux'], self.table['LP_alpha'], xerr=self.table['flux_err'], yerr=(self.table['LP_alpha_err_neg'], self.table['LP_alpha_err_pos']), fmt='o-', lw=0.5, ms=3, alpha=0.8, label='MJD{0}-{1}'.format(period[0], period[1]))
            ax.legend(loc=0)
        else:
            self.table['LP_alpha'].mask = mask_badLP
            self.table['LP_alpha_err'].mask = mask_badLP
            ax.errorbar(self.table['flux'], self.table['LP_alpha'], xerr=self.table['flux_err'], yerr=(self.table['LP_alpha_err_neg'], self.table['LP_alpha_err_pos']), fmt='o', c='k', lw=1, ms=3, alpha=0.8)

            if plot_unhighlighted is True:
                mask_goodLP = np.array([ TMath.Prob(chi2, int(dof+0.5))>=alpha_cut if chi2==chi2 and dof==dof else True for chi2, dof in zip(self.table['LP_Chi2'], self.table['LP_dof']) ]) 
                self.table['LP_alpha'].mask = mask_goodLP
                self.table['LP_alpha_err'].mask = mask_goodLP
                ax.errorbar(self.table['flux'], self.table['LP_alpha'], xerr=self.table['flux_err'], yerr=(self.table['LP_alpha_err_neg'], self.table['LP_alpha_err_pos']), fmt='o', alpha=0.1, c='k', lw=1, ms=3)
        
                

@click.command()
#@click.argument('name', type=str)
#@click.argument('csv', type=str)
@click.option('--title', '-t', type=str, default='MWL light curves', help='Title of the combined plot')
@click.option('--flux', type=str, default=None, help='Path of the MAGIC flux light curve')
@click.option('--fit', type=str, default='.', help='Path of the MAGIC fitting results')
@click.option('--sig', '-s', type=float, default=1, help='Cut value of significance')
@click.option('--logp', '-l', is_flag=True, help='Use log-parabola instead of power-law')
@click.option('--trange', type=(float, float), default=(None,None), help='Offset of time in MJD')
@click.option('--pathout', '-o', type=str, default='./FIG_SpectralIndex_vs_Flux_1ES1959+650_2016')
@click.option('--figform', '-f', type=str, default=('png','pdf'), multiple=True)
def main(title, flux, fit, sig, logp, trange, pathout, figform):
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))#, sharey=True)
    x_data = XRT_Data('XRT', '1ES1959+650')
    x_data.load_table('PWL', '/disk/gamma/cta/store/takhsm/MAGIC/1ES1959+650/2016Whole/NightlyFlute/Swift/LongtermLC_SwiftXRT_PL.csv')
    x_data.load_table('LP', '/disk/gamma/cta/store/takhsm/MAGIC/1ES1959+650/2016Whole/NightlyFlute/Swift/LongtermLC_SwiftXRT_LP.csv')
    if logp is False:
        print 'XRT Power-law'
        x_data.plot_index_vs_flux(ax[1], dchi2_cut=sig)
    else:
        print 'XRT Log-parabola'
        x_data.plot_index_vs_flux_logP(ax[1], alpha_cut=0.05)
        x_data.write_table('LP', '/disk/gamma/cta/store/takhsm/MAGIC/1ES1959+650/2016Whole/NightlyFlute/Swift/TBL_LongtermSpectrum_SwiftXRT_LP.csv')
        x_data.fit_root_LP_alpha_vs_norm()

    m_data = MAGIC_Data('MAGIC', '1ES1959+650')
    m_data.load_flux(flux)
    m_data.find_nightly_index(fit)
    if logp is False:
        print 'MAGIC Power-law'
        m_data.plot_index_vs_flux(ax[0], dchi2_cut=sig)
    else:
        print 'MAGIC Log-parabola'
        m_data.plot_index_vs_flux_logP(ax[0], alpha_cut=0.05)
        m_data.write_table('/disk/gamma/cta/store/takhsm/MAGIC/1ES1959+650/2016Whole/NightlyFlute/TBL_LongtermSpectrum_MAGIC.csv')

    ax[0].set_ylabel(r'Local photon spectral index $\alpha$ at $\rm{E_0} = 300$ GeV')
    ax[1].set_ylabel(r'Local photon spectral index $\alpha$ at $\rm{E_0} = 1$ keV')
    ax[0].grid(axis='x', which='minor', alpha=0.2)
    ax[1].grid(axis='x', which='minor', alpha=0.2)
    ax[0].set_xlim((1e-11, 5e-10))
    ax[1].set_xlim((4e-2, 2e-1))
    #ax[1].set_xlim((2e-2, 2e-1))
    #ax[1].set_ylim(ax[0].get_ylim())
    ax[0].tick_params(axis='x', which='major', labelrotation=30)
    ax[0].tick_params(axis='x', which='minor', labelrotation=30, labelsize='small')
    ax[1].tick_params(axis='x', which='major', labelrotation=30)
    ax[1].tick_params(axis='x', which='minor', labelrotation=30, labelsize='small')
    fig.tight_layout()
    if logp is True:
        pathout += '_logP'
    elif sig is not None:
        pathout += '_dchi2cut{0}sigma'.format(int(sig+0.5))
    for ff in figform:
        fig.savefig('.'.join([pathout, ff]))

if __name__ == '__main__':
    main()
