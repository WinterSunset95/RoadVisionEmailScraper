from bs4 import BeautifulSoup

from data_models import HomePageData

def apply_multi_column_table_layout(soup, container_element, align_last_right=False):
    """
    Takes a container element and rearranges its direct children into a table
    with evenly spaced columns. This is the email-safe way to create a
    multi-item, evenly-spaced layout.

    Args:
        soup (BeautifulSoup): The main soup object.
        container_element (Tag): The parent element whose children will be arranged.
        align_last_right (bool): If True, aligns the last item to the right, mimicking
                                space-between for 2+ items.
    """
    # Find all direct children to be arranged. 'recursive=False' is key here.
    children = container_element.find_all(recursive=False)
    
    # If there's nothing to do, just exit.
    if not children:
        return

    num_children = len(children)
    # Calculate the percentage width for each column.
    col_width = int(100 / num_children)

    # --- Create the new table structure ---
    table = soup.new_tag('table', width="100%", border="0", cellpadding="0", cellspacing="0")
    tr = soup.new_tag('tr')
    table.append(tr)

    print(f"Applying {num_children}-column table layout...")

    # --- Loop through each child and create a cell for it ---
    for i, child in enumerate(children):
        # Base style for all cells
        style = f"width: {col_width}%; vertical-align: top;"

        # Add specific text alignment
        if align_last_right and num_children > 1:
            if i == 0:
                style += " text-align: left;"  # First item
            elif i == num_children - 1:
                style += " text-align: right;" # Last item
            else:
                style += " text-align: center;" # Middle items
        else:
            style += " text-align: left;" # Default alignment for all

        # Create the table cell (td) with the calculated style
        td = soup.new_tag('td', style=style)
        
        # .extract() removes the child from its original location
        td.append(child.extract())
        
        # Add the new cell to our table row
        tr.append(td)

    # --- Finalize the container ---
    # Clear out any old inline styles (like display:flex)
    container_element.attrs.pop('style', None)
    
    # Add the newly created table into the now-empty container
    container_element.append(table)


def reformat_page(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Refactors an entire HTML page (as a BeautifulSoup object) to use email-safe
    table layouts instead of CSS Flexbox.
    """
    print("🚀 Starting HTML reformatting for email compatibility...")

    # --- Section 1: Image Header ---
    img_element = soup.find('img')
    if img_element:
        # Set email-safe image styles
        img_element.attrs['style'] = "width:100px; height:auto; display:block;"
        # The container is two levels above the image
        img_parent_container = img_element.parent.parent
        if img_parent_container:
            print("Applying table layout to image header...")
            apply_multi_column_table_layout(soup, img_parent_container, align_last_right=True)

    # --- Section 2: Owner Name ---
    owner = soup.find('p', attrs={'class': 'm-owner-name'})
    if owner:
        # The container is two levels above the owner p tag
        owner_parent_container = owner.parent.parent
        if owner_parent_container:
            print("Applying table layout to owner section...")
            apply_multi_column_table_layout(soup, owner_parent_container, align_last_right=True)

    # --- Section 3: Main Transaction Rows ---
    mainTR_list = soup.find_all('div', attrs={'class': 'm-mainTR'})
    for mainTR in mainTR_list:
        rows = mainTR.find_all('div', attrs={'class': 'row'})
        
        # Handle the specific case for company and place in the first row
        if len(rows) >= 1:
            row1 = rows[0]
            company = row1.find('div', attrs={'class': 'col-md-8'})
            place = row1.find('div', attrs={'class': 'col-md-4'})

            if company and place:
                print("Applying specific 2-column table to company/place row...")
                # This logic is already a perfect 2-column table, so we keep it.
                table = soup.new_tag('table', width="100%", border="0", cellpadding="0", cellspacing="0", role="presentation")
                tr = soup.new_tag('tr')
                table.append(tr)
                td_left = soup.new_tag('td', style="width: 50%; text-align: left; vertical-align: top;")
                td_left.append(company.extract())
                tr.append(td_left)
                td_right = soup.new_tag('td', style="width: 50%; text-align: right; vertical-align: top;")
                td_right.append(place.extract())
                tr.append(td_right)
                row1.insert(0, table)

        # Handle any other rows that need a general multi-column layout
        if len(rows) >= 2:
            row2 = rows[1]
            print("Applying table layout to the second row...")
            apply_multi_column_table_layout(soup, row2, align_last_right=True)
            
    print("✅ HTML reformatting complete.")
    return soup


def generate_email(data: HomePageData) -> str:
    """
    Generates an email HTML string from a HomePageData object.
    """
    # Import the exsiting HTML template
    with open('./template.html', 'r') as f:
        template_html = f.read()

    # Create a new BeautifulSoup object from the template HTML
    soup = BeautifulSoup(template_html, 'html.parser')

    # Search and replace variables in the template
