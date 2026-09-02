import ROOT
ROOT.gROOT.SetBatch()   
ROOT.gStyle.SetOptStat(0)
ROOT.gErrorIgnoreLevel = ROOT.kWarning
#import cmsstyle as cms

import os, sys
import array
import numpy as np

import data_toolkit as data
import utils as utagger
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import histo_toolkit as htools



if __name__ == "__main__":
    
    year = str(2018)
    ch = 'emu'
    used_mc_samples_names = ['tt_fullylep', 'tt_semilep', 'tt_had', 'bstautau', 'bstautauext']
    signal_factor = 20 # multiply signal for plotting
    outdir = "/eos/user/c/cbasile/www/BsTauTau-ttbar/tagger/diTau_tagMreg-v0/cutbase_wp/{channel}_{year}".format(channel=ch, year=year)
    if not os.path.exists(outdir):
        os.makedirs(outdir)


    mc_samples = data.ioutils.load_mc_samples(
        '/eos/cms/store/group/phys_bphys/cbasile/BsTauTau-ttbar/nanov15_skim/{channel}_2018_test_tagMregV0/sfs_applied'.format(channel=ch),
        used_mc_samples_names,
        year,
        data.samples.files_names,
        'Events',
        nevents = None,
        norm_to_xsec=False # should be already normalized.
    )

    anajet_branch = 'j_sel_btagL_pt20_for_histo'
    tau_scores = ['ParTRawTauhtauh', 'ParTRawTauhtaumu', 'ParTRawTauhtaue']
    bkg_scores = ['ParTRawB', 'ParTRawC', 'ParTRawOther', 'ParTRawSingletau']
    parT_scores = tau_scores + bkg_scores
    
    tagger_thresholds = {
        f'{anajet_branch}_part_all_sig_frac' : {
            'ref_var_label' : "#tau_{h}#tau_{x} score fraction",
            'thresholds': np.linspace(0.1, 0.9, 17).tolist(),
            'side': '>',
            'test_var' : f'{anajet_branch}_ParTRegMass',
            'test_var_label' : "m_{j}^{UParT}",
            'template': ROOT.RDF.TH1DModel(f'{anajet_branch}_ParTRegMass', "", 40, 0, 20),
        },
        f'{anajet_branch}_ParTRegMass' : {
            'ref_var_label' : "m_{j}^{UParT}",
            'thresholds': np.linspace(2.0, 17., 31).tolist(),
            'side': '<',
            'test_var' : f'{anajet_branch}_part_all_sig_frac',
            'test_var_label' : "#tau_{h}#tau_{x} score fraction",
            'template': ROOT.RDF.TH1DModel(f'{anajet_branch}_part_all_sig_frac', "", 20, 0, 1.),
        }
    }
    histos = dict()
    for cutvar, params in tagger_thresholds.items():
        for th in params['thresholds']:
            histos[f'{cutvar}_{th:.2f}'] = dict()

    print(f"\n------ PREPARE PLOTS ------")   
    for name, rdf in mc_samples.items():
        print(f"\n------ {name} ------")
        _is_bstautau_ = 'bstautau' in name

        # define tagger combined scores
        mc_samples[name] = utagger.part_scores_functions.define_combined_scores(mc_samples[name], 
                                                                                anajet_branch,
                                                                                tau_scores, parT_scores, bkg_scores, 
                                                                                is_bstautau=False, #'bstautau' in name, # FIXME: adjust mask
                                                                                bstautau_masks=None
                                                                                )

        for cutvar, params in tagger_thresholds.items():
            xvar = params['test_var']
            print(f" - {cutvar} {params['side']} {params['thresholds']}")
            for th in params['thresholds']:
                mask_expr = f"({cutvar} {params['side']} {th})" 
                if _is_bstautau_ : mask_expr = f"{mask_expr} && ({anajet_branch}_signalBs_mask)"

                histos[f'{cutvar}_{th:.2f}'][name] = mc_samples[name].Define('mask', mask_expr).Define('sel_jets', f"{xvar}[mask]").Histo1D(params['template'], 'sel_jets', 'norm_weight')

    # ----- PLOTTING -----
    print(f"\n------ PLOTTING ------")
    summary_results = dict()  # cutvar -> list of (threshold, max S/sqrt(S+B)) 
    for cutvar, params in tagger_thresholds.items():
        xvar = params['test_var']
        summary_results[cutvar] = []
        for th in params['thresholds']:
            
            sig_stk = ROOT.THStack(f"stk_{cutvar}_{th:.2f}", "")
            bkg_stk = ROOT.THStack(f"stk_{cutvar}_{th:.2f}", "")
            for name, histo in histos[f'{cutvar}_{th:.2f}'].items():
                is_bstautau = 'bstautau' in name
            
                htools.plotting_utils.set_histogram_style(
                    histo,
                    x_title = params['test_var_label'],
                    y_title = "Jets",
                    fill_color = data.samples.colours.get(name, ROOT.kBlack) if not is_bstautau else 0, 
                    line_color = data.samples.colours.get(name, ROOT.kBlack)
                )
                if 'bstautau' in name:
                    sig_stk.Add(histo.GetValue())
                else:
                    bkg_stk.Add(histo.GetValue())
            # merge signal histograms into one    
            sig_h = sig_stk.GetStack().Last().Clone()
            bkg_h = bkg_stk.GetStack().Last().Clone()


            # ----- significance histogram: S / sqrt(S+B) -----
            sig_over_sqrt = sig_h.Clone(f"sOverSqrtSB_{cutvar}_{th:.2f}")
            sig_over_sqrt.Reset()
            max_sig, s_tot, b_tot, tot_sig = 0., 0., 0., 0.
            for ibin in range(1, sig_h.GetNbinsX() + 1):
                s = sig_h.GetBinContent(ibin)
                b = bkg_h.GetBinContent(ibin)
                denom = (s + b) ** 0.5
                val = s / denom if denom > 0 else 0.
                sig_over_sqrt.SetBinContent(ibin, val)
                max_sig = max(max_sig, val)
                #s_tot += s
                #b_tot += b
                tot_sig += val**2
                sig_over_sqrt.SetBinError(ibin, 0.)
            tot_sig = tot_sig**0.5#s_tot / ((s_tot + b_tot) ** 0.5) if (s_tot + b_tot) > 0 else 0.
            sig_over_sqrt.SetLineColor(ROOT.kBlack)
            sig_over_sqrt.SetFillColor(0)
            sig_over_sqrt.SetTitle(f";{params['test_var_label']};S/#sqrt{{S+B}}")
            
            #summary_results[cutvar].append((th, max_sig))
            summary_results[cutvar].append((th, tot_sig))


            # legend
            leg = ROOT.TLegend(0.7, 0.7, 0.9, 0.9)
            leg.SetBorderSize(0)
            leg.SetFillStyle(0)
            for name, histo in histos[f'{cutvar}_{th:.2f}'].items():
                if 'bstautau' in name: continue
                leg.AddEntry(histo.GetValue(), name, "f")
            leg.AddEntry(sig_h, "Bs#rightarrow#tau_{h}#tau_{x}#times"+f" {signal_factor:.0f}", "f")
            sig_h.Scale(signal_factor)

            # info text
            info_text = ROOT.TLatex()
            info_text.SetNDC()
            info_text.SetTextSize(0.05)
            info_text.SetTextFont(42)

            y_max = 1.5*max(sig_h.GetMaximum(), bkg_h.GetMaximum())
            bkg_stk.SetMaximum(y_max)
            bkg_stk.SetTitle(f";{params['test_var_label']}; Jets")

            # drawing histograms
            c = ROOT.TCanvas(f"c_{xvar}_{cutvar}_{th:.2f}", "", 1000, 900)
 
            pad_top = ROOT.TPad(f"pad_top_{cutvar}_{th:.2f}", "", 0, 0.3, 1, 1.0)
            pad_top.SetBottomMargin(0.02)
            pad_top.Draw()
 
            pad_bot = ROOT.TPad(f"pad_bot_{cutvar}_{th:.2f}", "", 0, 0.0, 1, 0.3)
            pad_bot.SetTopMargin(0.03)
            pad_bot.SetBottomMargin(0.35)
            pad_bot.Draw()
 
            pad_top.cd()
            bkg_stk.Draw("hist")
            bkg_stk.GetXaxis().SetLabelSize(0)
            bkg_stk.GetXaxis().SetTitleSize(0)
            sig_h.Draw("hist same")
            leg.Draw()
            info_text.DrawLatex(0.25, 0.85, f"{ch} {year}")
            info_text.DrawLatex(0.25, 0.8, f"{params['ref_var_label']}{params['side']}{th:.2f}")
 
            pad_bot.cd()
            sig_over_sqrt.GetYaxis().SetTitleSize(0.11)
            sig_over_sqrt.GetYaxis().SetTitleOffset(0.4)
            sig_over_sqrt.GetYaxis().SetLabelSize(0.09)
            sig_over_sqrt.GetYaxis().SetNdivisions(505)
            sig_over_sqrt.GetXaxis().SetTitleSize(0.13)
            sig_over_sqrt.GetXaxis().SetLabelSize(0.11)
            sig_over_sqrt.GetXaxis().SetTitleOffset(1.1)
            sig_over_sqrt.SetMinimum(0.)
            sig_over_sqrt.SetMaximum(7.5)
            sig_over_sqrt.Draw("hist")
 
            c.cd()
            basename = os.path.join(outdir, f"{xvar}_{cutvar}-{th:.2f}")
            c.SaveAs(f"{basename}.png")
            c.SaveAs(f"{basename}.pdf")
        # < loop over thresholds

        # ----- summary plot: threshold on cutvar VS max S/sqrt(S+B) -----
        ths, max_sigs = zip(*summary_results[cutvar])
        ths_arr = array.array('d', ths)
        max_sigs_arr = array.array('d', max_sigs)
 
        gr_summary = ROOT.TGraph(len(ths_arr), ths_arr, max_sigs_arr)
        gr_summary.SetTitle(f";{params['ref_var_label']} threshold; #sum(S/#sqrt{{S+B}})^{{2}}")
        gr_summary.SetMarkerStyle(20)
        gr_summary.SetMarkerColor(ROOT.kAzure+2)
        gr_summary.SetLineColor(ROOT.kAzure+2)
        gr_summary.SetLineWidth(2)
        gr_summary.GetYaxis().SetTitleOffset(1.0)
        gr_summary.GetYaxis().SetRangeUser(4., 15.)
        
        c_summary = ROOT.TCanvas(f"c_summary_{cutvar}", "", 800, 600)
        gr_summary.Draw("APL")
 
        info_text.DrawLatex(0.25, 0.85, f"{ch} {year}")
        c_summary.SetGrid()
        c_summary.Update()
        basename = os.path.join(outdir, f"summary_{cutvar}")
        c_summary.SaveAs(f"{basename}.png")
        c_summary.SaveAs(f"{basename}.pdf")
        
    # < loop over cutvar
        
