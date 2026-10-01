from django.urls import re_path
from .consumers import DashboardConsumer, PatientConsumer, StaffAlertConsumer

websocket_urlpatterns = [
    re_path(r'^ws/dashboard/$', DashboardConsumer.as_asgi(), name='ws_dashboard'),
    re_path(r'^ws/patient/$', PatientConsumer.as_asgi(), name='ws_patient'),
    re_path(r'^ws/alerts/$', StaffAlertConsumer.as_asgi(), name='ws_alerts'),
]
