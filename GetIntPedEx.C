/*****************************************
Get the pedestal DC values (mean and rms).
GetIntPedEx("ssignal1_M1.root ssignal2_M1.root ssignal3_M1.root ...", "Path of output rc file", "Suffix for png file")
This method creates a combined plot of your files and outputs a rc file for star.
*****************************************/
#include "Riostream.h"
#include <iostream>
#include <fstream>
#include <TCanvas.h>
#include <TFile.h>
#include <TGraphErrors.h>
#include <TMultiGraph.h>
#include <TH1D.h>
int GetIntPedEx(string inputfiles = "", string strPathRC="", string strSuffix="")
{
  TFile* fileList = new TFile(inputfiles.c_str(), "READ");
  cout << fileList->GetName() << " is opened." << endl;
  TTree *trList = (TTree*)fileList->Get("ListSsignal");
  cout << trList->GetName() << " is found." << endl;
  TString* strPathSsignal;
  trList->SetBranchAddress("PathListSsignal", &strPathSsignal);

  TFile* fileIn;//[nFile];
  MStatusArray* sa;//[nFile];
  string nameFileIn;//[nFile];
  TCanvas* can;//[nFile];
  TPad* padMean;//[nFile];
  TPad* padRms;//[nFile];
  TGraphErrors* greMean;//[nFile];
  TGraphErrors* greRms;//[nFile];
  TMultiGraph *mgrMean = new TMultiGraph("mgrMean", "IntPedExtr_Mean");
  TMultiGraph *mgrRms = new TMultiGraph("mgrRMs", "IntPedExtr_RMS");
  for(Int_t iFile=0; iFile<trList->GetEntries(); iFile++)
    {
      trList->GetEntry(iFile);
      fileIn = new TFile(strPathSsignal->Data(), "READ");
      cout << fileIn->GetName() << " is opened." << endl;
      sa = (MStatusArray*)fileIn->Get("MStatusDisplay");
      cout << sa->GetName() << " is found." << endl;
      Int_t iAt=0; 
      Bool_t bFound=false;
      while(bFound==false && iAt<sa->GetEntries())
      	{
      	  can = (TCanvas*)sa->At(iAt);
      	  string strt = can->GetTitle();
      	  if(strt=="IntPedEx")
      	    {
      	      bFound = true;
      	      can->SetName(Form("%s%d", can->GetName(), iFile));
      	      can->Draw();
      	      padMean = (TPad*)can->cd(1);
      	      padRms = (TPad*)can->cd(2);
      	      greMean = (TGraphErrors*)padMean->FindObject("");
      	      greMean->SetName(Form("greMean%d", iFile));
      	      greRms = (TGraphErrors*)padRms->FindObject("");
      	      greRms->SetName(Form("greRms%d", iFile));
      	    }
      	  iAt++;
      	}
      mgrMean->Add(greMean);
      mgrRms->Add(greRms);
      fileIn->Close();
    }
  TCanvas *cAll = new TCanvas("cAll", "IntPedEx_all", 1200, 600);
  cAll->Divide(1,2);
  cAll->cd(1);
  mgrMean->Draw("AP");
  mgrMean->Fit("pol0");
  cout << "Fitted Mean = " << mgrMean->GetFunction("pol0")->GetParameter(0) << endl;
  cAll->cd(2);
  mgrRms->Draw("AP");
  mgrRms->Fit("pol0");
  cout << "Fitted RMS = " << mgrRms->GetFunction("pol0")->GetParameter(0) << endl;
  cAll->SaveAs(Form("IntPedEx_%s.png", strSuffix.c_str()));
  cout << strPathRC.c_str() << endl;
  ofstream ofs;
  ofs.open(strPathRC.c_str(), std::ios::out | std::ios::trunc);
  if(ofs.fail())
    cout << "Cannot open." << endl;
   ofs << "MJStar.MAddNoise.NewNoiseMean: " << mgrMean->GetFunction("pol0")->GetParameter(0) << endl;
  ofs << "MJStar.MAddNoise.NewNoiseRMS: " << mgrRms->GetFunction("pol0")->GetParameter(0) << endl;
  ofs.close();
  //  fclose( fp );
  delete fileList;
  delete cAll;
}
