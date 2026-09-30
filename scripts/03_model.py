"""
RepairBranch - Step 3: RUL prediction model (Random Forest)
Includes rolling-window features, NASA PHM08 scoring function, and evaluation artifacts.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

plt.rcParams.update({'figure.dpi': 130, 'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3})

CONSTANT_SENSORS = ['sensor_1','sensor_5','sensor_6','sensor_10','sensor_16','sensor_18','sensor_19']
USEFUL_SENSORS = [f'sensor_{i}' for i in range(1,22) if f'sensor_{i}' not in CONSTANT_SENSORS]
WINDOW = 5

def add_rolling_features(df, sensors=USEFUL_SENSORS, window=WINDOW):
    df = df.sort_values(['unit', 'cycle']).copy()
    grouped = df.groupby('unit')[sensors]
    roll_mean = grouped.rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
    roll_std = grouped.rolling(window, min_periods=1).std().fillna(0).reset_index(level=0, drop=True)
    roll_mean.columns = [f'{c}_rmean{window}' for c in sensors]
    roll_std.columns = [f'{c}_rstd{window}' for c in sensors]
    return pd.concat([df, roll_mean, roll_std], axis=1)

def nasa_score(y_true, y_pred):
    """PHM08 / NASA scoring function: asymmetric penalty, late predictions cost more."""
    d = y_pred - y_true
    score = np.where(d < 0, np.exp(-d/13) - 1, np.exp(d/10) - 1)
    return score.sum()

if __name__ == '__main__':
    train = pd.read_csv('data/train_fd001_rul.csv')
    test = pd.read_csv('data/test_fd001.csv')
    rul_truth = pd.read_csv('data/rul_fd001.csv')['RUL'].values

    train_f = add_rolling_features(train)
    test_f = add_rolling_features(test)

    feature_cols = [c for c in train_f.columns if c not in ['unit','cycle','os1','os2','os3','RUL','RUL_clipped']]

    X = train_f[feature_cols]
    y = train_f['RUL_clipped']
    groups = train_f['unit']

    # Grouped CV (by engine unit) so no engine leaks across folds
    import time
    gkf = GroupKFold(n_splits=5)
    cv_rmses = []
    for i, (tr_idx, va_idx) in enumerate(gkf.split(X, y, groups)):
        t0 = time.time()
        m = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42, n_jobs=1)
        m.fit(X.iloc[tr_idx], y.iloc[tr_idx])
        pred = m.predict(X.iloc[va_idx])
        cv_rmses.append(np.sqrt(mean_squared_error(y.iloc[va_idx], pred)))
        print(f'fold {i} done in {time.time()-t0:.1f}s', flush=True)
    print('5-fold GroupCV RMSE (train):', np.round(cv_rmses, 2), 'mean=', np.mean(cv_rmses).round(2))

    # Final model on full training data
    t0 = time.time()
    model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=1)
    model.fit(X, y)
    print(f'final model fit in {time.time()-t0:.1f}s', flush=True)

    # Test set: take the LAST cycle snapshot per unit (standard C-MAPSS protocol)
    test_last = test_f.sort_values(['unit','cycle']).groupby('unit').tail(1).reset_index(drop=True)
    X_test = test_last[feature_cols]
    y_test_pred = model.predict(X_test)
    y_test_pred = np.clip(y_test_pred, 0, None)

    rmse = np.sqrt(mean_squared_error(rul_truth, y_test_pred))
    mae = mean_absolute_error(rul_truth, y_test_pred)
    r2 = r2_score(rul_truth, y_test_pred)
    score = nasa_score(rul_truth, y_test_pred)

    perf = pd.DataFrame({
        'Metric': ['CV RMSE (train, 5-fold GroupKFold)', 'Test RMSE', 'Test MAE', 'Test R2', 'NASA PHM08 Score (lower=better)'],
        'Value': [round(np.mean(cv_rmses),2), round(rmse,2), round(mae,2), round(r2,3), round(score,1)]
    })
    perf.to_csv('tables/table2_model_performance.csv', index=False)
    print(perf)

    # Feature importance (aggregate rolling-mean/std back to base sensor for readability)
    importances = pd.Series(model.feature_importances_, index=feature_cols)
    base_importance = {}
    for feat, val in importances.items():
        base = feat.split('_rmean')[0].split('_rstd')[0]
        base_importance[base] = base_importance.get(base, 0) + val
    fi = pd.Series(base_importance).sort_values(ascending=False)
    fi_table = fi.reset_index()
    fi_table.columns = ['Sensor', 'Aggregated Importance']
    fi_table.to_csv('tables/table3_feature_importance.csv', index=False)

    # Figure 4: predicted vs actual RUL (test set)
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(rul_truth, y_test_pred, alpha=0.6, edgecolor='k', linewidth=0.3)
    lims = [0, max(rul_truth.max(), y_test_pred.max()) + 5]
    ax.plot(lims, lims, 'r--', linewidth=1, label='Perfect prediction')
    ax.set_xlabel('Actual RUL (cycles)')
    ax.set_ylabel('Predicted RUL (cycles)')
    ax.set_title(f'Figure 4. Predicted vs Actual RUL — Test Set (n=100 engines)\nRMSE={rmse:.1f}, MAE={mae:.1f}, R2={r2:.2f}')
    ax.legend()
    fig.tight_layout()
    fig.savefig('figures/fig4_pred_vs_actual_rul.png', bbox_inches='tight')
    plt.close(fig)

    # Figure 5: feature importance bar chart (top 12)
    fig, ax = plt.subplots(figsize=(7, 6))
    top = fi.head(12)
    ax.barh(top.index[::-1], top.values[::-1], color='#2471a3')
    ax.set_title('Figure 5. Top 12 Sensors by Aggregated Feature Importance (Random Forest)')
    ax.set_xlabel('Aggregated importance (raw + rolling mean/std)')
    fig.tight_layout()
    fig.savefig('figures/fig5_feature_importance.png', bbox_inches='tight')
    plt.close(fig)

    # Save model + features + test predictions for downstream counterfactual step
    test_last[['unit','cycle']].assign(pred_RUL=y_test_pred, true_RUL=rul_truth).to_csv('tables/table_test_predictions.csv', index=False)

    import joblib
    joblib.dump(model, 'data/rf_rul_model.joblib')
    print('Model, tables, and figures saved.')
