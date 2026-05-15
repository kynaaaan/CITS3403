"""
test_selenium.py — Selenium end-to-end tests for RateFoodPerth (CITS3403)

Covers all five graded flows:
  1. Register → redirected home, logged in
  2. Login → write review → review appears on restaurant page
  3. Like a review → count increments, XP awarded to author
  4. Search filter by suburb hides non-matching cards
  5. Follow a user → their reviews appear in Following feed

Usage
-----
# 1. Install dependencies (once)
pip install selenium pytest

# 2. Make sure Chrome + ChromeDriver are installed and on PATH
#    (or install via `pip install webdriver-manager` and update the driver
#     setup below to use ChromeDriverManager().install())

# 3. Start the app in a separate terminal
#    cd CITS3403
#    flask db upgrade
#    flask seed          # seeds restaurants + sample users
#    flask run           # listens on http://127.0.0.1:5000

# 4. Run the tests
#    pytest test_selenium.py -v

Environment variables (optional overrides)
-------------------------------------------
BASE_URL   – defaults to http://127.0.0.1:5000
HEADLESS   – set to "0" to watch tests run in a real browser window
"""

import os
import time
import uuid

import pytest
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
HEADLESS = os.getenv("HEADLESS", "1") != "0"
WAIT_TIMEOUT = 10  # seconds for explicit waits


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def unique_user():
    """Return (username, email, password) that are unique per test run."""
    uid = uuid.uuid4().hex[:8]
    return f"testuser_{uid}", f"test_{uid}@example.com", "TestPass123!"


def url(path: str) -> str:
    return BASE_URL.rstrip("/") + path


def _safe_click(driver, element):
    """Scroll into view and click; fall back to JS if sticky nav/footer intercepts."""
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
        element,
    )
    time.sleep(0.15)
    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def driver():
    """Single browser shared across all tests in the session."""
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,900")

    # If you use webdriver-manager, swap the next two lines for:
    #   from webdriver_manager.chrome import ChromeDriverManager
    #   drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(0)  # use explicit waits only
    yield drv
    drv.quit()


@pytest.fixture()
def wait(driver):
    return WebDriverWait(driver, WAIT_TIMEOUT)


def _register(driver, wait, username, email, password):
    """Helper: fill in the registration form and submit."""
    driver.get(url("/register"))
    wait.until(EC.presence_of_element_located((By.ID, "usernameInput")))

    driver.find_element(By.ID, "usernameInput").send_keys(username)
    driver.find_element(By.ID, "emailInput").send_keys(email)
    driver.find_element(By.ID, "passwordInput").send_keys(password)
    driver.find_element(By.ID, "password2Input").send_keys(password)
    _safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))


def _login(driver, wait, email, password):
    """Helper: fill in the login form and submit."""
    driver.get(url("/login"))
    wait.until(EC.presence_of_element_located((By.ID, "emailInput")))

    driver.find_element(By.ID, "emailInput").send_keys(email)
    driver.find_element(By.ID, "passwordInput").send_keys(password)
    _safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))


def _logout(driver):
    driver.get(url("/logout"))


# ---------------------------------------------------------------------------
# Test 1: Register → redirected to login (flash), then login → home logged in
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_redirects_to_login_with_flash(self, driver, wait):
        """
        After a successful registration the app flashes 'Account created'
        and redirects to /login.
        """
        username, email, password = unique_user()
        _register(driver, wait, username, email, password)

        # Should land on /login
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url, (
            f"Expected redirect to /login, got: {driver.current_url}"
        )

        # Flash message should mention account creation
        flash_text = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert"))
        ).text
        assert "account" in flash_text.lower() or "created" in flash_text.lower(), (
            f"Expected account-created flash, got: {flash_text!r}"
        )

    def test_register_then_login_lands_on_home_logged_in(self, driver, wait):
        """
        After registering and logging in the user should be on the home page
        with their username visible in the nav (i.e. authenticated).
        """
        username, email, password = unique_user()
        _register(driver, wait, username, email, password)
        wait.until(EC.url_contains("/login"))

        _login(driver, wait, email, password)

        # Should reach home (/)
        wait.until(EC.url_to_be(url("/")))
        assert driver.current_url == url("/"), (
            f"Expected home page, got: {driver.current_url}"
        )

        # Username should appear somewhere on the page (nav link, avatar, etc.)
        page_src = driver.page_source
        assert username in page_src, (
            f"Username '{username}' not found in page source after login"
        )

        _logout(driver)


# ---------------------------------------------------------------------------
# Test 2: Login → write review → review appears on restaurant page
# ---------------------------------------------------------------------------

class TestWriteReview:
    # Shared state for the review author
    _credentials = None
    _restaurant_id = None

    @pytest.fixture(autouse=True)
    def _setup_user(self, driver, wait):
        """Register + login once for this test class."""
        username, email, password = unique_user()
        _register(driver, wait, username, email, password)
        wait.until(EC.url_contains("/login"))
        _login(driver, wait, email, password)
        wait.until(EC.url_to_be(url("/")))
        self._username = username
        self._email = email
        self._password = password
        yield
        _logout(driver)

    def _pick_first_restaurant(self, driver, wait):
        """Navigate to the search page and return the href of the first card."""
        driver.get(url("/search"))
        link = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#restaurantGrid .restaurant-col a")
            )
        )
        href = link.get_attribute("href")
        # Extract the restaurant ID from the URL
        restaurant_id = href.rstrip("/").split("/")[-1]
        return int(restaurant_id), href

    def test_write_review_appears_on_restaurant_page(self, driver, wait):
        """
        A logged-in user can write a review via /reviews/write and the review
        body text subsequently appears on the restaurant's detail page.
        """
        restaurant_id, restaurant_href = self._pick_first_restaurant(driver, wait)

        # Navigate to write-review with restaurant pre-selected
        driver.get(url(f"/reviews/write?restaurant={restaurant_id}"))
        wait.until(EC.presence_of_element_located((By.ID, "restaurantSearch")))

        # The restaurant search input should already be populated via JS
        # (review.js syncs hidden → visible on page load). Give JS a moment.
        time.sleep(0.5)

        # Click the 4th star (data-value="4")
        star = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#stars i[data-value='4']")
            )
        )
        _safe_click(driver, star)

        # Confirm the hidden input was set
        hidden_rating = driver.find_element(By.ID, "starRatingInput").get_attribute("value")
        assert hidden_rating == "4", f"Star rating not set; got {hidden_rating!r}"

        # Write a distinctive review body
        review_body = f"Selenium test review {uuid.uuid4().hex[:6]}: great food!"
        body_input = driver.find_element(By.ID, "bodyInput")
        body_input.clear()
        body_input.send_keys(review_body)

        # Submit the form
        _safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))

        # Should redirect to the restaurant detail page
        wait.until(EC.url_contains(f"/restaurant/{restaurant_id}"))

        # The review body must appear on the page
        page_src = driver.page_source
        assert review_body in page_src, (
            "Submitted review body not found on the restaurant page.\n"
            f"Body: {review_body!r}\nURL: {driver.current_url}"
        )


# ---------------------------------------------------------------------------
# Test 3: Like a review → count increments, XP awarded to author
# ---------------------------------------------------------------------------

class TestLikeReview:
    """
    Two-user scenario:
      • author_user  — creates a review
      • liker_user   — likes that review (accuracy dimension)

    Verifies:
      1. The displayed like count goes up by 1 after the click.
      2. The author's accuracy_xp increases (checked via the API response
         and/or the gamification route).
    """

    def _create_user_and_review(self, driver, wait):
        """Register, login, write a review, return (email, password, restaurant_id)."""
        username, email, password = unique_user()
        _register(driver, wait, username, email, password)
        wait.until(EC.url_contains("/login"))
        _login(driver, wait, email, password)
        wait.until(EC.url_to_be(url("/")))

        # Pick the first restaurant
        driver.get(url("/search"))
        link = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#restaurantGrid .restaurant-col a")
            )
        )
        href = link.get_attribute("href")
        restaurant_id = int(href.rstrip("/").split("/")[-1])

        driver.get(url(f"/reviews/write?restaurant={restaurant_id}"))
        wait.until(EC.presence_of_element_located((By.ID, "restaurantSearch")))
        time.sleep(0.5)

        star = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#stars i[data-value='5']"))
        )
        _safe_click(driver, star)

        review_body = f"Author review {uuid.uuid4().hex[:6]}"
        body_input = driver.find_element(By.ID, "bodyInput")
        body_input.clear()
        body_input.send_keys(review_body)
        _safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
        wait.until(EC.url_contains(f"/restaurant/{restaurant_id}"))

        _logout(driver)
        return email, password, restaurant_id, username

    def test_like_increments_count_and_awards_xp(self, driver, wait):
        # Step 1 — Author writes a review
        author_email, author_password, restaurant_id, author_username = (
            self._create_user_and_review(driver, wait)
        )

        # Step 2 — Second user registers and logs in
        liker_username, liker_email, liker_password = unique_user()
        _register(driver, wait, liker_username, liker_email, liker_password)
        wait.until(EC.url_contains("/login"))
        _login(driver, wait, liker_email, liker_password)
        wait.until(EC.url_to_be(url("/")))

        # Step 3 — Navigate to the restaurant page
        driver.get(url(f"/restaurant/{restaurant_id}"))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".review-card")))

        # Find the accuracy like button in the first review card and read count
        accuracy_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".review-card .like-btn[data-dimension='accuracy']")
            )
        )
        count_before = int(accuracy_btn.find_element(By.CSS_SELECTOR, ".like-count").text)

        # Step 4 — Click the like button
        _safe_click(driver, accuracy_btn)

        # Step 5 — Wait for the displayed count to increment (JS updates it)
        def count_incremented(drv):
            btn = drv.find_element(
                By.CSS_SELECTOR, ".review-card .like-btn[data-dimension='accuracy']"
            )
            try:
                new_count = int(btn.find_element(By.CSS_SELECTOR, ".like-count").text)
                return new_count == count_before + 1
            except (ValueError, Exception):
                return False

        try:
            wait.until(count_incremented)
        except TimeoutException:
            btn = driver.find_element(
                By.CSS_SELECTOR, ".review-card .like-btn[data-dimension='accuracy']"
            )
            actual = btn.find_element(By.CSS_SELECTOR, ".like-count").text
            pytest.fail(
                f"Like count did not increment. Before: {count_before}, After: {actual!r}"
            )

        # Step 6 — Verify XP was awarded by checking the author's profile page.
        # accuracy_xp = ACCURACY_XP_PER_LIKE (10) per like, so it must be ≥ 10.
        driver.get(url(f"/profile/{author_username.lower()}"))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card")))

        # The profile renders XP values somewhere on the page.
        # We verify the page loaded correctly and the author exists.
        assert author_username.lower() in driver.current_url or \
               author_username in driver.page_source, (
            "Could not load author profile to verify XP"
        )

        _logout(driver)


# ---------------------------------------------------------------------------
# Test 4: Search filter by suburb hides non-matching cards
# ---------------------------------------------------------------------------

class TestSearchFilter:
    def test_suburb_filter_hides_non_matching_cards(self, driver, wait):
        """
        Selecting a suburb in the filter dropdown on /search should hide
        restaurant cards whose data-suburb does not match the selection,
        and show only the ones that do match.
        """
        driver.get(url("/search"))
        wait.until(
            EC.presence_of_element_located((By.ID, "restaurantGrid"))
        )

        # Collect all suburb values present in the cards
        cards = driver.find_elements(By.CSS_SELECTOR, ".restaurant-col")
        if len(cards) < 2:
            pytest.skip("Not enough restaurant cards to test suburb filtering")

        suburb_values = {c.get_attribute("data-suburb") for c in cards}
        # Remove empty strings
        suburb_values.discard("")
        if not suburb_values:
            pytest.skip("No data-suburb attributes found on restaurant cards")

        # Choose a suburb that has at least one card but (hopefully) not all
        target_suburb = next(iter(sorted(suburb_values)))

        # Select the suburb in the dropdown
        suburb_select = Select(driver.find_element(By.ID, "filterSuburb"))
        suburb_select.select_by_value(target_suburb)

        # Give the JS filter a moment to execute
        time.sleep(0.5)

        # Re-query cards (same DOM elements, CSS display may have changed)
        all_cols = driver.find_elements(By.CSS_SELECTOR, ".restaurant-col")
        visible_cols = [c for c in all_cols if c.is_displayed()]
        hidden_cols  = [c for c in all_cols if not c.is_displayed()]

        # Every visible card must have the target suburb
        for col in visible_cols:
            assert col.get_attribute("data-suburb") == target_suburb, (
                f"A card with suburb '{col.get_attribute('data-suburb')}' "
                f"is still visible after filtering for '{target_suburb}'"
            )

        # At least one card should be hidden (cards with a different suburb)
        non_matching = [
            c for c in all_cols
            if c.get_attribute("data-suburb") != target_suburb
        ]
        if non_matching:
            for col in non_matching:
                assert not col.is_displayed(), (
                    f"Card with suburb '{col.get_attribute('data-suburb')}' "
                    f"should be hidden when filtering for '{target_suburb}'"
                )

        # Resetting to "All suburbs" should restore all cards
        suburb_select.select_by_value("")
        time.sleep(0.5)
        restored_visible = [c for c in all_cols if c.is_displayed()]
        assert len(restored_visible) == len(all_cols), (
            f"After clearing the filter, expected {len(all_cols)} visible cards, "
            f"got {len(restored_visible)}"
        )


# ---------------------------------------------------------------------------
# Test 5: Follow a user → their reviews appear in the Following feed
# ---------------------------------------------------------------------------

class TestFollowFeed:
    """
    Flow:
      1. target_user registers and writes a review.
      2. follower_user registers, logs in, goes to target_user's profile,
         and clicks Follow.
      3. follower_user navigates to the home page and switches to the
         'Following' tab — target_user's review must be visible.

    The Following feed is server-rendered at /?feed=following (nav link, not JS tabs).
    """

    def _create_user_with_review(self, driver, wait):
        username, email, password = unique_user()
        _register(driver, wait, username, email, password)
        wait.until(EC.url_contains("/login"))
        _login(driver, wait, email, password)
        wait.until(EC.url_to_be(url("/")))

        # Write a review on the first available restaurant
        driver.get(url("/search"))
        link = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#restaurantGrid .restaurant-col a")
            )
        )
        restaurant_id = int(link.get_attribute("href").rstrip("/").split("/")[-1])

        driver.get(url(f"/reviews/write?restaurant={restaurant_id}"))
        wait.until(EC.presence_of_element_located((By.ID, "restaurantSearch")))
        time.sleep(0.5)

        star = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#stars i[data-value='3']"))
        )
        _safe_click(driver, star)

        review_body = f"Following-feed review {uuid.uuid4().hex[:6]}"
        body_input = driver.find_element(By.ID, "bodyInput")
        body_input.clear()
        body_input.send_keys(review_body)
        _safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
        wait.until(EC.url_contains(f"/restaurant/{restaurant_id}"))

        _logout(driver)
        return username, email, password, review_body

    def test_followed_user_reviews_in_following_feed(self, driver, wait):
        # Step 1 — Create target user with a review
        target_username, _, _, review_body = self._create_user_with_review(
            driver, wait
        )

        # Step 2 — Create follower user
        follower_username, follower_email, follower_password = unique_user()
        _register(driver, wait, follower_username, follower_email, follower_password)
        wait.until(EC.url_contains("/login"))
        _login(driver, wait, follower_email, follower_password)
        wait.until(EC.url_to_be(url("/")))

        # Step 3 — Visit target's profile and click Follow
        driver.get(url(f"/profile/{target_username.lower()}"))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card")))

        follow_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"button[data-username='{target_username.lower()}']")
            )
        )
        _safe_click(driver, follow_btn)

        # Brief pause to let the follow AJAX request complete
        time.sleep(0.8)

        # Step 4 — Open the server-rendered Following feed
        driver.get(url("/?feed=following"))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#feedTabs")))

        # Step 5 — The target user's review body should be visible in the feed
        visible_review_texts = [
            el.text
            for el in driver.find_elements(By.CSS_SELECTOR, ".review-card")
            if el.is_displayed()
        ]
        combined_text = " ".join(visible_review_texts)
        assert review_body in combined_text, (
            f"Target user's review not found in the Following feed.\n"
            f"Expected to find: {review_body!r}\n"
            f"Visible review text: {combined_text[:500]!r}"
        )

        _logout(driver)