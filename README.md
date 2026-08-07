# Analyzer for $Bs\to\tau\tau$
This analysis aims to reconstruct $Bs\to\tau_\mathrm{h}\tau_\mathrm{x}$ in b-jets exploiting $t\bar t$ events and a custom di-$\tau$ tagger based on UParT. </br>
This repository stores several tools to apply the events/jet selection and to  produce the output for the statistical analysis.

The analysis flow is organized in different code spaces:
1. [`./prel_studies`](./prel_studies/) : preliminary studies for the signal efficiency
1. [`./corrections`](./corrections/) : preselection and SF application using columnar dat format creating flat ntuples
1. [`./plotter_project`](./plotter_project/) : final plotting on top of the flat ntuples

<!-- Other code areas for validation studies: -->

## One-time setup
Use `lxplus8`, get the CMSSW release and compile:

```bash
cmsrel CMSSW_15_0_18
cd CMSSW_15_0_18/src/
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
cmsenv
scram b -j 8
```
Obtain this branch and install the python shared libraries
```bash
cd $CMSSW_BASE/src
git clone --recursive git@github.com:bstautau-ttbar/bstautau-analyzer.git -b nanoAODv15
pip3 install -e .
```
## At login

```bash
cd CMSSW_15_0_18/src/ && cmsenv
cd bstautau-analyzer/
pip3 install -e .
```
## Documentation

### Data handling

The analysis is jet-based and the global tools to handle the custom nanoAOD and to define the interesting jet collections are stored in the [`data_toolkit`](./data_toolkit/) folder. The most important libraries are:
- [samples.py](data_toolkit/samples.py) : MC and DATA samples listing by channel and year of data taking
- [selection.py](data_toolkit/selection.py) : the per-channel preselection and b-tagging conditions for the analysis jets
- [defutils.py](data_toolkit/defutils.py) : implementation of the function to extract the collection of the interesting jets

In each code space the `input/` folder contains `.yaml` files that specifies the input ntuples required for the corresponding step of the analysis .