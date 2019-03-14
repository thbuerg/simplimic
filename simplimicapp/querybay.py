"""
In memory of the days in:
>>> https://en.wikipedia.org/wiki/Quarry_Bay

"""
import os
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
    def __init__(self, FLAGS):
        super(Query, self).__init__()
        self.FLAGS = FLAGS  # namespace object to hold the path to settings py and other stuff

        with open(self.FLAGS.chartitems, 'r') as infobj:
            self.chartitems = json.load(infobj)
        with open(self.FLAGS.labitems, 'r') as infobj:
            self.labitems = json.load(infobj)

        # get list of all stays:
        self.stays_map = self._get_stays_map()

    def _get_stays_map(self):
        """ GEt a list of all stay IDs in the  database """
        stays = ICUSTAY.objects.filter(
            ADMISSION__ADMITTIME__range=(
                django.db.models.F('SUBJECT__DOB' + timedelta(years=18)),
                django.db.models.F('SUBJECT__DOB' + timedelta(years=110))),
            ADMISSION__HAS_CHARTEVENTS_DATA=True,
            DBSOURCE__exact='metavision').values('ICUSTAY_ID', 'ADMISSION', 'SUBJECT')

        # for each stay check if there are chartevents from metavision and if not, drop the stay\
        stays = pd.concat([pd.Series(s).to_frame().T for s in stays])
        stays = stays.sort_values('ICUSTAY_ID')

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
        meta_df['INTIME'] = pd.to_datetime(meta_df['INTIME'])
        meta_df['OUTTIME'] = pd.to_datetime(meta_df['OUTTIME'])

        # admission
        admission = ADMISSION.objects.filter(HADM_ID=stay[0]['ADMISSION'])\
            .values('ADMITTIME', 'DISCHTIME', 'DEATHTIME')
        admission_df = read_frame(admission)

        # subject
        subject = SUBJECT.objects.filter(SUBJECT_ID=stay[0]['SUBJECT'])\
            .values('GENDER', 'DOD_HOSP')
        subject_df = read_frame(subject)

        for df in [subject_df, admission_df]:
            for c in df.columns:
                meta_df[c] = df[c]

        for c in ['SUBJECT', 'ADMISSION']:
            meta_df.loc[0, c] = int(re.search(re.compile('(\d+)'), meta_df.loc[0, c]).group())

        # ensure a 1-to-1 mapping between admission and icustay:
        n_stays = ICUSTAY.objects.filter(ADMISSION=meta_df['ADMISSION']).values('ICUSTAY_ID', 'SUBJECT')
        n_stays = read_frame(n_stays)
        if n_stays.shape[0] > 1:
            # only keep the first stay:
            if n_stays.loc[0, 'ICUSTAY_ID'] != id_:
                raise ResourceWarning()

        meta_df['ICUSTAY'] = int(id_)

        meta_df.fillna(np.nan, inplace=True)

        return meta_df

    def get_stay_chart_timeseries(self, icustay_id):
        """
        For given ICU-stay ID -> get the events as time series.
        :return:
        """
        # read in the items.json and get the terms we want
        events = []
        for descriptor, item in self.chartitems.items():
            var_events = CHARTEVENTVALUE.objects.filter(
                ICUSTAY=icustay_id,
                ITEM__ITEMID__exact=item,
                ITEM__DBSOURCE__exact='metavision').values('CHARTTIME', 'VALUE', 'UNIT')
                                                    # TODO: check what we want!!!
                                                    # ).values('ITEM__ITEMID', 'CHARTTIME', 'VALUE', 'UNIT')
            var_events = read_frame(var_events)
            # var_events['ITEMID'] = var_events['ITEM__ITEMID']
            # var_events.drop('ITEMID', inplace=True)
            var_events['VARIABLE'] = descriptor
            var_events['ICUSTAY'] = icustay_id
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
        for descriptor, item in self.labitems.items():
            var_events = LABEVENTVALUE.objects.filter(ADMISSION=admission_id,
                                                      CHARTTIME__gte=intime,
                                                      CHARTTIME__lte=outtime
                                                      ).values('CHARTTIME', 'VALUE', 'UNIT')
            # TODO: check what we want!!!
                                                      # ).values('ITEM__ITEMID', 'CHARTTIME', 'VALUE', 'UNIT')
            var_events = read_frame(var_events)
            # var_events['ITEMID'] = var_events['ITEM__ITEMID']
            # var_events.drop('ITEMID', inplace=True)
            var_events['VARIABLE'] = descriptor
            var_events['ICUSTAY'] = icustay_id
            var_events.set_index('VARIABLE', inplace=True)
            events.append(var_events)
        events = pd.concat(events, axis=0)
        events['KIND'] = 'lab'
        return events


if __name__ == '__main__':
    raise NotImplementedError('No implemented standalone use.')

