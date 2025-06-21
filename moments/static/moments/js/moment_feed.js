// CSRF token helper (make sure this is at the top of the file)
function getCSRFToken() {
  // Try to get from input first, fallback to meta tag
  const input = document.querySelector('input[name=csrfmiddlewaretoken]');
  if (input) return input.value;
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.content;
  return '';
}

document.addEventListener('DOMContentLoaded', () => {
  // === Interest Autocomplete ===
  const input = document.getElementById('interest-input');
  const selectedContainer = document.getElementById('selected-interests');
  const hiddenInputsContainer = document.getElementById('interest-hidden-inputs');
  const suggestionBox = document.createElement('div');
  const selectedInterests = []; // Source of truth for selected items

  if (!input || !selectedContainer || !hiddenInputsContainer) {
    console.error("Interest feature critical elements not found. Autocomplete disabled.");
    return;
  }

  suggestionBox.className = 'bg-white border rounded shadow absolute z-10 max-h-40 overflow-y-auto text-sm';
  suggestionBox.style.display = 'none';
  if (input.parentNode) {
    input.parentNode.insertBefore(suggestionBox, input.nextSibling); // Insert suggestionBox after the input field
  } else {
    console.error("Input field has no parent node. Cannot append suggestion box.");
    return;
  }

  function updateSuggestionBoxPosition() {
    if (!input) return;
    const rect = input.getBoundingClientRect();
    suggestionBox.style.left = `${rect.left + window.scrollX}px`;
    suggestionBox.style.top = `${rect.bottom + window.scrollY}px`;
    suggestionBox.style.width = `${rect.width}px`;
  }

  updateSuggestionBoxPosition();
  window.addEventListener('resize', updateSuggestionBoxPosition);
  window.addEventListener('scroll', updateSuggestionBoxPosition, true); // Update on scroll too

  // Fetch wordlist ONCE and set up everything that depends on it
  fetch("/moments/interest-wordlist/")
    .then(res => {
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    })
    .then(wordlist => {
      console.log("Wordlist loaded successfully:", wordlist);
      if (!Array.isArray(wordlist)) {
        console.error("Fetched wordlist is not an array:", wordlist);
        alert("Could not load interests. The data format is incorrect.");
        if (input) {
            input.placeholder = "Interests unavailable (data error)";
            input.disabled = true;
        }
        return;
      }

      function addInterest(value) {
        const trimmedValue = value.trim();
        console.log(`Attempting to add interest: "${trimmedValue}"`);
        console.log("Current selectedInterests before add:", JSON.stringify(selectedInterests));
        console.log("Is value in wordlist?", wordlist.includes(trimmedValue));

        if (selectedInterests.length >= 3) {
          console.log("Interest limit reached (3). Current count:", selectedInterests.length);
          alert("You can only select up to 3 interests.");
          return false;
        }
        if (selectedInterests.includes(trimmedValue)) {
          console.log(`Duplicate interest detected: "${trimmedValue}"`);
          alert("This interest is already selected.");
          return false;
        }
        if (!wordlist.includes(trimmedValue)) {
          console.log(`Invalid interest: "${trimmedValue}". Not in wordlist.`);
          alert(`"${trimmedValue}" is not a valid interest. Please select from the suggestions.`);
          return false;
        }

        selectedInterests.push(trimmedValue);
        console.log("Interest added. Updated selectedInterests:", JSON.stringify(selectedInterests));

        const tag = document.createElement('span');
        tag.className = "bg-gray-200 px-2 py-1 rounded text-xs mr-2 mb-2 inline-block hover:bg-red-200 cursor-pointer";
        tag.innerHTML = `${trimmedValue} &times;`;
        tag.onclick = () => {
          console.log(`Removing interest: "${trimmedValue}"`);
          const index = selectedInterests.indexOf(trimmedValue);
          if (index > -1) {
            selectedInterests.splice(index, 1);
          }
          tag.remove();
          const hiddenInput = hiddenInputsContainer.querySelector(`input[name="interests"][value="${trimmedValue}"]`);
          if (hiddenInput) hiddenInput.remove();
          console.log("Interest removed. Updated selectedInterests:", JSON.stringify(selectedInterests));
        };
        selectedContainer.appendChild(tag);

        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'interests';
        hidden.value = trimmedValue;
        hiddenInputsContainer.appendChild(hidden);
        
        console.log("Hidden input created for interest:", trimmedValue);
        return true;
      }

      input.addEventListener('input', () => {
        const term = input.value.toLowerCase();
        suggestionBox.innerHTML = '';
        if (term) {
          const matches = wordlist.filter(w => w.toLowerCase().startsWith(term));
          if (matches.length > 0) {
            matches.slice(0, 5).forEach(match => {
              const item = document.createElement('div');
              item.className = 'p-2 hover:bg-gray-100 cursor-pointer';
              item.textContent = match;
              item.addEventListener('click', () => {
                console.log(`Suggestion clicked: "${match}"`);
                addInterest(match);
                input.value = ''; 
                suggestionBox.innerHTML = '';
                suggestionBox.style.display = 'none';
                // input.focus(); // Consider if refocus is needed, can sometimes cause quick re-opening of suggestions
              });
              suggestionBox.appendChild(item);
            });
            suggestionBox.style.display = 'block';
            updateSuggestionBoxPosition();
          } else {
            suggestionBox.style.display = 'none';
          }
        } else {
          suggestionBox.style.display = 'none';
        }
      });

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const currentValue = input.value.trim();
          let interestToAdd = null;

          if (currentValue) {
            if (wordlist.includes(currentValue)) {
              interestToAdd = currentValue;
            } else if (suggestionBox.children.length > 0 && suggestionBox.style.display !== 'none') {
              const firstSuggestionItem = suggestionBox.children[0];
              if (firstSuggestionItem) {
                const firstSuggestionText = firstSuggestionItem.textContent;
                if (firstSuggestionText && wordlist.includes(firstSuggestionText)) {
                  interestToAdd = firstSuggestionText;
                }
              }
            }
          }
          
          let added = false;
          if (interestToAdd) {
            console.log(`Enter key. Adding determined interest: "${interestToAdd}"`);
            added = addInterest(interestToAdd);
          } else if (currentValue) { // Attempt to add what user typed, even if not in suggestions
            console.log(`Enter key. Attempting to add direct input: "${currentValue}"`);
            added = addInterest(currentValue);
          }
          
          // Clear input and hide suggestions only if an attempt was made to add something
          // or if the input should always be cleared on Enter.
          // If 'added' is false due to validation, user might want to see their input.
          // For now, clear consistently.
          input.value = ''; 
          suggestionBox.innerHTML = '';
          suggestionBox.style.display = 'none';
        }
      });
      
      // Hide suggestion box if user clicks outside
      document.addEventListener('click', (event) => {
        if (input && suggestionBox && !input.contains(event.target) && !suggestionBox.contains(event.target)) {
          suggestionBox.style.display = 'none';
        }
      });

      const postBtn = document.getElementById('postMomentBtn');
      if (postBtn) {
        postBtn.addEventListener("click", function(e) {
          // Final client-side check, though server-side validation is key
          if (selectedInterests.length > 3) {
            alert("Error: You still have more than 3 interests selected. Please remove some.");
            e.preventDefault();
            return;
          }
          // Add any other pre-post validation if needed
        });
      }
    })
    .catch(err => {
      console.error("Failed to load or process wordlist for interests:", err);
      alert("Could not load interests. Please try refreshing the page or contact support if the issue persists.");
      if (input) {
        input.placeholder = "Interests unavailable";
        input.disabled = true;
      }
    });
  
  // Removed the 'addInterest' function from here as it's now inside fetch.then()
  // Removed the 'if (input)' block that contained old event listeners and addInterest definition.
  // All interest-related setup is now inside the fetch.then() callback

  // === Fire Cooldown Timer Initialization ===
  document.querySelectorAll('.fire-container').forEach(container => {
    const fireBtn = container.querySelector('.fire-btn');
    const timerDiv = container.querySelector('.fire-cooldown-timer');
    if (timerDiv && fireBtn) {
      const cooldown = parseInt(timerDiv.getAttribute('data-cooldown-seconds'), 10);
      console.log('Cooldown timer found:', timerDiv, 'Cooldown seconds:', cooldown);
      if (cooldown && cooldown > 0) {
        showFireCooldown(fireBtn, cooldown);
      }
    }
  });
}); // Correctly close DOMContentLoaded listener and its arrow function

window.loadComments = function(momentId) {
    const container = document.getElementById(`comments-${momentId}`);
    const btn = document.querySelector(`#comments-btn-${momentId}`);

    const isOpen = container.classList.contains("loaded-visible");

    if (isOpen) {
        container.innerHTML = "";
        container.classList.remove("loaded-visible");
        container.classList.add("hidden");
        btn.innerHTML = "👁️ View Comments";
        return;
    }

    fetch(`/moments/inline-comments/${momentId}/`)
        .then(res => res.text())
        .then(html => {
            console.log("Fetched comments:", html);
            container.innerHTML = html;
            container.classList.remove("hidden");
            container.classList.add("loaded-visible");
            btn.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Comments';
        })
        .catch(err => {
            console.error("Failed to load comments:", err);
        });
};


  
  

  // === Moment Chat (WebSocket) ===
  window.setupMomentRoom = function (momentId) {
    const socket = new WebSocket(`ws://${window.location.host}/ws/moments/${momentId}/`);
    const repliesBox = document.querySelector(`#moment-room-${momentId} .replies`);
    const input = document.querySelector(`#moment-room-${momentId} input`);
    const form = document.querySelector(`#moment-room-${momentId} form`);

    if (!form || !repliesBox || !input) return;

    form.addEventListener('submit', e => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      socket.send(JSON.stringify({ message }));
      input.value = '';
    });

    socket.onmessage = e => {
      const data = JSON.parse(e.data);
      const div = document.createElement('div');
      div.innerHTML = `<strong>${data.user}</strong>: ${data.message}`;
      repliesBox.appendChild(div);
      repliesBox.scrollTop = repliesBox.scrollHeight;
    };
  };

  // === Emoji Reaction (Event Delegation) ===
document.body.addEventListener('click', function(e) {
  // Fire reaction
  const fireBtn = e.target.closest('.fire-btn');
  if (fireBtn) {
    fireHandler(fireBtn);
    return;
  }
  // Heart reaction
  const heartBtn = e.target.closest('.heart-btn');
  if (heartBtn) {
    console.log('Heart button clicked', heartBtn);
    const momentId = heartBtn.dataset.momentId;
    fetch(`/moments/react/heart/${momentId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCSRFToken() },
    })
    .then(res => res.json())
    .then(data => {
      console.log('Heart fetch response', data);
      if (data.status === 'liked' || data.status === 'unliked') {
        heartBtn.innerText = `❤️ ${data.heart_count}`;
      }
    });
    return;
  }
});



  // === Ping System ===
  document.querySelectorAll('.ping-button').forEach(button => {
    button.addEventListener('click', () => {
      const userId = button.dataset.userId;
      const momentId = button.dataset.momentId;

      fetch(`/moments/${momentId}/ping/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `user_id=${userId}`
      })
        .then(response => response.json())
        .then(data => {
          button.innerText = data.status === 'pinged' ? '✅ Pinged' : '⚠️ Already Pinged';
        });
    });
  });

  // === Toast Notification ===
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 bg-${type === 'error' ? 'red' : 'green'}-500 text-white px-4 py-2 rounded shadow-lg z-50`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  // === CSRF Helper ===
  function getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [key, val] = cookie.trim().split('=');
      if (key === name) return decodeURIComponent(val);
    }
    return null;
  }

// === Moment Media Enhancements ===

  const fileInput = document.querySelector('input[type="file"]');
  const form = document.querySelector('.moment-form form');
  
  const previewContainer = document.getElementById('moment-preview');
  previewContainer.id = 'moment-preview';
  previewContainer.className = 'mb-3';
  form.insertBefore(previewContainer, form.querySelector('button[type="submit"]'));

  function clearPreview() {
    previewContainer.innerHTML = '';
  }

  function createMediaPreview(file) {
    clearPreview();
    const type = file.type;

    if (type.startsWith('image/')) {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.style.width = '160px';
      img.style.height = '160px';
      img.style.objectFit = 'cover';
      img.style.borderRadius = '0.5rem'; // roughly Tailwind's rounded
      img.style.marginBottom = '0.5rem';
      previewContainer.appendChild(img);
    } else if (type.startsWith('video/')) {
      const video = document.createElement('video');
      video.src = URL.createObjectURL(file);
      video.controls = true;
      video.style.width = '700px';
      video.style.height = '350px';
      video.style.objectFit = 'cover';
      video.style.borderRadius = '0.5rem'; // Tailwind's 'rounded'
      video.style.marginBottom = '0.5rem';
      video.setAttribute('muted', true);  // Optional: preload quietly
      video.setAttribute('playsinline', true);  // Fix for mobile
      previewContainer.appendChild(video);
    }
  }

  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        createMediaPreview(e.target.files[0]);
      }
    });
  }

  // === Drag & Drop Support ===
  const dropZone = form;
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('ring', 'ring-blue-400');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('ring', 'ring-blue-400');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('ring', 'ring-blue-400');
    if (e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      fileInput.files = e.dataTransfer.files;
      createMediaPreview(droppedFile);
    }
  });

window.flagMoment = function(momentId) {
  fetch(`/moments/flag/${momentId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  })
  .then(res => {
    if (!res.ok) {
      return res.text().then(text => {
        throw new Error(`Server error ${res.status}`);
      });
    }
    return res.json();
  })
  .then(data => {
    alert(data.status === 'flagged' ? 'Moment flagged!' : 'Already flagged.');
  })
  .catch(err => {
    alert("Error flagging moment: " + err.message);
  });
}


 
// === Ensure Description textarea allows paste and drop ===
  const descriptionInput = document.querySelector('textarea[name="content"], textarea#id_content');
  if (descriptionInput) {
    descriptionInput.removeAttribute('readonly');
    descriptionInput.removeAttribute('disabled');
    descriptionInput.addEventListener('paste', function(e) {
      // Do nothing, allow paste
    });
    // Add drop event to forward dropped YouTube links to Alpine.js
    descriptionInput.addEventListener('drop', function(e) {
      const droppedText = e.dataTransfer.getData('text');
      if (droppedText && window.Alpine && Alpine.store && Alpine.store('momentForm')) {
        // If Alpine store is used
        Alpine.store('momentForm').descriptionContent = droppedText;
      } else if (window.momentForm) {
        // If momentForm is global
        window.momentForm.descriptionContent = droppedText;
      } else {
        // Fallback: just insert text
        descriptionInput.value = droppedText;
      }
      // Let Alpine's x-model and handler take over
    });
  }

// === Fire Cooldown Timer ===
function showFireCooldown(btn, seconds) {
  // Use the existing .fire-cooldown-timer div above the fire button
  let timerDiv = btn.parentElement.querySelector('.fire-cooldown-timer');
  if (!timerDiv) {
    // Fallback: create if not present (should always exist from template)
    timerDiv = document.createElement('div');
    timerDiv.className = 'fire-cooldown-timer';
    btn.parentElement.insertBefore(timerDiv, btn);
  }
  function updateTimer() {
    if (seconds <= 0) {
      timerDiv.textContent = '';
      btn.disabled = false;
      btn.classList.remove('disabled');
      return;
    }
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    timerDiv.textContent = `🔥 Ready in ${min}:${sec.toString().padStart(2, '0')}`;
    seconds--;
    setTimeout(updateTimer, 1000);
  }
  btn.disabled = true;
  btn.classList.add('disabled');
  updateTimer();
}

// Patch event delegation for fire-btn to handle cooldown
function fireHandler(fireBtn) {
  const momentId = fireBtn.dataset.momentId;
  fetch(`/moments/react/fire/${momentId}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCSRFToken() },
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      fireBtn.innerText = `🔥 ${data.fire_count}`;
      showFireCooldown(fireBtn, data.cooldown_seconds);
    } else if (data.status === 'error' && data.cooldown_seconds !== undefined) {
      showFireCooldown(fireBtn, data.cooldown_seconds);
      alert(data.message);
    } else {
      alert(data.message);
    }
  });
}

// Update event delegation for fire-btn
document.body.addEventListener('click', function(e) {
  // Fire reaction
  const fireBtn = e.target.closest('.fire-btn');
  if (fireBtn) {
    fireHandler(fireBtn);
    return;
  }
  // Heart reaction
  const heartBtn = e.target.closest('.heart-btn');
  if (heartBtn) {
    console.log('Heart button clicked', heartBtn);
    const momentId = heartBtn.dataset.momentId;
    fetch(`/moments/react/heart/${momentId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCSRFToken() },
    })
    .then(res => res.json())
    .then(data => {
      console.log('Heart fetch response', data);
      if (data.status === 'liked' || data.status === 'unliked') {
        heartBtn.innerText = `❤️ ${data.heart_count}`;
      }
    });
    return;
  }
});
