int GetLC_values(string nameFileIn)
{
  TFile* fileIn = new TFile(nameFileIn.c_str(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  TGraphErrors *greLC = (TGraphErrors*)fileIn->Get("LightCurve");
  cout << greLC->GetName() << " is found." << endl;
  Double_t x, y, yerr;
  cout << greLC->GetYaxis()->GetTitle() << endl;
  for(Int_t i=0; i<greLC->GetN(); i++)
    {
      greLC->GetPoint(i, x, y);
      cout << "LC bin #" << i << " (MJD:" << x << ")"<< endl;
      cout << y << " +/- " << greLC->GetErrorY(i) << endl;
    }
  delete fileIn;
}
