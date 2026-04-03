
$(document).ready(function () {


    /*
       Each tab button has a data-feed attribute ('global', 'following',
       'suburb', or 'cuisine'). Clicking a tab:
         - updates the active visual state on the tab buttons
         - shows/hides the secondary filter dropdowns
         - calls filterCards() to show/hide matching review cards
    */
    $('#feedTabs .feed-tab-btn').on('click', function () {
        const $btn = $(this);
        const feedType = $btn.data('feed');

        // Update active state on all tab buttons
        $('#feedTabs .feed-tab-btn')
            .removeClass('active')
            .attr('aria-selected', 'false');
        $btn.addClass('active').attr('aria-selected', 'true');

        $('#suburbFilter, #cuisineFilter').hide();

        if (feedType === 'suburb') {
            $('#suburbFilter').show();
            $('#suburbSelect').val('');        // reset to "All suburbs"
        } else if (feedType === 'cuisine') {
            $('#cuisineFilter').show();
            $('#cuisineSelect').val('');       // reset to "All cuisines"
        }

        // Show all cards for this feed type (no secondary filter yet)
        filterCards(feedType, null);
    });


    /*
       When the user selects a suburb, re-filter the cards.
       An empty value means "show all suburbs".
     */
    $('#suburbSelect').on('change', function () {
        const suburb = $(this).val();
        filterCards('suburb', suburb || null);
    });


    /*
       When the user selects a cuisine, re-filter the cards.
       An empty value means "show all cuisines".
    */
    $('#cuisineSelect').on('change', function () {
        const cuisine = $(this).val();
        filterCards('cuisine', cuisine || null);
    });


    /*
       Each review card has three like buttons (accuracy, writing, breadth).
       Clicking a button toggles its 'liked' state and updates the displayed
       count by +1 or -1.
    */
    $(document).on('click', '.like-btn', function () {
        const $btn = $(this);
        const $count = $btn.find('.like-count');
        const currentCount = parseInt($count.text(), 10);

        if ($btn.hasClass('liked')) {
            $btn.removeClass('liked');
            $count.text(currentCount - 1);
        } else {
            $btn.addClass('liked');
            $count.text(currentCount + 1);
        }
    });


    /* 
       Shows or hides each .review-card based on the active tab and any
       secondary filter value.

       @param {string}      feedType    — 'global' | 'following' | 'suburb' | 'cuisine'
       @param {string|null} filterValue — suburb/cuisine slug, or null (show all)
     */
    function filterCards(feedType, filterValue) {
        let visibleCount = 0;

        $('.review-card').each(function () {
            const $card = $(this);

            const cardFeeds = $card.data('feed').split(' ');
            const cardSuburb = $card.data('suburb') || '';
            const cardCuisine = $card.data('cuisine') || '';

            let show = false;

            if (feedType === 'global') {
                show = cardFeeds.includes('global');

            } else if (feedType === 'following') {
                show = cardFeeds.includes('following');

            } else if (feedType === 'suburb') {
                show = !filterValue || cardSuburb === filterValue;

            } else if (feedType === 'cuisine') {
                show = !filterValue || cardCuisine === filterValue;
            }

            if (show) {
                $card.show();
                visibleCount++;
            } else {
                $card.hide();
            }
        });

        if (visibleCount === 0) {
            $('#emptyState').show();
        } else {
            $('#emptyState').hide();
        }
    }

}); 
