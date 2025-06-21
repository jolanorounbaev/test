document.addEventListener('DOMContentLoaded', function() {
    // Utility function to get CSRF token
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

    // Show result message with animation
    function showResult(element, message, type) {
        element.textContent = message;
        element.className = `result-message ${type}`;
        element.style.display = 'block';
        
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }

    // Add loading state to button
    function setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.innerHTML = '<span class="loading-spinner"></span> Sending...';
        } else {
            button.disabled = false;
            button.innerHTML = 'Send Request';
        }
    }

    // Add friend by ID functionality
    const addFriendBtn = document.getElementById('add-friend-btn');
    const friendIdInput = document.getElementById('friend-id-input');
    const addFriendResult = document.getElementById('add-friend-result');

    if (addFriendBtn) {
        addFriendBtn.addEventListener('click', function() {
            const friendId = friendIdInput.value.trim();
            
            if (!friendId) {
                showResult(addFriendResult, 'Please enter a user ID', 'error');
                return;
            }

            if (!/^\d+$/.test(friendId)) {
                showResult(addFriendResult, 'User ID must be a number', 'error');
                return;
            }

            setButtonLoading(addFriendBtn, true);

            const formData = new FormData();
            formData.append('user_id', friendId);

            fetch('/friendsearch/send-friend-request/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                setButtonLoading(addFriendBtn, false);
                showResult(addFriendResult, data.message, data.success ? 'success' : 'error');
                if (data.success) {
                    friendIdInput.value = '';
                }
            })
            .catch(error => {
                setButtonLoading(addFriendBtn, false);
                console.error('Error:', error);
                showResult(addFriendResult, 'An error occurred. Please try again.', 'error');
            });
        });

        // Allow Enter key to send friend request
        friendIdInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addFriendBtn.click();
            }
        });
    }

    // Search friends functionality
    const friendSearchInput = document.getElementById('friend-search-input');
    const friendsSearchResults = document.getElementById('friends-search-results');
    const allFriendsContainer = document.getElementById('all-friends-list');

    if (friendSearchInput && friendsSearchResults) {
        friendSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.trim().toLowerCase();
            
            if (searchTerm.length === 0) {
                friendsSearchResults.innerHTML = '';
                return;
            }

            if (searchTerm.length < 2) {
                friendsSearchResults.innerHTML = '<div class="empty-state"><p>Type at least 2 characters to search...</p></div>';
                return;
            }

            // Filter friends client-side
            const allFriendCards = allFriendsContainer ? allFriendsContainer.querySelectorAll('.friend-card') : [];
            const matchingFriends = [];

            allFriendCards.forEach(card => {
                const nameElement = card.querySelector('.friend-name');
                const bioElement = card.querySelector('.friend-bio');
                
                if (nameElement) {
                    const name = nameElement.textContent.toLowerCase();
                    const bio = bioElement ? bioElement.textContent.toLowerCase() : '';
                    
                    if (name.includes(searchTerm) || bio.includes(searchTerm)) {
                        matchingFriends.push(card.cloneNode(true));
                    }
                }
            });

            friendsSearchResults.innerHTML = '';
            
            if (matchingFriends.length === 0) {
                friendsSearchResults.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🔍</div>
                        <div class="empty-state-title">No friends found</div>
                        <div class="empty-state-text">No friends match your search term "${searchTerm}"</div>
                    </div>
                `;
            } else {
                matchingFriends.forEach((card, index) => {
                    card.style.animationDelay = `${index * 0.1}s`;
                    card.classList.add('search-result');
                    friendsSearchResults.appendChild(card);
                });
            }
        });
    }

    // People search functionality  
    const peopleSearchInput = document.getElementById('people-search-input');
    const peopleSearchBtn = document.getElementById('people-search-btn');
    const peopleSearchResults = document.getElementById('people-search-results');

    if (peopleSearchBtn) {
        peopleSearchBtn.addEventListener('click', function() {
            const searchTerm = peopleSearchInput.value.trim();
            
            if (searchTerm.length < 2) {
                showResult(document.getElementById('people-search-result'), 'Please enter at least 2 characters', 'error');
                return;
            }

            setButtonLoading(peopleSearchBtn, true);
            peopleSearchBtn.innerHTML = '<span class="loading-spinner"></span> Searching...';

            fetch(`/friendsearch/search-people/?q=${encodeURIComponent(searchTerm)}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                peopleSearchBtn.innerHTML = 'Search People';
                peopleSearchBtn.disabled = false;
                
                peopleSearchResults.innerHTML = '';
                
                if (data.users && data.users.length > 0) {
                    data.users.forEach((user, index) => {
                        const userCard = createUserCard(user, index);
                        peopleSearchResults.appendChild(userCard);
                    });
                } else {
                    peopleSearchResults.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">👥</div>
                            <div class="empty-state-title">No users found</div>
                            <div class="empty-state-text">No users match your search term "${searchTerm}"</div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                peopleSearchBtn.innerHTML = 'Search People';
                peopleSearchBtn.disabled = false;
                console.error('Error:', error);
                peopleSearchResults.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <div class="empty-state-title">Error</div>
                        <div class="empty-state-text">An error occurred while searching. Please try again.</div>
                    </div>
                `;
            });
        });

        // Allow Enter key to search
        peopleSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                peopleSearchBtn.click();
            }
        });
    }

    // Helper function to create user card
    function createUserCard(user, index) {
        const card = document.createElement('div');
        card.className = 'friend-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        const avatarHtml = user.profile_picture 
            ? `<img src="${user.profile_picture}" alt="${user.full_name}">`
            : `<div class="default-avatar">${user.first_name.charAt(0).toUpperCase()}${user.last_name.charAt(0).toUpperCase()}</div>`;

        card.innerHTML = `
            <div class="friend-avatar">${avatarHtml}</div>
            <div class="friend-info">
                <h3 class="friend-name">${user.full_name}</h3>
                <p class="friend-bio">${user.bio || 'No bio yet'}</p>
                <div class="friend-actions">
                    <span class="friend-status">ID: ${user.id}</span>
                    <button class="btn btn-primary btn-sm" onclick="sendFriendRequestToUser(${user.id})">
                        Add Friend
                    </button>
                </div>
            </div>
        `;

        return card;
    }

    // Make sendFriendRequestToUser globally available
    window.sendFriendRequestToUser = function(userId) {
        const formData = new FormData();
        formData.append('user_id', userId);

        fetch('/friendsearch/send-friend-request/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Create a temporary result element for this specific action
            const tempResult = document.createElement('div');
            tempResult.className = `result-message ${data.success ? 'success' : 'error'}`;
            tempResult.textContent = data.message;
            tempResult.style.position = 'fixed';
            tempResult.style.top = '20px';
            tempResult.style.right = '20px';
            tempResult.style.zIndex = '1000';
            tempResult.style.padding = '15px 20px';
            tempResult.style.borderRadius = '8px';
            tempResult.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            
            document.body.appendChild(tempResult);
            
            setTimeout(() => {
                document.body.removeChild(tempResult);
            }, 3000);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    };    // Friend request notifications functionality
    function loadFriendRequests() {
        fetch('/friendsearch/friend-requests-json/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            const requestsContainer = document.getElementById('friend-requests-list');
            if (!requestsContainer) return;

            requestsContainer.innerHTML = '';
            
            if (data.requests && data.requests.length > 0) {
                data.requests.forEach((request, index) => {
                    const requestElement = createFriendRequestElement(request, index);
                    requestsContainer.appendChild(requestElement);
                });
            } else {
                requestsContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <div class="empty-state-title">No friend requests</div>
                        <div class="empty-state-text">You don't have any pending friend requests.</div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading friend requests:', error);
        });
    }

    // Helper function to create friend request element
    function createFriendRequestElement(request, index) {
        const element = document.createElement('div');
        element.className = 'notification-item';
        element.style.animationDelay = `${index * 0.1}s`;
        
        const avatarHtml = request.from_user.profile_picture 
            ? `<img src="${request.from_user.profile_picture}" alt="${request.from_user.full_name}">`
            : `<div class="default-avatar">${request.from_user.first_name.charAt(0).toUpperCase()}${request.from_user.last_name.charAt(0).toUpperCase()}</div>`;

        element.innerHTML = `
            <div class="notification-content">
                <div class="notification-avatar">${avatarHtml}</div>
                <div class="notification-text">
                    <strong>${request.from_user.full_name}</strong> sent you a friend request
                </div>
            </div>
            <div class="notification-actions">
                <button class="btn btn-primary btn-sm" onclick="respondToFriendRequest(${request.id}, 'accept')">
                    Accept
                </button>
                <button class="btn btn-secondary btn-sm" onclick="respondToFriendRequest(${request.id}, 'decline')">
                    Decline
                </button>
            </div>
        `;

        return element;
    }

    // Handle friend request responses
    window.respondToFriendRequest = function(requestId, action) {
        const url = action === 'accept' 
            ? `/notifications/accept-friend-request/${requestId}/`
            : `/notifications/decline-friend-request/${requestId}/`;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.ok) {
                // Reload friend requests and friends list
                loadFriendRequests();
                if (action === 'accept') {
                    location.reload(); // Refresh to show new friend in the list
                }
            }
        })
        .catch(error => {
            console.error('Error responding to friend request:', error);
        });
    };

    // Remove friend functionality
    window.removeFriend = function(friendId, friendName) {
        if (!confirm(`Are you sure you want to remove ${friendName} from your friends?`)) {
            return;
        }

        fetch(`/friendsearch/remove-friend/${friendId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the friend card from the DOM
                const friendCard = document.querySelector(`[data-friend-id="${friendId}"]`);
                if (friendCard) {
                    friendCard.style.opacity = '0';
                    friendCard.style.transform = 'translateY(-20px)';
                    setTimeout(() => {
                        friendCard.remove();
                        
                        // Check if there are no more friends
                        const remainingFriends = document.querySelectorAll('#all-friends-list .friend-card');
                        if (remainingFriends.length === 0) {
                            document.getElementById('all-friends-list').innerHTML = `
                                <div class="empty-state">
                                    <div class="empty-state-icon">👥</div>
                                    <div class="empty-state-title">No friends yet</div>
                                    <div class="empty-state-text">Start adding friends to build your network!</div>
                                </div>
                            `;
                        }
                    }, 300);
                }
            } else {
                alert(data.message || 'Failed to remove friend');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while removing the friend');
        });
    };

    // Load friend requests on page load
    if (document.getElementById('friend-requests-list')) {
        loadFriendRequests();
    }

    // Add smooth scrolling for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add intersection observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all cards for animation
    document.querySelectorAll('.section-card, .friend-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
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
