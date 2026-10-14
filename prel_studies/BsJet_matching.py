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
                        default="chs", 
                        help="Label used internally for the sample being processed (default: %(default)s)"
    )
    parser.add_argument("--jet_algo", dest="jet_algo", choices=["chs", "puppi"], default="chs",
                        help="Name of the jet collection in the nanoAOD (default: %(default)s)"
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
    samples = {args.sample_name: args.input_file}
    decay = 'B_{s} #rightarrow#tau #tau'

    ### jet selection
    max_jet_dr  = 0.4

    min_jet_pt  = 10  
    max_jet_eta = 2.5 
    if args.jet_algo == "puppi":
        min_jet_pt  = 10  
        max_jet_eta = 2.4
    print(f"Using {args.jet_algo} jets with pT > {min_jet_pt} GeV and |eta| < {max_jet_eta}")

    for sample in samples:
        files = open(samples[sample]).readlines()

        ####### pT histograms definition
        pt_bins = array('d', [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 150, 200])
        npt_bins = len(pt_bins)-1
        xlo = 0
        xhi = 200

        ####### eta binning for the 2D (pT, eta) efficiency maps
        eta_bins = array('d', [-2.5, -1.6, -0.8, 0, 0.8, 1.6, 2.5])
        neta_bins = len(eta_bins)-1

        h_den            = ROOT.TH1F("h_all_Bs","h_all_Bs",npt_bins,pt_bins)
        h_num            = ROOT.TH1F("h_matched_Bs","h_matched_Bs",npt_bins,pt_bins)
        h_num_btagDeepL  = ROOT.TH1F("h_matched_Bs_btagDeepL", "h_matched_Bs_btagDeepL",    npt_bins,pt_bins)
        h_num_btagDeepL_pt20 = ROOT.TH1F("h_matched_Bs_btagDeepL_pt20", "h_matched_Bs_btagDeepL_pt20",    npt_bins,pt_bins)
        h_num_btagDeepL_pt30 = ROOT.TH1F("h_matched_Bs_btagDeepL_pt30", "h_matched_Bs_btagDeepL_pt30",    npt_bins,pt_bins)
        h_num_btagDeepM  = ROOT.TH1F("h_matched_Bs_btagDeepM", "h_matched_Bs_btagDeepM",    npt_bins,pt_bins)
        #h_num_btagDeepT  = ROOT.TH1F("h_matched_Bs_btagDeepT", "h_matched_Bs_btagDeepT",    npt_bins,pt_bins)
        h_num_btagUParTL = ROOT.TH1F("h_matched_Bs_btagUParTL","h_matched_Bs_btagUParTL", npt_bins,pt_bins)
        h_num_btagUParTL_pt20 = ROOT.TH1F("h_matched_Bs_btagUParTL_pt20","h_matched_Bs_btagUParTL_pt20", npt_bins,pt_bins)
        h_num_btagUParTL_pt30 = ROOT.TH1F("h_matched_Bs_btagUParTL_pt30","h_matched_Bs_btagUParTL_pt30", npt_bins,pt_bins)
        h_num_btagUParTM = ROOT.TH1F("h_matched_Bs_btagUParTM","h_matched_Bs_btagUParTM", npt_bins,pt_bins)
        #h_num_btagUParTT = ROOT.TH1F("h_matched_Bs_btagUParTT","h_matched_Bs_btagUParTT", npt_bins,pt_bins)

        out_histos = {h.GetName(): h for h in [
            h_den, h_num,
            h_num_btagDeepL, h_num_btagDeepL_pt20, h_num_btagDeepL_pt30,
            h_num_btagDeepM,
            h_num_btagUParTL, h_num_btagUParTL_pt20, h_num_btagUParTL_pt30,
            h_num_btagUParTM,]
            }
        for _, h in out_histos.items():
            h.Sumw2()
            h.SetDirectory(0)

        ####### 2D (pT, eta) histograms definition, one per 1D histogram above
        h2_den            = ROOT.TH2F("h2_all_Bs","h2_all_Bs",npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num            = ROOT.TH2F("h2_matched_Bs","h2_matched_Bs",npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num_btagDeepL  = ROOT.TH2F("h2_matched_Bs_btagDeepL", "h2_matched_Bs_btagDeepL",    npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num_btagDeepL_pt20 = ROOT.TH2F("h2_matched_Bs_btagDeepL_pt20", "h2_matched_Bs_btagDeepL_pt20",    npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num_btagDeepL_pt30 = ROOT.TH2F("h2_matched_Bs_btagDeepL_pt30", "h2_matched_Bs_btagDeepL_pt30",    npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num_btagDeepM  = ROOT.TH2F("h2_matched_Bs_btagDeepM", "h2_matched_Bs_btagDeepM",    npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num_btagUParTL = ROOT.TH2F("h2_matched_Bs_btagUParTL","h2_matched_Bs_btagUParTL", npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num_btagUParTL_pt20 = ROOT.TH2F("h2_matched_Bs_btagUParTL_pt20","h2_matched_Bs_btagUParTL_pt20", npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num_btagUParTL_pt30 = ROOT.TH2F("h2_matched_Bs_btagUParTL_pt30","h2_matched_Bs_btagUParTL_pt30", npt_bins,pt_bins,neta_bins,eta_bins)
        h2_num_btagUParTM = ROOT.TH2F("h2_matched_Bs_btagUParTM","h2_matched_Bs_btagUParTM", npt_bins,pt_bins,neta_bins,eta_bins)

        out_histos_2d = {h.GetName(): h for h in [
            h2_den, h2_num,
            h2_num_btagDeepL, h2_num_btagDeepL_pt20, h2_num_btagDeepL_pt30,
            h2_num_btagDeepM,
            h2_num_btagUParTL, h2_num_btagUParTL_pt20, h2_num_btagUParTL_pt30,
            h2_num_btagUParTM,]
            }
        for _, h in out_histos_2d.items():
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

                # look for bs-> tau tau
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
                    ## match to closest jet
                    if isTauhadronic > 0 :
                        h_den.Fill(genpart.pt)
                        h2_den.Fill(genpart.pt, genpart.eta)
                        jet, dr = closest(genpart,jets)
                        if jet is None:
                            if DEBUG: print("\t\t no jet in this event")
                            continue
                        
                        j_btag  = jet.btagDeepFlavB
                        jet.dr  = dr
                        if (DEBUG) : print(f"\t\t closest jet with pT {jet.pt} | dR {dr:.3f} | btag {j_btag:.3f}")
                        
                        if (dr<max_jet_dr and jet.pt>min_jet_pt and abs(jet.eta)<max_jet_eta): # good matched jets
                            h_num.Fill(genpart.pt)
                            h2_num.Fill(genpart.pt, genpart.eta)

                            # btagDeepFlavB selection
                            if (j_btag > dtk.selection.btag_wpval['deepflavB']['2018']['L']):
                                h_num_btagDeepL.Fill(genpart.pt)
                                h2_num_btagDeepL.Fill(genpart.pt, genpart.eta)
                                if (jet.pt > 20):
                                    h_num_btagDeepL_pt20.Fill(genpart.pt)
                                    h2_num_btagDeepL_pt20.Fill(genpart.pt, genpart.eta)
                                if (jet.pt > 30):
                                    h_num_btagDeepL_pt30.Fill(genpart.pt)
                                    h2_num_btagDeepL_pt30.Fill(genpart.pt, genpart.eta)
                            if (j_btag > dtk.selection.btag_wpval['deepflavB']['2018']['M']):
                                h_num_btagDeepM.Fill(genpart.pt)
                                h2_num_btagDeepM.Fill(genpart.pt, genpart.eta)
                            #if (j_btag > dtk.selection.btag_wpval['deepflavB']['2018']['T']): h_num_btagDeepT.Fill(genpart.pt)

                            try:
                                j_btag = jet.btagUParTAK4B
                                has_uparT = True
                            except (RuntimeError, AttributeError):
                                has_uparT = False

                            if has_uparT:
                                if (j_btag > dtk.selection.btag_wpval['upartB']['2018']['L']):
                                    h_num_btagUParTL.Fill(genpart.pt)
                                    h2_num_btagUParTL.Fill(genpart.pt, genpart.eta)
                                    if (jet.pt > 20):
                                        h_num_btagUParTL_pt20.Fill(genpart.pt)
                                        h2_num_btagUParTL_pt20.Fill(genpart.pt, genpart.eta)
                                    if (jet.pt > 30):
                                        h_num_btagUParTL_pt30.Fill(genpart.pt)
                                        h2_num_btagUParTL_pt30.Fill(genpart.pt, genpart.eta)
                                if (j_btag > dtk.selection.btag_wpval['upartB']['2018']['M']):
                                    h_num_btagUParTM.Fill(genpart.pt)
                                    h2_num_btagUParTM.Fill(genpart.pt, genpart.eta)
                                #if (j_btag > dtk.selection.btagUParT_wpval['upartB']['2018']['T']): h_num_btagUParTT.Fill(genpart.pt)

                            for var, cfg in matched_jet_histos.items():
                                cfg["template"].Fill(getattr(jet,var))

                if (DEBUG) : print('#-------------------------------#')
                            
        #### SAVE HISTOS ####
        outfile = ROOT.TFile.Open(f"{args.output_file}.root", "RECREATE")
        for _, h in out_histos.items():
            print(f" > {h.GetName()} written")
            h.Write()
        for _, h in out_histos_2d.items():
            print(f" > {h.GetName()} written")
            h.Write()
        for var, cfg in matched_jet_histos.items():
            print(f" > {cfg['template'].GetName()} written")
            cfg["template"].Write()
        outfile.Close()         
