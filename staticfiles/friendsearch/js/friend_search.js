/* ==================== */
/* Friend Search JavaScript - Migrated from inline scripts */
/* ==================== */

// Global variables
let isLocationLoading = false;
let autocompleteCache = {};
let autocompleteRequests = {};

// Initialize everything when document is ready
$(document).ready(function() {
  initializeAutocomplete();
  initializeCharacterCounter();
  setupFormSubmissions();
  handleDjangoMessagesFromData(); // Handle any Django messages
  initializeModals(); // Initialize modal functionality
});

// Initialize custom autocomplete for all interest inputs
function initializeAutocomplete() {
  console.log('Initializing custom autocomplete...');
  
  $('.autocomplete-container input').each(function() {
    const $input = $(this);
    const $container = $input.closest('.autocomplete-container');
    
    // Create dropdown if it doesn't exist
    let $dropdown = $container.find('.autocomplete-dropdown');
    if ($dropdown.length === 0) {
      $dropdown = $('<div class="autocomplete-dropdown"></div>');
      $container.append($dropdown);
    }
    
    // Clear existing event handlers to prevent duplicates
    $input.off('input.autocomplete keydown.autocomplete blur.autocomplete focus.autocomplete');
    
    // Input event for autocomplete
    $input.on('input.autocomplete', function() {
      const query = $(this).val().trim();
      
      if (query.length < 1) {
        hideDropdown($dropdown);
        return;
      }
      
      // Show loading state
      showLoadingDropdown($dropdown);
      
      // Debounce the request
      clearTimeout($input.data('autocomplete-timeout'));
      $input.data('autocomplete-timeout', setTimeout(() => {
        fetchSuggestions(query, $dropdown, $input);
      }, 200));
    });
    
    // Keyboard navigation
    $input.on('keydown.autocomplete', function(e) {
      const $dropdown = $container.find('.autocomplete-dropdown');
      const $items = $dropdown.find('.autocomplete-item');
      const $active = $items.filter('.active');
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if ($active.length === 0) {
          $items.first().addClass('active');
        } else {
          const nextIndex = $items.index($active) + 1;
          $active.removeClass('active');
          if (nextIndex < $items.length) {
            $items.eq(nextIndex).addClass('active');
          } else {
            $items.first().addClass('active');
          }
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if ($active.length === 0) {
          $items.last().addClass('active');
        } else {
          const prevIndex = $items.index($active) - 1;
          $active.removeClass('active');
          if (prevIndex >= 0) {
            $items.eq(prevIndex).addClass('active');
          } else {
            $items.last().addClass('active');
          }
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if ($active.length > 0) {
          const value = $active.text();
          $input.val(value);
          hideDropdown($dropdown);
          validateInterestInput($input, value);
        }
      } else if (e.key === 'Escape') {
        hideDropdown($dropdown);
      }
    });
    
    // Hide dropdown on blur (with delay to allow for clicks)
    $input.on('blur.autocomplete', function() {
      setTimeout(() => {
        if (!$container.find('.autocomplete-dropdown:hover').length) {
          hideDropdown($dropdown);
        }
      }, 150);
    });
    
    // Show dropdown on focus if there's content
    $input.on('focus.autocomplete', function() {
      const query = $(this).val().trim();
      if (query.length >= 1) {
        fetchSuggestions(query, $dropdown, $input);
      }
    });
  });
  
  // Handle dropdown item clicks
  $(document).on('click', '.autocomplete-item', function() {
    const $item = $(this);
    const $dropdown = $item.closest('.autocomplete-dropdown');
    const $container = $dropdown.closest('.autocomplete-container');
    const $input = $container.find('input');
    const value = $item.text();
    
    $input.val(value);
    hideDropdown($dropdown);
    validateInterestInput($input, value);
    $input.focus();
  });
  
  // Close dropdowns when clicking outside
  $(document).on('click', function(e) {
    if (!$(e.target).closest('.autocomplete-container').length) {
      $('.autocomplete-dropdown').hide();
    }
  });
}

// Fetch suggestions from backend
function fetchSuggestions(query, $dropdown, $input) {
  // Check cache first
  if (autocompleteCache[query]) {
    displaySuggestions(autocompleteCache[query], $dropdown, query);
    return;
  }
  
  // Cancel previous request for this input
  const inputId = $input.attr('id') || 'default';
  if (autocompleteRequests[inputId]) {
    autocompleteRequests[inputId].abort();
  }
  
  // Make new request
  autocompleteRequests[inputId] = $.ajax({
    url: '/friendsearch/autocomplete/',
    method: 'GET',
    data: { q: query },
    timeout: 5000,
    success: function(response) {
      console.log('Autocomplete response:', response);
      if (Array.isArray(response)) {
        // Cache the result
        autocompleteCache[query] = response;
        displaySuggestions(response, $dropdown, query);
      } else {
        showErrorDropdown($dropdown, 'Invalid response format');
      }
    },
    error: function(xhr, status, error) {
      if (status !== 'abort') {
        console.error('Autocomplete error:', error);
        showErrorDropdown($dropdown, 'Failed to load suggestions');
      }
    },
    complete: function() {
      delete autocompleteRequests[inputId];
    }
  });
}

// Display suggestions in dropdown
function displaySuggestions(suggestions, $dropdown, query) {
  if (!suggestions || suggestions.length === 0) {
    showEmptyDropdown($dropdown);
    return;
  }
  
  const html = suggestions.map(suggestion => {
    // Highlight matching text
    const highlighted = suggestion.replace(
      new RegExp('(' + escapeRegex(query) + ')', 'gi'), 
      '<strong>$1</strong>'
    );
    return `<div class="autocomplete-item">
      <i class="bi bi-tag me-2"></i>${highlighted}
    </div>`;
  }).join('');
  
  $dropdown.html(html).show();
  
  // Position dropdown
  positionDropdown($dropdown);
}

// Show loading state
function showLoadingDropdown($dropdown) {
  $dropdown.html(`
    <div class="autocomplete-loading">
      <i class="bi bi-hourglass me-2"></i>Searching...
    </div>
  `).show();
  positionDropdown($dropdown);
}

// Show empty state
function showEmptyDropdown($dropdown) {
  $dropdown.html(`
    <div class="autocomplete-empty">
      <i class="bi bi-search me-2"></i>No matches found
    </div>
  `).show();
  positionDropdown($dropdown);
}

// Show error state
function showErrorDropdown($dropdown, message) {
  $dropdown.html(`
    <div class="autocomplete-error">
      <i class="bi bi-exclamation-triangle me-2"></i>${message}
    </div>
  `).show();
  positionDropdown($dropdown);
}

// Hide dropdown
function hideDropdown($dropdown) {
  $dropdown.hide().find('.autocomplete-item').removeClass('active');
}

// Position dropdown below input
function positionDropdown($dropdown) {
  const $container = $dropdown.closest('.autocomplete-container');
  const $input = $container.find('input');
  
  // Reset positioning
  $dropdown.css({
    position: 'absolute',
    top: $input.outerHeight(),
    left: 0,
    right: 0,
    zIndex: 1050
  });
}

// Escape regex special characters
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Validate interest input against wordlist
function validateInterestInput($input, value) {
  // Simple client-side validation - can be enhanced
  if (value.length > 0 && value.length < 2) {
    $input.addClass('is-invalid');
    showValidationTooltip($input, 'Interest must be at least 2 characters long');
  } else if (value.length > 50) {
    $input.addClass('is-invalid');
    showValidationTooltip($input, 'Interest must be less than 50 characters');
  } else {
    $input.removeClass('is-invalid').addClass('is-valid');
    hideValidationTooltip($input);
  }
}

// Show validation tooltip
function showValidationTooltip($input, message) {
  // Remove existing tooltip
  hideValidationTooltip($input);
  
  const tooltip = $(`<div class="validation-tooltip">${message}</div>`);
  $input.parent().append(tooltip);
  
  // Position tooltip
  const inputPos = $input.position();
  tooltip.css({
    position: 'absolute',
    top: inputPos.top + $input.outerHeight() + 5,
    left: inputPos.left,
    background: '#dc3545',
    color: 'white',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    zIndex: 1001,
    whiteSpace: 'nowrap'
  });
  
  // Auto-hide after 3 seconds
  setTimeout(() => hideValidationTooltip($input), 3000);
}

// Hide validation tooltip
function hideValidationTooltip($input) {
  $input.parent().find('.validation-tooltip').remove();
}

// Character counter for description
function initializeCharacterCounter() {
  $('textarea[name="description"]').on('input', function() {
    const length = $(this).val().length;
    $('#desc-char-count').text(length);
    
    // Change color based on character count
    if (length > 140) {
      $('#desc-char-count').addClass('text-warning');
    } else if (length > 120) {
      $('#desc-char-count').addClass('text-info');
    } else {
      $('#desc-char-count').removeClass('text-warning text-info');
    }
  });
}

// Show toast notifications
function showToast(type, message) {
  // No notification needed - silent success
}

// Setup form submissions
function setupFormSubmissions() {  // Edit interests form
  $('#editInterestsForm').on('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const $submitBtn = $(this).find('button[type="submit"]');
    const originalText = $submitBtn.html();
    
    // Show loading state
    $submitBtn.html('<span class="loading"></span> Saving...').prop('disabled', true);
    
    $.ajax({
      url: window.location.href,
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false,      success: function(response) {
        if (response.status === 'success') {          // Show success state on button briefly
          $submitBtn.html('<i class="bi bi-check-circle"></i> Successfully Saved!').removeClass('btn-primary-custom').addClass('btn-success');
          
          // Update interests display immediately
          updateInterestsDisplay(response.interests);
          
          // Close modal instantly after brief success indication
          setTimeout(() => {
            const modal = $('#editInterestsModal');
            modal.attr('data-can-close', 'true');
            hideModal(modal);
            
            // Reset button after modal is closed
            setTimeout(() => {
              $submitBtn.html(originalText).removeClass('btn-success').addClass('btn-primary-custom').prop('disabled', false);
            }, 100);
          }, 500);
        } else {
          showToast('error', response.message || 'An error occurred');
          $submitBtn.html(originalText).prop('disabled', false);
        }
      },
      error: function(xhr) {
        const response = xhr.responseJSON;
        if (response && response.message) {
          showToast('error', response.message);
        } else {
          showToast('error', 'An error occurred while saving');
        }
        $submitBtn.html(originalText).prop('disabled', false);
      }
    });
  });
  // Search preferences form
  $('#searchPreferencesForm').on('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const $submitBtn = $(this).find('button[type="submit"]');
    const originalText = $submitBtn.html();
    
    // Show loading state
    $submitBtn.html('<span class="loading"></span> Saving...').prop('disabled', true);
    
    $.ajax({
      url: window.location.href,
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false,      success: function(response) {
        // Show success state on button briefly
        $submitBtn.html('<i class="bi bi-check-circle"></i> Successfully Saved!').removeClass('btn-primary-custom').addClass('btn-success');
        
        // Update the search preferences display immediately
        updateSearchPreferencesDisplay();
        
        // Close modal instantly after brief success indication
        setTimeout(() => {
          const modal = $('#searchPreferencesModal');
          modal.attr('data-can-close', 'true');
          hideModal(modal);
          
          // Reset button after modal is closed
          setTimeout(() => {
            $submitBtn.html(originalText).removeClass('btn-success').addClass('btn-primary-custom').prop('disabled', false);
          }, 100);
        }, 500);
      },
      error: function() {
        showToast('error', 'An error occurred while saving preferences');
        $submitBtn.html(originalText).prop('disabled', false);
      }
    });
  });
}

// Update interests display in the UI
function updateInterestsDisplay(interests) {
  const $interestsDisplay = $('.interests-display');
  const $currentInterests = $('.current-interests');
  
  if (interests && interests.length > 0) {
    const interestTags = interests.map(interest => 
      `<span class="interest-tag">${interest}</span>`
    ).join('');
    
    $interestsDisplay.html(interestTags);
    $currentInterests.find('.no-interests').hide();
  } else {
    $interestsDisplay.empty();
    $currentInterests.find('.no-interests').show();
  }
}

// Update search preferences display in the UI
function updateSearchPreferencesDisplay() {
  console.log('updateSearchPreferencesDisplay called');
  const $form = $('#searchPreferencesForm');
  // Get the form values
  const interests = [];
  if ($form.find('input[name="pref-interest_1"]').val().trim()) {
    interests.push($form.find('input[name="pref-interest_1"]').val().trim());
  }
  if ($form.find('input[name="pref-interest_2"]').val().trim()) {
    interests.push($form.find('input[name="pref-interest_2"]').val().trim());
  }
  if ($form.find('input[name="pref-interest_3"]').val().trim()) {
    interests.push($form.find('input[name="pref-interest_3"]').val().trim());
  }
  const language = $form.find('select[name="search-main_language"]').val();
  const languageText = $form.find('select[name="search-main_language"] option:selected').text();
  const radius = $form.find('select[name="search-radius_km"]').val();
  const radiusText = $form.find('select[name="search-radius_km"] option:selected').text();
  console.log('Form values extracted:', {
    interests: interests,
    language: language,
    languageText: languageText,
    radius: radius,
    radiusText: radiusText
  });
  // Update only the FIRST .mb-3 inside the correct .action-card
  const $preferencesCards = $('.action-card').filter(function() {
    return $(this).find('h3').text().includes('Search Preferences');
  });
  // Remove ALL but the first Search Preferences card from the DOM
  $preferencesCards.slice(1).remove();
  const $preferencesCard = $preferencesCards.first();
  // Remove ALL .mb-3 inside the card except the first, to prevent stacked preferences
  $preferencesCard.find('.mb-3').slice(1).remove();
  const $preferencesDiv = $preferencesCard.find('.mb-3').first();
  console.log('Found preferences div:', $preferencesDiv.length);
  if (interests.length > 0 || language || radius) {
    // Remove any duplicate preferences display in other cards
    $('.action-card').filter(function() {
      return $(this).find('h3').text().includes('Search Preferences');
    }).not($preferencesCard).find('.mb-3').empty();
    // Show preferences and potentially add "Find Friends" button if not exists
    const interestsText = interests.length > 0 ? interests.join(', ') : 'None';
    const langText = language ? languageText : 'Any';
    const rangeText = radius ? radiusText : '10km';
    const truncatedInterests = interestsText.length > 40 ? interestsText.substring(0, 37) + '...' : interestsText;
    console.log('Updating with:', {
      truncatedInterests: truncatedInterests,
      langText: langText,
      rangeText: rangeText
    });
    $preferencesDiv.html(`
      <small class="text-muted">
        <strong>Interests:</strong> ${truncatedInterests}<br>
        <strong>Language:</strong> ${langText}<br>
        <strong>Range:</strong> ${rangeText}
      </small>
    `);
    // Add "Find Friends" button if preferences are saved and button doesn't exist
    if ($('button').filter(function() { return $(this).text().includes('Find Friends'); }).length === 0) {
      console.log('Adding Find Friends button');
      $('.action-cards').after(`
        <div class="text-center mt-4 mb-4">
          <button type="button" class="btn btn-primary-custom btn-lg" onclick="searchWithPreferences()">
            <i class="bi bi-search"></i>
            Find Friends
          </button>
          <p class="text-muted mt-2">
            Search using your saved preferences
          </p>
        </div>
      `);
    } else {
      console.log('Find Friends button already exists');
    }
  } else {
    $preferencesDiv.html('<small class="text-muted">No preferences saved yet</small>');
    // Remove "Find Friends" button if no preferences
    $('button').filter(function() { return $(this).text().includes('Find Friends'); }).closest('.text-center').remove();
  }
}

// Location functionality
function getLocation() {
  if (isLocationLoading) return;
  
  const $btn = $('#location-btn-text');
  const originalText = $btn.text();
  
  if (!navigator.geolocation) {
    showToast('error', 'Geolocation is not supported by your browser');
    return;
  }
  
  isLocationLoading = true;
  $btn.html('<span class="loading"></span> Getting location...');
  
  navigator.geolocation.getCurrentPosition(
    function(position) {
      $('#latitude').val(position.coords.latitude);
      $('#longitude').val(position.coords.longitude);
      
      // Submit the form
      $('#locationForm').submit();
      
      showToast('success', 'Location updated successfully!');
    },
    function(error) {
      let errorMessage = 'Could not retrieve your location. ';
      switch(error.code) {
        case error.PERMISSION_DENIED:
          errorMessage += 'Please allow location access.';
          break;
        case error.POSITION_UNAVAILABLE:
          errorMessage += 'Location information is unavailable.';
          break;
        case error.TIMEOUT:
          errorMessage += 'Location request timed out.';
          break;
        default:
          errorMessage += 'An unknown error occurred.';
          break;
      }
      showToast('error', errorMessage);
      isLocationLoading = false;
      $btn.text(originalText);
    },
    { 
      timeout: 10000,
      enableHighAccuracy: true,
      maximumAge: 300000 // 5 minutes
    }
  );
}

// Function to start chat by redirecting to the chat room
function startChat(chatRoomId) {
  if (!chatRoomId) {
    alert('Chat room not found.');
    return;
  }
  // Redirect to the chat room URL
  window.location.href = `/chat/${chatRoomId}/`;
}

// Reset search function
function resetSearch() {
  // Clear all search form inputs
  $('#search_form input[type="text"]').val('');
  $('#search_form select').prop('selectedIndex', 0);
  $('#search_form input[type="radio"]').prop('checked', false);
  
  // Check the "Any age" radio button by default
  $('#age_any').prop('checked', true);
  
  showToast('info', 'Search form has been reset');
}

// Reinitialize autocomplete when modals are shown
// This will be called from the showModal function instead of Bootstrap events

// Handle window resize to reposition dropdowns
$(window).on('resize', function() {
  $('.autocomplete-dropdown').hide();
});

// Function to handle Django messages (called from template)
function handleDjangoMessages(messages) {
  messages.forEach(function(message) {
    showToast(message.tags, message.message);
  });
}

// Function to handle Django messages from data attribute
function handleDjangoMessagesFromData() {
  const messagesElement = document.getElementById('django-messages');
  if (messagesElement) {
    try {
      const messagesData = messagesElement.getAttribute('data-messages');
      if (messagesData) {
        const messages = JSON.parse(messagesData);
        handleDjangoMessages(messages);
      }
    } catch (e) {
      console.error('Error parsing Django messages:', e);
    }
  }
}

// Simple modal functionality to replace Bootstrap modals
function initializeModals() {
  // Handle modal triggers
  $(document).on('click', '[data-bs-toggle="modal"]', function(e) {
    e.preventDefault();
    const targetId = $(this).attr('data-bs-target');
    const modal = $(targetId);
    showModal(modal);
  });  
  // Prevent closing modals by clicking outside or other means
  // Only allow closing through the Save button
  $(document).on('click', '.modal', function(e) {
    // Prevent closing when clicking on the modal backdrop
    if (e.target === this) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  });
  
  // Also prevent closing when clicking on modal-dialog
  $(document).on('click', '.modal-dialog', function(e) {
    e.stopPropagation();
  });
  
  // Disable escape key for closing modals
  $(document).on('keydown', function(e) {
    if (e.key === 'Escape' && $('.modal.show').length > 0) {
      // Prevent escape key from closing the modal
      e.preventDefault();
      return false;
    }
  });
}

function showModal(modal) {
  modal.addClass('show').css('display', 'block');
  $('body').css('overflow', 'hidden');
  
  // Add a data attribute to track if modal can be closed
  modal.attr('data-can-close', 'false');
  
  // Reset button states when modal opens
  const $submitBtn = modal.find('button[type="submit"]');
  if ($submitBtn.length) {
    // Clear any existing timeouts to prevent conflicts
    if ($submitBtn.data('timeout-id')) {
      clearTimeout($submitBtn.data('timeout-id'));
      $submitBtn.removeData('timeout-id');
    }
    
    if (modal.attr('id') === 'editInterestsModal') {
      $submitBtn.html('<i class="bi bi-check-circle"></i> Save Interests')
                .removeClass('btn-success btn-danger')
                .addClass('btn-primary-custom')
                .prop('disabled', false);
    } else if (modal.attr('id') === 'searchPreferencesModal') {
      $submitBtn.html('<i class="bi bi-check-circle"></i> Save Preferences')
                .removeClass('btn-success btn-danger')
                .addClass('btn-primary-custom')
                .prop('disabled', false);
    }
  }
  
  // Reinitialize autocomplete for modal inputs
  setTimeout(initializeAutocomplete, 100);
}

function hideModal(modal) {
  // Only allow closing if the modal is marked as closeable
  if (modal.attr('data-can-close') !== 'true') {
    return false;
  }
  
  modal.removeClass('show').css('display', 'none');
  $('body').css('overflow', '');
  modal.removeAttr('data-can-close');
}

// Make functions globally available
window.getLocation = getLocation;
window.startChat = startChat;
window.resetSearch = resetSearch;
window.handleDjangoMessages = handleDjangoMessages;
window.searchWithPreferences = searchWithPreferences;

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

// Function to search for friends using saved preferences
function searchWithPreferences() {
  console.log('searchWithPreferences called');
  const $form = $('#searchPreferencesForm');
  const params = new URLSearchParams();
  const interest1 = $form.find('input[name="pref-interest_1"]').val().trim();
  const interest2 = $form.find('input[name="pref-interest_2"]').val().trim();
  const interest3 = $form.find('input[name="pref-interest_3"]').val().trim();
  if (interest1) params.append('search-interest_1', interest1);
  if (interest2) params.append('search-interest_2', interest2);
  if (interest3) params.append('search-interest_3', interest3);
  const language = $form.find('select[name="search-main_language"]').val();
  const radius = $form.find('select[name="search-radius_km"]').val();
  const ageMode = $form.find('input[name="search-age_filtering_mode"]:checked').val();
  if (language) params.append('search-main_language', language);
  if (radius) params.append('search-radius_km', radius);
  if (ageMode) params.append('search-age_filtering_mode', ageMode);
  // Show loading state
  const $findButton = $('button:contains("Find Friends")');
  $findButton.html('<span class="loading"></span> Searching...').prop('disabled', true);
  $('.results-section').html('<div class="text-center p-5"><span class="loading"></span> Loading results...</div>');
  // AJAX GET request instead of redirect
  $.ajax({
    url: window.location.pathname,
    method: 'GET',
    data: params.toString(),
    success: function(response) {
      // Try to extract the results section from the returned HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = response;
      // Debug: Log the entire HTML response for inspection
      console.debug('AJAX response (truncated):', response.slice(0, 1000));
      // Always check if .results-section exists in the response
      const $newSection = $(tempDiv).find('.results-section');
      if ($newSection.length) {
        const scrollY = window.scrollY;
        $('.results-section').replaceWith($newSection);
        window.scrollTo({ top: scrollY });
        // Slide-in animation removed: user cards will just appear instantly
        // Debug: Log the results content
        const newResults = $newSection.html();
        if (newResults && (newResults.includes('No friends found') || newResults.includes('No results'))) {
          console.warn('DEBUG: No results show up (results-section contains no results message).');
        } else {
          // Try to log the user names and all user data if possible
          const userCards = $newSection.find('.user-card');
          if (userCards.length > 0) {
            userCards.each(function(idx, card) {
              const $card = $(card);
              const name = $card.find('.user-info h4').text().trim();
              const age = $card.find('.user-meta .meta-item:contains("years old")').text().trim();
              const language = $card.find('.user-meta .meta-item:contains("translate")').text().trim();
              const location = $card.find('.user-meta .meta-item:contains("Nearby")').text().trim();
              const interests = $card.find('.user-interests li').map(function(){return $(this).text().trim();}).get();
              const description = $card.find('.user-description').text().trim();
              const score = $card.find('.match-score').text().trim();
              console.log(`User #${idx+1}:`, {
                name, age, language, location, interests, description, score
              });
            });
          } else {
            console.log('DEBUG: Results-section updated, but no user cards found.');
          }
        }
      } else {
        // fallback: replace whole container if results-section not found
        $('.results-section').html('<div class="text-danger">No results section found in response.</div>');
        console.error('DEBUG: No results-section found in AJAX response.');
      }
      $findButton.html('<i class="bi bi-search"></i> Find Friends').prop('disabled', false);
    },
    error: function(xhr) {
      $('.results-section').html('<div class="text-danger">An error occurred while searching. Please try again.</div>');
      $findButton.html('<i class="bi bi-search"></i> Find Friends').prop('disabled', false);
    }
  });
}
