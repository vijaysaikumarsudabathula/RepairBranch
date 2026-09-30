#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the RepairBranch IEEE paper by reconstructing document.xml body content
using exact style templates extracted from the user's AgroBranch/EDUGUARD papers.
"""
import re, os, subprocess, shutil
from PIL import Image

BASE = '/home/claude/paper_analysis/unpacked_agro'
FIGDIR = '/home/claude/repairbranch/figures'

# ---------------------------------------------------------------
# Reset BASE from a pristine copy of the original docx every run,
# so this script is safe to re-run while iterating on page count.
# ---------------------------------------------------------------
if os.path.exists(BASE):
    shutil.rmtree(BASE)
os.makedirs(BASE)
subprocess.run(['unzip', '-q', '-o', '/home/claude/paper_analysis/AgroBranch_IEEE_Research_Paper.docx', '-d', BASE], check=True)
# strip any symlinks (untrusted external docx)
subprocess.run(f"find {BASE} -type l -delete", shell=True, check=True)
subprocess.run(['python3', '/mnt/skills/public/docx/scripts/merge_runs.py', BASE], check=True)
print("Reset BASE from pristine AgroBranch docx.")

TNR = 'w:ascii="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"'

def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

# ---------------------------------------------------------------
# Style template functions (exact patterns extracted from source doc)
# ---------------------------------------------------------------

def title_para(text):
    return (f'<w:p><w:pPr><w:spacing w:after="200" w:before="120"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:b/><w:bCs/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def centered_line(text, sz='22', italic=False):
    it = '<w:i/><w:iCs/>' if italic else ''
    return (f'<w:p><w:pPr><w:spacing w:after="20"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/>{it}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def abstract_para(text):
    return (f'<w:p><w:pPr><w:spacing w:after="200"/><w:jc w:val="both"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:b/><w:bCs/><w:i/><w:iCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">Abstract\u2014</w:t></w:r>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def keywords_para(text):
    return (f'<w:p><w:pPr><w:spacing w:after="200"/><w:jc w:val="both"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:b/><w:bCs/><w:i/><w:iCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">Keywords\u2014</w:t></w:r>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:i/><w:iCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

SECTION_BREAK_1COL = ('<w:p><w:pPr><w:sectPr><w:type w:val="continuous"/>'
    '<w:pgSz w:w="12240" w:h="15840" w:orient="portrait"/>'
    '<w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080" w:header="708" w:footer="708" w:gutter="0"/>'
    '<w:pgNumType/><w:cols w:space="720" w:num="1"/><w:docGrid w:linePitch="360"/></w:sectPr></w:pPr></w:p>')

def section_heading(text):
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:after="140" w:before="260"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:b/><w:bCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def subsection_heading(text):
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:after="100" w:before="160"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:b/><w:bCs/><w:i/><w:iCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def body_para(text, after='120'):
    return (f'<w:p><w:pPr><w:spacing w:after="{after}"/><w:jc w:val="both"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def reference_para(text):
    return (f'<w:p><w:pPr><w:spacing w:after="100"/><w:jc w:val="both"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

_docpr_id = [1000]
def image_para(rid, cx, cy):
    _docpr_id[0] += 1
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:after="40" w:before="160"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent t="0" r="0" b="0" l="0"/>'
            f'<wp:docPr id="{_docpr_id[0]}" name="" descr="" title=""/>'
            f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="0" name="" descr=""/>'
            f'<pic:cNvPicPr><a:picLocks noChangeAspect="1" noChangeArrowheads="1"/></pic:cNvPicPr></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}" cstate="none"/><a:srcRect/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr bwMode="auto"><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
            f'</wp:inline></w:drawing></w:r></w:p>')

def caption_para(text):
    return (f'<w:p><w:pPr><w:spacing w:after="200" w:before="60"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def table_caption_para(text):
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:after="200" w:before="60"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def table_note_para(text):
    return (f'<w:p><w:pPr><w:spacing w:after="200" w:before="0"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts {TNR}/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def spacer_para():
    return (f'<w:p><w:pPr><w:spacing w:after="160"/></w:pPr><w:r><w:rPr><w:rFonts {TNR}/>'
            f'<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t xml:space="preserve"/></w:r></w:p>')

def make_table(col_widths, header, rows, table_w=4780):
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)
    def cell(text, w, is_header):
        shd = '<w:shd w:fill="2B6CB0" w:val="clear"/>' if is_header else ''
        color = 'FFFFFF' if is_header else '000000'
        bold = '<w:b/><w:bCs/>' if is_header else '<w:b w:val="false"/><w:bCs w:val="false"/>'
        return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w}"/>{shd}'
                f'<w:tcMar><w:top w:type="dxa" w:w="40"/><w:left w:type="dxa" w:w="60"/><w:bottom w:type="dxa" w:w="40"/><w:right w:type="dxa" w:w="60"/></w:tcMar>'
                f'<w:vAlign w:val="center"/></w:tcPr><w:p><w:pPr><w:jc w:val="left"/></w:pPr>'
                f'<w:r><w:rPr><w:rFonts {TNR}/>{bold}<w:color w:val="{color}"/><w:sz w:val="15"/><w:szCs w:val="15"/></w:rPr>'
                f'<w:t xml:space="preserve">{esc(str(text))}</w:t></w:r></w:p></w:tc>')
    tr_head = '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + ''.join(cell(h, w, True) for h, w in zip(header, col_widths)) + '</w:tr>'
    trs = tr_head
    for row in rows:
        trs += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + ''.join(cell(v, w, False) for v, w in zip(row, col_widths)) + '</w:tr>'
    return (f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="{table_w}"/>'
            f'<w:tblBorders><w:top w:val="single" w:color="auto" w:sz="4"/><w:left w:val="single" w:color="auto" w:sz="4"/>'
            f'<w:bottom w:val="single" w:color="auto" w:sz="4"/><w:right w:val="single" w:color="auto" w:sz="4"/>'
            f'<w:insideH w:val="single" w:color="auto" w:sz="4"/><w:insideV w:val="single" w:color="auto" w:sz="4"/></w:tblBorders></w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>{trs}</w:tbl>')

def algorithm_box(title, lines):
    """Bordered single-cell table containing monospace pseudocode -- styled like a table
    (reuses the paper's own table-border convention) but with a Courier New body."""
    mono = 'w:ascii="Courier New" w:cs="Courier New" w:eastAsia="Courier New" w:hAnsi="Courier New"'
    title_p = (f'<w:p><w:pPr><w:spacing w:after="80"/></w:pPr>'
               f'<w:r><w:rPr><w:rFonts {TNR}/><w:b/><w:bCs/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr>'
               f'<w:t xml:space="preserve">{esc(title)}</w:t></w:r></w:p>')
    body_ps = ''
    for ln in lines:
        body_ps += (f'<w:p><w:pPr><w:spacing w:after="20"/></w:pPr>'
                    f'<w:r><w:rPr><w:rFonts {mono}/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
                    f'<w:t xml:space="preserve">{esc(ln)}</w:t></w:r></w:p>')
    cell_content = title_p + body_ps
    return (f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="4780"/>'
            f'<w:tblBorders><w:top w:val="single" w:color="auto" w:sz="8"/><w:left w:val="single" w:color="auto" w:sz="8"/>'
            f'<w:bottom w:val="single" w:color="auto" w:sz="8"/><w:right w:val="single" w:color="auto" w:sz="8"/></w:tblBorders></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="4780"/></w:tblGrid>'
            f'<w:tr><w:trPr><w:cantSplit/></w:trPr><w:tc><w:tcPr><w:tcW w:type="dxa" w:w="4780"/>'
            f'<w:shd w:fill="F2F2F2" w:val="clear"/>'
            f'<w:tcMar><w:top w:type="dxa" w:w="80"/><w:left w:type="dxa" w:w="100"/><w:bottom w:type="dxa" w:w="80"/><w:right w:type="dxa" w:w="100"/></w:tcMar>'
            f'</w:tcPr>{cell_content}</w:tc></w:tr></w:tbl>')

# ---------------------------------------------------------------
# Figure sizing (EMU). Column max width ~4780 dxa = 3.319 in = 3,035,793 EMU
# ---------------------------------------------------------------
COL_MAX_EMU = 3035793

figure_files = [
    'fig0_flowchart.png',
    'fig1_sensor_trends.png',
    'fig2_sensor_rul_correlation.png',
    'fig3_rul_distribution.png',
    'fig4_pred_vs_actual_rul.png',
    'fig5_feature_importance.png',
    'fig6_counterfactual_branch_example.png',
    'fig7_life_extension_boxplot.png',
    'fig8_net_benefit_by_scenario.png',
]

def emu_size(fname, width_emu=COL_MAX_EMU):
    im = Image.open(os.path.join(FIGDIR, fname))
    w, h = im.size
    cy = int(width_emu * h / w)
    return width_emu, cy

fig_sizes = {f: emu_size(f) for f in figure_files}
# flowchart is very tall -- constrain by height instead, matching AgroBranch's Fig.1 proportions
flow_h_target = 3600000
im = Image.open(os.path.join(FIGDIR, 'fig0_flowchart.png'))
w, h = im.size
flow_w = int(flow_h_target * w / h)
fig_sizes['fig0_flowchart.png'] = (flow_w, flow_h_target)

for k, v in fig_sizes.items():
    print(k, v, 'in:', round(v[0]/914400,2), round(v[1]/914400,2))

# ---------------------------------------------------------------
# rId assignment for the 9 new figures (reuse the 500-series band)
# ---------------------------------------------------------------
rid_map = {f: f'rId{500+i}' for i, f in enumerate(figure_files)}
print(rid_map)

TITLE = "RepairBranch: A Mechanistically-Grounded Counterfactual Replay Framework for Remaining-Useful-Life Prognostics and Maintenance-Timing Optimization in Turbofan Engines"

ABSTRACT = open('/home/claude/repairbranch/abstract_250_final.txt', encoding='utf-8').read().strip()

KEYWORDS = ("Predictive Maintenance, Remaining Useful Life, Counterfactual Simulation, Digital Twin, "
            "Turbofan Engine Prognostics, Random Forest, NASA C-MAPSS, Maintenance Scheduling, "
            "Mechanistic Re-Simulation, Cost-Benefit Analysis")

print("word count check:", len(ABSTRACT.split()))

# =================================================================
# BODY CONTENT
# =================================================================

INTRO_P1 = ("Predictive maintenance (PdM) has moved steadily away from reactive, run-to-failure "
    "operation and toward prognostic estimation of Remaining Useful Life (RUL): given a stream of "
    "sensor readings, predict how many operating cycles remain before an asset fails. The NASA "
    "C-MAPSS turbofan-engine degradation benchmark [1], [2] catalyzed a large data-driven RUL "
    "literature, from an early recurrent-network winner of the original PHM'08 challenge [4] through "
    "deep convolutional [5] and long short-term memory [6] architectures, and more recently a "
    "higher-fidelity dataset generated under real flight conditions [3]. Nearly all of this work, "
    "however, treats RUL as a terminal output: a single number, or a distribution around one, handed "
    "to a human decision-maker. None of it answers the operationally relevant follow-up question \u2014 "
    "if this engine were serviced now instead of later, how much of its life would actually be "
    "recovered, and would that be worth the cost?")

INTRO_P2 = ("This paper presents RepairBranch, a framework that pairs a cross-validated RUL model "
    "with a counterfactual maintenance-timing replay engine, evaluated end-to-end on the public NASA "
    "C-MAPSS FD001 benchmark. Unlike a learned surrogate that approximates how a repaired engine "
    "would behave, RepairBranch mechanistically re-simulates each engine's own observed future "
    "degradation increments from a partially restored baseline \u2014 the same re-simulation discipline "
    "used in this group's prior GridGuard cascading-failure work \u2014 so every reported counterfactual "
    "outcome is grounded in that engine's real physics rather than in a model's extrapolation of it. "
    "An illustrative cost model then translates simulated life extension into a maintenance-timing "
    "decision, making explicit which assumptions would need to hold in a fielded deployment.")

INTRO_P3 = ("The economic stakes of this gap are not small. Unplanned downtime, expedited spare-parts "
    "shipping, and secondary damage from a component that failed rather than was retired on schedule "
    "are consistently identified across the predictive-maintenance survey literature as the dominant "
    "cost drivers that PdM programs are built to avoid [9], [10], and multi-classifier scheduling "
    "systems already in industrial use demonstrate that even a coarse act-now-or-later signal has "
    "measurable value in practice [7]. A framework that can additionally quantify how much value a "
    "specific repair date would recover, rather than only flagging that some date should be chosen, "
    "turns a binary alert into a scheduling input that can be weighed against production calendars, "
    "spare-parts lead times, and labor availability \u2014 the kind of quantity a maintenance planner can "
    "act on directly rather than merely a qualitative fact operations already suspected in the sensor "
    "trends. RepairBranch is designed to supply exactly that quantity without requiring a fleet to "
    "abandon whatever RUL model it already has in production, since the counterfactual replay engine "
    "in Section III consumes only a health-index trajectory and is agnostic to which model produced "
    "the underlying RUL estimate.")

RQ_TEXT = ("RQ1: Can sensor-derived features predict RUL on FD001 with accuracy confirmed by grouped "
    "cross-validation rather than a single favorable split? RQ2: Which sensors drive the prediction, "
    "and is the dominant signal consistent with known turbofan degradation physics? RQ3: How does "
    "simulated life extension vary with repair timing, and what property of the degradation curve "
    "explains that pattern? RQ4: Under an illustrative cost model, does earlier or later intervention "
    "yield the greater net benefit, and how much of that conclusion rests on the cost assumptions "
    "themselves rather than on the underlying physics?")

REL_P1 = ("The C-MAPSS dataset originates from a NASA thermodynamic simulation of turbofan damage "
    "propagation built for the PHM'08 prognostics challenge [1], with its simulation engine documented "
    "separately [2]; a higher-fidelity successor, N-CMAPSS, later added real recorded flight conditions "
    "[3]. Data-driven RUL prediction on this benchmark progressed from an early recurrent-network "
    "challenge entry [4] to deep convolutional [5] and LSTM-based [6] sequence models, each reporting "
    "improved point-prediction accuracy. None of these systems simulates an alternative maintenance "
    "history; RUL is estimated and reported, not acted upon within the model itself.")

REL_P2 = ("A parallel classical-ML predictive-maintenance literature treats the maintenance decision "
    "as a classification or threshold problem: Susto et al. [7] combine multiple classifiers to time "
    "interventions on semiconductor tools, while survey work [8], [9], [10] catalogs prognostic "
    "modelling options and the broader state of PHM practice. These systems recommend whether to act, "
    "typically now versus later on a fixed schedule, but do not simulate the graded consequence of "
    "acting at one specific cycle versus another.")

REL_P3 = ("Counterfactual reasoning has a separate, mature literature in explainable AI: Wachter et al. "
    "[11] introduced counterfactual explanations for automated decisions under GDPR, and Mothilal et "
    "al. [12] generalized this to diverse, actionable counterfactual sets for classifiers. These "
    "methods ask what minimal change to a static feature vector would flip a model's output \u2014 a "
    "fundamentally different object from asking how a physical degradation trajectory, unfolding over "
    "hundreds of operating cycles, would diverge under a different repair time. Applying counterfactual "
    "reasoning to the latter requires a mechanistic replay engine, not a feature-perturbation search.")

REL_P4b = ("A separate, older prognostics tradition is model-based rather than data-driven: Kalman and "
    "particle filters track a physical or empirical degradation state and update it as new sensor "
    "evidence arrives, an approach the prognostic-modelling survey in [8] situates alongside purely "
    "data-driven regressors. These filters output a single filtered state estimate at each time step, "
    "not an explicit set of alternative future trajectories under different intervention times, so the "
    "branching gap identified below applies to the model-based tradition as much as to the deep-learning "
    "RUL literature.")

REL_P4 = ("Table I summarizes this gap. No system in the RUL literature produces explicit "
    "maintenance-timing branches; no system in the counterfactual-explanation literature grounds its "
    "counterfactuals in a re-simulated physical trajectory; and no system in either literature couples "
    "its result to an explicit cost-benefit analysis. RepairBranch is positioned to close this "
    "three-way gap on a public, widely used benchmark.")

FRAMEWORK_P1 = ("RepairBranch is organized as a five-phase pipeline, shown in Fig. 1. Phase 1 ingests "
    "the raw FD001 sensor logs and constructs RUL labels and rolling-window features. Phase 2 trains "
    "and cross-validates a Random Forest RUL regressor. Phase 3 builds a smoothed, robust health-index "
    "signal from the regressor's leading sensor. Phase 4 is the counterfactual replay engine itself, "
    "detailed in Algorithm 1. Phase 5 converts simulated life extension into an illustrative "
    "cost-benefit comparison across repair-timing scenarios.")

FRAMEWORK_P2 = ("Algorithm 1 formalizes the replay step. For a given engine, the lead sensor's raw "
    "trajectory is first smoothed to suppress measurement noise (line 1); an early implementation used "
    "single-cycle readings for the healthy baseline S0 and the failure level S_fail, but this proved "
    "sensitive to sensor noise and was replaced with multi-point robust averages (line 2), which "
    "removed a class of spuriously near-zero life-extension results. At a counterfactual repair cycle "
    "T_r (line 3), the signal is partially restored toward its healthy baseline by a fixed restoration "
    "fraction r (line 4). The engine's own future increments \u2014 not a trained approximation of them \u2014 "
    "are then replayed forward from the restored value (lines 5\u201310) until the original failure level "
    "is re-crossed, cycling through the observed increment sequence if the restored trajectory outlasts "
    "the original horizon. The difference between the new and original failure cycles is the "
    "simulated life extension (line 12).")

ALG_TITLE = "Algorithm 1. Counterfactual Maintenance-Timing Replay"
ALG_LINES = [
    "Input: smoothed trajectory S[1..T_fail], restoration",
    "       fraction r, repair fraction f",
    "Output: simulated life extension \u0394T",
    " 1:  S \u2190 RollingMean(S_raw, window = 7)",
    " 2:  S0 \u2190 mean(S[1..10]);  S_fail \u2190 mean(S[T_fail-4..T_fail])",
    " 3:  T_r \u2190 round(f \u00d7 T_fail)",
    " 4:  S_restored \u2190 S[T_r] \u2212 r \u00d7 (S[T_r] \u2212 S0)",
    " 5:  \u0394 \u2190 Diff(S[T_r .. T_fail])      // observed future increments",
    " 6:  path[0] \u2190 S_restored;  i \u2190 0",
    " 7:  while path[last] < S_fail do",
    " 8:      path.append(path[last] + \u0394[i mod len(\u0394)])",
    " 9:      i \u2190 i + 1",
    "10:  end while",
    "11:  T_fail\u2032 \u2190 T_r + len(path) \u2212 1",
    "12:  return \u0394T \u2190 T_fail\u2032 \u2212 T_fail",
]

SETUP_P1 = ("Experiments use NASA C-MAPSS subset FD001 [1]: 100 training and 100 test turbofan "
    "engines, a single operating condition, a single fault mode (HPC degradation), and 21 sensor "
    "channels recorded once per operating cycle. Training engines run to failure (128\u2013362 cycles, "
    "mean 206.3); test trajectories are truncated before failure, with ground-truth RUL supplied "
    "separately. Seven sensors are constant under FD001's single operating condition and are excluded, "
    "leaving 14 informative channels.")

SETUP_P2 = ("Training RUL labels are the remaining cycles to failure, clipped at 125 cycles following "
    "standard practice, since degradation is close to flat over most of an engine's early life. Each "
    "of the 14 informative sensors contributes a 5-cycle rolling mean and standard deviation alongside "
    "its raw value. A Random Forest regressor (200 trees, max depth 10) is evaluated with grouped "
    "5-fold cross-validation \u2014 grouping by engine unit so that no engine's cycles appear in both the "
    "training and validation fold \u2014 before a final model is fit on the full training set and scored "
    "on the official FD001 test split using the last recorded cycle of each test engine.")

SETUP_P3 = ("The counterfactual replay engine (Algorithm 1) operates on sensor_4, the regressor's "
    "single most important feature (Section V.A), smoothed with a 7-cycle centered rolling mean. Three "
    "repair-timing scenarios are simulated for every training engine: repair at 50%, 70%, and 85% of "
    "its observed life, with a restoration fraction of 0.6. An illustrative cost model then assigns "
    "$50,000 to an unplanned failure, $8,000 to a scheduled repair, and $150 to each cycle of extended "
    "operating life; these figures are placeholders chosen to demonstrate the framework and should be "
    "replaced with fleet-specific figures in an applied deployment.")

SETUP_P4 = ("All models were implemented in scikit-learn [15] (RandomForestRegressor, 200 trees, "
    "max_depth=10, random_state=42 for the final model; 150 trees, max_depth=10 for each grouped "
    "cross-validation fold, keeping fold-level training time tractable on a single-core execution "
    "environment). GroupKFold was used in place of an ordinary K-fold split specifically so that "
    "cycles from the same engine unit could never appear in both a training and a validation fold, "
    "which would otherwise let the model implicitly memorize a unit's own trajectory rather than "
    "generalize across engines. The counterfactual replay engine and cost-benefit evaluation are "
    "implemented as deterministic NumPy/pandas computations with no learned component, so, unlike the "
    "RUL regressor, their outputs are exactly reproducible given the same restoration fraction, "
    "smoothing window, and cost assumptions.")

RESULTS_A_P1 = ("Table II summarizes the FD001 dataset actually used. Table III reports RUL prediction "
    "performance: a test RMSE of 18.9 cycles, MAE of 13.6 cycles, R\u00b2 of 0.794, and a NASA PHM'08 "
    "asymmetric score of 1044.1, with 5-fold grouped cross-validation (mean RMSE 18.0) confirming the "
    "held-out result is not an artifact of a favorable split. Fig. 2 shows six representative engines' "
    "sensor trajectories over normalized life; degradation is visibly flat for roughly the first "
    "60\u201370% of life before accelerating sharply, a pattern that later explains the counterfactual "
    "results in Section V.B. Fig. 3 ranks all 14 informative sensors by their linear correlation with "
    "RUL; sensor_11, sensor_4, and sensor_15 show the strongest negative correlation. Fig. 4 shows the "
    "resulting RUL distribution across all training cycle-snapshots, and Fig. 5 plots predicted versus "
    "actual RUL on the 100 held-out test engines.")

RESULTS_A_P2 = ("Table IV and Fig. 6 report aggregated Random Forest feature importance. sensor_4 "
    "accounts for 69.6% of total importance \u2014 roughly six times the combined weight of the next two "
    "sensors \u2014 which is why it was selected as the lead signal for the counterfactual replay engine in "
    "Section III. This concentration is consistent with turbofan physics: sensor_4 (total temperature "
    "at the low-pressure turbine outlet) is a standard proxy for the exhaust-gas-temperature margin "
    "used in real engine health monitoring, so a single-sensor triggering rule is not merely a "
    "modeling convenience but plausibly reflects how this fault mode actually manifests instrumentally.")

RESULTS_B_P1 = ("Fig. 7 shows Algorithm 1 applied to one representative engine (#24) at all three "
    "repair timings; each dashed branch diverges from the observed trajectory at its repair point and "
    "reaches the original failure level later than the unrepaired engine did. Fig. 8 confirms this "
    "pattern holds across the full 100-engine training set: Table V reports a mean simulated life "
    "extension of 13.8 cycles for early (50%) repair, rising to 17.5 cycles at mid (70%) repair and "
    "22.8 cycles at late (85%) repair. This ordering is not the naively expected one \u2014 intuition might "
    "suggest earlier intervention preserves more life \u2014 and Section VI.A explains why the observed, "
    "back-loaded degradation shape from Fig. 2 produces the opposite result.")

RESULTS_C_P1 = ("Table VI lists the illustrative cost-model assumptions; Fig. 9 shows the resulting "
    "mean net benefit per engine by repair-timing scenario. Because the fixed differential between an "
    "unplanned-failure cost and a scheduled-repair cost ($42,000) dominates the variable, "
    "extension-dependent term in this cost model, all three scenarios show large positive net benefit "
    "for every one of the 100 engines (Table V), with late repair producing the highest mean benefit "
    "($45,422) by a modest margin over early repair ($44,072). Because net benefit is a strictly "
    "increasing linear function of simulated life extension under this cost model, and late repair "
    "yields strictly greater mean life extension than early repair for every value of the per-cycle "
    "operating value (Table V), late repair's advantage cannot reverse by changing that one parameter "
    "in isolation; raising the per-cycle value from $150 toward, for example, $1,000 would widen the "
    "gap between scenarios roughly six-fold (from about $1,350 to about $9,000 between early and late "
    "repair) rather than close or invert it. A reversal would instead require changing which quantity "
    "is held fixed \u2014 for example, a cost model where late repair itself carries a higher risk premium "
    "because more accumulated damage must be inspected and corrected, a real-world effect this "
    "simplified model does not capture.")

DISC_A = ("Four implications follow from these results. First, because degradation on FD001 is "
    "back-loaded \u2014 nearly flat until roughly 60\u201370% of life, then sharply accelerating (Fig. 2) \u2014 a "
    "fixed restoration fraction removes more absolute accumulated damage the later it is applied, so "
    "late-but-safe repair timing can mechanically outperform very early intervention on this dataset; "
    "a maintenance policy built on the intuition that earlier is always better would be leaving "
    "simulated life extension on the table. Second, because sensor_4 alone carries roughly 70% of "
    "predictive weight and maps onto a physically meaningful exhaust-temperature margin, a lightweight "
    "single-sensor monitoring trigger may be a defensible simplification for early-warning purposes "
    "even where a full 14-sensor model is used for the final RUL estimate. Third, because net benefit "
    "in Section V.C is dominated by the fixed failure-versus-repair cost gap rather than by the "
    "variable life-extension term, the specific repair-timing recommendation is far more sensitive to "
    "getting that fixed cost gap right than to precisely tuning the repair-timing scenario itself. "
    "Fourth, because Algorithm 1 requires only a smoothed sensor trajectory and no trained surrogate "
    "at simulation time, the counterfactual replay engine could plausibly run as a lightweight what-if "
    "calculator alongside an existing fleet RUL dashboard without retraining any model \u2014 the marginal "
    "cost of adding maintenance-timing branches to a deployment that already estimates RUL is small, "
    "which is precisely what makes the framework worth adopting incrementally rather than as a "
    "wholesale replacement for existing PdM infrastructure.")

DATA_AVAIL = ("The FD001 dataset is publicly available from NASA's Prognostics Data Repository [1], "
    "[2]. The RUL regressor, counterfactual replay engine, and cost-benefit scripts described in this "
    "paper are implemented in Python (scikit-learn, NumPy, pandas, and Matplotlib) and are available "
    "from the corresponding author upon reasonable request.")

DISC_B = ("This study has five main limitations. FD001 covers a single operating condition and a "
    "single fault mode; the other three C-MAPSS subsets were not evaluated here and generalization "
    "across them is untested \u2014 FD002 adds six operating conditions across 260 training engines "
    "(128\u2013378 cycles), FD003 adds a second fault mode across 100 engines with a notably longer "
    "maximum life (145\u2013525 cycles), and FD004 combines both at once across 249 engines (128\u2013543 "
    "cycles), and each would need its own health-index sensor and restoration-fraction calibration "
    "rather than reusing FD001's sensor_4-based configuration unchanged. The higher-fidelity N-CMAPSS "
    "dataset [3], built "
    "under real flight conditions, was not reachable from this paper's execution sandbox, which is "
    "restricted to a fixed set of network domains; classic C-MAPSS remains the field's standard "
    "benchmark, but N-CMAPSS would be a natural extension. The RUL model is a Random Forest rather "
    "than a sequence model such as an LSTM or CNN [5], [6], a choice made for reliable execution on a "
    "single-core sandbox rather than a methodological preference; published deep-learning baselines on "
    "FD001 report both better and worse NASA scores depending on architecture and tuning, so this "
    "paper's baseline should be read as a solid but not state-of-the-art reference point. The "
    "counterfactual replay engine uses a single lead sensor as its health index rather than a "
    "multivariate composite, and reuses observed future increments cyclically when a restored "
    "trajectory outlasts the original horizon \u2014 a reasonable heuristic for the repair timings tested "
    "here (50\u201385% of life) but untested for very early repairs, where many replay cycles would be "
    "needed. Finally, the $50,000/$8,000/$150 cost figures are illustrative placeholders chosen to "
    "demonstrate the framework, not figures sourced from a real maintenance program; Section V.C's "
    "specific dollar conclusions should not be read as a general claim about optimal repair timing "
    "beyond this demonstration.")

DISC_C = ("Two threats to validity are worth naming explicitly rather than leaving implicit in Section "
    "VI.B. Internally, the grouped cross-validation protocol (Section IV) rules out engine-level data "
    "leakage as an explanation for the reported RUL accuracy, but the counterfactual replay results in "
    "Section V.B are not cross-validated in the same sense: each engine's life extension is computed "
    "from that engine's own trajectory alone, so the reported means are descriptive of these 100 "
    "training engines rather than an out-of-sample generalization claim. Externally, every quantitative "
    "result in this paper is specific to FD001's single operating condition and single fault mode; the "
    "qualitative mechanism identified in Section VI.A \u2014 that back-loaded degradation curves make later "
    "repair timing mechanically more effective under a fixed restoration fraction \u2014 should transfer "
    "wherever degradation is similarly back-loaded, but whether FD002\u2013FD004's additional operating "
    "conditions and fault modes preserve that same back-loaded shape is an empirical question this "
    "paper does not answer.")

CONCLUSION = ("This paper presented RepairBranch, a framework coupling a cross-validated Random Forest "
    "RUL model with a mechanistic counterfactual maintenance-timing replay engine, evaluated end-to-end "
    "on the NASA C-MAPSS FD001 benchmark. Across the four research questions: RUL is predicted with a "
    "test RMSE of 18.9 cycles and R\u00b2 of 0.794, confirmed by grouped cross-validation; a single sensor "
    "with a plausible physical interpretation accounts for roughly 70% of predictive importance; "
    "simulated life extension increases with later repair timing because FD001's degradation curves "
    "are back-loaded rather than linear; and net benefit under an illustrative cost model is dominated "
    "by the fixed failure-versus-repair cost gap rather than by the repair-timing choice itself. These "
    "findings indicate that disciplined, mechanistic counterfactual replay \u2014 re-simulating an asset's "
    "own observed degradation rather than a trained approximation of it \u2014 is a practical route to "
    "maintenance-timing decision support that point-prediction RUL systems do not by themselves "
    "provide, with the limitations in Section VI.B marking where multi-condition validation and "
    "fleet-specific cost data are needed before operational use.")

REFERENCES = [
    "[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, \u201cDamage propagation modeling for aircraft "
    "engine run-to-failure simulation,\u201d in Proc. Int. Conf. Prognostics and Health Management (PHM), "
    "Denver, CO, USA, Oct. 2008. doi: 10.1109/PHM.2008.4711414.",

    "[2] D. K. Frederick, J. A. DeCastro, and J. S. Litt, \u201cUser\u2019s Guide for the Commercial Modular "
    "Aero-Propulsion System Simulation (C-MAPSS),\u201d NASA/TM\u20142007-215026, NASA Glenn Research Center, "
    "2007.",

    "[3] M. Arias Chao, C. Kulkarni, K. Goebel, and O. Fink, \u201cAircraft engine run-to-failure dataset "
    "under real flight conditions for prognostics and diagnostics,\u201d Data, vol. 6, no. 1, art. 5, Jan. "
    "2021. doi: 10.3390/data6010005.",

    "[4] F. O. Heimes, \u201cRecurrent neural networks for remaining useful life estimation,\u201d in Proc. Int. "
    "Conf. Prognostics and Health Management (PHM), Denver, CO, USA, Oct. 2008.",

    "[5] X. Li, Q. Ding, and J.-Q. Sun, \u201cRemaining useful life estimation in prognostics using deep "
    "convolution neural networks,\u201d Reliab. Eng. Syst. Saf., vol. 172, pp. 1\u201311, 2018. doi: "
    "10.1016/j.ress.2017.11.021.",

    "[6] S. Zheng, K. Ristovski, A. Farahat, and C. Gupta, \u201cLong short-term memory network for "
    "remaining useful life estimation,\u201d in Proc. IEEE Int. Conf. Prognostics and Health Management "
    "(ICPHM), Dallas, TX, USA, 2017, pp. 88\u201395.",

    "[7] G. A. Susto, A. Schirru, S. Pampuri, S. McLoone, and A. Beghi, \u201cMachine learning for "
    "predictive maintenance: A multiple classifier approach,\u201d IEEE Trans. Ind. Informat., vol. 11, no. "
    "3, pp. 812\u2013820, 2015.",

    "[8] J. Z. Sikorska, M. Hodkiewicz, and L. Ma, \u201cPrognostic modelling options for remaining useful "
    "life estimation by industry,\u201d Mech. Syst. Signal Process., vol. 25, no. 5, pp. 1803\u20131836, 2011.",

    "[9] E. Zio, \u201cPrognostics and health management (PHM): Where are we and where do we (need to) go "
    "in theory and practice,\u201d Reliab. Eng. Syst. Saf., vol. 218, art. 108119, 2022.",

    "[10] T. P. Carvalho, F. A. A. M. N. Soares, R. Vita, R. P. Francisco, J. P. Basto, and S. G. "
    "Alcal\u00e1, \u201cA systematic literature review of machine learning methods applied to predictive "
    "maintenance,\u201d Comput. Ind. Eng., vol. 137, art. 106024, 2019.",

    "[11] S. Wachter, B. Mittelstadt, and C. Russell, \u201cCounterfactual explanations without opening the "
    "black box: Automated decisions and the GDPR,\u201d Harv. J. Law Technol., vol. 31, no. 2, pp. 841\u2013887, "
    "2018.",

    "[12] R. K. Mothilal, A. Sharma, and C. Tan, \u201cExplaining machine learning classifiers through "
    "diverse counterfactual explanations,\u201d in Proc. ACM Conf. Fairness, Accountability, and "
    "Transparency (FAT*), Barcelona, Spain, 2020, pp. 607\u2013617.",

    "[13] L. Breiman, \u201cRandom forests,\u201d Mach. Learn., vol. 45, no. 1, pp. 5\u201332, Oct. 2001. doi: "
    "10.1023/A:1010933404324.",

    "[14] J. H. Friedman, \u201cGreedy function approximation: A gradient boosting machine,\u201d Ann. Statist., "
    "vol. 29, no. 5, pp. 1189\u20131232, 2001.",

    "[15] F. Pedregosa et al., \u201cScikit-learn: Machine learning in Python,\u201d J. Mach. Learn. Res., vol. "
    "12, pp. 2825\u20132830, 2011.",
]
print("Num references:", len(REFERENCES))

# =================================================================
# TABLES
# =================================================================

TABLE_I = dict(
    caption="TABLE I.  COMPARISON WITH RELATED PRIOR WORK",
    col_widths=[1450, 850, 750, 750, 980],
    header=["System", "RUL Progn.", "Branch.", "Mech.", "Cost-Ben."],
    rows=[
        ["Saxena et al. [1] (C-MAPSS origin)", "N", "N", "Y (sim.)", "N"],
        ["Heimes/Li/Zheng [4]-[6] (deep RUL)", "Y", "N", "N", "N"],
        ["Susto et al. [7] (PdM classifier)", "Partial", "N", "N", "N"],
        ["Wachter/Mothilal [11],[12] (XAI)", "N", "Y (feat.)", "N", "N"],
        ["RepairBranch (this paper)", "Y", "Y", "Y", "Y"],
    ],
    note=("TABLE I. Branch. = produces explicit multi-scenario maintenance-timing branches. Mech. = "
          "grounded in mechanistic re-simulation rather than a trained surrogate (physics simulation "
          "counts as mechanistic for [1]). Cost-Ben. = includes an explicit cost-benefit analysis.")
)

TABLE_II = dict(
    caption="TABLE II.  DATASET SUMMARY (NASA C-MAPSS FD001)",
    col_widths=[3200, 1580],
    header=["Metric", "Value"],
    rows=[
        ["Training engine units", "100"],
        ["Test engine units", "100"],
        ["Training rows (cycle snapshots)", "20,631"],
        ["Test rows (cycle snapshots)", "13,096"],
        ["Sensors recorded", "21"],
        ["Informative sensors (non-constant)", "14"],
        ["Operating conditions", "1"],
        ["Fault modes", "1 (HPC degradation)"],
        ["Min cycles to failure (train)", "128"],
        ["Max cycles to failure (train)", "362"],
        ["Mean cycles to failure (train)", "206.3"],
    ],
    note=None
)

TABLE_III = dict(
    caption="TABLE III.  RUL PREDICTION MODEL PERFORMANCE",
    col_widths=[3200, 1580],
    header=["Metric", "Value"],
    rows=[
        ["CV RMSE (train, 5-fold GroupKFold)", "18.03 cycles"],
        ["Test RMSE", "18.87 cycles"],
        ["Test MAE", "13.62 cycles"],
        ["Test R\u00b2", "0.794"],
        ["NASA PHM\u201908 Score (lower = better)", "1044.1"],
    ],
    note="TABLE III. Test metrics computed on the official FD001 test split (100 engines, last cycle)."
)

TABLE_IV = dict(
    caption="TABLE IV.  TOP SENSORS BY AGGREGATED FEATURE IMPORTANCE",
    col_widths=[1850, 2930],
    header=["Sensor", "Aggregated Importance"],
    rows=[
        ["sensor_4", "0.696"],
        ["sensor_9", "0.109"],
        ["sensor_11", "0.091"],
        ["sensor_14", "0.019"],
        ["sensor_15", "0.014"],
        ["sensor_7", "0.012"],
        ["sensor_12", "0.011"],
        ["sensor_21", "0.010"],
    ],
    note=("TABLE IV. Importance aggregated across each sensor's raw, rolling-mean, and rolling-std "
          "features. sensor_4 = total temperature at low-pressure turbine outlet.")
)

TABLE_V = dict(
    caption="TABLE V.  COUNTERFACTUAL LIFE-EXTENSION AND NET-BENEFIT SUMMARY, BY SCENARIO (n=100 ENGINES)",
    col_widths=[1450, 1050, 1130, 1150],
    header=["Scenario", "Mean \u0394Life (cyc.)", "Mean Net Benefit ($)", "% Positive"],
    rows=[
        ["Early repair (50%)", "13.8", "44,072", "100.0"],
        ["Mid repair (70%)", "17.5", "44,621", "100.0"],
        ["Late repair (85%)", "22.8", "45,422", "100.0"],
    ],
    note=("TABLE V. \u0394Life = simulated life extension vs. no-repair baseline. % Positive = share of "
          "the 100 training engines with positive net benefit under the Table VI cost model.")
)

TABLE_VI = dict(
    caption="TABLE VI.  ILLUSTRATIVE COST MODEL ASSUMPTIONS",
    col_widths=[2960, 1820],
    header=["Assumption", "Value (USD)"],
    rows=[
        ["Unplanned failure cost", "50,000"],
        ["Scheduled repair cost", "8,000"],
        ["Value per extended operating cycle", "150"],
    ],
    note=("TABLE VI. Placeholder figures chosen to demonstrate the cost-benefit framework; not sourced "
          "from a real maintenance program (Section VI.B).")
)

ALL_TABLES = [TABLE_I, TABLE_II, TABLE_III, TABLE_IV, TABLE_V, TABLE_VI]

def render_table(t):
    xml = table_caption_para(t['caption'])
    xml += make_table(t['col_widths'], t['header'], t['rows'])
    xml += spacer_para()
    if t['note']:
        xml += table_note_para(t['note'])
    else:
        xml += table_note_para(t['caption'])
    return xml

print("Tables prepared:", len(ALL_TABLES))
for t in ALL_TABLES:
    assert sum(t['col_widths']) <= 4790, t['caption']
    print(t['caption'], 'width sum', sum(t['col_widths']))

# =================================================================
# ASSEMBLE FULL DOCUMENT BODY
# =================================================================

def fig_block(fname, caption):
    cx, cy = fig_sizes[fname]
    return image_para(rid_map[fname], cx, cy) + caption_para(caption)

body = []

# --- Title block (single column section) ---
body.append(title_para(TITLE))
body.append(centered_line("[Author Name(s) \u2014 to be completed]", sz='22'))
body.append(centered_line("Department / Affiliation, City, Country", sz='20', italic=True))
body.append(centered_line("email@example.com", sz='20'))
body.append(abstract_para(ABSTRACT))
body.append(keywords_para(KEYWORDS))
body.append(SECTION_BREAK_1COL)

# --- I. INTRODUCTION ---
body.append(section_heading("I. INTRODUCTION"))
body.append(body_para(INTRO_P1))
body.append(body_para(INTRO_P2))
body.append(body_para(INTRO_P3))
body.append(subsection_heading("A. Research Questions"))
body.append(body_para(RQ_TEXT))

# --- II. RELATED WORK ---
body.append(section_heading("II. RELATED WORK"))
body.append(body_para(REL_P1))
body.append(body_para(REL_P2))
body.append(body_para(REL_P3))
body.append(body_para(REL_P4b))
body.append(body_para(REL_P4))
body.append(render_table(TABLE_I))

# --- III. FRAMEWORK ARCHITECTURE ---
body.append(section_heading("III. REPAIRBRANCH FRAMEWORK ARCHITECTURE"))
body.append(body_para(FRAMEWORK_P1))
body.append(fig_block('fig0_flowchart.png', "Fig. 1. RepairBranch methodology flowchart: five phases from raw FD001 sensor logs through cost-benefit evaluation."))
body.append(body_para(FRAMEWORK_P2))
body.append(spacer_para())
body.append(algorithm_box(ALG_TITLE, ALG_LINES))
body.append(spacer_para())

# --- IV. EXPERIMENTAL SETUP ---
body.append(section_heading("IV. EXPERIMENTAL SETUP AND DATASET"))
body.append(body_para(SETUP_P1))
body.append(body_para(SETUP_P2))
body.append(body_para(SETUP_P3))
body.append(body_para(SETUP_P4))

# --- V. RESULTS ---
body.append(section_heading("V. RESULTS"))
body.append(subsection_heading("A. RUL Prediction Performance"))
body.append(render_table(TABLE_II))
body.append(body_para(RESULTS_A_P1))
body.append(fig_block('fig1_sensor_trends.png', "Fig. 2. Sensor degradation trends across engine life (6 sample engines, FD001)."))
body.append(fig_block('fig2_sensor_rul_correlation.png', "Fig. 3. Sensor correlation with Remaining Useful Life (RUL)."))
body.append(fig_block('fig3_rul_distribution.png', "Fig. 4. Distribution of Remaining Useful Life (training set)."))
body.append(render_table(TABLE_III))
body.append(fig_block('fig4_pred_vs_actual_rul.png', "Fig. 5. Predicted vs. actual RUL, test set (n=100 engines)."))
body.append(body_para(RESULTS_A_P2))
body.append(render_table(TABLE_IV))
body.append(fig_block('fig5_feature_importance.png', "Fig. 6. Top sensors by aggregated Random Forest feature importance."))

body.append(subsection_heading("B. Counterfactual Maintenance-Timing Replay"))
body.append(body_para(RESULTS_B_P1))
body.append(fig_block('fig6_counterfactual_branch_example.png', "Fig. 7. Counterfactual maintenance-timing branches, example engine #24."))
body.append(fig_block('fig7_life_extension_boxplot.png', "Fig. 8. Life extension by repair-timing scenario (n=100 engines)."))
body.append(render_table(TABLE_V))

body.append(subsection_heading("C. Cost-Benefit Analysis"))
body.append(render_table(TABLE_VI))
body.append(body_para(RESULTS_C_P1))
body.append(fig_block('fig8_net_benefit_by_scenario.png', "Fig. 9. Estimated net benefit by repair-timing scenario."))

# --- VI. DISCUSSION ---
body.append(section_heading("VI. DISCUSSION"))
body.append(subsection_heading("A. Key Findings and Practical Implications"))
body.append(body_para(DISC_A))
body.append(subsection_heading("B. Limitations and Future Work"))
body.append(body_para(DISC_B))
body.append(subsection_heading("C. Threats to Validity"))
body.append(body_para(DISC_C))

# --- VII. CONCLUSION ---
body.append(section_heading("VII. CONCLUSION"))
body.append(body_para(CONCLUSION))

# --- DATA AND CODE AVAILABILITY ---
body.append(subsection_heading("Data and Code Availability"))
body.append(body_para(DATA_AVAIL))

# --- REFERENCES ---
body.append(section_heading("REFERENCES"))
for r in REFERENCES:
    body.append(reference_para(r))

# --- Final section properties (two-column, with header/footer refs) ---
FINAL_SECTPR = ('<w:sectPr><w:headerReference w:type="default" r:id="rId7"/>'
    '<w:footerReference w:type="default" r:id="rId8"/><w:type w:val="continuous"/>'
    '<w:pgSz w:w="12240" w:h="15840" w:orient="portrait"/>'
    '<w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080" w:header="708" w:footer="708" w:gutter="0"/>'
    '<w:pgNumType/><w:cols w:space="360" w:num="2"/><w:docGrid w:linePitch="360"/></w:sectPr>')

new_body = ''.join(body) + FINAL_SECTPR

print("New body length (chars):", len(new_body))
print("Approx total words in new body:", len(re.sub('<[^>]+>', ' ', new_body).split()))

with open('/tmp/new_body.xml', 'w', encoding='utf-8') as f:
    f.write(new_body)
print("Wrote /tmp/new_body.xml")

# =================================================================
# SPLICE INTO document.xml
# =================================================================
doc_path = os.path.join(BASE, 'word/document.xml')
doc = open(doc_path, encoding='utf-8').read()
body_start = doc.find('<w:body>') + len('<w:body>')
header_part = doc[:body_start]
new_doc = header_part + new_body + '</w:body></w:document>'
with open(doc_path, 'w', encoding='utf-8') as f:
    f.write(new_doc)
print("document.xml rewritten, new length:", len(new_doc))

# =================================================================
# FIX HEADER (was leftover "EDUGUARD..." text)
# =================================================================
hdr_path = os.path.join(BASE, 'word/header1.xml')
hdr = open(hdr_path, encoding='utf-8').read()
hdr_new = hdr.replace(
    "EDUGUARD: Explainable Early-Warning and Decision Support for Student Dropout Prediction",
    "RepairBranch: Counterfactual Maintenance-Timing Replay for Turbofan RUL Prognostics"
)
assert hdr_new != hdr, "header replacement failed to match"
with open(hdr_path, 'w', encoding='utf-8') as f:
    f.write(hdr_new)
print("header1.xml fixed")

# =================================================================
# SWAP IMAGES: repoint rId500-508 to new files, remove rId509-513 and old media
# =================================================================
media_dir = os.path.join(BASE, 'word/media')
rels_path = os.path.join(BASE, 'word/_rels/document.xml.rels')
rels = open(rels_path, encoding='utf-8').read()

old_targets = {
    'rId500': 'media/agb_sample_grid.png',
    'rId501': 'media/agb_cm_potato.png',
    'rId502': 'media/agb_cm_corn.png',
    'rId503': 'media/agb_lesion_frac.png',
    'rId504': 'media/agb_flowchart.png',
    'rId505': 'media/agb_progress_curves.png',
    'rId506': 'media/agb_surrogate_scatter.png',
    'rId507': 'media/agb_surrogate_rollout.png',
    'rId508': 'media/agb_branch_potato.png',
}
extra_old_targets = {
    'rId509': 'media/agb_branch_corn.png',
    'rId510': 'media/agb_mc_timing.png',
    'rId511': 'media/agb_mc_weather.png',
    'rId512': 'media/agb_cross_crop.png',
    'rId513': 'media/agb_loo_surrogate.png',
}

new_filenames = {f'rId{500+i}': f'media/repairbranch_{fn}' for i, fn in enumerate(figure_files)}

for rid, old_target in old_targets.items():
    new_target = new_filenames[rid]
    old_full = f'Target="{old_target}"'
    new_full = f'Target="{new_target}"'
    assert old_full in rels, f"missing {old_full}"
    rels = rels.replace(old_full, new_full, 1)

# remove the 5 unused relationship entries entirely (rId509-513),
# plus the 12 orphaned hash-named image relationships (rId9-rId20, never
# referenced anywhere in document.xml/header/footer -- see investigation above)
orphan_rids = [f'rId{i}' for i in range(9, 21)]
for rid in list(extra_old_targets.keys()) + orphan_rids:
    pattern = re.compile(r'<Relationship Id="' + rid + r'"[^>]*/>')
    m = pattern.search(rels)
    assert m, f"could not find relationship {rid}"
    rels = rels[:m.start()] + rels[m.end():]

with open(rels_path, 'w', encoding='utf-8') as f:
    f.write(rels)
print("document.xml.rels updated")

# copy new figure files into media/, remove all old agb_*.png files
for fname in figure_files:
    src = os.path.join(FIGDIR, fname)
    dst = os.path.join(media_dir, f'repairbranch_{fname}')
    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        fdst.write(fsrc.read())

for old_target in list(old_targets.values()) + list(extra_old_targets.values()):
    p = os.path.join(BASE, 'word', old_target)
    if os.path.exists(p):
        os.remove(p)

# also remove the unused hash-named orphan images (never referenced anywhere)
for fname in os.listdir(media_dir):
    if re.fullmatch(r'[0-9a-f]{40}\.png', fname):
        os.remove(os.path.join(media_dir, fname))

print("Media files swapped.")
print("Remaining media dir contents:", sorted(os.listdir(media_dir)))

# =================================================================
# REZIP, VALIDATE, RENDER
# =================================================================
OUT_DOCX = '/home/claude/paper_analysis/RepairBranch_IEEE_Research_Paper.docx'
if os.path.exists(OUT_DOCX):
    os.remove(OUT_DOCX)
subprocess.run(f"cd {BASE} && zip -Xrq '{OUT_DOCX}' .", shell=True, check=True)
print("Zipped:", OUT_DOCX, os.path.getsize(OUT_DOCX))

val = subprocess.run(['python3', '/mnt/skills/public/docx/scripts/office/validate.py', OUT_DOCX,
                       '--original', '/home/claude/paper_analysis/AgroBranch_IEEE_Research_Paper.docx',
                       '--auto-repair'], capture_output=True, text=True)
print("VALIDATE STDOUT:", val.stdout[-3000:])
print("VALIDATE STDERR:", val.stderr[-2000:])

print("Body text prepared, total words:", sum(len(x.split()) for x in [
    INTRO_P1, INTRO_P2, RQ_TEXT, REL_P1, REL_P2, REL_P3, REL_P4, FRAMEWORK_P1, FRAMEWORK_P2,
    SETUP_P1, SETUP_P2, SETUP_P3, RESULTS_A_P1, RESULTS_A_P2, RESULTS_B_P1, RESULTS_C_P1,
    DISC_A, DISC_B, CONCLUSION]))



