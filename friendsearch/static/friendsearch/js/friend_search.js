// ==================== //
// Main Initialization
// ==================== //
$(document).ready(function() {
    // Only initialize friendsearch functionality if we're on a friendsearch page
    if (document.getElementById('allowed-words-json')) {
        // Initialize all components
        initializeDatalistAutocomplete('.autocomplete-container input'); // Updated call
        // setupEventHandlers();
        
        // Debugging
        // logWordlistData();
    };
});


// ==================== //
// Core Functions
// ==================== //

/**
 * Toggle between interest display and edit form
 * @param {boolean} showForm - Whether to show the form
 */
function toggleEdit(showForm) {
    const $interestDisplay = $('#interest-display');
    const $interestForm = $('#interest-form');
    console.log('[DEBUG] toggleEdit called. showForm:', showForm, 'interestDisplay:', $interestDisplay.length, 'interestForm:', $interestForm.length);
    if (showForm) {
        $interestDisplay.hide();
        $interestForm.show();        // Reinitialize datalist autocomplete after form is visible
        setTimeout(() => {
            console.log('[DEBUG] Calling initializeDatalistAutocomplete from toggleEdit for #interest-form');
            if (document.getElementById('allowed-words-json')) {
                initializeDatalistAutocomplete('#interest-form .autocomplete-container input'); // Updated call
            }
        }, 50);
    } else {
        $interestDisplay.show();
        $interestForm.hide();
    }
}
window.toggleEdit = toggleEdit;

/**
 * Get user's current location
 */
function getLocation() {
    if (!navigator.geolocation) {
        showAlert("Geolocation is not supported by your browser.", 'error');
        return;
    }

    const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    };

    navigator.geolocation.getCurrentPosition(
        position => {
            $('#latitude').val(position.coords.latitude);
            $('#longitude').val(position.coords.longitude);
            $('#locationForm').trigger('submit');
        },
        error => {
            const errorMessages = {
                1: 'Permission denied', 
                2: 'Position unavailable',
                3: 'Request timeout'
            };
            showAlert(`⚠️ Could not retrieve your location: ${errorMessages[error.code] || error.message}`, 'error');
        },
        options
    );
}

// ================================ //
// Datalist Autocomplete System
// ================================ //

/**
 * Initialize datalist-based autocomplete for specified input fields.
 * @param {string} selector - CSS selector for the input fields.
 */
function initializeDatalistAutocomplete(selector) {
    const wordlistScriptTag = document.getElementById('allowed-words-json');
    if (!wordlistScriptTag) {
        console.error('Wordlist JSON script tag ("allowed-words-json") not found.');
        return;
    }

    let availableWords = [];
    try {
        availableWords = JSON.parse(wordlistScriptTag.textContent);
        if (!Array.isArray(availableWords)) {
            console.error('Wordlist data is not an array:', availableWords);
            availableWords = []; // Fallback to empty array
        }
    } catch (e) {
        console.error('Failed to parse wordlist JSON:', e);
        return; // Cannot proceed without wordlist
    }

    // console.log(`Initializing datalist for selector: "${selector}" with ${availableWords.length} words.`);

    document.querySelectorAll(selector).forEach((inputField, index) => {
        if (!inputField) {
            // console.warn(`Input field not found for selector "${selector}" at index ${index}`);
            return;
        }
        
        // Ensure each input has a unique ID if it doesn't already
        // Django forms usually provide IDs like "id_formprefix-fieldname"
        if (!inputField.id) {
            // Create a reasonably unique ID if one is missing
            inputField.id = `interest-input-${Math.random().toString(36).substr(2, 9)}-${index}`;
            // console.log(`Assigned new ID to input: ${inputField.id}`);
        }
        const datalistId = `datalist-for-${inputField.id}`;

        // Remove existing datalist for this input to prevent duplicates if re-initialized
        const existingDatalist = document.getElementById(datalistId);
        if (existingDatalist) {
            existingDatalist.remove();
        }

        inputField.setAttribute('list', datalistId);
        inputField.setAttribute('autocomplete', 'off'); // Recommended for custom datalists

        const datalist = document.createElement('datalist');
        datalist.id = datalistId;

        availableWords.forEach(word => {
            const option = document.createElement('option');
            option.value = String(word); // Ensure value is a string
            datalist.appendChild(option);
        });

        // Insert the datalist into the DOM.
        // It's conventional to place it right after the input or as a child of its container.
        if (inputField.parentNode) {
            // Insert after the input field within the same parent.
            inputField.parentNode.insertBefore(datalist, inputField.nextSibling);
        } else {
            // Fallback: append to body, though less ideal.
            // console.warn(`Input field with ID ${inputField.id} has no parent. Appending datalist to body.`);
            document.body.appendChild(datalist);
        }
        // console.log(`Datalist "${datalistId}" initialized and attached for input "#${inputField.id}".`);
    });
}


// ==================== //
// Utility Functions
// ==================== //

/**
 * Display a custom alert message
 * @param {string} message - The message to display
 * @param {string} type - \'success\', \'error\', or \'info\'
 */
function showAlert(message, type = 'info') {
    // Basic alert for now, can be replaced with a more sophisticated UI element
    alert(`${type.toUpperCase()}: ${message}`);
}

/**
 * Validate friendsearch interest inputs before submission
 * Checks for duplicates and invalid words
 */
function validateFriendSearchInterests() {
    const interests = [];
    const wordlistScriptTag = document.getElementById('allowed-words-json');
    let validWords = [];
    
    // Get wordlist for validation
    if (wordlistScriptTag) {
        try {
            validWords = JSON.parse(wordlistScriptTag.textContent);
        } catch (e) {
            console.error('Error parsing wordlist for validation:', e);
            return { valid: false, error: 'Could not validate interests. Please try again.' };
        }
    } else {
        return { valid: false, error: 'Could not validate interests. Please try again.' };
    }
    
    // Convert to lowercase for case-insensitive comparison
    const validWordsLower = validWords.map(word => word.toLowerCase());
      // Collect all interest values from the form
    for (let i = 1; i <= 3; i++) {
        // Try prefixed fields first (for Django forms with prefix), then non-prefixed
        let input = document.querySelector(`#interest-form input[name="update-interest_${i}"]`);
        if (!input) {
            input = document.querySelector(`#interest-form input[name="interest_${i}"]`);
        }
        if (input && input.value.trim()) {
            interests.push(input.value.trim());
        }
    }
    
    // Check if at least one interest is provided
    if (interests.length === 0) {
        return { valid: false, error: 'Please select at least one interest.' };
    }
    
    // Check for duplicates
    const uniqueInterests = [...new Set(interests.map(interest => interest.toLowerCase()))];
    if (uniqueInterests.length !== interests.length) {
        return { valid: false, error: 'You cannot select the same interest multiple times. Please choose different interests.' };
    }
    
    // Check if all interests are valid (in wordlist)
    for (const interest of interests) {
        if (!validWordsLower.includes(interest.toLowerCase())) {
            return { valid: false, error: `"${interest}" is not a valid interest. Please select from the list.` };
        }
    }
    
    return { valid: true };
}

/**
 * Show error message to user in friendsearch
 */
function showFriendSearchInterestError(message) {
    // Remove any existing error messages
    const existingError = document.querySelector('.friendsearch-interest-error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and show new error message
    const form = document.getElementById('interest-form');
    if (form) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'friendsearch-interest-error-message';
        errorDiv.style.cssText = 'color: #d9534f; background: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; margin: 10px 0; font-size: 14px;';
        errorDiv.textContent = message;
        
        // Insert at the top of the form
        form.insertBefore(errorDiv, form.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
}

// Make validation functions globally available
window.validateFriendSearchInterests = validateFriendSearchInterests;
window.showFriendSearchInterestError = showFriendSearchInterestError;

// ==================== //
// AJAX Form Submission for Interests
// ==================== //
function submitFriendSearchInterestForm() {
    console.log('submitFriendSearchInterestForm called');
    
    // Perform client-side validation first
    const validation = validateFriendSearchInterests();
    if (!validation.valid) {
        showFriendSearchInterestError(validation.error);
        return; // Don't submit if validation fails
    }
    
    var $form = $('#interest-form');
    var formData = $form.serialize();
    console.log('FriendSearch form data serialized:', formData);

    $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(data) {
            console.log('FriendSearch AJAX success - received data:', data);
            if (data.status === 'success') {
                console.log('Success status confirmed, processing...');                // Update the interests display
                var interestDisplayDiv = $('#interest-display');
                if (data.interests && data.interests.length > 0) {
                    var newInterestsHtml = '<ul class="interests-list">';
                    data.interests.forEach(function(interest) {
                        newInterestsHtml += '<li>' + interest + '</li>';
                    });
                    newInterestsHtml += '</ul><button type="button" onclick="toggleEdit(true)">✏️ Edit Interests</button>';
                } else {
                    var newInterestsHtml = '<p>No interests set yet.</p><button type="button" onclick="toggleEdit(true)">✏️ Edit Interests</button>';
                }
                interestDisplayDiv.html(newInterestsHtml);
                
                // Hide form and show display
                toggleEdit(false);
                
                console.log('FriendSearch success handler completed');
                
            } else {
                console.log('Error in response:', data);
                let errorMsg = data.message || 'Error updating interests.';
                if (data.errors) {
                    for (const field in data.errors) {
                        if (field === '__all__') {
                            errorMsg = data.errors[field].join(', ');
                        } else {
                            errorMsg += '\n- ' + field + ': ' + data.errors[field].join(', ');
                        }
                    }
                }
                showFriendSearchInterestError(errorMsg);
            }
        },
        error: function(xhr) {
            console.log('FriendSearch AJAX error occurred:', xhr);
            console.error("FriendSearch AJAX error:", xhr.responseText);
            
            // Try to parse JSON error response
            try {
                const errorData = JSON.parse(xhr.responseText);
                console.log('FriendSearch AJAX error:', errorData);
                
                if (errorData.status === 'error') {
                    let errorMsg = errorData.message || 'Error updating interests.';
                    if (errorData.errors) {
                        for (const field in errorData.errors) {
                            if (field === '__all__') {
                                errorMsg = errorData.errors[field].join(', ');
                            } else {
                                errorMsg += '\n- ' + field + ': ' + errorData.errors[field].join(', ');
                            }
                        }
                    }
                    showFriendSearchInterestError(errorMsg);
                } else {
                    showFriendSearchInterestError('An unexpected error occurred. Please try again.');
                }
            } catch (e) {
                console.error('Could not parse error response:', e);
                showFriendSearchInterestError('An error occurred: ' + xhr.status + ' ' + xhr.statusText);
            }
        }
    });
}

// Make function globally available
window.submitFriendSearchInterestForm = submitFriendSearchInterestForm;

// ==================== //
// Event Handlers (Example Structure)
// ==================== //
/*
function setupEventHandlers() {
    // Example: Handling form submissions via AJAX
    $('#some-form').on('submit', function(event) {
        event.preventDefault();
        // AJAX call logic here
    });

    // Example: Click event for a button
    $('#some-button').on('click', function() {
        // Action logic here
    });
}
*/

// ==================== //
// Debugging Functions (Optional)
// ==================== //
/*
function logWordlistData() {
    const wordlistScriptTag = document.getElementById('allowed-words-json');
    if (wordlistScriptTag) {
        try {
            const words = JSON.parse(wordlistScriptTag.textContent);
            console.log("Parsed wordlist data:", words);
        } catch (e) {
            console.error("Error parsing wordlist data for logging:", e);
        }
    } else {
        console.warn("Wordlist script tag not found for logging.");
    }
}
*/

// Ensure to remove or comment out any old Typeahead/Bloodhound specific code
// that might have been below or intermingled if this edit is partial.
// The provided code replaces the relevant sections.

// Add CSS for validation tooltips
$('head').append(`
    <style>
        .validation-tooltip {
            position: absolute;
            background: #ffebee;
            color: #c62828;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-top: 5px;
            z-index: 1001;
            display: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .tt-dropdown-menu {
            z-index: 1000 !important;
        }
    </style>
`);
