import os, sys
os.environ["DJANGO_SETTINGS_MODULE"] = "simplimic.settings"
import django
django.setup()
import pandas as pd
import numpy as np
from simplimicapp.models import *

# some dirty FLAGS:
#DATADIR = '/Users/buergelt/projects/thesis/data/mimic_proc_all'
DATADIR= sys.argv[1]


def djangify_dataframe(df, model):
    """
    iterates over the rows of a pandas df and creates a django model for each row!
    :param df:
    :param model:
    :return:
    """
    # TODO delete template when all djangifications are implemented
    collection = []
    for i, row in df.iterrows():
        m = None
        collection.append(m)

def generate_patients():
    """
    Populate the database with patients from PATIENTS.csv  (MIMIC_raw)
    :return:
    """
    print('Generating Patients...')
    # read in the cleaned admission file and create patients:
    subjects_df = pd.read_csv(os.path.join(DATADIR, 'PATIENTS.csv'))
    subjects_df.set_index('SUBJECT_ID', inplace=True)

    # TODO: this probably better done in the prepopprocessing
    subjects_df = subjects_df.loc[~subjects_df.index.duplicated(keep='first')]

    # generate an django entry for each row:
    models = []
    for i, r in subjects_df.iterrows():
        m = SUBJECT(
            SUBJECT_ID=i,
            GENDER=r['GENDER'],
            DOB=r['DOB'],
            DOD=r['DOD'],
            DOD_HOSP=r['DOD_HOSP'],
            DOD_SSN=r['DOD_SSN'],
            EXPIRE_FLAG=r['EXPIRE_FLAG'],
        )
        models.append(m)
    SUBJECT.objects.bulk_create(models)

    print('DONE')


def generate_admissions():
    """
    Populate the database with admission from the MIMIC-raw ADMISSIONS.csv
    "ROW_ID","SUBJECT_ID","HADM_ID","ADMITTIME","DISCHTIME","DEATHTIME","ADMISSION_TYPE","ADMISSION_LOCATION", \
    "DISCHARGE_LOCATION","INSURANCE","LANGUAGE","RELIGION","MARITAL_STATUS","ETHNICITY","EDREGTIME","EDOUTTIME", \
    "DIAGNOSIS","HOSPITAL_EXPIRE_FLAG","HAS_CHARTEVENTS_DATA"
    :return:
    """
    print('Generating Admissions...')

    adm_df = pd.read_csv(os.path.join(DATADIR, 'ADMISSIONS.csv'))
    adm_df.set_index('SUBJECT_ID', inplace=True)


    # generate an django entry for each row:
    models = []
    for i, r in adm_df.iterrows():    
        p = SUBJECT.objects.get_or_create(SUBJECT_ID=i)[0]
        m = ADMISSION(
            SUBJECT=p,
            HADM_ID=r['HADM_ID'],
            ADMITTIME=r['ADMITTIME'],
            DISCHTIME=r['DISCHTIME'],
            DEATHTIME=r['DEATHTIME'],
            ADMISSION_TYPE=r['ADMISSION_TYPE'],
            ADMISSION_LOCATION=r['ADMISSION_LOCATION'],
            DISCHARGE_LOCATION=r['DISCHARGE_LOCATION'],
            INSURANCE=r['INSURANCE'],
            LANGUAGE=r['LANGUAGE'],
            RELIGION=r['RELIGION'],
            MARITAL_STATUS=r['MARITAL_STATUS'],
            ETHNICITY=r['ETHNICITY'],
            EDREGTIME=r['EDREGTIME'],
            EDOUTTIME=r['EDOUTTIME'],
            DIAGNOSIS=r['DIAGNOSIS'],
            HOSPITAL_EXPIRE_FLAG=r['HOSPITAL_EXPIRE_FLAG'],
            HAS_CHARTEVENTS_DATA=r['HAS_CHARTEVENTS_DATA']
        )
        models.append(m)
        
    ADMISSION.objects.bulk_create(models)

    print('DONE')


def generate_icustays():
    """
    Populate the database with icu stays from the MIMIC-raw ICUSTAYS.csv
   "ROW_ID","SUBJECT_ID","HADM_ID","ICUSTAY_ID","DBSOURCE","FIRST_CAREUNIT","LAST_CAREUNIT","FIRST_WARDID", \\
   "LAST_WARDID","INTIME","OUTTIME","LOS"

    :return:
    """
    print('Generating ICUstays...')
    #stays_df = pd.read_csv(os.path.join(DATADIR, 'ICUSTAYS.csv'))
    #stays_df.set_index('ICUSTAY_ID', inplace=True)
    
    for records in pd.read_csv(os.path.join(DATADIR, 'ICUSTAYS.csv'), chunksize=100000):

        stays_df = records.set_index('ICUSTAY_ID')
        # generate an django entry for each row:
        for admID, stays_per_adm_df in stays_df.groupby(stays_df['HADM_ID']):
            pids = stays_per_adm_df['SUBJECT_ID'].unique()
            assert pids.shape[0] == 1, 'ERROR: Same Admission ID assigned to multiple Patients.'

            p = SUBJECT.objects.get_or_create(SUBJECT_ID=pids[0])[0]
            a = ADMISSION.objects.get_or_create(HADM_ID=admID)[0]

            models = []

            for i, r in stays_per_adm_df.iterrows():
                m = ICUSTAY(
                    SUBJECT=p,
                    ADMISSION=a,
                    ICUSTAY_ID=float(i),  # float('10.0') -> int() works
                    DBSOURCE=r['DBSOURCE'],
                    FIRST_CAREUNIT= r['FIRST_CAREUNIT'],
                    LAST_CAREUNIT=r['LAST_CAREUNIT'],
                    FIRST_WARDID=r['FIRST_WARDID'],
                    LAST_WARDID=r['LAST_WARDID'],
                    INTIME=r['INTIME'],
                    OUTTIME=r['OUTTIME'],
                    LOS=r['LOS']
                )
                models.append(m)

            ICUSTAY.objects.bulk_create(models)

    print('DONE')


def generate_chartitems():
    """
    Generate the objects for the chartitems:
    :return:
    """
    print('Generating chartitems...')

    chartitems_df = pd.read_csv(os.path.join(DATADIR, 'D_ITEMS.csv'))

    chartitems_df.set_index('ITEMID', inplace=True)

    models = []
    for itemid, r in chartitems_df.iterrows():
        m = CHARTITEM(
            ITEMID=itemid,
            LABEL=r['LABEL'],
            ABBREVIATION=r['ABBREVIATION'],
            DBSOURCE=r['DBSOURCE'],
            LINKSTO=r['LINKSTO'],
            CATEGORY=r['CATEGORY'],
            UNITNAME=r['UNITNAME'],
            PARAM_TYPE=r['PARAM_TYPE'],
            CONCEPTID=r['CONCEPTID']
        )
        models.append(m)

    CHARTITEM.objects.bulk_create(models)

    print('DONE')


def generate_labitems():
    """
    Generate the objects for the chartitems:
    :return:
    """
    print('Generating labitems...')

    labitems_df = pd.read_csv(os.path.join(DATADIR, 'D_LABITEMS.csv'))
    labitems_df.set_index('ITEMID', inplace=True)

    models = []
    for itemid, r in labitems_df.iterrows():
        m = LABITEM(
            ITEMID=itemid,
            LABEL=r['LABEL'],
            FLUID=r['FLUID'],
            CATEGORY=r['CATEGORY'],
            LOINC_CODE=r['LOINC_CODE']
        )
        models.append(m)

    LABITEM.objects.bulk_create(models)

    print('DONE')


def generate_chartevents():
    """
    Generates the chartevents table. As the table comes in  stacked long-format, it first has to be formated by:
        - hadmID
        - then itemID
        - then models are generated per descriptor
    :return:
    """
    # read in the charts files:

    print('Generating chartevents...')

    fname = 'CHARTEVENTS.csv'

    for records in pd.read_csv(os.path.join(DATADIR, fname), chunksize=1000000):

        print('Found %d records to generate from file: %s' % (records.shape[0], fname))
        models = []

        for icustay_id, events_per_icustay in records.groupby('ICUSTAY_ID'):
            models = []
            # enforce many to one:
            pids = events_per_icustay['SUBJECT_ID'].unique()
            assert pids.shape[0] == 1, 'ERROR: Same ICUSTAY ID assigned to multiple Patients.'
            adms = events_per_icustay['HADM_ID'].unique()
            assert adms.shape[0] == 1, 'ERROR: Same ICUSTAY ID assigned to multiple Admissions: HADMID: %s, ICUSTAYID: %s' % (adms[0], icustay_id)

            a = ADMISSION.objects.get(HADM_ID=adms[0])
            p = SUBJECT.objects.get(SUBJECT_ID=pids[0])
            i = ICUSTAY.objects.get(ICUSTAY_ID=float(icustay_id))

            # loop over all descriptors and instatiate them all:
            events_per_icustay.set_index('ITEMID', inplace=True)

            for item, item_df in events_per_icustay.groupby(events_per_icustay.index):
                itm = CHARTITEM.objects.get(ITEMID=item)
                for _, r in item_df.iterrows():
                    m = CHARTEVENTVALUE(
                        SUBJECT=p,
                        ADMISSION=a,
                        ICUSTAY=i,
                        ITEM=itm,
                        CHARTTIME=r['CHARTTIME'],
                        STORETIME=r['STORETIME'],
                        CGID=r['CGID'],
                        VALUE=r['VALUE'],
                        VALUENUM=r['VALUENUM'],
                        VALUEUOM=r['VALUEUOM'],
                        WARNING=r['WARNING'],
                        ERROR=r['ERROR'],
                        RESULTSTATUS=r['RESULTSTATUS'],
                        STOPPED=r['STOPPED'],
                    )
                    models.append(m)                    
                   
        try:
            CHARTEVENTVALUE.objects.bulk_create(models)
        except TypeError:
            events_per_icustay.to_csv(os.path.join(DATADIR, 'CHARTEVENTS_CRASH.csv'))
            raise TypeError()

    print('DONE')

    
def generate_labevents():
    """
    Generates the labevents table. As the table comes in  stacked long-format, it first has to be formated by:
        - hadmID
        - then itemID
        - then models are generated per descriptor
        ,ROW_ID,SUBJECT_ID,HADM_ID,ITEMID,CHARTTIME,VALUE,VALUENUM,VALUEUOM,FLAG
    :return:
    """
    # read in the charts files:

    print('Generating labevents...')

    fname = 'LABEVENTS.csv'
<<<<<<< HEAD
    for records in pd.read_csv(os.path.join(DATADIR, fname), chunksize=100000, index_col=False):
        if 'Unnamed: 0' in records.columns:
            records.drop('Unnamed: 0', axis=1, inplace=True)
=======
    for records in pd.read_csv(os.path.join(DATADIR, fname), chunksize=100000):
        records = records.drop('Unnamed: 0', axis=1)
        records = records.dropna(subset=['HADM_ID', 'ITEMID'], axis=0)
        print(records.shape)
        print(records.head())
>>>>>>> 70442c4b2eacb5df917d59fff6ce0ace11111d23

        print('Found %d records to generate from file: %s' % (records.shape[0], fname))

        for adm_id, events_per_hadm in records.groupby('HADM_ID'):
            # enforce many to one:
            pids = events_per_hadm['SUBJECT_ID'].unique()
            assert pids.shape[0] == 1, 'ERROR: Same ICUSTAY ID assigned to multiple Patients.'
            
            try:
                a = ADMISSION.objects.get_or_create(HADM_ID=adm_id)[0]
                p = SUBJECT.objects.get_or_create(SUBJECT_ID=pids[0])[0]
            except:
                print(adm_id)
                print(pids)
                raise NotImplementedError()

            # loop over all descriptors and instatiate them all:
            events_per_hadm.set_index('ITEMID', inplace=True)

            models = []

            print(events_per_hadm.head())
            for item, item_df in events_per_hadm.groupby(events_per_hadm.index):
                itm = LABITEM.objects.get(ITEMID=item)
                for _, r in item_df.iterrows():
                    m = LABEVENTVALUE(
                        SUBJECT=p,
                        ADMISSION=a,
                        ITEM=itm,
                        CHARTTIME=r['CHARTTIME'],
                        VALUE=r['VALUE'],
                        VALUENUM=float(r['VALUENUM']),
                        VALUEUOM=r['VALUEUOM'],
                        FLAG=r['FLAG']
                    )
                    try:
                        m.save()
                    except:
                        print(a.__dict__)
                        print(p.__dict__)
                        print(itm.__dict__)
                        print(m.__dict__)
                        print(LABEVENTVALUE.objects.all())
                        raise NotImplementedError()
            raise NotImplementedError()
                    #models.append(m)
            #LABEVENTVALUE.objects.bulk_create(models)

        print('DONE')


def generate_diagnosis():
    """
    GEnerate the diagnosis...
    :return:
    """
    print('Generating diagnoses...')
    # records = pd.read_csv(os.path.join(DATADIR, 'DIAGNOSES.csv'))
    for records in pd.read_csv(os.path.join(DATADIR, 'DIAGNOSES_ICD.csv'), chunksize=100000):
        for hadmid, records_per_hadm in records.groupby('HADM_ID'):
            a = ADMISSION.objects.get_or_create(HADM_ID=hadmid)[0]
            p = SUBJECT.objects.get_or_create(SUBJECT_ID=records_per_hadm['SUBJECT_ID'].unique()[0])[0]

            models = []
            for _, r in records_per_hadm.iterrows():
                m = DIAGNOSIS(
                    SUBJECT=p,
                    ADMISSION=a,
                    SEQ_NUM=r['SEQ_NUM'],
                    ICD9_CODE=r['ICD9_CODE'],
                    ICD_CLASS=r['ICD_CLASS']
                )
                models.append(m)

            DIAGNOSIS.objects.bulk_create(models)

    print('DONE')


def generate_presriptions():
    """
    GEnerate the entries for the prescriptions.
    :return:
    """
    print('Generating prescriptions...')

    records = pd.read_csv(os.path.join(DATADIR, 'PRESCRIPTIONS.csv'))
    print(records.shape)
    records['GSN'] = records['GSN'].apply(dirty_to_nan)
    records['NDC'] = records['NDC'].apply(dirty_to_nan)
    records = records.dropna(subset=['GSN', 'NDC'], axis=0)
    print(records.shape)

    print('Found %d records to generate from file: %s' % (records.shape[0], os.path.join(DATADIR,  'PRESCRIPTIONS.csv')))

    for icustay_id, drugs_per_icustay in records.groupby('ICUSTAY_ID'):
        pids = drugs_per_icustay['SUBJECT_ID'].unique()
        assert pids.size == 1, 'ERROR: Same Admission ID assigned to multiple Patients.'
        adms = drugs_per_icustay['HADM_ID'].unique()
        #print(adms)
        #assert adms.shape[0] == 1, 'ERROR: Same ICUSTAY ID assigned to multiple Admissions. {}'.format(adms)
        if adms.shape[0] > 1:
            continue

        a = ADMISSION.objects.get_or_create(HADM_ID=adms[0])[0]
        p = SUBJECT.objects.get_or_create(SUBJECT_ID=pids[0])[0]
        i = ICUSTAY.objects.get_or_create(ICUSTAY_ID=icustay_id)[0]
        
        models = []
        for idx, r in drugs_per_icustay.iterrows():
            m = PRESCRIPTION(
                SUBJECT=p,
                ADMISSION=a,
                ICUSTAY=i,
                STARTDATE=r['STARTDATE'],
                ENDDATE=r['ENDDATE'],
                DRUG_TYPE=r['DRUG_TYPE'],     # TODO -> go through dict here?
                DRUG=r['DRUG'],
                DRUG_NAME_POE=r['DRUG_NAME_POE'],
                DRUG_NAME_GENERIC=r['DRUG_NAME_GENERIC'],
                FORMULARY_DRUG_CD=r['FORMULARY_DRUG_CD'],
                GSN=r['GSN'],
                NDC=r['NDC'],
                PROD_STRENGTH=r['PROD_STRENGTH'],
                DOSE_VAL_RX=r['DOSE_VAL_RX'],
                DOSE_UNIT_RX=r['DOSE_UNIT_RX'],
                FORM_VAL_DISP=r['FORM_VAL_DISP'],
                FORM_UNIT_DISP=r['FORM_UNIT_DISP'],
                ROUTE=r['ROUTE']
            )
            # m.save()
            models.append(m)
        PRESCRIPTION.objects.bulk_create(models)

    print('DONE')


def main():
    # setup
    django.setup()

    # go
    print('Starting population...')

    #generate_patients()
    #generate_admissions()
    #generate_icustays()

    #generate_presriptions()
    #generate_chartitems()
    #generate_labitems()
    #generate_diagnosis()
    generate_labevents()
    #generate_chartevents()

    print('DONE')
    
    
def dirty_to_nan(v):
    if isinstance(v, float):
        return v
    if ' ' in v:
        return np.nan
    try:
        return float(v)
    except:
        return np.nan


if __name__ == '__main__':
    main()
