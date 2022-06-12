from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
import pandas as pd
import requests
import time
import re
import os

def grab_all_urls_of_this_type(car_type):
    # Open the chrome browser
    path = Service('/Users/yangm/Desktop/chromedriver/chromedriver')
    driver = webdriver.Chrome(service=path)
    driver.get("http://www.edmunds.com/")
    driver.maximize_window()

    # Enter to the webpage with this car_type
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, 600)")
    driver.find_element(By.CSS_SELECTOR,"a[data-tracking-value='{}']".format(car_type)).click()
    # Close the ads
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR,
        ".fixed-bottom.sticky-banner>.edm-entry.aunit.pos-r>button[data-tracking-id='close_adhesion']").click()

    # Find all collapsed elements
    collapse_buttons = driver.find_elements(By.CSS_SELECTOR,
        ".collapse-control.mb-0.row.align-items-center.mx-0.mb-1_5.justify-content-start>button[data-tracking-id='subtype_list_expand']")

    # Click each of them
    for i in range(len(collapse_buttons)):
        ActionChains(driver).move_to_element(collapse_buttons[i]).perform()
        time.sleep(1)
        collapse_buttons[i].click()

    urls_and_years = driver.find_elements(By.CSS_SELECTOR,".vehicle-card.rounded.mb-1_5.pb-1")
    urls = []

    for i in range(len(urls_and_years)):
        url = urls_and_years[i].find_element(By.CSS_SELECTOR,"a[data-tracking-value='model_image']").get_attribute(
            "href")

        try:
            years = urls_and_years[i].find_element(By.CSS_SELECTOR,
                ".mb-0.list-unstyled.col-12.col-md-8>.mb-1>.label").text[-4:]
            years = int(years)
            print(years)
            while years <= 2022:
                url = re.sub('[0-9]{4}', str(years), url)
                url = os.path.join(url + "consumer-reviews/?pagesize=50")
                urls.append(url)
                years += 1
        except:
            url = os.path.join(url + "consumer-reviews/?pagesize=50")
            urls.append(url)
            print('error')
            continue

    return urls

def get_posts(url,count=False):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"
    }

    response = requests.get(url, timeout=10, headers=header)
    soup = BeautifulSoup(response.text, 'html.parser')
    if count:
        posts = soup.find('div', class_ ='review-count text-gray-darker')
    else:
        posts = soup.find_all('div', class_ ='review-item text-gray-darker')

    return posts


def find_review_and_ratings_of_this_page(posts):
    # Create all lists
    reviews = []
    Total_star = []
    Safety = []
    Technology = []
    Performance = []
    Interior = []
    Comfort = []
    Reliability = []
    Value = []

    for i in range(len(posts)):
        # Reviews and total stars
        reviews.append(posts[i].find('p').text.strip())
        Total_star.append(posts[i].find('span', class_="sr-only").text[0])

        # Safety rating star (if none, output 0)
        Safety_tag = posts[i].find('dt', string="Safety")
        if Safety_tag is None:
            Safety.append('0')
        else:
            Safety.append(Safety_tag.next_sibling.find('span', class_='sr-only').text[0])

        # Technology rating star (if none, output 0)
        Technology_tag = posts[i].find('dt', string="Technology")
        if Technology_tag is None:
            Technology.append('0')
        else:
            Technology.append(Technology_tag.next_sibling.find('span', class_='sr-only').text[0])

        # Performance rating star (if none, output 0)
        Performance_tag = posts[i].find('dt', string="Performance")
        if Performance_tag is None:
            Performance.append('0')
        else:
            Performance.append(Performance_tag.next_sibling.find('span', class_='sr-only').text[0])

        # Interior rating star (if none, output 0)
        Interior_tag = posts[i].find('dt', string="Interior")
        if Interior_tag is None:
            Interior.append('0')
        else:
            Interior.append(Interior_tag.next_sibling.find('span', class_='sr-only').text[0])

        # Comfort rating star (if none, output 0)
        Comfort_tag = posts[i].find('dt', string="Comfort")
        if Comfort_tag is None:
            Comfort.append('0')
        else:
            Comfort.append(Comfort_tag.next_sibling.find('span', class_='sr-only').text[0])

        # Reliability rating star (if none, output 0)
        Reliability_tag = posts[i].find('dt', string="Reliability")
        if Reliability_tag is None:
            Reliability.append('0')
        else:
            Reliability.append(Reliability_tag.next_sibling.find('span', class_='sr-only').text[0])

        # Value rating star (if none, output 0)
        Value_tag = posts[i].find('dt', string="Value")
        if Value_tag is None:
            Value.append('0')
        else:
            Value.append(Value_tag.next_sibling.find('span', class_='sr-only').text[0])

    df = pd.DataFrame({'Total_star': Total_star,
                       'Review': reviews,
                       'Safety': Safety,
                       'Technology': Technology,
                       'Performance': Performance,
                       'Interior': Interior,
                       'Comfort': Comfort,
                       'Reliability': Reliability,
                       'Value': Value,
                       })

    return df


def the_number_of_pages(post):
    number_of_reviews = int(post.text[:2])

    number_of_pages = number_of_reviews // 50
    if number_of_reviews % 50 > 0:
        number_of_pages += 1

    return number_of_pages


def grab_reviews_and_ratings_of_this_model(url):
    count_post = get_posts(url, count=True)
    number_of_pages = the_number_of_pages(count_post)
    df = pd.DataFrame()

    for page_number in range(number_of_pages):
        page_number += 1
        url = os.path.join(url + "&pagenum=%s" % page_number)
        posts = get_posts(url)
        temp_df = find_review_and_ratings_of_this_page(posts)
        df = pd.concat([df, temp_df], ignore_index=True)

    # Obtain the basic information
    url_splited = re.split('/', url)
    make = url_splited[3]
    df.insert(0, 'Make', make)
    model = url_splited[4]
    df.insert(1, 'Model', model)
    year = url_splited[5]
    df.insert(2, 'Year', year)

    return df

if __name__ == '__main__':
    car_types = ['SUVs', 'Trucks', 'Sedans', 'Electric Cars', 'Hybrids', 'Hatchbacks', 'Coupes', 'Wagons',
                 'Convertibles', 'Minivans']

    error = 0
    errors = []
    list_of_dfs = []
    for car_type in car_types:
        dfs = pd.DataFrame()
        urls = grab_all_urls_of_this_type(car_type)
        for url in urls:
            try:
                df_temp = grab_reviews_and_ratings_of_this_model(url)
                dfs = pd.concat([dfs, df_temp], ignore_index=True)
            except:
                error += 1
                errors.append(url)

        print(error)
        list_of_dfs.append(dfs)

    final_df = pd.DataFrame()
    for dfs, car_type in zip(list_of_dfs, car_types):
        dfs.insert(0, "Type", car_type)
        final_df = pd.concat([final_df, dfs])

    print(final_df)

