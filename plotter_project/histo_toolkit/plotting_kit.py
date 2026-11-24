import ROOT
import math, os, sys

import data_toolkit as data

from . import bstautau_cmsstyle as cms

_cms_style_ready = False

def set_histogram_style(hist, x_title, y_title, fill_color, line_color):
    hist.GetXaxis().SetTitle(x_title)
    hist.GetYaxis().SetTitle(y_title)
    hist.SetFillColor(fill_color)
    hist.SetLineColor(line_color)

"""
    plotting_kit class
"""

class plotting_kit:
    
    config_hists    = dict() # (dict): dictionary <name>: (<branch_name>, <selection_string>, <isJet_based(bool)>, <h_model(ROOT.RDF.TH1DModel)>, <xlabel>, <logscale>)   
    temp_hists      = dict() # torage for histogram outlines
    
    samples         = dict() # storage for RDataFrames
    colours         = data.samples.colours
    titles          = data.samples.titles

    year            = 2018 
    channel         = None
    signal_scale    = 50.
    mc_lumi_scale   = {'emu' : 1.0, 'ee' : 1.0, 'mumu': 1., 'e' : 1.0, 'mu' : 1.0 }  # DIRTY: apply scale to MC to match the lumi in processed data

    y_headroom_lin  = 1.5   # multiply the peak bin by this for a linear-scale frame
    y_headroom_log  = 100.  # log scale needs decades of headroom, not a percentage

    weight_branch   = 'tot_weight'

    blinding        = {# hname : (blinded interval)
        'j_tauhtauh_incl'   : [0.6, 1.0],
        'j_tauhtaue_incl'   : [0.6, 1.0],
        'j_tauhtaumu_incl'  : [0.6, 1.0],
        'j_tauhtauh_SR'     : [0.0, 1.0],
        'j_tauhtaue_SR'     : [0.0, 1.0],
        'j_tauhtaumu_SR'    : [0.0, 1.0],
        #'j_tauhtauh_CR'     : [0.6, 1.0],
        #'j_tauhtaue_CR'     : [0.6, 1.0],
        #'j_tauhtaumu_CR'    : [0.6, 1.0],
        #'j_Mreg'            : [0.,  5.]
    }

    output_dir       = './plots'
    _out_yscale      = ['log', 'lin']
    _out_formats     = ['png', 'pdf', 'C', 'root']
    
    _mc_only        = False
    _flavor_based   = False
    _debug          = False
    
    
    def __init__(self, config_hists, datamc_samples, ttbar_ch, year, weight_branch='tot_weight', output_dir='./plots', flavor_based=False, debug=False):
        
        self.config_hists   = config_hists
        self.temp_hists     = {}
        self.samples        = datamc_samples
        self.channel        = ttbar_ch
        self.year           = year
        self.weight_branch  = weight_branch
        self.output_dir     = output_dir
        
        self._mc_only       = False
        self._flavor_based  = flavor_based
        self._debug         = debug
        self._root_file      = None
        self._channel_folder = None

        # initialize cmsstyle once per process
        global _cms_style_ready
        if not _cms_style_ready:
            cms.setCMSStyle()
            _cms_style_ready = True
        ROOT.TGaxis.SetMaxDigits(3)  # Y-axis labels switch to scientific notation above 1e3

        # avoid the display histogram to be attached to the out root file
        ROOT.TH1.AddDirectory(False)

        cms.SetEnergy(13)
        cms.SetLumi(data.samples.luminosity_year.get(year, {'total':-1} )['total'])
        cms.SetExtraText("Preliminary")
        cms.cmsTextSize = 1.0
        cms.ResetAdditionalInfo()
        cms.AppendAdditionalInfo(data.samples.ch_labels[self.channel])
        cms.extraOverCmsTextSize = 0.9

        print(f" [PlottingKit] initialized with channel {self.channel} and smaples: {list(self.samples.keys())}")
        if not self._flavor_based:
            print(" [PlottingKit] sample-based")
        else:
            print(" [PlottingKit] flavor-based")
        
    # SETTERS

    def set_channel(self, ttbar_ch):
        self.channel = ttbar_ch
    def set_weight_branch(self, weight_branch):
        self.weight_branch = weight_branch
    def set_temp_hists(self, temp_hists):
        self.temp_hists = temp_hists
    def set_samples(self, datamc_samples):
        self.samples = datamc_samples
    def set_colors(self, colours):
        self.colours = colours
    def set_blinding(self, blinding):
        self.blinding = blinding
    def set_mc_only(self, mc_only):
        self._mc_only = mc_only
    def set_flavor_based(self, flavor_based):
        self._flavor_based = flavor_based
    def set_debug(self, debug):
        self._debug = debug
    def set_signal_scale(self, scale):
        if isinstance(scale, (int, float)):
            self.signal_scale = scale


    # ----------- I/O HELPER FUNCTIONS -----------
    def setup_output_directory(self):
        """Create directories for storing plots in multiple formats and versions."""
        self.out_plot_base_path  = os.path.join(self.output_dir, self.channel, 'samples_based' if not self._flavor_based else 'flavor_based')
        # Sample-based plots
        for y in self._out_yscale:
            for fmt in self._out_formats:
                os.makedirs( os.path.join(self.out_plot_base_path, 'bstautau_scaled', y, fmt), exist_ok=True)

        root_fname = 'histograms.root' if not self._flavor_based else 'histograms_flavor.root'
        self.root_file_path = os.path.join(self.output_dir, root_fname)
        print(f" [PlottingKit|OUTPUT] + plots directories {self.output_dir} --- {self.channel}")
    
    def unpack_histogram_info(self, hinfo):
        pass

    def save_plot_version(self, canv, outname):
        base_path = os.path.join(self.out_plot_base_path, 'bstautau_scaled', 'lin')
        for fmt in self._out_formats :
            canv.SaveAs(os.path.join(base_path,fmt, f'{outname}.{fmt}'))
    

    def _get_channel_folder(self):
        """ 
        open self.root_file_path once per channel run
        cached on the instance and ovoid duplicates for every histogram saving
        """
        if self._root_file is None:
            self._root_file = ROOT.TFile(self.root_file_path, 'UPDATE', "", ROOT.kLZMA)  # LZMA compression
            self._root_file.SetCompressionLevel(1)  # fast compression
            self._channel_folder = self._root_file.mkdir(self.channel)
        return self._channel_folder

    def close_root_file(self):
        if self._root_file is not None:
            self._root_file.Close()
            self._root_file = None
            self._channel_folder = None

    def save_toROOT(self, hname, mc_stack, data_stack):

        channel_folder = self._get_channel_folder()
        hfolder = channel_folder.mkdir(hname)
        hfolder.cd()

        # save MC
        if mc_stack.GetStack() and mc_stack.GetStack().Last():
            mc_total = mc_stack.GetStack().Last().Clone()
            mc_total.Write("mc_total")
        for key, hist in self.temp_hists[hname].items():
            sname = key.split(hname+'_')[1]
            if 'data' in sname : continue
            hist = hist.GetValue() if hasattr(hist, 'GetValue') else hist
            this_hist = hist.Clone()
            this_hist.Write(sname)

        # save DATA directly from the original (unblinded) version
        if not self._mc_only:
            data_string = '_'.join([hname, 'data'])
            data_keys = [k for k in self.temp_hists[hname] if data_string in k]
            if data_keys:
                first = self.temp_hists[hname][data_keys[0]]
                first = first.GetValue() if hasattr(first, 'GetValue') else first
                original_data_hist = first.Clone(f"{hname}_data_original")
                for k in data_keys[1:]:
                    nxt = self.temp_hists[hname][k]
                    original_data_hist.Add(nxt.GetValue() if hasattr(nxt, 'GetValue') else nxt)
                original_data_hist.Write("data_obs")
       

    # ----------- PLOTTING STYLE FUNCTIONS -----------
    def _combine_histogram_list(self, hist_list, out_name):
        """ 
        Merge a list of RResultPtr<TH1D> into one TH1D
        """
        first = hist_list[0]
        combined = (first.GetValue() if hasattr(first, 'GetValue') else first).Clone(out_name)
        for h in hist_list[1:]:
            combined.Add(h.GetValue() if hasattr(h, 'GetValue') else h)
        return combined

    def apply_style(self, hname, xtitle, ytitle):
        """ apply style to histos in temp_hists[hname] """
        for key, hist in self.temp_hists[hname].items():

            if isinstance(hist, list):
                hist = self._combine_histogram_list(hist, key)
                self.temp_hists[hname][key] = hist   # cache: list -> plain TH1D, in place

            if (self._debug) : print(f' [PlottingKit] styling {key} > {hist}')
            sample_name = key.split(hname + '_')[1]
            is_data     = f'{hname}_data' in key
            color = ROOT.kBlack if is_data else self.colours.get(sample_name, ROOT.kBlack)

            hist.GetXaxis().SetTitle(xtitle)
            hist.GetYaxis().SetTitle(ytitle)
            hist.SetFillColor(color)
            hist.SetLineColor(color)
            hist.SetMarkerStyle(20 if is_data else 0)
            hist.SetMarkerSize(1.0 if is_data else 0)
    
    def create_legend(self, hname, xylow_xyhigh=(0.30,.65,.95,.90)):
        """Create a legend for the histograms."""
        leg = ROOT.TLegend(*xylow_xyhigh)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(42)
        leg.SetTextSize(0.04)
        leg.SetNColumns(3)
        
        if self._flavor_based:
            entries = ['b_jets', 'c_jets', 'light_jets']
            if f'{hname}_bstautau' in self.temp_hists[hname]: entries.append('bstautau')
            if f'{hname}_data' in self.temp_hists[hname]:     entries.append('data')
        else:
            entries = list(self.samples.keys())

        data_added = False
        for entry in entries:
            if 'data' in entry and data_added: continue
            key = f'{hname}_{entry}'
            if key not in self.temp_hists[hname]: continue
            is_signal = 'bstautau' in entry
            hist = self.temp_hists[hname][key]
            hist = hist.GetValue() if hasattr(hist, 'GetValue') else hist
            leg.AddEntry(
                hist,
                self.titles.get(entry, entry) + (f'#times{int(self.signal_scale)}' if is_signal and self.signal_scale > 1. else ''),
                "EP" if 'data' in entry else ('L' if is_signal else 'F')
            )
            data_added = 'data' in entry or data_added

        if not data_added and not self._mc_only:
            print(f" [PlottingKit] WARNING: no data sample found in {list(self.samples.keys())}. Adding a dummy entry for data in the legend.")
            
        return leg

    def _blind_histogram(self, h, lo, hi):
        """ zero out bins whose center falls within [lo, hi] - blinds a display
        histogram in place; save_toROOT never sees this clone, only the pristine one """
        for i in range(1, h.GetNbinsX() + 1):
            if lo <= h.GetBinCenter(i) <= hi:
                h.SetBinContent(i, 0)
                h.SetBinError(i, 0)

    def create_stack(self, hname):
        """Create a stack of histograms for MC samples and a separate histogram for data."""
        mc_stack    = ROOT.THStack(f"{hname}_mc_stack", "")
        data_stck   = ROOT.THStack(f"{hname}_data_stack", "")
        h_sig        = None
        h_sig_scaled = None

        data_string = '_'.join([hname, 'data'])
        scaletolumi = self.mc_lumi_scale[self.channel]

        for key, hist in self.temp_hists[hname].items():
            if data_string in key:
                display_h = hist.GetValue().Clone(f"{key}_display") # crucial to avoid modifying the original when blinding
                if hname in self.blinding:
                    self._blind_histogram(display_h, *self.blinding[hname])
                data_stck.Add(display_h)
            elif 'bstautau' in key:
                h_sig        = hist.GetValue().Clone()
                h_sig.Scale(scaletolumi) 
                h_sig_scaled = hist.GetValue().Clone(f"{key}_scaled") 
                h_sig_scaled.Scale(self.signal_scale*scaletolumi)
            else:
                h_display = hist.GetValue().Clone()
                h_display.Scale(scaletolumi)
                mc_stack.Add(h_display)

        return mc_stack, data_stck, h_sig, h_sig_scaled

    def create_flavor_stack(self, hname):
        """
            Counterpart for flavor based stack
        """
        mc_stack    = ROOT.THStack(f"{hname}_mc_stack", "")
        data_stck   = ROOT.THStack(f"{hname}_data_stack", "")
        h_sig        = None
        h_sig_scaled = None

        data_string = '_'.join([hname, 'data'])
        scaletolumi = self.mc_lumi_scale[self.channel]

        for key, hist in self.temp_hists[hname].items():
            if data_string in key:
                display_h = hist.Clone(f"{key}_display") # crucial to avoid modifying the original when blinding
                if hname in self.blinding:
                    self._blind_histogram(display_h, *self.blinding[hname])
                data_stck.Add(display_h)
            elif 'bstautau' in key:
                h_sig        = hist.Clone()
                h_sig.Scale(scaletolumi)
                h_sig_scaled = hist.Clone(f"{key}_scaled")
                h_sig_scaled.Scale(self.signal_scale*scaletolumi)
            else:   # b_jets / c_jets / light_jets
                h_display = hist.Clone()
                h_display.Scale(scaletolumi)
                mc_stack.Add(h_display)

        return mc_stack, data_stck, h_sig, h_sig_scaled

    # ----------- PROCESSING HISTOGRAMS AND PLOTTING ----------------
    # 1. INITIALIZE HISTOGRAMS
    
    def initialize_histograms(self):
        """
            Initialize the histograms for a set of samples
            Works with:
                histos (dict): dictionary <name>: (<branch_name>, <selection_string>, <isJet_based(bool)>, <h_model(ROOT.RDF.TH1DModel)>, <xlabel>, <logscale>)
                samples (dict): dictionary <sample_name>: <RDataFrame>
                norm_weight (str): branch name for the normalization weight to be applied to the histograms. Default is 'tot_weight'

            Returns:
                dict: A dictionary containing the initialized histograms for each variable and sample. "xvar" : { "sample_name" : TH1D, ... }
        """

        # loop on histograms templates
        for hname, hinfo in self.config_hists.items():
            self.temp_hists[hname] = {}
            branch_name, selection, isjet_based, h_model, xlabel, logscale = hinfo
            # loop on samples
            for sname, srdf in self.samples.items():
                #print(f' [PlottingKit] {hname} -- {sname}')
                thisselection = selection
                if ('bstautau' in sname) and (isjet_based):
                    thisselection += "&&(j_sel_btagL_pt20_for_histo_signalBs_mask==1)"
                #if (isjet_based): thisselection +=  '&&(j_sel_btagL_pt20_for_histo_ParTRegMass>5)'
                if thisselection == '(1)':
                    self.temp_hists[hname][f'{hname}_{sname}'] = srdf.Histo1D(h_model, branch_name, self.weight_branch)
                else:
                    if isjet_based:
                        #print(f'  > jet-based selection: {selection}')
                        self.temp_hists[hname][f'{hname}_{sname}'] = srdf.Define(f'{branch_name}_toplot', f'{branch_name}[{thisselection}]').Histo1D(h_model, f'{branch_name}_toplot', self.weight_branch)
                    else: #event-based
                        self.temp_hists[hname][f'{hname}_{sname}'] = srdf.Filter(thisselection).Histo1D(h_model, branch_name, self.weight_branch)
            if self._debug: print(self.temp_hists)

    def initialize_flavor_histograms(self):
        """
            Initialize flavor-based histograms only for jet-based histograms.
            Based on jet_hadronFlavor = 5 (b-jet) = 4 (c-jet) = 0 (light jet)
            Breakdown MC histos by flavor merging different samples -> collected into a list per category
            Data and signal bstautau are not split
        """
        verbose = self._debug
        flavor_categories = {
            'b_jets':     '(j_sel_btagL_pt20_for_histo_hadronFlavour==5)',
            'c_jets':     '(j_sel_btagL_pt20_for_histo_hadronFlavour==4)',
            'light_jets': '(j_sel_btagL_pt20_for_histo_hadronFlavour!=4 && j_sel_btagL_pt20_for_histo_hadronFlavour!=5)',
        }
       
        for hname, hinfo in self.config_hists.items():
            branch_name, selection, isjet_based, h_model, xlabel, logscale = hinfo
            self.temp_hists[hname] = {}   # empty for event based vars

            if not isjet_based:
                if verbose:
                    print(f" [PlottingKit|flavor] skip '{hname}': event-based, no per-jet collection to split by hadronFlavour")
                continue

            def _book(srdf, thisselection, defbranch):
                if thisselection == '(1)':
                    return srdf.Histo1D(h_model, branch_name, self.weight_branch)
                return srdf.Define(defbranch, f'{branch_name}[{thisselection}]').Histo1D(h_model, defbranch, self.weight_branch)

            # ---- MC ----
            for category_name, category_cut in flavor_categories.items():
                cat_hists = []
                for sname, srdf in self.samples.items():
                    if 'data' in sname or 'bstautau' in sname:
                        continue
                    thisselection = f'{selection}&&{category_cut}' #&&(j_sel_btagL_pt20_for_histo_ParTRegMass>5)'
                    defbranch = f'{branch_name}_toplot_{category_name}'
                    cat_hists.append(_book(srdf, thisselection, defbranch))
                self.temp_hists[hname][f'{hname}_{category_name}'] = cat_hists
            # ---- DATA ----
            data_hists = []
            for sname, srdf in self.samples.items():
                if 'data' not in sname: continue
                thisselection = f'{selection}' #&&(j_sel_btagL_pt20_for_histo_ParTRegMass>5)
                defbranch = f'{branch_name}_toplot'
                data_hists.append(_book(srdf, thisselection, defbranch))
            if data_hists:
                self.temp_hists[hname][f'{hname}_data'] = data_hists

            # ---- bstautau signal ----
            sig_hists = []
            for sname, srdf in self.samples.items():
                if 'bstautau' not in sname: continue
                thisselection = f'{selection}&&(j_sel_btagL_pt20_for_histo_signalBs_mask==1)'#&&(j_sel_btagL_pt20_for_histo_ParTRegMass>5)
                defbranch = f'{branch_name}_toplot'
                sig_hists.append(_book(srdf, thisselection, defbranch))
            if sig_hists:
                self.temp_hists[hname][f'{hname}_bstautau'] = sig_hists

            if verbose:
                print(f" [PlottingKit|flavor] '{hname}': {{k: len(v) for k, v in self.temp_hists[hname].items()}}")
   

    # 2. PROCESS HISTOGRAMS
    def compute_ratio(self, denom, num):
        """ num/denom ratio histogram, accepting either a THStack (uses its total) or a plain TH1 """
        h_denom = denom.GetStack().Last().Clone() if isinstance(denom, ROOT.THStack) else denom.Clone()
        h_num   = num.GetStack().Last().Clone() if isinstance(num, ROOT.THStack) else num.Clone()

        h_num.Divide(h_denom)
        return h_num

    def get_mc_total(self, stack):
        """ MC total histogram (with combined stat errors), built from a THStack """
        return stack.GetStack().Last().Clone() if isinstance(stack, ROOT.THStack) else stack.Clone()

    def _style_stat_band(self, h):
        """ solid, semi-transparent stat-uncertainty band - a sparse hatch (3344) reads
        too faint at typical pad sizes, this is much easier to spot at a glance """
        h.SetFillColorAlpha(ROOT.kBlack, 0.50)
        h.SetFillStyle(3004)
        h.SetMarkerSize(0)
        h.SetLineWidth(0)
        return h

    def get_stat_unc(self, stack):
        """ 
        MC stat-uncertainty band around 1, built from a THStack's total.
        """
        h_total = self.get_mc_total(stack)
        band = h_total.Clone()
        for i in range(1, band.GetNbinsX() + 1):
            content = h_total.GetBinContent(i)
            rel_err = h_total.GetBinError(i) / content if content != 0 else 0.
            band.SetBinContent(i, 1.)
            band.SetBinError(i, rel_err)
        return self._style_stat_band(band)

    def _draw_and_save_stack(self, hname, xlabel, ytitle, logscale, mc_stack, data_stck, signal_h, scaled_signal_h, leg, scratch):
        """ 
        Shared drawing/saving for one histogram's stack
        """
        scratch.cd()
        scratch.Clear()
        mc_stack.Draw("hist") # important to get axis info

        has_data_hist = bool(data_stck.GetHists() and data_stck.GetHists().GetSize() > 0)
        if has_data_hist:
            data_stck.Draw("hist same") # same - data_stck needs this too, or GetStack() below comes back empty
        has_data = has_data_hist and bool(data_stck.GetStack() and data_stck.GetStack().Last())

        self.save_toROOT(hname, mc_stack, data_stck)

        max_y = 1
        if mc_stack.GetStack() and mc_stack.GetStack().Last():
            max_y = max(max_y, mc_stack.GetStack().Last().GetMaximum())
        if has_data:
            max_y = max(max_y, data_stck.GetStack().Last().GetMaximum())
        if signal_h is not None:
            max_y = max(max_y, signal_h.GetMaximum())
        max_y *= self.y_headroom_log if logscale else self.y_headroom_lin

        x_min = mc_stack.GetXaxis().GetXmin()
        x_max = mc_stack.GetXaxis().GetXmax()

        # create canvas
        c = cms.cmsDiCanvas(f"c_{self.channel}_{hname}",
                            x_min = x_min, x_max = x_max,
                            y_min = 0., y_max = max_y,
                            r_min = 0.6, r_max = 1.4,
                            nameXaxis = xlabel, nameYaxis = ytitle, nameRatio = "Data/MC",
                            square = False, iPos=11, extraSpace=0, scaleLumi=1
        )

        # --- main pad ---
        c.cd(1)
        #mc_stack.Draw("HIST same")
        cms.cmsObjectDraw(mc_stack, "HIST SAME")
        if mc_stack.GetStack() and mc_stack.GetStack().Last():
            mc_stat_band = self._style_stat_band(mc_stack.GetStack().Last().Clone(f"{hname}_mc_statband"))
            mc_stat_band.Draw("E2 same")
        if has_data:
            data_stck.GetStack().Last().Draw("EP same")
        if signal_h is not None:
            cms.cmsDraw(scaled_signal_h, "HIST same",
                        msize=0,
                        lwidth=2, lcolor= scaled_signal_h.GetLineColor(), lstyle=ROOT.kSolid,
                        fstyle=0, fcolor=0
                        )
        leg.Draw("same")

        # --- ratio pad ---
        c.cd(2)
        line = ROOT.TLine(x_min, 1., x_max, 1.)
        line.SetLineColor(ROOT.kBlack)
        line.SetLineStyle(ROOT.kDashed)

        # (S+B)/B
        if signal_h is not None:
            sb_pred = signal_h.Clone(f"{hname}_sb_pred")
            sb_pred.Add(self.get_mc_total(mc_stack))
            sb_ratio = self.compute_ratio(mc_stack, sb_pred)
            cms.cmsDraw(sb_ratio, "HIST", lcolor=sb_ratio.GetLineColor(), lwidth=2, lstyle=ROOT.kDashed, fstyle=0)
        line.Draw("same")

        # DATA/MC
        if has_data:
            stat_band = self.get_stat_unc(mc_stack)
            stat_band.Draw("E2 same")

            ratio_h = self.compute_ratio(mc_stack, data_stck)
            ratio_h.SetMarkerStyle(20)
            ratio_h.Draw("EP same")

        self.save_plot_version(c, hname)
        c.Close()

    def process_histograms(self):

        # scratch canvas used only to force THStack to build its internal axis/maximum
        # reused across histograms so it never leaks or collides with the saved canvases
        scratch = ROOT.TCanvas(f"c_{self.channel}_scratch", "", 10, 10)

        try:
            # loop on histograms templates
            for i, (hname, hinfo) in enumerate(self.config_hists.items()):
                print(f" [PlottingKit] ({i+1}/{len(self.config_hists)}) - {hname} ...")

                branch_name, selection, isjet_based, h_model, xlabel, logscale = hinfo
                ytitle = "Jets" if isjet_based else "Events"

                # apply style to histograms
                self.apply_style(hname, xlabel, ytitle)

                # create legend with unique sample names (data, MC, signal)
                leg                 = self.create_legend(hname)

                # stack
                mc_stack, data_stck, signal_h, scaled_signal_h  = self.create_stack(hname)

                self._draw_and_save_stack(hname, xlabel, ytitle, logscale, mc_stack, data_stck, signal_h, scaled_signal_h, leg, scratch)

        finally:
            scratch.Close()
            self.close_root_file()

    def process_flavor_histograms(self):
        """ Flavor-based counterpart to process_histograms: same drawing body
        (_draw_and_save_stack), but legend/stack come from the flavor-aware helpers
        and event-based histograms (nothing booked by initialize_flavor_histograms)
        are skipped entirely. """
        scratch = ROOT.TCanvas(f"c_{self.channel}_scratch_flavor", "", 10, 10)

        try:
            for i, (hname, hinfo) in enumerate(self.config_hists.items()):
                branch_name, selection, isjet_based, h_model, xlabel, logscale = hinfo

                if not isjet_based:
                    if self._debug: print(f" [PlottingKit|flavor] skip '{hname}': event-based, nothing booked")
                    continue

                print(f" [PlottingKit|flavor] ({i+1}/{len(self.config_hists)}) - {hname} ...")

                self.apply_style(hname, xlabel, "Jets") # here histograms list get merged
                leg = self.create_legend(hname, (0.45, 0.65, 0.95, 0.90))
                mc_stack, data_stck, signal_h, scaled_signal_h = self.create_flavor_stack(hname)

                self._draw_and_save_stack(hname, xlabel, "Jets", logscale, mc_stack, data_stck, signal_h, scaled_signal_h, leg, scratch)

        finally:
            scratch.Close()
            self.close_root_file()

# -------------------------------
    
    def run(self, debug=False):
        self.setup_output_directory()
        if self._flavor_based:
            self.initialize_flavor_histograms()
            self.process_flavor_histograms()
        else:
            self.initialize_histograms()
            self.process_histograms()

        self.temp_hists.clear()



# ------ plotting_kit class