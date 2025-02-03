const email = document.getElementById('email');
const password = document.getElementById('password');

// Add focus animation to input fields
email.addEventListener('focus', () => {
    email.classList.add('focused');
});
password.addEventListener('focus', () => {
    password.classList.add('focused');
});