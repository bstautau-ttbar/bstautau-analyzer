

# input files up to date with https://cms-analysis-corrections.docs.cern.ch/#2018-ul-v9 (June 2026)

object_sfs ={
    '2017' : {},
    '2018' : {
        'muon' : {
            'file' : '/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run2-2018-UL-NanoAODv9/latest/muon_Z.json.gz',
            'id'   : 'NUM_TightID_DEN_genTracks',
            'iso'  : 'NUM_TightRelIso_DEN_TightIDandIPCut',
            'trg'  : 'NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight',
        },
        'electron' : {
            'file' : '/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2018-UL-NanoAODv15/latest/electron.json.gz',
            'all'  : 'UL-Electron-ID-SF',
        },
        'dileptrg' : {
            'file' : './sf_toolkit/sf_maps/dilepton_trigger_sfs_2018.root',
            'hname': 'h2D_SF_{channel}_lepABpt_FullError'
        },
        'eletrg'   : {
            'file'  : './sf_toolkit/sf_maps/electron_trigger_"+year+".root',
            'hname' : 'EGamma_SF2D'
        },
        'btag' : {
            'file'    : '/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run2-2018-UL-NanoAODv15/latest/btagging.json.gz',
            'bc'      : 'UParTAK4_comb',
            'light'   : 'UParTAK4_light',
            'eff'     : './sf_toolkit/sf_maps/btag_efficiency/{channel}_2018/btag-upartB_efficiency.root',
            'effname' : 'effj_btag{workingpoint}_{jetflavor}_tt_fullylep',
        },
    }
}