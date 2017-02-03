int GetLC_values(string nameFileIn, string nameGraph="LightCurve", string pathFile="")
{
  TFile* fileIn = new TFile(nameFileIn.c_str(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  TGraphErrors *greLC = (TGraphErrors*)fileIn->Get(nameGraph.c_str());
  cout << greLC->GetName() << " is found." << endl;
  Double_t x, y, yerr;
  cout << greLC->GetYaxis()->GetTitle() << endl;
  double unitFlux=1e-11;
  ostringstream oss;
  for(Int_t i=0; i<greLC->GetN(); i++)
    {
      greLC->GetPoint(i, x, y);
      oss << "LC bin #" << i << " (MJD:" << std::fixed << ios::setprecision(5) << x << "+/-" << ios::setprecision(5) << greLC->GetErrorX(i) << ") : " << "(" << ios::setprecision(3) << y/unitFlux << " +/- " << ios::setprecision(3) << greLC->GetErrorY(i)/unitFlux << ")x" << scientific << unitFlux << " cm^{-2} s^{-1}" << endl;
    }
  cout << oss.str();
  if(pathFile!="")
    {
      ofstream ofs(pathFile.c_str());
      ofs << oss.str();
    }
  delete fileIn;
}
