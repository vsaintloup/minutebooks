from django.urls import path
from django.http import HttpResponse

def home(_):
    return HttpResponse("MinuteBooks OK")

urlpatterns = [path("", home, name="home")]
