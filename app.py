import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import re

# Page Configuration
st.set_page_config(page_title="Amazon USA - Generic Product Finder", layout="wide")
st.title("🔍 Amazon USA Generic Product Finder (Target: South Asian Sellers)")
st.write("Enter keywords to find Generic products on Amazon.com sold by Indian, Pakistani, or Bangladeshi sellers via FBM.")

# User Input Sidebar
st.sidebar.header("Scraping Parameters")
keyword_input = st.sidebar.text_input("Enter Product Keyword (e.g., macrame, leather journal)", "macrame wall hanging")
num_pages = st.sidebar.slider("Number of Pages to Scan", min_value=1, max_value=5, value=1)

# Target Countries for Sellers
TARGET_COUNTRIES = ["IN", "PK", "BD", "INDIA", "PAKISTAN", "BANGLADESH"]

# Headers to avoid Amazon Captcha/Blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/"
}

def get_seller_country(asin):
    """
    Fetches the seller's country by looking at the 'All Offers' page for the ASIN.
    """
    offers_url = f"https://www.amazon.com/gp/offer-listing/{asin}/"
    try:
        # Deliberate small delay to mimic human behavior
        time.sleep(random.uniform(1.0, 2.5))
        response = requests.get(offers_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().upper()
            
            # Simple keyword matching for seller origin in page source
            for country in TARGET_COUNTRIES:
                if country in page_text:
                    return country
        return "Other/Unknown"
    except Exception:
        return "Error/Blocked"

def search_amazon_generic(keyword, pages):
    products_list = []
    
    # UI Progress Bar
    progress_bar = st.progress(0)
    
    for page in range(1, pages + 1):
        st.write(f"Scanning Page {page}...")
        search_url = f"https://www.amazon.com/s?k=generic+{keyword.replace(' ', '+')}&page={page}"
        
        try:
            time.sleep(random.uniform(2.0, 4.0))
            response = requests.get(search_url, headers=HEADERS, timeout=15)
            
            if response.status_code != 200:
                st.warning(f"Amazon blocked the request on Page {page} (Status Code: {response.status_code}). Try again later.")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            # Amazon search result blocks
            results = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for index, item in enumerate(results):
                # 1. ASIN
                asin = item.get('data-asin')
                if not asin:
                    continue
                    
                # 2. Title
                title_element = item.find('h2', {'class': 'a-size-mini'})
                title = title_element.text.strip() if title_element else "No Title"
                
                # 3. Product Link
                link_element = item.find('a', {'class': 'a-link-normal s-no-outline'})
                link = f"https://www.amazon.com{link_element.get('href')}" if link_element else "No Link"
                
                # Filter strictly for 'Generic' keyword in title or URL as a safety check
                if "generic" in title.lower() or "generic" in link.lower():
                    # 4. Seller Country Check (Deep Scan)
                    seller_country = get_seller_country(asin)
                    
                    # Filtering only requested origins
                    if seller_country in TARGET_COUNTRIES or seller_country == "Other/Unknown":
                        products_list.append({
                            "ASIN": asin,
                            "Title Name": title,
                            "Product Link": link,
                            "Seller Country": seller_country
                        })
                        
            # Update progress
            progress_bar.progress(int((page / pages) * 100))
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            break
            
    return pd.DataFrame(products_list)

# Main App Execution Trigger
if st.sidebar.button("Start Product Hunt 🚀"):
    if keyword_input:
        with st.spinner("Scraping Amazon USA... Please hold tight (mimicking human browsing to prevent bans)"):
            df_results = search_amazon_generic(keyword_input, num_pages)
            
        if not df_results.empty:
            st.success(f"Found {len(df_results)} potential Generic items!")
            
            # Displaying the Dataframe
            st.dataframe(df_results, use_container_width=True)
            
            # Export Options
            csv = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"amazon_generic_{keyword_input.replace(' ', '_')}.csv",
                mime='text/csv',
            )
        else:
            st.info("No matching Generic items found with South Asian seller footprint. Try another keyword or expand pages.")
    else:
        st.error("Please enter a keyword first.")
