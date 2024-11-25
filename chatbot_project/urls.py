from django.contrib import admin
from django.urls import path
from chatbot.views import chatbot_response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chatbot/api/chat/', chatbot_response, name='chatbot_response'),
    path('chatbot/api/image/', chatbot_response, name='chatbot_image'),

]
