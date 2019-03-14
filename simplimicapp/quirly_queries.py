import os
import sys
import re
import datetime
import json
import numpy as np
import pandas as pd

pd.set_option('display.max_columns', None)
import django
sys.path.append("../simplimic")
# sys.path.insert(0, '../simplimic')
os.environ['DJANGO_SETTINGS_MODULE'] = 'simplimic.settings'
django.setup()
from django_pandas.io import read_frame
from simplimicapp.models import *


def add_hours_elpased_to_events(events, dt, remove_charttime=True):
    """
<<<<<<< HEAD
    Yet another helper stolen from the good people at:
    https://github.com/YerevaNN/mimic3-benchmarks/blob/master/mimic3benchmark/subject.py
    <3
    :param events:
    :param dt:
    :param remove_charttime:
=======
    Queries the information on the corresponding admission and outputs:
     - an xarray with all descriptor values (unpreprocessed)in destacked long form (date_time index).
        dim0: time
        dim1: itemIDs
        dim2: param (e.g.: value, unit, flag, kind)
     - a df holding the meta information on Subject, Outcome, Diagnosis.
    :param admID:
>>>>>>> ef51ef1d6af2ad98f8afd2d127f732db4877db2c
    :return:
    """
    if not isinstance(events['chart_time'].values[0], datetime.datetime):
        events['chart_time'] = pd.to_datetime(events['chart_time'])

<<<<<<< HEAD
    events['hours'] = (events['chart_time'] - dt).apply(lambda s: s / np.timedelta64(1, 's')) / 60./60
    if remove_charttime:
        del events['chart_time']
    return events

=======
    # get the info on the admission period:
    admission = Admission.objects.filter(admID=admID)
    admission_df = read_frame(admission).set_index('admID')
    
    # get info on diagnosis:
    diagnoses = Diagnosis.objects.filter(admID=admID)
    diagnoses_df = read_frame(diagnoses).set_index('admID')
    
    return descriptor_ds, admission_df, diagnoses_df
>>>>>>> ef51ef1d6af2ad98f8afd2d127f732db4877db2c

def _events_to_ts(events, variable_col, value, variables=[]):
    """
    helper to turn an events file into an indexed ts.

    Stolen from https://github.com/YerevaNN/mimic3-benchmarks/blob/master/mimic3benchmark/subject.py
    :param events:
    :param variable_col:
    :return:
    """
    metadata = events[['chart_time', 'icustayID']].sort_values(by=['chart_time', 'icustayID']) \
        .drop_duplicates(keep='first').set_index('chart_time')

    timeseries = events[['chart_time', variable_col, value]] \
        .sort_values(by=['chart_time', variable_col, value], axis=0) \
        .drop_duplicates(subset=['chart_time', variable_col], keep='last')
    timeseries = timeseries.pivot(index='chart_time', columns=variable_col, values=value)
    timeseries = pd.concat([metadata, timeseries], axis=1)

    for v in variables:
        if v not in timeseries:
            timeseries[v] = np.nan

    return timeseries


def get_stay_chart_timeseries(icustay_id):
    """
    For given ICU-stay ID -> get the events as time series.
    :return:
    """
    # read in the items.json and get the terms we want
    events = ChartEventValue.objects.filter(icustay=icustay_id).values()
    events = read_frame(events)#.set_index('itemID').drop(['subject','admission','id'], axis=1)

    if events.empty:
        return events

    events['icustayID'] = icustay_id

    stay = ICUstay.objects.filter(icustayID=icustay_id)
    stay = read_frame(stay)

    events_ts = _events_to_ts(events, variable_col='itemID', value='value').reset_index()



    # intime = pd.Timestamp(stay['intime'].values[0])
    # events_ts = add_hours_elpased_to_events(events_ts, dt=intime)

    return events_ts


def get_stay_lab_timeseries(icustay_id):
    """
    For a given admission ID -> get the ts with all the labevents.
    then get in and out time from an icustay and cut the bits out that fall between
    """
    # get ICUstay:
    stay = ICUstay.objects.filter(icustayID=icustay_id)
    stay = read_frame(stay)
    stay['intime'] = pd.to_datetime(stay['intime'])
    stay['outtime'] = pd.to_datetime(stay['outtime'])

    admission_obj_str = stay['admission'].values[0] # this is a string: `Admission object (199395)`
    admission_id = re.search(re.compile('(\d+)'), admission_obj_str).group()

    stay_period = pd.Interval(stay['intime'].values[0],
                              stay['outtime'].values[0])

    # filter the lab_events:
    events = LabEventValue.objects.filter(admission_id=admission_id)
    events = read_frame(events)
    events['chart_time'] = pd.to_datetime(events['chart_time'])
    events.set_index('chart_time', inplace=True)
    idx = [t in stay_period for t in events.index.values]

    events = events.loc[idx].reset_index()
    events['icustayID'] = stay['icustayID'].unique()[0]

    # convert to ts:
    events_ts = _events_to_ts(events, variable_col='itemID', value='value').reset_index()

    if events_ts.empty:
        return events_ts

    intime = pd.Timestamp(stay['intime'].values[0])

    events_ts = add_hours_elpased_to_events(events_ts, dt=intime)

    return events_ts


def get_meta_info(icustay_id):
    """
    This function  is supposed to return an df containing meta info like:
    - ward, moves, outcomes, admission ID, patient ID, etc FOR A GIVEN ICUSTAY.
    - this is what will become the labels later!

    :param icustay_id:
    :return:
    """
    stay = ICUSTAY.objects.filter(icustayID=icustay_id)
    stay = read_frame(stay)
    stay['intime'] = pd.to_datetime(stay['intime'])
    stay['outtime'] = pd.to_datetime(stay['outtime'])

    # admission
    admission_obj_str = stay['admission'].values[0] # this is a string: `Admission object (199395)`
    admission_id = re.search(re.compile('(\d+)'), admission_obj_str).group()
    admission = Admission.objects.filter(admID=admission_id)
    admission = read_frame(admission)
    stay['admission'] = admission_id

    # patient
    subject_obj_str = stay['subject'].values[0] # this is a string: `Patient object (199395)`
    subject_id = re.search(re.compile('(\d+)'), subject_obj_str).group()
    patient = Patient.objects.filter(subjectID=subject_id)
    patient = read_frame(patient)
    stay['subject'] = subject_id

    # gather info:
    stay.drop(['first_ward_id', 'last_ward_id', 'first_cu', 'last_cu'], axis=1, inplace=True)

    for c in ['adm_time', 'disch_time', 'inpmor', 'pdismor', 'read']:
        stay[c] = admission[c]

    for c in ['gender', 'age', 'date_of_death_hosp']:
        stay[c] = patient[c]

    return stay


def get_all_stays_info():
    """
    1. query a list of _all_ icstay ids
    2. for every icustay, get the meta info as well as the ts data
    :return:
    """
    all_stays = ICUSTAY.objects.filter(DBSOURCE__exact='metavision')
    all_stays = read_frame(all_stays)

    #all_stays_ids = [re.search(re.compile('(\d+)'), obj_str).group() for obj_str in all_stays['icustayID']]
    all_stays_ids = all_stays['ICUSTAYID'].values
    del all_stays

    all_stays_chart = []
    all_stays_lab = []
    all_stays_meta = []

    for id in all_stays_ids:
        all_stays_meta.append(get_meta_info(id))
        all_stays_chart.append(get_stay_chart_timeseries(id))

        all_stays_lab.append(get_stay_lab_timeseries(id))

    all_stays_meta = pd.concat(all_stays_meta, axis=0, sort=True)
    print('meta: %s' % str(all_stays_meta.shape))
    all_stays_chart = pd.concat(all_stays_chart, axis=0, sort=True)
    print('chart: %s' % str(all_stays_chart.shape))
    all_stays_lab = pd.concat(all_stays_lab, axis=0, sort=True)
    print('lab: %s' % str(all_stays_lab.shape))

    return all_stays_meta, all_stays_chart, all_stays_lab


def get_single_stay(id):
    """
    Get and comnbine the information for a single stay.
    :param id:
    :return:
    """
    meta = get_meta_info(id)
    chart = get_stay_chart_timeseries(id)
    lab = get_stay_lab_timeseries(id)

    return meta, chart, lab


def filter_items(df):
    """
    Filter items of interest from the stays.csv files
    :param events_df:
    :param itemIDs:
    :return:
    """
    with open('simplimicapp/items.JSON') as infobj:
        items_dict = json.load(infobj)

    all_relevant = [_ for d in items_dict.values() for v in d.values() for _ in v]
    df.drop([c for c in df.columns if c not in all_relevant and str(c).isdigit()], axis=1, inplace=True)

    return df


def main():
    meta, chart, lab = get_all_stays_info()
    chart = filter_items(chart)
    lab = filter_items(lab)

    # dirty save for playing around:
    chart.to_csv('~/projects/thesis/data/sandbox/chart.csv')
    lab.to_csv('~/projects/thesis/data/sandbox/lab.csv')
    meta.to_csv('~/projects/thesis/data/sandbox/meta.csv')


if __name__ == '__main__':
    main()






