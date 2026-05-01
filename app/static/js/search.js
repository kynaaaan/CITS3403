$(document).ready(function () {

    /* Re-filter whenever any dropdown changes */
    $('#filterSuburb, #filterCuisine, #filterPrice').on('change', function () {
        filterRestaurants();
    });


    /*
       Show or hide each .restaurant-col based on the current filter values.
       A card must match ALL active filters (AND logic).
    */
    function filterRestaurants() {
        var suburb  = $('#filterSuburb').val();
        var cuisine = $('#filterCuisine').val();
        var price   = $('#filterPrice').val();

        var visibleCount = 0;

        $('.restaurant-col').each(function () {
            var $col = $(this);

            var matchSuburb  = !suburb  || $col.data('suburb')  === suburb;
            var matchCuisine = !cuisine || $col.data('cuisine') === cuisine;
            /* data-price is stored as a number by jQuery, so compare with == */
            var matchPrice   = !price   || String($col.data('price')) === price;

            if (matchSuburb && matchCuisine && matchPrice) {
                $col.show();
                visibleCount++;
            } else {
                $col.hide();
            }
        });

        /* Update the results count text */
        if (visibleCount === 0) {
            $('#resultsCount').text('No restaurants found');
            $('#emptyState').show();
        } else {
            var label = visibleCount === 1 ? 'restaurant' : 'restaurants';
            $('#resultsCount').text('Showing ' + visibleCount + ' ' + label);
            $('#emptyState').hide();
        }
    }

});
