#include <iostream>

#include <TArrow.h>
#include <TCanvas.h>
#include <TF1.h>
#include <TFile.h>
#include <TGraphErrors.h>
#include <TMultiGraph.h>
#include <TH1D.h>
#include <TH1I.h>
#include <TObjArray.h>
#include <TObjString.h>
int CombineLCs(string inputfiles, string strPathFileOut, string strSuffix="", Bool_t bLegend=kFALSE, double widthCan=600, double heightCan=400)
{
  //  TObjArray* objarray = inputfiles.Tokenize(" ");
  //  Int_t nfiles = objarray->GetEntries();
  string strTitleLC = "Light Curve";
  string strTitleUL = "Upper limit";
  string strTitleBC = "Background Curve";
  if(strSuffix!="")
    {
      strTitleLC = strTitleLC + " (" + strSuffix + ")";
      strTitleUL = strTitleUL + " (" + strSuffix + ")";
      strTitleBC = strTitleBC + " (" + strSuffix + ")";
    }
  TMultiGraph *mgrLC = new TMultiGraph("mgrLC", strTitleLC.c_str());
  TMultiGraph *mgrUL = new TMultiGraph("mgrUL", strTitleUL.c_str());
  TMultiGraph *mgrBC = new TMultiGraph("mgrBC", strTitleBC.c_str());

  TFile* fin;
  TGraphErrors* greLC;
  TGraphErrors* greUL;
  TGraphErrors *greBC;
  std::ifstream ifs(inputfiles.c_str());
  char str[256];
  TString strStatus;
  if (ifs.fail())
    {
      std::cerr << "Failed." << std::endl;
      return -1;
    }
  
  while (ifs.getline(str, 256 - 1))
    {
      std::cout << "[" << str << "]" << std::endl;
      //      TObjString* ostr = (TObjString*) objarray->At(ifile);
      //      cout << "Opened " << ostr->GetString().Data() << endl;
      //      fin = new TFile(ostr->GetString().Data());

      fin = new TFile(str, "READ");
      cout << fin->GetName() << endl;
      greLC = (TGraphErrors*)fin->FindObjectAny("LightCurve");
      cout << greLC->GetN() << " points" << endl;
      greLC->SetMarkerStyle(7);
      greLC->SetFillStyle(0);
      mgrLC->Add(greLC);
      greUL = (TGraphErrors*)fin->FindObjectAny("UpperLimLC");
      greUL->SetLineColor(kBlue);
      greUL->SetMarkerColor(kBlue);
      greUL->SetFillStyle(0);
      greUL->SetMarkerSize(0.8);
      if(greUL->GetN()>0)
	{
	  mgrUL->Add(greUL);
	}
      greBC = (TGraphErrors*)fin->FindObjectAny("BackgroundCurve");
      greBC->SetMarkerColor(kGray+1);
      greBC->SetMarkerStyle(5);
      greBC->SetFillStyle(0);
      greBC->SetLineColor(kGray+1);
      greBC->SetFillColor(kGray+1);
      mgrBC->Add(greBC);

      delete fin;
      strStatus = str;
      strStatus = strStatus.ReplaceAll("Output", "Status");
    }

  TFile *fileStatus = new TFile(strStatus.Data(), "READ");
  cout << fileStatus->GetName() << " is opened." << endl;
  MStatusArray* sa = (MStatusArray*)fileStatus->Get("MStatusDisplay");
  cout << sa->GetName() << " is found." << endl;
  TCanvas *can;
  TLine *lCrab;
  TText *txCrab;
  Double_t fluxCrab=-999;
  string nameFig="";
  for(Int_t iAt=0; iAt<sa->GetEntries(); iAt++)
    {
      can = (TCanvas*)sa->At(iAt);
      cout << can->GetName() << " is found." << endl;
      string strt = can->GetTitle();
      if(strt=="Light Curve")
	{
	  can->Draw();
	  lCrab = (TLine*)can->GetListOfPrimitives()->At(3)->Clone();
	  txCrab = (TText*)can->GetListOfPrimitives()->At(4)->Clone();
	  fluxCrab = lCrab->GetY1();
	  cout << "Crab flux: " << fluxCrab << endl;
	}
    }

  TFitResultPtr r=mgrLC->Fit("pol0","S");
  TF1* fConst = (TF1*)mgrLC->GetFunction("pol0");
  fConst->SetLineColor(kGreen+2);
  fConst->SetLineWidth(1);
  txFit = new TLatex();
  txFit->SetTextSize(0.04);
  txFit->SetTextAlign(13);
  txFit->SetTextColor(kGreen+2);
  ostringstream ossFit;
  ossFit.str("");
  ossFit << "#Chi^{2}/ndf = "<< std::setprecision(4) << r->Chi2() << "/" << r->Ndf() << " = " << std::setprecision(4) << r->Chi2()/r->Ndf();
  cout << "Chi^2=" << r->Chi2() << ", Ndf=" << r->Ndf()<< endl;

  TMultiGraph *mgrPlot = new TMultiGraph("mgrPlot", strTitleLC.c_str());
  mgrPlot->Add(mgrBC);
  mgrPlot->Add(mgrUL);
  mgrPlot->Add(mgrLC);
  
  TCanvas *cLC = new TCanvas("cLC", "Combined Light Curve", widthCan, heightCan);
  cLC->cd();
  cLC->SetGrid();
  mgrPlot->Draw("AP");
  mgrPlot->GetXaxis()->SetTitle(greLC->GetXaxis()->GetTitle());
  mgrPlot->GetYaxis()->SetTitle(greLC->GetYaxis()->GetTitle());
  mgrPlot->SetMinimum(0.);
  mgrPlot->SetMaximum(TMath::Max(fluxCrab*1.1, mgrPlot->GetYaxis()->GetXmax()));
  fConst->Draw("same");
  txFit->DrawLatexNDC(.6,.5,ossFit.str().c_str());
  lCrab->SetX1(mgrPlot->GetXaxis()->GetXmin());
  lCrab->SetX2(mgrPlot->GetXaxis()->GetXmax());
  lCrab->Draw("same");
  txCrab->Draw("same");

  TLegend *leg = new TLegend(0.7, 0.6, 0.85, 0.8);
  leg->SetFillColor(kWhite);
  leg->SetName("leg");
  leg->AddEntry(greLC, "Light curve", "p");
  leg->AddEntry(greUL, "Upper limit", "p");
  leg->AddEntry(greBC, "Background curve", "p");
  leg->AddEntry(fConst, "Fitting by constant", "l");
  if(bLegend==kTRUE)
    leg->Draw("same");

  TFile *fileOut = new TFile(strPathFileOut.c_str(), "UPDATE");
  fileOut->cd();
  mgrLC->Write();
  mgrUL->Write();
  mgrBC->Write();
  mgrPlot->Write();
  leg->Write();
  cLC->Write();
  string strPathPlotOut = strPathFileOut.replace(strPathFileOut.size()-5, 5, ".png");
  cLC->SaveAs(strPathPlotOut.c_str());
  delete txFit;
  delete leg;
  delete cLC;
  delete fileOut;
}
