# myapp/models.py
from django.db import models

class File(models.Model):
    name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/')
