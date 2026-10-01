/**
 * Modern ES6+ / TypeScript-style API Client for AlzPredictor DRF v1
 * Provides async/await wrappers with automatic token handling and DOM events.
 */
class ApiClient {
    static BASE_URL = '/api/v1';

    static async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.BASE_URL}${endpoint}`;
        const isFormData = options.body instanceof FormData;
        
        const defaultHeaders = CookieManager.getAuthHeaders(!isFormData);
        const headers = { ...defaultHeaders, ...(options.headers || {}) };

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);
            
            window.dispatchEvent(new CustomEvent('api:response', {
                detail: { url, status: response.status, ok: response.ok }
            }));

            if (response.status === 401) {
                console.warn('API Authentication required or session expired.');
            }

            const contentType = response.headers.get('content-type');
            let data = null;
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                const errorMsg = data?.detail || data?.error || data?.message || (typeof data === 'string' ? data : JSON.stringify(data));
                throw new Error(errorMsg || `HTTP Error ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`ApiClient error [${options.method || 'GET'} ${url}]:`, error);
            window.dispatchEvent(new CustomEvent('api:error', {
                detail: { url, error: error.message }
            }));
            throw error;
        }
    }

    // Auth
    static async login(username, password) {
        const data = await this.request('/auth/token/', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        if (data.access) {
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            CookieManager.set('access_token', data.access, 1);
        }
        return data;
    }

    static async register(userData) {
        return this.request('/auth/register/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    static async getCurrentUser() {
        return this.request('/auth/me/');
    }

    // Predictions
    static async getMyPredictions() {
        return this.request('/patients/me/predictions/');
    }

    static async getPredictionDetail(id) {
        return this.request(`/patients/me/predictions/${id}/`);
    }

    static async submitPrediction(clinicalData) {
        return this.request('/predict/', {
            method: 'POST',
            body: JSON.stringify(clinicalData)
        });
    }

    static async checkPredictStatus(taskId) {
        return this.request(`/predict/status/${taskId}/`);
    }

    static async deletePrediction(id) {
        return this.request(`/predict/${id}/delete/`, {
            method: 'POST'
        });
    }

    // Doctors & Appointments
    static async getDoctors() {
        return this.request('/appointments/doctors/');
    }

    static async getDoctorDetail(id) {
        return this.request(`/doctors/${id}/`);
    }

    static async bookAppointment(appointmentData) {
        return this.request('/appointments/book/', {
            method: 'POST',
            body: JSON.stringify(appointmentData)
        });
    }

    static async getMyAppointments() {
        return this.request('/appointments/my-bookings/');
    }

    static async cancelAppointment(id) {
        return this.request(`/appointments/${id}/cancel/`, {
            method: 'POST'
        });
    }

    // VR Tasks
    static async submitVRTask(gameMetrics) {
        return this.request('/vr-tasks/submit/', {
            method: 'POST',
            body: JSON.stringify(gameMetrics)
        });
    }

    static async getVRHistory() {
        return this.request('/vr-tasks/history/');
    }

    static async deleteVRRecord(id) {
        return this.request(`/vr-tasks/${id}/delete/`, {
            method: 'POST'
        });
    }

    // Prescriptions
    static async getPrescriptionHistory() {
        return this.request('/prescriptions/');
    }

    static async uploadPrescription(formDataOrJson) {
        const isFormData = formDataOrJson instanceof FormData;
        return this.request('/prescriptions/', {
            method: 'POST',
            body: isFormData ? formDataOrJson : JSON.stringify(formDataOrJson)
        });
    }

    static async deletePrescription(id) {
        return this.request(`/prescriptions/${id}/delete/`, {
            method: 'POST'
        });
    }

    // Model Training
    static async getTrainedModels() {
        return this.request('/training/models/');
    }

    static async triggerTraining(config) {
        return this.request('/training/train/', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    static async activateModel(id) {
        return this.request(`/training/models/${id}/activate/`, {
            method: 'POST'
        });
    }

    // Contact & Alerts
    static async submitContact(contactData) {
        return this.request('/contact/', {
            method: 'POST',
            body: JSON.stringify(contactData)
        });
    }

    static async getContactMessages() {
        return this.request('/contact/');
    }

    // Service & Management
    static async getServiceCases(isReviewed = null) {
        const query = isReviewed !== null ? `?is_reviewed=${isReviewed}` : '';
        return this.request(`/service/cases/${query}`);
    }

    static async reviewServiceCase(id, reviewData) {
        return this.request(`/service/cases/${id}/review/`, {
            method: 'POST',
            body: JSON.stringify(reviewData)
        });
    }

    static async getManagementStats() {
        return this.request('/management/stats/');
    }
}

window.ApiClient = ApiClient;

