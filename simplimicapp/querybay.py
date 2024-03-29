"""
In memory of the days in:
>>> https://en.wikipedia.org/wiki/Quarry_Bay

"""
import os
import sys
import simplimic.settings
os.environ["DJANGO_SETTINGS_MODULE"] = "simplimic.settings"
import re
import json
import django
django.setup()
import pandas as pd
import numpy as np
from pprint import pprint
from datetime import timedelta
from django_pandas.io import read_frame
from simplimicapp.models import *
from simplimicapp.util import *


class Query(object):
    """
    Class performing the queries from the database.
    """
    def __init__(self, FLAGS, warm_start_id=None):
        super(Query, self).__init__()
        self.FLAGS = FLAGS  # namespace object to hold the path to settings py and other stuff

        with open(self.FLAGS.chartitems, 'r') as infobj:
            self.chartitems = pd.read_csv(infobj)
        with open(self.FLAGS.labitems, 'r') as infobj:
            self.labitems = pd.read_csv(infobj)

        # get list of all stays:
        self.stays_map = self._get_stays_map(warm_start_id)

    def _get_stays_map(self, warm_start_id=None):
        """ GEt a list of all stay IDs in the  database """
        stays = ICUSTAY.objects.filter(
            ADMISSION__ADMITTIME__range=(
                django.db.models.F('SUBJECT__DOB') + timedelta(days=365*self.FLAGS.agerange[0]),
                django.db.models.F('SUBJECT__DOB') + timedelta(days=365*self.FLAGS.agerange[1])),
            ADMISSION__HAS_CHARTEVENTS_DATA=True,
            LOS__range=(self.FLAGS.losrange[0], self.FLAGS.losrange[1]),
            DBSOURCE__exact='metavision').values('ICUSTAY_ID', 'ADMISSION', 'SUBJECT')

        # for each stay check if there are chartevents from metavision and if not, drop the stay\
        stays = pd.concat([pd.Series(s).to_frame().T for s in stays])
        stays = stays.sort_values('ICUSTAY_ID')
        
        if warm_start_id is not None:
            stays.set_index('ICUSTAY_ID', inplace=True)
            drop = stays.index.values <= warm_start_id
            stays.drop(stays.loc[drop].index.values, inplace=True)
            stays.reset_index(inplace=True)

            
        return stays

    def query_stay(self, id):
        """
        Retrieve the data for a single icustay.
        :param id:
        :return:
        """
        events = pd.concat([self.get_stay_chart_timeseries(id),
                            self.get_stay_lab_timeseries(id)], axis=0)
        meta = self.get_stay_meta(id)

        return events, meta

    def get_stay_meta(self, id_):
        """
        Query the  meta information for an  icu stay.

        Raise QueryError if there is no 1-to-1 mapping between stay and admission.
        :param id:
        :return:
        """
        stay = ICUSTAY.objects.filter(ICUSTAY_ID=id_).values('INTIME', 'OUTTIME', 'ADMISSION', 'SUBJECT')
        meta_df = read_frame(stay)

        # reindex:
        meta_df = meta_df.reset_index().drop('index', axis=1)

        # admission
        admission = ADMISSION.objects.filter(HADM_ID=stay[0]['ADMISSION'])\
            .values('ADMITTIME',
                    'DISCHTIME',
                    'DEATHTIME',  # time of death recorded in hospital, if it was NaT we set it to '1911-11-11 11:11:11'
                    'HOSPITAL_EXPIRE_FLAG',  # binary FLAG whether the patient died during the admission
                    'ADMISSION_TYPE',
                    'ADMISSION_LOCATION',
                    'DIAGNOSIS',
                    )
        admission_df = read_frame(admission)
        admission_df = admission_df.reset_index().drop('index', axis=1)

        # subject
        subject = SUBJECT.objects.filter(SUBJECT_ID=stay[0]['SUBJECT'])\
            .values('GENDER',
                    'DOB',  # to calculate the age
                    'DOD_HOSP',  # date of death as recorded in hospital
                    'DOD',  # date of death, not necessarily in hosp. matched with Social security Nr.
                    'EXPIRE_FLAG', # wheter patient died or not
                    )
        subject_df = read_frame(subject)
        subject_df = subject_df.reset_index().drop('index', axis=1)

        for df in [subject_df, admission_df]:
            meta_df[df.columns] = df

        for c in ['SUBJECT', 'ADMISSION']:
            meta_df.loc[0, c] = int(re.search(re.compile('(\d+)'), meta_df.loc[0, c]).group())

        # ensure a 1-to-1 mapping between admission and icustay:
        n_stays = ICUSTAY.objects.filter(ADMISSION=meta_df['ADMISSION']).values('ICUSTAY_ID', 'SUBJECT')
        n_stays = read_frame(n_stays)
        if n_stays.shape[0] > 1:
            # only keep the first stay:
            if n_stays.loc[0, 'ICUSTAY_ID'] != id_:
                print('not first stay')
                raise ResourceWarning()

        meta_df['icustay'] = int(id_)

        for c in ['INTIME', 'OUTTIME', 'ADMITTIME', 'DISCHTIME', 'DEATHTIME', 'DOD', 'DOD_HOSP', 'DOB']:
            meta_df[c] = pd.to_datetime(meta_df[c])
        meta_df.fillna(np.nan, inplace=True)

        return meta_df

    def get_stay_chart_timeseries(self, icustay_id):
        """
        For given ICU-stay ID -> get the events as time series.
        :return:
        """
        # read in the items.json and get the terms we want
        events = []
        for i, r in self.chartitems.iterrows():
            descriptor = r['descriptor'] 
            item = r['item'] 
            var_events = CHARTEVENTVALUE.objects.filter(
                ICUSTAY=icustay_id,
                ITEM__ITEMID__exact=item,
                ITEM__DBSOURCE__exact='metavision').values('CHARTTIME', 'VALUE', 'VALUEUOM')
                # ).values('CHARTTIME', 'VALUE', 'VALUEUOM')
                                                    # TODO: check what we want!!!
                                                    # ).values('ITEM__ITEMID', 'CHARTTIME', 'VALUE', 'UNIT')
            # var_events=CHARTEVENTVALUE.objects.all().values('CHARTTIME', 'VALUE', 'VALUEUOM')
            var_events = read_frame(var_events)
            # var_events['ITEMID'] = var_events['ITEM__ITEMID']
            # var_events.drop('ITEMID', inplace=True)
            var_events['VARIABLE'] = descriptor
            var_events['VALUEUOM'].fillna('unknown', inplace=True)
            var_events['icustay'] = icustay_id
            var_events.set_index('VARIABLE', inplace=True)
            events.append(var_events)

        events = pd.concat(events, axis=0)
        events['KIND'] = 'chart'
        return events

    def get_stay_lab_timeseries(self, icustay_id):
        """
        1. look up the admission in the meta info
        :param icustay_id:
        :return:
        """
        stay = ICUSTAY.objects.filter(ICUSTAY_ID=icustay_id).values('INTIME', 'OUTTIME', 'ADMISSION')
        assert len(stay) == 1

        intime = pd.to_datetime(stay[0]['INTIME'])
        outtime = pd.to_datetime(stay[0]['OUTTIME'])
        admission_id = stay[0]['ADMISSION']

        # now query the relevant lab events:
        events = []
        for i, r in self.labitems.iterrows():
            descriptor = r['descriptor'] 
            item = r['item']
            var_events = LABEVENTVALUE.objects.filter(ADMISSION=admission_id,
                                                      ITEM__ITEMID__exact=item,
                                                      CHARTTIME__gte=intime,
                                                      CHARTTIME__lte=outtime
                                                      ).values('CHARTTIME', 'VALUE', 'VALUEUOM')
            # TODO: check what we want!!!
                                                      # ).values('ITEM__ITEMID', 'CHARTTIME', 'VALUE', 'UNIT')
            var_events = read_frame(var_events)
            # var_events['ITEMID'] = var_events['ITEM__ITEMID']
            # var_events.drop('ITEMID', inplace=True)
            var_events['VARIABLE'] = descriptor
            var_events['icustay'] = icustay_id
            var_events['VALUEUOM'].fillna('unknown', inplace=True)
            var_events.set_index('VARIABLE', inplace=True)
            events.append(var_events)
        events = pd.concat(events, axis=0)
        events['KIND'] = 'lab'
        return events


if __name__ == '__main__':
    raise NotImplementedError('No implemented standalone use.')

