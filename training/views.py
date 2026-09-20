from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json

from accounts.views import ManagementRequiredMixin
from training.models import TrainedModelArtifact
from training.tasks import run_model_training_task

class ModelTrainingDashboardView(LoginRequiredMixin, ManagementRequiredMixin, TemplateView):
    template_name = "training/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["models"] = TrainedModelArtifact.objects.all().order_by("-created_at")
        return context

    def post(self, request, *args, **kwargs):
        """
        Triggers the model training task. Returns JSON status response.
        """
        try:
            body = json.loads(request.body)
            model_type = body.get("model_type", "Random Forest")
            
            # Extract hyperparameters based on model type
            hyperparams = {}
            if model_type == "Deep Learning MLP":
                hyperparams["epochs"] = int(body.get("epochs", 10))
                hyperparams["learning_rate"] = float(body.get("learning_rate", 0.01))
                hyperparams["hidden_units"] = int(body.get("hidden_units", 64))
            else: # Random Forest
                hyperparams["epochs"] = int(body.get("epochs", 8)) # Simulated epochs
                hyperparams["n_estimators"] = int(body.get("n_estimators", 100))
                hyperparams["max_depth"] = int(body.get("max_depth", 10))
            
            # Enqueue celery task
            task = run_model_training_task.delay(model_type, hyperparams)
            
            return JsonResponse({
                "status": "STARTED",
                "task_id": task.id,
                "message": f"Training session started for {model_type}."
            })
        except Exception as e:
            return JsonResponse({
                "status": "ERROR",
                "message": str(e)
            }, status=400)
