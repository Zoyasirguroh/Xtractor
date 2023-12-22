# # serializers.py

# from rest_framework import serializers

# class FilePathSerializer(serializers.Serializer):
#     file_path = serializers.CharField(max_length=255)
# myapp/serializers.py
from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['file_path']
