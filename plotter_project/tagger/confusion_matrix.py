"""
Jet-level confusion matrix for the UParT tagger.

For each jet in the `j_sel_btagL_pt20_for_histo` collection, the tagger
prediction is the argmax of 4 scores:
    - ParTRawTauhtauh                                       -> tauhtauh
    - ParTRawTauhtaumu                                      -> tauhtaumu
    - ParTRawTauhtaue                                       -> tauhtaue
    - ParTRawB + ParTRawC + ParTRawOther + ParTRawSingletau  -> bkg

A second matrix uses the same 4 true classes but only 3 prediction
classes, picking the argmax among the 3 signal scores alone (no bkg
score in the race) -- i.e. every jet, including true bkg jets, is
forced into one of {tauhtauh, tauhtaumu, tauhtaue}.

The truth label comes from the gen-matched decay-mode masks (only filled for the bstautau sample):
    - {jb}_signalBsTauhh_mask   -> tauhtauh
    - {jb}_signalBsTauhmu_mask  -> tauhtaumu
    - {jb}_signalBsTauhe_mask   -> tauhtaue
Any jet not matched to one of those (background samples, or extra jets
in the signal sample not matched to the Bs decay) is truth bkg.
"""

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gErrorIgnoreLevel = ROOT.kWarning
ROOT.gStyle.SetPalette(ROOT.kViridis)  # same 2D palette as SetCMSPalette() in histo_toolkit/bstautau_cmsstyle.py

import os, sys
import argparse

import data_toolkit as data

CLASSES             = ['tauhtauh', 'tauhtaumu', 'tauhtaue', 'bkg']
CLASS_LABELS        = ['#tau_{h}#tau_{h}', '#tau_{h}#tau_{#mu}', '#tau_{h}#tau_{e}', 'bkg']
N_CLASSES           = len(CLASSES)

# 3-way "signal-only" prediction: argmax among the 3 signal scores alone (no bkg score)
SIGNAL_CLASSES       = CLASSES[:3]
SIGNAL_CLASS_LABELS  = CLASS_LABELS[:3]
N_SIGNAL_CLASSES     = len(SIGNAL_CLASSES)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Jet-level confusion matrix for the UParT tagger")
    parser.add_argument('--input', '-i', default=None,
                         help=".yml file with the input ntuple locations (same format as plotter_project/main.py). "
                              "If not given, --indir is used instead.")
    parser.add_argument('--indir', default=None,
                         help="Input directory with the skimmed+SF-applied ntuples for --channel "
                              "(defaults to the standard tagMreg-v0 sfs_applied path)")
    parser.add_argument('--channel', default='emu', choices=data.samples.channels, help='Channel to process')
    parser.add_argument('--year', default='2018', choices=data.samples.years, help='Year of data taking')
    parser.add_argument('--outdir', default='plots/confusion_matrix', help='Output directory for plots')
    parser.add_argument('--test', action='store_true', help='Run only on ttbar fully-leptonic + signal, for a quick test')
    return parser.parse_args()


def define_predicted_class(rdf, jb):
    """Predicted class per jet = argmax(tauhtauh, tauhtaumu, tauhtaue, bkg_score)."""
    rdf = rdf.Define(f"{jb}_bkg_score",
                      f"{jb}_ParTRawB + {jb}_ParTRawC + {jb}_ParTRawOther + {jb}_ParTRawSingletau")
    rdf = rdf.Define(f"{jb}_pred_class", f"""
        ROOT::RVec<double> s0 = {jb}_ParTRawTauhtauh;
        ROOT::RVec<double> s1 = {jb}_ParTRawTauhtaumu;
        ROOT::RVec<double> s2 = {jb}_ParTRawTauhtaue;
        ROOT::RVec<double> s3 = {jb}_bkg_score;
        ROOT::VecOps::RVec<int> pred(s0.size());
        for (size_t i = 0; i < s0.size(); ++i) {{
            std::array<double, 4> scores = {{s0[i], s1[i], s2[i], s3[i]}};
            pred[i] = std::distance(scores.begin(), std::max_element(scores.begin(), scores.end()));
        }}
        return pred;
    """)
    return rdf


def define_predicted_signalonly_class(rdf, jb):
    """Predicted class per jet, 3-way: argmax(tauhtauh, tauhtaumu, tauhtaue) only (no bkg score)."""
    rdf = rdf.Define(f"{jb}_pred_signalonly_class", f"""
        ROOT::RVec<double> s0 = {jb}_ParTRawTauhtauh;
        ROOT::RVec<double> s1 = {jb}_ParTRawTauhtaumu;
        ROOT::RVec<double> s2 = {jb}_ParTRawTauhtaue;
        ROOT::VecOps::RVec<int> pred(s0.size());
        for (size_t i = 0; i < s0.size(); ++i) {{
            std::array<double, 3> scores = {{s0[i], s1[i], s2[i]}};
            pred[i] = std::distance(scores.begin(), std::max_element(scores.begin(), scores.end()));
        }}
        return pred;
    """)
    return rdf


def define_truth_class(rdf, jb, is_signal):
    """Truth class per jet: 0=tauhtauh, 1=tauhtaumu, 2=tauhtaue, 3=bkg."""
    if is_signal:
        rdf = rdf.Define(f"{jb}_truth_class", f"""
            ROOT::RVec<int> is_h  = {jb}_signalBsTauhh_mask;
            ROOT::RVec<int> is_mu = {jb}_signalBsTauhmu_mask;
            ROOT::RVec<int> is_e  = {jb}_signalBsTauhe_mask;
            ROOT::VecOps::RVec<int> truth(is_h.size(), 3);
            for (size_t i = 0; i < is_h.size(); ++i) {{
                if      (is_h[i])  truth[i] = 0;
                else if (is_mu[i]) truth[i] = 1;
                else if (is_e[i])  truth[i] = 2;
            }}
            return truth;
        """)
    else:
        rdf = rdf.Define(f"{jb}_truth_class", f"ROOT::VecOps::RVec<int>({jb}_pt.size(), 3)")
    return rdf


def row_normalize(h):
    """Normalize each truth row (x-axis) to 1, so cells read as the fraction
    of true-class jets predicted as a given class."""
    hnorm = h.Clone(h.GetName() + "_norm")
    nx, ny = h.GetNbinsX(), h.GetNbinsY()
    for ix in range(1, nx + 1):
        row_sum = sum(h.GetBinContent(ix, iy) for iy in range(1, ny + 1))
        for iy in range(1, ny + 1):
            val = h.GetBinContent(ix, iy) / row_sum if row_sum > 0 else 0.
            hnorm.SetBinContent(ix, iy, val)
            hnorm.SetBinError(ix, iy, 0.)
    return hnorm


def draw_cell_text(h, zmin, zmax, fmt="{:.2f}"):
    """Draw the bin content of each cell, picking white/black text depending on
    how bright the underlying palette colour is at that bin's value (so labels
    stay readable on both the dark and the light end of the Viridis palette)."""
    texts = []
    frac_threshold = 0.55  # Viridis gets visually bright above ~55% of its range
    for ix in range(1, h.GetNbinsX() + 1):
        for iy in range(1, h.GetNbinsY() + 1):
            val = h.GetBinContent(ix, iy)
            frac = (val - zmin) / (zmax - zmin) if zmax > zmin else 0.
            text_color = ROOT.kBlack if frac > frac_threshold else ROOT.kWhite

            t = ROOT.TText(h.GetXaxis().GetBinCenter(ix), h.GetYaxis().GetBinCenter(iy), fmt.format(val))
            t.SetTextAlign(22)
            t.SetTextFont(42)
            t.SetTextSize(0.035)
            t.SetTextColor(text_color)
            t.Draw("same")
            texts.append(t)  # keep alive until the canvas is saved
    return texts


def style_and_draw(h, outpath, label, x_labels=CLASS_LABELS, y_labels=CLASS_LABELS,
                    y_title='predicted jet class (argmax score)', zmax=None):
    c = ROOT.TCanvas(f"c_{h.GetName()}", "", 900, 800)
    c.SetLeftMargin(0.16)
    c.SetBottomMargin(0.14)
    c.SetRightMargin(0.18)
    c.SetTopMargin(0.08)

    for ic, cl in enumerate(x_labels):
        h.GetXaxis().SetBinLabel(ic + 1, cl)
    for ic, cl in enumerate(y_labels):
        h.GetYaxis().SetBinLabel(ic + 1, cl)
    h.GetXaxis().SetTitle('true jet class')
    h.GetYaxis().SetTitle(y_title)
    h.GetXaxis().SetLabelSize(0.045)
    h.GetYaxis().SetLabelSize(0.045)
    h.GetXaxis().SetTitleOffset(1.4)
    h.GetYaxis().SetTitleOffset(1.6)
    if zmax is not None:
        h.SetMinimum(0.)
        h.SetMaximum(zmax)

    zlo = 0.
    zhi = zmax if zmax is not None else h.GetMaximum()
    h.Draw("COLZ")
    texts = draw_cell_text(h, zlo, zhi)  # noqa: F841 (kept alive for the canvas lifetime)

    info = ROOT.TLatex()
    info.SetNDC()
    info.SetTextFont(42)
    info.SetTextSize(0.035)
    info.DrawLatex(0.16, 0.02, label)

    c.SaveAs(outpath.format(ext='png'))
    c.SaveAs(outpath.format(ext='pdf'))


if __name__ == "__main__":
    args = parse_arguments()
    ch, year = args.channel, args.year

    if args.input:
        in_info = data.samples.parse_inyml(args.input)
        indir   = in_info.get('MC', {}).get('inpath_template_wsfs', '').format(channel=ch)
    elif args.indir:
        indir = args.indir
    else:
        indir = f'/eos/cms/store/group/phys_bphys/cbasile/BsTauTau-ttbar/nanov15_skim/{ch}_{year}_tagMreg-v0/sfs_applied'

    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    used_mc_samples_names = ['tt_fullylep', 'bstautau'] if args.test else data.samples.mc_samples_names
    print(f" > channel {ch}, year {year}")
    print(f" > input dir: {indir}")
    print(f" > samples: {used_mc_samples_names}")

    mc_samples = data.ioutils.load_mc_samples(
        indir, used_mc_samples_names, year,
        data.samples.files_names, 'Events',
        nevents=None,
        norm_to_xsec=False,  # ntuples already carry norm_weight from the corrections step
    )

    jb = 'j_sel_btagL_pt20_for_histo'  # jet collection used for analysis histograms

    h_model     = ROOT.RDF.TH2DModel('confusion_matrix', '', N_CLASSES, 0, N_CLASSES, N_CLASSES, 0, N_CLASSES)
    h_model_sig = ROOT.RDF.TH2DModel('confusion_matrix_signalonly', '', N_CLASSES, 0, N_CLASSES, N_SIGNAL_CLASSES, 0, N_SIGNAL_CLASSES)

    h_cm, h_cm_sigonly = None, None
    for name, rdf in mc_samples.items():
        is_bstautau = 'bstautau' in name
        print(f" ------ {name} {'(signal)' if is_bstautau else ''}")

        rdf = rdf.Define('tot_weight', data.defutils.build_weight_string(ch, sf=True, btag_sfs=True))
        rdf = define_predicted_class(rdf, jb)
        rdf = define_predicted_signalonly_class(rdf, jb)
        rdf = define_truth_class(rdf, jb, is_bstautau)

        h_sample = rdf.Histo2D(h_model, f"{jb}_truth_class", f"{jb}_pred_class", "tot_weight").GetValue()
        if h_cm is None:
            h_cm = h_sample.Clone("confusion_matrix")
        else:
            h_cm.Add(h_sample)

        h_sample_sig = rdf.Histo2D(h_model_sig, f"{jb}_truth_class", f"{jb}_pred_signalonly_class", "tot_weight").GetValue()
        if h_cm_sigonly is None:
            h_cm_sigonly = h_sample_sig.Clone("confusion_matrix_signalonly")
        else:
            h_cm_sigonly.Add(h_sample_sig)

    h_norm         = row_normalize(h_cm)
    h_norm_sigonly = row_normalize(h_cm_sigonly)

    # --- save & plot ---
    outroot = os.path.join(outdir, f"confusion_matrix_{ch}_{year}.root")
    f_out = ROOT.TFile(outroot, 'RECREATE')
    h_cm.Write("confusion_matrix_counts")
    h_norm.Write("confusion_matrix_normalized")
    h_cm_sigonly.Write("confusion_matrix_signalonly_counts")
    h_norm_sigonly.Write("confusion_matrix_signalonly_normalized")
    f_out.Close()
    print(f" > histograms saved to {outroot}")

    label = f"{data.samples.ch_labels.get(ch, ch)}  {year}"
    style_and_draw(
        h_cm.Clone("confusion_matrix_counts_draw"),
        os.path.join(outdir, f"confusion_matrix_{ch}_{year}_counts.{{ext}}"),
        label,
    )
    style_and_draw(
        h_norm.Clone("confusion_matrix_normalized_draw"),
        os.path.join(outdir, f"confusion_matrix_{ch}_{year}_normalized.{{ext}}"),
        label,
        zmax=1.,
    )
    style_and_draw(
        h_cm_sigonly.Clone("confusion_matrix_signalonly_counts_draw"),
        os.path.join(outdir, f"confusion_matrix_{ch}_{year}_signalonly_counts.{{ext}}"),
        label,
        y_labels=SIGNAL_CLASS_LABELS,
        y_title='predicted jet class (argmax signal score)',
    )
    style_and_draw(
        h_norm_sigonly.Clone("confusion_matrix_signalonly_normalized_draw"),
        os.path.join(outdir, f"confusion_matrix_{ch}_{year}_signalonly_normalized.{{ext}}"),
        label,
        y_labels=SIGNAL_CLASS_LABELS,
        y_title='predicted jet class (argmax signal score)',
        zmax=1.,
    )
    print(f" > plots saved to {outdir}")
