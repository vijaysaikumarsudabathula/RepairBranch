"""
RepairBranch - Step 2: Exploratory Data Analysis
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams.update({'figure.dpi': 130, 'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3})

train = pd.read_csv('data/train_fd001_rul.csv')

CONSTANT_SENSORS = ['sensor_1','sensor_5','sensor_6','sensor_10','sensor_16','sensor_18','sensor_19']
USEFUL_SENSORS = [f'sensor_{i}' for i in range(1,22) if f'sensor_{i}' not in CONSTANT_SENSORS]

# ---------------------------------------------------------------
# Table 1: Dataset summary
# ---------------------------------------------------------------
summary = pd.DataFrame({
    'Metric': [
        'Training engine units', 'Test engine units', 'Training rows (cycle snapshots)',
        'Test rows (cycle snapshots)', 'Sensors recorded', 'Informative sensors (non-constant)',
        'Operating conditions', 'Fault modes', 'Min cycles to failure (train)',
        'Max cycles to failure (train)', 'Mean cycles to failure (train)'
    ],
    'Value': [
        train.unit.nunique(),
        100,
        train.shape[0],
        13096,
        21,
        len(USEFUL_SENSORS),
        1,
        1,
        train.groupby('unit')['cycle'].max().min(),
        train.groupby('unit')['cycle'].max().max(),
        round(train.groupby('unit')['cycle'].max().mean(), 1)
    ]
})
summary.to_csv('tables/table1_dataset_summary.csv', index=False)
print(summary)

# ---------------------------------------------------------------
# Figure 1: Sensor degradation trends (normalized life %) for 6 sample engines
# ---------------------------------------------------------------
sample_units = [1, 15, 32, 47, 68, 90]
key_sensors = ['sensor_2', 'sensor_3', 'sensor_4', 'sensor_11', 'sensor_15', 'sensor_17']

fig, axes = plt.subplots(2, 3, figsize=(13, 7))
for ax, sensor in zip(axes.flat, key_sensors):
    for u in sample_units:
        sub = train[train.unit == u]
        life_pct = sub['cycle'] / sub['cycle'].max() * 100
        ax.plot(life_pct, sub[sensor], alpha=0.8, linewidth=1.2)
    ax.set_title(sensor.replace('_', ' ').title())
    ax.set_xlabel('% of engine life')
    ax.set_ylabel('Sensor reading')
fig.suptitle('Sensor Degradation Trends Across Engine Life (6 sample engines, FD001)', fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig('figures/fig1_sensor_trends.png', bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------
# Figure 2: Correlation of informative sensors with RUL
# ---------------------------------------------------------------
corr = train[USEFUL_SENSORS + ['RUL']].corr()['RUL'].drop('RUL').sort_values()
fig, ax = plt.subplots(figsize=(7, 6))
colors = ['#c0392b' if v < 0 else '#2471a3' for v in corr.values]
ax.barh(corr.index, corr.values, color=colors)
ax.axvline(0, color='black', linewidth=0.8)
ax.set_title('Sensor Correlation with Remaining Useful Life (RUL)')
ax.set_xlabel('Pearson correlation with RUL')
fig.tight_layout()
fig.savefig('figures/fig2_sensor_rul_correlation.png', bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------
# Figure 3: RUL distribution across training set
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.hist(train['RUL'], bins=40, color='#2471a3', edgecolor='white')
ax.set_title('Distribution of Remaining Useful Life (Training Set)')
ax.set_xlabel('RUL (cycles)')
ax.set_ylabel('Count of cycle-snapshots')
fig.tight_layout()
fig.savefig('figures/fig3_rul_distribution.png', bbox_inches='tight')
plt.close(fig)

print('EDA figures and table1 saved.')
