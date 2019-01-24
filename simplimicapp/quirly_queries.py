import os
import sys
import pandas as pd
import xarray as xr
import django
sys.path.append("../")
os.environ['DJANGO_SETTINGS_MODULE'] = 'simplimic.settings'
django.setup()
from django_pandas.io import read_frame
from simplimicapp.models import *


def get_admission(admID):
    """
    Queries the information on the corresponding admission and outputs:
     - an xarray with all descriptor values (unpreprocessed)in destacked long form (date_time index).
        dim0: time
        dim1: itemIDs
        dim2: param (e.g.: value, unit, flag, kind)
     - a df holding the meta information on Subject, Outcome, Diagnosis.
    :param admID:
    :return:
    """
    # get the descriptor dataset:
    descriptor_ds = _get_descriptors_array(admID)

    # get the info on the admission period:
    admission = Admission.objects.filter(admID=admID)
    admission_df = read_frame(admission).set_index('admID')
    
    # get info on diagnosis:
    diagnoses = Diagnosis.objects.filter(admID=admID)
    diagnoses_df = read_frame(diagnoses).set_index('admID')
    
    return descriptor_ds, admission_df, diagnoses_df


def _get_descriptors_array(admID):
    """
    Querry the descriptors information in an xarray. Format:
        dim0: time
        dim1: itemIDs
        dim2: param (e.g.: value, unit, flag, kind)

    :param admID:
    :return:
    """
    descriptors = DescriptorValue.objects.filter(admission=admID)

    # get the descriptors
    d_df = read_frame(descriptors).set_index('itemID').drop(['subject','admission','id'], axis=1)

    # convert to dataframe:
    d_df['chart_time'] = pd.to_datetime(d_df['chart_time'].values)
    d_df.sort_index(inplace=True)
    d_df.reset_index(inplace=True)

    # convert to wide format:
    param_dfs = dict()
    params = [c for c in d_df.columns if c not in ['itemID', 'chart_time']]

    for p in params:
        param_dfs[p] = d_df.drop([q for q in params if q !=  p], axis=1).pivot(index='chart_time', columns='itemID')

    # concat into xarray:
    #d_ds = xr.concat([p_df.to_xarray() for p_df in param_dfs], dim="descriptor_param")
    d_ds = pd.concat(param_dfs.values(), axis=1)
 
    return d_ds




