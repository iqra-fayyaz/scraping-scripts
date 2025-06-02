import time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re
import pandas as pd

# Initialize the WebDriver (e.g., Chrome)
chrome_driver_path = ChromeDriverManager().install()
correct_chrome_driver_path = chrome_driver_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver.exe")

print(f"Python executable: {os.path.abspath(__file__)}")
print(f"ChromeDriver path: {correct_chrome_driver_path}")

# Set up Chrome options
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(correct_chrome_driver_path), options=chrome_options)

# Open the target website
driver.get('https://www.notaryresume.com/')

# Wait until the select element is present
wait = WebDriverWait(driver, 10)
select_element = wait.until(EC.presence_of_element_located((By.NAME, 'state')))

# Create a Select object
select = Select(select_element)

# Print available options for debugging
options = select.options
print("Available options:")
for i, option in enumerate(options):
    print(f'{i}: Value: {option.get_attribute("value")}, Text: {option.text}')

# Prepare a list to store the data
data = []

# Define the output file name
output_file = 'notary_data.xlsx'

# Load existing data if file exists
if os.path.exists(output_file):
    df_existing = pd.read_excel(output_file)
    data.extend(df_existing.to_dict(orient='records'))
    print(f"Resuming from existing data in {output_file}")

# Determine the last scraped state
scraped_states = {record['State'] for record in data if 'State' in record}
state_options = [option.text for option in options]
remaining_states = [state for state in state_options if state not in scraped_states]

if not remaining_states:
    print("All states have been scraped.")
    driver.quit()
    exit()


def handle_stale_element_exception(func, *args, **kwargs):
    """Handle StaleElementReferenceException with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Exception on attempt {attempt + 1}: {e}")
            time.sleep(1)
    raise Exception("Failed after multiple retries")


# Iterate through remaining states and select each one
for state in remaining_states:
    try:
        select_element = wait.until(EC.presence_of_element_located((By.NAME, 'state')))
        select = Select(select_element)
        select.select_by_visible_text(state)

        time.sleep(2)

        selected_option = select.first_selected_option
        state_text = selected_option.text
        print(f"Selected: {state_text}")

        # Wait for the submit button to be clickable and click it
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
        submit_button.click()

        time.sleep(10)
        while True:
            # Wait for the results page to load
            wait.until(EC.presence_of_element_located((By.XPATH, '//table[@id="closer-search-table"]')))
            soup = BeautifulSoup(driver.page_source, 'lxml')
            # Find all table rows
            rows = soup.select('table#closer-search-table tbody tr')
            for row in rows:
                t_data = row.find_all('td')
                if len(t_data) >= 6:  # Ensure there are enough columns
                    name = t_data[2].text.strip()
                    address = t_data[3].text.strip()
                    phone = t_data[4].text.strip()

                    # Click the row using Selenium
                    row_index = row.get('data-index')
                    selenium_row = wait.until(
                        EC.element_to_be_clickable((By.XPATH, f'//tr[@data-index="{row_index}"]')))
                    handle_stale_element_exception(selenium_row.click)
                    time.sleep(5)

                    # Wait for the profile dialog to appear
                    dialog = handle_stale_element_exception(lambda: wait.until(
                        EC.visibility_of_element_located((By.XPATH, '//div[contains(@class, "modal-content")]'))))
                    # Extract and print information from the dialog
                    profile_info = dialog.text
                    email_match = re.search(r'[\w.-]+@[\w.-]+', profile_info)
                    email = email_match.group(0) if email_match else "None"

                    time.sleep(3)
                    close_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Close']")))
                    close_button.click()

                    # Append the data to the list
                    data.append({
                        'State': state_text,
                        'Name': name,
                        'Address': address,
                        'Phone': phone,
                        'Email': email
                    })

            try:
                pagination = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.page-next a")))
                print("Pagination Button HTML:", pagination.get_attribute('outerHTML'))

                # Scroll the pagination button into view
                driver.execute_script("arguments[0].scrollIntoView(true);", pagination)
                time.sleep(1)  # Give some time for scrolling

                pagination.click()
                time.sleep(5)  # Wait for pagination to load
            except Exception as e:
                print("Pagination button not found or not accessible:", e)
                break

            time.sleep(2)

        # Save progress to file
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        print(f"Progress saved to {output_file}")

    except Exception as e:
        print(f"Error processing state option: {state}, {e}")
        # Save progress to file before exiting
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        print(f"Progress saved to {output_file} due to error")
        break

# Convert the list of dictionaries to a pandas DataFrame and save to Excel
df = pd.DataFrame(data)
df.to_excel(output_file, index=False)

print(f"Final data has been written to {output_file}")

# Close the WebDriver
driver.quit()