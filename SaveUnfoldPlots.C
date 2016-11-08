/*
This is a ROOT macro for saving CombUnfold.C products in human-friendly formats
Example: .x SaveUnfoldPlots("./Unfolding_Output_combunfold_20160613_PL_Bertero_0.root", "1ES1959+650", "20160613_300GeV")
*/
int SaveUnfoldPlots(TString nameFileIn, string nameSource, string strSuffix, string strFmt="png")
{
  TFile* fileIn = new TFile(nameFileIn.Data(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  MStatusArray* sa = (MStatusArray*)fileIn->Get("MStatusDisplay");
  cout << sa->GetName() << " is found." << endl;
  TCanvas* can;
  TCanvas* canClone;
  string aStrPlot[] = {"Correlated Fit"}; // Please add plot items which you want to save
  string testString;
  string nameFig="";
  for(Int_t iAt=0; iAt<sa->GetEntries(); iAt++)
    {
      can = (TCanvas*)sa->At(iAt);
      cout << can->GetName() << " is found." << endl;
      for(Int_t iPlot=0; iPlot<sizeof(aStrPlot)/sizeof(aStrPlot[0]); iPlot++)
	{
	  string strt = can->GetTitle();
	  cout << strt << endl;
	  if(strt==aStrPlot[iPlot])
	    {
	      testString = aStrPlot[iPlot];
	      for(size_t c = testString.find_first_of(" "); c != string::npos; c = c = testString.find_first_of(" ")){
		testString.erase(c,1);
	      }
	      can->Draw();
	      nameFig = Form("%s_%s_%s.%s", testString.c_str(), nameSource.c_str(), strSuffix.c_str(), strFmt.c_str());
	      can->SaveAs(nameFig.c_str());
	    }
	}
    }
  delete fileIn;
}
