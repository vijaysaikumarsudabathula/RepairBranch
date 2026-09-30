"""
RepairBranch - Step 1: Load & preprocess NASA C-MAPSS FD001
"""
import pandas as pd
import numpy as np

COLS = ['unit','cycle','os1','os2','os3'] + [f'sensor_{i}' for i in range(1,22)]

def load_fd001(data_dir='data'):
    train = pd.read_csv(f'{data_dir}/train_FD001.txt', sep=r'\s+', header=None, names=COLS)
    test  = pd.read_csv(f'{data_dir}/test_FD001.txt',  sep=r'\s+', header=None, names=COLS)
    rul   = pd.read_csv(f'{data_dir}/RUL_FD001.txt',   sep=r'\s+', header=None, names=['RUL'])
    return train, test, rul

def add_rul(train, clip=125):
    max_cycle = train.groupby('unit')['cycle'].transform('max')
    train = train.copy()
    train['RUL'] = max_cycle - train['cycle']
    train['RUL_clipped'] = train['RUL'].clip(upper=clip)
    return train

# Sensors with zero variance in FD001 (uninformative for a single operating condition)
CONSTANT_SENSORS = ['sensor_1','sensor_5','sensor_6','sensor_10','sensor_16','sensor_18','sensor_19']
USEFUL_SENSORS = [f'sensor_{i}' for i in range(1,22) if f'sensor_{i}' not in CONSTANT_SENSORS]

if __name__ == '__main__':
    train, test, rul = load_fd001()
    train = add_rul(train)
    print('Train:', train.shape, 'units:', train.unit.nunique())
    print('Test:', test.shape, 'units:', test.unit.nunique())
    print('Useful sensors:', len(USEFUL_SENSORS))
    train.to_csv('data/train_fd001_rul.csv', index=False)
    test.to_csv('data/test_fd001.csv', index=False)
    rul.to_csv('data/rul_fd001.csv', index=False)
    print('Saved preprocessed csv files.')
