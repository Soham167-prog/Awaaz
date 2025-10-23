from rest_framework import serializers
from complaints.models import Complaint


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['id', 'image', 'public', 'location', 'title', 'description', 'predicted_severity', 'confidence', 'generated_text']
        read_only_fields = ['id']


class AnalyzeResponseSerializer(serializers.Serializer):
    severity = serializers.ChoiceField(choices=[('good','good'),('minor','minor'),('moderate','moderate'),('severe','severe')])
    confidence = serializers.FloatField()
    generated_text = serializers.CharField()


# New serializers for simple upload/post endpoints
class UploadComplaintSerializer(serializers.Serializer):
    image = serializers.ImageField()
    username = serializers.CharField()


class UploadComplaintResponseSerializer(serializers.Serializer):
    upload_id = serializers.IntegerField()
    draft = serializers.CharField()
    severity = serializers.CharField()


class PostComplaintSerializer(serializers.Serializer):
    complaint_text = serializers.CharField()
    username = serializers.CharField()
    severity = serializers.CharField()
    upload_id = serializers.IntegerField(required=False)


class PostComplaintResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    id = serializers.IntegerField(required=False)

