from django.db import models


class SUBJECT(models.Model):
    """
    The patient class for MIMIC-III.

    "ROW_ID","SUBJECT_ID","GENDER","DOB","DOD","DOD_HOSP","DOD_SSN","EXPIRE_FLAG"

    we keeo all  fields except row-IDs.
    """
    # TODO: 1. Determine if the pre-pop-processing will:
    # TODO:     - integerize static patients vars (GENDER, ETHNICITY)
    SUBJECT_ID = models.IntegerField(default=None, primary_key=True)
    GENDER = models.CharField(max_length=10)
    DOB = models.DateTimeField(default=None, max_length=20)
    DOD = models.DateTimeField(default=None, max_length=20)
    DOD_HOSP = models.DateTimeField(default=None, max_length=20)
    DOD_SSN = models.DateTimeField(default=None, max_length=20)   # ssn = stationary?
    EXPIRE_FLAG = models.BooleanField(default=None)   # TODO: is there a default?


class ADMISSION(models.Model):
    """
    Holds the information for a single admission period.

    "ROW_ID","SUBJECT_ID","HADM_ID","ADMITTIME","DISCHTIME","DEATHTIME","ADMISSION_TYPE",
    "ADMISSION_LOCATION","DISCHARGE_LOCATION","INSURANCE","LANGUAGE","RELIGION","MARITAL_STATUS",
    "ETHNICITY","EDREGTIME","EDOUTTIME","DIAGNOSIS","HOSPITAL_EXPIRE_FLAG","HAS_CHARTEVENTS_DATA"

    """
    ADMISSION_CHOICES = (    # TODO: since we're storing real data now: do we still want these?
        ('Elective',
         (('NB', 'newborn'),
         ('EL', 'elective')
         )),
        ('Non-elective',
         (('UR', 'urgent'),
         ('EM', 'emergency')
         )),
    )

    # meta
    SUBJECT = models.ForeignKey('SUBJECT', on_delete=models.CASCADE)
    HADM_ID = models.IntegerField(default=None,  primary_key=True)
    # adm_time = models.CharField(default=None, max_length=20, null=True, blank=True)
    ADMITTIME = models.DateTimeField(null=True, blank=True)
    # disch_time = models.CharField(default=None, max_length=20, null=True, blank=True)
    DISCHTIME = models.DateTimeField(null=True, blank=True)
    # death_time = models.CharField(default=None, max_length=20, null=True, blank=True)
    DEATHTIME = models.DateTimeField(default=None, null=True, blank=True)
    ADMISSION_TYPE = models.CharField(choices=ADMISSION_CHOICES, default=None, max_length=40)
    ADMISSION_LOCATION = models.CharField(default=None, max_length=40)  # TODO: get choices for this?
    DISCHARGE_LOCATION = models.CharField(default=None, max_length=40)  # TODO: get choices for this?
    INSURANCE = models.CharField(default=None, max_length=15)  # TODO: get choices for this?
    LANGUAGE = models.CharField(default=None, max_length=10, blank=True, null=True)  # may be `nan` (still str)
    RELIGION = models.CharField(default=None, max_length=30, blank=True, null=True)  # Fun Experiment proposal: proof indifference between religions by demonstrating statistical insignificance of religion choice as model covariate (after stripping outgroups. Sorry my `7TH DAY ADVENTIST`s)
    MARITAL_STATUS = models.CharField(default=None, max_length=50, blank=True, null=True)  # -> GREAT EXPERIMENTS IMAGINABLE HERE....
    ETHNICITY = models.CharField(default=None, max_length=150)
    EDREGTIME = models.DateTimeField(default=None, null=True, blank=True)
    EDOUTTIME = models.DateTimeField(default=None, null=True, blank=True)
    DIAGNOSIS = models.CharField(default=None, max_length=300)  # some of them are really detailed in description -> definitively better to use codes
    HOSPITAL_EXPIRE_FLAG = models.BooleanField(default=None) # TODO find out what this is
    HAS_CHARTEVENTS_DATA = models.BooleanField(default=None)


class ICUSTAY(models.Model):
    """
    The class holding ICU stays:
   "ROW_ID","SUBJECT_ID","HADM_ID","ICUSTAY_ID","DBSOURCE","FIRST_CAREUNIT","LAST_CAREUNIT", \
   "FIRST_WARDID","LAST_WARDID","INTIME","OUTTIME","LOS"
    """
    SUBJECT = models.ForeignKey('SUBJECT', on_delete=models.CASCADE)
    ADMISSION = models.ForeignKey('ADMISSION', on_delete=models.CASCADE)
    ICUSTAY_ID = models.IntegerField(default=None,  primary_key=True)
    DBSOURCE = models.CharField(default=None,  max_length=10) # TODO we most vertainly want a choice here
    FIRST_CAREUNIT = models.CharField(default=None,  max_length=10)
    LAST_CAREUNIT = models.CharField(default=None,  max_length=10)
    FIRST_WARDID = models.IntegerField(default=None)
    LAST_WARDID = models.IntegerField(default=None)
    INTIME = models.DateTimeField(default=None)  # important field.
    OUTTIME = models.DateTimeField(default=None)  # important field.
    LOS = models.IntegerField(default=None)


class CHARTEVENTVALUE(models.Model):
    """
    "ROW_ID","SUBJECT_ID","HADM_ID","ICUSTAY_ID","ITEMID","CHARTTIME","STORETIME","CGID","VALUE",
    "VALUENUM","VALUEUOM","WARNING","ERROR","RESULTSTATUS","STOPPED"
    This holds a single lab value
    itemID
    timestamps
    value
    unit (valueuom)
    """

    # keys
    SUBJECT = models.ForeignKey('SUBJECT', on_delete=models.CASCADE)
    ADMISSION = models.ForeignKey('ADMISSION', on_delete=models.CASCADE)
    ICUSTAY = models.ForeignKey('ICUSTAY', on_delete=models.CASCADE)
    ITEM = models.ForeignKey('CHARTITEM', on_delete=models.CASCADE)

    # Fields:
    CHARTTIME = models.DateTimeField(default=None) #, max_length=20)
    STORETIME = models.DateTimeField(default=None, null=True, blank=True) #, max_length=20, null=True, blank=True)
    CGID = models.CharField(default=None, max_length=10, null=True, blank=True)
    VALUE = models.CharField(default=None, max_length=210)
    VALUENUM = models.CharField(max_length=25, default=None, null=True, blank=True)  # TOOD check if float is safe here
    VALUEUOM = models.CharField(max_length=50, default=None, null=True, blank=True)  # TOOD check if float is safe here
    WARNING = models.CharField(default=None, max_length=25, null=True, blank=True)
    ERROR = models.CharField(default=None, max_length=25, null=True, blank=True)
    RESULTSTATUS = models.CharField(default=None, max_length=50, null=True, blank=True)  # contained only nans the top 1 Mio rows
    STOPPED = models.CharField(default=None, max_length=50, null=True, blank=True)  # contained only nans the top 1 Mio rows


class LABEVENTVALUE(models.Model):
    """
    This holds a single lab value
    itemID
    timestamps
    value
    unit (valueuom)

    "ROW_ID","SUBJECT_ID","HADM_ID","ITEMID","CHARTTIME","VALUE","VALUENUM","VALUEUOM","FLAG"
    """
    
    # keys
    SUBJECT = models.ForeignKey('SUBJECT', on_delete=models.CASCADE)
    ADMISSION = models.ForeignKey('ADMISSION', on_delete=models.CASCADE)
    ITEM = models.ForeignKey('LABITEM', on_delete=models.CASCADE)#, primary_key=True)   # TODO sure? it might actually  be smart to have squential keys...

    # Fields:
    CHARTTIME = models.DateTimeField(default=None, blank=True, null=True)
    VALUE = models.CharField(default=None, max_length=10, blank=True, null=True)
    VALUENUM = models.FloatField(default=None, null=True, blank=True)  # TOOD check if float is safe here
    VALUEUOM = models.CharField(max_length=10, default=None, null=True, blank=True)  # TOOD check if float is safe here
    UNIT = models.CharField(max_length=10, null=True, blank=True)
    FLAG = models.CharField(default=None, max_length=8, null=True, blank=True) # abnormal or normal for lab values


class SERVICE(models.Model):
    """
    Holds information on the servive
    "SUBJECT_ID","HADM_ID","TRANSFERTIME","PREV_SERVICE","CURR_SERVICE"
    """
    # keys
    SUBJECT = models.ForeignKey('SUBJECT', on_delete=models.CASCADE)
    ADMISSION = models.ForeignKey('ADMISSION', on_delete=models.CASCADE)

    # fields:
    TRANSFERTIME = models.CharField(default=None, max_length=20)

    # TODO: standardize through choices?
    PREV_SERVICE = models.CharField(default=None, max_length=10)
    CURR_SERVICE = models.CharField(default=None, max_length=10)


class CHARTITEM(models.Model):
    """
    "ROW_ID","ITEMID","LABEL","ABBREVIATION","DBSOURCE","LINKSTO","CATEGORY","UNITNAME","PARAM_TYPE","CONCEPTID"
    """
    ITEMID = models.IntegerField(primary_key=True, default=None)
    LABEL = models.CharField(default=None, max_length=100, null=True, blank=True)
    ABBREVIATION = models.CharField(default=None, max_length=100, null=True, blank=True)
    DBSOURCE = models.CharField(default=None, max_length=100, null=True, blank=True)
    LINKSTO = models.CharField(default=None, max_length=100, null=True, blank=True)
    CATEGORY = models.CharField(default=None, max_length=100, null=True, blank=True)
    UNITNAME = models.CharField(default=None, max_length=100, null=True, blank=True)
    PARAM_TYPE = models.CharField(default=None, max_length=100, null=True, blank=True)
    CONCEPTID = models.CharField(default=None, max_length=100, null=True, blank=True)


class LABITEM(models.Model):
    """
    "ROW_ID","ITEMID","LABEL","FLUID","CATEGORY","LOINC_CODE"
    """
    ITEMID = models.IntegerField(primary_key=True, default=None)
    LABEL = models.CharField(default=None, max_length=100, null=True, blank=True)
    FLUID = models.CharField(default=None, max_length=100, null=True, blank=True)
    CATEGORY = models.CharField(default=None, max_length=100, null=True, blank=True)
    LOINC_CODE = models.CharField(default=None, max_length=100, null=True, blank=True)


class DIAGNOSIS(models.Model):
    """
    Holds information on the diagnosis.
    "ROW_ID","SUBJECT_ID","HADM_ID","SEQ_NUM","ICD9_CODE"
    """
    # keys
    SUBJECT = models.ForeignKey('SUBJECT', on_delete=models.CASCADE)
    ADMISSION = models.ForeignKey('ADMISSION', on_delete=models.CASCADE)
    # no ICU here

    # fields
    SEQ_NUM = models.CharField(default=None, max_length=20, null=True, blank=True)     # e.g. the rank of the diagnosis in the end of the admission
    ICD9_CODE = models.CharField(default=None, max_length=20, null=True, blank=True)
    ICD_CLASS = models.CharField(default=None, max_length=20, null=True, blank=True)


class PRESCRIPTION(models.Model):
    """
    Holds information about a drug
    """
    DRUG_TYPE_CHOICES = (
        ('M', 'MAIN'),
         ('A', 'ADDITIVE'),
         ('B', 'BASE')
    )
    ROUTE_CHOICES = (
        # TODO: implement
    )
    # keys
    SUBJECT = models.ForeignKey('SUBJECT', on_delete=models.CASCADE)
    ADMISSION = models.ForeignKey('ADMISSION', on_delete=models.CASCADE)
    ICUSTAY = models.ForeignKey('ICUSTAY', on_delete=models.CASCADE)

    # fields
    STARTDATE = models.CharField(default=None, max_length=20, null=True)
    ENDDATE = models.CharField(default=None, max_length=20, null=True)
    DRUG_TYPE = models.CharField(choices=DRUG_TYPE_CHOICES, default=None, max_length=1, null=True)
    DRUG = models.CharField(default=None, max_length=25, null=True)#, primary_key=True)   # TODO: check  if we want primary key here
    DRUG_NAME_POE = models.CharField(default=None, max_length=25, null=True)
    DRUG_NAME_GENERIC = models.CharField(default=None, max_length=25, null=True)
    FORMULARY_DRUG_CD = models.CharField(default=None, max_length=15, null=True)
    GSN = models.FloatField(default=None, null=True, blank=True)  # this is mostly INTs but some NaNs  disallow intfield.
    NDC = models.FloatField(default=None, null=True, blank=True)
    PROD_STRENGTH = models.CharField(default=None, max_length=25, null=True)
    DOSE_VAL_RX = models.CharField(default=None, max_length=25, null=True)  # can't take  float here as there are ranges somtimes
    DOSE_UNIT_RX = models.CharField(default=None, max_length=25, null=True)
    FORM_VAL_DISP = models.CharField(default=None, max_length=25, null=True)  # can't take  float here as there are ranges somtimes
    FORM_UNIT_DISP = models.CharField(default=None, max_length=25, null=True)
    ROUTE = models.CharField(default=None, max_length=25, null=True)   # TODO: establish a CHOICE set here that is hierarchical!
