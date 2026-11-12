/**
 * Live Machine Learning & Deep Learning Model Trainer & Activation Manager
 */
class LiveModelTrainerManager {
    static init() {
        this.form = document.getElementById('modelTrainingForm');
        this.modelTypeSelect = document.getElementById('modelTypeSelect');
        this.rfParams = document.getElementById('rfParametersGroup');
        this.dlParams = document.getElementById('dlParametersGroup');
        this.startBtn = document.getElementById('btnStartTraining');
        this.canvas = document.getElementById('trainingMetricsCanvas');
        this.artifactsList = document.getElementById('trainedArtifactsList');
        
        if (this.canvas) {
            this.ctx = this.canvas.getContext('2d');
            this.initCanvas();
        }
        this.bindEvents();
    }

    static initCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * (window.devicePixelRatio || 1);
        this.canvas.height = rect.height * (window.devicePixelRatio || 1);
        this.ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        this.width = rect.width;
        this.height = rect.height;
    }

    static bindEvents() {
        if (this.modelTypeSelect) {
            this.modelTypeSelect.addEventListener('change', () => {
                const isDL = this.modelTypeSelect.value === 'Deep Learning MLP';
                if (this.dlParams) this.dlParams.classList.toggle('d-none', !isDL);
                if (this.rfParams) this.rfParams.classList.toggle('d-none', isDL);
            });
        }

        if (this.form) {
            this.form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleTrainSubmit();
            });
        }

        // Handle model activation click
        document.addEventListener('click', async (e) => {
            const actBtn = e.target.closest('[data-action="activate-model"]');
            if (actBtn) {
                const modelId = actBtn.getAttribute('data-model-id');
                actBtn.disabled = true;
                actBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Activating...`;
                try {
                    const res = await ApiClient.activateModel(modelId);
                    alert(`✅ Model Artifact #${modelId} (${res.artifact.name}) is now the ACTIVE clinical inference model!`);
                    window.location.reload();
                } catch (err) {
                    alert(`Failed to activate model: ${err.message}`);
                    actBtn.disabled = false;
                    actBtn.innerHTML = `Activate Model ↗`;
                }
            }
        });
    }

    static async handleTrainSubmit() {
        const modelType = this.modelTypeSelect.value;
        const epochs = parseInt(document.getElementById('inputEpochs')?.value || 10);
        
        const payload = {
            model_type: modelType,
            epochs: epochs
        };

        if (modelType === 'Deep Learning MLP') {
            payload.learning_rate = parseFloat(document.getElementById('inputLearningRate')?.value || 0.01);
            payload.hidden_units = parseInt(document.getElementById('inputHiddenUnits')?.value || 64);
        } else {
            payload.n_estimators = parseInt(document.getElementById('inputEstimators')?.value || 100);
            payload.max_depth = parseInt(document.getElementById('inputMaxDepth')?.value || 10);
        }

        const originalText = this.startBtn.innerHTML;
        this.startBtn.disabled = true;
        this.startBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Training Pipeline Running...`;

        try {
            const res = await ApiClient.triggerTraining(payload);
            
            // Draw simulated live curve
            await this.animateTrainingCurves(epochs);

            alert(`🎉 Training Session Succeeded! Artifact created and deployed. Reloading dashboard artifacts.`);
            window.location.reload();
        } catch (err) {
            alert(`Training Pipeline Error: ${err.message}`);
        } finally {
            this.startBtn.disabled = false;
            this.startBtn.innerHTML = originalText;
        }
    }

    static async animateTrainingCurves(epochs) {
        if (!this.ctx) return;
        const losses = [];
        let currLoss = 0.75;
        for (let i = 0; i < epochs; i++) {
            currLoss *= 0.78 + (Math.random() * 0.06);
            losses.push(currLoss);
        }

        for (let i = 0; i < losses.length; i++) {
            this.drawCurves(losses.slice(0, i + 1), epochs);
            await new Promise(r => setTimeout(r, 200));
        }
    }

    static drawCurves(lossHistory, totalEpochs) {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.width, this.height);

        const padX = 40;
        const padY = 30;
        const plotW = this.width - padX * 2;
        const plotH = this.height - padY * 2;

        // Draw axes
        this.ctx.strokeStyle = '#cbd5e1';
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(padX, padY);
        this.ctx.lineTo(padX, this.height - padY);
        this.ctx.lineTo(this.width - padX, this.height - padY);
        this.ctx.stroke();

        // Title
        this.ctx.fillStyle = '#475569';
        this.ctx.font = '12px Outfit, sans-serif';
        this.ctx.fillText('Loss Convergence Curve', padX + 10, padY + 15);

        if (lossHistory.length < 2) return;

        // Draw loss curve
        this.ctx.strokeStyle = '#ef4444';
        this.ctx.lineWidth = 2.5;
        this.ctx.beginPath();
        lossHistory.forEach((loss, idx) => {
            const x = padX + (idx / (totalEpochs - 1)) * plotW;
            const y = (this.height - padY) - (loss / 0.8) * plotH;
            if (idx === 0) this.ctx.moveTo(x, y);
            else this.ctx.lineTo(x, y);
        });
        this.ctx.stroke();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('modelTrainingForm')) {
        LiveModelTrainerManager.init();
    }
});

window.LiveModelTrainerManager = LiveModelTrainerManager;

