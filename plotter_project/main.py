'''
- Once you have computed the SFs, the selection is fixed! If you change the selection, also Sfs need to be recomputed
--plot_all_jets options is independent from Sfs computation, so you can compute it also after having already copmuted sfs
Data is not well saved in the root file if you don't run with --noblinding option'''

# new imports
import argparse
import os, sys
import time, datetime
import multiprocessing

import ROOT
ROOT.gROOT.SetBatch()   
ROOT.gStyle.SetOptStat(0)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

import utils
import histo_toolkit as htools
sys.path.append('../corrections') #FIXME
import data_toolkit as data

# old imports
from io_utils import *
#from samples import *
import samples as info_samples
from selection import *
from weights import *
from sf_electron import *
from sf_muon import *
from sf_trigger_dilepton import *
from sf_computation import *
from utils import *
from plotting_utils import *
from histos_part import histos_combined_scores, histos_max_scores
from part_scores_functions import *
from plotting_flavourbased_utils import *
from histos_part_selections import histos_part_selections
# ------------

# FIXME : TO_DO
# [x] read samples form input file (json or txt) instead of hardcoding them in samples.py
# [x] remove part that compute SF
# [x] remove part with preselection
# [x] include option to test a subset of (significant) histograms for quick testing
# [ ] merge together similar samlpes and work on colors
# [ ] organize into libraries
# [ ] common data toolkit

BATCH_SIZE  = int(1e4)
NTHREADS    = multiprocessing.cpu_count()
def setup_multithreading(nevents):
    # Enable multithreading for performance (only if processing all events)
    # uproot
    if nevents is None:
        # ROOT
        utils.logger.print_info(f"[ROOT] Enabling ROOT multithreading with {NTHREADS} threads\n")
        ROOT.EnableImplicitMT(NTHREADS)
        # Optimize ROOT for performance
        ROOT.gEnv.SetValue("TFile.AsyncPrefetching", "1")  # Enable async prefetching
        ROOT.gEnv.SetValue("TTreeCache.Size", "50000000")  # 50MB cache
        ROOT.gEnv.SetValue("TFile.MaxPrefetchCacheSize", "100000000")  # 100MB prefetch
        ROOT.gEnv.SetValue("RDataFrame.DefaultNSlots", str(NTHREADS))  # Force RDataFrame to use all cores
        # Optimize snapshot writing
        opts = ROOT.RDF.RSnapshotOptions()
        opts.fCompressionLevel = 1  # faster write, slightly larger file
        opts.fCompressionAlgorithm = ROOT.ROOT.kLZ4  # LZ4 is much faster than default ZLIB
    else:
        utils.logger.print_info(f"Multithreading disabled because nevents is limited to {nevents}")
        utils.logger.print_info("ROOT multithreading doesn't work well with limited event processing")
nevents = None # Set to None to process all events, or specify a number for a limited range


def parse_arguments():

    defaults_ = {
        "channels": ['emu'],
        "year": '2018',
    }

    parser = argparse.ArgumentParser(
        description="BsTauTau Plotter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--input", "-i", 
                        required=True, 
                        help=".yml file containing the input ntuples locations and metadata"
                        )
    parser.add_argument('--channels', 
                        nargs='+', 
                        default=defaults_["channels"], 
                        help='List of channel(s) to process, e.g --channels emu mu or --channels emu'
                        )
    parser.add_argument('--year', 
                        default=defaults_["year"], choices=info_samples.years, 
                        type = str, 
                        help='Year of data taking'
                        )
    parser.add_argument('--flavor', 
                        action='store_true', 
                        help='Enable flavor-based histograms'
                        )
    parser.add_argument('--make_histos', 
                        action='store_true', 
                        help='Enable sample-based histograms'
                        )
    parser.add_argument('--noblinding', 
                        action='store_true', 
                        help='Disable blinding'
                        )
    parser.add_argument('--not_part_samples', 
                        action='store_true', 
                        help='Disable part samples (if you want to plot with old Cecile samples)'
                        )
    parser.add_argument('--plot_all_jets',
                        action='store_true', 
                        help='Plot all b-tagged jets instead of just top 2 by pT'
                        )
    parser.add_argument('--plot_part_selections', 
                        action='store_true', 
                        help='Enable ParT sequential cuts plots (ParTRawTauhtaumu_frac > 0.6)'
                        )
    parser.add_argument('--mc_only', 
                        action='store_true', 
                        help='Skip data samples and run on MC only'
                        )
    parser.add_argument('--test', 
                        action='store_true', 
                        help='Run a quick test with only signal sample'
                        )
    return parser.parse_args()

tau_scores = ['ParTRawTauhtauh', 'ParTRawTauhtaumu', 'ParTRawTauhtaue']
bkg_scores = ['ParTRawB', 'ParTRawC', 'ParTRawOther', 'ParTRawSingletau']
parT_scores = tau_scores + bkg_scores



if __name__ == '__main__':

    start_time = time.time()

    # process arguments
    args = parse_arguments()

    in_info = None
    if os.path.isfile(args.input): in_info = data.samples.parse_inyml(args.input)
    else : utils.logger.print_error(f"Input file {args.input} does not exist. EXIT"); sys.exit(1)

    channels             = args.channels
    #channels             = channels[0].split(',')
    year                 = args.year
    flavor               = args.flavor
    make_histos          = args.make_histos
    blinddata            = not args.noblinding
    part_samples         = not args.not_part_samples
    plot_all_jets        = args.plot_all_jets
    plot_part_selections = args.plot_part_selections
    mc_only              = args.mc_only
    _testmode_           = args.test
    nevents              = 1000 if _testmode_ else None
    
    # multithreading setup
    setup_multithreading(nevents)

    # input samples
    tree_dir_base = in_info.get('MC', {}).get('inpath_template_wsfs', None) #FIXME put SFs path

    used_mc_samples_names = data.samples.mc_samples_names
    if (_testmode_):
        utils.logger.print_info(" TEST MODE ENABLED")
    used_mc_samples_names = ['tt_fullylep', 'tt_semilep', 'bstautau'] # FIXME : temporary for testing
    
    print(f" > Processing {len(used_mc_samples_names)} MC samples for channels {channels}: {used_mc_samples_names}")

    # output plots
    out_dir_base  = './plots/plots{year}_{label}' if _testmode_ else in_info.get('common', {}).get('outpath_template', None) #FIXME : add outpath_template to yml file
    label = "_".join(filter(None, [
        year, 
        "test" if _testmode_ else None,
        datetime.now().strftime('%d%b%Y_%Hh%Mm%Ss')
        ]))
    out_dir = out_dir_base.format(year=year, label=label)
    hitsos_to_plot = htools.histos_baseline.histos_test #htools.histos_baseline.histos if not _testmode_ else htools.histos_baseline.histos_test  #FIXME to test
    make_directories_for_plots(out_dir, channels)


    samples   = dict()
    tree_name = in_info.get('common', {}).get('treename', 'Events')

    # --> LOOP ON CHANNELS
    for ch in channels:
        utils.logger.print_bold(f"\n--------- CHANNEL {ch} ---------")

        samples[ch] = dict()
        
        print("-- loading MC samples --")
        tree_dir = tree_dir_base.format(channel=ch)
        data.ioutils.checkpath(tree_dir, isdir=True, mustexist=True)
        mc_samples = data.ioutils.load_mc_samples(
            tree_dir,
            used_mc_samples_names,
            year,
            data.samples.files_names,
            tree_name,
            nevents = nevents,
            norm_to_xsec=False # should be already normalized.
        )
        samples[ch].update(mc_samples)
        
        if not mc_only:
            print(" ... loading data samples")
            utils.logger.print_warning("Not yet implemented ...")
            sys.exit(0)
            #data_samples = data.ioutils.load_data_samples(
            #    tree_dir,
            #    data.samples.data_samples_names,
            #    year,
            #    data.samples.files_names,
            #    tree_name,
            #    nevents = nevents
            #)
            #samples[ch].update(data_samples)
        else :
            logger.print_warning(" MC ONLY mode enabled, skipping data samples")
        

        utils.logger.print_bold(f"\n--> PROCESSING SAMPLES")
        # --> LOOP ON SAMPLES
        for name, rdf in samples[ch].items():
            

            if 'bstautau' in name:
                bstautau_conditions = {
                    "general":      "SigJetMask",
                    "tauhtauh":     "SigJetMaskTauhtauh",
                    "tauhtaue":     "SigJetMaskTauhtaue",
                    "tauhtaumu":    "SigJetMaskTauhtaumu"
                }
            else:
                bstautau_conditions = None

            # Define histogram-specific b-tagging branches AFTER filtering (won't be in snapshots)
            samples[ch][name]     = data.defutils.define_jets_with_btagging_selection_for_histos(samples[ch][name], part_samples=part_samples, plot_all_jets=plot_all_jets)
            ## define bstautau mask for different tau decay modes
            if 'bstautau' in name:
                samples[ch][name] = data.defutils.define_bstautau_taudecaymodes_mask(samples[ch][name])
            
            # Define  total event-weight
            if 'data' not in name: # FIXME implement correctly
                weight_str = data.defutils.build_weight_string(name, info_samples.files_names, sf=True, btag_sfs=False)
                print(f"Applying weights to {name}: {weight_str}")
                samples[ch][name] = samples[ch][name].Define('tot_weight', weight_str)

            print(f" > Sample {name} has {samples[ch][name].Count().GetValue():.0f} events after filtering")
            
            if False:#part_samples: #using updated samples with part scores # FIXME tocheck
                samples[ch][name] = define_combined_scores(samples[ch][name], tau_scores, parT_scores, bkg_scores, 'bstautau' in name, bstautau_conditions)
                #FIXME : at some point I want the save step here save_samples_with_btagging_sfs(samples[ch][name], ch, name, info_samples.files_names, output_dir=output_dir)
                
                if plot_part_selections:
                    # Apply  cuts filter and ONLY use those histograms
                    samples[ch][name] = apply_part_sequential_cuts_filter(samples[ch][name], is_bstautau='bstautau' in name)
                    histos[ch] = {}  # Clear regular histos
                    histos[ch].update(histos_part_selections)  # Only add sequential cuts histos
                    
                    if flavor:
                        histos_flavor[ch] = {}  # Clear regular flavor histos
                        histos_flavor[ch].update(histos_part_selections)  # Only add sequential cuts histos for flavor
                else:
                    # Regular plotting - define all the usual histograms
                    ## Define combined scores histograms
                    histos[ch].update(histos_combined_scores)
                    histos[ch].update(histos_jets_part)
                    histos[ch].update(histos_interesting_jets_part)

                    if flavor:
                        histos_flavor[ch].update(histos_interesting_jets_part)
                        histos_flavor[ch].update(histos_combined_scores)

                    ## define MAX scores
                    samples[ch][name] = define_max_scores(samples[ch][name], parT_scores, 'bstautau' in name, bstautau_conditions)
                    histos[ch].update(histos_max_scores)
                    #histos_flavor[ch].update(histos_max_scores) Not really easy to do because they are filtered in a weird way and I would need to define also hadronFlavor with the same filter
        # -- end loop on samples

        logger.print_bold(f"\n-- PLOTTING --")
        print(" > creating histogram definitions ...")
        # Initialize all histogram definitions BEFORE processing (lazy setup)
        temp_hists = None
        temp_flavor_hists = None
        
        if make_histos:
            print(" > sample-based ")
            temp_hists = initialize_histograms(hitsos_to_plot, samples, ch, sys_uncertainty=False)
            print(temp_hists)
            if flavor:
                print(" > flavor-based ")
                temp_flavor_hists = initialize_flavor_histograms(hitsos_to_plot, samples, ch)

        print(" > plotting histograms ...")
        c1, main_pad, ratio_pad = create_canvas_with_pads()
        
        if make_histos and temp_hists:
            process_histograms(hitsos_to_plot, temp_hists, samples, ch, info_samples.colours, out_dir, info_samples.titles, main_pad, ratio_pad, c1, blinddata, mconly=mc_only)

        if flavor and temp_flavor_hists:
            process_flavor_histograms(hitsos_to_plot, temp_flavor_hists, ch, out_dir, main_pad, ratio_pad, c1, info_samples.colours, blinddata)

        print("-------- DONE --------")
    # end of channel loop
    
    logger.print_success(f"\n Output plot in {out_dir}")

    elapsed_time = time.time() - start_time
    utils.logger.print_bold(f"\n>>> DONE AFTER {elapsed_time//60:.0f}m {elapsed_time%60:.0f}s <<<")
