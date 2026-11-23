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
        'j_Mreg'            : [0.,  5.]
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
        cms.ResetAdditionalInfo()
        cms.AppendAdditionalInfo(data.samples.ch_labels[self.channel])

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

        self.root_file_path = os.path.join(self.output_dir, 'histograms.root')
        print(f" [PlottingKit|OUTPUT] + plots directories {self.output_dir} --- {self.channel}")
    
    def unpack_histogram_info(self, hinfo):
        pass

    def save_plot_version(self, canv, outname):
        base_path = os.path.join(self.out_plot_base_path, 'bstautau_scaled', 'lin')
        for fmt in self._out_formats :
            canv.SaveAs(os.path.join(base_path,fmt, f'{outname}.{fmt}'))
    

    def _get_channel_folder(self):
        """ lazily open self.root_file_path once per channel run, cached on the instance
        so every histogram doesn't re-open/re-mkdir the same file (that was silently
        creating duplicate ';2', ';3', ... cycles and risking losing unflushed writes) """
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
            this_hist = hist.GetValue().Clone()
            this_hist.Write(sname)

        # save DATA directly from the original (unblinded) version
        if not self._mc_only:
            data_string = '_'.join([hname, 'data'])
            data_keys = [k for k in self.temp_hists[hname] if data_string in k]
            if data_keys:
                original_data_hist = self.temp_hists[hname][data_keys[0]].GetValue().Clone(f"{hname}_data_original")
                for k in data_keys[1:]:
                    original_data_hist.Add(self.temp_hists[hname][k].GetValue())
                original_data_hist.Write("data_obs")
       

    # ----------- PLOTTING STYLE FUNCTIONS -----------
    def apply_style(self, hname, xtitle, ytitle):
        """ apply style to histos in temp_hists[hname] """
        for key, hist in self.temp_hists[hname].items():
            
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
        
        data_added = False
        for entry in self.samples.keys():
            if 'data' in entry and data_added: continue
            is_signal = 'bstautau' in entry
            leg.AddEntry(
                self.temp_hists[hname][hname+'_'+entry].GetValue(), 
                self.titles.get(entry, entry) + (f' #times{self.signal_scale}' if is_signal and self.signal_scale > 1. else ''), 
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
                if (isjet_based): thisselection +=  '&&(j_sel_btagL_pt20_for_histo_ParTRegMass>5)'
                
                if thisselection == '(1)':
                    self.temp_hists[hname][f'{hname}_{sname}'] = srdf.Histo1D(h_model, branch_name, self.weight_branch)
                else:
                    if isjet_based:
                        #print(f'  > jet-based selection: {selection}')
                        self.temp_hists[hname][f'{hname}_{sname}'] = srdf.Define(f'{branch_name}_toplot', f'{branch_name}[{thisselection}]').Histo1D(h_model, f'{branch_name}_toplot', self.weight_branch)
                    else: #event-based
                        self.temp_hists[hname][f'{hname}_{sname}'] = srdf.Filter(thisselection).Histo1D(h_model, branch_name, self.weight_branch)
            if self._debug: print(self.temp_hists)

    def initialize_flavor_histograms(self, debug=False):
       pass

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

    def process_histograms(self):

        # scratch canvas used only to force THStack to build its internal axis/maximum
        # reused across histograms so it never leaks or collides with the saved canvases
        scratch = ROOT.TCanvas(f"c_{self.channel}_scratch", "", 10, 10)

        try:
            # loop on histograms templates
            for i, (hname, hinfo) in enumerate(self.config_hists.items()):
                print(f" [PlottingKit] ({i+1}/{len(self.config_hists)}) - {hname} ...")

                branch_name, selection, isjet_based, h_model, xlabel, logscale = hinfo

                # apply style to histograms
                self.apply_style(hname, xlabel, "Jets" if isjet_based else "Events")

                # create legend with unique sample names (data, MC, signal)
                leg                 = self.create_legend(hname)

                # stack
                mc_stack, data_stck, signal_h, scaled_signal_h  = self.create_stack(hname)

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
                                    nameXaxis = xlabel, nameYaxis = "Jets" if isjet_based else "Events", nameRatio = "Data/MC",
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

        finally:
            scratch.Close()
            self.close_root_file()

             

            


    
# -------------------------------
    
    def run(self, debug=False):
        self.setup_output_directory()
        self.initialize_histograms()
        self.process_histograms()
        
        self.temp_hists.clear()



# ------ plotting_kit class