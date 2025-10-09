// Admin panel specific logic
document.addEventListener('DOMContentLoaded', () => {
    // Admin-specific initialization
    initializeAdmin();
});

function initializeAdmin() {
    console.log('Admin panel initialized');

    // Additional admin-specific setup can go here
    // For now, the main logic is in the admin.html Alpine component
}

// Admin-specific utility functions
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

function showConfirmDialog(title, message, onConfirm) {
    // Simple confirmation dialog - can be enhanced with a modal
    if (confirm(`${title}\n\n${message}`)) {
        onConfirm();
    }
}

// Export admin utilities
window.adminUtils = {
    confirmDelete,
    showConfirmDialog
};