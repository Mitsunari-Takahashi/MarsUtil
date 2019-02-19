TChain* MakeEventChain(string nameFilesIn, string nameChain)
{
  TChain *ch = new TChain(nameChain.c_str());
  ch->Add(nameFilesIn.c_str());
  return ch;
}

TTree* GetEventTree(string nameFileIn, string nameTree)
{
  TFile *fileIn = TFile::Open(nameFileIn.c_str(), "READ");
  TTree *trOut = (TTree*)fileIn->Get(nameTree.c_str());
  return trOut;
}

void LookOverCalibratedTree(TTree* trMerit, TTree* trCalibrated1, TTree* trCalibrated2, string nameFileOut, TTree* trRunHeader1, TTree* trRunHeader2)
{
  Int_t nMeritEvent = trMerit->GetEntries();
  Int_t nCalibrated1Event = trCalibrated1->GetEntries();
  Int_t nCalibrated2Event = trCalibrated2->GetEntries();

  /* Timing information */
  MTime *timeMerit1 = new MTime();
  MTime *timeMerit2 = new MTime();
  trMerit->SetBranchAddress("MTime_1.",&timeMerit1);
  trMerit->SetBranchAddress("MTime_2.",&timeMerit2);
  Long64_t msMerit1, msMerit2;
  Double_t mjdMerit1, mjdMerit2;

  MTime *timeCalibrated1 = new MTime();
  MTime *timeCalibrated2 = new MTime();
  trCalibrated1->SetBranchAddress("MTime.",&timeCalibrated1);
  trCalibrated2->SetBranchAddress("MTime.",&timeCalibrated2);
  Long64_t msCalibrated1, msCalibrated2;
  Double_t mjdCalibrated1, mjdCalibrated2;

  /* Hadronness */
  MHadronness *hadMerit = new MHadronness();
  Double_t hadronness;
  trMerit->SetBranchAddress("MHadronness.",&hadMerit);

  /* Pointing information */
  MPointingPos *pointMerit1 = new MPointingPos();
  MPointingPos *pointMerit2 = new MPointingPos();
  trMerit->SetBranchAddress("MPointingPos_1.",&pointMerit1);
  trMerit->SetBranchAddress("MPointingPos_2.",&pointMerit2);
  /* Source position information */
  MSrcPosCam *srcMerit1 = new MSrcPosCam();
  MSrcPosCam *srcMerit2 = new MSrcPosCam();
  trMerit->SetBranchAddress("MSrcPosCam_1.",&srcMerit1);
  trMerit->SetBranchAddress("MSrcPosCam_2.",&srcMerit2);

    /* Outputs */
  string pathFileOutCsv = nameFileOut + ".csv";
  std::ofstream ofs(pathFileOutCsv.c_str());

  string pathFileOutRoot = nameFileOut + ".root";
  TFile *fileOutRoot = new TFile(pathFileOutRoot.c_str(), "RECREATE");
  fileOutRoot->cd();
  TTree *trOut = new TTree("trOut", "trOut");

  const Int_t NGRID = 71;
  const Double_t stepGrid = 20.;
  Double_t xmm[NGRID][NGRID], ymm[NGRID][NGRID];
  Int_t ijLim = NGRID%2==0 ? NGRID/2 : (NGRID-1)/2;
  for(Int_t i=-ijLim; i<=ijLim; i++)
    {
      for(Int_t j=-ijLim; j<=ijLim; j++)
	{
	  //std::cout << i+ijLim << ", " << j+ijLim << ", " << stepGrid * i << std::endl;
	  xmm[i+ijLim][j+ijLim] = double(stepGrid * i);
	  ymm[i+ijLim][j+ijLim] = double(stepGrid * j);
	}
    }
  TGraph2D *gr2dRa = new TGraph2D();
  TGraph2D *gr2dDec = new TGraph2D();

  gr2dRa->SetName("RA");
  gr2dDec->SetName("DEC");
  trOut->Branch("RA", &gr2dRa);
  trOut->Branch("DEC", &gr2dDec);
  trOut->Branch("MJD", &mjdMerit1);
  trOut->Branch("Millisec", &msMerit1);
  trOut->Branch("Hadronness", &hadronness);
  trOut->Branch("MPointingPos_1.", &pointMerit1);
  trOut->Branch("MPointingPos_2.", &pointMerit2);
  trOut->Branch("MSrcPosCam_1.",&srcMerit1);
  trOut->Branch("MSrcPosCam_2.",&srcMerit2);
  
  MGeomCamMagic magicGeo;
  Double_t mm2Deg = magicGeo.GetConvMm2Deg();
  MObservatory magicObs;
  MStarCamTrans* cameraTrans = new MStarCamTrans(magicGeo, magicObs);
  Double_t poHa = 0;
  Double_t poRa = 0;
  Double_t lst = 0; // Local sidereal time
  Double_t corrPoHa = 0;
  Double_t corrPoDec = 0;
  Double_t haPhot = 0.;
  Double_t decPhot = 0.;
  Double_t raPhot = 0;

  TEntryList* listEvt1 = new TEntryList();
  TEntryList* listEvt2 = new TEntryList();
  Int_t ic1 = 0;
  Int_t ic2 = 0;
  ofs << "QEvtNum,Q1MilliSec,Q1NanoSec,Q2MilliSec,Q2NanoSec,Y1EvtNum,Y1MilliSec,Y2EvtNum,Y2MilliSec" << std::endl;
  for(Int_t im=0; im<nMeritEvent; im++)
    {
      trMerit->GetEntry(im);
      std::cout << "Melibea event #" << im << ", ";
      msMerit1 = timeMerit1->GetTime();
      msMerit2 = timeMerit2->GetTime();
      ofs << im << "," << msMerit1 << "," << msMerit2 << ",";
      mjdMerit1 = timeMerit1->GetMjd();
      mjdMerit2 = timeMerit2->GetMjd();
      hadronness = hadMerit->GetHadronness();
      if(im%10==0)
	std::cout << "  MJD: " << mjdMerit1 << std::endl;
      while(ic1<nCalibrated1Event)
	{
	  trCalibrated1->GetEntry(ic1);
	  msCalibrated1 = timeCalibrated1->GetTime();
	  mjdCalibrated1 = timeCalibrated1->GetMjd();
	  if(msCalibrated1>msMerit1+1e3 || mjdCalibrated1>mjdMerit1+0.5)
	    break;
	  else if(msCalibrated1>=msMerit1-0 && msCalibrated1<=msMerit1+0 && int(mjdCalibrated1+0.5)==int(mjdMerit1+0.5) && int(timeCalibrated1->GetNanoSec()+500)/1000==int(timeMerit1->GetNanoSec()+500)/1000)
	    {
	      ofs << ic1 << "," << msCalibrated1 << "," << timeCalibrated1->GetNanoSec();
	      std::cout << trCalibrated1->GetTree()->GetReadEntry() << "," << msCalibrated1 << "," << timeCalibrated1->GetNanoSec();
	      listEvt1->Enter(trCalibrated1->GetTree()->GetReadEntry(), trCalibrated1->GetTree());

	      // Add real photon to On-Plot
	      poHa = pointMerit1->GetHa();
	      poRa = pointMerit1->GetRa();
	      lst = poRa + poHa;
	      corrPoHa = pointMerit1->GetCorrHa();
	      corrPoDec = pointMerit1->GetCorrDec();
	      // Corrdinate transfer
	      Int_t nra=0;
	      Int_t ndec=0;
	      for(Int_t i=0; i<NGRID; i++)
		{
		  for(Int_t j=0; j<NGRID; j++)
		    {
		      cameraTrans->Cel0CamToCel(corrPoDec, corrPoHa, xmm[i][j], ymm[i][j], decPhot, haPhot);
		      raPhot = lst - haPhot;
		      raPhot += raPhot<0.?24.:0. +  raPhot>24.?-24.:0.;
		      //std::cout << "(" << xmm[i][j] << ", " << ymm[i][j] << ") <-> (" << raPhot << ", " << decPhot << ")" << std::endl;
		      gr2dRa->SetPoint(nra, xmm[i][j], ymm[i][j], raPhot);
		      gr2dDec->SetPoint(ndec, xmm[i][j], ymm[i][j], decPhot);
		      nra++;
		      ndec++;
		    }
		}
	      
	      trOut->Fill();
	      break;
	    }
	  ic1++;
	}
      ofs << ",";
      std::cout << ",";
      while(ic2<nCalibrated2Event)
	{
	  trCalibrated2->GetEntry(ic2);
	  msCalibrated2 = timeCalibrated2->GetTime();
	  mjdCalibrated2 = timeCalibrated2->GetMjd();
	  if(msCalibrated2>msMerit2+1e3 || mjdCalibrated2>mjdMerit2+0.5)
	    break;
	  else if(msCalibrated2>=msMerit2-0 && msCalibrated2<=msMerit2+0 && int(mjdCalibrated2+0.5)==int(mjdMerit2+0.5) && int(timeCalibrated2->GetNanoSec()+500)/1000==int(timeMerit2->GetNanoSec()+500)/1000)
	    {
	      ofs << ic2 << "," << msCalibrated2 << "," << timeCalibrated2->GetNanoSec();
	      std::cout << trCalibrated2->GetTree()->GetReadEntry() << "," << msCalibrated2 << "," << timeCalibrated2->GetNanoSec();
	      listEvt2->Enter(trCalibrated2->GetTree()->GetReadEntry(), trCalibrated2->GetTree());
	      //ofs << ic2; // << std::endl;
	      //ic2++;
	      break;
	    }
	  ic2++;
	}
      ofs << std::endl;
      std::cout << std::endl;
      std::cout << "Finished analyzing Melibea event #" << im << std::endl;
    }
  std::cout << std::endl;

  fileOutRoot->cd();
  trOut->Write();
  
  string pathFileOutY1 = nameFileOut + "_Y1_selected.root";
  TFile *fileOutY1 = new TFile(pathFileOutY1.c_str(), "UPDATE");
  fileOutY1->cd();
  trCalibrated1->SetEntryList(listEvt1);
  listEvt1->Write();
  std::cout << trCalibrated1->GetEntries() << std::endl;
  TTree* trCalibrated1_skimmed = (TTree*)trCalibrated1->CopyTree("");
  trCalibrated1_skimmed->Write();
  //  trRunHeader1->Write();
  
  string pathFileOutY2 = nameFileOut + "_Y2_selected.root";
  TFile *fileOutY2 = new TFile(pathFileOutY2.c_str(), "UPDATE");
  fileOutY2->cd();
  trCalibrated2->SetEntryList(listEvt2);
  listEvt2->Write();
  std::cout << trCalibrated2->GetEntries() << std::endl;
  TTree* trCalibrated2_skimmed = (TTree*)trCalibrated2->CopyTree("");
  trCalibrated2_skimmed->Write();
  //  trRunHeader2->Write();

  delete cameraTrans;
  delete listEvt1;
  delete listEvt2;
  delete timeMerit1;
  delete timeMerit2;
  delete timeCalibrated1;
  delete timeCalibrated2;
  delete pointMerit1;
  delete pointMerit2;
  delete srcMerit1;
  delete srcMerit2;
  delete fileOutY1;
  delete fileOutY2;
  delete fileOutRoot;
}

int FindCalibratedEvents(string nameFileMerit, string nameFileCalibratedM1, string nameFileCalibratedM2, string nameFileOut)
{
  //  string pathFileOut = nameFileOut + ".root";
  //  TFile*fileOut = new TFile(pathFileOut.c_str(), "RECREATE");
  TFile* fileMerit = new TFile(nameFileMerit.c_str(), "READ");
  cout << fileMerit->GetName() << " is opened." << endl;
  TTree* trMerit = (TTree*)fileMerit->Get("Events");

  //  TChain *chCalibratedM1 = (TChain*)MakeEventChain(nameFileCalibratedM1, "Events");
  //  TChain *chCalibratedM2 = (TChain*)MakeEventChain(nameFileCalibratedM2, "Events");
  TTree *chCalibratedM1 = GetEventTree(nameFileCalibratedM1, "Events");
  TTree *chCalibratedM2 = GetEventTree(nameFileCalibratedM2, "Events");

  string strCopy1 = "cp "+nameFileCalibratedM1+" "+nameFileOut+"_Y1_selected.root";
  gSystem->Exec(strCopy1.c_str());
  string strCopy2 = "cp "+nameFileCalibratedM2+" "+nameFileOut+"_Y2_selected.root";
  gSystem->Exec(strCopy2.c_str());
  TTree *trRunHeaderM1 = GetEventTree(nameFileCalibratedM1, "RunHeaders");
  TTree *trRunHeaderM2 = GetEventTree(nameFileCalibratedM2, "RunHeaders");

  LookOverCalibratedTree(trMerit, chCalibratedM1, chCalibratedM2, nameFileOut, trRunHeaderM1, trRunHeaderM2);

  delete chCalibratedM1;
  delete chCalibratedM2;
  delete fileMerit;
}
