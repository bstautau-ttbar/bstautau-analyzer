# Preselection and MC correction for $Bs\to\tau\tau$

In this step we apply additional **preselction** based on the $t \bar t$ phase space, the jet selection for **b-tagged jets** that that will enter the next steps of the analysis. Also the main MC correction are applied:
- [] muon scale factors (iso, ID)
- ...

## Main usage: apply $t\bar t$ preselection and SF corrections
The basic way to run the code is 
```bash
python main.py --input <inputs/data-info.yml> [--channels <ch1> <ch2> ...] [--mc_only]
```

The main options are:

| Option | Short | Default | Description |
|---|---|---|---|
| `--input` | `-i` | required | `.yml` file with input ntuple locations and metadata from `inputs/` folder |
| `--channels` | | `emu` | One or more decay channels to process. Supported channels: `mu`, `e`, `emu`, `mumu`, `ee` and space-separated list of any subset. |
| `--outdirectory` | `-o` | from `.yml` | Output directory for corrected ntuples (overrides `.yml` value) |
|`--mc_only`| | `False` | Skip data |
| `--test_samples` | | `False` | Run on few samples : $t\bar t$ fullylep, semilep and $B_s\tau\tau$ signal. |
| `--sample` | | `None` | Process only this single sample (MC key, e.g. `tt_fullylep`, or data key, e.g. `data_sm`). Used by `submit_onCondor.py` to split the production per-sample. |
|`--Nevents`| `-N` | `None` | MAX number of events to process. None: all events |


**Example:** running on all channel on a test production of custom-nanoAODv15 ntuples with ParT-tagger and ParT regressed-mass inference
```bash
python3 main.py --input inputs/datamc_2018_UParTedge_tagMreg-v0.yml --channels emu mumu ee e mu --mc_only  --test_samples
``` 
### Running on batch (HTCondor)
The script [`submit_onCondor.py`](./submit_onCondor.py) submits `main.py` on HTCondor, one job per individual sample and per channel. Accepts the same `--input`, `--outdirectory`, `--channels`, `--mc_only`, `--test_samples`, `--Nevents` options as `main.py`, plus some related to the job scheduling and naming. 
It creates a directory `condor_corrections_<tag>_<yyyymmdd-hhmmss>` containing the submission script and the jobs logs and output.
Example:
  ```bash
  python3 submit_onCondor.py --input inputs/datamc_2018_UParTedge-v0.yml --channels emu --submit
  ```


## Important elements

### Input configuration file

The input `.yml` file specifies paths and common metadata of the `custom nanoAOD` 
carrying the inferred di-$\tau$ tagger score, per each jet:

```yaml
MC:
  inpath_template: "/eos/cms/.../ntuples_{channel}_2018_ParT"
  outpath_template: "/eos/cms/.../ntuples_{channel}_2018_ParT/sfs_applied"
data:
  inpath_template: "/eos/cms/.../ntuples_{channel}_2018_ParT"
  outpath_template: "/eos/cms/.../ntuples_{channel}_2018_ParT/sfs_applied"
common:
  year: 2018
  treename: Events
```
`{channel}` is substituted at runtime with the channel being processed.
See [`inputs/datamc_TEMPLATE.yml`](./inputs/datamc_TEMPLATE.yml) for a blank template and [`inputs/datamc_2018_UParTedge_tagMreg-v0.yml`](./inputs/datamc_2018_UParTedge_tagMreg-v0.yml) for a concrete example.

<!---
## Processing pipeline

For each channel and MC sample, `main.py` runs the following steps in order:

1. **Trigger selection** — applies the OR of per-dataset HLT paths defined in `data_toolkit/selection.py`
2. **Variable definition** — computes derived quantities (invariant mass, transverse mass, jet masks, b-tagging conditions)
3. **Preselection** — filters on lepton pT/η, MET, and b-tagging/jet requirements (channel-dependent)
4. **Jet selection** — requires at least one jet passing minimum kinematics (pT > 20 GeV, |η| < 2.5, jetId ≥ 2)
5. **Snapshot** — saves the skimmed tree to a temporary ROOT file in `tmp_output/`
6. **Scale factor computation** (chunked, via `sf_toolkit`):
   - Muon ID and isolation SFs (nominal + up/down)
   - Electron ID, reco, and trigger SFs (nominal + up/down)
   - Trigger SFs (channel-dependent)
   - Top pT reweighting (applied to `tt` and `bstautau` samples)
   - b-tag SFs (channel-specific working point)
7. **Consistency check** — verifies no events are lost or duplicated between the preselected and SF files
8. **Merge** — adds the SF branches back to the skimmed tree via `TTree::AddFriend` and writes the final output ntuple

Output files are named `<sample>_wsfs.root` and written to the `outpath_template` directory from the `.yml`.

## MC samples

| Key | ROOT file | Process |
|---|---|---|
| `tt_fullylep` | `TTTo2L2Nu` | $t\bar{t}$ fully leptonic |
| `tt_semilep` | `TTToSemileptonic` | $t\bar{t}$ semi-leptonic |
| `tt_had` | `TTToHadronic` | $t\bar{t}$ hadronic |
| `ww` / `wz` / `zz` | `WW` / `WZ` / `ZZ` | Diboson |
| `st_s`, `st_antit`, `st_tw`, `st_antitw` | `ST_*` | Single top |
| `w` / `wext` | `W` / `W_ext` | W+jets |
| `dy` | `DY` | Drell-Yan |
| `bstautau` | `ttbarToBsToTauTau` | Signal: $t\bar{t} \to B_s \to \tau\tau$ |
--->
## Additional scripts

- **`genmatching.py`** — studies the efficiency of matching $B_s$ to b-tagged jets at generator level (CHS and PUPPI jets). Run with `--input` pointing to a signal ntuple.