// Receipt Downloader JavaScript functionality

class ReceiptApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupFormValidation();
        this.setupPhoneFormatting();
        this.setupLoadingStates();
        this.setupKeyboardShortcuts();
    }

    // Form validation and submission
    setupFormValidation() {
        const verificationForm = document.getElementById('verificationForm');
        if (verificationForm) {
            verificationForm.addEventListener('submit', (e) => {
                const phoneInput = document.getElementById('phone_number');
                const phone = phoneInput.value.trim();
                
                // Basic phone validation
                if (!this.isValidPhone(phone)) {
                    e.preventDefault();
                    this.showError('Please enter a valid phone number');
                    phoneInput.focus();
                    return;
                }
                
                // Store phone number for later use
                sessionStorage.setItem('verifiedPhone', phone);
                
                // Show loading state
                this.showLoadingModal('Verifying your information...');
            });
        }
    }

    // Phone number formatting and validation
    setupPhoneFormatting() {
        const phoneInput = document.getElementById('phone_number');
        if (phoneInput) {
            phoneInput.addEventListener('input', (e) => {
                // Remove all non-digits
                let value = e.target.value.replace(/\D/g, '');
                
                // Format as (XXX) XXX-XXXX for US numbers
                if (value.length >= 6) {
                    value = value.replace(/(\d{3})(\d{3})(\d{0,4})/, '($1) $2-$3');
                } else if (value.length >= 3) {
                    value = value.replace(/(\d{3})(\d{0,3})/, '($1) $2');
                }
                
                e.target.value = value;
            });

            // Allow only digits, spaces, parentheses, and dashes
            phoneInput.addEventListener('keypress', (e) => {
                const allowedChars = /[\d\s\(\)\-]/;
                if (!allowedChars.test(e.key) && !['Backspace', 'Delete', 'Tab', 'Enter'].includes(e.key)) {
                    e.preventDefault();
                }
            });
        }
    }

    // Loading states and modals
    setupLoadingStates() {
        // Download button loading
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.setButtonLoading(downloadBtn, true);
                
                // Reset after a delay (PDF generation time)
                setTimeout(() => {
                    this.setButtonLoading(downloadBtn, false);
                }, 3000);
            });
        }
    }

    // Keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Enter key on phone input
            if (e.key === 'Enter' && e.target.id === 'phone_number') {
                const form = document.getElementById('verificationForm');
                if (form) {
                    form.dispatchEvent(new Event('submit'));
                }
            }
            
            // Escape key to close modals
            if (e.key === 'Escape') {
                const openModals = document.querySelectorAll('.modal.show');
                openModals.forEach(modal => {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                });
            }
        });
    }

    // Utility functions
    isValidPhone(phone) {
        // Remove all non-digits
        const digitsOnly = phone.replace(/\D/g, '');
        
        // Check if it's a valid length (US: 10 digits, International: 7-15 digits)
        return digitsOnly.length >= 7 && digitsOnly.length <= 15;
    }

    showError(message) {
        // Create or update error alert
        let errorAlert = document.querySelector('.alert-danger');
        
        if (!errorAlert) {
            errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger alert-dismissible fade show';
            errorAlert.innerHTML = `
                <strong>Error:</strong> <span class="error-message">${message}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Insert after the form
            const form = document.getElementById('verificationForm');
            if (form) {
                form.parentNode.insertBefore(errorAlert, form.nextSibling);
            }
        } else {
            errorAlert.querySelector('.error-message').textContent = message;
        }
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (errorAlert) {
                const alert = bootstrap.Alert.getInstance(errorAlert);
                if (alert) alert.close();
            }
        }, 5000);
    }

    showLoadingModal(message = 'Loading...') {
        const loadingModal = document.getElementById('loadingModal');
        if (loadingModal) {
            const messageElement = loadingModal.querySelector('p');
            if (messageElement) {
                messageElement.textContent = message;
            }
            
            const modal = new bootstrap.Modal(loadingModal);
            modal.show();
        }
    }

    hideLoadingModal() {
        const loadingModal = document.getElementById('loadingModal');
        if (loadingModal) {
            const modal = bootstrap.Modal.getInstance(loadingModal);
            if (modal) modal.hide();
        }
    }

    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.classList.add('btn-loading');
            button.disabled = true;
            
            // Store original text
            if (!button.dataset.originalText) {
                button.dataset.originalText = button.innerHTML;
            }
            
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Processing...
            `;
        } else {
            button.classList.remove('btn-loading');
            button.disabled = false;
            
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
            }
        }
    }

    // Format currency for display
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    // Format date for display
    formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }

    // Copy receipt ID to clipboard
    copyReceiptId(receiptId) {
        navigator.clipboard.writeText(receiptId).then(() => {
            this.showSuccess('Receipt ID copied to clipboard');
        }).catch(() => {
            this.showError('Failed to copy receipt ID');
        });
    }

    showSuccess(message) {
        const successAlert = document.createElement('div');
        successAlert.className = 'alert alert-success alert-dismissible fade show';
        successAlert.innerHTML = `
            <i data-feather="check-circle" class="me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(successAlert);
        feather.replace();
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            const alert = bootstrap.Alert.getInstance(successAlert);
            if (alert) alert.close();
        }, 3000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ReceiptApp();
});

// Utility functions available globally
window.ReceiptUtils = {
    formatPhone: (phone) => {
        const digitsOnly = phone.replace(/\D/g, '');
        if (digitsOnly.length >= 6) {
            return digitsOnly.replace(/(\d{3})(\d{3})(\d{0,4})/, '($1) $2-$3');
        } else if (digitsOnly.length >= 3) {
            return digitsOnly.replace(/(\d{3})(\d{0,3})/, '($1) $2');
        }
        return digitsOnly;
    },
    
    cleanPhone: (phone) => {
        return phone.replace(/\D/g, '');
    }
};
