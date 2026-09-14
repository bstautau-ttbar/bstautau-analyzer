"""
    Study the matching efficiency between the Bs and Jet collection BEFORE any kinematic selection.
"""
from array import array
import argparse
from PhysicsTools.NanoAODTools.postprocessing.tools import *
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object, Event
from PhysicsTools.NanoAODTools.postprocessing.framework.treeReaderArrayTools import *

import ROOT
#from officialStyle import officialStyle
from cmsstyle import CMS_lumi
import data_toolkit as dtk



def get_args():
    parser = argparse.ArgumentParser(
        description="Study the matching efficiency between the Bs and Jet collection BEFORE any kinematic selection."
    )
    parser.add_argument("-i", "--input", dest="input_file",
        default="./data/mcUL18_ParTedge_nanoAODv15.txt",
        help="Path to the text file listing the input nanoAOD files (default: %(default)s)"
    )
    parser.add_argument("-s", "--sample-name", dest="sample_name",
        default="bstt",
        help="Label used internally for the sample being processed (default: %(default)s)"
    )
    parser.add_argument("--maxfiles", dest="maxfiles", 
                        type=int, default=-1,
                        help="Max number of files to process, -1 for all (default: %(default)s)"
    )
    parser.add_argument("--maxevents", dest="maxevents", 
                        type=int, default=-1,
                        help="Max number of events to process per file, -1 for all (default: %(default)s)"
    )
    parser.add_argument("--printevery", dest="printevery", 
                        type=int, default=int(1e4),
        help="Print progress every N events (default: %(default)s)"
    )
    parser.add_argument("--debug", dest="debug", 
                        action="store_true",
                        help="Enable verbose debugging printouts"
    )
    parser.add_argument("-o", "--output", dest="output_file",
        default="efficiency_plot_new",
        help="Output plot filename (default: %(default)s)"
    )
    return parser.parse_args()

matched_jet_histos = {
    "pt"  : {
        "template"  : ROOT.TH1F("matched_jet_pt", "Matched Jet p_{T};p_{T} (GeV);Jets", 50, 0, 200),
    },
    "eta" : {
        "template" : ROOT.TH1F("matched_jet_eta", "Matched Jet #eta;#eta;Jets", 50, -2.5, 2.5),
    },
    "dr"  : {
        "template" : ROOT.TH1F("matched_jet_dr", "Matched Jet #Delta R;#Delta R;Jets", 50, 0, 0.5),
    },
    #"btagDeepFlavB" : {
    #    "template" : ROOT.TH1F("matched_jet_btagDeepFlavB", "Matched Jet btagDeepFlavB;btagDeepFlavB;Jets", 50, 0, 1),
    #},
    #"btagUParTAK4B" : {
    #    "template" : ROOT.TH1F("matched_jet_btagUParTAK4B", "Matched Jet btagUParTAK4B;btagUParTAK4B;Jets", 50, 0, 1),
    #},
}
 
if __name__ == "__main__":

    args = get_args()
    
    ROOT.gROOT.SetBatch()
    ROOT.gStyle.SetOptStat(0)
    
    c1 = ROOT.TCanvas('c1', '', 700, 700)
    c1.Draw()
    c1.cd()
    c1.SetTicks(True)
    
    leg = ROOT.TLegend(0.24,.75,.95,.90)
    leg.SetBorderSize(0)
    leg.SetFillColor(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(42)
    leg.SetTextSize(0.035)
    
    ### some options (now driven by command-line arguments)
    MAXFILES    = args.maxfiles     # max files to process
    MAXEVENTS   = args.maxevents    # max events to process
    DEBUG       = args.debug        # helpful prints for debugging
    PRINTEVERY  = args.printevery   # print out the event number every N events
    #samples = {"bstt":"/afs/cern.ch/user/f/friti/work/softtaus/CMSSW_13_0_10/src/bstt/reRunNano/crab_production/nanoaodv12_bstt.txt"}
    # nanoAOD content to explore : https://cms-xpog.docs.cern.ch/autoDoc/
    #samples = {"bstt":"./data/mcUL18_ParT_nanoAODv9.txt"}
    samples = {args.sample_name: args.input_file}
    decay = 'B_{s} #rightarrow  #tau #tau'

    for sample in samples:
        files = open(samples[sample]).readlines()
        

        ####### pT histograms definition
        bins = array('d', [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 150, 200])
        nbins = len(bins)-1
        xlo = 0
        xhi = 200
        
        h_den            = ROOT.TH1F("h_good_j","h_good_j",nbins,bins)
        h_num            = ROOT.TH1F("h_matched_j","h_matched_j",nbins,bins)
        h_num_btagDeepL  = ROOT.TH1F("h_matched_j_btagDeepL","h_matched_j_btagDeepL",    nbins,bins)
        h_num_btagDeepM  = ROOT.TH1F("h_matched_j_btagDeepM","h_matched_j_btagDeepM",    nbins,bins)
        h_num_btagDeepT  = ROOT.TH1F("h_matched_j_btagDeepT","h_matched_j_btagDeepT",    nbins,bins)
        h_num_btagUParTL = ROOT.TH1F("h_matched_j_btagUParTL","h_matched_j_btagUParTL", nbins,bins)
        h_num_btagUParTM = ROOT.TH1F("h_matched_j_btagUParTM","h_matched_j_btagUParTM", nbins,bins)
        h_num_btagUParTT = ROOT.TH1F("h_matched_j_btagUParTT","h_matched_j_btagUParTT", nbins,bins)

        out_histos = {h.GetName(): h for h in [
            h_den, h_num, 
            h_num_btagDeepL, h_num_btagDeepM, h_num_btagDeepT,
            h_num_btagUParTL, h_num_btagUParTM, h_num_btagUParTT]
            }
        for _, h in out_histos.items():
            h.Sumw2()
            h.SetDirectory(0)

        ############# loop over the events
        if MAXFILES != -1: files = files[:MAXFILES]
        for fil in files:

            print("===> Processing file ",fil)
            fil = fil.strip("\n")
        
            infile = ROOT.TFile.Open(fil)        
            tree = InputTree(infile["Events"])
            
            # loop over the entries
            nevents = tree.GetEntries() if MAXEVENTS == -1 else min(tree.GetEntries(), MAXEVENTS)
            if args.maxevents > 0: nevents = min(nevents, args.maxevents)
            for i in range(nevents):
                event = Event(tree,i)
                if (DEBUG) : print(f'## EVENT {i} ##')
                if i%PRINTEVERY == 0: print(f'processing {i}th event')

                genvistaus  = Collection(event, "GenVisTau") # hadronic taus
                jets        = Collection(event, "Jet")
                genparts    = Collection(event, "GenPart")

                # look for bs-> tau tau first
                for genpart in genparts:
                    if abs(genpart.pdgId)!=531: continue #if not Bs continue
                    daughters = []
                    if (DEBUG): print(f" ({genpart._index}) Bs found pT = {genpart.pt} | pdgID {genpart.pdgId}")
                    for g in genparts: # select taus coming from the Bs
                        if abs(g.pdgId)==15 and g.genPartIdxMother == genpart._index:
                            daughters.append(g)
                            if (DEBUG): print(f"\t ({g._index}) tau-daughter pT = {g.pt} | pdgID {g.pdgId}")

                    if len(daughters) !=2: continue # Bs -> tau_x tau_x    

                    ## request at least 1 tau to decay hadronically
                    isTauhadronic = 0
                    for daughter in daughters:
                        for genvistau in genvistaus:
                            if (DEBUG) : print(f"\t\t genvistau with pT {genvistau.pt} | decay-mode {genvistau.status} | mother index {genvistau.genPartIdxMother}")
                            if genvistau.genPartIdxMother == daughter._index: isTauhadronic += 1

                    if isTauhadronic > 0 :
                        h_den.Fill(genpart.pt)
                        jet, dr = closest(genpart,jets)
                        j_btag  = jet.btagDeepFlavB if jet is not None else -1
                        jet.dr  = dr if jet is not None else -1
                        if (DEBUG) : print(f"\t\t closest jet with pT {jet.pt} | dR {dr:.3f} | btag {j_btag:.3f}")
                        
                        if (dr<0.4 and jet.pt>10 and abs(jet.eta)<2.5): # good matched jets
                            h_num.Fill(genpart.pt)
                            
                            # btagDeepFlavB selection
                            if (j_btag > dtk.selection.btag_wpval['L']): h_num_btagDeepL.Fill(genpart.pt)
                            if (j_btag > dtk.selection.btag_wpval['M']): h_num_btagDeepM.Fill(genpart.pt)
                            if (j_btag > dtk.selection.btag_wpval['T']): h_num_btagDeepT.Fill(genpart.pt)

                            try:
                                j_btag = jet.btagUParTAK4B
                                has_uparT = True
                            except (RuntimeError, AttributeError):
                                has_uparT = False

                            if has_uparT:
                                if (j_btag > dtk.selection.btagUParT_wpval['L']): h_num_btagUParTL.Fill(genpart.pt)
                                if (j_btag > dtk.selection.btagUParT_wpval['M']): h_num_btagUParTM.Fill(genpart.pt)
                                if (j_btag > dtk.selection.btagUParT_wpval['T']): h_num_btagUParTT.Fill(genpart.pt)

                            for var, cfg in matched_jet_histos.items():
                                cfg["template"].Fill(getattr(jet,var))

                if (DEBUG) : print('#-------------------------------#')
                            
        #### SAVE HISTOS ####
        outfile = ROOT.TFile.Open(f"{args.output_file}.root", "RECREATE")
        for _, h in out_histos.items():
            print(f" > {h.GetName()} written")
            h.Write()
        for var, cfg in matched_jet_histos.items():
            print(f" > {cfg['template'].GetName()} written")
            cfg["template"].Write()
        outfile.Close()         
                    
        ############ PLOTTING #########
        h_num.Sumw2()
        h_den.Sumw2()
        h_num.Divide(h_den)
        
        ## legend
        leg = ROOT.TLegend(0.24,.75,.95,.90)
        leg.SetBorderSize(0)
        leg.SetFillColor(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(42)
        leg.SetTextSize(0.035)

        leg.AddEntry(h_num,'B_{s}#rightarrow #tau_{h}#tau_{X} #Delta R(j,B_{s}) <0.4','P')
        c1.cd()
        h_num.SetTitle(";GEN B_{s} p_{T} (GeV) ;ak4/B_{s} matching efficiency")
        h_num.SetFillColor(ROOT.kWhite)
        h_num.SetLineColor(ROOT.kMagenta)
        h_num.SetMarkerColor(ROOT.kMagenta)
        h_num.SetMinimum(0)
        h_num.SetMaximum(1.3)
        
        h_num.Draw("EP2")
        h_num.Draw("hist same")
        
        leg.Draw("same")
        #CMS_lumi(c1, 4, 0, cmsText = 'CMS', extraText = ' Simulation', lumi_13TeV = '')

        c1.SaveAs(f"{args.output_file}.png")
        c1.SaveAs(f"{args.output_file}.pdf")
        
