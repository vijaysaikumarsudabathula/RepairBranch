"""
RepairBranch - Step 4: Counterfactual Maintenance-Timing Replay Engine

Methodology (mechanistic re-simulation, not a trained surrogate):
For each engine's OBSERVED run-to-failure trajectory of the lead health-indicator
sensor (sensor_4, the top RUL predictor from Step 3):
  1. Identify the actual failure cycle T_fail and failure-level sensor value S_fail.
  2. At a counterfactual repair cycle T_r = x% of T_fail, partially restore the
     sensor toward its early-life baseline by a restoration factor.
  3. Replay the engine's OWN observed future degradation increments (not a new
     model) starting from the restored baseline, preserving the true nonlinear
     (accelerating) shape of that engine's degradation curve.
  4. Find the new cycle at which the replayed path re-crosses S_fail -> T_fail'.
  5. Life extension = T_fail' - T_fail.

Illustrative cost model (assumptions clearly stated for the paper's methodology
section; replace with real client figures in an applied setting):
  - C_FAILURE  = $50,000  (unplanned failure / downtime cost)
  - C_REPAIR   = $8,000   (scheduled maintenance intervention cost)
  - V_CYCLE    = $150     (value of one extra operating cycle)
  Net benefit(scenario) = (C_FAILURE - C_REPAIR) + V_CYCLE * life_extension
  Baseline (no repair) net benefit = 0 by definition (reference case).
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({'figure.dpi': 130, 'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3})

SENSOR = 'sensor_4'          # top RUL predictor from Step 3 feature importance
RESTORE_FRAC = 0.6           # fraction of accumulated degradation removed at repair
SCENARIOS = {'Early repair (50% of life)': 0.50,
             'Mid repair (70% of life)': 0.70,
             'Late repair (85% of life)': 0.85}

C_FAILURE = 50_000
C_REPAIR = 8_000
V_CYCLE = 150

train = pd.read_csv('data/train_fd001_rul.csv')
SMOOTH_WINDOW = 7  # smooth raw sensor noise before mechanistic replay

def simulate_unit(df_unit):
    """Return dict of {scenario_name: life_extension} for one engine's trajectory."""
    df_unit = df_unit.sort_values('cycle').reset_index(drop=True)
    S_raw = df_unit[SENSOR].values
    # smooth to get a stable degradation signal (raw sensor is noisy — see Fig.1)
    S = pd.Series(S_raw).rolling(SMOOTH_WINDOW, min_periods=1, center=True).mean().values
    T_fail = len(S)              # actual observed failure cycle (last row)
    S_fail = np.mean(S[-5:])     # robust failure-level value
    S0 = np.mean(S[:10])         # robust healthy baseline
    results = {}
    for name, frac in SCENARIOS.items():
        T_r = max(1, int(round(frac * T_fail)))
        if T_r >= T_fail - 2:
            results[name] = 0.0
            continue
        # restore sensor at T_r toward baseline
        S_at_repair = S[T_r]
        S_restored = S_at_repair - RESTORE_FRAC * (S_at_repair - S0)
        # observed future increments from the SAME unit (mechanistic replay)
        future_increments = np.diff(S[T_r:])   # increments actually observed post-T_r
        # replay forward from restored baseline using those real increments,
        # extending (looping) the last-observed increment pattern if we run past
        # the original horizon before crossing S_fail again
        path = [S_restored]
        i = 0
        max_steps = 5 * len(future_increments) + 50
        steps = 0
        while path[-1] < S_fail and steps < max_steps:
            inc = future_increments[i % len(future_increments)] if len(future_increments) > 0 else (S_fail - S0) / T_fail
            path.append(path[-1] + inc)
            i += 1
            steps += 1
        T_fail_new = T_r + len(path) - 1
        life_extension = T_fail_new - T_fail
        results[name] = max(0, life_extension)
    return results

records = []
for unit, df_unit in train.groupby('unit'):
    res = simulate_unit(df_unit)
    for scenario, ext in res.items():
        net_benefit = (C_FAILURE - C_REPAIR) + V_CYCLE * ext
        records.append({'unit': unit, 'scenario': scenario, 'life_extension_cycles': ext,
                         'net_benefit_usd': net_benefit})

cf = pd.DataFrame(records)
cf.to_csv('tables/table4_counterfactual_results_by_unit.csv', index=False)

summary = cf.groupby('scenario').agg(
    mean_life_extension=('life_extension_cycles', 'mean'),
    median_life_extension=('life_extension_cycles', 'median'),
    mean_net_benefit_usd=('net_benefit_usd', 'mean'),
    pct_units_positive_benefit=('net_benefit_usd', lambda x: round(100 * (x > 0).mean(), 1))
).reset_index()
summary = summary.round(1)
summary.to_csv('tables/table5_counterfactual_summary.csv', index=False)
print(summary)

# ---------------------------------------------------------------
# Figure 6: hero visual - one engine's trajectory with 3 counterfactual branches
# ---------------------------------------------------------------
example_unit = 24
df_ex = train[train.unit == example_unit].sort_values('cycle').reset_index(drop=True)
S_raw = df_ex[SENSOR].values
S = pd.Series(S_raw).rolling(SMOOTH_WINDOW, min_periods=1, center=True).mean().values
T_fail = len(S)
S_fail = np.mean(S[-5:])
S0 = np.mean(S[:10])

fig, ax = plt.subplots(figsize=(9, 6))
ax.plot(range(1, T_fail + 1), S_raw, color='#bbbbbb', linewidth=1, label='Raw sensor reading')
ax.plot(range(1, T_fail + 1), S, color='black', linewidth=2, label='Smoothed trajectory (no repair)')
ax.scatter([T_fail], [S_fail], color='black', zorder=5, s=60, marker='X')
ax.annotate('Actual failure', (T_fail, S_fail), textcoords="offset points", xytext=(-60, 8))

colors = {'Early repair (50% of life)': '#2ecc71', 'Mid repair (70% of life)': '#e67e22', 'Late repair (85% of life)': '#c0392b'}
for name, frac in SCENARIOS.items():
    T_r = int(round(frac * T_fail))
    S_at_repair = S[T_r]
    S_restored = S_at_repair - RESTORE_FRAC * (S_at_repair - S0)
    future_increments = np.diff(S[T_r:])
    path = [S_restored]
    i = 0
    max_steps = 5 * len(future_increments) + 50
    while path[-1] < S_fail and i < max_steps:
        inc = future_increments[i % len(future_increments)]
        path.append(path[-1] + inc)
        i += 1
    xs = np.arange(T_r, T_r + len(path))
    ax.plot(xs, path, '--', color=colors[name], linewidth=1.8, label=f'{name} (branch)')
    ax.scatter([T_r], [S_at_repair], color=colors[name], zorder=5, s=45, marker='v')
    ax.scatter([xs[-1]], [path[-1]], color=colors[name], zorder=5, s=60, marker='X')

ax.axhline(S_fail, color='gray', linestyle=':', linewidth=1)
ax.set_xlabel('Operating cycle')
ax.set_ylabel(f'{SENSOR} reading (lead degradation indicator)')
ax.set_title(f'Counterfactual Maintenance-Timing Branches — Example Engine #{example_unit}\n(\u25bc = repair point, X = resulting failure point)')
ax.legend(fontsize=8, loc='upper left')
fig.tight_layout()
fig.savefig('figures/fig6_counterfactual_branch_example.png', bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------
# Figure 7: life extension distribution by scenario (boxplot)
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 5))
order = list(SCENARIOS.keys())
data_by_scn = [cf[cf.scenario == s]['life_extension_cycles'].values for s in order]
bp = ax.boxplot(data_by_scn, labels=[s.split(' (')[0] for s in order], patch_artist=True)
for patch, s in zip(bp['boxes'], order):
    patch.set_facecolor(colors[s])
    patch.set_alpha(0.6)
ax.set_ylabel('Simulated life extension (cycles)')
ax.set_title('Life Extension by Repair-Timing Scenario (n=100 engines)')
fig.tight_layout()
fig.savefig('figures/fig7_life_extension_boxplot.png', bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------
# Figure 8: net benefit by scenario
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 5))
means = [cf[cf.scenario == s]['net_benefit_usd'].mean() for s in order]
stds = [cf[cf.scenario == s]['net_benefit_usd'].std() for s in order]
bar_colors = [colors[s] for s in order]
ax.bar([s.split(' (')[0] for s in order], means, yerr=stds, color=bar_colors, alpha=0.75, capsize=6)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_ylabel('Mean net benefit (USD, illustrative cost model)')
ax.set_title('Estimated Net Benefit by Repair-Timing Scenario')
fig.tight_layout()
fig.savefig('figures/fig8_net_benefit_by_scenario.png', bbox_inches='tight')
plt.close(fig)

print('Counterfactual tables and figures saved.')
