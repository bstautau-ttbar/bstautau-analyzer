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
histo_testmode = dict()
# --- ttbar emu
histo_testmode['emu'] = { 
    'e1_pt'     : ('e1_pt', '(1)', False, ROOT.RDF.TH1DModel('e1_pt', '', 40, 0, 200), 'electron p_{T} (GeV)', False),
    'j_pt_cut'  : ('j_sel_btagL_pt20_for_histo_pt', '(j_sel_btagL_pt20_for_histo_pt > 50)', True, ROOT.RDF.TH1DModel('j_signalBs_pt', '', 50, 0, 200), 'signal Bs jet p_{T} (GeV)', False),
    # categories based on max tagger score 
    'j_tauhtauh_incl' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtauh_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 0)', True, 
                         ROOT.RDF.TH1DModel('j_tauhtauh_frac', '', 20, 0, 1), 
                         'tagger #tau_{h}#tau_{h} frac', False),
    'j_tauhtaumu_incl': ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaumu_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 1)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaumu_frac', '', 20, 0, 1), 
                        'tagger #tau_{h}#tau_{#mu} frac', False),
    'j_tauhtaue_incl': ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaue_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 2)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaue_frac', '', 20, 0, 1), 
                        'tagger #tau_{h}#tau_{e} frac', False),
    # in signal region wit Mreg < X
    'j_tauhtauh_SR' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtauh_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 0 && j_sel_btagL_pt20_for_histo_ParTRegMass <= 4.5)', True, 
                         ROOT.RDF.TH1DModel('j_tauhtauh_frac_SR', '', 20, 0, 1), 
                         'tagger #tau_{h}#tau_{h} frac', False),
    'j_tauhtaumu_SR': ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaumu_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 1 && j_sel_btagL_pt20_for_histo_ParTRegMass <= 4.5)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaumu_frac_SR', '', 20, 0, 1), 
                        'tagger #tau_{h}#tau_{#mu} frac', False),
    'j_tauhtaue_SR' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaue_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 2 && j_sel_btagL_pt20_for_histo_ParTRegMass <= 4.5)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaue_frac_SR', '', 20, 0, 1), 
                        'tagger #tau_{h}#tau_{e} frac', False),
    # in control region wit Mreg > X
    'j_tauhtauh_CR' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtauh_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 0 && j_sel_btagL_pt20_for_histo_ParTRegMass > 4.5)', True, 
                         ROOT.RDF.TH1DModel('j_tauhtauh_frac_CR', '', 20, 0, 1), 
                         'tagger #tau_{h}#tau_{h} frac', False),
    'j_tauhtaumu_CR': ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaumu_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 1 && j_sel_btagL_pt20_for_histo_ParTRegMass > 4.5)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaumu_frac_CR', '', 20, 0, 1), 
                        'tagger #tau_{h}#tau_{#mu} frac', False),
    'j_tauhtaue_CR' : ('j_sel_btagL_pt20_for_histo_ParTRawTauhtaue_frac', '(j_sel_btagL_pt20_for_histo_part_class_mask == 2 && j_sel_btagL_pt20_for_histo_ParTRegMass > 4.5)', True, 
                        ROOT.RDF.TH1DModel('j_tauhtaue_frac_CR', '', 20, 0, 1), 
                        'tagger #tau_{h}#tau_{e} frac', False),
    
}
