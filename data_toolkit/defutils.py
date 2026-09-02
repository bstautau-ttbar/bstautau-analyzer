import ROOT
from . import selection
from .defcpp_functions import *
from .defak_functions import * 


jet_attributes_global = [
    "pt", "eta", "phi", "m", 
    "puid",
    "deepflavB", "upartB", "hadronFlavour"
]

jet_attributes_part = [
    "ParTRawB", 
    "ParTRawC", 
    "ParTRawOther", 
    "ParTRawSingletau",
    "ParTRawTauhtaue", 
    "ParTRawTauhtauh", 
    "ParTRawTauhtaumu",
    "ParTRegMass"
]

jet_conditions = {
    "emu"   : "(nj_sel>=2)",
    "mumu"  : "(nj_sel>=2)",
    "ee"    : "(nj_sel>=2)",
    "mu"    : "(nj_sel>=4)",
    "e"     : "(nj_sel>=4)"
}

btagging_conditions = {
    "emu"   : "nj_sel_btagL_pt20>=2",
    "mumu"  : "nj_sel_btagL_pt20>=2",
    "ee"    : "nj_sel_btagL_pt20>=2",
    "mu"    : "nj_sel_btagM_pt20>=2",
    "e"     : "nj_sel_btagL_pt30>=2"
}

# Define b-tagging thresholds
_btag_algo_           = selection.btag_algo
_btag_thresholds_     = selection.btag_wpval
_bjet_pT_threshold_   = [20, 30]

# ------ JET SELECTIONS ------

def define_jets_passing_selection(sample, channel, jet_branch, minimum_jet_conditions):
    """Define the number of jets passing the minimum selection conditions for a given channel."""
    # number of jets with minimal kinematic conditions
    sample = sample.Define(f"n{jet_branch}_sel",       f"{jet_branch}_pt[{minimum_jet_conditions}].size()")
    
    # number of jets with b-tagging conditions loose and medium working-points
    for pt in _bjet_pT_threshold_: 
        sample = sample.Define(f"n{jet_branch}_sel_btagL_pt{pt}", f"{jet_branch}_pt[{minimum_jet_conditions} & {jet_branch}_{_btag_algo_} > {_btag_thresholds_['L']} & {jet_branch}_pt > {pt}].size()")
        sample = sample.Define(f"n{jet_branch}_sel_btagM_pt{pt}", f"{jet_branch}_pt[{minimum_jet_conditions} & {jet_branch}_{_btag_algo_} > {_btag_thresholds_['M']} & {jet_branch}_pt > {pt}].size()")

    return sample

def define_btagging_conditions(samples, ch):
    """Define b-tagging conditions for different channels."""
    
    for channel, condition in btagging_conditions.items():
        samples = samples.Define(f"btagging_condition_{channel}", condition)
    
    return samples

def define_jet_conditions(samples, ch, minimum_jet_conditions):
    """Define jet selection conditions for different channels."""
    for channel, condition in jet_conditions.items():
        samples = samples.Define(f"jet_conditions_{channel}", condition)
    
    return samples

def define_jet_mask(sample, channel, jet_branch, jet_base_selection, btagging_mask=True):
    """
        For a given jet collection, define the masks for minimal selection and btagging
        (!) Just make sure that <jet_branch> and <jet_base_selection> are consistent 
    """
    masks = []
    # base selection
    sel_mask = f"{jet_branch}_sel_mask"
    sample = sample.Define(sel_mask, jet_base_selection)
    masks.append(sel_mask)
    if not btagging_mask : return sample

    # b-tagging
    for bwp, bvalue in _btag_thresholds_.items(): 
        for ptmin in _bjet_pT_threshold_: 
            mask_name = '{j}_sel_btag{wp}_pt{th}_mask'.format(j=jet_branch, wp=bwp, th=ptmin)
            mask      = '({sel}) & ({j}_{algo}>{val}) & ({j}_pt>{th})'.format(sel=jet_base_selection, j=jet_branch, algo=_btag_algo_, val=bvalue, th=ptmin)
            
            sample = sample.Define(mask_name, mask)
            masks.append(mask_name)

    return sample, masks

def define_jets_from_mask(sample, jet_branch, mask_name, part_samples = True, add_branches = [], save_njets = False):
    """
        Define a new jet collection based on a mask
        The mask should be <new-name>_mask ant the new collection will be <new-name>
    """
    jet_attributes = jet_attributes_global
    if part_samples: jet_attributes = jet_attributes + jet_attributes_part
    jet_attributes.extend(add_branches)

    new_name = mask_name.strip('_mask')
    print(f" [+] jet collection from {mask_name} -> {new_name}")
    for attr in jet_attributes:
        sample = sample.Define(f"{new_name}_{attr}", f"{jet_branch}_{attr}[{mask_name}]")

    if save_njets:
        sample = sample.Define(f"n{new_name}", f"{new_name}_pt.size()")

    return sample 

def define_jets_for_analysis(sample, jet_branch, gen_matching_condition=None, add_branches=[], all_jets=False):
    """ Select jets entering the analysis and to be plot in histograms."""

    jet_attributes = jet_attributes_global + jet_attributes_part    
    
    if all_jets: # pick all jets without selection
        for attr in jet_attributes:
            sample = sample.Define(f"{jet_branch}_for_histo_{attr}", f"{jet_branch}_{attr}")
    
    else: # pick only the 2 jets with highest pT, optionally restricted to MC-truth-matched jets
        if gen_matching_condition is not None:
            sample = sample.Define(f"{jet_branch}_for_histo_mask", f"get_topNbyVarSel_mask({jet_branch}_pt, {gen_matching_condition}, 2)")
        else:
            sample = sample.Define(f"{jet_branch}_for_histo_mask", f"get_topNbyVar_mask({jet_branch}_pt, 2)")
        sample = define_jets_from_mask(sample, jet_branch, f"{jet_branch}_for_histo_mask", part_samples=True, add_branches=add_branches, save_njets=True)

        #sample = sample.Define(f"{jet_branch}_for_histo_mask", f"get_topNbyVar_mask({jet_branch}_pt, 2)")
        #sample = define_jets_from_mask(sample, jet_branch, f"{jet_branch}_for_histo_mask", part_samples=True, save_njets=True)    

    return sample

def define_jets_with_minimum_selection(samples, minimum_jet_conditions, part_samples = True):
    """Function to define jet-related branches."""

    # Define branches for each jet attribute
    jet_attributes = jet_attributes_global
    if part_samples: jet_attributes = jet_attributes + jet_attributes_part

    for attr in jet_attributes:
        samples = samples.Define(f"j_sel_{attr}", f"j_{attr}[j_sel_mask]")

    return samples

def define_jets_with_minimum_selection_for_histos(samples, is_bstautau, bstautau_conditions, part_samples=True):

    '''Prepare branches selected for bstautau specific case (only jets matching with bs->tautau)'''
    if part_samples:
        jet_attributes = jet_attributes_global + jet_attributes_part
    else:
        jet_attributes = jet_attributes_global

    if is_bstautau:
        for attr in jet_attributes:
            samples = samples.Define(f"j_sel_for_histo_{attr}", f"j_sel_{attr}[{bstautau_conditions['general']}]")

    else:
        for attr in jet_attributes:
            samples = samples.Define(f"j_sel_for_histo_{attr}", f"j_sel_{attr}")    


    samples = samples.Define("nj_sel_for_histo", "j_sel_for_histo_pt.size()")

    return samples


def define_jets_with_btagging_selection_for_filters(samples, part_samples=True):
    """Function to define b-tagging conditions needed for event selection filters."""

    if part_samples:
        jet_attributes = jet_attributes_global + jet_attributes_part
    else:
        jet_attributes = jet_attributes_global

    # Define b-tagging conditions for medium and loose thresholds
    for btag_level, btag_value in _btag_thresholds_.items():
        # Base b-tagging condition
        samples = samples.Define(f"j_sel_btag{btag_level}_pt", f"j_sel_pt[j_sel_deepflavB > {btag_value}]")
        
        # Add pt thresholds - these are needed for selection filters
        for pt in _bjet_pT_threshold_:
            
            samples = samples.Define(
                f"j_sel_btag{btag_level}_pt{pt}",
                f"j_sel_pt[j_sel_deepflavB > {btag_value} & j_sel_pt > {pt}]"
            )

    '''Define the btagged jets but with the bstautau mask - base collections only'''
    # Define b-tagging conditions for medium and loose thresholds
    for btag_level, btag_value in _btag_thresholds_.items():
        # Base b-tagging condition for histograms
        for attr in jet_attributes:
            samples = samples.Define(f"j_sel_btag{btag_level}_for_histo_{attr}", f"j_sel_for_histo_{attr}[j_sel_for_histo_{_btag_algo_} > {btag_value}]")

    return samples

def define_jets_with_btagging_selection_for_histos(samples, part_samples, plot_all_jets=False):
    """Function to define b-tagging histogram branches - call after snapshots."""

    if part_samples:
        jet_attributes = jet_attributes_global + jet_attributes_part
    else:
        jet_attributes = jet_attributes_global

    # Define b-tagging conditions for medium and loose thresholds
    for btag_level, btag_value in _btag_thresholds_.items():
        # Add pt thresholds - conditionally apply top N selection
        for pt in _bjet_pT_threshold_:
            for attr in jet_attributes:
                # First create the filtered collection
                filtered_attr = f"j_sel_btag{btag_level}_pt{pt}_filtered_{attr}"

                print(f" [define_jets_with_btagging_selection_for_histos()] btag WP {btag_level}| pT > {pt}| var {attr} -> filtered collection: {filtered_attr}")
                samples = samples.Define(
                    filtered_attr,
                    f"j_sel_for_histo_{attr}[j_sel_for_histo_{_btag_algo_} > {btag_value} & j_sel_for_histo_pt > {pt}]"
                )
                # Choose between top 2 jets or all jets based on flag
                if plot_all_jets:
                    # Use all jets - just alias the filtered collection
                    samples = samples.Define(
                        f"j_sel_btag{btag_level}_pt{pt}_for_histo_{attr}",
                        filtered_attr
                    )
                else:
                    # Take top 2 jets (current behavior)
                    if attr == 'pt':
                        samples = samples.Define(
                            f"j_sel_btag{btag_level}_pt{pt}_for_histo_{attr}",
                            f"take_top_N_byVar({filtered_attr}, {filtered_attr}, 2)"
                        )
                    else:
                        filtered_pt = f"j_sel_btag{btag_level}_pt{pt}_filtered_pt"
                        samples = samples.Define(
                            f"j_sel_btag{btag_level}_pt{pt}_for_histo_{attr}",
                            f"take_top_N_byVar({filtered_attr}, {filtered_pt}, 2)"
                        )


        # Define the number of b-tagged jets for each threshold
        for pt in _bjet_pT_threshold_:
            samples = samples.Define(
                f"j_sel_btag{btag_level}_pt{pt}_for_histo_njets",
                f"j_sel_btag{btag_level}_pt{pt}_for_histo_pt.size()"
            )

    return samples

# ------ Bs MC matching ------
def define_bstautau_mask(sample, jet_branch = 'j_sel', taudecays = False):
    """
        Define a jet mask for the <jet_branch> collection for jets matching with the gen-level Bs.
        If <taudecays> is True, then the mask will be defined for each tau decay mode (htauh, htaue, htaumu)

        FIXME: can be improved avoiding passing the btagging and working with the proper collection directly.
    """
    if not "GenCand_SignalBs_idx" in sample.GetColumnNames():
        sample = sample.Define("GenCand_SignalBs_idx",   "findIndicesOfBsTauTau(GenCand_isBsTauTau)")
    # inclusive tau decay
    sample = (
        sample
        .Define("{j}_signalBs_idx".format(j=jet_branch), "matchSignalBsToJets(GenCand_SignalBs_idx, GenCand_eta, GenCand_phi, {j}_pt, {j}_eta, {j}_phi, {j}_{balgo}, {bth})".format(j=jet_branch, balgo=_btag_algo_, bth=_btag_thresholds_['L']))
        .Define("{j}_signalBs_mask".format(j=jet_branch), "maskFromIndices({j}_signalBs_idx, {j}_pt.size())".format(j=jet_branch))
    )
                 
    if not taudecays: return sample

    # tau decay modes
    for branch, outname in zip(['GenCand_isBsTauTauh', 'GenCand_isBsTauTaue', 'GenCand_isBsTauTaumu'], 
                           ['Tauhh', 'Tauhe', 'Tauhmu']):
        if not f"GenCand_SignalBs{outname}_idx" in sample.GetColumnNames():
            sample = sample.Define(f"GenCand_SignalBs{outname}_idx", f"findIndicesOfBsTauTau({branch})") 
        sample = (
                    sample
                    .Define("{j}_signalBs{o}_idx".format(j=jet_branch, o=outname), "matchSignalBsToJets(GenCand_SignalBs{o}_idx, GenCand_eta, GenCand_phi, {j}_pt, {j}_eta, {j}_phi, {j}_{balgo}, {bth})".format(o=outname, j=jet_branch, balgo=_btag_algo_, bth=_btag_thresholds_['L']))
                    .Define("{j}_signalBs{o}_mask".format(j=jet_branch, o=outname), "maskFromIndices({j}_signalBs{o}_idx, {j}_pt.size())".format(j=jet_branch, o=outname))
                    )

    return sample

def match_BsToJets(data, 
                   sigflag = 'GenCand_isBsTauTau',
                   jetcollection = 'jets',
                   btag_wp=_btag_thresholds_['L'], 
                   max_dr=0.4, min_jet_pt=20.0, max_jet_eta=2.5, 
                   debug = False
):
    bs_indices       = awfindIndicesOfBsTauTau(data[sigflag])
    mask, mtch_dR    = awmatchSignalBsToJets(bs_indices, 
                                         data['GenCand_eta'], data[f'GenCand_phi'], 
                                         data[f'{jetcollection}_pt'], data[f'{jetcollection}_eta'], data[f'{jetcollection}_phi'], 
                                         data[f'{jetcollection}_{_btag_algo_}'], btag_wp, 
                                         max_dr, min_jet_pt, max_jet_eta
                                         )
    
    data[f'{jetcollection}_SigJetMask'] = mask
    data[f'{jetcollection}_SigDR']      = mtch_dR   
    return data


# ------ WEIGHTS ------
def build_weight_string(k, sf=True, btag_sfs=False):
    """
    Constructs a weight expression string based on sample name and options.

    Args:
        k (str): Sample key.
        files_names (dict): Mapping of sample keys to filenames.
        options (dict): Dict of flags like compute_sfs, use_ntuples_with_sfs, etc.

    Returns:
        str: Weight expression (e.g., "norm_weight*L1PreFiringWeight_Nom*puWeight*tot_sf_weight").
    """
    weight_terms = ['norm_weight', 'L1PreFiringWeight_Nom', 'puWeight',]

    print(f" [W] top pT reweighting")
    weight_terms.append('top_pt_weight')

    if sf:
        print(f" [W] object scale factors")
        weight_terms.extend(['mu_sf_weight', 'e_sf_weight', 'trg_sf_weight']) #only SFs are applied

    if btag_sfs:
        print(f" [W] b-tag scale factors")
        weight_terms.append('btag_event_weight') #only btagging SFs are applied

    return '*'.join(weight_terms)






# -------------------------------------------------------------------#
# -------------------------------------------------------------------#
# -----------------         DEPRECATED          ---------------------#
# -------------------------------------------------------------------#
# -------------------------------------------------------------------#

# Keep the old function for backward compatibility, but mark it as deprecated
def define_jets_with_btagging_selection(samples, part_samples, plot_all_jets=False):
    """DEPRECATED: Use define_jets_with_btagging_selection_for_filters and define_jets_with_btagging_selection_for_histos instead."""
    samples = define_jets_with_btagging_selection_for_filters(samples, part_samples)
    samples = define_jets_with_btagging_selection_for_histos(samples, part_samples, plot_all_jets)
    return samples


def define_invariant_mass_and_mt(samples,ch):
    """
    Defines the invariant mass and transverse mass (MT) for different channels.

    Parameters:
    - samples: The dictionary containing the sample data.
    - ch: The channel type (e.g., 'mumu', 'emu', 'ee', etc.).
    - k: The key in the sample dictionary.

    Returns:
    - Updated samples dictionary.
    """

    # Define the HT (sum of selected jets pt)
    #samples = samples.Define("j_sel_ht", "Sum(j_sel_pt)")

    # Invariant mass and MT definitions based on channel
    if ch == 'mumu':
        samples = samples.Define("inv_mass", "compute_inv_mass(mu1_pt, mu1_eta, mu1_phi, 0.105, mu2_pt, mu2_eta, mu2_phi, 0.105)")
        samples = samples.Define("MT_mu1_MET", "compute_mt(mu1_pt, mu1_phi, PuppiMET_pt, PuppiMET_phi)")
        samples = samples.Define("MT_mu2_MET", "compute_mt(mu2_pt, mu2_phi, PuppiMET_pt, PuppiMET_phi)")

    elif ch == 'emu':
        samples = samples.Define("inv_mass", "compute_inv_mass(mu1_pt, mu1_eta, mu1_phi, 0.105, e1_pt, e1_eta, e1_phi, 0.000511)")
        samples = samples.Define("MT_mu1_MET", "compute_mt(mu1_pt, mu1_phi, PuppiMET_pt, PuppiMET_phi)")
        samples = samples.Define("MT_e1_MET", "compute_mt(e1_pt, e1_phi, PuppiMET_pt, PuppiMET_phi)")

    elif ch == 'ee':
        samples = samples.Define("inv_mass", "compute_inv_mass(e1_pt, e1_eta, e1_phi, 0.000511, e2_pt, e2_eta, e2_phi, 0.000511)")
        samples = samples.Define("MT_e1_MET", "compute_mt(e1_pt, e1_phi, PuppiMET_pt, PuppiMET_phi)")
        samples = samples.Define("MT_e2_MET", "compute_mt(e2_pt, e2_phi, PuppiMET_pt, PuppiMET_phi)")

    elif ch == 'mu':
        samples = samples.Define("MT_mu1_MET", "compute_mt(mu1_pt, mu1_phi, PuppiMET_pt, PuppiMET_phi)")

    elif ch == 'e':
        samples = samples.Define("MT_e1_MET", "compute_mt(e1_pt, e1_phi, PuppiMET_pt, PuppiMET_phi)")

    return samples


def define_bstautau_taudecaymodes_mask(samples):

    samples = (
        samples
        .Define("SignalBsTauhtauh", "findIndicesOfBsTauTau(GenCand_isBsTauTauh)")
        .Define("SigJetIdxTauhtauh", 
                f"matchSignalBsToJets(SignalBsTauhtauh, GenCand_eta, GenCand_phi, "
                f"j_sel_btagL_pt20_for_histo_pt, j_sel_btagL_pt20_for_histo_eta, j_sel_btagL_pt20_for_histo_phi, "
                f"j_sel_btagL_pt20_for_histo_{_btag_algo_}, {_btag_thresholds_['L']})")
        .Define("SigJetMaskTauhtauh", "maskFromIndices(SigJetIdxTauhtauh, j_sel_btagL_pt20_for_histo_pt.size())")
    )

    # For Tauhtaue
    samples = (
        samples
        .Define("SignalBsTauhtaue", "findIndicesOfBsTauTau(GenCand_isBsTauTaue)")
        .Define("SigJetIdxTauhtaue", 
                f"matchSignalBsToJets(SignalBsTauhtaue, GenCand_eta, GenCand_phi, "
                f"j_sel_btagL_pt20_for_histo_pt, j_sel_btagL_pt20_for_histo_eta, j_sel_btagL_pt20_for_histo_phi, "
                f"j_sel_btagL_pt20_for_histo_{_btag_algo_}, {_btag_thresholds_['L']})")
        .Define("SigJetMaskTauhtaue", "maskFromIndices(SigJetIdxTauhtaue, j_sel_btagL_pt20_for_histo_pt.size())")
    )

    # For Tauhtaumu
    samples = (
        samples
        .Define("SignalBsTauhtaumu", "findIndicesOfBsTauTau(GenCand_isBsTauTaumu)")
        .Define("SigJetIdxTauhtaumu",
                f"matchSignalBsToJets(SignalBsTauhtaumu, GenCand_eta, GenCand_phi, "
                f"j_sel_btagL_pt20_for_histo_pt, j_sel_btagL_pt20_for_histo_eta, j_sel_btagL_pt20_for_histo_phi, "
                f"j_sel_btagL_pt20_for_histo_{_btag_algo_}, {_btag_thresholds_['L']})")
        .Define("SigJetMaskTauhtaumu", "maskFromIndices(SigJetIdxTauhtaumu, j_sel_btagL_pt20_for_histo_pt.size())")
    )

    return samples
