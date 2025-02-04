from django.db import models

class PrdgyDataset(models.Model):
    name = models.CharField(max_length=255)
    created = models.BigIntegerField()
    meta = models.BinaryField()
    session = models.BooleanField()

    class Meta:
        db_table = 'dataset'  # Optional: specify the table name if different
        managed = False  # Important: prevent Django from managing migrations for this table
        app_label = 'prodigy'  # Specify the app label for this model
