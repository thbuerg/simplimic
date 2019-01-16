from django.db import models

# Create your models here.

class Patient(models.Model):
    """
    The patient class for MIMIC-III.
    """
    subjectID = models.IntegerField(default=None)
    gender = models.CharField(max_length=1)
    age = models.IntegerField(default=0)
    date_of_birth = models.DateField(default=None)


class Admission(models.Model):
    """
    Holds the information for a single admission period.
    """
    ADMISSION_CHOICES = (
        ('Elective',
         ('NB', 'newborn'),
         ('EL', 'elective')
         ),
        ('Non-elective',
         ('UR', 'urgent'),
         ('EM', 'emergency')
         ),
    )

    # meta
    subjectID = models.IntegerField(default=None)  # TODO: need to define explicitly or is implicitly through queries enough?
    admID = models.IntegerField(default=None)
    adm_time = models.DateTimeField(default=None)
    disch_time = models.DateTimeField(default=None)
    adm_type = models.CharField(choices=ADMISSION_CHOICES, default=None)

    # Outcomes
    inpmor = models.BooleanField(default=None)  # in-hospital death
    pdimor = models.BooleanField(default=None)  # past discharge death (within 30 days)
    read = models.BooleanField(default=None)  # readmission (within 30)
    los = models.IntegerField(default=0)  # length of stay (in days)
    plos = models.BooleanField(default=None)  # prolonged length of stay

    # TODO: define the link from admission to patient
    #3


class Sevice(models.Model):
    """
    Holds information on the servive
    """
    # TODO:  no real need to define this as a class, might also be an attribute?
    pass


class Descriptor(models.Model):
    """
    The class for a descriptor.

    This holds measurements. either a single if its static, or multiple if its a TS.
    """
    # TODO: find out if we need an explicit definition of the HADM and SUBJID here or if queries
    #       and relations will take care of that
    subjectID = models.IntegerField(default=None)  # TODO: need to define explicitly or is implicitly through queries enough?
    admID = models.IntegerField(default=None)


    # TODO: check out how MEasurements can be linked to the descriptor
    # 1 to many relation needed here


class Measurement(models.Model):
    """
    Holds information on a single measurement
    """
    descr_name = models.CharField(max_length=20)
    itemID = models.IntegerField(default=None)
    chart_time = models.DateTimeField(default=None)
    value = models.FloatField(default=None)
    unit = models.CharField(max_length=10)

    # TODO: define the link from Descriptor to admission
    # TODO: check whether values are `str` or `num`


class Diagnosis(models.Model):
    """
    Holds information on the diagnosis.
    """
    seq_num = models.IntegerField(default=None, max_length=1)     # e.g. the rank of the diagnosis in the end of the admission
    icd_code = models.IntegerField(max_length=6)
    icd_class = models.IntegerField(max_length=2)


class Drug(models.Model):
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
    """
    PROD_STRENGTH,DOSE_VAL_RX,DOSE_UNIT_RX,FORM_VAL_DISP,FORM_UNIT_DISP,ROUTE """
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    drug_type = models.CharField(choices=DRUG_TYPE_CHOICES, default=None)
    drug = models.CharField(default=None, max_length=25)
    drug_name_poe = models.CharField(default=None, max_length=25)
    drug_name_generic = models.CharField(default=None, max_length=25)
    formulary_drug_cd = models.CharField(default=None, max_length=15)
    gsn = models.IntegerField(default=None, max_length=15)
    ndc = models.FloatField(default=None, max_length=25)
    prod_strength = models.CharField(default=None, max_length=25)
    dose_val_rx = models.CharField(default=None, max_length=25)  # can't take  float here as there are ranges somtimes
    dose_unit_rx = models.CharField(default=None, max_length=25)
    form_val_disp = models.CharField(default=None, max_length=25)  # can't take  float here as there are ranges somtimes
    form_unit_disp = models.CharField(default=None, max_length=25)
    route = models.CharField(default=None, max_length=25)   # TODO: establish a CHOICE set here that is hierarchical!



