"""
Several dictionaries for histogram definitions.
    h_dict = {
        <name>: (<branch_name>, <selection_string>, <isJet_based(bool)>, <h_model(ROOT.RDF.TH1DModel)>, <xlabel>, <logscale>)
        ...
    }
    for jet-based histograms:
        - <branch_name> name of the vector-branch to be plotted (e.g. 'jet_pt')
        - <selection_string> selection to be applied to the branch before plotting (e.g. 'jet_pt[<selection_string>]')
        Ex: sample.Define('jet_pt_toplot', 'jet_pt[jet_pt > 30]').Histo1D(<h_model>)
    for event-based histograms:
        - <branch_name> name of the branch to be plotted (e.g. 'e1_pt')
        - <selection_string> selection to be applied to the event before plotting (e.g. 'nj < 4' if no selection is needed)
        Ex: sample.Filter('nj < 4').Histo1D(<h_model>)

"""
import ROOT

# ------------------ GENERIC HISTOGRAMS ------------------
histo_leptons = {
    'e1_pt'     : ('e1_pt', '(1)', False, ROOT.RDF.TH1DModel('e1_pt', '', 40, 0, 200), 'e_{1} p_{T} (GeV)', False),
    'e1_eta'    : ('e1_eta','(1)', False, ROOT.RDF.TH1DModel('e1_eta','', 50, -2.5, 2.5), 'e_{1} #eta', False),
    'e1_phi'    : ('e1_phi','(1)', False, ROOT.RDF.TH1DModel('e1_phi', '', 20, -3.14, 3.14), 'e_{1} #phi', False),
    'e1_dxy'    : ('e1_dxy','(1)', False, ROOT.RDF.TH1DModel('e1_dxy', '', 40, -0.02, 0.02), 'e_{1} d_{xy}', False),
    'e1_charge' : ('e1_charge', '(1)', False, ROOT.RDF.TH1DModel('e1_charge', '',3, -1.5, 1.5), 'Electron 1 charge', False),
    'MT_e1_MET' : ('MT_e1_MET', '(1)', False, ROOT.RDF.TH1DModel('MT_e1_MET', '',60, 30, 180), 'e_{1} m_{T}', False), 
    'e2_pt'     : ('e2_pt', '(1)', False, ROOT.RDF.TH1DModel('e2_pt', '', 40, 0, 200), 'e_{2} p_{T} (GeV)', False),
    'e2_eta'    : ('e2_eta','(1)', False, ROOT.RDF.TH1DModel('e2_eta','', 50, -2.5, 2.5), 'e_{2} #eta', False),
    'e2_phi'    : ('e2_phi','(1)', False, ROOT.RDF.TH1DModel('e2_phi', '', 20, -3.14, 3.14), 'e_{2} #phi', False),
    'e2_dxy'    : ('e2_dxy','(1)', False, ROOT.RDF.TH1DModel('e2_dxy', '', 40, -0.02, 0.02), 'e_{2} d_{xy}', False),
    'e2_charge' : ('e2_charge', '(1)', False, ROOT.RDF.TH1DModel('e2_charge', '',3, -1.5, 1.5), 'Electron 1 charge', False),
    'MT_e2_MET' : ('MT_e2_MET', '(1)', False, ROOT.RDF.TH1DModel('MT_e2_MET', '',60, 30, 180), 'e_{2} m_{T}', False), 

    'mu1_pt'     : ('mu1_pt', '(1)', False, ROOT.RDF.TH1DModel('mu1_pt', '', 40, 0, 200), '#mu_{1} p_{T} (GeV)', False),
    'mu1_eta'    : ('mu1_eta','(1)', False, ROOT.RDF.TH1DModel('mu1_eta','', 50, -2.5, 2.5), '#mu_{1} #eta', False),
    'mu1_phi'    : ('mu1_phi','(1)', False, ROOT.RDF.TH1DModel('mu1_phi', '', 20, -3.14, 3.14), '#mu_{1} #phi', False),
    'mu1_dxy'    : ('mu1_dxy','(1)', False, ROOT.RDF.TH1DModel('mu1_dxy', '', 40, -0.02, 0.02), '#mu_{1} d_{xy}', False),
    'mu1_charge' : ('mu1_charge', '(1)', False, ROOT.RDF.TH1DModel('mu1_charge', '',3, -1.5, 1.5), 'Electron 1 charge', False),
    'MT_mu1_MET' : ('MT_mu1_MET', '(1)', False, ROOT.RDF.TH1DModel('MT_mu1_MET', '',60, 0, 180), '#mu_{1} m_{T}', False),
    'mu2_pt'     : ('mu2_pt', '(1)', False, ROOT.RDF.TH1DModel('mu2_pt', '', 40, 0, 200), '#mu_{2} p_{T} (GeV)', False),
    'mu2_eta'    : ('mu2_eta','(1)', False, ROOT.RDF.TH1DModel('mu2_eta','', 50, -2.5, 2.5), '#mu_{2} #eta', False),
    'mu2_phi'    : ('mu2_phi','(1)', False, ROOT.RDF.TH1DModel('mu2_phi', '', 20, -3.14, 3.14), '#mu_{2} #phi', False),
    'mu2_dxy'    : ('mu2_dxy','(1)', False, ROOT.RDF.TH1DModel('mu2_dxy', '', 40, -0.02, 0.02), '#mu_{2} d_{xy}', False),
    'mu2_charge' : ('mu2_charge', '(1)', False, ROOT.RDF.TH1DModel('mu2_charge', '',3, -1.5, 1.5), '#mu_{2} charge', False),
    'MT_mu2_MET' : ('MT_mu2_MET', '(1)', False, ROOT.RDF.TH1DModel('MT_mu2_MET', '',60, 30, 180), '#mu_{2} m_{T}', False),
}

histo_jets = {
    # all jets
    'njets'                           : ('nj_sel',               '(1)', False, ROOT.RDF.TH1DModel('nj_sel',               '', 10, -0.5, 9.5), "N jets (minimal selection)", False ) ,
    'nj_btagL_pt20'                   : ('nj_sel_btagL_pt20',    '(1)', False, ROOT.RDF.TH1DModel('nj_sel_btagL_pt20',    '', 10, -0.5, 9.5), "N b-tagged jets (L)", False ) ,
    'nj_btagM_pt20'                   : ('nj_sel_btagM_pt20',    '(1)', False, ROOT.RDF.TH1DModel('nj_sel_btagM_pt20',    '', 10, -0.5, 9.5), "N b-tagged jets (M)", False ) ,
    # analisys jets
    'j_btagL_pt20_pt'                 : ('j_sel_btagL_pt20_for_histo_pt',               '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_pt',               '', 50, 0, 200), "jet p_{T} (GeV)", False ) ,
    'j_btagL_pt20_eta'                : ('j_sel_btagL_pt20_for_histo_eta',              '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_eta',              '', 50, -2.5, 2.5), "jet #eta", False ), 
    'j_btagL_pt20_phi'                : ('j_sel_btagL_pt20_for_histo_phi',              '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_phi',              '', 50, -3.14, 3.14), "jet #phi", False ), 
    'j_btagL_pt20_m'                  : ('j_sel_btagL_pt20_for_histo_m',                '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_m',                '', 40, 0, 20), "reco jet mass", False ), 
    #'j_btagL_pt20_id'                 : ('j_sel_btagL_pt20_for_histo_id',               '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_jetid',            'jet ID', 7, 0, 7), "", False ), 
    'j_btagL_pt20_ParTRawB'           : ('j_sel_btagL_pt20_for_histo_ParTRawB',         '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_ParTRawB',         '',        40, 0., 1.), "jet di#tau tagger score B", False ), 
    'j_btagL_pt20_ParTRawC'           : ('j_sel_btagL_pt20_for_histo_ParTRawC',         '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_ParTRawC',         '',        40, 0., 1.), "jet di#tau tagger score C", False ), 
    'j_btagL_pt20_ParTRawOther'       : ('j_sel_btagL_pt20_for_histo_ParTRawOther',     '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_ParTRawOther',     '',    40, 0., 1.), "jet di#tau tagger score Other", False ), 
    #'j_btagL_pt20_ParTRawSingletau'   : ('j_sel_btagL_pt20_for_histo_ParTRawSingletau', '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_ParTRawSingletau', 'jet di#tau tagger score SingleTau',40, 0., 1.), "", False ), 
    'j_btagL_pt20_ParTRawTauhtaue'    : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaue',  '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_ParTRawTauhtaue',  '', 40, 0., 1.), "jet di#tau tagger score Tauhtaue", False ), 
    'j_btagL_pt20_ParTRawTauhtauh'    : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtauh',  '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_ParTRawTauhtauh',  '', 40, 0., 1.), "jet di#tau tagger score Tauhtauh", False ), 
    'j_btagL_pt20_ParTRawTauhtaumu'   : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaumu', '(1)', True, ROOT.RDF.TH1DModel('j_sel_for_histo_ParTRawTauhtaumu', '',40, 0., 1.), "jet di#tau tagger score Tauhtaumu", False ), 
    'j_btagL_pt20_sig_frac'           : ('j_sel_btagL_pt20_for_histo_part_sig_sum',     '(1)', True, ROOT.RDF.TH1DModel('j_sel_btagL_pt20_for_histo_part_sig_sum', '',40, 0., 1.), "jet di#tau tagger #tau_{h}#tau_{x} score fraction", False ), 

    'j_btagL_pt20_upartB'             : ('j_sel_btagL_pt20_for_histo_upartB',           '(1)', True, ROOT.RDF.TH1DModel('j_sel_btagL_pt20_for_histo_upartB',    '',40, 0., 1.), "UParT score B", False ), 
    'j_btagL_pt20_deepflavB'          : ('j_sel_btagL_pt20_for_histo_deepflavB',        '(1)', True, ROOT.RDF.TH1DModel('j_sel_btagL_pt20_for_histo_deepflavB', '',40, 0., 1.), "DeepJet score B", False ), 
}

# ------------------ TARGET OBSERVABLES TO FIT ------------------ 
histo_fit = {
    # categories based on max tagger score 
    'j_tauhtauh_incl' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtauh_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 0)', True, 
                         ROOT.RDF.TH1DModel('j_tauhtauh_frac', '', 40, 0, 1), 
                         'tagger #tau_{h}#tau_{h} frac', False),
    'j_tauhtaumu_incl': ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaumu_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 1)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaumu_frac', '', 40, 0, 1), 
                        'tagger #tau_{h}#tau_{#mu} frac', False),
    'j_tauhtaue_incl': ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaue_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 2)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaue_frac', '', 40, 0, 1), 
                        'tagger #tau_{h}#tau_{e} frac', False),
    'j_Mreg' : ('j_sel_btagL_pt20_for_histo_ParTRegMass', '(1)', True, 
                         ROOT.RDF.TH1DModel('j_Mreg', '', 40, 0, 20), 
                         'UParT M_{reg} (GeV)', False),
    # in signal region wit Mreg < X
    'j_tauhtauh_SR' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtauh_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 0 && j_sel_btagL_pt20_for_histo_ParTRegMass <= 4.5)', True, 
                         ROOT.RDF.TH1DModel('j_tauhtauh_frac_SR', '', 40, 0, 1), 
                         'tagger #tau_{h}#tau_{h} frac', False),
    'j_tauhtaumu_SR': ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaumu_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 1 && j_sel_btagL_pt20_for_histo_ParTRegMass <= 4.5)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaumu_frac_SR', '', 40, 0, 1), 
                        'tagger #tau_{h}#tau_{#mu} frac', False),
    'j_tauhtaue_SR' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaue_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 2 && j_sel_btagL_pt20_for_histo_ParTRegMass <= 4.5)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaue_frac_SR', '', 40, 0, 1), 
                        'tagger #tau_{h}#tau_{e} frac', False),
    # in control region wit Mreg > X
    'j_tauhtauh_CR' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtauh_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 0 && j_sel_btagL_pt20_for_histo_ParTRegMass > 4.5)', True, 
                         ROOT.RDF.TH1DModel('j_tauhtauh_frac_CR', '', 40, 0, 1), 
                         'tagger #tau_{h}#tau_{h} frac', False),
    'j_tauhtaumu_CR': ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaumu_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 1 && j_sel_btagL_pt20_for_histo_ParTRegMass > 4.5)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaumu_frac_CR', '', 40, 0, 1), 
                        'tagger #tau_{h}#tau_{#mu} frac', False),
    'j_tauhtaue_CR' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaue_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 2 && j_sel_btagL_pt20_for_histo_ParTRegMass > 4.5)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaue_frac_CR', '', 40, 0, 1), 
                        'tagger #tau_{h}#tau_{e} frac', False),
} 


# ---------------- HISTOGRAMS PER TTBAR CHANNEL ---------------- 
# ---- standard ----
histo_baseline = {
    'emu' : {},
    'ee'  : {},
    'mumu': {},
    'e'   : {},
    'mu'  : {},
}

for ch in ['emu', 'ee', 'e']:
    histo_baseline[ch]['e1_pt'] = histo_leptons['e1_pt']
    histo_baseline[ch]['e1_eta'] = histo_leptons['e1_eta']
    histo_baseline[ch]['e1_phi'] = histo_leptons['e1_phi']
    histo_baseline[ch]['e1_dxy'] = histo_leptons['e1_dxy']
    histo_baseline[ch]['e1_charge'] = histo_leptons['e1_charge']
    histo_baseline[ch]['MT_e1_MET'] = histo_leptons['MT_e1_MET']
for ch in ['emu', 'mumu', 'mu']:
    histo_baseline[ch]['mu1_pt'] = histo_leptons['mu1_pt'] 
    histo_baseline[ch]['mu1_eta'] = histo_leptons['mu1_eta']
    histo_baseline[ch]['mu1_phi'] = histo_leptons['mu1_phi']
    histo_baseline[ch]['mu1_dxy'] = histo_leptons['mu1_dxy']
    histo_baseline[ch]['mu1_charge'] = histo_leptons['mu1_charge']
    histo_baseline[ch]['MT_mu1_MET'] = histo_leptons['MT_mu1_MET']

histo_baseline['ee']['e2_pt']    = histo_leptons['e2_pt']
histo_baseline['ee']['e2_eta'] = histo_leptons['e2_eta']
histo_baseline['ee']['e2_phi'] = histo_leptons['e2_phi']
histo_baseline['ee']['e2_dxy'] = histo_leptons['e2_dxy']
histo_baseline['ee']['e2_charge'] = histo_leptons['e2_charge']
histo_baseline['ee']['MT_e2_MET'] = histo_leptons['MT_e2_MET']

histo_baseline['mumu']['mu2_pt'] = histo_leptons['mu2_pt'] 
histo_baseline['mumu']['mu2_eta'] = histo_leptons['mu2_eta']
histo_baseline['mumu']['mu2_phi'] = histo_leptons['mu2_phi']
histo_baseline['mumu']['mu2_dxy'] = histo_leptons['mu2_dxy']
histo_baseline['mumu']['mu2_charge'] = histo_leptons['mu2_charge']
histo_baseline['mumu']['MT_mu2_MET'] = histo_leptons['MT_mu2_MET']

for ch in ['emu', 'ee', 'mumu', 'e', 'mu']:
    histo_baseline[ch].update(histo_jets)
    histo_baseline[ch].update(histo_fit)

#  ---- test ----
histo_testmode = dict()
# --- ttbar emu
histo_testmode['emu'] = { 
    'e1_pt'     : histo_leptons['e1_pt'],
    'mu1_pt'    : histo_leptons['mu1_pt'],
}
histo_testmode['emu'].update(histo_fit)
# --- ttbar mumu
histo_testmode['mumu'] = {
    'mu1_pt'    : histo_leptons['mu1_pt'],
    'mu2_pt'    : histo_leptons['mu2_pt'],
}
histo_testmode['mumu'].update(histo_fit)
# --- ttbar ee
histo_testmode['ee'] = {
    'e1_pt'     : histo_leptons['e1_pt'],
    'e2_pt'     : histo_leptons['e2_pt'],
}
histo_testmode['ee'].update(histo_fit)
# --- ttbar mu
histo_testmode['mu'] = {
    'mu1_pt'    : histo_leptons['mu1_pt'],
}
histo_testmode['mu'].update(histo_fit)
# --- ttbar e
histo_testmode['e'] = {
    'e1_pt'     : histo_leptons['e1_pt'],
}
histo_testmode['e'].update(histo_fit)