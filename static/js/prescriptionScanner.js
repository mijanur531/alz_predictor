/**
 * Prescription OCR Scanner & LLM Drug Interaction Engine
 */
class PrescriptionScannerManager {
    static init() {
        this.dropZone = document.getElementById('prescriptionDropZone');
        this.fileInput = document.getElementById('prescriptionFileInput');
        this.textInput = document.getElementById('prescriptionRawText');
        this.previewContainer = document.getElementById('prescriptionPreviewContainer');
        this.previewImg = document.getElementById('prescriptionImgPreview');
        this.submitBtn = document.getElementById('btnSubmitScan');
        this.resultsContainer = document.getElementById('scanResultsContainer');
        
        this.bindEvents();
    }

    static bindEvents() {
        if (this.dropZone && this.fileInput) {
            this.dropZone.addEventListener('click', () => this.fileInput.click());
            
            this.dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                this.dropZone.classList.add('border-primary', 'bg-light');
            });

            this.dropZone.addEventListener('dragleave', () => {
                this.dropZone.classList.remove('border-primary', 'bg-light');
            });

            this.dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                this.dropZone.classList.remove('border-primary', 'bg-light');
                if (e.dataTransfer.files.length) {
                    this.fileInput.files = e.dataTransfer.files;
                    this.handleFileSelected(e.dataTransfer.files[0]);
                }
            });

            this.fileInput.addEventListener('change', () => {
                if (this.fileInput.files.length) {
                    this.handleFileSelected(this.fileInput.files[0]);
                }
            });
        }

        // Preset templates
        document.querySelectorAll('[data-preset-rx]').forEach(btn => {
            btn.addEventListener('click', () => {
                const rxType = btn.getAttribute('data-preset-rx');
                this.loadPreset(rxType);
            });
        });

        // Submit button
        if (this.submitBtn) {
            this.submitBtn.addEventListener('click', () => this.handleSubmit());
        }

        // Delete scan triggers
        document.addEventListener('click', async (e) => {
            const deleteBtn = e.target.closest('[data-action="delete-scan"]');
            if (deleteBtn) {
                const scanId = deleteBtn.getAttribute('data-scan-id');
                if (confirm('Are you sure you want to delete this prescription scan?')) {
                    try {
                        await ApiClient.deletePrescription(scanId);
                        const row = deleteBtn.closest('.scan-card-item');
                        if (row) row.remove();
                    } catch (err) {
                        alert(`Failed to delete scan: ${err.message}`);
                    }
                }
            }
        });
    }

    static handleFileSelected(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file (PNG, JPEG, WebP).');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            if (this.previewImg) {
                this.previewImg.src = e.target.result;
            }
            if (this.previewContainer) {
                this.previewContainer.classList.remove('d-none');
            }
        };
        reader.readAsDataURL(file);
    }

    static loadPreset(type) {
        if (!this.textInput) return;
        const presets = {
            'donepezil': "PRESCRIPTION INTAKE\nPatient: John Doe | Age: 71\nRx: Donepezil Hydrochloride 10mg Tablets\nSig: Take 1 tablet by mouth daily at bedtime.\nIndication: Mild to moderate Alzheimer's dementia.\nRefills: 3",
            'memantine': "CLINICAL RX RECORD\nPatient: Sarah Jenkins | Age: 78\nRx: Memantine HCl 10mg Tablets (Namenda)\nSig: Take 1 tablet twice daily with food.\nIndication: Moderate to severe Alzheimer's disease.",
            'combo': "NEUROLOGY PRESCRIPTION\nPatient: Robert Taylor | Age: 74\n1. Donepezil 10mg PO Daily\n2. Memantine 10mg PO BID\nRefills: 2. Clinic: Memorial Neurology Institute"
        };
        this.textInput.value = presets[type] || presets['donepezil'];
    }

    static async handleSubmit() {
        const file = this.fileInput?.files?.[0];
        const rawText = this.textInput?.value?.trim();

        if (!file && !rawText) {
            alert('Please upload a prescription image or enter clinical prescription text.');
            return;
        }

        const originalText = this.submitBtn.innerHTML;
        this.submitBtn.disabled = true;
        this.submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Analyzing with LLM...`;

        try {
            let result;
            if (file) {
                const formData = new FormData();
                formData.append('uploaded_image', file);
                if (rawText) formData.append('raw_text', rawText);
                result = await ApiClient.uploadPrescription(formData);
            } else {
                result = await ApiClient.uploadPrescription({ raw_text: rawText });
            }

            this.renderScanResult(result);
        } catch (err) {
            alert(`Analysis Error: ${err.message || 'Failed to scan prescription.'}`);
        } finally {
            this.submitBtn.disabled = false;
            this.submitBtn.innerHTML = originalText;
        }
    }

    static renderScanResult(scan) {
        if (!this.resultsContainer) return;
        this.resultsContainer.classList.remove('d-none');

        const drugsHtml = (scan.detected_medicines || []).map(d => `
            <span class="badge bg-primary-subtle text-primary fs-6 px-3 py-2 rounded-pill me-2 mb-2">
                💊 ${d}
            </span>
        `).join('') || '<span class="text-muted">No specific Alzheimer medications detected</span>';

        this.resultsContainer.innerHTML = `
            <div class="nuvica-card p-4 border-success mt-4">
                <div class="d-flex align-items-center justify-content-between mb-3">
                    <h5 class="fw-bold mb-0 text-dark">📋 Clinical NLP & LLM Analysis Result</h5>
                    <span class="badge bg-success-subtle text-success">Scan ID #${scan.id} Verified</span>
                </div>
                <div class="mb-3">
                    <div class="text-muted small mb-2">Detected Alzheimer's Therapeutics:</div>
                    <div class="d-flex flex-wrap">${drugsHtml}</div>
                </div>
                <div class="p-3 bg-light rounded-3 mb-3">
                    <div class="fw-bold small text-muted mb-2">Clinical LLM Recommendations:</div>
                    <div class="markdown-output small" style="white-space: pre-line;">${scan.llm_analysis}</div>
                </div>
                <div class="d-flex gap-2">
                    <a href="/appointments/booking/" class="btn btn-pill btn-pill-primary">
                        Discuss Rx with Neurologist ↗
                    </a>
                    <button class="btn btn-pill btn-pill-light" onclick="window.location.reload()">New Scan</button>
                </div>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    PrescriptionScannerManager.init();
});

window.PrescriptionScannerManager = PrescriptionScannerManager;

