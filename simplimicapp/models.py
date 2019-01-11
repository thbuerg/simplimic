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

class StaticDescriptor(models.Model):
    """
    The class for a static descriptor. Should hold the value and name of descriptor.
    """
    descr_name = models.CharField(max_length=20)
    value = models.IntegerField(default=0)

    # TODO: define the link from Descriptor to admission
    # TODO: check whether values are `str` or `num`

class TSDescriptor(models.Model):
    """
    The class for an time series descriptor.
    
    """




