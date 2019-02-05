"""
Script that evaluates the events.csv and the admissions.csv files:

Basically performs the data cleaning steps proposed by:
https://github.com/YerevaNN/mimic3-benchmarks

"""
import os
import pandas as pd
import numpy as np
from shutil import copyfile


MIMIC_DIR = '/Users/buergelt/projects/thesis/data/mimic_demo'
OUT_DIR = '/Users/buergelt/projects/thesis/data/mimic_demo_clean'
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
    if missing.index.values:
        admissions = admissions.loc[~missing.index.values]
    print('Found %d Admissions with ID.' % len(admissions))

    admissions.drop_duplicates(inplace=True)
    print('Found %d Admissions with unique ID.' % len(admissions))
    admissions.reset_index(inplace=True)
    print(admissions.head())

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
        raise OSError()
        stays = pd.read_csv(os.path.join(OUT_DIR, 'stays.csv'))
    except OSError:
        stays = get_stays_csv()

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
                            print('Successfully inferred ICUSTAY_ID.')

                    if not corrected:
                        droplist.append(idx)
                        continue
                else:
                    # check that the combo of ICUSTAY_ID and HADM_ID is in stays, if not try to correct:
                    icustays_p_hadmid = stays.loc[[hadmID]]
                    if r['ICUSTAY_ID'] in icustays_p_hadmid[['ICUSTAY_ID']].values:
                        continue
                   # else:
                   #     # we have to correct:
                   #     if not r['ICUSTAY_ID'] in stays['ICUSTAY_ID'].values:
                   #         # drop it:
                   #         droplist.append(idx)
                   #     else:
                   #         # get the HADMID and assign it:
                   #         stays_p_icuid = stays.reset_index().set_index('ICUSTAY_ID')
                   #         if stays_p_icuid.loc[[r['ICUSTAY_ID']]]['HADM_ID'].nunique() > 1:
                   #             droplist.append(idx)
                   #         else:
                   #             # we correct the HADM_ID:
                   #             hadmid_corrected = stays_p_icuid.loc[r['ICUSTAY_ID']]['HADM_ID']
                   #             print('Successfully corrected HADM_ID (%s -> %s) for ICUSTAY %s' %
                   #                   (r['HADM_ID'], hadmid_corrected, r['ICUSTAY_ID']))
                   #             events_to_edit.loc[idx, 'HADM_ID'] = hadmid_corrected
                   #
                   #             # TODO: OR: Correct the ICUSTAY?!
                   #             # correct the stay ID instead of the HADM_ID
                    else:
                        # discard!
                        droplist.append(idx)

    del events
    print('Dropping %s events due to invalid IDs' % len(droplist))
    events_to_edit.drop(droplist, inplace=True)
    events_to_edit.to_csv(os.path.join(OUT_DIR, '%sEVENTS.csv' % kind))
    events_to_edit


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
