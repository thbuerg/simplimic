from django.db import models


class Patient(models.Model):
    """
    The patient class for MIMIC-III.

    we keeo all  fields except row-IDs.
    """
    # TODO: 1. Determine if the pre-pop-processing will:
    # TODO:     - integerize static patients vars (GENDER, ETHNICITY)
    subjectID = models.IntegerField(default=None, primary_key=True)
    gender = models.CharField(max_length=10)
    age = models.IntegerField(default=0)
    date_of_birth = models.CharField(default=None, max_length=20)
    date_of_death = models.CharField(default=None, max_length=20)
    date_of_death_hosp = models.CharField(default=None, max_length=20)
    date_of_death_ssn = models.CharField(default=None, max_length=20)   # ssn = stationary?
    expire_flag = models.BooleanField(default=None)   # TODO: is there a default?


class Admission(models.Model):
    """
    Holds the information for a single admission period.
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
    subject = models.ForeignKey('Patient', on_delete=models.CASCADE)
    admID = models.IntegerField(default=None,  primary_key=True)
    # adm_time = models.CharField(default=None, max_length=20, null=True, blank=True)
    adm_time = models.DateTimeField(null=True, blank=True)
    # disch_time = models.CharField(default=None, max_length=20, null=True, blank=True)
    disch_time = models.DateTimeField(null=True, blank=True)
    # death_time = models.CharField(default=None, max_length=20, null=True, blank=True)
    death_time = models.DateTimeField(default=None, null=True, blank=True)
    adm_type = models.CharField(choices=ADMISSION_CHOICES, default=None, max_length=2)
    adm_location = models.CharField(default=None, max_length=40)  # TODO: get choices for this?
    disch_location = models.CharField(default=None, max_length=40)  # TODO: get choices for this?
    insurance = models.CharField(default=None, max_length=15)  # TODO: get choices for this?
    language = models.CharField(default=None, max_length=10)  # may be `nan` (still str)
    religion = models.CharField(default=None, max_length=10)  # Fun Experiment proposal: proof indifference between religions by demonstrating statistical insignificance of religion choice as model covariate (after stripping outgroups. Sorry my `7TH DAY ADVENTIST`s)
    marital_status = models.CharField(default=None, max_length=10)  # -> GREAT EXPERIMENTS IMAGINABLE HERE....
    ethnicity = models.CharField(default=None, max_length=50)
    edregtime = models.DateTimeField(default=None, null=True, blank=True)
    edouttime = models.DateTimeField(default=None, null=True, blank=True)
    init_diagnosis = models.CharField(default=None, max_length=100)  # some of them are really detailed in description -> definitively better to use codes
    hosp_exp_flag = models.BooleanField(default=None) # TODO find out what this is
    has_chartevents = models.BooleanField(default=None)

class ICUstay(models.Model):
    """
    The class holding ICU stays:
   "ROW_ID","SUBJECT_ID","HADM_ID","ICUSTAY_ID","DBSOURCE","FIRST_CAREUNIT","LAST_CAREUNIT", \
   "FIRST_WARDID","LAST_WARDID","INTIME","OUTTIME","LOS"
    """
    subject = models.ForeignKey('Patient', on_delete=models.CASCADE)
    admission = models.ForeignKey('Admission', on_delete=models.CASCADE)
    icustayID = models.IntegerField(default=None,  primary_key=True)
    db_source = models.CharField(default=None,  max_length=10) # TODO we most vertainly want a choice here
    first_cu = models.CharField(default=None,  max_length=10)
    last_cu = models.CharField(default=None,  max_length=10)
    first_ward_id = models.IntegerField(default=None)
    last_ward_id = models.IntegerField(default=None)
    intime = models.DateTimeField(default=None)  # important field.
    outtime = models.DateTimeField(default=None)  # important field.
    los = models.IntegerField(default=None)


class ChartEventValue(models.Model):
    """
    This holds a single lab value
    itemID
    timestamps
    value
    unit (valueuom)
    """

    # keys
    subject = models.ForeignKey('Patient', on_delete=models.CASCADE)
    admission = models.ForeignKey('Admission', on_delete=models.CASCADE)
    icustay = models.ForeignKey('ICUstay', on_delete=models.CASCADE)

    # Fields:
    itemID = models.IntegerField(default=None) #, primary_key=True)   # TODO sure? it might actually  be smart to have squential keys...
    chart_time = models.DateTimeField(default=None) #, max_length=20)
    store_time = models.DateTimeField(default=None, null=True, blank=True) #, max_length=20, null=True, blank=True)
    cgID = models.CharField(default=None, max_length=10, null=True, blank=True)
    value = models.CharField(default=None, max_length=10)
    valuenum = models.FloatField(default=None, null=True, blank=True)  # TOOD check if float is safe here
    unit = models.CharField(max_length=10)
    warning = models.CharField(default=None, max_length=25, null=True, blank=True)
    error = models.CharField(default=None, max_length=25, null=True, blank=True)
    resultstatus = models.CharField(default=None, max_length=50, null=True, blank=True)  # contained only nans the top 1 Mio rows
    stopped = models.CharField(default=None, max_length=50, null=True, blank=True)  # contained only nans the top 1 Mio rows


class LabEventValue(models.Model):
    """
    This holds a single lab value
    itemID
    timestamps
    value
    unit (valueuom)
    """
    
    # keys
    subject = models.ForeignKey('Patient', on_delete=models.CASCADE)
    admission = models.ForeignKey('Admission', on_delete=models.CASCADE)

    # Fields:
    itemID = models.IntegerField(default=None)#, primary_key=True)   # TODO sure? it might actually  be smart to have squential keys...
    # chart_time = models.CharField(default=None, max_length=20, blank=True, null=True)
    chart_time = models.DateTimeField(default=None, blank=True, null=True)
    value = models.CharField(default=None, max_length=10, blank=True, null=True)
    valuenum = models.FloatField(default=None, null=True, blank=True)  # TOOD check if float is safe here
    unit = models.CharField(max_length=10, null=True, blank=True)
    flag = models.CharField(default=None, max_length=8, null=True, blank=True) # abnormal or normal for lab values


class Service(models.Model):
    """
    Holds information on the servive
    "SUBJECT_ID","HADM_ID","TRANSFERTIME","PREV_SERVICE","CURR_SERVICE"
    """
    # keys
    subject = models.ForeignKey('Patient', on_delete=models.CASCADE)
    admission = models.ForeignKey('Admission', on_delete=models.CASCADE)

    # fields:
    transfertime = models.CharField(default=None, max_length=20)

    # TODO: standardize through choices?
    prev_service = models.CharField(default=None, max_length=10)
    curr_service = models.CharField(default=None, max_length=10)


class Diagnosis(models.Model):
    """
    Holds information on the diagnosis.
    "ROW_ID","SUBJECT_ID","HADM_ID","SEQ_NUM","ICD9_CODE"
    """
    # keys
    subject = models.ForeignKey('Patient', on_delete=models.CASCADE)
    admission = models.ForeignKey('Admission', on_delete=models.CASCADE)
    # no ICU here

    # fields
    seq_num = models.IntegerField(default=None)     # e.g. the rank of the diagnosis in the end of the admission
    icd_code = models.IntegerField(primary_key=True)

    # TODO: map this in prepopproc?:
    #icd_class = models.IntegerField()


class Prescription(models.Model):
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
    subject = models.ForeignKey('Patient', on_delete=models.CASCADE)
    admission = models.ForeignKey('Admission', on_delete=models.CASCADE)
    icustay = models.ForeignKey('ICUstay', on_delete=models.CASCADE)

    # fields
    start_date = models.CharField(default=None, max_length=20, null=True)
    end_date = models.CharField(default=None, max_length=20, null=True)
    drug_type = models.CharField(choices=DRUG_TYPE_CHOICES, default=None, max_length=1, null=True)
    drug = models.CharField(default=None, max_length=25, null=True)#, primary_key=True)   # TODO: check  if we want primary key here
    drug_name_poe = models.CharField(default=None, max_length=25, null=True)
    drug_name_generic = models.CharField(default=None, max_length=25, null=True)
    formulary_drug_cd = models.CharField(default=None, max_length=15, null=True)
    gsn = models.FloatField(default=None, null=True, blank=True)  # this is mostly INTs but some NaNs  disallow intfield.
    ndc = models.FloatField(default=None, null=True, blank=True)
    prod_strength = models.CharField(default=None, max_length=25, null=True)
    dose_val_rx = models.CharField(default=None, max_length=25, null=True)  # can't take  float here as there are ranges somtimes
    dose_unit_rx = models.CharField(default=None, max_length=25, null=True)
    form_val_disp = models.CharField(default=None, max_length=25, null=True)  # can't take  float here as there are ranges somtimes
    form_unit_disp = models.CharField(default=None, max_length=25, null=True)
    route = models.CharField(default=None, max_length=25, null=True)   # TODO: establish a CHOICE set here that is hierarchical!
