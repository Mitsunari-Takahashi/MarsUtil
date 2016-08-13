/*
This is a ROOT macro for saving Flute products in human-friendly formats
Example: .x SaveFlutePlots("./Status_flute.root", "./Output_flute.root", "1ES1959+650", "20151106_300GeV")
*/
int SaveFlutePlots(TString nameFileIn, string nameSource, string strSuffix, string strFmt="png", double fluxMaxInCrab=2)
{
  TFile* fileIn = new TFile(nameFileIn.Data(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  TString nameFileIn2 = nameFileIn.ReplaceAll("Status", "Output");
  TFile* fileIn2 = new TFile(nameFileIn2.Data(), "READ");
  cout << fileIn2->GetName() << " is opened." << endl;
  MStatusArray* sa = (MStatusArray*)fileIn->Get("MStatusDisplay");
  cout << sa->GetName() << " is found." << endl;
  //644,454
  TCanvas* can;
  TCanvas* canClone;
  string aStrPlot[] = {"SED", "Light Curve"}; // Please add plot items which you want to save
  string testString;
  //  TMultiGraph *mgrLC = new TMultiGraph("mgrLC", "Light Curve");
  TLine *lCrab;
  TLine *lCrabClone;
  TText *txCrab;
  TFrame *frame;
  TLatex *txFit;
  Double_t fluxCrab=-999;
  string nameFig="";
  for(Int_t iAt=0; iAt<sa->GetEntries(); iAt++)
    {
      can = (TCanvas*)sa->At(iAt);
      cout << can->GetName() << " is found." << endl;
      for(Int_t iPlot=0; iPlot<sizeof(aStrPlot)/sizeof(aStrPlot[0]); iPlot++)
	{
	  string strt = can->GetTitle();
	  if(strt==aStrPlot[iPlot])
	    {
	      testString = aStrPlot[iPlot];
	      for(size_t c = testString.find_first_of(" "); c != string::npos; c = c = testString.find_first_of(" ")){
		testString.erase(c,1);
	      }
	      can->Draw();
	      nameFig = Form("%s_%s_%s.%s", testString.c_str(), nameSource.c_str(), strSuffix.c_str(), strFmt.c_str());
	      if(strt=="Light Curve")
		{
		  can->cd();
		  canClone = (TCanvas*)can->Clone(testString.c_str());
		  canClone->Draw();
		  frame = (TFrame*)canClone->GetListOfPrimitives()->At(0);
		  double x1Frame = frame->GetX1();
		  double x2Frame = frame->GetX2();
		  double y1Frame = frame->GetY1();
		  double y2Frame = frame->GetY2();
		  lCrab = (TLine*)canClone->GetListOfPrimitives()->At(3)->Clone();
		  txCrab = (TText*)canClone->GetListOfPrimitives()->At(4)->Clone();
		  fluxCrab = lCrab->GetY1();
		  cout << "Crab flux: " << fluxCrab << endl;
		  canClone->Clear();
		  canClone->cd();
		  TH1F* hFrame = canClone->DrawFrame(x1Frame, 0.0, x2Frame, TMath::Max(y2Frame*1.1, fluxCrab*fluxMaxInCrab));
		  TGraphErrors *greLC = (TGraphErrors*)fileIn2->Get("LightCurve");
		  cout << greLC->GetName() << " is found." << endl;
		  greLC->Draw("P same");
		  if(greLC->GetN()>1)
		    {
		      TFitResultPtr r=greLC->Fit("pol0","S");
		      TF1* fConst = (TF1*)greLC->GetFunction("pol0");
		      fConst->SetLineColor(kGreen+3);
		      fConst->SetLineWidth(1);
		      txFit = new TLatex();
		      txFit->SetTextSize(0.04);
		      txFit->SetTextAlign(13);
		      txFit->SetTextColor(kGreen+3);
		      ostringstream ossFit;
		      ossFit.str("");
		      ossFit << "#Chi^{2}/ndf = "<< std::setprecision(4) << r->Chi2() << "/" << r->Ndf() << " = " << std::setprecision(4) << r->Chi2()/r->Ndf();
		      txFit->DrawLatexNDC(.6,.9,ossFit.str().c_str());
		      cout << "Chi^2=" << r->Chi2() << ", Ndf=" << r->Ndf()<< endl;
		    }
		  canClone->RedrawAxis();
		  TGraphErrors *greBC = (TGraphErrors*)fileIn2->Get("BackgroundCurve");
		  cout << greBC->GetName() << " is found." << endl;
		  greBC->SetMarkerColor(kGray+1);
		  greBC->SetLineColor(kGray+1);
		  greBC->Draw("P same");
		  TGraph *grUL = (TGraph*)fileIn2->Get("UpperLimLC");
		  cout << grUL->GetName() << " is found." << endl;		  
		  if(grUL->GetN()>0)
		    grUL->Draw("P same");
		  hFrame->GetXaxis()->SetTitle(greLC->GetXaxis()->GetTitle());
		  hFrame->GetYaxis()->SetTitle(greLC->GetYaxis()->GetTitle());
		  if(fluxCrab>0)
		    {
		      cout << "Crab flux: " << fluxCrab << endl;
		      lCrab->Draw("same");
		      txCrab->Draw("same");
		    }
		  else
		    {
		      cout << "No Crab flux indicator." << endl;
		    }
		  canClone->SaveAs(nameFig.c_str());
		  if(greLC->GetN()>1)
		    delete txFit;
		}
	      else
		can->SaveAs(nameFig.c_str());
	    }
	}
    }
  delete fileIn;
  delete fileIn2;
}
