"""
    
"""

import ROOT
ROOT.gROOT.SetBatch(True)
RStyle = ROOT.gStyle
RStyle.SetPadLeftMargin(0.10)
RStyle.SetTitleOffset(1.1, "Y")
RStyle.SetPadRightMargin(0.20)
RStyle.SetPadGridX(1)
RStyle.SetPadGridY(1)

import sys, os


channel_label = {
    'emu': 'e#mu',
    'mumu': '#mu#mu',
    'ee': 'ee',
    'e' : 'e',
    'mu': '#mu',
}

channel_colors = {
    'emu'  : ROOT.kGreen + 2,
    'mumu' : ROOT.kBlue + 1,
    'ee'   : ROOT.kRed + 1,
    'e'    : ROOT.kOrange + 1,
    'mu'   : ROOT.kViolet + 1,
}


if __name__ == "__main__":

    var_name = "roc_{channel}_btagged_loose_jets_pt_above_20_for_histo_part_all_sig_frac"
    input_ref  = {
        "file" : "/eos/user/c/cbasile/www/BsTauTau-ttbar/tagger/ref-VS-UParTedgeV0/plots_ref/roc_curves.root",
        "label": "ParT-weaver",
    }
    ref_file = ROOT.TFile(input_ref["file"])
    input_test = {
        "file" : "/eos/user/c/cbasile/www/BsTauTau-ttbar/tagger/ref-VS-UParTedgeV0/plots_UParTedge-v0/roc_curves.root",
        "label": "UParT b-hive"
    }
    test_file = ROOT.TFile(input_test["file"])
    channels = ["emu", "mumu", "ee", "e", "mu"]
    
    tot_canvas = ROOT.TCanvas(f"canvas_tot", f"", 900, 800) 
    tot_leg = ROOT.TLegend(0.81, 0.50, 1., 0.9)
    tot_leg.SetBorderSize(0)
    
    keep_alive = []   # stop Python from deleting objects the legend points to

    # line-style entries: dashed = ref, solid = test
    style_ref = ROOT.TGraph()
    style_ref.SetLineStyle(ROOT.kDashed)
    style_ref.SetLineWidth(2)
    style_ref.SetLineColor(ROOT.kBlack)
    style_test = ROOT.TGraph()
    style_test.SetLineStyle(ROOT.kSolid)
    style_test.SetLineWidth(2)
    style_test.SetLineColor(ROOT.kBlack)
    tot_leg.AddEntry(style_ref,  input_ref["label"],  "l")
    tot_leg.AddEntry(style_test, input_test["label"], "l")
    
    keep_alive += [style_ref, style_test]
    
    for i, ch in enumerate(channels):

        var_name_ch     = var_name.format(channel=ch)
        ref_hist        = ref_file.Get(var_name_ch).Clone(f"ref_hist_{ch}")
        test_hist       = test_file.Get(var_name_ch).Clone(f"test_hist_{ch}")

        if not ref_hist or not test_hist:
            print(f"Histograms for channel {ch} not found in the input files.")
            continue

        # Create a canvas to draw the histograms
        canvas = ROOT.TCanvas(f"canvas_{ch}", f"", 800, 800)
        ref_hist.SetLineColor(channel_colors.get(ch, ROOT.kBlue))
        ref_hist.SetLineWidth(2)
        ref_hist.SetLineStyle(ROOT.kDashed)
        test_hist.SetLineColor(channel_colors.get(ch, ROOT.kRed))
        test_hist.SetLineWidth(2)

        ref_hist.GetXaxis().SetTitle('Signal efficiency')
        ref_hist.GetYaxis().SetTitle('Background rejection (1 - #varepsilon_{B})')
        ref_hist.GetXaxis().SetLimits(0, 1)
        ref_hist.GetHistogram().SetMaximum(1)
        ref_hist.GetHistogram().SetMinimum(0)
        ref_hist.Draw("") 
        test_hist.Draw("SAME")

        legend = ROOT.TLegend(0.65, 0.8, 0.9, 0.9)
        legend.SetBorderSize(0)

        legend.AddEntry(ref_hist, input_ref["label"] + f" ({channel_label.get(ch, ch)})", "l")
        legend.AddEntry(test_hist, input_test["label"] + f" ({channel_label.get(ch, ch)})", "l")
        legend.Draw()

        canvas.SaveAs(f"ROC_{input_ref['label'].replace(' ', '_')}-VS-{input_test['label'].replace(' ', '_')}_{ch}.png")
        canvas.SaveAs(f"ROC_{input_ref['label'].replace(' ', '_')}-VS-{input_test['label'].replace(' ', '_')}_{ch}.pdf")
        canvas.Close()

        tot_canvas.cd()
        if i == 0 : ref_hist.Draw("") 
        else : ref_hist.Draw("same") 
        test_hist.Draw("same")
        tot_leg.AddEntry(test_hist, channel_label.get(ch, ch), "f")

    tot_canvas.cd()
    tot_leg.Draw() 
    tot_canvas.SaveAs(f"ROC_{input_ref['label'].replace(' ', '_')}-VS-{input_test['label'].replace(' ', '_')}.png")
    tot_canvas.SaveAs(f"ROC_{input_ref['label'].replace(' ', '_')}-VS-{input_test['label'].replace(' ', '_')}.pdf")

        