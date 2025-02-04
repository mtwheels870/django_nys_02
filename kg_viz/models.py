from django.db import models

# Create your models here.
class PrdgyDataset(models.Model):
    name = models.CharField(max_length=255)
    created = models.BigIntegerField()
    meta = models.BinaryField()
    session = models.BooleanField()

    class Meta:
        db_table = 'dataset'  # Optional: specify the table name if different
        managed = False  # Important: prevent Django from managing migrations for this table
        app_label = 'prodigy'  # Specify the app label for this model

class PrdgyExample(models.Model):
    input_hash = models.BigIntegerField()
    content = models.BinaryField()
    task_hash = models.BigIntegerField()

    class Meta:
        db_table = 'example'  # Optional: specify the table name if different
        managed = False  # Important: prevent Django from managing migrations for this table
        app_label = 'prodigy'  # Specify the app label for this model

class PrdgyLink(models.Model):
    example_id = models.ForeignKey(PrdgyExample, on_delete=models.CASCADE)
    dataset_id = models.ForeignKey(PrdgyDataset, on_delete=models.CASCADE)

    class Meta:
        db_table = 'link'  # Optional: specify the table name if different
        managed = False  # Important: prevent Django from managing migrations for this table
        app_label = 'prodigy'  # Specify the app label for this model
