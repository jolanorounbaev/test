// Modal open/close logic
const modal = document.getElementById('editProfileModal');
const btn = document.getElementById('openEditProfileModal');
const span = document.getElementById('closeEditProfileModal');

// Only add event listeners if elements exist
if (btn && modal) {
  btn.onclick = function() { modal.style.display = 'block'; }
}
if (span && modal) {
  span.onclick = function() { modal.style.display = 'none'; }
}
if (modal) {
  window.onclick = function(event) { if (event.target == modal) { modal.style.display = 'none'; } }
}

function showProfileSuccessMessage() {
  // Check if jQuery is available
  if (typeof $ !== 'undefined' && $('#profile-success-msg').length === 0) {
    $('body').append('<div id="profile-success-msg" style="position:fixed;top:32px;left:50%;transform:translateX(-50%);background:#4fd18b;color:#fff;padding:18px 32px;border-radius:8px;z-index:2000;font-size:1.2em;box-shadow:0 2px 12px rgba(0,0,0,0.12);">Profile updated successfully!</div>');
    setTimeout(function() { $('#profile-success-msg').fadeOut(400, function() { $(this).remove(); }); }, 2500);
  }
}
window.showProfileSuccessMessage = showProfileSuccessMessage;

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

// Add Friend button functionality
document.addEventListener('DOMContentLoaded', function() {
  const addFriendButton = document.getElementById('addFriendButton');
  
  if (addFriendButton) {
    addFriendButton.addEventListener('click', function(e) {
      e.preventDefault();
      
      const userId = this.getAttribute('data-user-id');
      const csrfToken = getCookie('csrftoken');
      
      if (!csrfToken) {
        alert('CSRF token not found. Please refresh the page.');
        return;
      }
      
      // Disable button to prevent double-clicking
      this.disabled = true;
      this.textContent = 'Sending...';
      
      fetch('/friendsearch/send-friend-request/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
          'user_id': userId
        }),
        credentials: 'same-origin'
      })
      .then(response => response.text())      .then(text => {
        try {
          const data = JSON.parse(text);
            if (data.success) {
            this.innerHTML = '<i class="fas fa-check"></i> Request Sent';
            this.style.background = '#28a745';
            this.style.color = 'white';
          } else {
            // Re-enable button on failure
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-user-plus"></i> Add Friend';
            this.style.background = '';
            this.style.color = '';
            alert('Error: ' + data.message);
          }
        } catch (e) {
          // Re-enable button on error
          this.disabled = false;
          this.innerHTML = '<i class="fas fa-user-plus"></i> Add Friend';
          this.style.background = '';
          this.style.color = '';
          alert('Server error occurred. Please try again.');
        }
      })
      .catch(error => {
        // Re-enable button on error
        this.disabled = false;
        this.innerHTML = '<i class="fas fa-user-plus"></i> Add Friend';
        this.style.background = '';
        this.style.color = '';
        alert('Failed to send friend request. Please try again.');
      });
    });  }
});

// Three dots dropdown menu functionality
document.addEventListener('DOMContentLoaded', function() {
  const threeDotsBtn = document.getElementById('threeDots');
  const dropdownMenu = document.getElementById('dropdownMenu');
  const reportBtn = document.getElementById('reportUser');
  const blockBtn = document.getElementById('blockUser');

  if (threeDotsBtn && dropdownMenu) {
    // Toggle dropdown when clicking three dots
    threeDotsBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      dropdownMenu.classList.toggle('show');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function() {
      dropdownMenu.classList.remove('show');
    });

    // Prevent dropdown from closing when clicking inside it
    dropdownMenu.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  }
  <!-- Report user functionality (placeholder) -->
  if (reportBtn) {
    reportBtn.addEventListener('click', function() {
      const userId = this.getAttribute('data-user-id');
      // Show report modal
      document.getElementById('reportModal').style.display = 'block';
      document.getElementById('reportUserId').value = userId;
      dropdownMenu.classList.remove('show');
    });
  }
  // Block user functionality
  if (blockBtn) {
    blockBtn.addEventListener('click', function() {
      const userId = this.getAttribute('data-user-id');
      if (confirm('Are you sure you want to block this user? This will prevent them from contacting you and remove any friend connections.')) {
        // Show loading state
        const originalText = this.innerHTML;
        this.innerHTML = '⏳ Blocking...';
        this.disabled = true;
        
        // Make AJAX request to block user
        fetch('/block-user/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          },
          body: new URLSearchParams({
            'user_id': userId,
            'action': 'block'
          })
        })
        .then(response => response.json())        .then(data => {
          if (data.success) {
            // Reload the page to show the blocked state
            window.location.reload();
          } else {
            alert('Error: ' + data.message);
            this.innerHTML = originalText;
            this.disabled = false;
          }
        })
        .catch(error => {
          console.error('Error:', error);
          alert('An error occurred while blocking the user.');
          this.innerHTML = originalText;
          this.disabled = false;
        });
      }      dropdownMenu.classList.remove('show');
    });
  }
});

// Function to unblock a user
function unblockUser(userId, button) {
  if (confirm('Are you sure you want to unblock this user?')) {
    // Show loading state
    const originalText = button.innerHTML;
    button.innerHTML = '⏳ Unblocking...';
    button.disabled = true;
    
    // Make AJAX request to unblock user
    fetch('/block-user/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      },
      body: new URLSearchParams({
        'user_id': userId,
        'action': 'unblock'
      })
    })
    .then(response => response.json())    .then(data => {
      if (data.success) {
        // Reload the page to update the UI
        window.location.reload();
      } else {
        alert('Error: ' + data.message);
        button.innerHTML = originalText;
        button.disabled = false;
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('An error occurred while unblocking the user.');
      button.innerHTML = originalText;
      button.disabled = false;
    });
  }
}

// Carousel functionality for content items
let currentSlide = 0;

function changeSlide(direction) {
  const carousel = document.getElementById('carousel');
  if (!carousel) return;
  
  const contentItems = carousel.querySelectorAll('.content-item');
  const totalSlides = contentItems.length;
  
  if (totalSlides === 0) return;
  
  currentSlide += direction;
  
  if (currentSlide < 0) {
    currentSlide = totalSlides - 1;
  } else if (currentSlide >= totalSlides) {
    currentSlide = 0;
  }
  
  const translateX = -currentSlide * 100;
  carousel.style.transform = `translateX(${translateX}%)`;
}

// Initialize carousel
document.addEventListener('DOMContentLoaded', function() {
  const carousel = document.getElementById('carousel');
  if (carousel) {
    // Auto-advance carousel every 5 seconds
    setInterval(() => {
      changeSlide(1);
    }, 5000);
  }
});
