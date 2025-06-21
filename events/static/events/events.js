// ProximityLinked Events JavaScript

// --- Helper Functions (Shared or General) ---
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2) {
    var R = 6371; // Radius of the earth in km
    var dLat = (lat2 - lat1) * Math.PI / 180;
    var dLon = (lon2 - lon1) * Math.PI / 180;
    var a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    var d = R * c;
    return d;
}


// --- Events Page (events.html) Specific ---
let quickNearbyEventIds = [];
let eventsPageMap = null; // For the main map on events.html if it were to be re-added
let modalMap = null; // For the interactive modal map

function updateQuickNearbyDisplay(showOnlyQuickNearby) {
    console.log('updateQuickNearbyDisplay called with showOnlyQuickNearby:', showOnlyQuickNearby);
    console.log('quickNearbyEventIds:', quickNearbyEventIds);
    
    document.querySelectorAll('.event-card').forEach(function(card) {
        const eventId = card.id.replace('event-card-', '');
        const quickLabel = card.querySelector('.quick-nearby-label');
        
        if (showOnlyQuickNearby) {
            // When active (blue), show ONLY quick & nearby events
            if (quickNearbyEventIds.length > 0 && quickNearbyEventIds.includes(parseInt(eventId))) {
                card.style.display = '';
                if(quickLabel) quickLabel.style.display = 'inline-block';
                console.log('Showing quick/nearby event:', eventId);
            } else {
                card.style.display = 'none';
                console.log('Hiding non-quick/nearby event:', eventId);
            }
        } else {
            // When inactive (grey), show ALL events but with labels for quick & nearby ones
            card.style.display = '';
            if (quickNearbyEventIds.includes(parseInt(eventId))) {
                 if(quickLabel) quickLabel.style.display = 'inline-block';
                 console.log('Showing label for quick/nearby event:', eventId);
            } else {
                 if(quickLabel) quickLabel.style.display = 'none';
                 console.log('Hiding label for non-quick/nearby event:', eventId);
            }
        }
    });
}

function initializeEventsPageMap(eventsData) {
    // This function would initialize a main map on events.html if needed.
    // For now, it's a placeholder if you re-add a non-modal main map.
    // Example:
    // const mapDiv = document.getElementById('events-main-map-container');
    // if (!mapDiv || !eventsData) return;
    // ... map initialization logic ...
}

function initializeModalMapLogic(eventsData) {
    const openMapBtn = document.getElementById('open-interactive-map');
    const closeMapBtn = document.getElementById('close-interactive-map');
    const modalDiv = document.getElementById('interactive-map-modal');
    const modalMapDiv = document.getElementById('modal-events-map');

    if (!openMapBtn || !closeMapBtn || !modalDiv || !modalMapDiv || !eventsData) return;

    let eventsWithCoords = eventsData.filter(e => e.lat !== null && e.lng !== null);

    openMapBtn.addEventListener('click', function(e) {
        e.preventDefault();
        modalDiv.style.display = 'block';
        setTimeout(function() {
            if (!modalMap && eventsWithCoords.length > 0) {
                modalMap = L.map(modalMapDiv, { minZoom: 10, maxZoom: 17, zoomDelta: 0.5, zoomSnap: 0.5 })
                             .setView([eventsWithCoords[0].lat, eventsWithCoords[0].lng], 12);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(modalMap);

                eventsWithCoords.forEach(function(ev) {
                    L.marker([ev.lat, ev.lng]).addTo(modalMap)
                      .bindPopup('<b>' + ev.title + '</b><br>' + ev.address + '<br>' + ev.time + '<br><a href="#event-card-' + ev.id + '" onclick="document.getElementById(\\\'interactive-map-modal\\\').style.display=\\\'none\\\'">View details</a>');
                });
            } else if (modalMap) {
                modalMap.invalidateSize(); // Adjust map size if already initialized
            }
        }, 50);
    });

    closeMapBtn.addEventListener('click', function() {
        modalDiv.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === modalDiv) {
            modalDiv.style.display = 'none';
        }
    });
}

function setupEventsPageInteractions() {
    // Quick Nearby Toggle Button
    const quickNearbyToggleBtn = document.getElementById('quick-nearby-toggle-btn');    if (quickNearbyToggleBtn) {
        quickNearbyToggleBtn.addEventListener('click', function() {            const isActive = this.classList.toggle('active');
            console.log('Quick & Nearby button clicked. Now active:', isActive);
            updateQuickNearbyDisplay(isActive);            if (isActive) {
                console.log('Button is now ACTIVE (blue) - should show only quick & nearby events');
                this.style.setProperty('background', '#007bff', 'important'); // Blue when active
                this.style.setProperty('color', 'white', 'important'); // White text
                // Disable the radius form when quick & nearby is active
                const radiusForm = document.getElementById('radius-filter-form');
                if (radiusForm) {
                    radiusForm.style.opacity = '0.5';
                    radiusForm.style.pointerEvents = 'none';
                }            } else {
                console.log('Button is now INACTIVE (white) - should show all events');
                this.style.setProperty('background', '#f8f9fa', 'important'); // White/light grey when inactive
                this.style.setProperty('color', '#495057', 'important'); // Dark text
                // Re-enable the radius form
                const radiusForm = document.getElementById('radius-filter-form');
                if (radiusForm) {
                    radiusForm.style.opacity = '1';
                    radiusForm.style.pointerEvents = 'auto';
                }
            }
        });    }

    // AJAX Delete for Event Cards
    document.querySelectorAll('.event-card form[action*="delete_event"]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!confirm('Are you sure you want to delete this event?')) return;
            fetch(form.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') },
                body: new FormData(form)
            })
            .then(response => {
                if (response.ok) {
                    form.closest('.event-card').remove();
                } else {
                    alert('Failed to delete event.');
                }
            })
            .catch(() => alert('Failed to delete event.'));
        });
    });
}

// --- Create Event Page (create_event.html) Specific ---
let createUserLat = null;
let createUserLng = null;
let createEventMarker = null;
let createUserLocationMarker = null; // Renamed from userMarker
let createEventMap = null; // Renamed from map
let createGlowCircle = null;
let createReverseGeocodeTimeout = null;
let maxRadiusCircleCreate = null; // Was window.maxRadiusCircle

function setCreateLatLng(lat, lng, updateGlowAndAddress = true) {
    const latInput = document.getElementById('id_latitude');
    const lngInput = document.getElementById('id_longitude');
    if (latInput) latInput.value = lat;
    if (lngInput) lngInput.value = lng;

    if (!createEventMap) return;

    if (createEventMarker) {
        createEventMarker.setLatLng([lat, lng]);
    } else {
        createEventMarker = L.marker([lat, lng], { draggable: true }).addTo(createEventMap);
        createEventMarker.on('dragend', function() {
            const pos = createEventMarker.getLatLng();
            setCreateLatLng(pos.lat, pos.lng, true);
            validateCreateRadius();
        });
        createEventMarker.on('drag', function() {
            const pos = createEventMarker.getLatLng();
            setCreateLatLng(pos.lat, pos.lng, false); // Don't geocode on drag
        });
    }
    validateCreateRadius();
    if (updateGlowAndAddress) {
        highlightCreateLocation(lat, lng);
        reverseGeocodeAndFillCreate(lat, lng);
    }
}

function showCreateUserMarker(lat, lng) {
    if (!createEventMap) return;
    if (createUserLocationMarker) {
        createUserLocationMarker.setLatLng([lat, lng]);
    } else {
        createUserLocationMarker = L.marker([lat, lng], {
            icon: L.icon({
                iconUrl: 'https://cdn.jsdelivr.net/gh/pointhi/leaflet-color-markers@master/img/marker-icon-blue.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
                iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
            }),
            draggable: false
        }).addTo(createEventMap).bindPopup('Your location');
    }
}

function validateCreateRadius() {
    const eventLatEl = document.getElementById('id_latitude');
    const eventLngEl = document.getElementById('id_longitude');
    const radiusSelectEl = document.getElementById('radius-select'); // ID is 'radius-select'
    const warningEl = document.getElementById('radius-warning');

    if (!eventLatEl || !eventLngEl || !radiusSelectEl || !warningEl || createUserLat === null || createUserLng === null) {
        if(warningEl) warningEl.style.display = 'none';
        return true; // Not enough info to validate, or user location unknown
    }

    const eventLat = parseFloat(eventLatEl.value);
    const eventLng = parseFloat(eventLngEl.value);
    if (isNaN(eventLat) || isNaN(eventLng)) {
        warningEl.style.display = 'none';
        return true; // Event location not set yet
    }
    
    const radius = parseInt(radiusSelectEl.value);
    const dist = getDistanceFromLatLonInKm(createUserLat, createUserLng, eventLat, eventLng);

    if (dist > radius) {
        warningEl.style.display = 'inline';
        return false;
    } else {
        warningEl.style.display = 'none';
        return true;
    }
}

function highlightCreateLocation(lat, lng) {
    if (!createEventMap) return;
    if (createGlowCircle) {
        createEventMap.removeLayer(createGlowCircle);
    }
    createGlowCircle = L.circle([lat, lng], {
        color: '#28a745', fillColor: '#28a745', fillOpacity: 0.25,
        radius: 30, weight: 6, opacity: 0.7, className: 'glow-effect'
    }).addTo(createEventMap);
}

function reverseGeocodeAndFillCreate(lat, lng) {
    const addressInput = document.getElementById('id_address');
    if (addressInput) addressInput.value = 'Loading address...';

    if (createReverseGeocodeTimeout) clearTimeout(createReverseGeocodeTimeout);

    createReverseGeocodeTimeout = setTimeout(function() {
        fetch(`https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=AIzaSyD9zYnUg77DHVU0KY2bZrJU74iNm5SIYX4`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'OK' && data.results && data.results.length > 0) {
                    if (addressInput) addressInput.value = data.results[0].formatted_address;
                } else {
                    if (addressInput) addressInput.value = 'Address not found.'; // Clearer message
                    console.error('Geocoding failed:', data.status, data.error_message);
                }
            })
            .catch(error => {
                if (addressInput) addressInput.value = 'Error fetching address.';
                console.error('Error fetching address:', error);
            });
    }, 400);
}

function drawMaxRadiusCircleCreate(lat, lng, radiusKm) {
    if (!createEventMap) return;
    if (maxRadiusCircleCreate) {
        createEventMap.removeLayer(maxRadiusCircleCreate);
    }
    maxRadiusCircleCreate = L.circle([lat, lng], {
        color: '#007bff', fillOpacity: 0, radius: radiusKm * 1000,
        weight: 3, opacity: 0.8, dashArray: '8 12', interactive: false
    }).addTo(createEventMap);
}

function updateMaxRadiusCircleCreate() {
    if (createUserLat !== null && createUserLng !== null) {
        const radiusSelectEl = document.getElementById('radius-select');
        if (radiusSelectEl) {
            const radius = parseInt(radiusSelectEl.value);
            drawMaxRadiusCircleCreate(createUserLat, createUserLng, radius);
        }
    }
}

function initCreateEventMap(centerLat, centerLng) {
    const mapDiv = document.getElementById('map'); // This is the map for create_event.html
    if (!mapDiv) {
        // console.error("Map container 'map' not found for create event page.");
        return;
    }

    // console.log("Initializing create event map with Lat:", centerLat, "Lng:", centerLng);

    createEventMap = L.map(mapDiv, { 
        minZoom: 10, maxZoom: 17, zoomDelta: 0.5, zoomSnap: 0.5
    });

    if (typeof centerLat === 'number' && !isNaN(centerLat) && typeof centerLng === 'number' && !isNaN(centerLng)) {
        createEventMap.setView([centerLat, centerLng], 13);
    } else {
        // console.warn("Invalid or missing center coordinates for create event map. Defaulting to Brussels. Received Lat:", centerLat, "Lng:", centerLng);
        createEventMap.setView([50.8503, 4.3517], 10); // Brussels fallback view
    }

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(createEventMap);

    const radiusSelectEl = document.getElementById('radius-select');
    if (radiusSelectEl) { // This is the radius select on create_event.html
        const radius = parseInt(radiusSelectEl.value);
        drawMaxRadiusCircleCreate(centerLat, centerLng, radius); // Draw for initial user location
    }

    L.Control.geocoder({ defaultMarkGeocode: false })
        .on('markgeocode', function(e) {
            setCreateLatLng(e.geocode.center.lat, e.geocode.center.lng);
            if (createEventMap) createEventMap.panTo(e.geocode.center);
        })
        .addTo(createEventMap);

    createEventMap.on('click', function(e) {
        setCreateLatLng(e.latlng.lat, e.latlng.lng);
    });

    // Initial marker if lat/lng are already in the form (e.g., editing an event - though form doesn't support this yet)
    const initialLatEl = document.getElementById('id_latitude');
    const initialLngEl = document.getElementById('id_longitude');
    if (initialLatEl && initialLngEl) {
        const initialLat = parseFloat(initialLatEl.value);
        const initialLng = parseFloat(initialLngEl.value);
        if (!isNaN(initialLat) && !isNaN(initialLng) && initialLat !== 0 && initialLng !== 0) {
            setCreateLatLng(initialLat, initialLng);
        } else {
            setCreateLatLng(centerLat, centerLng); // Default to center (user location or fallback)
        }
    } else {
         setCreateLatLng(centerLat, centerLng);
    }


    if (createUserLat !== null && createUserLng !== null) {
        showCreateUserMarker(createUserLat, createUserLng);
    }
}

function setupCreateEventPage() {
    // console.log("Setting up Create Event Page. window.userLatitude:", window.userLatitude, "window.userLongitude:", window.userLongitude);
    // Attempt to get user's location first
    if (typeof window.userLatitude === 'number' && !isNaN(window.userLatitude) && 
        typeof window.userLongitude === 'number' && !isNaN(window.userLongitude)) {
        createUserLat = window.userLatitude;
        createUserLng = window.userLongitude;
        // console.log("Using user location from window object for create map: Lat:", createUserLat, "Lng:", createUserLng);
        initCreateEventMap(createUserLat, createUserLng);
    } else if (navigator.geolocation) {
        // console.log("Attempting to use browser geolocation for create map.");
        navigator.geolocation.getCurrentPosition(function(pos) {
            createUserLat = pos.coords.latitude;
            createUserLng = pos.coords.longitude;
            // console.log("Browser geolocation success for create map: Lat:", createUserLat, "Lng:", createUserLng);
            initCreateEventMap(createUserLat, createUserLng);
        }, function() { // Geolocation failed or denied
            // console.warn("Browser geolocation failed or denied for create map. Defaulting to Brussels.");
            createUserLat = 50.8503; // Brussels fallback
            createUserLng = 4.3517;
            initCreateEventMap(createUserLat, createUserLng);
            alert("Could not get your location. Defaulting to Brussels. Please allow location access for better experience or search for your address.");
        });
    } else { // Geolocation not supported
        // console.warn("Browser geolocation not supported. Defaulting to Brussels for create map.");
        createUserLat = 50.8503; // Brussels fallback
        createUserLng = 4.3517;
        initCreateEventMap(createUserLat, createUserLng);
        alert("Geolocation is not supported by your browser. Defaulting to Brussels. Please search for your address.");
    }

    const radiusSelectEl = document.getElementById('radius-select'); // Specific to create_event form context
    if (radiusSelectEl) {
        radiusSelectEl.addEventListener('change', function() {
            validateCreateRadius();
            updateMaxRadiusCircleCreate();
        });
    }

    const eventCreateForm = document.getElementById('event-create-form');
    if (eventCreateForm) {
        eventCreateForm.addEventListener('submit', function(e) {
            if (!validateCreateRadius()) {
                e.preventDefault();
                alert('Selected event location is outside the chosen radius from your current location!');
            }
        });
    }
}

function fetchQuickNearbyEvents() {
    // Get user location for quick nearby calculation
    let userLat, userLng;
    
    // Try to get user location from window object first (from profile)
    if (typeof window.userLatitude === 'number' && !isNaN(window.userLatitude) && 
        typeof window.userLongitude === 'number' && !isNaN(window.userLongitude)) {
        userLat = window.userLatitude;
        userLng = window.userLongitude;
        fetchQuickNearbyWithLocation(userLat, userLng);
    } else if (navigator.geolocation) {
        // Fallback to browser geolocation
        navigator.geolocation.getCurrentPosition(function(pos) {
            userLat = pos.coords.latitude;
            userLng = pos.coords.longitude;
            fetchQuickNearbyWithLocation(userLat, userLng);
        }, function() {
            console.warn("Could not get user location for quick nearby events");
            // Show warning
            const warning = document.getElementById('quick-nearby-warning');
            if (warning) warning.style.display = 'inline';
        });
    } else {
        console.warn("Geolocation not supported for quick nearby events");
        // Show warning
        const warning = document.getElementById('quick-nearby-warning');
        if (warning) warning.style.display = 'inline';
    }
}

function fetchQuickNearbyWithLocation(lat, lng) {
    const now = new Date();
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    fetch('/events/quick-nearby/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },        body: JSON.stringify({
            lat: lat,
            lng: lng,
            time: now.toISOString(),
            timezone: timezone
        })
    })
    .then(response => response.json())    .then(data => {
        quickNearbyEventIds = data.quick_nearby_ids || [];
        console.log('Received quick nearby events from server:', quickNearbyEventIds);
        console.log('Debug info from server:', data.debug);
        // Hide warning if successful
        const warning = document.getElementById('quick-nearby-warning');
        if (warning) warning.style.display = 'none';
        
        // Update display to show labels for quick nearby events
        updateQuickNearbyDisplay(false); // Show all events but with labels
    })
    .catch(error => {
        console.error('Error fetching quick nearby events:', error);
    });
}

function applyRadiusFilter(radiusKm) {
    // Only apply if user has location and not in quick nearby mode
    const quickNearbyBtn = document.getElementById('quick-nearby-toggle-btn');
    const isQuickNearbyActive = quickNearbyBtn && quickNearbyBtn.classList.contains('active');
    
    if (isQuickNearbyActive) {
        return; // Don't apply radius filter when quick & nearby is active
    }
    
    // Get user location
    let userLat, userLng;
    if (typeof window.userLatitude === 'number' && !isNaN(window.userLatitude) && 
        typeof window.userLongitude === 'number' && !isNaN(window.userLongitude)) {
        userLat = window.userLatitude;
        userLng = window.userLongitude;
    } else {
        // If no user location, show all events
        document.querySelectorAll('.event-card').forEach(function(card) {
            card.style.display = '';
        });
        return;
    }
    
    // Filter events by radius
    document.querySelectorAll('.event-card').forEach(function(card) {
        const eventId = card.id.replace('event-card-', '');
        
        // Find event data in the eventsDataForMap array
        let eventData = null;
        if (typeof eventsDataForMap !== 'undefined') {
            eventData = eventsDataForMap.find(e => e.id == eventId);
        }
        
        if (eventData && eventData.lat && eventData.lng) {
            const distance = getDistanceFromLatLonInKm(userLat, userLng, eventData.lat, eventData.lng);
            if (distance <= radiusKm) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        } else {
            // Show events without coordinates
            card.style.display = '';
        }
    });
}

// --- Unified DOMContentLoaded ---
document.addEventListener('DOMContentLoaded', function() {
    // console.log("DOMContentLoaded event fired.");
    // console.log("Initial window.userLatitude:", window.userLatitude, "window.userLongitude:", window.userLongitude);    // Initialization for events.html
    if (document.getElementById('open-interactive-map') && typeof eventsDataForMap !== 'undefined') {
        // console.log("Initializing events.html specific JavaScript");        initializeEventsPageMap(eventsDataForMap); 
        initializeModalMapLogic(eventsDataForMap);
        setupEventsPageInteractions();
        // Fetch quick nearby events on page load
        fetchQuickNearbyEvents();
    }

    // Initialization for create_event.html
    if (document.getElementById('event-create-form') && document.getElementById('map')) {
        // console.log("Initializing create_event.html specific JavaScript");
        setupCreateEventPage();
    }
    
    // Handle radius filtering form
    const radiusForm = document.getElementById('radius-filter-form');
    const radiusSelect = document.getElementById('radius-select');
    
    if (radiusForm && radiusSelect) {
        // Apply initial radius filter on page load
        const initialRadius = parseFloat(radiusSelect.value) || 10;
        setTimeout(function() {
            applyRadiusFilter(initialRadius);
        }, 500); // Wait for events data to be ready
        
        // Handle form submission
        radiusForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const selectedRadius = parseFloat(radiusSelect.value) || 10;
            applyRadiusFilter(selectedRadius);
        });
        
        // Handle select change
        radiusSelect.addEventListener('change', function() {
            const selectedRadius = parseFloat(this.value) || 10;
            applyRadiusFilter(selectedRadius);
        });
    }
});
