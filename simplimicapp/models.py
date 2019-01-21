from django.db import models


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
    admID = models.IntegerField(default=None)
    adm_time = models.DateTimeField(default=None)
    disch_time = models.DateTimeField(default=None)
    adm_type = models.CharField(choices=ADMISSION_CHOICES, default=None, max_length=2)

    # Outcomes
    inpmor = models.BooleanField(default=None)  # in-hospital death
    pdimor = models.BooleanField(default=None)  # past discharge death (within 30 days)
    read = models.BooleanField(default=None)  # readmission (within 30)
    los = models.IntegerField(default=0)  # length of stay (in days)
    plos = models.BooleanField(default=None)  # prolonged length of stay


class Descriptor(models.Model):
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
    itemID = models.IntegerField(default=None)
    chart_time = models.DateTimeField(default=None)
    value = models.FloatField(default=None)
    unit = models.CharField(max_length=10)
    flag = models.CharField(max_length=8) # abnormal or normal


class Sevice(models.Model):
    """
    Holds information on the servive
    """
    # TODO:  no real need to define this as a class, might also be an attribute?
    pass


class Diagnosis(models.Model):
    """
    Holds information on the diagnosis.
    """
    # keys
    subject = models.ForeignKey('Patient', on_delete=models.CASCADE)
    admission = models.ForeignKey('Admission', on_delete=models.CASCADE)

    # fields
    seq_num = models.IntegerField(default=None, max_length=1)     # e.g. the rank of the diagnosis in the end of the admission
    icd_code = models.IntegerField(max_length=6)
    icd_class = models.IntegerField(max_length=2)


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

    # fields
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    drug_type = models.CharField(choices=DRUG_TYPE_CHOICES, default=None, max_length=1)
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

