"""
https://en.wikipedia.org/wiki/Quarry_Bay
"""
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "simplimic.settings"
import re
import json
import django
django.setup()
import pandas as pd
from pprint import pprint
from django_pandas.io import read_frame
from simplimicapp.models import *


class Query(object):
    """
    Class performing the queries from the database.
    """
    def __init__(self, FLAGS):
        super(Query, self).__init__()
        self.FLAGS = FLAGS  # namespace object to hold the path to settings py and other stuff
        self.columns = ('chart_time', 'value', 'unit')

        with open(self.FLAGS.chartitems, 'r') as infobj:
            self.chartitems = json.load(infobj)
        with open(self.FLAGS.labitems, 'r') as infobj:
            self.labitems = json.load(infobj)

        # self._initialize()
    #
    # def _initialize(self):
        ##TODO: rewrite into regular init?
        # """
        # initialize the query and establish a connection to the database
        # :return:
        # """

    def query_stay(self, id):
        """
        Retrieve the data for a single icustay
        :param id:
        :return:
        """
        # charts = self.get_stay_chart_timeseries(id)
        labs = self.get_stay_lab_timeseries(id)

    def get_stay_chart_timeseries(self, icustay_id):
        """
        For given ICU-stay ID -> get the events as time series.
        :return:
        """
        # read in the items.json and get the terms we want
        events = []
        for descriptor, item in self.chartitems.items():
            var_events = ChartEventValue.objects.filter(icustay=icustay_id, itemID__exact=item).values(*self.columns)
            pprint(var_events)
            var_events = read_frame(var_events)
            var_events['variable'] = descriptor
            var_events['icustayID'] = icustay_id
            var_events.set_index('variable', inplace=True)
            events.append(var_events)

        events = pd.concat(var_events, axis=0)
        return events

    def get_stay_lab_timeseries(self, icustay_id):
        """
        1. look up the admission in the meta info
        :param icustay_id:
        :return:
        """
        stay = ICUstay.objects.filter(icustayID=icustay_id).values('intime', 'outtime', 'admission_id')
        assert len(stay) == 1

        intime = pd.to_datetime(stay[0]['intime'])
        outtime = pd.to_datetime(stay[0]['outtime'])
        admission_id = stay[0]['admission_id']

        # now query the relevant lab events:
        for descriptor, item in self.labitems.items():
            var_events = LabEventValue.objects.filter(admission=admission_id, chart_time__gte=intime,
                                                      chart_time__lte=outtime).values(*self.columns)
            pprint(var_events)
            # var_events = read_frame(var_events)
        raise NotImplementedError()



        raise NotImplementedError()


if __name__ == '__main__':
    # parse FLAGS:




    q = Query('/Users/buergelt/projects/thesis/scripts/mortimer/resources/config.JSON')


