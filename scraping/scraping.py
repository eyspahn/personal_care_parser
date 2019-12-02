import time
from datetime import datetime
import os
import csv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException


def scrape_ingredients_list():

    # hardcoding link for now
    url = "https://www.ewg.org/skindeep/search?search=*&search_type=ingredients&per_page=36"
    page_num = 1
    driver = webdriver.Chrome()
    driver.get(url)

    try:
        driver.find_element_by_id('yeaClose').click()
    except NoSuchElementException:
        pass

    time.sleep(10)

    while driver.find_element_by_class_name('next_page').is_displayed():

        parse_ingredient_search_page(driver, page_num)
        page_num += 1
        # Proceed to next page
        driver.find_element_by_class_name('next_page').click()

    # and we'll need to scrape that last page as well
    parse_ingredient_search_page(driver, page_num)

    driver.close()
    print("Hey it worked!")


def parse_ingredient_search_page(driver, page_num):

    product_tile_num = 0
    out_filename = 'ingredient_search_page_' + str(page_num) + '.csv'

    # Get the elements with this class - returns a list of webelements
    pt = driver.find_elements_by_class_name('product-tile')

    try:
        # Iterate through all the product-tiles:
        for i in range(len(pt)):
            a_tag = pt[i].find_elements_by_tag_name("a")[1]
            chemical_name = a_tag.text
            chemical_link = a_tag.get_attribute('href')
            a_tag.click()
            scraped = scrape_chemical_page(driver, page_num)
            driver.back()
            time.sleep(10)
            pt = driver.find_elements_by_class_name('product-tile')

            with open(out_filename, 'a+') as f:
                search_page_writer = csv.writer(f)
                search_page_writer.writerow([datetime.now(), page_num, chemical_name, chemical_link, scraped])
    except:
        scraped = False
        with open(out_filename, 'a+') as f:
            search_page_writer = csv.writer(f)
            search_page_writer.writerow(['missed finishing scraping page', '','', '', scraped])


def scrape_chemical_page(driver, search_page_num):
    """Scrape the ingredient page and record results. Returns True if scrape successful, False otherwise."""

    try:
        chemical_name = driver.find_element_by_class_name('chemical-name').text
        score_url = driver.find_element_by_class_name('squircle').get_attribute('src')
        data_availability = driver.find_element_by_class_name('chemical-score').text.split('\n')[1]

        # Now we need to start clicking and pulling off the data we want.
        # starts with "other concerns" selected

        driver.find_element_by_class_name('chemical-concerns').click()
        driver.find_element_by_class_name('chemical-concerns').click()
        chemical_concerns = driver.find_elements_by_class_name('chemical-info')[0].text

        # and the click-record pairs
        driver.find_element_by_class_name('chemical-functions').click()
        chemical_functions = driver.find_elements_by_class_name('chemical-info')[1].text
        driver.find_element_by_class_name('chemical-about').click()
        chemical_about = driver.find_elements_by_class_name('chemical-info')[2].text
        driver.find_element_by_class_name('chemical-synonyms').click()
        chemical_synonyms = driver.find_elements_by_class_name('chemical-info')[3].text

        # let's write out these into a csv file, which is
        # possibly not the best option for long strings...but it should be fairly short
        out_filename = 'chemical_details_search_page_' + str(search_page_num) + '.csv'
        with open(out_filename, 'a+') as f:

            field_names = ['datetime_pulled',
                           'search_page_num',
                           'chemical_name',
                           'score_url',
                           'data_availability',
                           'chemical_concerns',
                           'chemical_functions',
                           'chemical_about',
                           'chemical_synonyms']

            chemical_writer = csv.DictWriter(f, field_names)
            chemical_writer.writerow({'datetime_pulled': datetime.now(),
                                      'search_page_num': search_page_num,
                                      'chemical_name': chemical_name,
                                      'score_url': score_url,
                                      'data_availability': data_availability,
                                      'chemical_concerns': chemical_concerns,
                                      'chemical_functions': chemical_functions,
                                      'chemical_about': chemical_about,
                                      'chemical_synonyms': chemical_synonyms})

        return True

    except:
        with open('missed_entries_on_search_page.log', "a+") as f:
            f.write(f"Missed an entry on page: {search_page_num}")
        return False


if __name__ == "__main__":
    scrape_ingredients_list()
