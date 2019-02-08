import os, sys
os.environ["DJANGO_SETTINGS_MODULE"] = "simplimic.settings"
import django
django.setup()
import pandas as pd
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
    patients_df = pd.read_csv(os.path.join(DATADIR, 'PATIENTS.csv'))
    patients_df.set_index('SUBJECT_ID', inplace=True)

    # TODO: this probably better done in the prepopprocessing
    patients_df = patients_df.loc[~patients_df.index.duplicated(keep='first')]

    # generate an django entry for each row:
    models = []
    for i, r in patients_df.iterrows():
        m = Patient(
            subjectID=i,
            gender=r['GENDER'],
            #age=r['AGE'],
            date_of_birth=r['DOB'],
            date_of_death=r['DOD'],
            date_of_death_hosp=r['DOD_HOSP'],
            date_of_death_ssn=r['DOD_SSN'],
            expire_flag=r['EXPIRE_FLAG'],
        )
        models.append(m)
    Patient.objects.bulk_create(models)

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
        p = Patient.objects.get_or_create(subjectID=i)[0]
        m = Admission(
            subject = p,
            admID=r['HADM_ID'],
            adm_time=r['ADMITTIME'],
            disch_time=r['DISCHTIME'],
            death_time=r['DEATHTIME'],
            adm_type=r['ADMISSION_TYPE'],
            adm_location=r['ADMISSION_LOCATION'],
            disch_location=r['DISCHARGE_LOCATION'],
            insurance=r['INSURANCE'],
            language=r['LANGUAGE'],
            religion=r['RELIGION'],
            marital_status=r['MARITAL_STATUS'],
            ethnicity = r['ETHNICITY'],
            edregtime = r['EDREGTIME'],
            edouttime = r['EDOUTTIME'],
            init_diagnosis = r['DIAGNOSIS'],
            hosp_exp_flag = r['HOSPITAL_EXPIRE_FLAG'],
            has_chartevents =r['HAS_CHARTEVENTS_DATA']
        )
        models.append(m)
        
    Admission.objects.bulk_create(models)

    print('DONE')


def generate_icustays():
    """
    Populate the database with icu stays from the MIMIC-raw ICUSTAYS.csv
   "ROW_ID","SUBJECT_ID","HADM_ID","ICUSTAY_ID","DBSOURCE","FIRST_CAREUNIT","LAST_CAREUNIT","FIRST_WARDID", \\
   "LAST_WARDID","INTIME","OUTTIME","LOS"

    :return:
    """
    print('Generating ICUstays...')
    stays_df = pd.read_csv(os.path.join(DATADIR, 'ICUSTAYS.csv'))
    stays_df.set_index('ICUSTAY_ID', inplace=True)

    # generate an django entry for each row:
    for admID, stays_per_adm_df in stays_df.groupby(stays_df['HADM_ID']):
        pids = stays_per_adm_df['SUBJECT_ID'].unique()
        assert pids.shape[0] == 1, 'ERROR: Same Admission ID assigned to multiple Patients.'

        p = Patient.objects.get_or_create(subjectID=pids[0])[0]
        a = Admission.objects.get_or_create(admID=admID)[0]

        models = []

        for i, r in stays_df.iterrows():
            m = ICUstay(
                subject = p,
                admission=a,
                icustayID=i,
                db_source=r['DBSOURCE'],
                first_cu= r['FIRST_CAREUNIT'],
                last_cu=r['LAST_CAREUNIT'],
                first_ward_id=r['FIRST_WARDID'],
                last_ward_id=r['LAST_WARDID'],
                intime=r['INTIME'],
                outtime=r['OUTTIME'],
                los=r['LOS']
            )
            models.append(m)

    ICUstay.objects.bulk_create(models)   # TODO maybe better within the outer for loop?

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
    for records in pd.read_csv(os.path.join(DATADIR, fname), chunksize=100000):

        print('Found %d records to generate from file: %s' % (records.shape[0], fname))

        for icustay_id, events_per_icustay in records.groupby('ICUSTAY_ID'):
            # enforce many to one:
            pids = events_per_icustay['SUBJECT_ID'].unique()
            assert pids.shape[0] == 1, 'ERROR: Same ICUSTAY ID assigned to multiple Patients.'
            adms = events_per_icustay['HADM_ID'].unique()
            assert adms.shape[0] == 1, 'ERROR: Same ICUSTAY ID assigned to multiple Admissions: HADMID: %s, ICUSTAYID: %s' % (adms[0], icustay_id)

            a = Admission.objects.get_or_create(admID=adms[0])[0]
            p = Patient.objects.get_or_create(subjectID=pids[0])[0]
            i = ICUstay.objects.get_or_create(icustayID=icustay_id)[0]

            # loop over all descriptors and instatiate them all:
            events_per_icustay.set_index('ITEMID', inplace=True)

            models = []

            for item, r in events_per_icustay.iterrows():
                # if sum(r.isna()) > 0:
                #     r.where((pd.notnull(r)), None)
                    # r.fillna(value=None, inplace=True)

                m = ChartEventValue(
                    subject=p,
                    admission=a,
                    icustay=i,
                    itemID = item,
                    chart_time=r['CHARTTIME'],
                    store_time=r['STORETIME'],
                    cgID =r['CGID'],
                    value=r['VALUE'],
                    valuenum=r['VALUENUM'],
                    unit=r['VALUEUOM'],
                    warning=r['WARNING'],
                    error=r['ERROR'],
                    resultstatus=r['RESULTSTATUS'],
                    stopped=r['STOPPED'],
                    # warning=None if np.isnan(r['WARNING']) else r['WARNING'],
                    # error=None if np.isnan(r['ERROR']) else r['ERROR'],
                    # resultstatus=None if np.isnan(r['RESULTSTATUS']) else r['RESULTSTATUS'],
                    # stopped=None if np.isnan(r['STOPPED']) else r['STOPPED'],
                )
                models.append(m)
            ChartEventValue.objects.bulk_create(models)

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
    for records in pd.read_csv(os.path.join(DATADIR, fname), chunksize=100000):

        print('Found %d records to generate from file: %s' % (records.shape[0], fname))

        for adm_id, events_per_hadm in records.groupby('HADM_ID'):
            # enforce many to one:
            pids = events_per_hadm['SUBJECT_ID'].unique()
            assert pids.shape[0] == 1, 'ERROR: Same ICUSTAY ID assigned to multiple Patients.'

            a = Admission.objects.get_or_create(admID=adm_id)[0]
            p = Patient.objects.get_or_create(subjectID=pids[0])[0]

            # loop over all descriptors and instatiate them all:
            events_per_hadm.set_index('ITEMID', inplace=True)

            models = []

            for item, r in events_per_hadm.iterrows():

                m = LabEventValue(
                    subject=p,
                    admission=a,
                    itemID = item,
                    chart_time=r['CHARTTIME'],
                    # store_time=r['STORETIME'],
                    # cgID =r['CGID'],
                    value=r['VALUE'],
                    valuenum=r['VALUENUM'],
                    unit=r['VALUEUOM'],
                    flag=r['FLAG']
                )
                models.append(m)
            LabEventValue.objects.bulk_create(models)

        print('DONE')


def generate_presriptions():
    """
    GEnerate the entries for the prescriptions.
    :return:
    """
    print('Generating prescriptions...')

    records = pd.read_csv(os.path.join(DATADIR, 'PRESCRIPTIONS.csv'))

    print('Found %d records to generate from file: %s' % (records.shape[0], os.path.join(DATADIR,  'PRESCRIPTIONS.csv')))

    for icustay_id, drugs_per_icustay in records.groupby('ICUSTAY_ID'):
        pids = drugs_per_icustay['SUBJECT_ID'].unique()
        assert pids.size == 1, 'ERROR: Same Admission ID assigned to multiple Patients.'
        adms = drugs_per_icustay['HADM_ID'].unique()
        assert adms.shape[0] == 1, 'ERROR: Same ICUSTAY ID assigned to multiple Admissions.'

        a = Admission.objects.get_or_create(admID=adms[0])[0]
        p = Patient.objects.get_or_create(subjectID=pids[0])[0]
        i = ICUstay.objects.get_or_create(icustayID=icustay_id)[0]

        models = []
        for idx, r in drugs_per_icustay.iterrows():
            m = Prescription(
                subject=p,
                admission=a,
                icustay=i,
                start_date=r['STARTDATE'],
                end_date=r['ENDDATE'],
                drug_type=r['DRUG_TYPE'],     # TODO -> go through dict here?
                drug=r['DRUG'],
                drug_name_poe=r['DRUG_NAME_POE'],
                drug_name_generic=r['DRUG_NAME_GENERIC'],
                formulary_drug_cd=r['FORMULARY_DRUG_CD'],
                gsn=r['GSN'],
                ndc=r['NDC'],
                prod_strength=r['PROD_STRENGTH'],
                dose_val_rx=r['DOSE_VAL_RX'],
                dose_unit_rx=r['DOSE_UNIT_RX'],
                form_val_disp=r['FORM_VAL_DISP'],
                form_unit_disp=r['FORM_UNIT_DISP'],
                route=r['ROUTE']
            )
            # m.save()
            models.append(m)
        Prescription.objects.bulk_create(models)

    print('DONE')


def main():
    # setup
    django.setup()

    # go
    print('Starting population...')

    generate_patients()
    generate_admissions()
    generate_icustays()
    generate_chartevents()
    generate_labevents()
    generate_presriptions()

    # TODO:
    # generate diagnosis
    # generate services

    print('DONE')


if __name__ == '__main__':
    main()
