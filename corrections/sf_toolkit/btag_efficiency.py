"""
    Calcultae btag efficiency for (L, M) working points to be used for btag SF computation.
"""

import os, sys
import multiprocessing
import numpy as np
import argparse
import time

import ROOT
ROOT.gROOT.SetBatch()   
ROOT.gStyle.SetOptStat(0)
ROOT.gErrorIgnoreLevel = ROOT.kWarning  # Suppresses Info messages, keeps Warning and Error
import uproot
BATCH_SIZE  = int(1e4)
NTHREADS    = multiprocessing.cpu_count()
# custom imports
import data_toolkit as data
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import utils


input_samples = {
    "common" : {
        "treename" : "Events",
    },
    "MC" : {
        "inpath_template"       : "/eos/cms/store/group/phys_bphys/cbasile/BsTauTau-ttbar/nanov15_skim/{channel}_{year}_test_tagMregV0/",
        "inpath_template_wsfs"  : "/eos/cms/store/group/phys_bphys/cbasile/BsTauTau-ttbar/nanov15_skim/{channel}_{year}_test_tagMregV0/sfs_applied",
    },
}

def parse_arguments():

    defaults_ = {
        "input": None,
        "channels": ['emu'],
        "test": False,
        "mc_only": False
    }

    parser = argparse.ArgumentParser(
        description="Calculate btagging SF for (L, M) working points from input ntuples and store them in a .root file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--channels', 
                        nargs='+', 
                        default=defaults_["channels"],
                        help=f'select channels to process.')
    parser.add_argument('-y', '--year',
                        type=int, default=2018,
                        help='Year of the data taking to process.'
                        )
    parser.add_argument('--test_samples',
                        action='store_true', 
                        help='Run only on signal and ttbar samples for quick testing'
                        )
    parser.add_argument('-N', '--Nevents',
                        type=int, default=None,
                        help='MAX number of events to process None: all events.'
                        )
    return parser.parse_args()


if __name__ == "__main__":

    start_time = time.time()

    # process arguments
    args = parse_arguments()
    
    channels   = args.channels
    year       = str(args.year)
    _testmode_ = args.test_samples
    nevents    = args.Nevents
    #_multit_   = setup_multithreading(nevents)

    # get samples
    tree_dir_base = input_samples.get('MC', {}).get('inpath_template_wsfs', None) # use samples w/ ttbar selection and NOT apply btag SF
    out_dir_base  = './sf_maps/btag_efficiency/{channel}_{year}/'

    used_mc_samples_names = data.samples.mc_samples_names
    if (_testmode_):
        utils.logger.print_info(" TEST MODE ENABLED")
        used_mc_samples_names = ['tt_fullylep']
    print(f" > Processing {len(used_mc_samples_names)} MC samples for channels {channels}: {used_mc_samples_names}")
    
    samples = dict()
    _tree_name = input_samples.get('common', {}).get('treename', 'Events')


    # efficiency histograms
    pt_bins  = np.array([0, 20, 30, 50, 70, 100, 140, 200, 300, 600, 1000], dtype=np.float64)
    aeta_bins = np.array([0.0, 0.8, 1.6, 2.5], dtype=np.float64)
    base_jet_collection = "j_sel"

    h_templates = {
        'denomname' : 'allj_{jetflavor}_{samplename}',
        'denom'     : ROOT.RDF.TH2DModel('h2_denom', 'all jets; jet pT [GeV]; |#eta|', len(pt_bins)-1, pt_bins, len(aeta_bins)-1, aeta_bins),
        'numname'   : 'passj_btag{wp}_{jetflavor}_{samplename}',
        'num'       : ROOT.RDF.TH2DModel('h2_num',   'pass jets; jet pT [GeV]; |#eta|', len(pt_bins)-1, pt_bins, len(aeta_bins)-1, aeta_bins),
    }

    jet_flavors = {
        0 : 'udsg',
        4 : 'c',
        5 : 'b'
    }

    btag_algo = data.selection.btag_algo
    btag_wps  = data.selection.btag_wpval[btag_algo][year]

    rootfilename = os.path.join(out_dir_base, f"btag-{btag_algo}_efficiency.root")

    utils.logger.print_bold(f"\n--- btagging efficiency calculation for {year} ---")
    print(f" > btagging algorithm: {btag_algo}")
    print(f" > btagging working points: {btag_wps}")

    # loop on channels
    print("--"*20+"\n")
    histo_to_save = []
    for ch in channels:
        utils.logger.print_bold(f"\n--------- CHANNEL {ch} ---------")
        samples[ch] = dict()

        # MC
        tree_dir = tree_dir_base.format(channel=ch, year=year)
        data.ioutils.checkpath(tree_dir, isdir=True, mustexist=True)
        out_dir  = out_dir_base.format(channel=ch, year=year)
        data.ioutils.checkpath(out_dir, isdir=True, mustexist=False)

        mc_samples = data.ioutils.load_mc_samples(
            tree_dir,
            used_mc_samples_names,
            year,
            data.samples.files_names,
            _tree_name,
            nevents = nevents,
            norm_to_xsec = False
        )
        samples[ch].update(mc_samples)
        
        for name, rdf in samples[ch].items():
            print(f" ---- {name}: {rdf.Count().GetValue()} events")

            for flav, flavname in jet_flavors.items():
                print(f"\t > Processing {flavname}-jets (flav={flav})")

                # denominator: all jets of given flavor
                model_denom = h_templates['denom']
                model_denom_name  = h_templates['denomname'].format(jetflavor=flavname, samplename=name)
                denom_selection = "{j}_{var}[{j}_hadronFlavour == {fj}]"
                
                h_den = rdf.Define("all_jet_pt", denom_selection.format(j=base_jet_collection, var="pt", fj=flav)).Define("all_jet_eta", denom_selection.format(j=base_jet_collection, var="eta", fj=flav)).Histo2D(model_denom, "all_jet_pt", "all_jet_eta")
                h_den.SetName(model_denom_name + "_denom")
                histo_to_save.append(h_den)
                
                for wp, wpval in btag_wps.items():
                    print(f"\t\t > Processing {wp} working point (btag cut={wpval})")

                    # numerator: jets of given flavor passing btag WP
                    model_num      = h_templates['num']
                    model_num_name = h_templates['numname'].format(wp=wp, jetflavor=flavname, samplename=name)
                    num_selection = "{j}_{var}[({j}_hadronFlavour == {fj}) && ({j}_{algo} > {wpval})]"
                    
                    h_num = rdf.Define("pass_jet_pt", num_selection.format(j=base_jet_collection, var="pt", fj=flav, algo=btag_algo, wpval=wpval)).Define("pass_jet_eta", num_selection.format(j=base_jet_collection, var="eta", fj=flav, algo=btag_algo, wpval=wpval)).Histo2D(model_num, "pass_jet_pt", "pass_jet_eta")
                    h_num.SetName(model_num_name + "_num")
                    histo_to_save.append(h_num)

                    # efficiency histogram: divide numerator by denominator
                    h_eff = ROOT.TEfficiency(h_num.GetValue(), h_den.GetValue())
                    h_eff.SetName(model_num_name.replace("pass", "eff"))
                    histo_to_save.append(h_eff)

        # save histograms
        chfilename = rootfilename.format(channel=ch, year=year)
        utils.logger.print_info(f"[OUT] saving in {chfilename} ---")
        out_file = ROOT.TFile(chfilename, "RECREATE")
        for h in histo_to_save:
            h.Write()
        out_file.Close()
        utils.logger.print_success(f" btagging efficiency histograms saved in {chfilename} ---")




