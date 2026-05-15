/*
 * Follow / unfollow handling for profile pages.
 *
 * Markup contract — any element with class `.follow-btn`:
 *   data-username   target user's username (already lowercased server-side)
 *   data-following  current state, string "true" or "false"
 *
 * CSRF: the token is read from the <meta name="csrf-token"> tag set in base.html
 * and sent as the X-CSRFToken header (the name Flask-WTF expects by default).
 */
$(function () {
    const csrfToken = $('meta[name="csrf-token"]').attr('content');

    $(document).on('click', '.follow-btn', function () {
        const $btn = $(this);
        if ($btn.prop('disabled')) return;

        const username = $btn.data('username');
        const isFollowing = String($btn.data('following')) === 'true';
        const url = (isFollowing ? '/unfollow/' : '/follow/') + username + '/';

        $btn.prop('disabled', true);

        $.ajax({
            url: url,
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
        }).done(function (resp) {
            const nowFollowing = !!resp.following;
            $btn.data('following', nowFollowing ? 'true' : 'false');
            $btn.text(nowFollowing ? 'Unfollow' : 'Follow');
            $btn.toggleClass('btn-primary', !nowFollowing);
            $btn.toggleClass('btn-outline-primary', nowFollowing);

            if (typeof resp.follower_count === 'number') {
                const $count = $('.follower-count');
                $count.text(resp.follower_count);
                $count.next('.text-muted').text(
                    resp.follower_count === 1 ? 'follower' : 'followers'
                );
            }
        }).fail(function (xhr) {
            const msg = (xhr.responseJSON && xhr.responseJSON.error) ||
                        'Could not update follow state. Try again.';
            alert(msg);
        }).always(function () {
            $btn.prop('disabled', false);
        });
    });
});
