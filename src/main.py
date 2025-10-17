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
from drive import authenticate_google_drive, download_folders, get_shareable_link, upload_folder_to_drive
from email_sender import send_html_email
from home_page_scrape import scrape_page
from templater import generate_email, reformat_page

load_dotenv()

GOOGLE_DRIVE_PARENT_FOLDER = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER")
base_url = "https://www.tenderdetail.com"
tdr_xpath = "/html/body/div/div[1]/section[2]/div[1]/div/div/table[1]/tbody/tr[2]/td[2]"

def clean_project():
    # First lets clear the tenders/ directory
    os.system("rm -rf tenders/")
    # Create the tenders/ directory
    os.mkdir("tenders/")

def insert_drive_links(soup: BeautifulSoup):
    soup2 = BeautifulSoup(open("./final.html"), 'html.parser')
    soup1_tenders_links = soup.find_all('a', attrs={'class': 'tender_table_view_tender_link'})
    soup2_tenders_links = soup2.find_all('p', attrs={'class': 'm-td-brief-link'})

    # Replace the links in soup1 with the google drive links in soup2
    # Iterate through both lists at the same time
    for tender1, tender2 in zip(soup1_tenders_links, soup2_tenders_links):
        tender1['href'] = tender2.find_all('a')[0]['href']

def main():
    link = input("Enter link: ")
    if link == "":
        link = "https://www.tenderdetail.com/dailytenders/47136136/7c7651b5-98f3-4956-9404-913de95abb79"
    homepage = scrape_page(link)
    for query_table in homepage.query_table:
        print("Current query: " + query_table.query_name)
        for tender in query_table.tenders:
            tender.details = scrape_tender(tender.tender_url)
    download_folders(homepage)
    generated_template = generate_email(homepage)

    with open("email.html", "w") as f:
        f.write(generated_template.prettify())

    send_html_email(generated_template)

main()
