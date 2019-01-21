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


def generate_patients():
    # read in the cleaned admission file and create patients:
    adm_filt_df = pd.read_csv(os.path.join(DATADIR, 'admission_events_all.csv'))
    adm_filt_df.set_index('SUBJECT_ID')
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
        m.save()  # TODO: check if this is performant or if its  better todo w/ a single save!


def main():
    # setup
    django.setup()

    # go
    generate_patients()
    print('DONE')
    

if __name__ == '__main__':
    main()
