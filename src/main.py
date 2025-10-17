from dotenv import load_dotenv
from bs4 import BeautifulSoup
from premailer import transform
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import requests
import re
import json
import os

# Local modules
from detail_page_scrape import scrape_tender
from drive import authenticate_google_drive, get_shareable_link, upload_folder_to_drive
from email_sender import send_html_email
from templater import reformat_page

load_dotenv()

GOOGLE_DRIVE_PARENT_FOLDER = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER")
base_url = "https://www.tenderdetail.com"
tdr_xpath = "/html/body/div/div[1]/section[2]/div[1]/div/div/table[1]/tbody/tr[2]/td[2]"

def clean_project():
    # First lets clear the tenders/ directory
    os.system("rm -rf tenders/")
    # Create the tenders/ directory
    os.mkdir("tenders/")

def scrape_tenders(tenders_links_list, driver: WebDriver):
    for tender in tenders_links_list:
        tender_link = tender.find_all('a')[0]['href']
        driver.get(f"{base_url}{tender_link}")

        # Get the TDR
        tdr = driver.find_element(By.XPATH, value=tdr_xpath).text
        os.mkdir(f"tenders/{tdr}")

        # Get all a elements with the "Download" text
        download_links = driver.find_elements(By.XPATH, value='//a[contains(text(), "Download")]')

        print(f"Current TDR: {tdr}")
        print("Link: ", tender_link)

        # Download all the files
        for download_link in download_links:
            download_link_url = download_link.get_attribute("href")
            if not download_link_url:
                print("No download link found")
                continue
            file_name = download_link_url.split("FileName=")[-1]
            with open(f"tenders/{tdr}/{file_name}", "wb") as f:
                # If the file already exists, skip it
                print(f"Downloading {file_name}")
                f.write(requests.get(download_link_url).content)

        # Upload the folder to Google Drive
        drive_service = authenticate_google_drive()
        if not drive_service:
            return

        # Upload the folder to Google Drive, if it doesn't already exist
        folder_id = upload_folder_to_drive(drive_service, f"tenders/{tdr}", parent_folder_id=GOOGLE_DRIVE_PARENT_FOLDER)

        # Get the shareable link and print it
        shareable_link = get_shareable_link(drive_service, folder_id)
        print(f"Shareable link: {shareable_link}")

        # Add the shareable link to the tender
        tender.find_all('a')[0]['href'] = shareable_link

def fix_css_links(soup: BeautifulSoup):
    for link in soup.find_all('link', href=True):
        link['href'] = f"{base_url}{link['href']}"

def change_image_src(soup: BeautifulSoup):
    for img in soup.find_all('img'):
        img['src'] = f"https://wintersunset95.github.io/roadvisionlogo.jpg"

def remove_view_column(soup: BeautifulSoup):
    list_of_rows = soup.find_all('tr')
    # for every row in the table, remove the third column
    for row in list_of_rows:
        row.find_all('td')[2].decompose()

def insert_drive_links(soup: BeautifulSoup):
    soup2 = BeautifulSoup(open("./final.html"), 'html.parser')
    soup1_tenders_links = soup.find_all('p', attrs={'class': 'm-td-brief-link'})
    soup2_tenders_links = soup2.find_all('p', attrs={'class': 'm-td-brief-link'})

    # Replace the links in soup1 with the google drive links in soup2
    # Iterate through both lists at the same time
    for tender1, tender2 in zip(soup1_tenders_links, soup2_tenders_links):
        tender1.find_all('a')[0]['href'] = tender2.find_all('a')[0]['href']

def main():
    link = "https://www.tenderdetail.com/dailytenders/47136136/7c7651b5-98f3-4956-9404-913de95abb79"

    # driver = webdriver.Chrome()
    # driver.get(link)

    # Get page source from selenium
    # page = driver.page_source
    page = requests.get(link).content

    soup = BeautifulSoup(page, 'html.parser')

    # First lets do some search and replace
    owner_name = soup.find('p', attrs={'class': 'm-owner-name'})
    company_name = soup.find('p', attrs={'class': 'm-company-name'})
    support = soup.find_all('p', attrs={'class': 'm-r-date'})[1]
    if owner_name and company_name and support:
        owner_name.string = "Shubham Kanojia"
        company_name.string = "RoadVision AI Pvt. Ltd."
        support.string = "For customer support: (+91) 8115366981"

    tenders_links_list = soup.find_all('p', attrs={'class': 'm-td-brief-link'})
    remove_view_column(soup)
    # The following function should be commented if scrape_tenders is uncommented
    insert_drive_links(soup)
    # clean_project()
    # scrape_tenders(tenders_links_list, driver)
    change_image_src(soup)
    fix_css_links(soup)

    # Export the soup to a html file
    with open("output.html", "w") as f:
        f.write(str(soup.prettify()))

    final_html = transform(soup.prettify())
    final_html_soup = BeautifulSoup(final_html, 'html.parser')
    reformat_page(final_html_soup)
    # Export the final html to a html file
    with open("final.html", "w") as f:
        f.write(final_html_soup.prettify())

    send_html_email(final_html_soup)

# main()
detail = scrape_tender("https://www.tenderdetail.com/Indian-Tenders/TenderNotice/51705827/5E530F8D-3A76-4A23-8D77-0E0EB22B445B/147107/47136136/7c7651b5-98f3-4956-9404-913de95abb79")
print(detail)
