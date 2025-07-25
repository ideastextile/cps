// Custom Admin Panel JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeCustomAdmin();
});

function initializeCustomAdmin() {
    // Add loading states to buttons
    addButtonLoadingStates();
    
    // Enhance form interactions
    enhanceFormInteractions();
    
    // Add keyboard shortcuts
    addKeyboardShortcuts();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Add confirmation dialogs for delete actions
    addDeleteConfirmations();
    
    // Enhance table interactions
    enhanceTableInteractions();
}

function addButtonLoadingStates() {
    const buttons = document.querySelectorAll('.button, input[type="submit"], input[type="button"]');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.type === 'submit' || this.classList.contains('default')) {
                const originalText = this.textContent || this.value;
                const loadingText = 'Processing...';
                
                if (this.tagName === 'INPUT') {
                    this.value = loadingText;
                } else {
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + loadingText;
                }
                
                this.disabled = true;
                
                // Re-enable after 3 seconds (fallback)
                setTimeout(() => {
                    this.disabled = false;
                    if (this.tagName === 'INPUT') {
                        this.value = originalText;
                    } else {
                        this.textContent = originalText;
                    }
                }, 3000);
            }
        });
    });
}

function enhanceFormInteractions() {
    // Add focus effects to form fields
    const formFields = document.querySelectorAll('input, select, textarea');
    
    formFields.forEach(field => {
        field.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        field.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
        
        // Add validation feedback
        field.addEventListener('invalid', function() {
            this.classList.add('error');
            showFieldError(this, this.validationMessage);
        });
        
        field.addEventListener('input', function() {
            this.classList.remove('error');
            hideFieldError(this);
        });
    });
}

function showFieldError(field, message) {
    hideFieldError(field); // Remove existing error
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.cssText = `
        color: #ef4444;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    `;
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    field.parentElement.appendChild(errorDiv);
}

function hideFieldError(field) {
    const existingError = field.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveButton = document.querySelector('input[type="submit"][name="_save"]');
            if (saveButton) {
                saveButton.click();
            }
        }
        
        // Ctrl/Cmd + Enter to save and continue editing
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            const continueButton = document.querySelector('input[type="submit"][name="_continue"]');
            if (continueButton) {
                continueButton.click();
            }
        }
        
        // Escape to cancel/go back
        if (e.key === 'Escape') {
            const cancelLink = document.querySelector('.cancel-link, .deletelink');
            if (cancelLink) {
                window.location.href = cancelLink.href;
            }
        }
    });
}

function initializeTooltips() {
    // Add tooltips to buttons and links
    const elementsWithTooltips = document.querySelectorAll('[title]');
    
    elementsWithTooltips.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            showTooltip(e.target, e.target.getAttribute('title'));
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    hideTooltip(); // Remove existing tooltip
    
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #1f2937;
        color: white;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        font-size: 0.875rem;
        z-index: 1000;
        pointer-events: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
}

function hideTooltip() {
    const existingTooltip = document.querySelector('.custom-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }
}

function addDeleteConfirmations() {
    const deleteButtons = document.querySelectorAll('.deletelink, input[value*="Delete"]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const confirmDialog = createConfirmDialog(
                'Confirm Deletion',
                'Are you sure you want to delete this item? This action cannot be undone.',
                'Delete',
                'Cancel'
            );
            
            confirmDialog.onConfirm = () => {
                if (this.tagName === 'A') {
                    window.location.href = this.href;
                } else {
                    this.form.submit();
                }
            };
        });
    });
}

function createConfirmDialog(title, message, confirmText, cancelText) {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: white;
        border-radius: 12px;
        padding: 2rem;
        max-width: 400px;
        width: 90%;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    `;
    
    dialog.innerHTML = `
        <h3 style="margin: 0 0 1rem 0; color: #1f2937; font-size: 1.25rem; font-weight: 600;">
            <i class="fas fa-exclamation-triangle" style="color: #f59e0b; margin-right: 0.5rem;"></i>
            ${title}
        </h3>
        <p style="margin: 0 0 2rem 0; color: #6b7280; line-height: 1.6;">${message}</p>
        <div style="display: flex; gap: 1rem; justify-content: flex-end;">
            <button class="cancel-btn" style="
                background: #f3f4f6;
                color: #374151;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            ">${cancelText}</button>
            <button class="confirm-btn" style="
                background: #ef4444;
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            ">${confirmText}</button>
        </div>
    `;
    
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    
    const cancelBtn = dialog.querySelector('.cancel-btn');
    const confirmBtn = dialog.querySelector('.confirm-btn');
    
    const close = () => {
        document.body.removeChild(overlay);
    };
    
    cancelBtn.addEventListener('click', close);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close();
    });
    
    confirmBtn.addEventListener('click', () => {
        close();
        if (overlay.onConfirm) overlay.onConfirm();
    });
    
    // Add hover effects
    cancelBtn.addEventListener('mouseenter', () => {
        cancelBtn.style.background = '#e5e7eb';
    });
    cancelBtn.addEventListener('mouseleave', () => {
        cancelBtn.style.background = '#f3f4f6';
    });
    
    confirmBtn.addEventListener('mouseenter', () => {
        confirmBtn.style.background = '#dc2626';
    });
    confirmBtn.addEventListener('mouseleave', () => {
        confirmBtn.style.background = '#ef4444';
    });
    
    return overlay;
}

function enhanceTableInteractions() {
    const tables = document.querySelectorAll('.results table');
    
    tables.forEach(table => {
        // Add row hover effects
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.background = '#f8fafc';
                this.style.transform = 'scale(1.01)';
                this.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
                this.style.transition = 'all 0.2s ease';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.background = '';
                this.style.transform = '';
                this.style.boxShadow = '';
            });
        });
        
        // Add sortable column indicators
        const headers = table.querySelectorAll('th a');
        headers.forEach(header => {
            if (!header.querySelector('.sort-indicator')) {
                const indicator = document.createElement('i');
                indicator.className = 'fas fa-sort sort-indicator';
                indicator.style.marginLeft = '0.5rem';
                indicator.style.opacity = '0.5';
                header.appendChild(indicator);
            }
        });
    });
}

// Utility function to show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        font-weight: 500;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentElement) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .focused {
        transform: scale(1.02);
        transition: transform 0.2s ease;
    }
    
    .error {
        border-color: #ef4444 !important;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
    }
`;
document.head.appendChild(style);

