/**
 * Doctor Appointment Scheduling Modal & Interactivity
 */
class AppointmentModalManager {
    static init() {
        this.modalEl = document.getElementById('appointmentBookingModal');
        this.formEl = document.getElementById('modalAppointmentForm');
        this.doctorSelectEl = document.getElementById('modalDoctorSelect');
        this.departmentSelectEl = document.getElementById('modalDepartmentSelect');
        this.timeSlotSelectEl = document.getElementById('modalTimeSlot');
        this.dateInputEl = document.getElementById('modalAppointmentDate');
        this.reasonInputEl = document.getElementById('modalReason');
        this.doctorPreviewCard = document.getElementById('modalDoctorPreview');
        
        this.doctorsList = [];
        this.bindEvents();
        this.loadDoctors();
    }

    static bindEvents() {
        // Trigger buttons with data-action="book-doctor"
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action="book-doctor"]');
            if (btn) {
                const doctorId = btn.getAttribute('data-doctor-id');
                const doctorName = btn.getAttribute('data-doctor-name');
                const department = btn.getAttribute('data-department');
                this.openModal(doctorId, doctorName, department);
            }
        });

        if (this.departmentSelectEl) {
            this.departmentSelectEl.addEventListener('change', () => {
                this.filterDoctorsByDepartment(this.departmentSelectEl.value);
            });
        }

        if (this.doctorSelectEl) {
            this.doctorSelectEl.addEventListener('change', () => {
                this.updateDoctorPreview(this.doctorSelectEl.value);
            });
        }

        if (this.formEl) {
            this.formEl.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleBookingSubmit();
            });
        }
    }

    static async loadDoctors() {
        try {
            const doctors = await ApiClient.getDoctors();
            this.doctorsList = doctors;
            this.populateDoctorOptions(doctors);
        } catch (err) {
            console.error('Error loading doctors for modal:', err);
        }
    }

    static populateDoctorOptions(doctors) {
        if (!this.doctorSelectEl) return;
        this.doctorSelectEl.innerHTML = '<option value="">-- Choose Specialist Doctor --</option>';
        doctors.forEach(doc => {
            const opt = document.createElement('option');
            opt.value = doc.id;
            opt.textContent = `${doc.name} - ${doc.specialty} (${doc.department})`;
            opt.dataset.doctor = JSON.stringify(doc);
            this.doctorSelectEl.appendChild(opt);
        });
    }

    static filterDoctorsByDepartment(department) {
        if (!department) {
            this.populateDoctorOptions(this.doctorsList);
            return;
        }
        const filtered = this.doctorsList.filter(d => d.department === department);
        this.populateDoctorOptions(filtered);
    }

    static updateDoctorPreview(doctorId) {
        if (!this.doctorPreviewCard) return;
        const doctor = this.doctorsList.find(d => d.id == doctorId);
        if (!doctor) {
            this.doctorPreviewCard.classList.add('d-none');
            return;
        }

        this.doctorPreviewCard.classList.remove('d-none');
        this.doctorPreviewCard.innerHTML = `
            <div class="d-flex align-items-center gap-3 p-3 bg-light rounded-3">
                <img src="${doctor.avatar_url}" alt="${doctor.name}" class="rounded-circle" style="width: 54px; height: 54px; object-fit: cover;">
                <div class="flex-grow-1">
                    <h6 class="mb-0 fw-bold">${doctor.name}</h6>
                    <span class="badge bg-primary-subtle text-primary mb-1">${doctor.specialty}</span>
                    <div class="small text-muted">${doctor.qualification} • ⭐ ${doctor.rating} (${doctor.experience_years} yrs exp)</div>
                </div>
            </div>
        `;
    }

    static openModal(doctorId = null, doctorName = null, department = null) {
        if (!this.modalEl) return;
        
        // Set default minimum date to tomorrow
        if (this.dateInputEl) {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            this.dateInputEl.min = tomorrow.toISOString().split('T')[0];
            if (!this.dateInputEl.value) {
                this.dateInputEl.value = tomorrow.toISOString().split('T')[0];
            }
        }

        if (department && this.departmentSelectEl) {
            this.departmentSelectEl.value = department;
            this.filterDoctorsByDepartment(department);
        }

        if (doctorId && this.doctorSelectEl) {
            this.doctorSelectEl.value = doctorId;
            this.updateDoctorPreview(doctorId);
        }

        // Bootstrap modal open
        if (window.bootstrap && window.bootstrap.Modal) {
            const modalInstance = window.bootstrap.Modal.getOrCreateInstance(this.modalEl);
            modalInstance.show();
        }
    }

    static async handleBookingSubmit() {
        const doctorId = this.doctorSelectEl.value;
        const appointmentDate = this.dateInputEl.value;
        const timeSlot = this.timeSlotSelectEl.value;
        const reason = this.reasonInputEl?.value || 'Consultation assessment';

        if (!doctorId || !appointmentDate || !timeSlot) {
            alert('Please select a doctor, appointment date, and time slot.');
            return;
        }

        const submitBtn = this.formEl.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Confirming Booking...`;

        try {
            const result = await ApiClient.bookAppointment({
                doctor: doctorId,
                appointment_date: appointmentDate,
                time_slot: timeSlot,
                reason: reason
            });

            // Close modal
            if (window.bootstrap && window.bootstrap.Modal) {
                const modalInstance = window.bootstrap.Modal.getInstance(this.modalEl);
                if (modalInstance) modalInstance.hide();
            }

            // Dispatch global event
            window.dispatchEvent(new CustomEvent('appointment:booked', { detail: result }));

            // Display toast or notification
            alert(`🎉 Success! Medical consultation booked with ${result.doctor_name} on ${result.appointment_date} at ${result.time_slot}. Confirmation email dispatched!`);
            
            // Reload or refresh appointments view if present
            if (window.location.pathname.includes('appointment') || window.location.pathname.includes('dashboard')) {
                window.location.reload();
            }
        } catch (err) {
            alert(`Booking Error: ${err.message || 'Could not schedule appointment.'}`);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    AppointmentModalManager.init();
});

window.AppointmentModalManager = AppointmentModalManager;

