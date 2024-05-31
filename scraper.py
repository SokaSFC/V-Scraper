import os
import re
import time

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome import options as chrome_options


def get_pages(count=1, headless=False):
    """Fetch a specific count of result pages of property advertisements

    Args:
        count (int, optional): Number of result pages to fetch. Defaults to 1.
        headless (bool, optional): Whether to hide the browser. Defaults to False.

    Returns:
        list: pages HTML as utf-8 encoded bytes
    """

    pages = []

    driver = get_driver(headless=headless)

    for page_nb in range(1, count + 1):
        page_url = f"https://www.vinted.fr/catalog?catalog[]=4&status_ids[]=6&time=1717152368&page={page_nb}"
        driver.get(page_url)
        if page_nb == 1:
            time.sleep(15)
        else:
            time.sleep(10)
        pages.append(driver.page_source.encode("utf-8"))
    return pages


def get_driver(headless=False):
    """Returns a selenium firefox webdriver

    Args:
        headless (bool, optional): Whether to hide the browser. Defaults to False.

    Returns:
        selenium.webdriver.Firefox: firefox webdriver
    """
    if headless:
        options = chrome_options.Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Chrome()
    return driver


def save_pages(pages):
    """Saves HTML pages into the "data" folder

    Args:
        pages (list): list of pages as bytes
    """
    os.makedirs("data", exist_ok=True)
    for page_nb, page in enumerate(pages):
        with open(f"data/page_{page_nb}.html", "wb") as f_out:
            f_out.write(page)


def parse_pages():
    """Parse all pages from the data folder

    Returns:
        pd.DataFrame: parsed data
    """
    results = pd.DataFrame()
    pages_paths = os.listdir("data")
    for pages_path in pages_paths:
        with open(os.path.join("data", pages_path), "rb") as f_in:
            page = f_in.read().decode("utf-8")
            temp_df = parse_page(page)
            results = pd.concat([results, temp_df], ignore_index=True)
    return results


def parse_page(page):
    """Parses data from a HTML page and return it as a dataframe

    We can extract these items :
    - account_name (str)
    - likes (int)
    - boosted (bool)
    - brand (str)
    - size (str)
    - base_price (float)
    - commissioned_price (float)

    Args:
        page (bytes): utf-8 encoded HTML page

    Returns:
        pd.DataFrame: Parsed data
    """
    soup = BeautifulSoup(page, "html.parser")
    result = pd.DataFrame(columns=["account_name", "product_id"])

    # Trouver le parent commun des éléments 'account_name' et 'product_id'
    pattern = re.compile(r'product-item-id-(\d+)')
    parents = soup.find_all("div", attrs={"data-testid": pattern})

    for parent in parents:
        # Vérifier si l'élément a un enfant avec le même attribut 'data-testid'
        if parent.find(attrs={"data-testid": parent["data-testid"]}):
            # Sélectionner le parent parent dans ce cas
            parent = parent.find_parent("div", attrs={"data-testid": pattern})
            
        # Trouver l'élément 'account_name'
        p_tag = parent.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left")
        if p_tag:
            account_name = clean_account_name(p_tag)

            # Trouver l'élément 'product_id'
            product_id = clean_product_id(parent["data-testid"])

            if product_id:
                temp_df = pd.DataFrame({
                    "account_name": [account_name],
                    "product_id": [product_id]
                })

                result = pd.concat([result, temp_df], ignore_index=True)
#    for item in items:
#        p_tag = item.find("p", class_="web_ui__Text__text web_ui__Text__caption web_ui__Text__left")
#        if p_tag:
#            account_name = clean_account_name(p_tag)
#            product_id = clean_product_id(item["data-testid"])
#
#            temp_df = pd.DataFrame({
#                "account_name": [account_name],
#                "product_id": [product_id]
#            })
#
#            result = pd.concat([result, temp_df], ignore_index=True)

    return result


     #account_names = [
    #    clean_account_name(tag) for tag in soup.find_all(attrs={"data-testid": pattern})
    #]
    #result["likes"] = [
    #    clean_type(tag) for tag in soup.find_all(attrs={"class": "web_ui__Text__text web_ui__Text__caption web_ui__Text__left"})
    #]
    #result["boosted"] = [
    #    clean_surface(tag)
    #    for tag in soup.find_all(attrs={"class": "announceDtlInfos announceDtlInfosArea"})
    ##]
    #result["brand"] = [
    #    clean_rooms(tag)
    #    for tag in soup.find_all(attrs={"class": "announceDtlInfos announceDtlInfosNbRooms"})
    #]
    #result["size"] = [
    #    clean_postal_code(tag) for tag in soup.find_all(attrs={"class": "announcePropertyLocation"})
    #]
    #result["base_price"] = [
    #    tag.text.strip() for tag in soup.find_all(attrs={"class": "announceDtlDescription"})
    #]
    #result["commissioned_price"] = [
    #    tag.text.strip() for tag in soup.find_all(attrs={"class": "announceDtlDescription"})



def clean_account_name(tag):
    text = tag.text.strip()
    return text

def clean_product_id(testid_str):
    product_id_pattern = r'product-item-id-(\d+)'
    match = re.search(product_id_pattern, testid_str)
    if match:
        return match.group(1)
    else:
        return None


#def clean_type(tag):
#    text = tag.text.strip()
#    return text.replace("Location ", "")


#def clean_surface(tag):
#    text = tag.text.strip()
#    return int(text.replace("m²", ""))


#def clean_rooms(tag):
#    text = tag.text.strip()
#    rooms = int(text.replace("p.", "").replace(" ", ""))
#    return rooms


#def clean_postal_code(tag):
#    text = tag.text.strip()
#    match = re.match(".*\(([0-9]+)\).*", text)
#    return match.groups()[0]


def main():
    pages = get_pages(count=2)
    save_pages(pages)


if __name__ == "__main__":
    main()