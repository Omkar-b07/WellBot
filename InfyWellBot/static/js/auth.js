document.addEventListener('DOMContentLoaded', () => {
    // ... (loginForm handler remains the same) ...
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const logoutButton = document.getElementById('logoutButton');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');

    // --- Login Handler ---
    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent default form submission
            errorMessage.textContent = ''; // Clear previous errors

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/login', { // Call our Flask API endpoint
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password }),
                });

                const data = await response.json();

                if (response.ok) {
                    // Login successful! Flask sets the cookie automatically.
                    // Redirect to the chat page
                    window.location.href = '/chat_page';
                } else {
                    errorMessage.textContent = data.msg || 'Login failed.';
                }
            } catch (error) {
                console.error('Login error:', error);
                errorMessage.textContent = 'An error occurred during login.';
            }
        });
    }

    // --- Registration Handler (UPDATED) ---
    if (registerForm) {
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            errorMessage.textContent = '';
            successMessage.textContent = '';

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            // --- GET NEW VALUES ---
            const age_group = document.getElementById('age_group').value;
            const preferred_language = document.getElementById('preferred_language').value;
            // --- END GET NEW VALUES ---

            // --- Basic validation ---
            if (!age_group) {
                errorMessage.textContent = 'Please select an age group.';
                return;
            }
            // --- End basic validation ---

            try {
                const response = await fetch('/register', { // Call Flask API
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    // --- SEND NEW VALUES ---
                    body: JSON.stringify({ email, password, age_group, preferred_language }),
                    // --- END SEND NEW VALUES ---
                });

                const data = await response.json();

                if (response.ok) {
                    successMessage.textContent = 'Registration successful! Please login.';
                    registerForm.reset(); // Clear the form
                } else {
                    errorMessage.textContent = data.msg || 'Registration failed.';
                }
            } catch (error) {
                console.error('Registration error:', error);
                errorMessage.textContent = 'An error occurred during registration.';
            }
        });
    }

    // --- Logout Handler ---
    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
             try {
                const response = await fetch('/logout', { method: 'POST' });
                if (response.ok) {
                    // Redirect to login after successful logout
                    window.location.href = '/login_page';
                } else {
                    alert('Logout failed.');
                }
            } catch (error) {
                console.error('Logout error:', error);
                alert('An error occurred during logout.');
            }
        });
    }

    // --- Profile Update Handler (NEW - for profile.html later) ---
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
         // Function to load current profile data
        const loadProfile = async () => {
            try {
                const response = await fetch('/profile'); // GET request, uses cookie
                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('emailDisplay').textContent = data.email || 'N/A';
                    document.getElementById('edit_age_group').value = data.age_group || '';
                    document.getElementById('edit_preferred_language').value = data.preferred_language || 'en';
                } else {
                     document.getElementById('profileErrorMessage').textContent = 'Could not load profile.';
                }
            } catch (error) {
                 document.getElementById('profileErrorMessage').textContent = 'Error loading profile.';
                 console.error("Load profile error:", error);
            }
        };

        // Load profile data when the page loads
        loadProfile();

        // Handle form submission for updates
        profileForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const age_group = document.getElementById('edit_age_group').value;
            const preferred_language = document.getElementById('edit_preferred_language').value;
            const successMsg = document.getElementById('profileSuccessMessage');
            const errorMsg = document.getElementById('profileErrorMessage');
            successMsg.textContent = '';
            errorMsg.textContent = '';


            try {
                const response = await fetch('/profile', { // PUT request, uses cookie
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ age_group, preferred_language }),
                });
                 if (response.ok) {
                    successMsg.textContent = 'Profile updated successfully!';
                } else {
                    const data = await response.json();
                    errorMsg.textContent = data.msg || 'Update failed.';
                }
            } catch(error) {
                errorMsg.textContent = 'Error updating profile.';
                console.error("Update profile error:", error);
            }
        });
    }
    // --- END Profile Update Handler ---
});
