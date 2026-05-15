$(document).ready(function () {

    $('#suburbSelect').on('change', function () {
        $(this).closest('form').submit();
    });

    $('#cuisineSelect').on('change', function () {
        $(this).closest('form').submit();
    });


    $(document).on('click', '.like-btn', function () {
        const $btn = $(this);
        const reviewId = $btn.data('review-id');
        const dimension = $btn.data('dimension');
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

        fetch(`/reviews/${reviewId}/like/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ dimension: dimension }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error(data.error);
                return;
            }
            $btn.toggleClass('liked', data.liked);
            $btn.find('.like-count').text(data.count);
        })
        .catch(error => console.error(error));
    });


    function filterCards(suburb, cuisine) {
        let visibleCount = 0;
        $('.review-card').each(function () {
            const $card = $(this);
            const cardSuburb = $card.data('suburb') || '';
            const cardCuisines = String($card.data('cuisine') || '').split(' ');

            const suburbMatch  = !suburb  || cardSuburb === suburb;
            const cuisineMatch = !cuisine || cardCuisines.includes(cuisine);

            if (suburbMatch && cuisineMatch) {
                $card.show();
                visibleCount++;
            } else {
                $card.hide();
            }
        });
        $('#emptyState').toggle(visibleCount === 0);
    }
    window.RFP_filterCards = filterCards;
});
