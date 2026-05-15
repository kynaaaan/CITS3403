/*
   review.js — Client-side widgets for write_review.html.

   Two concerns:
   1. Star rating: click a star: fill that star and all to its left, update
      the hidden #starRatingInput. Also restore the visual on page load so
      validation-failure renders don't lose the highlighted stars.
   2. Restaurant search (datalist): the visible <input> is for typing; the
      hidden #restaurantIdHidden is what actually gets posted. Sync the two
      via the data-id attribute on each <option>.

*/

document.addEventListener('DOMContentLoaded', function () {
    initStarRating();
    initRestaurantDatalist();
});


function initStarRating() {
    const stars = document.querySelectorAll('#stars i');
    const ratingInput = document.getElementById('starRatingInput');
    if (!stars.length || !ratingInput) return;

    let selectedRating = parseInt(ratingInput.value, 10) || 0;

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

    stars.forEach(function (star) {
        star.style.cursor = 'pointer';
        star.addEventListener('click', function () {
            selectedRating = parseInt(star.getAttribute('data-value'), 10);
            ratingInput.value = selectedRating;
            updateStars();
        });
    });

    if (selectedRating > 0) updateStars();
}


function initRestaurantDatalist() {
    const search = document.getElementById('restaurantSearch');
    const hidden = document.getElementById('restaurantIdHidden');
    const list   = document.getElementById('restaurantsList');
    if (!search || !hidden || !list) return;

    const nameToId = {};
    const idToName = {};
    Array.from(list.options).forEach(function (opt) {
        const id = opt.dataset.id;
        nameToId[opt.value.toLowerCase()] = id;
        idToName[id] = opt.value;
    });

    if (hidden.value && idToName[hidden.value]) {
        search.value = idToName[hidden.value];
    }

    function sync() {
        hidden.value = nameToId[search.value.toLowerCase()] || '';
    }

    search.addEventListener('input', sync);
    search.addEventListener('change', sync);
}
