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


class Descriptor(models.Model):
    """
    The class for a descriptor.

    This holds measurements. either a single if its static, or multiple if its a TS.
    """
    # TODO: find out if we need an explicit definition of the HADM and SUBJID here or if queries
    #       and relations will take care of that

    # TODO: check out how MEasurements can be linked to the descriptor
    # 1 to many relation needed here


class Diagnosis(models.Model):
    """
    Holds information on the diagnosis.
    """
    seq_num = models.IntegerField(default=None)     # e.g. the rank of the admission in the patient
    icd_code = models.IntegerField(max_length=6)
    icd_class = models.IntegerField(max_length=2)


class Measurement(models.Model):
    """
    Holds information on a single measurement
    """
    descr_name = models.CharField(max_length=20)
    itemID = models.IntegerField(default=None)
    chart_time = models.DateTimeField(default=None)
    value = models.IntegerField(default=None)
    unit = models.CharField(max_length=10)

    # TODO: define the link from Descriptor to admission
    # TODO: check whether values are `str` or `num`


class Drug(models.Model):
    """
    Holds information about a drug
    """
    # TODO: implement
    pass


