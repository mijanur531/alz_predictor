from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('', include('accounts.urls')),
    path('', include('appointments.urls')),
    path('', include('prescriptions.urls')),
    path('', include('training.urls')),
]

