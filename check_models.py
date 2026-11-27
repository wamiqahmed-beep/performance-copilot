"""Availability and export invariants; does not fit or retest a model."""
import json
import numpy as np
import pandas as pd
from train_models import ROOT, OUT, FEATURES, aggregate, features

pnl=pd.read_csv(OUT/'updated-pnl.csv')
original=pd.read_csv(ROOT/'dummy-pnl.csv')
pd.testing.assert_frame_equal(pnl[pnl.date>='2023-01'].reset_index(drop=True),original,check_exact=False,rtol=1e-10,atol=1e-7)
monthly=aggregate(pnl)
base=features(monthly)
changed=monthly.copy()
changed.loc[changed.date>='2025-07',['revenue','fx']]*=10
altered=features(changed)
# July's outcome and every later outcome cannot change the July inputs.
pd.testing.assert_frame_equal(base[base.date<='2025-07'][FEATURES],altered[altered.date<='2025-07'][FEATURES])
for country,g in base.groupby('country'):
    source=monthly[monthly.country==country].set_index('date')
    for row in g.itertuples():
        previous=(pd.Period(row.date,freq='M')-1).strftime('%Y-%m')
        assert np.isclose(row.lag1,source.loc[previous,'revenue'])
        assert np.isclose(row.fx_lag1,source.loc[previous,'fx'])
evaluation=json.loads((OUT/'final-evaluation.json').read_text())
assert len(evaluation['rows'])==36
assert all('2025-07'<=r['date']<='2025-12' for r in evaluation['rows'])
for key,col in [('Ridge','prediction'),('Last month','lag1'),('Same month last year','lag12')]:
    errors=[abs(r[col]-r['revenue']) for r in evaluation['rows']]
    assert np.isclose(np.mean(errors),evaluation['metrics'][key]['mae'])
print('PASS: Phase 1 preservation, future-perturbation leakage check, lag availability, test split and metrics.')
