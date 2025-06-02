from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import pandas as pd
import time
import traceback

# Initialize the webdriver
chrome_driver_path = ChromeDriverManager().install()
correct_chrome_driver_path = chrome_driver_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver.exe")
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(correct_chrome_driver_path), options=chrome_options)
wait = WebDriverWait(driver, 3)

output_file = "scraped_data.xlsx"
data_list = []  # List to store data incrementally

def save_data_to_excel():
    """Save the data list to an Excel file."""
    df = pd.DataFrame(data_list)
    df.to_excel(output_file, index=False)
    print(f"Data saved to {output_file}")

def grab_company_page(company_list_link):
    global data_list
    try:
        driver.get(company_list_link)
        time.sleep(2)
        soup1 = BeautifulSoup(driver.page_source, 'lxml')
        company_list = soup1.find('table', id='membersTable')
        trow = company_list.find_all('tr', class_='normal')

        for td in trow:
            data = {'Company_Name': '', 'Email': '', 'Profile_Link': ''}

            if td.h5:
                name = td.find('h5').text
                data['Company_Name'] = name.strip() if name else "N/A"
                data['Profile_Link'] = td.a['href'] if td.a else "N/A"

                # Navigate to the company profile page
                if td.a and td.a['href']:
                    try:
                        driver.get(td.a['href'])
                        time.sleep(2)
                        soup3 = BeautifulSoup(driver.page_source, 'lxml')

                        page = soup3.find('div', class_='inner')
                        info = page.find('div', id='idContainer12872051')
                        company_info = info.find('div', class_='fieldBody')
                        data['Email'] = company_info.a.text if company_info and company_info.a else "N/A"
                    except Exception as e:
                        print(f"Error while processing company profile: {e}")
                        traceback.print_exc()

            # Add data to the list and save incrementally
            data_list.append(data)
            save_data_to_excel()

    except Exception as e:
        print(f"Error while processing the company list page: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    try:
        main_page_url = 'https://www.czap.cz/adresar'
        grab_company_page(main_page_url)
    except Exception as e:
        print(f"An error occurred in the main execution: {e}")
        traceback.print_exc()
    finally:
        # Ensure data is saved and the driver quits even if an error occurs
        save_data_to_excel()
        driver.quit()
