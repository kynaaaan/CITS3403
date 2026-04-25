/*
   review.js — Star rating widget for write_review.html.

   Click a star → fills in that star and all to its left, updates the hidden
   #starRatingInput so the form submits the chosen value as `star_rating`.

   Craving tags use Bootstrap's native btn-check pattern (checkbox + styled
   label) and need no JS — the browser handles toggle state and form
   submission automatically.
*/

document.addEventListener('DOMContentLoaded', function () {
    const stars = document.querySelectorAll('#stars i');
    const ratingInput = document.getElementById('starRatingInput');
    if (!stars.length || !ratingInput) return;

    let selectedRating = 0;

    stars.forEach(function (star) {
        star.style.cursor = 'pointer';

        star.addEventListener('click', function () {
            selectedRating = parseInt(star.getAttribute('data-value'), 10);
            ratingInput.value = selectedRating;
            updateStars();
        });
    });

    function updateStars() {
        stars.forEach(function (star) {
            const value = parseInt(star.getAttribute('data-value'), 10);
            if (value <= selectedRating) {
                star.classList.remove('bi-star');
                star.classList.add('bi-star-fill', 'text-warning');
            } else {
                star.classList.add('bi-star');
                star.classList.remove('bi-star-fill', 'text-warning');
            }
        });
    }
});
