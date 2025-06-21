// ==================== //
// Main Initialization
// ==================== //
$(document).ready(function() {
    // Initialize all components
    initializeTypeaheads();
    // setupEventHandlers();
    
    // Debugging
    // logWordlistData();
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
    
    if (showForm) {
        $interestDisplay.hide();
        $interestForm.show();
        // Reinitialize typeahead after form is visible
        setTimeout(initializeTypeaheads, 50);
    } else {
        $interestDisplay.show();
        $interestForm.hide();
    }
}

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

// ==================== //
// Autocomplete System
// ==================== //

/**
 * Initialize all typeahead instances
 */
function initializeTypeaheads() {
    try {
        // Destroy existing instances more thoroughly
        $('.autocomplete-container input').typeahead('destroy');
        $('.autocomplete-container input').off('.typeahead');

        // Initialize Bloodhound with better configuration
        const engine = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.whitespace,
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            identify: function(item) { return item.toLowerCase(); }, // For duplicate detection
            remote: {
                url: '/friendsearch/autocomplete/?q=%QUERY%',
                replace: function(url, uriEncodedQuery) {
                    // Add timestamp to prevent caching issues
                    return url.replace('%QUERY%', uriEncodedQuery) + '&t=' + Date.now();
                },
                wildcard: '%QUERY%',
                rateLimitBy: 'debounce',
                rateLimitWait: 300,
                filter: function(response) {
                    if (!Array.isArray(response)) return [];
                    // Remove empty/null suggestions and trim whitespace
                    return response.filter(item => item && typeof item === 'string').map(item => item.trim());
                }
            }
        });

        // Initialize Typeahead with enhanced configuration
        $('.autocomplete-container input').each(function() {
            const $input = $(this);
            const $container = $input.parent('.autocomplete-container');
            
            $input.typeahead({
                hint: true,
                highlight: true,
                minLength: 1,
                autoselect: true,
                classNames: {
                    input: 'tt-input',
                    hint: 'tt-hint',
                    menu: 'tt-dropdown-menu',
                    dataset: 'tt-dataset',
                    suggestion: 'tt-suggestion',
                    selectable: 'tt-selectable',
                    empty: 'tt-empty',
                    open: 'tt-open',
                    cursor: 'tt-cursor'
                }
            }, {
                name: $input.attr('id'),
                source: engine,
                limit: 15,
                display: function(item) { return item; },
                templates: {
                    suggestion: function(data) {
                        // Highlight matching parts of the suggestion
                        const query = $input.typeahead('val').toLowerCase();
                        const index = data.toLowerCase().indexOf(query);
                        if (index >= 0) {
                            const before = data.substring(0, index);
                            const match = data.substring(index, index + query.length);
                            const after = data.substring(index + query.length);
                            return `<div class="tt-suggestion">${before}<strong>${match}</strong>${after}</div>`;
                        }
                        return `<div class="tt-suggestion">${data}</div>`;
                    },
                    empty: [
                        '<div class="empty-message">',
                        'No matches found',
                        '</div>'
                    ].join('\n'),
                    footer: function() {
                        return '<div class="tt-footer">Scroll for more results</div>';
                    }
                }
            })
            .on('typeahead:render', function() {
                // Position dropdown relative to container
                const $menu = $input.siblings('.tt-dropdown-menu');
                $menu.css({
                    'width': $container.outerWidth() + 'px',
                    'max-height': '300px',
                    'overflow-y': 'auto'
                });
            })
            .on('typeahead:select typeahead:autocomplete', function(ev, suggestion) {
                // Validate selection matches exactly
                if ($input.val().toLowerCase() !== suggestion.toLowerCase()) {
                    $input.val(suggestion); // Force exact match
                }
            })
            .on('typeahead:close', function() {
                // Validate on blur
                const currentValue = $input.val();
                if (currentValue) {
                    engine.get(currentValue, function(suggestions) {
                        if (suggestions.length === 0 || 
                            !suggestions.some(s => s.toLowerCase() === currentValue.toLowerCase())) {
                            $input.val('');
                            showTooltip($input, 'Please select a valid suggestion from the list');
                        }
                    });
                }
            })
            .on('keydown', function(e) {
                // Prevent form submission if value isn't valid
                if (e.which === 13) { // Enter key
                    const currentValue = $input.val();
                    engine.get(currentValue, function(suggestions) {
                        if (suggestions.length === 0 || 
                            !suggestions.some(s => s.toLowerCase() === currentValue.toLowerCase())) {
                            e.preventDefault();
                            showTooltip($input, 'Please select a valid suggestion from the list');
                            return false;
                        }
                    });
                }
            });
        });

        // Initialize engine with error handling
        engine.initialize()
            .then(function() {
                console.log('Autocomplete engine ready');
            })
            .catch(function(error) {
                console.error('Autocomplete initialization failed:', error);
            });

    } catch (error) {
        console.error('Error initializing typeaheads:', error);
        // Fallback to regular inputs if Typeahead fails
        $('.autocomplete-container input').typeahead('destroy');
    }
}

// Helper function to show validation tooltips
function showTooltip($element, message) {
    let $tooltip = $element.siblings('.validation-tooltip');
    if ($tooltip.length === 0) {
        $tooltip = $(`<div class="validation-tooltip">${message}</div>`);
        $element.after($tooltip);
    }
    $tooltip.text(message).fadeIn(200);
    setTimeout(() => $tooltip.fadeOut(500), 3000);
}

// Document ready with better initialization handling
$(document).ready(function() {
    // Initialize with a small delay to ensure DOM is fully ready
    setTimeout(initializeTypeaheads, 50);
    
    // Reinitialize when showing edit form
    $(document).on('click', '[onclick*="toggleEdit(true)"]', function() {
        setTimeout(initializeTypeaheads, 150);
    });

    // Handle window resize and scroll events
    let resizeTimer;
    $(window).on('resize scroll', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            $('.tt-dropdown-menu').each(function() {
                const $input = $(this).siblings('.tt-input');
                $(this).css({
                    'width': $input.outerWidth() + 'px',
                    'top': $input.outerHeight() + 'px'
                });
            });
        }, 100);
    });
});

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
