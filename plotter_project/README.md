# Plotter for $Bs\to\tau\tau$


## Main usage: make plots after applying the SFs

The basic usage is:
```bash
python3 main.py --input <inputs/data-wsf-info.yml> [--year <20XX>] [--channels <ch1> <ch2> ...] [--mc_only]
```

Possible (main) argumets
|Option| Description|
|---|---|
| `--input`               | `.yml` file with input ntuple locations and metadata from `inputs/` folder |
| `--channels`            | One or more decay channels to process. Supported channels: `mu`, `e`, `emu`, `mumu`, `ee` and space-separated list of any subset. |
| `--year`                | Year of CMS data-taking (only 2018 implemented for the moment) |
| `--flavor`              | Split jets based on their flavor, rather than on the physics process. [TO BE IMPLEMENTED] |
| `--noblinding`          | Disable blinding for data |
| `--not_part_samples`    | Disable ParT scores handling, if you want to run on standard nanoAOD  |
| `--plot_all_jets`       | Plot all b-tagged jets instead of just top 2 by pT [TO BE CHECKED]|
| `--plot_part_selections`| Enable ParT sequential cuts plots (ParTRawTauhtaumu_frac > 0.6) [TO BE CHECKED]|
| `--dryrun`              | Do not produce the output plots.|
| `--mc_only`             | Skip data samples and run on MC only|
| `-N`, `--Nevents`       | MAX number of events to process None: all events.|
| `--test_samples`        | Run only on signal and ttbar samples for quick testing|
| `--test_histos`         | Run only on a subset of histograms for quick testing|

**Example:** produce a set of plot for a test-production of nanoAODv15 samples
```bash
python3 main.py --input inputs/datamc_2018_UParTedge-v0.yml --channels emu ee mumu mu e --mc_only  --test_samples
```

## Documentation
<!--
### Data handling
- [Available 2018 flat samples (without and with SFs)](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/main.py#L125-L127)
- [selection.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/selection.py)
  - Selections for each ttbar channel + trigger selection
- All the histograms with their features are saved in [histos_baseline.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/histos_baseline.py)
  - \+ [histos_part.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/histos_part.py) if we also want to include the parT scores histograms
  - \+ [histos_part_selection.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/histos_part_selections.py) if we want to include the final histograms with the exclusive categories that go in the fit!
      
- **In addition to event-level selections, our analysis relies heavily on jet-level selections. Because we use `RDataFrame`, these cannot be implemented with a simple `Filter()` (which operates only at the event level). Instead, each time we introduce a new jet selection, we must define a corresponding new jet collection.**
  - Since much of the analysis is performed at the jet level, it is important to note that not all jets in the signal sample are genuinely signal-like. To address this, we apply a mask when producing histograms that requires jets to be matched to GEN-level Bs → ττ decays (see [this implementation](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L17)).
  - As a consequence, for every new jet collection we define, we actually need to create two versions:
  1. One where, for signal samples, jets are required to match the GEN-level signal (used for histogramming).
  2. One without this requirement (used for applying selections).
- Depending on the goal of the plot, the BsTauTau signal can be displayed in different ways:
  1. Using all jets in the sample,
  2. Restricting to jets matched to the GEN-level signal,
  3. Further restricting to[ jets matched to a specific τhτX decay channel](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L26).



### Overall Pipeline:
- [main.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/main.py)
  - Loading of MC and data samples: [io_utils.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/io_utils.py)
    - [MC](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/io_utils.py#L85-L89) and [data](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/io_utils.py#L160-L167) Trigger selections applied at this stage
    - [MC normalisation](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/io_utils.py#L79) computed at this stage
  - Definitions of variables and new jet collection (to use for event-level selection) in [utils.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py):
    - Definition of [invariant mass and MT](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L262)
    - [Definition](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L63) of jet collections with [minimum selection](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/main.py#L145). These are the *selected_jets*.
      - [Definition](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L80) of same jets, but this time bstautau signal jets are required [to match with GEN bstautau](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L17). These are the *selected_jets_for_histo*.
    - [Definition](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L102) of new jet collection, on top of the *selected_jets* one, where the jets need to pass specific b-tagging requirements. *btagged_{btag_level}_jets* and *btagged_{btag_level}_jets_for_histo_*.
  - Event-based selection [applied](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/main.py#L181-L186):
    - Preselections defined [here](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/selection.py) for each channel
      - where jet_conditions are defined [here](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L210)
      - where btagging_conditions are defined [here](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L194)
  - Scale factors are computed and new samples saved if requested [here](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/main.py#L191-L220)
    - [sf_computation.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/sf_computation.py)
  - New jet collection where only [the first 2 btagged jets](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L134) with pt>20 are saved. *btagged_{btag_level}_jets_pt_above_{pt}_for_histo_*
  - Define the [final total weight](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L305) for MC samples

  - If parT scores are includes in the samples, [part_scores_function.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/part_scores_functions.py):
    - The 3 parT scores that are output of the tagger can be [combined in various ways](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/part_scores_functions.py#L5) that can be interesting to plot. For example a single signal/bkg score, or splitting the 3 signal scores vs the total bkg etc. These are interesting to look at and they are computed and [histos](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/histos_part.py) are saved.
    - Exclusive categories computed applying [subsequential parT scores cuts](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/part_scores_functions.py#L153) -> these are the final categories used for the fit! *btagged_loose_jets_pt_above_20_for_histo_m_exclusive_tauhtau{taus_decay_channel}*
  - Create histograms with [plotting_utils.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/plotting_utils.py) and [plotting_flavourbased_utils.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/plotting_flavourbased_utils.py)

-->
