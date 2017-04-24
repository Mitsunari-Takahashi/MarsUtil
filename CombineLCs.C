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
#include <limits.h>
int CombineLCs(string inputfiles, string strPathFileOut, string strSuffix="", string strPathCsv="", Bool_t bLegend=kFALSE, Bool_t bMakeNightWise=kFALSE, double fluxMargin=1.1, double widthCan=800, double heightCan=500, int mjdStart_makeNightWise=0, int mjdStop_makeNightWise=INT_MAX, string strSuffixNightwise="")
{
  //  TObjArray* objarray = inputfiles.Tokenize(" ");
  //  Int_t nfiles = objarray->GetEntries();
  string strTitleLC = "Light Curve";
  string strTitleUL = "Upper limit";
  string strTitleBC = "Background Curve";
  string strTitleTeff = "Effective time";
  string strTitleLCN = strTitleLC;
  if(strSuffix!="")
    {
      strTitleLC = strTitleLC + " (" + strSuffix + ")";
      strTitleUL = strTitleUL + " (" + strSuffix + ")";
      strTitleBC = strTitleBC + " (" + strSuffix + ")";
      strTitleTeff = strTitleTeff + " (" + strSuffix + ")";
    }
  if(strSuffixNightwise!="")
    {
      strTitleLCN = strTitleLCN + " (" + strSuffixNightwise + ")";
    }
  else
    {
      strTitleLCN = strTitleLC;
    }

  TMultiGraph *mgrLC = new TMultiGraph("mgrLC", strTitleLC.c_str());
  TMultiGraph *mgrUL = new TMultiGraph("mgrUL", strTitleUL.c_str());
  TMultiGraph *mgrBC = new TMultiGraph("mgrBC", strTitleBC.c_str());
  TMultiGraph *mgrTeff = new TMultiGraph("mgrTeff", strTitleTeff.c_str());

  TFile* fin;
  TGraphErrors* greLC;
  TGraphErrors* greUL;
  TGraphErrors *greBC;
  TGraphErrors *greTeff;
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
      greTeff = (TGraphErrors*)fin->FindObjectAny("teffLC");
      // greTeff->SetLineColor(kBlue);
      // greTeff->SetMarkerColor(kBlue);
      // greTeff->SetFillStyle(0);
      // greTeff->SetMarkerSize(0.8);
      mgrTeff->Add(greTeff);

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
  cout << "NDF=" << r->Ndf() << endl;
  if(r->Ndf()>0)
    {
      TF1* fConst = (TF1*)mgrLC->GetFunction("pol0");
      fConst->SetLineColor(kGreen+2);
      fConst->SetLineWidth(1);
    }
  txFit = new TLatex();
  txFit->SetTextSize(0.04);
  txFit->SetTextAlign(13);
  txFit->SetTextColor(kGreen+2);
  ostringstream ossFit;
  ossFit.str("");
  if(r->Ndf()>0)
    {
      ossFit << "#Chi^{2}/ndf = "<< std::setprecision(4) << r->Chi2() << "/" << r->Ndf() << " = " << std::setprecision(4) << r->Chi2()/r->Ndf();
      cout << "Chi^2=" << r->Chi2() << ", Ndf=" << r->Ndf()<< endl;
    }
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
  mgrPlot->SetMaximum(TMath::Max(fluxCrab, mgrPlot->GetYaxis()->GetXmax())*fluxMargin);
  if(r->Ndf()>0)
    fConst->Draw("same");
  txFit->DrawLatexNDC(.6,.5,ossFit.str().c_str());
  lCrab->SetX1(mgrPlot->GetXaxis()->GetXmin());
  lCrab->SetX2(mgrPlot->GetXaxis()->GetXmax());
  lCrab->Draw("same");
  txCrab->Draw("same");
  txCrab->SetName("txCrab");

  TLegend *leg = new TLegend(0.7, 0.6, 0.85, 0.8);
  leg->SetFillColor(kWhite);
  leg->SetName("leg");
  leg->AddEntry(greLC, "Light curve", "p");
  leg->AddEntry(greUL, "Upper limit", "p");
  leg->AddEntry(greBC, "Background curve", "p");
  if(r->Ndf()>0)
    leg->AddEntry(fConst, "Fitting by constant", "l");
  if(bLegend==kTRUE)
    leg->Draw("same");

  TFile *fileOut = new TFile(strPathFileOut.c_str(), "UPDATE");
  fileOut->cd();
  lCrab->Write();
  txCrab->Write();
  mgrLC->Write();
  mgrUL->Write();
  mgrBC->Write();
  mgrTeff->Write();
  mgrPlot->Write();
  leg->Write();
  cLC->Write();
  string strPathPlotOut = strPathFileOut.replace(strPathFileOut.size()-5, 5, ".png");
  cLC->SaveAs(strPathPlotOut.c_str());

  // Make night-wise
  ostringstream ossCsv;
  ossCsv << "#MJDmin:MJDmax:teff:flux_averaged:flux_averaged_err" << endl;
  if(bMakeNightWise==kTRUE)
    {
      const Int_t NLC = mgrLC->GetListOfGraphs()->GetSize();
      TGraphErrors *greTemp;
      TGraphErrors *greTeffTemp;
      // Search min and max of MJD in Light curves
      Int_t MjdMin = INT_MAX;
      Int_t MjdMax = 0;
      for(Int_t iGre=0; iGre<NLC; iGre++)
	{
	  greTemp = (TGraphErrors*)mgrLC->GetListOfGraphs()->At(iGre);
	  MjdMin = TMath::Min(MjdMin, (int)(greTemp->GetXaxis()->GetXmin()+0.5));
	  MjdMax = TMath::Max(MjdMax, (int)(greTemp->GetXaxis()->GetXmax()+0.5));
	}
      cout << MjdMin << " - " << MjdMax << endl;
      const Int_t NNightNominal = MjdMax - MjdMin + 1;
      cout << "Number of array element:" << NNightNominal << endl;
      TGraphErrors *greNightWiseLC = new TGraphErrors();
      greNightWiseLC->SetName("greNightWise");
      //greNightWiseLC->SetTitle(Form("Night-wise %s", mgrLC->GetTitle()));
      greNightWiseLC->SetTitle(strTitleLCN.c_str());
      vector<double> arrVctrFlux[NNightNominal]; // array of Nights > vectors of LCs
      vector<double> arrVctrFluxErr[NNightNominal];
      vector<double> arrVctrTimeStart[NNightNominal]; // In MJD
      vector<double> arrVctrTimeStop[NNightNominal]; // In MJD
      vector<double> arrVctrTeff[NNightNominal];
      for(Int_t kNight=0; kNight<NNightNominal; kNight++)
	{
	  arrVctrFlux[kNight].reserve(10);
	  arrVctrFluxErr[kNight].reserve(10);
	  arrVctrTimeStart[kNight].reserve(10);
	  arrVctrTimeStop[kNight].reserve(10);
	  arrVctrTeff[kNight].reserve(10);
	}
      Double_t xTemp;
      Double_t yTemp;
      Double_t xErrLowTemp;
      Double_t xErrHighTemp;
      Double_t yErrTemp;
      Double_t xTeffTemp;
      Double_t yTeffTemp;
      Int_t nElmn;
      for(Int_t iLC=0; iLC<NLC; iLC++)
	{
	  greTemp = (TGraphErrors*)mgrLC->GetListOfGraphs()->At(iLC);
	  greTeffTemp = (TGraphErrors*)mgrTeff->GetListOfGraphs()->At(iLC);
	  if(greTemp==0x0)
	    continue;
	  for(Int_t iPoint=0; iPoint<greTemp->GetN(); iPoint++)
	    {
	      greTemp->GetPoint(iPoint, xTemp, yTemp);
	      greTeffTemp->GetPoint(iPoint, xTeffTemp, yTeffTemp);
	      if((int)(xTemp+0.5)>=mjdStart_makeNightWise && (int)(xTemp+0.5)<=mjdStop_makeNightWise)
		{
		  yErrTemp = TMath::Max(greTemp->GetErrorYlow(iPoint), greTemp->GetErrorYhigh(iPoint));
		  nElmn = (int)(xTemp+0.5 - MjdMin);
		  arrVctrFlux[nElmn].push_back(yTemp); //
		  arrVctrFluxErr[nElmn].push_back(yErrTemp);
		  xErrLowTemp = greTemp->GetErrorXlow(iPoint);
		  xErrHighTemp = greTemp->GetErrorXhigh(iPoint);
		  arrVctrTimeStart[nElmn].push_back(xTemp - xErrLowTemp);
		  arrVctrTimeStop[nElmn].push_back(xTemp + xErrHighTemp);
		  arrVctrTeff[nElmn].push_back(yTeffTemp);
		}
	    }
	}
      Int_t nCategory;
      Double_t avrg;
      Double_t avrgErr;
      Double_t weightTemp;
      Double_t weightSum;
      Double_t timeMin;
      Double_t timeMax;
      for(Int_t jPoint=0; jPoint<NNightNominal; jPoint++)
	{
	  nCategory = arrVctrFlux[jPoint].size();
	  avrg = 0.;
	  avrgErr = 0.;
	  weightSum = 0.;
	  timeMin=INT_MAX;
	  timeMax=INT_MIN;
	  if(nCategory>0)
	    {
	      cout << "====================" << endl;
	      cout << "Day " << jPoint << endl;
	      double teff_sum=0;
	      for(Int_t jCategory=0; jCategory<nCategory; jCategory++)
		{
		  weightTemp = arrVctrTeff[jPoint][jCategory];//1./TMath::Power(arrVctrFluxErr[jPoint][jCategory], 2);
		  teff_sum = teff_sum + arrVctrTeff[jPoint][jCategory];
		  avrg = avrg + arrVctrFlux[jPoint][jCategory]*weightTemp;
		  avrgErr = avrgErr + TMath::Power(arrVctrTeff[jPoint][jCategory]*arrVctrFluxErr[jPoint][jCategory], 2);
		  cout << "Flux: " << arrVctrFlux[jPoint][jCategory] << "+/-" << arrVctrFluxErr[jPoint][jCategory] << ", Duration: " << arrVctrTimeStop[jPoint][jCategory]-arrVctrTimeStart[jPoint][jCategory] << ", Weight:" << weightTemp << endl;
		  weightSum = weightSum + weightTemp;
		  if(arrVctrTimeStart[jPoint][jCategory]<timeMin)
		    timeMin = arrVctrTimeStart[jPoint][jCategory];
		  if(arrVctrTimeStop[jPoint][jCategory]>timeMax)
		    timeMax = arrVctrTimeStop[jPoint][jCategory];
		}
	      cout << endl;
	      cout << "--------------------" << endl;
	      cout << "Time: " << timeMin << " - " << timeMax << endl;
	      //	      cout << "Effective time: " << arrVctrTeff[jPoint][jCategory] << endl;
	      cout << "Effective time: " << teff_sum << endl;
	      avrg = avrg / weightSum;
	      avrgErr = TMath::Sqrt(avrgErr)/weightSum;//1./TMath::Sqrt(weightSum);
	      cout << "Averaged flux: " << avrg << "+/-" << avrgErr << endl;
	      greNightWiseLC->SetPoint(greNightWiseLC->GetN(), (timeMin+timeMax)/2., avrg);
	      greNightWiseLC->SetPointError(greNightWiseLC->GetN()-1, (timeMax-timeMin)/2., avrgErr);
	      ossCsv << fixed << setprecision(8) << timeMin << "," << fixed << setprecision(8) << timeMax << "," << scientific << teff_sum << "," << scientific << avrg << "," << scientific << avrgErr << endl;
	    }
	}
      fileOut->cd();

      TCanvas *cLCN = new TCanvas("cLCN", "Night-wise Combined Light Curve", widthCan, heightCan);
      cLCN->cd();
      cLCN->SetGrid();
      greNightWiseLC->SetMarkerStyle(5);
      greNightWiseLC->Draw("AP");
      greNightWiseLC->GetXaxis()->SetTitle(greLC->GetXaxis()->GetTitle());
      greNightWiseLC->GetYaxis()->SetTitle(greLC->GetYaxis()->GetTitle());
      greNightWiseLC->Write();
      greNightWiseLC->SetMinimum(0.);
      greNightWiseLC->SetMaximum(TMath::Max(fluxCrab, greNightWiseLC->GetYaxis()->GetXmax())*fluxMargin);
      lCrab->SetX1(greNightWiseLC->GetXaxis()->GetXmin());
      lCrab->SetX2(greNightWiseLC->GetXaxis()->GetXmax());
      lCrab->SetLineWidth(2);
      lCrab->Draw("same");
      txCrab->SetX(0.3*greNightWiseLC->GetXaxis()->GetXmin()+0.7*greNightWiseLC->GetXaxis()->GetXmax());
      txCrab->SetY(1.2*lCrab->GetY2());
      txCrab->Draw("same");
      cLCN->Write();
      delete greNightWise;
      delete cLCN;

      if(strPathCsv!="")
	{
	  ofstream ofs(strPathCsv.c_str());
	  ofs << ossCsv.str();
	}
    }
  delete txFit;
  delete leg;
  delete cLC;
  delete mgrLC;
  delete mgrUL;
  delete mgrBC;
  delete mgrTeff;
  delete fileOut;
}
