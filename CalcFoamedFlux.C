/*
This is a ROOT macro for calculating flux from a Foam file.
Example: .x CalcFoamedFlux("./Foam.root")
*/
#include <iostream>
#include <TFile.h>
#include <TGraphErrors.h>

int CalcFoamedFlux(string pathFileIn, double eThreshold, string pathAssum, double mjd=0.0, string pathFile="")
{
  TFile* fileIn = new TFile(pathFileIn.c_str(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  
  /* Collection Area */
  MHMcCollectionArea* ctnAcoll = (MHMcCollectionArea*)fileIn->Get("collareaVsEest");
  cout << ctnAcoll->GetName() << " is found." << endl;
  TH2D* htgAcoll = (TH2D*)ctnAcoll->GetHistCoarse();
  cout << htgAcoll->GetName() << " is found." << endl;
  Double_t acoll=0;
  Double_t acoll_err=0;
  Int_t nBinThre = FindEnergyBin(htgAcoll, eThreshold);
  //acoll = htgAcoll->IntegralAndError(nBinThre, htgAcoll->GetNbinsX(), 1, htgAcoll->GetNbinsY(), acoll_err);
  TFile *fileAssum = new TFile(pathAssum.c_str(), "READ");
  TF1 *fcAssum = (TF1*)fileAssum->Get("abs_spec");
  //TF1 *fcAssum = (TF1*)fileAssum->Get("Spectrum");
  //  TF1* fc_intrinsic = new TF1("intrinsic_spectrum", pathAssum.c_str(), 1, 1000000);
  //  acoll = ctnAcoll->GetTotalAeffInCoarseBinRange(fc_intrinsic, nBinThre, htgAcoll->GetNbinsX(), &acoll_err);
  acoll = ctnAcoll->GetTotalAeffInCoarseBinRange(fcAssum, nBinThre, htgAcoll->GetNbinsX(), &acoll_err);
  cout << "Collection Area = " << acoll << " +/- " << acoll_err << endl;
  //  delete fc_intrinsic;
  delete fileAssum;

  /* Effective Time */
  TH2D *htgTeff = (TH2D*)fileIn->Get("TotalEffTimevsAzZd");
  Double_t teff;
  Double_t teff_err;
  teff = htgTeff->IntegralAndError(1, htgTeff->GetNbinsX(), 1, htgTeff->GetNbinsY(), teff_err);
  cout << "Effective time = " << teff << " +/- " << teff_err << endl;

  /* Total Non */
  TH1D *htgNon = (TH1D*)fileIn->Get("total_non");
  Double_t non;
  non = htgNon->Integral(nBinThre, htgNon->GetNbinsX());
  cout << "Number of ON events = " << non << endl;

  /* Total Nbckg */
  TH1D *htgBckg = (TH1D*)fileIn->Get("total_bckg");
  Double_t bckg;
  Double_t bckg_err;
  bckg = htgBckg->IntegralAndError(nBinThre, htgBckg->GetNbinsX(), bckg_err);
  cout << "Number of background events = " << bckg << " +/- " << bckg_err << endl;

  /* Total Nbckg */
  TH1D *htgExcess = (TH1D*)fileIn->Get("total_nexcess");
  Double_t excess;
  Double_t excess_err;
  excess = htgExcess->IntegralAndError(nBinThre, htgExcess->GetNbinsX(), excess_err);
  cout << "Number of excess events = " << excess << " +/- " << excess_err << endl;

  Double_t flux = (non - bckg) / acoll / teff /100./100.;
  Double_t flux_err = sqrt( (non+bckg_err*bckg_err)/(acoll*acoll) + pow(acoll_err*(non-bckg)/(acoll*acoll) ,2) ) / teff /100./100.;
  cout << "############################" << endl;
  cout << "Flux = " << flux << " +/- " << flux_err << endl;
  cout << "############################" << endl;

  if(mjd>0)
    {
      ostringstream oss;
      cout << pathFile.c_str() << endl;
      oss << "#MJD/I:flux/F:fluxErr/F" << endl;
      oss << mjd << "," << flux << "," << flux_err << endl;
      cout << oss.str();
      if(pathFile.c_str()!="")
	{
	  ofstream ofs(pathFile.c_str());
	  ofs << oss.str();
	}
    }

  delete fileIn;
}


int FindEnergyBin(TH2* htg, double enr)
{
  Double_t ebinedge = 0;
  Int_t nbin_tgt = 0;
  Double_t ebinratiolog = 100.;
  Double_t ebinratiolog_temp = 100.;
  cout << htg->GetNbinsX() << endl;
  for(Int_t ibin=1; ibin<htg->GetNbinsX(); ibin++)
    {
      ebinedge = htg->GetXaxis()->GetBinLowEdge(ibin);
      ebinratiolog_temp = TMath::Log10(enr) - TMath::Log10(ebinedge);
      //cout << ibin << " : " << TMath::Abs(ebinratiolog) << ", " << TMath::Abs(ebinratiolog_temp) << endl;
      if(TMath::Abs(ebinratiolog)>TMath::Abs(ebinratiolog_temp))
	{
	  ebinratiolog = ebinratiolog_temp;
	  nbin_tgt = ibin;
	}
    }
  cout << "Closet bin: " << nbin_tgt << ", Deviation factor: " << TMath::Power(10, ebinratiolog) << endl;
  return nbin_tgt;
}
