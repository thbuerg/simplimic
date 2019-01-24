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


def generate_patients_and_admissions():
    # read in the cleaned admission file and create patients:
    adm_filt_df = pd.read_csv(os.path.join(DATADIR, 'admission_events_all.csv'))
    adm_filt_df.set_index('SUBJECT_ID', inplace=True)

    # patients:
    print('Patients...')
    patients = adm_filt_df.copy()
    patients.drop(['HADM_ID',
                   'ADMITTIME',
                   'DISCHTIME',
                   'ADMISSION_TYPE',
                   'INPMOR',
                   'PDISMOR',
                   'READ',
                   'LOS',
                   'PLOS',], axis=1, inplace=True)
    patients = patients.loc[~patients.index.duplicated(keep='first')]

    # generate an django entry for each row:
    models = []
    for i, r in patients.iterrows():
        m = Patient(
            subjectID = i,
            gender = r['GENDER'],
            age = r['AGE'],
            date_of_birth = r['DOB']
        )
        # patient_models.append(m)
        # m.save()
        models.append(m)
    Patient.objects.bulk_create(models)

    # free up mem:
    del patients
    print('DONE')

    print('Admissions...')
    # Admission periods:
    models = []
    for i, r in adm_filt_df.iterrows():
        # get the Patient first
        p = Patient.objects.get_or_create(subjectID=i)[0]
        m = Admission(
            subject=p,
            admID=r['HADM_ID'],
            adm_time=r['ADMITTIME'],
            disch_time=r['DISCHTIME'],
            adm_type=r['ADMISSION_TYPE'],  # TODO: convert to the choice we set first?!
            inpmor=r['INPMOR'],
            pdismor=r['PDISMOR'],
            read=r['READ'],
            los=r['LOS'],
            plos=r['PLOS']
        )
        # m.save()
        models.append(m)
    Admission.objects.bulk_create(models)
    print('DONE')

def generate_descriptors(kind='charts'):
    """
    Generates the chartevents table. As the table comes in  stacked long-format, it first has to be formated by:
        - hadmID
        - then itemID
        - then models are generated per descriptor
    :return:
    """
    # read in the charts files:
    assert kind in ['charts', 'lab'], 'kind   must be one of: `charts`, `lab`'
    fname = 'chart_filt_all.csv' if kind == 'charts' else 'lab_filt_all.csv'

    records = pd.read_csv(os.path.join(DATADIR, fname))
    print('Found %d records to generate from file: %s' % (records.shape[0], fname))

    for admid, events_per_adm in records.groupby('HADM_ID'):
        pids = events_per_adm['SUBJECT_ID'].unique()
        assert pids.size == 1, 'ERROR: Same Admission ID assigned to multiple Patients.'

        a = Admission.objects.get_or_create(admID=admid)[0]
        p = Patient.objects.get_or_create(subjectID=pids[0])[0]

        # loop over all descriptors and instatiate them all:
        events_per_adm.set_index('ITEMID', inplace=True)

        # for item in events_per_adm.index.unique():
        #     item_df = events_per_adm.loc[item]  # TODO: this .loc might be removed? -> Check! (or keep it if iterrows() is faster then)
        #     for i, r in item_df.iterrows():
        models = []
        for item, r in events_per_adm.iterrows():
            m = DescriptorValue(
                subject=p,
                admission=a,
                itemID=item,
                chart_time=r['CHARTTIME'],
                value=r['VALUE'],
                unit=r['VALUEUOM'],
                kind='L' if kind == 'lab' else 'C',          # TODO: this LOOKS SLOOOOOOWWWW -> get rid of cond?
                flag=r['FLAG'] if kind == 'lab' else None,   # TODO:    ^
            )
            # m.save()
            models.append(m)
        DescriptorValue.objects.bulk_create(models)

    print('DONE')

def generate_presriptions():
    """
    GEnerate the entries for the prescriptions.
    :return:
    """
    records = pd.read_csv(os.path.join(DATADIR, 'presc_filt_all.csv'))

    print('Found %d records to generate from file: %s' % (records.shape[0], os.path.join(DATADIR,  'presc_filt_all.csv')))

    for admid, events_per_adm in records.groupby('HADM_ID'):
        pids = events_per_adm['SUBJECT_ID'].unique()
        assert pids.size == 1, 'ERROR: Same Admission ID assigned to multiple Patients.'

        a = Admission.objects.get_or_create(admID=admid)[0]
        p = Patient.objects.get_or_create(subjectID=pids[0])[0]

        models = []
        for i, r in drugs_per_adm.iterrows():
            m = Prescription(
                subject=p,
                admission=a,
                start_date=r['STARTDATE'],
                end_date=r['ENDDATE'],
                drug_type=r['DRUGTYPE'],     # TODO -> go through dict here?
                drug=r['DRUG'],
                drug_name_poe=r['DRUG_NAME_POE'],
                drug_name_generic=r['DRUG_NAME_GENERIC'],
                formulary_drug_cd=r['FORMULARY_DRUG_CD'],
                gsn=r['GSN'],
                ndc=r['NDC'],
                prod_strength=r['PROD_STRENGHT'],
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
    print('Generating Patients and Admissions:')
    generate_patients_and_admissions()
    print('Generating descriptors:')
    generate_descriptors()
    print('Generating prescriptions:')
    generate_presriptions()
    print('DONE')


if __name__ == '__main__':
    main()
