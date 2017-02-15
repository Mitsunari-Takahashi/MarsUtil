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
#include <limits.h>
int CombineLCs_Gr(string path_file_output, string path_file_graph, string name_graph, string path_file_dat, float xOffset=0)
{
  TFile *file_graph = new TFile(path_file_graph.c_str(), "READ");
  TGraphErrors *gre0 = (TGraph*)file_graph->Get(name_graph.c_str());
  gre0->SetLineColor(kBlack);
  gre0->SetMarkerColor(kBlack);
  gre0->SetMarkerStyle(5);

  TTree * trDat = new TTree("trDat", "trDat");
  trDat->ReadFile(path_file_dat.c_str(), "start:stop:flux:error");
  trDat->Draw("(start+stop)/2.0:(start-stop)/2.0:flux:error", "", "goff");
  TGraphErrors *gre1 = new TGraphErrors(trDat->GetEntries(), trDat->GetV1(), trDat->GetV3(), trDat->GetV2(), trDat->GetV4());
  gre1->SetLineColor(kBle);
  gre1->SetMarkerColor(kBlue);
  gre1->SetMarkerStyle(4);

  TMultiGraph *mgr = new TMultiGraph("mgr", "Light Curve Comparison");
  mgr->Add(gre0);
  mgr->Add(gre1);
 
  TFile *file_output = new TFile(path_file_output.c_str(), "RECREATE");
  file_output->cd();
  gre0->Write();
  gre1->Write();
  TLine* lineCrab = (TLine*)file_graph->Get("TLine");
  TLatex* txCrab = (TLatex*)file_graph->Get("txCrab");
  TCanvas *cLC = new TCanvas("cLC", "Light Curve Comparison", 1200, 750);
  cLC->cd();
  mgr->Draw("AP");
  mgr->GetXaxis()->SetTitle("MJD");
  if(lineCrab!=0x0)
    lineCrab->Draw("same");
  if(txCrab!=0x0)
    txCrab->Draw("same");
  cLC->Write();

  delete file_graph;
  delete trDat;
  delete mgr;
  delete file_output;
  delete cLC;
}
