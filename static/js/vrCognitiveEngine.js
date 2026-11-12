/**
 * Interactive VR & Spatial Memory Cognitive Testing Engine
 * Tracks user reaction latency, errors, spatial memory accuracy,
 * and submits telemetry to DRF API endpoint /api/v1/vr-tasks/submit/
 */
class VRCognitiveEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        
        this.nodes = [];
        this.sequence = [];
        this.userSequence = [];
        this.state = 'IDLE'; // IDLE, SHOWING, PLAYING, COMPLETED
        this.currentRound = 1;
        this.maxRounds = 4;
        this.errors = 0;
        this.startTime = 0;
        this.totalDuration = 0;
        
        this.initCanvas();
        this.bindEvents();
    }

    initCanvas() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.generateNodes();
        this.render();
    }

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * (window.devicePixelRatio || 1);
        this.canvas.height = rect.height * (window.devicePixelRatio || 1);
        this.ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        this.width = rect.width;
        this.height = rect.height;
    }

    generateNodes() {
        this.nodes = [];
        const numNodes = 6;
        const radius = Math.min(this.width, this.height) * 0.35;
        const centerX = this.width / 2;
        const centerY = this.height / 2;

        for (let i = 0; i < numNodes; i++) {
            const angle = (i / numNodes) * Math.PI * 2 - Math.PI / 2;
            this.nodes.push({
                id: i,
                x: centerX + Math.cos(angle) * radius,
                y: centerY + Math.sin(angle) * radius,
                radius: 34,
                active: false,
                highlightColor: '#6366f1',
                label: `Node ${i + 1}`
            });
        }
    }

    bindEvents() {
        this.canvas.addEventListener('click', (e) => {
            if (this.state !== 'PLAYING') return;
            const rect = this.canvas.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;

            for (let node of this.nodes) {
                const dist = Math.hypot(node.x - clickX, node.y - clickY);
                if (dist <= node.radius) {
                    this.handleNodeClick(node);
                    break;
                }
            }
        });

        const startBtn = document.getElementById('btnStartVRTask');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startAssessment());
        }
    }

    startAssessment() {
        this.state = 'SHOWING';
        this.currentRound = 1;
        this.errors = 0;
        this.startTime = performance.now();
        this.updateStatusText('🧠 Observe the neural sequence...');
        this.generateSequence();
        this.playSequence();
    }

    generateSequence() {
        this.sequence = [];
        const length = this.currentRound + 2; // Round 1: 3 nodes, Round 2: 4 nodes, etc.
        for (let i = 0; i < length; i++) {
            this.sequence.push(Math.floor(Math.random() * this.nodes.length));
        }
        this.userSequence = [];
    }

    async playSequence() {
        this.state = 'SHOWING';
        for (let idx of this.sequence) {
            await this.flashNode(this.nodes[idx], 650);
            await new Promise(r => setTimeout(r, 250));
        }
        this.state = 'PLAYING';
        this.updateStatusText('👉 Your Turn: Repeat the neural sequence!');
    }

    flashNode(node, duration = 500, color = '#6366f1') {
        return new Promise(resolve => {
            node.active = true;
            node.highlightColor = color;
            this.render();
            setTimeout(() => {
                node.active = false;
                this.render();
                resolve();
            }, duration);
        });
    }

    async handleNodeClick(node) {
        this.flashNode(node, 200, '#0d9488');
        this.userSequence.push(node.id);
        const currentStep = this.userSequence.length - 1;

        if (this.userSequence[currentStep] !== this.sequence[currentStep]) {
            // Incorrect
            this.errors++;
            this.updateStatusText('❌ Sequence error! Try to maintain spatial focus.');
            await this.flashNode(node, 400, '#e11d48');
        }

        if (this.userSequence.length === this.sequence.length) {
            if (this.currentRound < this.maxRounds) {
                this.currentRound++;
                this.updateStatusText(`✅ Level passed! Moving to Level ${this.currentRound}...`);
                setTimeout(() => {
                    this.generateSequence();
                    this.playSequence();
                }, 1000);
            } else {
                this.finishAssessment();
            }
        }
    }

    async finishAssessment() {
        this.state = 'COMPLETED';
        const endTime = performance.now();
        this.totalDuration = Math.round((endTime - this.startTime) / 100) / 10; // seconds

        // Calculate score (100 - penalties)
        const errorPenalty = this.errors * 12;
        const timePenalty = Math.max(0, (this.totalDuration - 25) * 1.5);
        const rawScore = Math.max(20, Math.min(100, Math.round(100 - errorPenalty - timePenalty)));
        const mmseScore = Math.round((rawScore / 100.0) * 30.0 * 10) / 10;

        this.updateStatusText(`🎉 VR Spatial Assessment Complete! Score: ${rawScore}/100 (MMSE: ${mmseScore}/30)`);

        try {
            // Submit to API
            const result = await ApiClient.submitVRTask({
                time_taken: this.totalDuration,
                errors: this.errors,
                score: rawScore
            });

            this.displayResultsModal(rawScore, mmseScore, this.totalDuration, this.errors);
        } catch (err) {
            console.error('Failed to submit VR telemetry:', err);
            this.displayResultsModal(rawScore, mmseScore, this.totalDuration, this.errors);
        }
    }

    displayResultsModal(score, mmse, timeTaken, errors) {
        const resultContainer = document.getElementById('vrResultSummary');
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="p-4 bg-white rounded-4 shadow-sm border mt-3">
                    <div class="d-flex align-items-center justify-content-between mb-3">
                        <h5 class="fw-bold mb-0 text-primary">Cognitive Task Results</h5>
                        <span class="badge bg-success-subtle text-success fs-6">${score >= 80 ? 'Optimal Performance' : score >= 60 ? 'Moderate Alert' : 'Specialist Attention Suggested'}</span>
                    </div>
                    <div class="row g-3 text-center mb-4">
                        <div class="col-4">
                            <div class="p-3 bg-light rounded-3">
                                <div class="text-muted small">MMSE Score</div>
                                <div class="fs-4 fw-bold text-dark">${mmse} / 30</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-3 bg-light rounded-3">
                                <div class="text-muted small">Time Taken</div>
                                <div class="fs-4 fw-bold text-dark">${timeTaken}s</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-3 bg-light rounded-3">
                                <div class="text-muted small">Mistakes</div>
                                <div class="fs-4 fw-bold text-danger">${errors}</div>
                            </div>
                        </div>
                    </div>
                    <div class="d-flex gap-2 flex-wrap">
                        <a href="/dashboard/?auto_mmse=${mmse}#predictionFormCard" class="btn btn-pill btn-pill-primary flex-grow-1">
                            Transfer Score to AI Diagnostic Assessment ↗
                        </a>
                        <button class="btn btn-pill btn-pill-light" onclick="window.location.reload()">Retry Test</button>
                    </div>
                </div>
            `;
        }
    }

    updateStatusText(msg) {
        const el = document.getElementById('vrTaskStatus');
        if (el) el.textContent = msg;
    }

    render() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.width, this.height);

        // Background subtle grid
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        this.ctx.lineWidth = 1;
        const step = 40;
        for (let x = 0; x < this.width; x += step) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.height);
            this.ctx.stroke();
        }
        for (let y = 0; y < this.height; y += step) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.width, y);
            this.ctx.stroke();
        }

        // Connect lines between nodes
        this.ctx.strokeStyle = 'rgba(99, 102, 241, 0.25)';
        this.ctx.lineWidth = 2;
        for (let i = 0; i < this.nodes.length; i++) {
            for (let j = i + 1; j < this.nodes.length; j++) {
                this.ctx.beginPath();
                this.ctx.moveTo(this.nodes[i].x, this.nodes[i].y);
                this.ctx.lineTo(this.nodes[j].x, this.nodes[j].y);
                this.ctx.stroke();
            }
        }

        // Draw nodes
        this.nodes.forEach(node => {
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
            if (node.active) {
                this.ctx.fillStyle = node.highlightColor;
                this.ctx.shadowColor = node.highlightColor;
                this.ctx.shadowBlur = 20;
            } else {
                this.ctx.fillStyle = '#1e293b';
                this.ctx.shadowBlur = 0;
            }
            this.ctx.fill();
            this.ctx.lineWidth = 3;
            this.ctx.strokeStyle = node.active ? '#ffffff' : '#475569';
            this.ctx.stroke();
            this.ctx.shadowBlur = 0;

            // Label
            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = '600 13px Outfit, sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(node.label, node.x, node.y);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('vrCanvas')) {
        window.vrEngine = new VRCognitiveEngine('vrCanvas');
    }
});

window.VRCognitiveEngine = VRCognitiveEngine;

