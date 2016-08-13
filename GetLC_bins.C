int GetLC_bins(string nameFileIn, double unitSubBin=3.0)
{
  const TFile* fileIn = new TFile(nameFileIn.c_str(), "READ");
  cout << fileIn->GetName() << " is opened." << endl;
  const TGraphErrors *greLC = (TGraphErrors*)fileIn->Get("LightCurve");
  cout << greLC->GetName() << " is found." << endl;
  Double_t x, y, xerr;
  //cout << greLC->GetYaxis()->GetTitle() << endl;
  std::vector<double> vecStart;
  std::vector<double> vecStop;
  Int_t nSubBin = 1;
  for(Int_t i=0; i<greLC->GetN(); i++)
    {
      greLC->GetPoint(i, x, y);
      xerr = greLC->GetErrorX(i);
      cout << xerr << endl;
      cout << "Run-wise LC bin #" << i << " (MJD:" << setprecision(11) << x-xerr << "-" << setprecision(11) << x+xerr << ")"<< endl;
      nSubBin = (int)2*xerr*24.*60./unitSubBin;
      if(nSubBin<1)
	nSubBin++;
      if(2.*xerr*24.*60./nSubBin>=unitSubBin+1 || nSubBin<1)
	nSubBin++;
      cout << "  Sub-run LC bin (" << 2.*xerr*24.*60./nSubBin << " min):" << endl;
      for(Int_t isb=0; isb<nSubBin; isb++)
	{
	  cout << "    " << setprecision(11) << x-xerr+isb*2.*xerr/nSubBin << " - " << setprecision(11) << x-xerr+(isb+1)*2.*xerr/nSubBin << endl;
	  vecStart.push_back(x-xerr+isb*2.*xerr/nSubBin);
	  vecStop.push_back(x-xerr+(isb+1)*2.*xerr/nSubBin);
	}
    }
  cout << "flute.LCbinlowedge:" << endl;
  for(Int_t elVec=0; elVec<vecStart.size(); elVec++)
    cout << setprecision(11) << vecStart[elVec] << ", ";
  cout << endl;
  cout << "flute.LCbinupedge:" << endl;
  for(Int_t elVec=0; elVec<vecStop.size(); elVec++)
    cout << setprecision(11) << vecStop[elVec] << ", ";
  cout << endl;
  delete fileIn;
}
