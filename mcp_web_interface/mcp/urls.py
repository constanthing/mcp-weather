"""
URL configuration for mcp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from mcp_server import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='get_custom_prompts'),
    path('chat/', views.chat, name='chat'),
    path('chat/<uuid:chat_id>/', views.chat, name='chat'),
    path('custom_prompts/', views.create_custom_prompt, name='create_custom_prompt'),
    path('custom_prompts/<uuid:custom_prompt_id>/', views.custom_prompt_actions, name='custom_prompt_actions'),
]
