// ==================== //
// UserProfile Interest Management
// Mirrors friendsearch functionality but for userprofile
// ==================== //

$(document).ready(function() {
    // Only initialize if we're on a userprofile page with interest editing
    if (document.getElementById('update-user-interests-form')) {
        initializeUserProfileInterestAutocomplete();
    }
});

/**
 * Initialize autocomplete for userprofile interest inputs
 * Uses the same wordlist but different selectors than friendsearch
 */
function initializeUserProfileInterestAutocomplete() {
    // Try to get wordlist from embedded script tag first
    const wordlistScript = document.getElementById('wordlist-data');
    if (wordlistScript) {
        try {
            const words = JSON.parse(wordlistScript.textContent);
            console.log('Using embedded wordlist:', words.length, 'words');
            setupUserProfileDatalistOptions(words);
            return;
        } catch (e) {
            console.error('Error parsing embedded wordlist:', e);
        }
    }
    
    // Fallback: Fetch wordlist from API
    fetch('/userprofile/api/get_word_list/')
        .then(response => {
            console.log('API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(words => {
            console.log('Wordlist fetched successfully:', words.length, 'words');
            setupUserProfileDatalistOptions(words);
        })
        .catch(error => {
            console.error('Failed to fetch wordlist for userprofile interests:', error);
            console.error('Make sure you have interests autocomplete working by typing the full interest name');
        });
}

/**
 * Setup datalist options for userprofile interest inputs
 */
function setupUserProfileDatalistOptions(wordlist) {
    const interestInputs = document.querySelectorAll('.interest-input-profile');
    
    interestInputs.forEach(input => {
        const datalistId = input.getAttribute('list');
        const datalist = document.getElementById(datalistId);
        
        if (datalist) {
            // Clear existing options
            datalist.innerHTML = '';
            
            // Add all wordlist options
            wordlist.forEach(word => {
                const option = document.createElement('option');
                option.value = word;
                datalist.appendChild(option);
            });
        }
    });
    
    console.log('UserProfile interest autocomplete initialized with', wordlist.length, 'words');
}

/**
 * Load current user interests into the form when editing starts
 */
function loadCurrentUserInterestsIntoForm() {
    // Get interests from the template context
    const userInterestsRaw = document.querySelector('#user-interests-data');
    let userInterests = [];
    
    if (userInterestsRaw) {
        try {
            userInterests = JSON.parse(userInterestsRaw.textContent);
        } catch (e) {
            console.error("Error parsing user interests data:", e);
            userInterests = [];
        }
    }    // Populate the form fields
    for (let i = 1; i <= 3; i++) {
        const input = document.getElementById(`id_interest_${i}`);
        if (input) {
            input.value = userInterests[i-1] || '';
        }
    }
    
    console.log('Loaded current interests into form:', userInterests);
}

/**
 * Show the interest editing form and hide the display
 */
function showUserProfileInterestForm() {
    const display = document.getElementById('user-interest-display');
    const form = document.getElementById('update-user-interests-form');
    
    if (display && form) {
        display.style.display = 'none';
        form.style.display = 'block';
        loadCurrentUserInterestsIntoForm();
    }
}

/**
 * Hide the interest editing form and show the display
 */
function hideUserProfileInterestForm() {
    const display = document.getElementById('user-interest-display');
    const form = document.getElementById('update-user-interests-form');
    
    if (display && form) {
        form.style.display = 'none';
        display.style.display = 'block';
    }
}

/**
 * Validate interest inputs before submission
 * Checks for duplicates and invalid words
 */
function validateUserProfileInterests() {
    const interests = [];
    const wordlistScript = document.getElementById('wordlist-data');
    let validWords = [];
    
    // Get wordlist for validation
    if (wordlistScript) {
        try {
            validWords = JSON.parse(wordlistScript.textContent);
        } catch (e) {
            console.error('Error parsing wordlist for validation:', e);
            return { valid: false, error: 'Could not validate interests. Please try again.' };
        }
    }
    
    // Convert to lowercase for case-insensitive comparison
    const validWordsLower = validWords.map(word => word.toLowerCase());    // Collect all interest values
    for (let i = 1; i <= 3; i++) {
        const input = document.getElementById(`id_interest_${i}`);
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
 * Show error message to user
 */
function showUserProfileInterestError(message) {
    // Remove any existing error messages
    const existingError = document.querySelector('.interest-error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and show new error message
    const form = document.getElementById('update-user-interests-form');
    if (form) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'interest-error-message';
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

// Make functions globally available
window.showUserProfileInterestForm = showUserProfileInterestForm;
window.hideUserProfileInterestForm = hideUserProfileInterestForm;
window.loadCurrentUserInterestsIntoForm = loadCurrentUserInterestsIntoForm;
window.validateUserProfileInterests = validateUserProfileInterests;
window.showUserProfileInterestError = showUserProfileInterestError;
