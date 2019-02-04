"""
Script that evaluates the events.csv and the admissions.csv files:

Basically performs the data cleaning steps proposed by:
https://github.com/YerevaNN/mimic3-benchmarks

"""
import os
import pandas as pd
import numpy as np


MIMIC_DIR = '/Users/buergelt/projects/thesis/data/mimic_demo'
# global MIMIC_DIR

def _clean_admissions():
    """
    Go over the Admissions.csv -> select the entries w/o an hadmID
    :return:
    """
    # 1. read in ADMISSIONS.csv
    admissions = pd.read_csv(os.path.join(MIMIC_DIR, 'ADMISSIONS.csv'))

    admissions.set_index('HADM_ID', inplace=True)
    missing = admissions.index == np.nan
    missing = admissions[missing].copy()

    print('Found %d Admissions.' % len(admissions))
    if missing.index.values:
        admissions = admissions.loc[~missing.index.values]
    print('Found %d Admissions with ID.' % len(admissions))

    admissions.drop_duplicates(inplace=True)
    print('Found %d Admissions with unique ID.' % len(admissions))
    admissions.reset_index(inplace=True)

    admissions.to_csv(os.path.join(MIMIC_DIR, 'ADMISSIONS_CLEAN.csv'))

    return admissions


def _clean_icu_stays():
    """
    Go over the ICUSTAYS.csv and discard stays without admission
    :return:
    """
    # read stays:
    icustays = pd.read_csv(os.path.join(MIMIC_DIR, 'ICUSTAYS.csv'))
    icustays.set_index('ICUSTAY_ID', inplace=True)

    stays = _get_stays_csv()
    stays.set_index('ICUSTAY_ID', inplace=True)

    icustays = icustays.loc[stays.index]
    icustays.reset_index(inplace=True)

    return icustays


def _clean_events(kind='CHART'):
    """
    Go over an xxxEVENTS.csv  and lookup the ICUSTAY/ADMISSION ID combo in the stays mapping.

    If  the combination is illegitimate -> try to correct it:
        - if hadmID is missing: add it from stays
        - if ICUSTAY id is missiong  and NOT found in combination w/ another HADMID -> add it from stays
        - if both are missing or the conditions are unfulfilled -> discard the entry
    :return:
    """
    assert kind in ['LAB', 'CHART']

    try:
        raise OSError()
        stays = pd.read_csv(os.path.join(MIMIC_DIR, 'stays.csv'))
    except OSError:
        stays = _get_stays_csv()

    # read the events:
    events = pd.read_csv(os.path.join(MIMIC_DIR, '%sEVENTS.csv' % kind))
    print(events.head())

    # stays.set_index('HADM_ID', inplace=True)

    droplist = []
    events_to_edit = events.copy()

    for hadmID, events_per_hadm in events.groupby('HADM_ID'):

        # iterate over the thing an correct each row
        # print(events_per_hadm.head())
        # print(stays.head())

        for idx, r in events_per_hadm.iterrows():
            # first check if HADM_ID is valid:

            # TODO: see if we want to reconstruct the HADM_ID from stays as well
            if not r['HADM_ID'] in stays.index.values:
                droplist.append(idx)
                continue

            elif 'ICUSTAY_ID' in r.index:
                # check if we have the stay
                if np.isnan(r['ICUSTAY_ID']):
                    # -> get the ID from the stays table by comparing the time.
                    icustays_p_hadmid = stays.loc[[hadmID]] # make sure to get a dataframe
                    corrected = False
                    for hadmID, stay_info in icustays_p_hadmid.iterrows():
                        timestamp = pd.to_datetime(r['CHARTTIME'])
                        if timestamp in pd.Interval(stay_info['INTIME'], stay_info['OUTTIME']):
                            events_to_edit.loc[idx]['ICUSTAY_ID'] = stay_info['ICUSTAY_ID']
                            corrected = True
                            print('Successfully corrected value.')

                    if not corrected:
                        droplist.append(idx)
                        continue

    del events
    print('Dropping %s events due to invalid IDs' % len(droplist))
    events_to_edit.drop(droplist, inplace=True)
    events_to_edit.to_csv(os.path.join(MIMIC_DIR, '%sEVENTS_clean.csv' % kind))


def _get_stays_csv():
    """
    Write a csv file mapping ICU-stays to admissions (id to id):
        - read the ICUSTAY file
    :return:
    """
    admissions = _clean_admissions()

    icustays = pd.read_csv(os.path.join(MIMIC_DIR, 'ICUSTAYS.csv'))
    assert icustays.shape[0] == icustays['ICUSTAY_ID'].nunique()
    assert icustays['ICUSTAY_ID'].isna().sum() == 0

    stays = icustays.drop(['ROW_ID', 'DBSOURCE', 'FIRST_CAREUNIT',
                            'LAST_CAREUNIT', 'FIRST_WARDID',
                            'LAST_WARDID', 'LOS'], axis=1)

    # drop the stays for which the HADM_ID is not in admissions:
    valid_admission_ids = sorted(list(set(stays['HADM_ID'].values).intersection(admissions['HADM_ID'].values)))

    stays.set_index('HADM_ID', inplace=True)

    for c in ['INTIME', 'OUTTIME']:
        stays[c] = pd.to_datetime(stays[c])

    stays = stays.loc[valid_admission_ids]
    stays.to_csv(os.path.join(MIMIC_DIR, 'stays.csv'))

    return stays


def main():
    _clean_events()
    _clean_events(kind='LAB')


if __name__ == '__main__':
    main()
