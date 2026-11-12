from django.urls import path
from .views import ModelTrainingDashboardView

urlpatterns = [
    path('management/training/', ModelTrainingDashboardView.as_view(), name='model_training_dashboard'),
]
