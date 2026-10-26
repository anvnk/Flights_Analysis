"""Practical work 2: initial-part EDA, without fitting a prediction model.

Run from project root: python scripts/eda.py
Notebook users can call individual functions in order. All EDA uses initial.csv.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'results/figures'
TABLE = ROOT / 'results/tables'
for directory in [FIG, TABLE]:
    directory.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False})


def save_json(name, value):
    (ROOT/'results'/name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                               default=str), encoding='utf-8')


def load_initial():
    df = pd.read_csv(ROOT/'data/initial/initial.csv')
    df['searchDate'] = pd.to_datetime(df['searchDate'], format='%Y-%m-%d')
    df['flightDate'] = pd.to_datetime(df['flightDate'], format='%Y-%m-%d')
    # Recompute source-derived variables without learning any parameters.
    df['days_before_flight'] = (df.flightDate-df.searchDate).dt.days
    df['flight_month'] = df.flightDate.dt.month
    df['flight_day_of_week'] = df.flightDate.dt.day_of_week
    dep = df.segmentsDepartureTimeRaw.str.split('||', regex=False).str[0]
    df['departure_hour'] = dep.str.slice(11, 13).astype(int)
    df['stops_count'] = df.segmentsDepartureTimeRaw.str.count(r'\|\|')
    duration = df.travelDuration.str.extract(r'^PT(?:(\d+)H)?(?:(\d+)M)?$').fillna('0').astype(int)
    df['duration_minutes'] = duration[0]*60+duration[1]
    df['route'] = df.startingAirport+'-'+df.destinationAirport
    df['cabin'] = df.segmentsCabinCode.str.split('||', regex=False).apply(
        lambda x: x[0] if len(set(x)) == 1 else 'mixed')
    df['airlines'] = df.segmentsAirlineName
    df['booking_window'] = pd.cut(df.days_before_flight, [-1,7,14,30,10000],
                                   labels=['0–7', '8–14', '15–30', '31+'])
    return df


def dataset_summary():
    df = load_initial()
    schema = pd.DataFrame({'field': df.columns[:20],
                            'dtype': [str(df[c].dtype) for c in df.columns[:20]],
                            'missing': [int(df[c].isna().sum()) for c in df.columns[:20]],
                            'unique': [int(df[c].nunique()) for c in df.columns[:20]]})
    schema.to_csv(TABLE/'schema.csv', index=False, encoding='utf-8-sig')
    summary = {'rows': len(df), 'source_columns': 20,
               'search_min': str(df.searchDate.min().date()),
               'search_max': str(df.searchDate.max().date()),
               'flight_min': str(df.flightDate.min().date()),
               'flight_max': str(df.flightDate.max().date()),
               'routes': int(df.route.nunique()), 'airline_itineraries': int(df.airlines.nunique()),
               'cabin_counts': df.cabin.value_counts().to_dict()}
    save_json('summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return df


def quality_report():
    df = load_initial()
    key = ['searchDate','legId','totalFare']
    numeric = df.totalFare.describe(percentiles=[.25,.5,.75,.95,.99])
    q1,q3 = df.totalFare.quantile([.25,.75])
    low,high = q1-1.5*(q3-q1), q3+1.5*(q3-q1)
    invalid = {
        'invalid_date_order': int((df.flightDate < df.searchDate).sum()),
        'nonpositive_price': int((~np.isfinite(df.totalFare) | (df.totalFare<=0)).sum()),
        'invalid_airport': int((~df.startingAirport.str.fullmatch('[A-Z]{3}') |
                                ~df.destinationAirport.str.fullmatch('[A-Z]{3}')).sum()),
        'same_airports': int((df.startingAirport==df.destinationAirport).sum()),
        'invalid_seats': int((~np.isfinite(df.seatsRemaining) | df.seatsRemaining.lt(0)
                              | df.seatsRemaining.ne(np.floor(df.seatsRemaining))).sum()),
        'nonpositive_distance': int((df.totalTravelDistance.dropna()<=0).sum()),
        'nonpositive_duration': int((df.duration_minutes<=0).sum()),
        'inconsistent_nonstop': int((df.isNonStop != df.stops_count.eq(0)).sum()),
    }
    report = {'rows':len(df), 'missing': df.iloc[:,:20].isna().sum().to_dict(),
              'duplicate_full_rows':int(df.iloc[:,:20].duplicated().sum()),
              'duplicate_observation_key':int(df.duplicated(key).sum()),
              'repeated_legId':int(df.legId.duplicated().sum()),
              'invalid':invalid, 'price_stats_usd':numeric.to_dict(),
              'iqr_low':float(low),'iqr_high':float(high),
              'iqr_outlier_count':int((~df.totalFare.between(low,high)).sum()),
              'distance_missing_pct':float(df.totalTravelDistance.isna().mean()*100),
              'seat_counts':df.seatsRemaining.value_counts().sort_index().to_dict()}
    save_json('quality.json', report)
    pd.DataFrame({'field': list(report['missing']), 'missing': list(report['missing'].values())}).to_csv(TABLE/'missing.csv',index=False)
    print('Начальная часть:',len(df),'записей')
    print('Пропуски расстояния:', report['missing']['totalTravelDistance'],
          f"({report['distance_missing_pct']:.2f}%)")
    print('Полные дубликаты:',report['duplicate_full_rows'])
    print('Дубликаты ключа наблюдения:',report['duplicate_observation_key'])
    print('Нарушений проверок допустимости:',sum(invalid.values()))
    print('Выбросы цены по IQR:',report['iqr_outlier_count'],
          f'; верхняя граница {high:.2f} USD')
    print(numeric.round(2).to_string())
    return report


def price_plots():
    df = load_initial()
    fig,ax = plt.subplots(1,2,figsize=(11,3.7))
    ax[0].hist(df.totalFare,bins=35,color='#44728b',edgecolor='white')
    ax[0].set(xlabel='Стоимость, USD',ylabel='Число предложений',title='Распределение цены')
    ax[1].boxplot(df.totalFare,orientation='horizontal',showmeans=True)
    ax[1].set(xlabel='Стоимость, USD',yticks=[],title='Разброс и выбросы')
    fig.tight_layout(); fig.savefig(FIG/'price.png',dpi=190,bbox_inches='tight'); plt.close(fig)
    print('График сохранён: results/figures/price.png')


def relationship_plots():
    df=load_initial()
    fig,ax=plt.subplots(1,3,figsize=(12,3.6))
    for a,x,label in [(ax[0],'days_before_flight','Дней до вылета'),
                      (ax[1],'totalTravelDistance','Расстояние, мили'),
                      (ax[2],'duration_minutes','Длительность, мин')]:
        a.scatter(df[x],df.totalFare,s=9,alpha=.3,color='#36617b')
        a.set(xlabel=label,ylabel='Цена, USD')
    fig.tight_layout(); fig.savefig(FIG/'relationships.png',dpi=190,bbox_inches='tight');plt.close(fig)
    booking=df.groupby('booking_window',observed=True).totalFare.agg(['count','median','mean'])
    stops=df.groupby('stops_count').totalFare.agg(['count','median'])
    cabins=df.groupby('cabin').totalFare.agg(['count','median'])
    airlines=df.groupby('airlines').totalFare.agg(['count','median']).query('count >= 20').sort_values('median')
    for name,table in [('booking',booking),('stops',stops),('cabins',cabins),('airlines',airlines)]:
        table.to_csv(TABLE/(name+'.csv'),encoding='utf-8-sig')
    fig,ax=plt.subplots(1,3,figsize=(11,3.8))
    for a,tab,label in [(ax[0],booking,'Срок до вылета, дней'),
                        (ax[1],stops,'Число пересадок'),(ax[2],cabins,'Класс обслуживания')]:
        a.bar(tab.index.astype(str),tab['median'],color='#44728b')
        a.set(xlabel=label,ylabel='Медиана цены, USD')
        a.tick_params(axis='x',labelrotation=25)
    fig.tight_layout(); fig.savefig(FIG/'groups.png',dpi=190,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.0))
    ax.barh(airlines.index,airlines['median'],color='#44728b')
    ax.set(xlabel='Медиана цены, USD',title='Перевозчики и комбинации, не менее 20 наблюдений')
    fig.tight_layout();fig.savefig(FIG/'airlines.png',dpi=190,bbox_inches='tight');plt.close(fig)
    print('Окна бронирования:\n',booking.round(2).to_string())
    print('\nПересадки:\n',stops.round(2).to_string())
    print('\nКлассы:\n',cabins.round(2).to_string())


def correlation_report():
    df=load_initial()
    cols=['totalFare','days_before_flight','totalTravelDistance','duration_minutes',
          'stops_count','seatsRemaining','flight_month','flight_day_of_week']
    corr=df[cols].corr(method='spearman')
    corr.to_csv(TABLE/'spearman.csv')
    labels=['Цена','Дней до вылета','Расстояние','Длительность','Пересадки',
            'Доступные места','Месяц вылета','День недели']
    fig,ax=plt.subplots(figsize=(9,6))
    im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r')
    ax.set_xticks(range(len(cols)),labels,rotation=40,ha='right')
    ax.set_yticks(range(len(cols)),labels)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',fontsize=9,
                    color='white' if abs(corr.iloc[i,j])>.65 else 'black')
    fig.colorbar(im,ax=ax,label='Коэффициент Спирмена')
    fig.tight_layout();fig.savefig(FIG/'correlations.png',dpi=190,bbox_inches='tight');plt.close(fig)
    print('Корреляции с ценой:\n',corr.totalFare.round(3).to_string())
    print('\nРасстояние и длительность:',round(corr.loc['totalTravelDistance','duration_minutes'],3))
    return corr


def hypothesis_report():
    df=load_initial()
    # Exploratory tests. Repeated searches and route/class mix prevent causal interpretation.
    near=df.loc[df.days_before_flight<=7,'totalFare']
    far=df.loc[df.days_before_flight>=30,'totalFare']
    one=df.loc[df.isNonStop,'totalFare']
    many=df.loc[~df.isNonStop,'totalFare']
    distance=df[['totalTravelDistance','totalFare']].dropna()
    rho,p=stats.spearmanr(distance.totalTravelDistance,distance.totalFare)
    tests=[{'id':'H1','question':'Цена при сроке до вылета не более 7 дней выше, чем при сроке от 30 дней',
            'test':'Mann–Whitney, two-sided','n1':len(near),'n2':len(far),
            'median1':float(near.median()),'median2':float(far.median()),
            'p':float(stats.mannwhitneyu(near,far,alternative='two-sided').pvalue),
            'direction_supported':bool(near.median()>far.median())},
           {'id':'H2','question':'С увеличением расстояния цена повышается',
            'test':'Spearman','n':len(distance),'rho':float(rho),'p':float(p),
            'direction_supported':bool(rho>0)},
           {'id':'H3','question':'Предложения с пересадками дороже прямых в общей выборке',
            'test':'Mann–Whitney, two-sided','n1':len(many),'n2':len(one),
            'median1':float(many.median()),'median2':float(one.median()),
            'p':float(stats.mannwhitneyu(many,one,alternative='two-sided').pvalue),
            'direction_supported':bool(many.median()>one.median())}]
    # Holm correction over these three exploratory tests.
    ordered=sorted(range(3),key=lambda i:tests[i]['p'])
    prev=0.
    for rank,i in enumerate(ordered):
        adjusted=min(1.,max(prev,(3-rank)*tests[i]['p']))
        tests[i]['p_holm']=adjusted
        tests[i]['supported_exploratory']=bool(adjusted<.05 and tests[i]['direction_supported'])
        prev=adjusted
    save_json('hypotheses.json',tests)
    pd.DataFrame(tests).to_csv(TABLE/'hypotheses.csv',index=False,encoding='utf-8-sig')
    for t in tests:
        print(t['id'],t['question'])
        if t['id']=='H2':
            print(f"  n={t['n']}; rho={t['rho']:.3f}; p Holm={t['p_holm']:.3g}")
        else:
            print(f"  n={t['n1']}/{t['n2']}; медианы={t['median1']:.2f}/{t['median2']:.2f} USD; p Holm={t['p_holm']:.3g}")
        print('  Поддерживается в EDA:',t['supported_exploratory'])
    print('Результаты разведочные: состав маршрутов и классов, повторные наблюдения не контролируются.')
    return tests


def artifact_inventory():
    files=sorted(p for p in (ROOT/'results').rglob('*')
                 if p.is_file() and p.name!='artifact_inventory.json')
    inventory=[{'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
                'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    save_json('artifact_inventory.json',inventory)
    print('Сохранено результатов:',len(inventory))


def main():
    dataset_summary(); quality_report(); price_plots(); relationship_plots()
    correlation_report(); hypothesis_report(); artifact_inventory()


if __name__=='__main__':
    main()
