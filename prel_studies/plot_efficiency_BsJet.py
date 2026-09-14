import ROOT
ROOT.gROOT.SetBatch(True)

import argparse
import sys, os
import json

import cmsstyle as cms
cms.setCMSStyle()
cms.SetExtraText("Simulation Preliminary")
cms.SetLumi("")
cms.SetEnergy(13)
cms.ResetAdditionalInfo()
style = cms.getCMSStyle()
style.SetTitleSize(0.05, "X")
style.SetTitleOffset(1.5, "Y")

palette = [
    ROOT.TColor.GetColor("#5790fc"),
    ROOT.TColor.GetColor("#f89c20"),
    ROOT.TColor.GetColor("#e42536"),
    ROOT.TColor.GetColor("#964a8b"),
    ROOT.TColor.GetColor("#9c9ca1"),
]


def get_arguments() :
    argparser = argparse.ArgumentParser(description='Plot the efficiency of Bs-Jet matching')
    argparser.add_argument('--config', type=str,
                           required=True,
                           help='Configuration file')
    return argparser.parse_args()

def style_efficiency(graph, color=ROOT.kBlue, marker=20):
    graph.SetLineColor(color)
    graph.SetMarkerColor(color)
    graph.SetMarkerStyle(marker)
    graph.SetMarkerSize(1.2)
    graph.SetLineWidth(2)

if __name__ == "__main__":
    args = get_arguments()
    with open(args.config, 'r') as f:
        config = json.load(f)

    files   = config.get('infiles', None)
    labels  = config.get('labels', None)
    outdir  = config.get('outdir', None)
    ref     = config.get('ref', None)
    compare = config.get('compare', None)
    extraText = config.get('extraText', None)
    
    # input files
    for f in files:
        if not os.path.isfile(f):
            print(f"File {f} does not exist. Exiting.")
            sys.exit(1)
        print(f" + {f}")

    # output directory
    os.makedirs(outdir, exist_ok=True)

    cms.ResetAdditionalInfo()
    for text in extraText:
        cms.AppendAdditionalInfo(text)

    for clist in compare:
        # legend
        legend = ROOT.TLegend(0.5, 0.8, 0.9, 0.9)
        legend.SetBorderSize(0)
        legend.SetFillStyle(0)
        legend.SetTextFont(42)
        legend.SetTextSize(0.035)
        
        tokeep = [] # keep alive
        i = 0
        for file, label, histo in zip(files, labels, clist):
            print(f"   - {label} {histo[1]} : {file}")
            f = ROOT.TFile(file)
            h_den = f.Get(ref)
            h_num = f.Get(histo[0])
            
        
            g_eff = ROOT.TGraphAsymmErrors(h_num, h_den, "cp")
            g_eff.SetName(f"graph_{histo[0]}_{label}")
            style_efficiency(g_eff, color=palette[i % len(palette)], marker=20)
            tokeep.append(g_eff)
            
            x_lo, x_hi = g_eff.GetXaxis().GetXmin(), g_eff.GetXaxis().GetXmax()
            y_lo, y_hi = 0, 1.4
            
            legend.AddEntry(g_eff, ' '.join([label, histo[1]]), "lp")
            i += 1

        canv = cms.cmsCanvas(f'c_{histo[0]}', 
                             x_lo, x_hi, y_lo, y_hi, 
                             "p^{gen}_{T}(B_{s}) (GeV)", "matched fraction",
                             square=False, 
                             extraSpace=0.0, iPos=11
                            )

        canv.cd()
        for h in tokeep:
            cms.cmsDraw(h, "EP",
                        marker = h.GetMarkerStyle(),
                        msize  = h.GetMarkerSize(),
                        mcolor = h.GetMarkerColor(),
                        lcolor = h.GetLineColor(),
                        lwidth = h.GetLineWidth(),
                        lstyle = h.GetLineStyle(),
                        fstyle = h.GetFillStyle(),
                        fcolor = h.GetFillColor()
                          ) 
        
        legend.Draw()
        canv.SaveAs(os.path.join(outdir, f"efficiency_{histo[0]}.png"))
        canv.SaveAs(os.path.join(outdir, f"efficiency_{histo[0]}.pdf"))