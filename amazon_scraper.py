"""
amazon_scraper.py
-----------------
This script extracts product information and reviews from Amazon Turkey (amazon.com.tr)
based on given brand and category IDs. The scraped data includes product names, sellers,
ratings, number of reviews, and individual review sentiments (if available).
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import re

# Example inputs (can be customized by the user)
brand_codes = {
    "vitra": "426255"  # Example brand code
}

category_codes = {
    "Bathroom Accessories": "13028018031",
    "Kitchen Faucets": "12707216031"
}

# Initialize Chrome WebDriver
service = Service()
options = Options()
options.add_argument("--headless")  # Run in background
driver = webdriver.Chrome(service=service, options=options)

# Loop through categories and brands
for category_name, category_id in category_codes.items():
    product_list = []

    for brand, brand_id in brand_codes.items():
        page_number = 1

        while True:
            url = f"https://www.amazon.com.tr/s?rh=n%3A{category_id}%2Cp_123%3A{brand_id}&page={page_number}"
            driver.get(url)
            time.sleep(2)

            product_cards = driver.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')
            if not product_cards:
                break

            for card in product_cards:
                try:
                    product_link = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(product_link)
                    time.sleep(2)

                    title = driver.find_element(By.ID, "productTitle").text.strip()
                    price = driver.find_element(By.CSS_SELECTOR, 'span.a-price-whole').text.strip() \
                        if driver.find_elements(By.CSS_SELECTOR, 'span.a-price-whole') else "N/A"

                    try:
                        seller = driver.find_element(By.XPATH, "//span[text()='Satıcı']")
                        seller = seller.find_element(By.XPATH, "../../following-sibling::div//span[@class='a-size-small offer-display-feature-text-message']").text.strip()
                    except NoSuchElementException:
                        seller = None

                    try:
                        rating = driver.find_element(By.XPATH, '//*[@id="acrPopover"]/span[1]/a/span').text.strip()
                    except NoSuchElementException:
                        rating = None

                    try:
                        review_count = driver.find_element(By.XPATH, "//span[@id='acrCustomerReviewText']").text.strip()
                        review_count = int(''.join(filter(str.isdigit, review_count)))
                    except NoSuchElementException:
                        review_count = None

                    # Review extraction
                    review_list = []
                    review_url = f"{product_link}#customerReviews"
                    driver.get(review_url)
                    time.sleep(2)

                    while True:
                        comments = driver.find_elements(By.XPATH, '//span[@data-hook="review-body"]')
                        stars = driver.find_elements(By.XPATH, '//i[@data-hook="review-star-rating"]/span')

                        for comment, star in zip(comments, stars):
                            comment_text = comment.text.strip() if comment.text else None
                            star_match = re.search(r'(\d+),(\d+)', star.get_attribute("innerText").strip())
                            star_rating = int(star_match.group(1)) if star_match else None

                            if comment_text and star_rating is not None:
                                review_list.append({"Comment": comment_text, "Rating": star_rating})

                        try:
                            next_button = driver.find_element(By.CSS_SELECTOR, '.a-pagination .a-last a')
                            driver.execute_script("arguments[0].click();", next_button)
                            time.sleep(2)
                        except NoSuchElementException:
                            break

                    if not review_list:
                        review_list = None

                    product_list.append({
                        "Category": category_name,
                        "Category ID": category_id,
                        "Brand": brand,
                        "Brand ID": brand_id,
                        "Title": title,
                        "Seller": seller,
                        "Rating": rating,
                        "Review Count": review_count,
                        "Price": price,
                        "Reviews": review_list
                    })

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    print(f"Error occurred: {e}")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

            page_number += 1

    # Export category data to CSV
    df = pd.DataFrame(product_list)
    df.to_csv(f"amazon_reviews_{category_name.replace(' ', '_')}.csv", index=False, encoding="utf-8-sig")
    print(f"Saved: amazon_reviews_{category_name}.csv")

driver.quit()
