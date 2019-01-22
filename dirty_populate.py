import os
os.environ["DJANGO_SETTINGS_MODULE"] = "simplimic.settings"
import django
django.setup()
import pandas as pd
from simplimicapp.models import *

# some dirty FLAGS:
DATADIR = '/Users/buergelt/projects/thesis/data/mimic_proc_all'

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
    adm_filt_df.set_index('SUBJECT_ID')

    # patients:
    patients = adm_filt_df.loc[~adm_filt_df.index.duplicated(keep='first')]
    patients.drop(['HADM_ID',
                   'ADMITTIME',
                   'DISCHTIME',
                   'ADMISSION_TYPE',
                   'INPMOR',
                   'PDISMOR',
                   'READ',
                   'LOS',
                   'PLOS',], axis=1, inplace=True)

    # generate an django entry for each row:
    # patient_models = []
    for i, r in patients.iterrows():
        m = Patient(
            subjectID = i,
            gender = r['GENDER'],
            age = r['AGE'],
            date_of_birth = r['DOB']
        )
        # patient_models.append(m)
        m.save()

    # free up mem:
    del patients

    # Admission periods:
    for i, r in adm_filt_df.iterrows():
        # get the Patient first
        p = Patient.objects.get(subjectID=i)
        m = Admission(
            subject=p,
            admID=r['HADM_ID'],
            adm_time=r['ADMITTIME'],
            disch_time=r['DISCHTIME'],
            adm_type=r['ADMISSION_TYPE'],  # TODO: convert to the choice we set first?!
            inpmor=r['INPMOR'],
            pdimor=r['PDIMOR'],
            read=r['READ'],
            los=r['LOS'],
            plos=r['PLOS']
        )
        m.save()

def generate_chartevents():
    """
    Generates the chartevents table. As the table comes in  stacked long-format, it first has to be formated by:
        - hadmID
        - then itemID
        - then models are generated per descriptor
    :return:
    """
    pass
    


def main():
    # setup
    django.setup()

    # go
    # generate_patients_and_admissions()
    generate_chartevents()

    print('DONE')


if __name__ == '__main__':
    main()
