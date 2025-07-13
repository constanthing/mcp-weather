import uuid
from django.db import models

# Create your models here.

class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=30, default=None, null=True)
    history = models.TextField(default="[]")
    history_full = models.TextField(default="[]")
    created_at = models.DateTimeField(auto_now_add=True)
    model = models.CharField(max_length=255, default="gemini-2.5-flash")


class DeletedChat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history = models.TextField(default="[]")
    history_full = models.TextField(default="[]")
    created_at = models.DateTimeField(auto_now_add=True)


class CustomPrompt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # TODO: make sure interface character limit is 255
    name = models.CharField(max_length=255)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class FunctionResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.TextField()