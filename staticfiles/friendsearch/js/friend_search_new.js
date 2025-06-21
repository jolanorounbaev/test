/* ==================== */
/* Friend Search JavaScript - Clean Version */
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
  handleDjangoMessagesFromData();
  initializeModals();
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
      }, 300));
    });
    
    // Keydown events for navigation
    $input.on('keydown.autocomplete', function(e) {
      const $dropdown = $container.find('.autocomplete-dropdown');
      const $items = $dropdown.find('.dropdown-item');
      const $active = $items.filter('.active');
      
      switch(e.which) {
        case 40: // Down arrow
          e.preventDefault();
          if ($items.length === 0) return;
          if ($active.length === 0) {
            $items.first().addClass('active');
          } else {
            $active.removeClass('active');
            const next = $active.next('.dropdown-item');
            if (next.length) {
              next.addClass('active');
            } else {
              $items.first().addClass('active');
            }
          }
          break;
          
        case 38: // Up arrow
          e.preventDefault();
          if ($items.length === 0) return;
          if ($active.length === 0) {
            $items.last().addClass('active');
          } else {
            $active.removeClass('active');
            const prev = $active.prev('.dropdown-item');
            if (prev.length) {
              prev.addClass('active');
            } else {
              $items.last().addClass('active');
            }
          }
          break;
          
        case 13: // Enter
          if ($active.length) {
            e.preventDefault();
            $active.click();
          }
          break;
          
        case 27: // Escape
          hideDropdown($dropdown);
          break;
      }
    });
    
    // Focus event
    $input.on('focus.autocomplete', function() {
      const query = $(this).val().trim();
      if (query.length >= 1) {
        fetchSuggestions(query, $dropdown, $input);
      }
    });
    
    // Blur event with delay to allow clicks
    $input.on('blur.autocomplete', function() {
      setTimeout(() => {
        hideDropdown($dropdown);
      }, 200);
    });
    
    // Click away handler
    $(document).on('click.autocomplete', function(e) {
      if (!$container.is(e.target) && $container.has(e.target).length === 0) {
        hideDropdown($dropdown);
      }
    });
    
    positionDropdown($dropdown);
  });
}

// Fetch suggestions from backend
function fetchSuggestions(query, $dropdown, $input) {
  // Cancel previous request if exists
  if (autocompleteRequests[query]) {
    autocompleteRequests[query].abort();
  }
  
  // Check cache first
  if (autocompleteCache[query]) {
    displaySuggestions(autocompleteCache[query], $dropdown, query);
    return;
  }
  
  // Make new request
  autocompleteRequests[query] = $.ajax({
    url: '/friendsearch/autocomplete/',
    method: 'GET',
    data: { q: query },
    success: function(response) {
      // Cache the response
      autocompleteCache[query] = response;
      
      // Display suggestions
      displaySuggestions(response, $dropdown, query);
      
      // Clean up request tracking
      delete autocompleteRequests[query];
    },
    error: function(xhr) {
      console.error('Autocomplete error:', xhr);
      if (xhr.statusText !== 'abort') {
        showErrorDropdown($dropdown, 'Error loading suggestions');
      }
      delete autocompleteRequests[query];
    }
  });
}

// Display suggestions in dropdown
function displaySuggestions(suggestions, $dropdown, query) {
  if (!suggestions || suggestions.length === 0) {
    showEmptyDropdown($dropdown);
    return;
  }
  
  let html = '';
  suggestions.forEach(function(suggestion) {
    const escapedSuggestion = $('<div>').text(suggestion).html();
    const regex = new RegExp('(' + escapeRegex(query) + ')', 'gi');
    const highlighted = escapedSuggestion.replace(regex, '<strong>$1</strong>');
    html += `<div class="dropdown-item" data-value="${escapedSuggestion}">${highlighted}</div>`;
  });
  
  $dropdown.html(html).show();
  positionDropdown($dropdown);
  
  // Click handler for suggestions
  $dropdown.find('.dropdown-item').on('click', function() {
    const value = $(this).data('value');
    const $input = $dropdown.closest('.autocomplete-container').find('input');
    $input.val(value).trigger('input');
    hideDropdown($dropdown);
    $input.focus();
  });
}

// Show loading state
function showLoadingDropdown($dropdown) {
  $dropdown.html('<div class="dropdown-item loading">Loading...</div>').show();
  positionDropdown($dropdown);
}

// Show empty state
function showEmptyDropdown($dropdown) {
  $dropdown.html('<div class="dropdown-item empty">No suggestions found</div>').show();
  positionDropdown($dropdown);
}

// Show error state
function showErrorDropdown($dropdown, message) {
  $dropdown.html(`<div class="dropdown-item error">${message}</div>`).show();
  positionDropdown($dropdown);
}

// Hide dropdown
function hideDropdown($dropdown) {
  $dropdown.hide();
}

// Position dropdown below input
function positionDropdown($dropdown) {
  const $container = $dropdown.closest('.autocomplete-container');
  const $input = $container.find('input');
  
  if ($input.length) {
    const inputPos = $input.position();
    $dropdown.css({
      top: inputPos.top + $input.outerHeight(),
      left: inputPos.left,
      width: $input.outerWidth()
    });
  }
}

// Escape regex special characters
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Character counter for description
function initializeCharacterCounter() {
  $('textarea[name="description"]').on('input', function() {
    const maxLength = 500;
    const currentLength = $(this).val().length;
    const remaining = maxLength - currentLength;
    
    let $counter = $(this).siblings('.character-counter');
    if ($counter.length === 0) {
      $counter = $('<div class="character-counter"></div>');
      $(this).after($counter);
    }
    
    $counter.text(`${remaining} characters remaining`);
    
    if (remaining < 0) {
      $counter.addClass('text-danger');
    } else if (remaining < 50) {
      $counter.removeClass('text-danger').addClass('text-warning');
    } else {
      $counter.removeClass('text-danger text-warning');
    }
  });
}

// Show toast notifications
function showToast(type, message) {
  // Silent success - no notification needed
}

// Setup form submissions
function setupFormSubmissions() {
  // Edit interests form
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
      contentType: false,
      success: function(response) {
        if (response.status === 'success') {
          // Update interests display
          updateInterestsDisplay(response.interests);
          
          // Show success state briefly
          $submitBtn.html('<i class="bi bi-check-circle"></i> Saved!')
                    .removeClass('btn-primary-custom')
                    .addClass('btn-success')
                    .prop('disabled', false);
          
          // Close modal immediately
          const modal = $('#editInterestsModal');
          modal.attr('data-can-close', 'true');
          hideModal(modal);
          
        } else {
          // Show error state
          $submitBtn.html('<i class="bi bi-x-circle"></i> Error')
                    .removeClass('btn-primary-custom')
                    .addClass('btn-danger')
                    .prop('disabled', false);
          
          // Reset after delay
          setTimeout(() => {
            $submitBtn.html(originalText)
                      .removeClass('btn-danger')
                      .addClass('btn-primary-custom');
          }, 2000);
        }
      },
      error: function() {
        // Show error state
        $submitBtn.html('<i class="bi bi-x-circle"></i> Error')
                  .removeClass('btn-primary-custom')
                  .addClass('btn-danger')
                  .prop('disabled', false);
        
        // Reset after delay
        setTimeout(() => {
          $submitBtn.html(originalText)
                    .removeClass('btn-danger')
                    .addClass('btn-primary-custom');
        }, 2000);
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
      contentType: false,
      success: function(response) {
        if (response.status === 'success') {
          // Update search preferences display
          updateSearchPreferencesDisplay();
          
          // Show success state briefly
          $submitBtn.html('<i class="bi bi-check-circle"></i> Saved!')
                    .removeClass('btn-primary-custom')
                    .addClass('btn-success')
                    .prop('disabled', false);
          
          // Close modal immediately
          const modal = $('#searchPreferencesModal');
          modal.attr('data-can-close', 'true');
          hideModal(modal);
          
        } else {
          // Show error state
          $submitBtn.html('<i class="bi bi-x-circle"></i> Error')
                    .removeClass('btn-primary-custom')
                    .addClass('btn-danger')
                    .prop('disabled', false);
          
          // Reset after delay
          setTimeout(() => {
            $submitBtn.html(originalText)
                      .removeClass('btn-danger')
                      .addClass('btn-primary-custom');
          }, 2000);
        }
      },
      error: function() {
        // Show error state
        $submitBtn.html('<i class="bi bi-x-circle"></i> Error')
                  .removeClass('btn-primary-custom')
                  .addClass('btn-danger')
                  .prop('disabled', false);
        
        // Reset after delay
        setTimeout(() => {
          $submitBtn.html(originalText)
                    .removeClass('btn-danger')
                    .addClass('btn-primary-custom');
        }, 2000);
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
  
  // Update the search preferences card using a more reliable selector
  const $preferencesDiv = $('.action-card').filter(function() {
    return $(this).find('h3').text().includes('Search Preferences');
  }).find('.mb-3');
  
  console.log('Found preferences div:', $preferencesDiv.length);
  
  if (interests.length > 0 || language || radius) {
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
          errorMessage += 'Please allow location access and try again.';
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

// Start chat function
function startChat(chatRoomId) {
  window.location.href = `/chat/room/${chatRoomId}/`;
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

// Simple modal functionality
function initializeModals() {
  // Handle modal triggers
  $(document).on('click', '[data-bs-toggle="modal"]', function(e) {
    e.preventDefault();
    const targetId = $(this).attr('data-bs-target');
    const modal = $(targetId);
    showModal(modal);
  });  
  
  // Prevent closing modals by clicking outside
  $(document).on('click', '.modal', function(e) {
    if (e.target === this) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  });
  
  $(document).on('click', '.modal-dialog', function(e) {
    e.stopPropagation();
  });
  
  // Disable escape key for closing modals
  $(document).on('keydown', function(e) {
    if (e.key === 'Escape' && $('.modal.show').length > 0) {
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

// Function to search for friends using saved preferences
function searchWithPreferences() {
  console.log('searchWithPreferences called');
  
  // Get the preferences from the form (since these are the current saved values)
  const $form = $('#searchPreferencesForm');
  
  // Build search parameters using the saved preferences
  const params = new URLSearchParams();
  
  // Add interests with search- prefix (matching the backend expectation)
  const interest1 = $form.find('input[name="pref-interest_1"]').val().trim();
  const interest2 = $form.find('input[name="pref-interest_2"]').val().trim();
  const interest3 = $form.find('input[name="pref-interest_3"]').val().trim();
  
  console.log('Raw form values:', {
    interest1: interest1,
    interest2: interest2, 
    interest3: interest3
  });
  
  if (interest1) params.append('search-interest_1', interest1);
  if (interest2) params.append('search-interest_2', interest2);
  if (interest3) params.append('search-interest_3', interest3);
  
  // Add other search preferences
  const language = $form.find('select[name="search-main_language"]').val();
  const radius = $form.find('select[name="search-radius_km"]').val();
  const ageMode = $form.find('input[name="search-age_filtering_mode"]:checked').val();
  
  console.log('Other preferences:', {
    language: language,
    radius: radius,
    ageMode: ageMode
  });
  
  if (language) params.append('search-main_language', language);
  if (radius) params.append('search-radius_km', radius);
  if (ageMode) params.append('search-age_filtering_mode', ageMode);
  
  console.log('Final search parameters:', params.toString());
  
  // Show loading state
  const $findButton = $('button:contains("Find Friends")');
  const originalText = $findButton.html();
  $findButton.html('<span class="loading"></span> Searching...').prop('disabled', true);
    // Make GET request to perform search
  const searchUrl = window.location.pathname + '?' + params.toString();
  console.log('Search URL:', searchUrl);
  
  // Redirect to search results
  window.location.href = searchUrl;
}

// Make functions globally available
window.getLocation = getLocation;
window.startChat = startChat;
window.resetSearch = resetSearch;
window.handleDjangoMessages = handleDjangoMessages;
window.searchWithPreferences = searchWithPreferences;
