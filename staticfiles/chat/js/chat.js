document.addEventListener('DOMContentLoaded', () => {
    console.log("Chat script initialized");
    
    const sendButton = document.getElementById('send-button');
    const inputField = document.getElementById('message-input');
    const messageArea = document.getElementById('messages-container');
    const roomId = ACTIVE_ROOM_ID;
    const userId = CURRENT_USER_ID;

    if (!roomId) {
        console.log("No active room selected");
        sendButton.disabled = true;
        return;
    }

    // Connection management
    let chatSocket;
    let retryCount = 0;
    const maxRetries = 5;
    const retryDelay = 2000;
    let isConnected = false;
    
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = protocol + window.location.host + `/ws/chat/${roomId}/`;
        
        chatSocket = new WebSocket(wsUrl);

        chatSocket.onopen = function(e) {
            console.log("✅ WebSocket connected");
            isConnected = true;
            retryCount = 0;
            updateUIState('connected');
        };

chatSocket.onmessage = async function(e) {
    console.log("📩 Message received:", e.data);
    try {
        const data = JSON.parse(e.data);
        if (data.type === 'error') {
            console.error("Server error:", data.error);
            showError(data.error);
        } else if (data.type === 'chat_message') {
            // ✅ Remove any pending version of this message if from same sender
            if (data.sender_id == userId) {
                document.querySelectorAll('.message.pending').forEach(el => el.remove());
            }
            await appendMessage(data);
            // Play notification sound if message is received (not sent by current user)
            if (data.sender_id != userId) {
                const notifAudio = document.getElementById('notificationSound');
                if (notifAudio) notifAudio.play();
            }
        }
    } catch (error) {
        console.error("Error parsing message:", error);
    }
};


        chatSocket.onerror = function(e) {
            console.error("❌ WebSocket error:", e);
            isConnected = false;
            updateUIState('error');
        };

        chatSocket.onclose = function(e) {
            console.warn(`⚠️ WebSocket closed (code ${e.code})`);
            isConnected = false;
            
            if (e.code === 4001) {
                showError("Authentication failed");
                return;
            }
            
            if (retryCount < maxRetries) {
                retryCount++;
                console.log(`Retrying connection (${retryCount}/${maxRetries})...`);
                updateUIState('reconnecting');
                setTimeout(connectWebSocket, retryDelay * retryCount);
            } else {
                updateUIState('disconnected');
            }
        };
    }

    function updateUIState(state) {
        switch(state) {
            case 'connected':
                sendButton.disabled = false;
                sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
                break;
            case 'reconnecting':
                sendButton.disabled = true;
                sendButton.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Reconnecting...';
                break;
            case 'disconnected':
                sendButton.disabled = true;
                sendButton.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Disconnected';
                break;
            case 'error':
                sendButton.disabled = true;
                sendButton.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error';
                break;
        }
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chat-error';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        `;
        messageArea.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }        async function appendMessage(data) {
        console.log("appendMessage called with data:", data); // Debug log
        
        // Check if sender is blocked (for real-time messages)
        if (!data.hasOwnProperty('is_blocked') && data.sender_id != userId) {
            data.is_blocked = await isUserBlocked(data.sender_id);
        }
          const messageDiv = document.createElement('div');
        if (data.message_id) {
            messageDiv.id = `message-${data.message_id}`;
        }
        messageDiv.classList.add('message');
        messageDiv.classList.add(data.sender_id == userId ? 'sent' : 'received');
        messageDiv.dataset.senderId = data.sender_id; // Add sender ID for blocking refresh
        if (data.pending) messageDiv.classList.add('pending');

        if (data.sender_id != userId) {
            const avatarDiv = document.createElement('div');
            avatarDiv.classList.add('message-avatar');
            const avatarUrl = data.sender_profile_picture ? data.sender_profile_picture : '/static/img/default-avatar.png';
            avatarDiv.innerHTML = `<img src="${avatarUrl}" alt="${data.username || 'User'}">`;            messageDiv.appendChild(avatarDiv);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
          // Reply preview (visual distinction) - Discord/Messenger style
        if (data.reply_to_message) {
            const replyPreview = document.createElement('div');
            replyPreview.className = 'reply-preview-in-message';
            
            // Show who was replied to and a preview of their message
            const replyAuthor = data.reply_to_user || 'Unknown User';
            let originalMessage;
            
            // Check if the replied message is from a blocked user
            if (data.is_blocked && data.sender_id != userId) {
                originalMessage = 'Blocked message';
            } else {
                originalMessage = data.reply_to_message.length > 50 
                    ? data.reply_to_message.substring(0, 50) + '...' 
                    : data.reply_to_message;
            }
            
            replyPreview.innerHTML = `
                <span class="reply-label">Replying to ${replyAuthor}</span>
                <span class="reply-original">${originalMessage}</span>
            `;
            contentDiv.appendChild(replyPreview);
        }

        if (data.sender_id != userId) {
            const nameSpan = document.createElement('span');
            nameSpan.classList.add('message-sender');
            nameSpan.textContent = data.username || 'Unknown';
            contentDiv.appendChild(nameSpan);
        }        const bubbleDiv = document.createElement('div');
        bubbleDiv.classList.add('message-bubble');
        
        // Check if message is blocked and sender is not current user
        if (data.is_blocked && data.sender_id != userId) {
            bubbleDiv.classList.add('blocked-message');
            bubbleDiv.textContent = 'Blocked message';
        } else {
            bubbleDiv.textContent = data.message;
        }

        const timeSpan = document.createElement('span');
        timeSpan.classList.add('message-time');
        timeSpan.textContent = data.timestamp ? 
            new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 
            'Just now';

        if (data.pending) {
            const spinner = document.createElement('span');
            spinner.classList.add('message-spinner');
            spinner.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
            timeSpan.appendChild(spinner);
        }

        contentDiv.appendChild(bubbleDiv);
        contentDiv.appendChild(timeSpan);

        // Add message actions (reply/delete) for all messages
        if (data.message_id) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';
            let actionsHtml = `<button class="dots-btn" type="button" style="color:#888;font-size:1.5rem;background:none;border:none;cursor:pointer;" onclick="toggleDropdown(${data.message_id})">&hellip;</button>`;
            actionsHtml += `<div class="dropdown-menu" id="dropdown-${data.message_id}" style="display:none;position:absolute;z-index:10;background:#fff;border:1px solid #ccc;padding:4px 0;box-shadow:0 2px 8px rgba(0,0,0,0.08);right:0;top:28px;min-width:100px;">`;
            actionsHtml += `<button style="width:100%;text-align:left;padding:6px 16px;background:none;border:none;cursor:pointer;" onclick=\"replyToMessage('${data.message_id}')\">💬 Reply</button>`;
            if (data.sender_id == userId) {
                actionsHtml += `<button style="width:100%;text-align:left;padding:6px 16px;background:none;border:none;cursor:pointer;color:#d9534f;" onclick=\"deleteMessage('${data.message_id}')\">🗑️ Delete</button>`;
            }
            actionsHtml += `</div>`;
            actionsDiv.innerHTML = actionsHtml;
            actionsDiv.style.position = 'relative';
            contentDiv.appendChild(actionsDiv);
        }

        messageDiv.appendChild(contentDiv);
        
        // Remove any pending messages from the same user
        if (data.pending) {
            document.querySelectorAll('.message.pending').forEach(el => el.remove());
        }
        
        messageArea.appendChild(messageDiv);
        messageArea.scrollTop = messageArea.scrollHeight;
    }


function sendMessage() {
    const message = inputField.value.trim();
    const file = document.getElementById('media-upload').files[0];  // ✅ moved here
    const replyText = document.getElementById('reply-text').dataset.replyTo || null;
    if (!message && !file) return;

    if (file) {
        const formData = new FormData();
        formData.append('message', message);
        if (file.type.startsWith('image/')) {
            formData.append('image', file);
        } else if (file.type === 'video/mp4') {
            formData.append('video', file);
        }

        fetch(`/chat/send/${roomId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                inputField.value = '';
                document.getElementById('media-upload').value = '';
                const previewArea = document.getElementById('preview-area');
                if (previewArea) previewArea.innerHTML = '';
                location.reload();  // for now
            }
        })
        .catch(err => {
            console.error("Upload error:", err);
            showError("Media upload failed.");
        });

        return;
    }

    // Text-only message via WebSocket
    if (!isConnected) {
        showError("Not connected to server");
        return;
    }

    const messageData = {
        'message': message,
        'sender_id': userId,
        'reply_to': replyText
    };

    try {
        chatSocket.send(JSON.stringify(messageData));        appendMessage({
            message: message,
            sender_id: userId,
            timestamp: new Date().toISOString(),
            username: "You",
            pending: true,
            reply_to_message: replyText ? document.getElementById(`message-${replyText}`)?.querySelector('.message-bubble')?.textContent : null,
            reply_to_user: replyText ? document.getElementById(`message-${replyText}`)?.querySelector('.message-sender')?.textContent || 'User' : null
        });
        inputField.value = '';
        cancelReply();  
    } catch (e) {
        console.error("WebSocket error:", e);
        showError("Failed to send message");
    }
}

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // --- Conversation Search Filter ---
    const searchInput = document.getElementById('chat-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const term = this.value.trim().toLowerCase();
            // Filter direct messages
            document.querySelectorAll('.contacts-section ul.contacts-list').forEach(list => {
                list.querySelectorAll('li.contact').forEach(li => {
                    const name = li.querySelector('.contact-name');
                    if (!name) return;
                    if (name.textContent.toLowerCase().includes(term)) {
                        li.style.display = '';
                    } else {
                        li.style.display = 'none';
                    }
                });
            });
        });
    }

    // Initial connection
    connectWebSocket();
});


// IMAGES AND VIDEOS

document.addEventListener('DOMContentLoaded', function () {

  // ✅ Enable drag-and-drop image/video upload
document.addEventListener('dragover', function (e) {
  e.preventDefault();
});

document.addEventListener('drop', function (e) {
  e.preventDefault();

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    const file = files[0];
    const mediaInput = document.getElementById('media-upload');

    // Set the dropped file into the input
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    mediaInput.files = dataTransfer.files;

    // Trigger preview manually
    mediaInput.dispatchEvent(new Event('change'));
  }
});
  
  const sendButton = document.getElementById('send-button');
  const messageInput = document.getElementById('message-input');
  const mediaInput = document.getElementById('media-upload');
  const previewArea = document.getElementById('preview-area');

  function resetPreview() {
    previewArea.innerHTML = '';
  }

  mediaInput.addEventListener('change', function () {
    resetPreview();

    const file = this.files[0];
    if (!file) return;

    const fileURL = URL.createObjectURL(file);
    const mediaType = file.type;

    let element;
    if (mediaType.startsWith('image/')) {
      element = document.createElement('img');
      element.src = fileURL;
      element.className = 'preview-image';
    } else if (mediaType === 'video/mp4') {
      element = document.createElement('video');
      element.src = fileURL;
      element.className = 'preview-video';
      element.controls = true;
    }

    if (element) {
      previewArea.appendChild(element);
    }
  });



// Function to check if user is blocked via AJAX
async function isUserBlocked(userId) {
    try {
        const response = await fetch('/chat/check-blocked-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken')
            },
            body: `user_id=${userId}`
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.is_blocked || false;
        }
    } catch (error) {
        console.error('Error checking blocked status:', error);
    }
    return false;
}

// Helper function to get CSRF cookie
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

  });


  function zoomImage(src) {
  const modal = document.getElementById("imagePreviewModal");
  const modalImg = document.getElementById("zoomedImage");
  modal.style.display = "block";
  modalImg.src = src;
}

function closeZoom() {
  document.getElementById("imagePreviewModal").style.display = "none";
}


function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function deleteMessage(messageId) {
    if (!confirm("Delete this message?")) return;

    fetch(`/chat/delete-message/${messageId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
    })    .then(res => res.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`message-${messageId}`).remove();
        } else {
            console.error("Delete failed:", data.error);
        }
    });
}

function getCSRFToken() {
  const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
  return tokenInput ? tokenInput.value : '';
}


function toggleDropdown(messageId) {
  // Close all dropdowns
  document.querySelectorAll(".dropdown-menu").forEach(el => el.style.display = "none");

  // Toggle the selected one
  const dropdown = document.getElementById(`dropdown-${messageId}`);
  if (dropdown) {
    dropdown.style.display = "block";
  }
}

// Optional: close dropdown when clicking elsewhere
document.addEventListener("click", function(e) {
  if (!e.target.closest(".message-actions")) {
    document.querySelectorAll(".dropdown-menu").forEach(el => el.style.display = "none");
  }
});


function replyToMessage(messageId) {
  const original = document.getElementById(`message-${messageId}`);
  if (!original) return;

  const previewBox = document.getElementById('reply-preview');
  const replyTextSpan = document.getElementById('reply-text');
  
  const bubble = original.querySelector('.message-bubble');
  const text = bubble ? bubble.textContent : '(media)';
  
  // Get the sender's name from the message
  const senderElement = original.querySelector('.message-sender');
  const senderName = senderElement ? senderElement.textContent : 'User';

  replyTextSpan.innerHTML = `<strong>Replying to ${senderName}:</strong> ${text.slice(0, 50)}${text.length > 50 ? '...' : ''}`;
  replyTextSpan.dataset.replyTo = messageId;
  previewBox.style.display = 'block';
}

function cancelReply() {
  const preview = document.getElementById('reply-preview');
  preview.style.display = 'none';
  const replyText = document.getElementById('reply-text');
  replyText.textContent = '';
  replyText.removeAttribute('data-reply-to');
}

// Function to refresh all chat messages (update blocking status)
window.refreshChatMessages = async function() {
    console.log('Refreshing chat messages due to blocking event...');
    
    // Get all existing message elements
    const messages = document.querySelectorAll('.message');
    
    for (const messageEl of messages) {
        const senderId = messageEl.dataset.senderId;
        
        // Skip if no sender ID or if it's the current user's message
        if (!senderId || senderId == userId) continue;
        
        try {
            // Check if this user is now blocked
            const isBlocked = await isUserBlocked(senderId);
            
            // Update the message bubble
            const bubble = messageEl.querySelector('.message-bubble');
            if (bubble) {
                if (isBlocked) {
                    bubble.classList.add('blocked-message');
                    bubble.textContent = 'Blocked message';
                } else {
                    bubble.classList.remove('blocked-message');
                    // Restore original message - we need to reload it from server
                    // For now, we'll just reload the entire chat
                    window.location.reload();
                    return;
                }
            }
            
            // Update reply previews if they exist
            const replyPreview = messageEl.querySelector('.reply-preview');
            if (replyPreview) {
                const originalSpan = replyPreview.querySelector('.reply-original');
                if (originalSpan && isBlocked) {
                    originalSpan.textContent = 'Blocked message';
                }
            }
            
        } catch (error) {
            console.error('Error checking blocking status:', error);
        }
    }
};

// Function to update chat sidebar when blocking events occur
window.updateChatSidebar = function() {
    console.log('Updating chat sidebar due to blocking event...');
    
    // Find all sidebar chat items
    const sidebarItems = document.querySelectorAll('.chat-sidebar-item, .sidebar-chat-item');
    
    sidebarItems.forEach(async (item) => {
        const senderId = item.dataset.senderId || item.dataset.userId;
        
        if (!senderId || senderId == userId) return;
        
        try {
            const isBlocked = await isUserBlocked(senderId);
            
            // Update preview message if blocked
            const previewEl = item.querySelector('.chat-preview, .last-message, .message-preview');
            if (previewEl && isBlocked) {
                previewEl.textContent = 'Blocked message';
                previewEl.classList.add('blocked-message');
            } else if (previewEl && !isBlocked) {
                previewEl.classList.remove('blocked-message');
                // Would need to restore original text - for now reload
                setTimeout(() => window.location.reload(), 100);
            }
            
        } catch (error) {
            console.error('Error updating sidebar item:', error);
        }
    });
};
