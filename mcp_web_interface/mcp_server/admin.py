from django.contrib import admin

from .models import CustomPrompt, Chat, DeletedChat, FunctionResponse

# Register your models here.

admin.site.register(CustomPrompt)
admin.site.register(Chat)
admin.site.register(DeletedChat)
admin.site.register(FunctionResponse)