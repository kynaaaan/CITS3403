$(document).ready(function() {
    // 1. Handle Profile Form Submission
    $('#profileForm').on('submit', function(e) {
        e.preventDefault();
        alert('Profile updated successfully!');
        // Later, you'll add an AJAX call here to save to the Flask backend
    });

    // 2. Visibility Toggle Logic
    $('#visibilityToggle').on('change', function() {
        const isPublic = $(this).is(':checked');
        console.log("Profile visibility set to: " + (isPublic ? "Public" : "Private"));
        // You could show a small toast notification here
    });

    // 3. Simple animation for XP bar on page load
    $('.xp-bar-fill').css('width', '0%');
    setTimeout(function() {
        $('.xp-bar-fill').css('width', '65%');
    }, 500);
});