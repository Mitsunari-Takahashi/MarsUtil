int GetLC_values(string nameFileIn)
{
  TFile* fileIn = new TFile(nameFileIn.c_str(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  TGraphErrors *greLC = (TGraphErrors*)fileIn->Get("LightCurve");
  cout << greLC->GetName() << " is found." << endl;
  Double_t x, y, yerr;
  cout << greLC->GetYaxis()->GetTitle() << endl;
  double unitFlux=1e-11;
  for(Int_t i=0; i<greLC->GetN(); i++)
    {
      greLC->GetPoint(i, x, y);
      cout << "LC bin #" << i << " (MJD:" << std::fixed << ios::setprecision(5) << x << "+/-" << ios::setprecision(5) << greLC->GetErrorX(i) << ") : " << "(" << ios::setprecision(3) << y/unitFlux << " +/- " << ios::setprecision(3) << greLC->GetErrorY(i)/unitFlux << ")x" << scientific << unitFlux << " cm^{-2} s^{-1}" << endl;
    }
  delete fileIn;
}
