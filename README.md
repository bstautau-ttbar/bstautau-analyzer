# Analyzer for $Bs\to\tau\tau$

Various tools for Bs TauTau analysis.

Analysis flow :
1. [`prel_studies`](prel_studies/) : preliminary studies for the signal efficiency
1. [`corrections`](corrections/) : preselection and SF application using columnar dat format creating flat ntuples
1. [`plotter_project`](plotter_project/) : final plotting on top of the flat ntuples

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
pip3 install -e . # not sure
```

