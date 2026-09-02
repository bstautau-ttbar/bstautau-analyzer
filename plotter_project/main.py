'''
- Once you have computed the SFs, the selection is fixed! If you change the selection, also Sfs need to be recomputed
--plot_all_jets options is independent from Sfs computation, so you can compute it also after having already copmuted sfs
Data is not well saved in the root file if you don't run with --noblinding option'''

# new imports
import argparse
import os, sys
import time
from datetime import datetime
import multiprocessing

import ROOT
ROOT.gROOT.SetBatch()   
ROOT.gStyle.SetOptStat(0)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

import utils
import histo_toolkit as htools
import data_toolkit as data
import tagger.utils as tagger
# ------------

# FIXME : TO_DO
# [x] read samples form input file (json or txt) instead of hardcoding them in samples.py
# [x] remove part that compute SF
# [x] remove part with preselection
# [x] include option to test a subset of (significant) histograms for quick testing
# [x] common data toolkit
# [ ] merge together similar samlpes and work on colors
# [ ] organize into libraries (WIP)
# [ ] implement the splitting by flavor rather than by samples 

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
                        default=defaults_["year"], choices=data.samples.years, 
                        type = str, 
                        help='Year of data taking'
                        )
    parser.add_argument('--flavor', 
                        action='store_true', 
                        help='Enable flavor-based histograms'
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
    parser.add_argument('--dryrun', 
                        action='store_true', 
                        help='Do not produce the output plots.'
                        )
    parser.add_argument('--mc_only', 
                        action='store_true', 
                        help='Skip data samples and run on MC only'
                        )
    parser.add_argument('-N', '--Nevents',
                        type=int, default=None,
                        help='MAX number of events to process None: all events.'
                        )
    parser.add_argument('--test_samples', 
                        action='store_true', 
                        help='Run only on signal and ttbar samples for quick testing'
                        )
    parser.add_argument('--test_histos', 
                        action='store_true', 
                        help='Run only on a subset of histograms for quick testing'
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
    year                 = args.year
    flavor               = args.flavor
    make_histos          = not args.dryrun
    blinddata            = not args.noblinding
    part_samples         = not args.not_part_samples
    plot_all_jets        = args.plot_all_jets
    plot_part_selections = args.plot_part_selections
    mc_only              = args.mc_only
    _testmode_           = args.test_samples
    test_histos          = args.test_histos
    nevents              = args.Nevents
    
    # multithreading setup
    setup_multithreading(nevents)

    # input samples
    tree_dir_base = in_info.get('MC', {}).get('inpath_template_wsfs', None)

    used_mc_samples_names = data.samples.mc_samples_names
    if (_testmode_):
        utils.logger.print_info("TEST MODE: only processing a subset of MC samples for quick testing")
        used_mc_samples_names = ['tt_fullylep', 'tt_semilep', 'tt_had', 'bstautau', 'bstautauext']
    
    print(f" > Processing {len(used_mc_samples_names)} MC samples for channels {channels}: {used_mc_samples_names}")

    # output plots
    out_dir_base  = './plots/test_{year}_{label}' if _testmode_ else in_info.get('common', {}).get('outpath_template', None)
    label = "_".join(filter(None, [
        year, 
        "test" if _testmode_ else None,
        datetime.now().strftime('%d%b%Y_%Hh%Mm%Ss')
        ]))
    out_dir        = out_dir_base.format(year=year, label=label)
    hitsos_to_plot = htools.histos_baseline.histos_test if test_histos else htools.histos_baseline.histos
    if make_histos:
        htools.io.make_directories_for_plots(out_dir, channels, flavor_based=flavor)

    samples   = dict()
    tree_name = in_info.get('common', {}).get('treename', 'Events')
    
    # --> LOOP ON CHANNELS
    for ch in channels:
        utils.logger.print_bold(f"\n--------- CHANNEL {ch} ---------")

        samples[ch] = dict()
        # MC
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
        
        # DATA (to be checked)
        if not (mc_only or _testmode_):
            print("-- loading DATA samples --")
            data.ioutils.load_data_samples(
                tree_dir,
                ch,
                data.samples.data_samples_names,
                year,
                data.samples.files_names,
                tree_name,
                nevents = nevents,
            )
        else :
            utils.logger.print_warning(" MC ONLY mode enabled, skipping data samples")
        

        utils.logger.print_bold(f"\n ... PROCESSING SAMPLES ...")
        # --> LOOP ON SAMPLES
        for name, rdf in samples[ch].items():
            print(f"\n------ {name} ------")
            _is_bstautau_ = 'bstautau' in name

            # event weight
            if 'data' not in name:
                weight_str = data.defutils.build_weight_string(name, sf=True, btag_sfs=False)
                samples[ch][name] = samples[ch][name].Define('tot_weight', weight_str)
            
            # --- JET branches specfic fo histograms
            jet_branch = 'j_sel_btagL_pt20'
            if _is_bstautau_:
                bstautau_conditions = {
                    "general"   :     f"{jet_branch}_signalBs_mask",
                    "tauhtauh"  :     f"{jet_branch}_signalBsTauhh_mask",
                    "tauhtaue"  :     f"{jet_branch}_signalBsTauhe_mask",
                    "tauhtaumu" :     f"{jet_branch}_signalBsTaumu_mask"
                }
            else:
                bstautau_conditions = None

            #samples[ch][name]     =  data.defutils.define_jets_with_btagging_selection_for_histos(samples[ch][name], part_samples=part_samples, plot_all_jets=plot_all_jets)
            # select jets for the analysis
            samples[ch][name] =  data.defutils.define_jets_for_analysis(samples[ch][name], jet_branch, 
                                                                        gen_matching_condition = bstautau_conditions['general'] if _is_bstautau_ else None, 
                                                                        all_jets = plot_all_jets
                                                                        )
            
            samples[ch][name] = tagger.part_scores_functions.define_combined_scores(samples[ch][name], 
                                                                                    f'{jet_branch}_for_histo', 
                                                                                    tau_scores, parT_scores, bkg_scores, 
                                                                                    False, #'bstautau' in name, # FIXME: adjust mask
                                                                                    bstautau_conditions
                                                                                    )
            
            # Apply  cuts filter and ONLY use those histograms
            samples[ch][name] = tagger.part_scores_functions.apply_part_sequential_cuts_filter(samples[ch][name], 
                                                                                               f'{jet_branch}_for_histo', 
                                                                                               is_bstautau='bstautau' in name
                                                                                               )
            #histos[ch] = {}  # Clear regular histos
            #histos[ch].update(histos_part_selections)  # Only add sequential cuts histos
                
            if False: # FIXME: commented for the moment need to be reimplemented properly
                histos_flavor[ch] = {}  # Clear regular flavor histos
                histos_flavor[ch].update(histos_part_selections)  # Only add sequential cuts histos for flavor
            # else:
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
            
            # Save a snapshot of few events for debugging
            if _testmode_ and (nevents is not None):
                os.makedirs(f"tmp_out/{ch}", exist_ok=True)
                samples[ch][name].Snapshot(tree_name, f"tmp_out/{ch}/{name}_snapshot.root")
                utils.logger.print_info(f" SAVED snapshot : tmp_out/{ch}/{name}_snapshot.root")
        
        
        
        # -- end loop on samples
        if not make_histos: 
            utils.logger.print_warning("Dry-run mode enabled, skipping histogram creation and plotting")
            continue
        utils.logger.print_bold(f"\n-- PLOTTING --")
        print(" > creating histogram definitions ...")
        
        # initialize all histogram definitions BEFORE processing (lazy setup)
        temp_hists = None
        temp_flavor_hists = None
        print(" > sample-based ")
        temp_hists = htools.plotting_utils.initialize_histograms(hitsos_to_plot, samples, ch, sys_uncertainty=False)
        
        if not temp_hists:
            utils.logger.print_error(f" In histogram initialization for channel {ch}. SKIPPING...")
            continue
        
        if flavor:
            print(" > flavor-based ")
            temp_flavor_hists = htools.plotting_flavourbased_utils.initialize_flavor_histograms(hitsos_to_plot, samples, ch)

        # actually process the histograms and produce the plots
        print(" > plotting histograms ...")
        c1, main_pad, ratio_pad = htools.plotting_utils.create_canvas_with_pads()
        htools.plotting_utils.process_histograms(
            hitsos_to_plot, temp_hists, 
            samples, ch, 
            data.samples.colours, 
            out_dir, 
            data.samples.titles, 
            main_pad, ratio_pad, c1, 
            blinddata, 
            mconly=mc_only
        )

        if flavor and temp_flavor_hists:
            htools.plotting_flavourbased_utils.process_flavor_histograms(hitsos_to_plot, temp_flavor_hists, ch, out_dir, main_pad, ratio_pad, c1, data.samples.colours, blinddata)

        print("-------- DONE --------")
    # end of channel loop
    
    utils.logger.print_success(f"\n Output plot in {out_dir}")

    elapsed_time = time.time() - start_time
    utils.logger.print_bold(f"\n>>> DONE AFTER {elapsed_time//60:.0f}m {elapsed_time%60:.0f}s <<<")
