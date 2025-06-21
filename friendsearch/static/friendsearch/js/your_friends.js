document.addEventListener('DOMContentLoaded', function () {
    // Add friend by ID
    document.getElementById('add-friend-btn').addEventListener('click', function () {
        const friendId = document.getElementById('friend-id-input').value.trim();
        const resultDiv = document.getElementById('add-friend-result');

        if (!friendId) {
            showResult(resultDiv, 'Please enter a user ID', 'error');
            return;
        }

        fetch('/friendsearch/send-friend-request/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({
                'user_id': friendId
            }),
            credentials: 'same-origin'
        })
        .then(response => response.text())
        .then(text => {
            try {
                const data = JSON.parse(text);
                
                if (data.success) {
                    // Clear the input field on success
                    document.getElementById('friend-id-input').value = '';
                }
                
                showResult(resultDiv, data.message, data.success ? 'success' : 'error');
            } catch (e) {
                showResult(resultDiv, 'Server did not return JSON: ' + text, 'error');
            }
        });
    });
});



    
    // Search your friends
    const friendSearchInput = document.getElementById('friend-search-input');
    const friendsSearchResults = document.getElementById('friends-search-results');
    
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
