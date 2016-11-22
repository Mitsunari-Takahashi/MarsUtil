/*
This is a ROOT macro for saving Flute products in human-friendly formats
Example: .x SaveFoldPlots("./Status_flute.root", "1ES1959+650", "20151106_300GeV", "pdf")
*/
int SaveFoldPlots(TString nameFileIn, string nameSource, string strSuffix, string strFmt="png")
{
  TFile* fileIn = new TFile(nameFileIn.Data(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  TString nameFileIn2 = nameFileIn.ReplaceAll("Status", "Output");
  TFile* fileIn2 = new TFile(nameFileIn2.Data(), "READ");
  cout << fileIn2->GetName() << " is opened." << endl;

  MStatusArray* sa = (MStatusArray*)fileIn->Get("MStatusDisplay");
  cout << sa->GetName() << " is found." << endl;
  TCanvas* can;
  TCanvas* canClone;
  string aStrPlot[] = {"SED"}; // Please add plot items which you want to save
  string testString;
  string nameFig="";
  TF1 *funcSed;
  TString strFormulaSED;
  TLatex *txSED;
  TParameter<int>* ndof;
  TParameter<float>* chiSq;

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
	      if(strt=="SED")
		{
		  funcSed = (TF1*)fileIn2->Get("SpectralModel");
		  txSED = new TLatex();
		  txSED->SetTextSize(0.03);
		  txSED->SetTextAlign(13);
		  txSED->SetTextColor(kRed);
		  txSED->DrawLatexNDC(.2,.8,funcSed->GetExpFormula());
		  for(Int_t iPar=0; iPar<funcSed->GetNpar(); iPar++)
		    {
		      txSED->DrawLatexNDC(.7,0.1*(8-0.4*(1+iPar)),Form("Par %d: %.2e +/- %.2e", iPar, funcSed->GetParameter(iPar), funcSed->GetParError(iPar)));
		    }
		  //strFormulaSED = (TString)funcSed->GetExpFormula();
		  ndof = (TParameter<int>*)fileIn2->Get("ndof");
		  chiSq = (TParameter<float>*)fileIn2->Get("chisquare");
		  txSED->DrawLatexNDC(.2,.4,Form("Chi^2/ndof=%.2f/%d=%.2f", chiSq->GetVal(), ndof->GetVal(), chiSq->GetVal()/ndof->GetVal()));
		}
	      nameFig = Form("%s_Fold_%s%s.%s", testString.c_str(), nameSource.c_str(), strSuffix.c_str(), strFmt.c_str());
	      can->SaveAs(nameFig.c_str());
	      if(strt=="SED")
		delete txSED;
	    }
	}
    }
  delete fileIn;
  delete fileIn2;
}
