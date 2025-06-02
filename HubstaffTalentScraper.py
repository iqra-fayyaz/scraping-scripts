import asyncio
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from selenium.webdriver.chrome.options import Options

# Setup Selenium WebDriver with headless mode
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-images")
chrome_options.add_argument("--disable-javascript")
chrome_options.add_argument("--headless")

# Use a single instance of the WebDriver for all async calls
driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(10)

async def profile_page(profile_url):
    start_time = time.time()  # Start the timer

    driver.get(profile_url)
    profile_soup = BeautifulSoup(driver.page_source, 'lxml')
    result = profile_soup.find('div', class_='profile-header-info')

    # Initialize all fields locally
    reply = 'N/A'
    experience = 'N/A'
    skills = 'N/A'
    linkedIn_link = 'N/A'
    facebook_link = 'N/A'
    github_link = 'N/A'

    if result:
        experience_tags = result.find_all('dl')
        reply = experience_tags[0].dd.text.strip() if experience_tags else 'N/A'
        experience = experience_tags[-1].dd.text.strip() if experience_tags else 'N/A'

    list_element = profile_soup.find('div', id='profile-skills')
    if list_element:
        skill_element = list_element.find('ul', class_='list-inline')
        if skill_element:
            list_tags = skill_element.find_all('li')
            skills = ','.join(li.text.strip() for li in list_tags)

    social_media_tags = profile_soup.find('ul', class_='list-inline social-profiles')
    if social_media_tags:
        a_tags = social_media_tags.find_all('a')
        for a_tag in a_tags:
            href = a_tag.get('href', '')
            if 'linkedin.com' in href:
                linkedIn_link = href
            elif 'facebook.com' in href:
                facebook_link = href
            elif 'github.com' in href:
                github_link = href

    end_time = time.time()  # Stop the timer
    elapsed_time = end_time - start_time  # Calculate elapsed time
    return reply, experience, skills, linkedIn_link, facebook_link, github_link, elapsed_time

async def process_profile_data(data, profile_url):
    result = await profile_page(profile_url)
    # Unpack the tuple
    reply, experience, skills, linkedIn_link, facebook_link, github_link, elapsed_time = result

    # Update the data dictionary with profile details
    data.update({
        'Reply_Rate': reply,
        'Experience': experience,
        'Skills': skills,
        'LinkedIn_Link': linkedIn_link,
        'Facebook_Link': facebook_link,
        'Github_Link': github_link,
        'Load_Time': elapsed_time,
    })

    return data

async def talent_search(main_url, soup):
    profiles = soup.find_all('div', class_='search-result')

    tasks = []
    for profile in profiles:
        # Create a local copy of data for each profile
        data = {}

        freelancer_name = profile.find('a', class_='name margin-right-10')
        data['Name'] = freelancer_name.text.strip() if freelancer_name.text else 'N/A'

        working_category = freelancer_name.find_next_sibling()
        data['Availability'] = working_category.text.strip() if working_category.text else 'N/A'

        data['Pay_rate'] = working_category.find_next_sibling().text.strip()

        speciality = profile.find('div', class_='speciality')
        data['Speciality'] = speciality.text.strip()

        location_tag = profile.find('span', class_='location text-success').text.split(',')
        data['Country'] = location_tag[-1].strip()
        data['Location'] = ','.join(location_tag[0:2]).strip()

        find_profile_url = freelancer_name['href']
        profile_url = urljoin(main_url, find_profile_url)
        data['Profile_Link'] = profile_url

        # Process profile data asynchronously and collect tasks
        tasks.append(process_profile_data(data, profile_url))

    # Gather results from all tasks
    results = await asyncio.gather(*tasks)

    # Return the collected data
    return results

async def main():
    main_url = 'https://hubstafftalent.net/'
    all_data = []

    for i in range(500, 1000):
        print(f'Extracting page {i}')
        search_results_url = f'https://hubstafftalent.net/search/profiles?search%5Bkeywords%5D=&page={i}&search%5Btype%5D=all&search%5Bpayrate_start%5D=1&search%5Bpayrate_end%5D=100&search%5Bpayrate_null%5D=0&search%5Bpayrate_null%5D=1&search%5Bexperience_start%5D=0&search%5Bexperience_end%5D=40&search%5Blanguages%5D%5B%5D=&search%5Bage_start%5D=18&search%5Bage_end%5D=100&search%5Bage_null%5D=0&search%5Bage_null%5D=1&search%5Bcountries%5D%5B%5D='
        driver.get(search_results_url)
        time.sleep(3)
        soup_element = BeautifulSoup(driver.page_source, 'lxml')
        profile_data = await talent_search(main_url, soup_element)
        all_data.extend(profile_data)

    # Save the collected data to Excel
    df = pd.DataFrame(all_data)
    df.to_excel('freelancer_profiles_async2.xlsx', index=False)
    print("Data saved to freelancer_profiles_async2.xlsx")

    driver.quit()

asyncio.run(main())