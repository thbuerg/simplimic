"""
Script that evaluates the events.csv and the admissions.csv files:

Basically performs the data cleaning steps proposed by:
https://github.com/YerevaNN/mimic3-benchmarks

"""
import os
import pandas as pd
import numpy as np
from shutil import copyfile


MIMIC_DIR = '/nfs/research1/birney/projects/ehr/mimic/mimic_raw'
OUT_DIR = '/nfs/research1/birney/projects/ehr/mimic/mimic_raw_clean'
# global MIMIC_DIR

def clean_admissions():
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
    if missing.index.values.size > 0:
        admissions = admissions.loc[~missing.index.values]
    print('Found %d Admissions with ID.' % len(admissions))

    admissions.drop_duplicates(inplace=True)
    print('Found %d Admissions with unique ID.' % len(admissions))
    admissions.reset_index(inplace=True)

    # correct the missing timestamps
    for c in [
        # 'ADMITTIME',
        # 'DISCHTIME',
        'DEATHTIME',
        'EDREGTIME',
        'EDOUTTIME',
    ]:
        admissions[c] = pd.to_datetime(admissions[c].fillna('1911-11-11 11:11:11'))

    print(admissions.isna().sum())

    admissions.to_csv(os.path.join(OUT_DIR, 'ADMISSIONS.csv'))

    return admissions


def clean_icu_stays():
    """
    Go over the ICUSTAYS.csv and discard stays without admission
    :return:
    """
    # read stays:
    icustays = pd.read_csv(os.path.join(MIMIC_DIR, 'ICUSTAYS.csv'))
    icustays.set_index('ICUSTAY_ID', inplace=True)

    stays = get_stays_csv()
    stays.set_index('ICUSTAY_ID', inplace=True)

    icustays = icustays.loc[stays.index]
    icustays.reset_index(inplace=True)

    for c in ['INTIME', 'OUTTIME']:
        icustays[c] = pd.to_datetime(icustays[c])
        
    # drop where in and outtimes are missing:
    icustays = icustays.loc[icustays['OUTTIME'].notnull()]
    icustays = icustays.loc[icustays['INTIME'].notnull()]
    icustays.to_csv(os.path.join(OUT_DIR, 'ICUSTAYS.csv'))

    return icustays


def clean_events(kind='CHART'):
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
        stays = pd.read_csv(os.path.join(OUT_DIR, 'stays.csv'))
    except OSError:
        stays = get_stays_csv()
    
    stays.reset_index(inplace=True)
    stays_by_icu = stays.set_index('ICUSTAY_ID')
    stays_by_hadm = stays.set_index('HADM_ID')

    stays.reset_index(inplace=True)

    # read the events:
    for events in pd.read_csv(os.path.join(MIMIC_DIR, '%sEVENTS.csv' % kind), chunksize=500000):

        droplist = []
        events_to_edit = events.copy()

        if kind == 'CHART':
            """
            1. group by icustay. 
                - ensure the stay-HADMID combo is legit (in stays)
                    - if not -> discard
            """
            for icustayID, events_per_icustay in events.groupby('ICUSTAY_ID'):
                # correct nan
                if np.isnan(icustayID):
                    print('Found %d NaN ICUSTAY_IDs. Correcting.' % events_per_icustay.shape[0])
                    for idx, r in events_per_icustay.iterrows():
                        # -> get the ID from the stays table by comparing the time.
                        icustays_p_hadmid = stays_by_hadm.loc[[hadmID]] # make sure to get a dataframe
                        corrected = False
                        for hadmID, stay_info in icustays_p_hadmid.iterrows():
                            timestamp = pd.to_datetime(r['CHARTTIME'])
                            if timestamp in pd.Interval(stay_info['INTIME'], stay_info['OUTTIME']):
                                # print('\n'*3)
                                # print(stay_info['ICUSTAY_ID'])
                                # print('\n'*3)
                                events_to_edit.loc[idx, 'ICUSTAY_ID'] = stay_info['ICUSTAY_ID']
                                corrected = True
                                print('Successfully inferred ICUSTAY_ID.')

                        if not corrected:
                            droplist.append(idx)
                            continue
                    continue

                if icustayID not in stays_by_icu.index:
                    droplist.extend(events_per_icustay.index.values)
                    continue

                # check if pair is legit:
                hadmIDs = events_per_icustay['HADM_ID'].unique()
                correct_hadmID = stays_by_icu.loc[icustayID, 'HADM_ID']

                if correct_hadmID not in hadmIDs:
                    # drop all:
                    droplist.extend(events_per_icustay.index.values)
                    continue

                else:
                    # discard all that have different HADM_IDs
                    for id, df in events_per_icustay.groupby('HADM_ID'):
                        if not id == correct_hadmID:
                            droplist.extend(df.index.values)

        else:
            for hadmID, events_per_hadm in events.groupby('HADM_ID'):

                # TODO: implement recovery of hadmID based on intime/outtime!
                # check if hadmID in stays. if not discard:
                if hadmID not in stays_by_hadm.index:
                    droplist.extend(events_per_hadm.index.values)
                else:
                    continue

        del events
        print('Dropping %s events due to invalid IDs' % len(droplist))
        events_to_edit.drop(droplist, inplace=True)
        events_to_edit['CHARTTIME'] = pd.to_datetime(events_to_edit['CHARTTIME'])  #.fillna('1911-11-11 11:11:11'))
        if kind == 'CHART':
            events_to_edit['STORETIME'] = pd.to_datetime(events_to_edit['STORETIME'].fillna('1911-11-11 11:11:11'))
        events_to_edit = events_to_edit.loc[events_to_edit['CHARTTIME'].notnull()]
        with open(os.path.join(OUT_DIR, '%sEVENTS.csv' % kind), 'a') as fobj:
            events_to_edit.to_csv(fobj, mode='a', header=fobj.tell() == 0)


def get_stays_csv():
    """
    Write a csv file mapping ICU-stays to admissions (id to id):
        - read the ICUSTAY file
    :return:
    """
    admissions = clean_admissions()

    icustays = pd.read_csv(os.path.join(MIMIC_DIR, 'ICUSTAYS.csv'))
    assert icustays.shape[0] == icustays['ICUSTAY_ID'].nunique()
    assert icustays['ICUSTAY_ID'].isna().sum() == 0
    
    icustays = icustays.loc[icustays['OUTTIME'].notnull()]
    icustays = icustays.loc[icustays['INTIME'].notnull()]

    stays = icustays.drop(['ROW_ID', 'DBSOURCE', 'FIRST_CAREUNIT',
                            'LAST_CAREUNIT', 'FIRST_WARDID',
                            'LAST_WARDID', 'LOS'], axis=1)

    valid_admission_ids = sorted(list(set(stays['HADM_ID'].values).intersection(admissions['HADM_ID'].values)))
    stays.set_index('HADM_ID', inplace=True)

    for c in ['INTIME', 'OUTTIME']:
        stays[c] = pd.to_datetime(stays[c])

    # drop the stays for which the HADM_ID is not in admissions:
    stays = stays.loc[valid_admission_ids]

    # save:
    stays.to_csv(os.path.join(OUT_DIR, 'stays.csv'))

    return stays

# TODO:
"""
- get fn to check that there is a one to many mapping between HADM and ICUSTAY not vice versa
- in case there is, get a fn to throw out the one with less information? (this would have to be based no the events files...)
"""


def copy_raw_files():
    """
    Copy the raw files from the MIMIC_DIR to OUT_DIR:
    - Patients.csv
    - Prescriptions.csv
    :return:
    """
    copyfile(os.path.join(MIMIC_DIR, 'PATIENTS.csv'),
             os.path.join(OUT_DIR, 'PATIENTS.csv'))
    copyfile(os.path.join(MIMIC_DIR, 'PRESCRIPTIONS.csv'),
             os.path.join(OUT_DIR, 'PRESCRIPTIONS.csv'))


def main():
    # create outdir if needed:
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)
    copy_raw_files()
    clean_admissions()
    clean_icu_stays()
    clean_events()
    clean_events(kind='LAB')


if __name__ == '__main__':
    main()
