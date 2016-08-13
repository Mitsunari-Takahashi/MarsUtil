int SaveTh2OnAndOffCan(string nameFileIn, string nameSource, string strSuffix)
{
  TFile* fileIn = new TFile(nameFileIn.c_str(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  TCanvas* cTh2 = (TCanvas*)fileIn->Get("th2OnAndOffCan");
  cout << cTh2->GetName() << " is found." << endl;
  cTh2->Draw();
  cTh2->SaveAs(Form("th2OnAndOffCan_%s_%s.png", nameSource.c_str(), strSuffix.c_str()));
  delete fileIn;
}
