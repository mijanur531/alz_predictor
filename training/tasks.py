from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from management.models import AuditLog
from training.models import TrainedModelArtifact
import time
import random

@shared_task(name='training.tasks.run_model_training_task')
def run_model_training_task(model_type, hyperparameters):
    """
    Simulates training an ML (Random Forest) or DL (Multi-Layer Perceptron) model.
    Sends live progress metrics (loss, accuracy) via WebSockets to the dashboard.
    Saves the output as the active TrainedModelArtifact.
    """
    channel_layer = get_channel_layer()
    
    # Extract training configurations
    epochs = int(hyperparameters.get("epochs", 10))
    learning_rate = float(hyperparameters.get("learning_rate", 0.01))
    hidden_units = int(hyperparameters.get("hidden_units", 64))
    n_estimators = int(hyperparameters.get("n_estimators", 100))
    max_depth = int(hyperparameters.get("max_depth", 10))
    
    # Cap epochs at 15 for responsive demo testing
    epochs = min(epochs, 15)
    
    # Telemetry tracking lists
    loss_curve = []
    accuracy_curve = []

    # Initial values
    loss = 0.85
    accuracy = 0.55

    for epoch in range(1, epochs + 1):
        # Training iteration delay
        time.sleep(0.5)

        # Learning simulation step (loss goes down, accuracy goes up)
        if model_type == "Deep Learning MLP":
            decay = learning_rate * 5.0
            loss -= (loss * random.uniform(0.1, 0.2)) * (1.0 - decay)
            accuracy += (1.0 - accuracy) * random.uniform(0.08, 0.15)
        else: # Random Forest
            loss -= (loss * random.uniform(0.15, 0.25))
            accuracy += (1.0 - accuracy) * random.uniform(0.12, 0.22)

        # Bounding values
        loss = max(0.04, round(loss, 4))
        accuracy = min(0.97, round(accuracy, 4))

        loss_curve.append(loss)
        accuracy_curve.append(accuracy)

        # Send live updates to WS subscribers
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "management_dashboard",
                {
                    "type": "dashboard_update",
                    "data": {
                        "event": "training_progress",
                        "data": {
                            "epoch": epoch,
                            "total_epochs": epochs,
                            "loss": loss,
                            "accuracy": accuracy,
                            "status": "TRAINING"
                        }
                    }
                }
            )

    # 4. Finalizing training artifacts
    final_accuracy = accuracy
    final_loss = loss
    
    # Deactivate older models
    TrainedModelArtifact.objects.filter(is_active=True).update(is_active=False)

    # Create new model record
    model_name = f"{model_type.replace(' ', '_')}_{int(time.time())}"
    artifact = TrainedModelArtifact.objects.create(
        name=model_name,
        model_type=model_type,
        hyperparameters=hyperparameters,
        metrics={
            "final_accuracy": final_accuracy,
            "final_loss": final_loss,
            "loss_curve": loss_curve,
            "accuracy_curve": accuracy_curve
        },
        is_active=True
    )

    # Save to Audit log
    AuditLog.objects.create(
        user=None,  # System task
        action="model_training_completed",
        metadata={
            "model_id": artifact.id,
            "model_type": model_type,
            "accuracy": final_accuracy,
            "loss": final_loss
        }
    )

    # Broadcast final status
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            "management_dashboard",
            {
                "type": "dashboard_update",
                "data": {
                    "event": "training_progress",
                    "data": {
                        "status": "COMPLETE",
                        "model_name": model_name,
                        "accuracy": final_accuracy,
                        "loss": final_loss
                    }
                }
            }
        )

    return {
        "status": "SUCCESS",
        "model_id": artifact.id,
        "model_name": model_name,
        "accuracy": final_accuracy,
        "loss": final_loss
    }
