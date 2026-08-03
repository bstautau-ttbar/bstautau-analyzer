# Plotter BsTauTau

## Setup environment

```
cmsrel CMSSW_13_0_10
cd CMSSW_13_0_10/src/
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools # install nanoaodtools
cd PhysicsTools/NanoAODTools
cmsenv
scram b
cd ../../../../ 
git clone --recursive git@github.com:bstautau-ttbar/bstautau-analyzer.git --branch nanoAODv9
cd BsTauTau/plotter_project/
```

## Arguments
General arguments:
- `make_histos`: if enabled it saves the final histograms as png, pdf, root and C files; with lin and log scale; and with the signal scaled to the stack or normalised as LHCb.
- `channels`: choose which ttbar channels to process (sometimes it is useful for testing to just process the `emu` channel, since it is the fastest one). Example: `--channels 'emu','mumu'`
- `flavor`: if enabled, it also creates flavor-based histograms (instead of only sample-based histograms). This is only for jet-based histograms, where the jets are split depending on their flavor rather than the physics process they come from.
- `noblinding`: if enabled, it removes blinding from plots (to be improved)
- `not_part_samples`: it disables all the parts of the framework where the parT score is used. This is useful if you want to run on ntuples without the saved new parT score.
- `plot_all_jets`: As a default, in the jet-based plots [only the two jets](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/utils.py#L157-L175) with highest pT are included there (this is to reduce the QCD bkg). If this flag is enabled, it plots the jet-based histograms with all the b-tagged jets.
- `plot_part_selections`: [Add to the final histograms](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/main.py#L248-L256) also [the ones](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/histos_part_selections.py) used for the final fit: 3 exclusive categories for each ttbar channel, found cutting the parT scores. Also the histogram where only the parT score of tauhtaumu is applied is saved + the histograms of the exclusive categories for the jet mass.
- `save_filtered_data`: This was an attempt to load the full data sample, apply selection, and save a snapshot of data sample already skimmed. The reason is to speed up the processhistogram creation process. This is TO BE FIXED, it is not working properly yet :( 
- `use_filtered_data`: once skimmed data sample is saved, it can be used using this flag. TO BE FIXED because it doesn't really work.

The framework also computes and applies object and trigger scale factors. Since computing them takes a long time, once they are cmputed, a snapshot of the samples is saved with new branches including the SFs, and depending on the used flag you can either compute scale factors or use samples with already computed scale factors.

Scale Factors arguments:
- `compute_sfs`: [It computes the SFs](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/sf_computation.py#L130-L137) and saves snapshots of the samples with additional branches with the new SFs. This includes reco, ID and isolation [objects](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/sf_computation.py#L10) SFs; [trigger SFs](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/sf_computation.py#L60); [top pT reweighting](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/sf_computation.py#L96).
- `compute_btag_sfs`: It loads samples where the other SFs are already computed (using the flag --compute_sfs), it [computes the b-tagging SFs](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/sf_computation.py#L159-L199) and [saves snapshots](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/sf_computation.py#L246) of the samples with additional branches with the new computed SFs.
- `use_ntuples_with_sfs`: This flag must be used if you want to use samples where the object and trigger SFs are saved. In this case these SFs are also applied.
- `use_ntuples_with_btag_sfs`: This flag must be used if you want to use samples where the b-tagging SFs (+ all the others) are saved. In this case all the SFs are applied.

## Sequence to compute SFs:

`python3 main.py --channels 'emu','mumu','ee','e','mu' --compute_sfs`

`python3 main.py --channels 'emu','mumu','ee','e','mu' --compute_btag_sfs --use_ntuples_with_sfs`

`python3 main.py --channels 'emu','mumu','ee','e','mu' --use_ntuples_with_btag_sfs --make_histos` --> final plots with all the corrections


## Examples to run

Simplest command to make plots:
`python3 main.py --make_histos --channels 'emu'`

Final command to plot everything with all the right corrections:
`python3 main.py --make_histos --channels 'emu','mumu','ee','e','mu' --use_ntuples_with_btag_sfs --plot_part_selections `

## Documentation on the code

### Some general info:
- [Available 2018 flat samples (without and with SFs)](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/main.py#L125-L127)
- [samples.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/samples.py)
  - it also includes samples cross sections
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
    - Exclusive categories computed applying [subsequential parT scores cuts](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/part_scores_functions.py#L153) --> these are the final categories used for the fit! *btagged_loose_jets_pt_above_20_for_histo_m_exclusive_tauhtau{taus_decay_channel}*
  - Create histograms with [plotting_utils.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/plotting_utils.py) and [plotting_flavourbased_utils.py](https://github.com/friti/BsTauTau/blob/bstautau/plotter_project/plotting_flavourbased_utils.py)
  
