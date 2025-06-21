// edit_profile.js - JavaScript functionality for Edit Profile page

function openModal(id) {
  var modalElement = document.getElementById(id);
  if (modalElement) {
    modalElement.style.display = 'block';
    document.body.classList.add('modal-open');
  } else {
    console.error('Modal with id ' + id + ' not found.');
  }
}

function closeModal(id) {
  var modalElement = document.getElementById(id);
  if (modalElement) {
    modalElement.style.display = 'none';
    // Remove modal-open only if no other modals are open
    setTimeout(function() {
      if (!document.querySelector('.modal[style*="display: block"]')) {
        document.body.classList.remove('modal-open');
      }
    }, 100);
  } else {
    console.error('Modal with id ' + id + ' not found.');
  }
}

function saveAllProfileForms() {
  // Submit each form via AJAX and close the parent modal if present
  var formsToSubmit = [
    document.querySelector('#profile-modal form'),
    document.querySelector('#places-modal .add-place-form'),
    document.querySelector('#achievements-modal .add-achievement-form'),
    document.querySelector('#quotes-modal .add-quote-form'),
    document.querySelector('#add-content-modal .add-content-form')
  ];
  var ajaxCalls = [];
  formsToSubmit.forEach(function(form) {
    if (form) {
      var $form = $(form);
      var formData = new FormData(form);
      var ajaxCall = $.ajax({
        url: $form.attr('action') || window.location.href,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {'X-CSRFToken': $form.find('input[name="csrfmiddlewaretoken"]').val()}
      });
      ajaxCalls.push(ajaxCall);
    }
  });
  $.when.apply($, ajaxCalls).done(function() {
    // Try to close the modal in both parent and current window
    var closed = false;
    try {
      if (window.parent && window.parent.document) {
        var parentModal = window.parent.document.getElementById('editProfileModal');
        if (parentModal) {
          parentModal.style.display = 'none';
          closed = true;
        }
      }
    } catch (e) { console.error('Error closing parent modal:', e); }
    var mainModal = document.getElementById('editProfileModal');
    if (mainModal) {
      mainModal.style.display = 'none';
      closed = true;
    }
    if (!closed) {
      console.warn('No editProfileModal found to close.');
    }
  });
}

// Success toast notification function
function showSuccessToast(message) {
  var toastId = 'success-toast-' + Date.now();
  var defaultMessage = 'Operation completed successfully!';
  var displayMessage = message || defaultMessage;
  
  // Remove any existing toasts first
  $('.success-toast').remove();
  
  // Create and show the toast
  $('body').append('<div id="' + toastId + '" class="success-toast" style="position:fixed;top:32px;left:50%;transform:translateX(-50%);background:#28a745;color:#fff;padding:16px 32px;border-radius:8px;z-index:2100;font-size:1.1em;box-shadow:0 4px 12px rgba(0,0,0,0.15);font-weight:500;">' + displayMessage + '</div>');
  
  // Auto-hide after 3 seconds
  setTimeout(function() { 
    $('#' + toastId).fadeOut(400, function() { 
      $(this).remove(); 
    }); 
  }, 3000);
}

// Make it globally available
window.showSuccessToast = showSuccessToast;

// Function to handle interest form submission manually
function submitInterestForm() {
    console.log('submitInterestForm called');
    
    // Perform client-side validation first
    const validation = validateUserProfileInterests();
    if (!validation.valid) {
        showUserProfileInterestError(validation.error);
        return; // Don't submit if validation fails
    }
    
    var $form = $('#update-user-interests-form');
    var formData = $form.serialize();
    console.log('Form data serialized:', formData);

    $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: formData,
        success: function(data) {
            console.log('AJAX success - received data:', data);
            if (data.status === 'success') {
                console.log('Success status confirmed, processing...');
                // Update the interests display
                var newInterestsListHtml = '';
                if (data.interests && data.interests.length > 0) {
                    data.interests.forEach(function(interest) {
                        newInterestsListHtml += '<li>' + interest + '</li>';
                    });
                } else {
                    newInterestsListHtml = '<li>No interests set yet.</li>';
                }
                $('#current-interests-list-profile').html(newInterestsListHtml);
                
                // Hide form and show display
                hideUserProfileInterestForm();
                
                // Close the interests modal and show success
                console.log('About to close modal and show toast...');
                closeModal('update-user-interests-modal');
                
                // Update interests display in parent page if it exists
                try {
                    if (window.parent && window.parent.document) {
                        var parentInterestsContainer = window.parent.document.querySelector('.interests-display .grid-container');
                        if (parentInterestsContainer && data.interests) {
                            var newInterestsHtml = '';
                            data.interests.forEach(function(interest) {
                                newInterestsHtml += '<div class="grid-item">' + interest + '</div>';
                            });
                            if (newInterestsHtml === '') {
                                newInterestsHtml = '<div class="grid-item">No interests set yet.</div>';
                            }
                            parentInterestsContainer.innerHTML = newInterestsHtml;
                        }
                    }
                } catch (e) {
                    console.log('Could not update parent interests display:', e);
                }
                console.log('Success handler completed');
                
            } else {
                console.log('Error in response:', data);
                let errorMsg = data.message || 'Error updating interests.';
                if (data.errors) {
                    for (const field in data.errors) {
                        errorMsg += '\\n- ' + field + ': ' + data.errors[field].join(', ');
                    }
                }
                alert(errorMsg);
            }
        },
        error: function(xhr) {
            console.log('AJAX error occurred:', xhr);
            console.error("AJAX error:", xhr.responseText);
            
            // Try to parse JSON error response
            try {
                const errorData = JSON.parse(xhr.responseText);
                console.log('AJAX error:', errorData);
                
                if (errorData.status === 'error') {
                    let errorMsg = errorData.message || 'Error updating interests.';
                    if (errorData.errors) {
                        // Display field-specific errors
                        for (const field in errorData.errors) {
                            if (field === '__all__') {
                                // General form errors
                                errorMsg = errorData.errors[field].join(', ');
                            } else {
                                errorMsg += '\n- ' + field + ': ' + errorData.errors[field].join(', ');
                            }
                        }
                    }
                    showUserProfileInterestError(errorMsg);
                } else {
                    showUserProfileInterestError('An unexpected error occurred. Please try again.');
                }
            } catch (e) {
                console.error('Could not parse error response:', e);
                showUserProfileInterestError('An error occurred: ' + xhr.status + ' ' + xhr.statusText);
            }
        }
    });
}

// Make it globally available
window.submitInterestForm = submitInterestForm;

// Profile picture preview functionality
function initializeProfilePicturePreview() {
    var fileInput = document.querySelector('input[name="profile_picture"]');
    var img = document.getElementById('profile-picture-img');
    if (fileInput && img) {
        fileInput.addEventListener('change', function(e) {
            if (fileInput.files && fileInput.files[0]) {
                var reader = new FileReader();
                reader.onload = function(ev) {
                    img.src = ev.target.result;
                    img.style.display = 'block';
                };
                reader.readAsDataURL(fileInput.files[0]);
            }
        });
    }
}

// Make openModal function globally available
window.openModal = openModal;

// Window click handler for modal closing
window.onclick = function(event) {
  const modals = document.querySelectorAll('.modal');
  modals.forEach(function(modal) {
    if (event.target === modal) {
      // Check if the modal being closed is the main options container
      // If so, and it's inside an iframe, try to close the parent modal
      if (modal.id === 'profile-options-content-box' && window.parent && window.parent.document.getElementById('editProfileModal')) {
        try {
          var parentModal = window.parent.document.getElementById('editProfileModal');
          if (parentModal) {
            parentModal.style.display = 'none';
          }
        } catch (e) {
          console.error('Error closing parent modal from window.onclick:', e);
        }
      } else {
         modal.style.display = 'none';
      }
    }
  });
};

// Load initial interests into the form when editing starts (legacy function for compatibility)
function loadCurrentInterestsIntoForm() {
    // This function is now handled by the new interests.js file
    if (typeof loadCurrentUserInterestsIntoForm === 'function') {
        loadCurrentUserInterestsIntoForm();
    }
}

// Legacy function for compatibility
function initializeProfileInterestAutocompletes() {
    // This function is now handled by the new interests.js file  
    if (typeof initializeUserProfileInterestAutocomplete === 'function') {
        initializeUserProfileInterestAutocomplete();
    }
}

// Profile success message function
function showProfileSuccessMessage(message) {
  if ($('#profile-success-msg').length === 0) {
    const displayMessage = message || 'Profile updated successfully!';
    $('body').append(`<div id="profile-success-msg" style="position:fixed;top:32px;left:50%;transform:translateX(-50%);background:#4fd18b;color:#fff;padding:18px 32px;border-radius:8px;z-index:2000;font-size:1.2em;box-shadow:0 2px 12px rgba(0,0,0,0.12);">${displayMessage}</div>`);
    setTimeout(function() { $('#profile-success-msg').fadeOut(400, function() { $(this).remove(); }); }, 2500);
  }
}

// jQuery document ready function
$(document).ready(function() {
    console.log('Edit profile page JavaScript loaded successfully');
    console.log('jQuery version:', $.fn.jquery);
    
    // Check if the interest form exists
    var $interestForm = $('#update-user-interests-form');
    console.log('Interest form exists:', $interestForm.length > 0);
    if ($interestForm.length > 0) {
        console.log('Interest form found, attaching submit handler...');
    }
    
    // AJAX for profile form
    $('#profile-modal form').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var formData = new FormData(this);
        $.ajax({
            url: $form.attr('action') || window.location.href,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {'X-CSRFToken': $form.find('input[name="csrfmiddlewaretoken"]').val()},
            success: function(data) {
                closeModal('profile-modal');
                // Check if response is JSON and has a message (from our updated view)
                if (data && data.message) {
                    showProfileSuccessMessage(data.message);
                } else {
                    showProfileSuccessMessage(); // Original generic message
                }
            },
            error: function(xhr) {
                // Try to parse error from backend if available
                let errorMsg = 'Error saving profile.';
                if (xhr.responseJSON && xhr.responseJSON.errors) {
                    // You might want to format this better if there are multiple errors
                    errorMsg = "Error: " + JSON.stringify(xhr.responseJSON.errors);
                } else if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                }
                alert(errorMsg);
            }
        });
    });

    // AJAX for places form
    $('#places-modal form').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var formData = new FormData(this);
        $.ajax({
            url: $form.attr('action') || window.location.href,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {'X-CSRFToken': $form.find('input[name="csrfmiddlewaretoken"]').val()},
            success: function(data) {
                closeModal('places-modal');
            },
            error: function() {
                alert('Error saving place.');
            }
        });
    });

    // AJAX for achievements form
    $('#achievements-modal form').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var formData = new FormData(this);
        $.ajax({
            url: $form.attr('action') || window.location.href,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {'X-CSRFToken': $form.find('input[name="csrfmiddlewaretoken"]').val()},
            success: function(data) {
                closeModal('achievements-modal');
            },
            error: function() {
                alert('Error saving achievement.');
            }
        });
    });

    // AJAX for quotes form
    $('#quotes-modal form').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var formData = new FormData(this);
        $.ajax({
            url: $form.attr('action') || window.location.href,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {'X-CSRFToken': $form.find('input[name="csrfmiddlewaretoken"]').val()},
            success: function(data) {
                closeModal('quotes-modal');
            },
            error: function() {
                alert('Error saving quote.');
            }
        });
    });

    // AJAX for add content form
    $('#add-content-modal form').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var formData = new FormData(this);
        $.ajax({
            url: $form.attr('action') || window.location.href,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {'X-CSRFToken': $form.find('input[name="csrfmiddlewaretoken"]').val()},
            success: function(data) {
                closeModal('add-content-modal');
            },
            error: function() {
                alert('Error saving content.');
            }
        });
    });

    // Clean AJAX handler for interest updates
    $('#update-user-interests-form').on('submit', function(e) {
        console.log('Form submission intercepted by AJAX handler');
        e.preventDefault();
        e.stopPropagation();
        var $form = $(this);
        var formData = $form.serialize();

        $.ajax({
            url: $form.attr('action'),
            type: 'POST',
            data: formData,
            success: function(data) {
                if (data.status === 'success') {
                    // Update the interests display
                    var newInterestsListHtml = '';
                    if (data.interests && data.interests.length > 0) {
                        data.interests.forEach(function(interest) {
                            newInterestsListHtml += '<li>' + interest + '</li>';
                        });
                    } else {
                        newInterestsListHtml = '<li>No interests set yet.</li>';
                    }
                    $('#current-interests-list-profile').html(newInterestsListHtml);
                    
                    // Hide form and show display
                    hideUserProfileInterestForm();
                    
                    // Close the interests modal and show success
                    closeModal('update-user-interests-modal');
                    
                    // Update interests display in parent page if it exists
                    try {
                        if (window.parent && window.parent.document) {
                            var parentInterestsContainer = window.parent.document.querySelector('.interests-display .grid-container');
                            if (parentInterestsContainer && data.interests) {
                                var newInterestsHtml = '';
                                data.interests.forEach(function(interest) {
                                    newInterestsHtml += '<div class="grid-item">' + interest + '</div>';
                                });
                                if (newInterestsHtml === '') {
                                    newInterestsHtml = '<div class="grid-item">No interests set yet.</div>';
                                }
                                parentInterestsContainer.innerHTML = newInterestsHtml;
                            }
                        }
                    } catch (e) {
                        console.log('Could not update parent interests display:', e);
                    }
                    console.log('Success handler completed');
                    
                } else {
                    console.log('Error in response:', data);
                    let errorMsg = data.message || 'Error updating interests.';
                    if (data.errors) {
                        for (const field in data.errors) {
                            errorMsg += '\\n- ' + field + ': ' + data.errors[field].join(', ');
                        }
                    }
                    alert(errorMsg);
                }
            },
            error: function(xhr) {
                alert('An error occurred: ' + xhr.status + ' ' + xhr.statusText);
                console.error("AJAX error:", xhr.responseText);
            }
        });
    });

    // Initialize profile picture preview
    initializeProfilePicturePreview();
});
