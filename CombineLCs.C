#include <iostream>

#include <TArrow.h>
#include <TCanvas.h>
#include <TF1.h>
#include <TFile.h>
#include <TGraphErrors.h>
#include <TMultiGraph.h>
#include <TH1D.h>
#include <TH1I.h>
#include <TObjArray.h>
#include <TObjString.h>
int CombineLCs(string inputfiles, string strPathFileOut)
{
  //  TObjArray* objarray = inputfiles.Tokenize(" ");
  //  Int_t nfiles = objarray->GetEntries();
  TMultiGraph *mgrLC = new TMultiGraph("mgrLC", "Combined Light Curves");
  TFile* fin;
  TGraphErrors* greLC;
  std::ifstream ifs(inputfiles.c_str());
  char str[256];
  if (ifs.fail())
    {
      std::cerr << "Failed." << std::endl;
      return -1;
    }
  
  while (ifs.getline(str, 256 - 1))
    {
      std::cout << "[" << str << "]" << std::endl;
      //      TObjString* ostr = (TObjString*) objarray->At(ifile);
      //      cout << "Opened " << ostr->GetString().Data() << endl;
      //      fin = new TFile(ostr->GetString().Data());

      fin = new TFile(str, "READ");
      cout << fin->GetName() << endl;
      greLC = (TGraphErrors*)fin->FindObjectAny("LightCurve");
      mgrLC->Add(greLC);
      delete fin;
    }

  TCanvas *cLC = new TCanvas("cLC", "LightCurve", 1000, 400);
  cLC->cd();
  mgrLC->Draw("AP");
  mgrLC->GetXaxis()->SetTitle(greLC->GetXaxis()->GetTitle());
  mgrLC->GetYaxis()->SetTitle(greLC->GetYaxis()->GetTitle());
  //  for (Int_t ifile = 0; ifile < nfiles; ifile++)
  //    {
  //    }
  TFile *fileOut = new TFile(strPathFileOut.c_str(), "UPDATE");
  fileOut->cd();
  mgrLC->Write();
  cLC->Write();
  delete fileOut;
}
