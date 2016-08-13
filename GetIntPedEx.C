int GetIntPedEx(TString inputfiles = "", string strPathRC="", string strSuffix="")
{
  TObjArray* objarray = inputfiles.Tokenize(" ");
  const Int_t nFile = objarray->GetEntries();
  TObjString* ostr;
  TFile* fileIn[nFile];
  MStatusArray* sa[nFile];
  string nameFileIn[nFile];
  TCanvas* can[nFile];
  TPad* padMean[nFile];
  TPad* padRms[nFile];
  TGraphErrors* greMean[nFile];
  TGraphErrors* greRms[nFile];
  TMultiGraph *mgrMean = new TMultiGraph("mgrMean", "IntPedExtr_Mean");
  TMultiGraph *mgrRms = new TMultiGraph("mgrRMs", "IntPedExtr_RMS");
  for(Int_t iFile=0; iFile<nFile; iFile++)
    {
      ostr = (TObjString*) objarray->At(iFile);
      fileIn[iFile] = new TFile(ostr->GetString().Data());
      cout << fileIn[iFile]->GetName() << " is opened." << endl;
      sa[iFile] = (MStatusArray*)fileIn[iFile]->Get("MStatusDisplay");
      cout << sa[iFile]->GetName() << " is found." << endl;
      Int_t iAt=0; 
      Bool_t bFound=false;
      while(bFound==false && iAt<sa[iFile]->GetEntries())
	{
	  can[iFile] = (TCanvas*)sa[iFile]->At(iAt);
	  string strt = can[iFile]->GetTitle();
	  if(strt=="IntPedEx")
	    {
	      bFound = true;
	      can[iFile]->SetName(Form("%s%d", can[iFile]->GetName(), iFile));
	      can[iFile]->Draw();
	      padMean[iFile] = (TPad*)can[iFile]->cd(1);
	      padRms[iFile] = (TPad*)can[iFile]->cd(2);
	      greMean[iFile] = (TGraphErrors*)padMean[iFile]->FindObject("");
	      greMean[iFile]->SetName(Form("greMean%d", iFile));
	      greRms[iFile] = (TGraphErrors*)padRms[iFile]->FindObject("");
	      greRms[iFile]->SetName(Form("greRms%d", iFile));
	    }
	  iAt++;
	}
      mgrMean->Add(greMean[iFile]);
      mgrRms->Add(greRms[iFile]);
    }
  TCanvas *cAll = new TCanvas("cAll", "IntPedEx_all", 1200, 600);
  cAll->Divide(1,2);
  cAll->cd(1);
  mgrMean->Draw("AP");
  mgrMean->Fit("pol0");
  cout << "Fitted Mean = " << mgrMean->GetFunction("pol0")->GetParameter(0) << endl;
  cAll->cd(2);
  mgrRms->Draw("AP");
  mgrRms->Fit("pol0");
  cout << "Fitted RMS = " << mgrRms->GetFunction("pol0")->GetParameter(0) << endl;
  cAll->SaveAs(Form("IntPedEx_%s.png", strSuffix.c_str()));
  cout << strPathRC.c_str() << endl;
  ofstream ofs;
  ofs.open(strPathRC.c_str(), std::ios::out | std::ios::trunc);
  if(ofs.fail())
    cout << "Cannot open." << endl;
   ofs << "MJStar.MAddNoise.NewNoiseMean: " << mgrMean->GetFunction("pol0")->GetParameter(0) << endl;
  ofs << "MJStar.MAddNoise.NewNoiseRMS: " << mgrRms->GetFunction("pol0")->GetParameter(0) << endl;
  ofs.close();

  delete cAll;
  for(Int_t jFile=0; jFile<nFile; jFile++)
    delete fileIn[jFile];
}
