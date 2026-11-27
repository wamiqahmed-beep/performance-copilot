"""Reproduce Phase 2. First run: validation only. Then --finalize once.
Later runs regenerate exports from the recorded evaluation without retesting.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, silhouette_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'model-output'
COUNTRIES = [('Türkiye','TRY',.029,1.38),('Germany','EUR',1,1.13),('United Kingdom','GBP',1.17,1.05),('France','EUR',1,.91),('Poland','PLN',.23,.79),('Romania','RON',.20,.57)]
BRANDS = [('Beko',1),('Arçelik',1.13),('Grundig',1.27)]
CHANNELS = [('Retail',1),('Online',.73),('Dealer',.86)]
FEATURES = ['log_lag1','log_lag2','log_lag12','log_mean3','log_mean12','month_sin','month_cos','time','fx_lag1','fx_change']
SPLIT = {'train_end':'2024-12','validation_start':'2025-01','validation_end':'2025-06','test_start':'2025-07','test_end':'2025-12'}

def generate():
    # Existing CSV remains the canonical, immutable Phase 1 data.
    original = pd.read_csv(ROOT / 'dummy-pnl.csv')
    records = []
    for m in range(-36, 0):
        date = (pd.Period('2023-01',freq='M') + m).strftime('%Y-%m')
        for ci,(country,currency,fx,scale) in enumerate(COUNTRIES):
            for bi,(brand,bp) in enumerate(BRANDS):
                for hi,(channel,cs) in enumerate(CHANNELS):
                    season=1+.13*math.sin((m%12-3)*math.pi/6)
                    base=1350*scale*cs*(1-bi*.15)*season*(1+.008*m)
                    bu=math.floor(base+.5)
                    au=math.floor(base*(1+.08*math.sin(m*.55+ci*1.8+bi*.7+hi*.5)+[.015,-.065,.075,-.025,.045,-.075][ci])+.5)
                    bf=fx*(1-.002*m*(1.9 if ci==0 else .3 if ci==4 else 0))
                    af=bf*(1+.025*math.sin(m*.27+ci))
                    price=(270+bi*65+hi*12)/bf
                    ap=price*(1+.025*math.cos(m*.4+ci+bi))
                    br=bu*price; ar=au*ap
                    records.append(dict(zip(original.columns,[date,country,currency,brand,channel,bu,au,br,ar,br*(.66+bi*.015+hi*.01),ar*(.66+bi*.015+hi*.01+.018*math.sin(m*.31+ci+hi)),bf,af])))
    df=pd.concat([pd.DataFrame(records),original],ignore_index=True)
    assert len(df)==3888 and not df.duplicated(['date','country','brand','channel']).any()
    pd.testing.assert_frame_equal(df[df.date>='2023-01'].reset_index(drop=True),original,check_dtype=False)
    df.to_csv(OUT/'updated-pnl.csv',index=False,float_format='%.8f')
    return df

def aggregate(df):
    x=df.assign(revenue=df.actual_revenue_local*df.actual_fx,budget=df.budget_revenue_local*df.budget_fx)
    return x.groupby(['date','country'],as_index=False).agg(revenue=('revenue','sum'),budget=('budget','sum'),fx=('actual_fx','first'))

def features(history, future=False):
    x=history.copy()
    if future:
        extra=[]
        for ci,(country,currency,fx,scale) in enumerate(COUNTRIES):
            budget=0
            for bi,_ in enumerate(BRANDS):
                for hi,(_,cs) in enumerate(CHANNELS):
                    base=1350*scale*cs*(1-bi*.15)*(1+.13*math.sin(-3*math.pi/6))*(1+.008*36)
                    budget+=math.floor(base+.5)*(270+bi*65+hi*12)
            extra.append({'date':'2026-01','country':country,'budget':budget,'revenue':np.nan,'fx':np.nan})
        x=pd.concat([x,pd.DataFrame(extra)],ignore_index=True)
    x=x.sort_values(['country','date']).reset_index(drop=True)
    g=x.groupby('country')
    for lag in [1,2,12]: x[f'lag{lag}']=g.revenue.shift(lag); x[f'log_lag{lag}']=np.log(x[f'lag{lag}'])
    for n in [3,12]: x[f'log_mean{n}']=np.log(g.revenue.transform(lambda s:s.shift(1).rolling(n).mean()))
    x['fx_lag1']=g.fx.shift(1)
    x['fx_change']=g.fx.shift(1)/g.fx.shift(2)-1
    month=x.date.str[5:].astype(int)
    x['month_sin']=np.sin(2*np.pi*month/12); x['month_cos']=np.cos(2*np.pi*month/12)
    x['time']=(x.date.str[:4].astype(int)-2020)*12+month-1
    return x.dropna(subset=FEATURES)

def pipeline(alpha):
    prep=ColumnTransformer([('numeric',StandardScaler(),FEATURES),('country',OneHotEncoder(handle_unknown='ignore',sparse_output=False),['country'])])
    return make_pipeline(prep,Ridge(alpha=alpha))

def fit(x,alpha):
    model=pipeline(alpha); model.fit(x[FEATURES+['country']],np.log(x.revenue)); return model

def predict(model,x): return np.exp(model.predict(x[FEATURES+['country']]))

def scores(y,p): return {'mae':float(mean_absolute_error(y,p)),'wape':float(np.abs(y-p).sum()/y.sum()),'bias':float(np.mean(p-y))}

def profiles(df,end):
    start=(pd.Period(end,freq='M')-11).strftime('%Y-%m'); records=[]
    for country,g in df[(df.date>=start)&(df.date<=end)].groupby('country'):
        effects=np.zeros(4); budget=0.; revenue=0.
        for _,r in g.groupby('date'):
            qb=r.budget_units.sum(); qa=r.actual_units.sum(); pb=r.budget_revenue_local/r.budget_units; pa=r.actual_revenue_local/r.actual_units
            b=(r.budget_revenue_local*r.budget_fx).sum(); a=(r.actual_revenue_local*r.actual_fx).sum()
            effects+=np.array([(qa-qb)*b/qb,(qa*(r.actual_units/qa-r.budget_units/qb)*pb*r.budget_fx).sum(),(r.actual_units*(pa-pb)*r.budget_fx).sum(),(r.actual_units*pa*(r.actual_fx-r.budget_fx)).sum()])
            budget+=b; revenue+=a
        assert abs(effects.sum()-(revenue-budget))<.01
        records.append({'country':country,'revenue':revenue,'budget':budget,**dict(zip(['volume','mix','price','FX'],effects/budget))})
    return pd.DataFrame(records)

def segment_setup(df):
    p=profiles(df,'2025-06'); scaler=StandardScaler().fit(p[['volume','mix','price','FX']]); z=scaler.transform(p[['volume','mix','price','FX']]); trials=[]
    for k in range(2,5):
        km=KMeans(n_clusters=k,n_init=30,random_state=27).fit(z)
        trials.append({'k':k,'inertia':float(km.inertia_),'silhouette':float(silhouette_score(z,km.labels_)),'min_size':int(np.bincount(km.labels_).min())})
    eligible=[t for t in trials if t['min_size']>=2] or trials
    best=max(t['silhouette'] for t in eligible)
    chosen=min(t['k'] for t in eligible if t['silhouette']>=best-.05)
    return scaler,KMeans(n_clusters=chosen,n_init=30,random_state=27).fit(z),trials

def clean(records):
    return json.loads(pd.DataFrame(records).to_json(orient='records'))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--finalize',action='store_true'); args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    df=generate(); monthly=aggregate(df); x=features(monthly)
    train=x[x.date<='2024-12']; val=x[(x.date>='2025-01')&(x.date<='2025-06')]
    assert train.date.max()<val.date.min() and val.date.max()<SPLIT['test_start']
    trials=[]
    for alpha in [.01,.1,1.,10.]:
        trials.append({'alpha':alpha,**scores(val.revenue,predict(fit(train,alpha),val))})
    alpha=min(trials,key=lambda t:t['mae'])['alpha']
    scaler,km,cluster_trials=segment_setup(df)
    contract={'split':SPLIT,'features':FEATURES,'alphas':[.01,.1,1.,10.],'selected_alpha':alpha,'k':int(km.n_clusters),'seed':27,'selection':'validation MAE; clusters: no singletons if possible, smallest k within .05 of best silhouette','test_protocol':'fixed coefficients; sequential one-month-ahead; no shuffle','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'data_sha256':hashlib.sha256((OUT/'updated-pnl.csv').read_bytes()).hexdigest()}
    frozen=OUT/'frozen-design.json'; evaluated=OUT/'final-evaluation.json'
    if frozen.exists():
        assert json.loads(frozen.read_text())==contract,'Frozen design changed: preserve the recorded test; do not retune against it.'
    else: frozen.write_text(json.dumps(contract,indent=2))
    validation={'ridge_trials':trials,'last_month':scores(val.revenue,val.lag1),'seasonal_naive':scores(val.revenue,val.lag12),'clusters':cluster_trials}
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2))
    print(json.dumps(validation,indent=2))
    if not evaluated.exists():
        if not args.finalize:
            print('Design frozen. Test untouched. Run --finalize once to evaluate and export.'); return
        test=x[(x.date>='2025-07')&(x.date<='2025-12')].copy()
        model=fit(x[x.date<='2025-06'],alpha); test['prediction']=predict(model,test)
        test['error']=test.prediction-test.revenue
        result={'metrics':{'Ridge':scores(test.revenue,test.prediction),'Last month':scores(test.revenue,test.lag1),'Same month last year':scores(test.revenue,test.lag12)},'rows':clean(test[['date','country','revenue','budget','prediction','error','lag1','lag12']]),'by_country':[],'by_month':[]}
        for key,target in [('country','by_country'),('date','by_month')]:
            result[target]=[{key:name,**scores(g.revenue,g.prediction)} for name,g in test.groupby(key)]
        result['coefficients']=[{'feature':n,'coefficient':float(v)} for n,v in zip(model[0].get_feature_names_out(),model[1].coef_)]
        evaluated.write_text(json.dumps(result,indent=2))
    result=json.loads(evaluated.read_text())
    # Production fit is separate; no evaluation of its historical fitted values.
    future=features(monthly,True); live=future[future.date=='2026-01'].copy()
    production=fit(x,alpha); live['prediction']=predict(production,live); live['predicted_gap']=live.prediction/live.budget-1
    live['forecast_flag']=np.where(live.predicted_gap>.05,'Above +5%',np.where(live.predicted_gap<-.05,'Below -5%','Within range'))
    live['as_of']='2025-12'; live['fx_assumption']=live.fx_lag1
    p=profiles(df,'2025-12'); p['segment']=km.predict(scaler.transform(p[['volume','mix','price','FX']]))
    live=live.merge(p[['country','segment']],on='country')
    segments=[]; actions={'volume':'Review demand, distribution and sales execution.','mix':'Review brand/channel mix and availability.','price':'Review discounts and realised selling prices.','FX':'Review currency exposure and budget FX assumptions.'}
    for label,g in p.groupby('segment'):
        driver=g[['volume','mix','price','FX']].abs().mean().idxmax()
        segments.append({'id':int(label),'name':f'{driver.capitalize()}-led markets','size':len(g),'value':float(g.revenue.sum()),'share':float(g.revenue.sum()/p.revenue.sum()),'countries':g.country.tolist(),'profile':{n:float(g[n].mean()) for n in ['volume','mix','price','FX']},'action':actions[driver]})
    live[['date','as_of','country','budget','prediction','predicted_gap','forecast_flag','fx_assumption','segment']].to_csv(OUT/'country-predictions.csv',index=False)
    p.to_csv(OUT/'country-segments.csv',index=False)
    pd.DataFrame(result['rows']).to_csv(OUT/'test-predictions.csv',index=False)
    bundle={'contract':contract,'validation':validation,'evaluation':result,'forecasts':clean(live[['date','as_of','country','budget','prediction','predicted_gap','forecast_flag','segment']]),'segments':segments,'profiles':clean(p),'pnl':clean(df)}
    (ROOT/'model-data.js').write_text('window.MODEL_DATA = '+json.dumps(bundle,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8')
    print('Final test recorded; static assets exported. '+json.dumps(result['metrics']))

if __name__=='__main__': main()
