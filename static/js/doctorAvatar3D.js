/**
 * Doctor 3D Avatar & Holographic Speech Synthesizer
 * Uses Canvas 3D Hologram & Web Speech API to provide interactive vocal diagnostic consults.
 */
class DoctorAvatar3D {
    constructor(canvasId, textOutputId) {
        this.canvas = document.getElementById(canvasId);
        this.outputEl = document.getElementById(textOutputId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.isSpeaking = false;
        this.animFrameId = null;
        this.angle = 0;
        this.pulse = 0;
        
        this.initCanvas();
        this.bindEvents();
        this.animate();
    }

    initCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * (window.devicePixelRatio || 1);
        this.canvas.height = rect.height * (window.devicePixelRatio || 1);
        this.ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        this.width = rect.width;
        this.height = rect.height;
    }

    bindEvents() {
        window.addEventListener('resize', () => this.initCanvas());

        const speakBtn = document.getElementById('btnSpeakDoctorAdvice');
        if (speakBtn) {
            speakBtn.addEventListener('click', () => {
                const text = this.outputEl ? this.outputEl.innerText : 'Hello, I am Dr. Evelyn, your AI Medical Assistant. Your cognitive assessment results have been processed.';
                this.speak(text);
            });
        }

        const stopBtn = document.getElementById('btnStopDoctorSpeech');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopSpeaking());
        }

        // Listen for new prediction events
        window.addEventListener('prediction:received', (e) => {
            const pred = e.detail;
            const msg = `Diagnostic Assessment complete. Evaluated risk category: ${pred.class}, with a confidence score of ${Math.round(pred.probability * 100)} percent. Please consult our neurology department for comprehensive clinical staging.`;
            if (this.outputEl) {
                this.outputEl.innerHTML = `<strong>Dr. Evelyn:</strong> "${msg}"`;
            }
            this.speak(msg);
        });
    }

    speak(text) {
        if (!('speechSynthesis' in window)) {
            console.warn('Speech synthesis not supported in this browser.');
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.05;

        // Try to pick a natural medical/doctor voice
        const voices = window.speechSynthesis.getVoices();
        const femaleVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Female') || v.name.includes('Samantha') || v.name.includes('Natural') || v.name.includes('Google UK English Female')));
        if (femaleVoice) {
            utterance.voice = femaleVoice;
        }

        utterance.onstart = () => {
            this.isSpeaking = true;
            this.updateSpeakingBadge(true);
        };

        utterance.onend = () => {
            this.isSpeaking = false;
            this.updateSpeakingBadge(false);
        };

        utterance.onerror = () => {
            this.isSpeaking = false;
            this.updateSpeakingBadge(false);
        };

        window.speechSynthesis.speak(utterance);
    }

    stopSpeaking() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        this.isSpeaking = false;
        this.updateSpeakingBadge(false);
    }

    updateSpeakingBadge(speaking) {
        const badge = document.getElementById('doctorSpeakingBadge');
        if (badge) {
            if (speaking) {
                badge.classList.remove('d-none');
                badge.innerHTML = `<span class="spinner-grow spinner-grow-sm me-1 text-danger"></span> Speaking...`;
            } else {
                badge.classList.add('d-none');
            }
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        this.angle += 0.02;
        this.pulse += this.isSpeaking ? 0.08 : 0.03;

        const baseRadius = 55 + Math.sin(this.pulse) * (this.isSpeaking ? 8 : 3);

        // 1. Holographic Aura Rings
        for (let i = 1; i <= 3; i++) {
            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY, baseRadius + i * 22, 0, Math.PI * 2);
            this.ctx.strokeStyle = `rgba(99, 102, 241, ${0.18 / i})`;
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
        }

        // 2. Rotating Particles Ring
        const numParticles = 16;
        for (let i = 0; i < numParticles; i++) {
            const partAngle = this.angle + (i / numParticles) * Math.PI * 2;
            const px = centerX + Math.cos(partAngle) * (baseRadius + 15);
            const py = centerY + Math.sin(partAngle) * (baseRadius + 15);

            this.ctx.beginPath();
            this.ctx.arc(px, py, 3.5, 0, Math.PI * 2);
            this.ctx.fillStyle = this.isSpeaking ? '#38bdf8' : '#818cf8';
            this.ctx.shadowColor = '#38bdf8';
            this.ctx.shadowBlur = 10;
            this.ctx.fill();
            this.ctx.shadowBlur = 0;
        }

        // 3. Central Hologram Core Avatar
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, baseRadius, 0, Math.PI * 2);
        const grad = this.ctx.createRadialGradient(centerX, centerY, 5, centerX, centerY, baseRadius);
        grad.addColorStop(0, this.isSpeaking ? '#6366f1' : '#4f46e5');
        grad.addColorStop(0.7, '#312e81');
        grad.addColorStop(1, '#1e1b4b');
        this.ctx.fillStyle = grad;
        this.ctx.fill();
        this.ctx.lineWidth = 3;
        this.ctx.strokeStyle = '#a5b4fc';
        this.ctx.stroke();

        // 4. Stethoscope / Caduceus / Face Icon inside Core
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = '36px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(this.isSpeaking ? '🗣️' : '👩‍⚕️', centerX, centerY - 2);

        // 5. Sound Wave Bars if Speaking
        if (this.isSpeaking) {
            const waveY = centerY + baseRadius + 40;
            const numBars = 18;
            const barWidth = 4;
            const gap = 5;
            const totalWidth = numBars * (barWidth + gap);
            const startX = centerX - totalWidth / 2;

            for (let i = 0; i < numBars; i++) {
                const barHeight = 8 + Math.abs(Math.sin(this.pulse * 2 + i * 0.5)) * 26;
                const bx = startX + i * (barWidth + gap);
                const by = waveY - barHeight / 2;

                this.ctx.fillStyle = '#38bdf8';
                this.ctx.beginPath();
                this.ctx.roundRect(bx, by, barWidth, barHeight, 2);
                this.ctx.fill();
            }
        }

        this.animFrameId = requestAnimationFrame(() => this.animate());
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('doctorAvatarCanvas')) {
        window.doctorAvatar = new DoctorAvatar3D('doctorAvatarCanvas', 'doctorSpeechBubble');
    }
});

window.DoctorAvatar3D = DoctorAvatar3D;

