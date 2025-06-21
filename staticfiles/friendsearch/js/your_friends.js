// Modern Friends Management JavaScript
class FriendsManager {
    constructor() {
        this.notificationInterval = null;
        this.searchDebounceTimer = null;
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.loadNotifications();
        this.startNotificationPolling();
        this.animateCards();
    }

    bindEventListeners() {
        // Add friend by ID
        const addFriendBtn = document.getElementById('add-friend-btn');
        if (addFriendBtn) {
            addFriendBtn.addEventListener('click', () => this.addFriendById());
        }

        // Enter key for add friend input
        const addFriendInput = document.getElementById('friend-id-input');
        if (addFriendInput) {
            addFriendInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.addFriendById();
                }
            });
        }

        // Search friends
        const searchInput = document.getElementById('friend-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.searchFriends(e.target.value));
        }

        // Friends of friends search
        const friendOfFriendInput = document.getElementById('friend-of-friend-input');
        if (friendOfFriendInput) {
            friendOfFriendInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchFriendsOfFriends(e.target.value);
                }
            });
        }

        // Remove friend buttons
        this.bindRemoveFriendButtons();

        // Refresh notifications button
        const refreshBtn = document.getElementById('refresh-notifications');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadNotifications());
        }
    }

    bindRemoveFriendButtons() {
        document.querySelectorAll('.btn-remove-friend').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const friendId = e.target.dataset.friendId;
                const friendName = e.target.dataset.friendName;
                this.removeFriend(friendId, friendName);
            });
        });
    }

    async addFriendById() {
        const input = document.getElementById('friend-id-input');
        const resultDiv = document.getElementById('add-friend-result');
        const button = document.getElementById('add-friend-btn');
        
        const friendId = input.value.trim();
        
        if (!friendId) {
            this.showResult(resultDiv, 'Please enter a user ID', 'error');
            return;
        }

        // Show loading state
        const originalText = button.textContent;
        button.innerHTML = '<span class="loading-spinner"></span> Sending...';
        button.disabled = true;

        try {
            const response = await fetch('/friendsearch/send-friend-request/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: new URLSearchParams({
                    'user_id': friendId
                }),
                credentials: 'same-origin'
            });

            const text = await response.text();
            const data = JSON.parse(text);
            
            if (data.success) {
                input.value = '';
                this.showResult(resultDiv, data.message, 'success');
            } else {
                this.showResult(resultDiv, data.message, 'error');
            }
        } catch (error) {
            console.error('Error sending friend request:', error);
            this.showResult(resultDiv, 'Network error. Please try again.', 'error');
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    searchFriends(searchTerm) {
        clearTimeout(this.searchDebounceTimer);
        
        this.searchDebounceTimer = setTimeout(() => {
            const resultsContainer = document.getElementById('friends-search-results');
            const friendsList = document.getElementById('your-friends-list');
            
            if (!resultsContainer || !friendsList) return;

            if (searchTerm.length < 2) {
                resultsContainer.innerHTML = '';
                resultsContainer.style.display = 'none';
                return;
            }

            resultsContainer.style.display = 'block';
            const searchTermLower = searchTerm.toLowerCase();
            const allFriends = friendsList.querySelectorAll('.friend-card');
            const matches = [];

            allFriends.forEach(friendCard => {
                const nameElement = friendCard.querySelector('.friend-name');
                const bioElement = friendCard.querySelector('.friend-bio');
                
                if (nameElement) {
                    const name = nameElement.textContent.toLowerCase();
                    const bio = bioElement ? bioElement.textContent.toLowerCase() : '';
                    
                    if (name.includes(searchTermLower) || bio.includes(searchTermLower)) {
                        matches.push(friendCard.cloneNode(true));
                    }
                }
            });

            if (matches.length > 0) {
                resultsContainer.innerHTML = `
                    <div class="search-results-header">
                        <span class="results-count">${matches.length} friend${matches.length === 1 ? '' : 's'} found</span>
                        <button class="clear-results" onclick="friendsManager.clearSearchResults()">Clear</button>
                    </div>
                    <div class="friends-grid"></div>
                `;
                
                const grid = resultsContainer.querySelector('.friends-grid');
                matches.forEach((match, index) => {
                    match.style.setProperty('--order', index);
                    grid.appendChild(match);
                });
                
                // Re-bind remove buttons for cloned elements
                this.bindRemoveFriendButtons();
            } else {
                resultsContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🔍</div>
                        <h3>No friends found</h3>
                        <p>No friends match your search for "${searchTerm}"</p>
                    </div>
                `;
            }
        }, 300);
    }

    clearSearchResults() {
        const resultsContainer = document.getElementById('friends-search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
            resultsContainer.style.display = 'none';
        }
        
        const searchInput = document.getElementById('friend-search-input');
        if (searchInput) {
            searchInput.value = '';
        }
    }

    async searchFriendsOfFriends(friendName) {
        const resultsContainer = document.getElementById('friends-of-friends-results');
        
        if (!friendName.trim()) {
            resultsContainer.innerHTML = '';
            return;
        }

        resultsContainer.innerHTML = `
            <div class="loading-state">
                <span class="loading-spinner"></span> Loading ${friendName}'s friends...
            </div>
        `;

        try {
            // Simulate API call - replace with actual endpoint
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // For demo purposes, showing some mock data
            // In a real app, you would make an actual API call here
            resultsContainer.innerHTML = `
                <div class="search-results-header">
                    <span class="results-count">Friends of ${friendName}</span>
                </div>
                <div class="empty-state">
                    <div class="empty-state-icon">👥</div>
                    <h3>Feature Coming Soon</h3>
                    <p>Friends of friends viewing will be available in a future update</p>
                </div>
            `;
        } catch (error) {
            console.error('Error searching friends of friends:', error);
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <h3>Error</h3>
                    <p>Could not load friends of ${friendName}</p>
                </div>
            `;
        }
    }

    async removeFriend(friendId, friendName) {
        if (!confirm(`Are you sure you want to remove ${friendName} from your friends?`)) {
            return;
        }

        const friendCard = document.querySelector(`[data-friend-id="${friendId}"]`);
        if (!friendCard) return;

        try {
            const response = await fetch(`/friendsearch/remove-friend/${friendId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                // Animate removal
                friendCard.style.transform = 'scale(0)';
                friendCard.style.opacity = '0';
                
                setTimeout(() => {
                    friendCard.remove();
                    this.updateFriendsCount();
                }, 300);
                
                this.showToast(`${friendName} has been removed from your friends`, 'success');
            } else {
                this.showToast(data.message || 'Failed to remove friend', 'error');
            }
        } catch (error) {
            console.error('Error removing friend:', error);
            this.showToast('Network error. Please try again.', 'error');
        }
    }

    async loadNotifications() {
        const notificationsContainer = document.getElementById('friend-requests-container');
        const notificationBadge = document.querySelector('.notification-badge');
        
        if (!notificationsContainer) return;

        try {
            const response = await fetch('/notifications/friend-requests/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error('Failed to load notifications');
            
            const data = await response.json();
            
            if (data.requests && data.requests.length > 0) {
                notificationsContainer.innerHTML = data.requests.map(request => `
                    <div class="friend-request-card" data-request-id="${request.id}">
                        <div class="request-header">
                            <div class="request-avatar">
                                ${request.from_user.profile_picture ? 
                                    `<img src="${request.from_user.profile_picture}" alt="${request.from_user.name}">` :
                                    `<div class="default-avatar">${request.from_user.name.charAt(0).toUpperCase()}</div>`
                                }
                            </div>
                            <div class="request-info">
                                <h4>${request.from_user.name}</h4>
                                <p class="request-time">${this.formatTime(request.timestamp)}</p>
                            </div>
                        </div>
                        <div class="request-actions">
                            <button class="btn btn-success" onclick="friendsManager.acceptFriendRequest(${request.id})">
                                Accept
                            </button>
                            <button class="btn btn-secondary" onclick="friendsManager.declineFriendRequest(${request.id})">
                                Decline
                            </button>
                        </div>
                    </div>
                `).join('');
                
                if (notificationBadge) {
                    notificationBadge.textContent = data.requests.length;
                    notificationBadge.style.display = 'flex';
                }
            } else {
                notificationsContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📬</div>
                        <h3>No pending requests</h3>
                        <p>You don't have any pending friend requests</p>
                    </div>
                `;
                
                if (notificationBadge) {
                    notificationBadge.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            notificationsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <h3>Error</h3>
                    <p>Could not load friend requests</p>
                </div>
            `;
        }
    }

    async acceptFriendRequest(requestId) {
        await this.handleFriendRequest(requestId, 'accept');
    }

    async declineFriendRequest(requestId) {
        await this.handleFriendRequest(requestId, 'decline');
    }

    async handleFriendRequest(requestId, action) {
        const requestCard = document.querySelector(`[data-request-id="${requestId}"]`);
        if (!requestCard) return;

        try {
            const response = await fetch(`/notifications/${action}-friend-request/${requestId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                }
            });

            if (response.ok) {
                // Animate removal
                requestCard.style.transform = 'translateX(100%)';
                requestCard.style.opacity = '0';
                
                setTimeout(() => {
                    requestCard.remove();
                    this.loadNotifications(); // Refresh to update badge
                }, 300);
                
                const message = action === 'accept' ? 'Friend request accepted!' : 'Friend request declined';
                this.showToast(message, 'success');
                
                if (action === 'accept') {
                    // Refresh friends list to show new friend
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                this.showToast('Failed to process request', 'error');
            }
        } catch (error) {
            console.error(`Error ${action}ing friend request:`, error);
            this.showToast('Network error. Please try again.', 'error');
        }
    }

    startNotificationPolling() {
        // Poll for new notifications every 30 seconds
        this.notificationInterval = setInterval(() => {
            this.loadNotifications();
        }, 30000);
    }

    stopNotificationPolling() {
        if (this.notificationInterval) {
            clearInterval(this.notificationInterval);
        }
    }

    animateCards() {
        const cards = document.querySelectorAll('.friend-card');
        cards.forEach((card, index) => {
            card.style.setProperty('--order', index);
        });
    }

    updateFriendsCount() {
        const friendsList = document.getElementById('your-friends-list');
        const countElement = document.querySelector('.section-count');
        
        if (friendsList && countElement) {
            const count = friendsList.querySelectorAll('.friend-card').length;
            countElement.textContent = count;
        }
    }

    showResult(element, message, type) {
        if (!element) return;
        
        element.textContent = message;
        element.className = `result-message ${type}`;
        element.style.display = 'block';
        
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }

    showToast(message, type = 'info') {
        // Create toast if it doesn't exist
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius-md);
                padding: 1rem 1.5rem;
                box-shadow: var(--shadow-lg);
                z-index: 1000;
                transform: translateX(100%);
                transition: transform 0.3s ease;
                max-width: 300px;
            `;
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.className = `result-message ${type}`;
        
        // Show toast
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Hide toast after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
        }, 3000);
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }

    getCookie(name) {
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
}

// Initialize the friends manager when the page loads
let friendsManager;
document.addEventListener('DOMContentLoaded', function() {
    friendsManager = new FriendsManager();
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (friendsManager) {
        friendsManager.stopNotificationPolling();
    }
});
    
    friendSearchInput.addEventListener('input', function() {
        const searchTerm = this.value.trim().toLowerCase();
        
        if (searchTerm.length < 2) {
            friendsSearchResults.innerHTML = '';
            return;
        }
        
        // Filter friends client-side (or make AJAX call to server)
        const allFriends = document.querySelectorAll('#your-friends-list .friend-card');
        friendsSearchResults.innerHTML = '';
        
        let delay = 0;
        allFriends.forEach(friend => {
            const name = friend.querySelector('.friend-info h3').textContent.toLowerCase();
            if (name.includes(searchTerm)) {
                const clone = friend.cloneNode(true);
                clone.style.setProperty('--order', delay);
                friendsSearchResults.appendChild(clone);
                delay++;
            }
        });
    });
    
    // Friends of friends search
    const friendOfFriendInput = document.getElementById('friend-of-friend-input');
    const selectedFriendDiv = document.getElementById('selected-friend');
    const friendsOfFriendsResults = document.getElementById('friends-of-friends-results');
    
    friendOfFriendInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const searchTerm = this.value.trim();
            
            if (searchTerm.length < 2) {
                return;
            }
            
            // In a real app, you would make an AJAX call here to get the friend's friends
            // For demo, we'll simulate it with your current friends
            selectedFriendDiv.style.display = 'block';
            selectedFriendDiv.innerHTML = `
                <h3>${searchTerm}</h3>
                <p>Showing friends of ${searchTerm}</p>
            `;
            
            friendsOfFriendsResults.innerHTML = '';
            
            // Simulate loading friends of friends with a delay
            setTimeout(() => {
                // Again, in a real app, you would use actual data from the server
                const allFriends = document.querySelectorAll('#your-friends-list .friend-card');
                
                allFriends.forEach((friend, index) => {
                    setTimeout(() => {
                        const clone = friend.cloneNode(true);
                        clone.style.setProperty('--order', index);
                        friendsOfFriendsResults.appendChild(clone);
                    }, index * 100);
                });
            }, 500);                    
        }
    });
    
    // Remove friend
    document.querySelectorAll('.btn-remove').forEach(btn => {
        btn.addEventListener('click', function() {
            const friendId = this.dataset.id;
            if (confirm('Are you sure you want to remove this friend?')) {
                fetch('/friendsearch/remove-friend/' + friendId + '/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.closest('.friend-card').remove();
                    } else {
                        alert(data.message);
                    }
                });
            }
        });
    });
    
    function showResult(element, message, type) {
        element.textContent = message;
        element.className = 'result-message ' + type;
        element.style.display = 'block';
        
        setTimeout(() => {
            element.style.display = 'none';
        }, 3000);
    }

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

window.copyUserId = function () {
  const userId = document.getElementById("user-id-code").dataset.id;
  navigator.clipboard.writeText(userId).then(() => {
    showCopyToast();
  });
}

function showCopyToast() {
  const toast = document.getElementById("copy-toast");
  toast.classList.remove("hidden");
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
    toast.classList.add("hidden");
  }, 2500); // Toast disappears after 2.5 seconds
}
