// Quick review functionality for reports
function quickReview(reportId, action) {
    const actionText = action === 'approved' ? 'approve' : 'dismiss';
    
    if (confirm(`Are you sure you want to ${actionText} this report?`)) {
        // Create a form and submit it
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/registerandlogin/report/${reportId}/change/`;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add approval status field
        const statusInput = document.createElement('input');
        statusInput.type = 'hidden';
        statusInput.name = 'approval_status';
        statusInput.value = action;
        form.appendChild(statusInput);
        
        // Add is_reviewed field
        const reviewedInput = document.createElement('input');
        reviewedInput.type = 'hidden';
        reviewedInput.name = 'is_reviewed';
        reviewedInput.value = 'on';
        form.appendChild(reviewedInput);
        
        // Add save button
        const saveInput = document.createElement('input');
        saveInput.type = 'hidden';
        saveInput.name = '_save';
        saveInput.value = 'Save';
        form.appendChild(saveInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

// Add some styling to make the admin interface more user-friendly
document.addEventListener('DOMContentLoaded', function() {
    // Add tooltips to action buttons
    const actionButtons = document.querySelectorAll('button[onclick^="quickReview"]');
    actionButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Highlight unreviewed reports
    const unreviewedRows = document.querySelectorAll('tr:has(.field-review_status_display:contains("Needs Review"))');
    unreviewedRows.forEach(row => {
        row.style.backgroundColor = '#fff3cd';
        row.style.borderLeft = '4px solid #ffc107';
    });
});
