from typing import List, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag
import requests

from data_models import TenderDetailContactInformation, TenderDetailDetails, TenderDetailKeyDates, TenderDetailNotice, TenderDetailOtherDetail, TenderDetailPage, TenderDetailPageFile

def scrape_notice_table(table: Tag) -> TenderDetailNotice:
    # 14 rows in the notice table
    # Row one is table name, Ignore
    # Remaining rows are as follows:
    # 1. TDR
    # 2. Tendering Authority
    # 3. Tender No
    # 4. Tender ID
    # 5. Tender Brief
    # 6. City
    # 7. State
    # 8. Document Fees
    # 9. EMD
    # 10. Tender Value
    # 11. Tender Type
    # 12. Bidding Type
    # 13. Competition Type
    rows = table.find_all('tr')
    if not len(rows) == 14:
        raise Exception("Tender notice table has incorrect number of rows")

    tdr = rows[1].find_all('td')[1].text
    tendering_authority = rows[2].find_all('td')[1].text
    tender_no = rows[3].find_all('td')[1].text
    tender_id = rows[4].find_all('td')[1].text
    tender_brief = rows[5].find_all('td')[1].text
    city = rows[6].find_all('td')[1].text
    state = rows[7].find_all('td')[1].text
    document_fees = rows[8].find_all('td')[1].text
    emd = rows[9].find_all('td')[1].text
    tender_value = rows[10].find_all('td')[1].text
    tender_type = rows[11].find_all('td')[1].text
    bidding_type = rows[12].find_all('td')[1].text
    competition_type = rows[13].find_all('td')[1].text

    return TenderDetailNotice(
        tdr=tdr,
        tendering_authority=tendering_authority,
        tender_no=tender_no,
        tender_id=tender_id,
        tender_brief=tender_brief,
        city=city,
        state=state,
        document_fees=document_fees,
        emd=emd,
        tender_value=tender_value,
        tender_type=tender_type,
        bidding_type=bidding_type,
        competition_type=competition_type
    )

def scrape_details(table: Tag) -> TenderDetailDetails:
    # This table will have a paragraph that contains all the details
    p = table.find('p')
    if not p:
        raise Exception("Tender details table does not have a paragraph")
    return TenderDetailDetails(tender_details=p.text)

def scrape_key_dates(table: Tag) -> TenderDetailKeyDates:
    # This table has 4 rows:
    # 1. Table name
    # 2. Publish Date
    # 3. Last Date of Bid Submission
    # 4. Tender Opening Date
    rows = table.find_all('tr')
    if not len(rows) == 4:
        raise Exception("Tender key dates table has incorrect number of rows")

    publish_date = rows[1].find_all('td')[1].text
    last_date_of_bid_submission = rows[2].find_all('td')[1].text
    tender_opening_date = rows[3].find_all('td')[1].text

    return TenderDetailKeyDates(
        publish_date=publish_date,
        last_date_of_bid_submission=last_date_of_bid_submission,
        tender_opening_date=tender_opening_date
    )

def scrape_contact_information(table: Tag) -> TenderDetailContactInformation:
    # This table has 4 rows:
    # 1. Table name
    # 2. Company Name
    # 3. Contact Person
    # 4. Address
    rows = table.find_all('tr')
    if not len(rows) == 4:
        raise Exception("Tender contact information table has incorrect number of rows")

    company_name = rows[1].find_all('td')[1].text
    contact_person = rows[2].find_all('td')[1].text
    address = rows[3].find_all('td')[1].text

    return TenderDetailContactInformation(
        company_name=company_name,
        contact_person=contact_person,
        address=address
    )

def scrape_other_details(table: Tag) -> TenderDetailOtherDetail:
    # This table has 4 rows:
    # 1. Table name
    # 2. Information source
    # 3. Another sub-table with variable number of rows containing the following columns:
    #     1. File name
    #     2. File type
    #     3. File size
    #     4. File link
    #   The first row is the column names and should be ignored
    # 4. Empty row
    rows = table.find_all('tr', recursive=False)
    if not len(rows) == 4:
        raise Exception("Tender other details table has incorrect number of rows")

    # Information source
    information_source = rows[1].find_all('td')[1].text

    # Another sub-table
    sub_table = rows[2]
    if not sub_table:
        raise Exception("Tender other details table does not have a sub-table")
    sub_table_rows = sub_table.find_all('tr')
    if not len(sub_table_rows) > 0:
        raise Exception("Tender other details table sub-table has incorrect number of rows")

    # Ignoring the first row, iterate through the remaining rows
    files: List[TenderDetailPageFile] = []
    for i in range(1, len(sub_table_rows)):
        file_row = sub_table_rows[i]
        url_element = file_row.find('a')
        if not url_element:
            raise Exception("Tender other details table sub-table does not have a link")
        file_link = url_element.attrs['href']
        file_name = file_row.find_all('td')[1].text
        file_type = file_row.find_all('td')[2].text
        file_size = file_row.find_all('td')[3].text
        files.append(TenderDetailPageFile(
            file_name=file_name,
            file_url=str(file_link),
            file_description=file_type,
            file_size=file_size
        ))

    return TenderDetailOtherDetail(
        information_source=information_source,
        files=files
    )


def scrape_tender(tender_link) -> TenderDetailPage:
    page = requests.get(tender_link)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Every tender page will have a tender-details-home class that contains all the content
    tender_details_home = soup.find('div', attrs={'class': 'tender-details-home'})
    if not tender_details_home:
        raise Exception("Tender details home not found")

    # Tender details home will have 5 tables in the order:
    # 1. Tender Notice
    # 2. Tender Details
    # 3. Key Dates
    # 4. Contact Information
    # 5. Other Detail
    tender_details_tables = tender_details_home.find_all('table', recursive=False)
    if not tender_details_tables:
        raise Exception("Tender details tables not found")
    if not len(tender_details_tables) == 5:
        raise Exception("Tender details tables not found")


    # Tender notice table
    tender_notice_table = tender_details_tables[0]
    if not tender_notice_table:
        raise Exception("Tender notice table not found")

    # Tender details table
    tender_details_table = tender_details_tables[1]
    if not tender_details_table:
        raise Exception("Tender details table not found")

    # Key dates table
    key_dates_table = tender_details_tables[2]
    if not key_dates_table:
        raise Exception("Key dates table not found")

    # Contact information table
    contact_information_table = tender_details_tables[3]
    if not contact_information_table:
        raise Exception("Contact information table not found")

    # Other details table
    other_details_table = tender_details_tables[4]
    if not other_details_table:
        raise Exception("Other details table not found")

    notice = scrape_notice_table(tender_notice_table)
    details = scrape_details(tender_details_table)
    key_dates = scrape_key_dates(key_dates_table)
    contact_information = scrape_contact_information(contact_information_table)
    other_detail = scrape_other_details(other_details_table)

    return TenderDetailPage(
        notice=notice,
        details=details,
        key_dates=key_dates,
        contact_information=contact_information,
        other_detail=other_detail
    )
