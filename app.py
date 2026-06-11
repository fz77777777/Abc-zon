import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random

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

# Advanced rotation of User-Agents to mimic different browsers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def get_seller_country(asin):
    offers_url = f"https://www.amazon.com/gp/offer-listing/{asin}/"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.amazon.com/"
    }
    try:
        time.sleep(random.uniform(2.0, 4.0)) # Increased delay
        response = requests.get(offers_url, headers=headers, timeout=12)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().upper()
            for country in TARGET_COUNTRIES:
                if country in page_text:
                    return country
            return "Other/Unknown"
        return f"Block ({response.status_code})"
    except Exception:
        return "Timeout"

def search_amazon_generic(keyword, pages):
    products_list = []
    progress_bar = st.progress(0)
    
    for page in range(1, pages + 1):
        st.write(f"Scanning Page {page}...")
        search_url = f"https://www.amazon.com/s?k=generic+{keyword.replace(' ', '+')}&page={page}"
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }
        
        try:
            time.sleep(random.uniform(3.0, 6.0)) # Slower scraping helps prevent 503
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                st.error(f"Amazon blocked the request on Page {page} (Status Code: {response.status_code}). Try scanning fewer pages or running locally.")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for index, item in enumerate(results):
                asin = item.get('data-asin')
                if not asin:
                    continue
                    
                title_element = item.find('h2', {'class': 'a-size-mini'})
                title = title_element.text.strip() if title_element else "No Title"
                
                link_element = item.find('a', {'class': 'a-link-normal s-no-outline'})
                link = f"https://www.amazon.com{link_element.get('href')}" if link_element else "No Link"
                
                if "generic" in title.lower() or "generic" in link.lower():
                    seller_country = get_seller_country(asin)
                    
                    if seller_country in TARGET_COUNTRIES or seller_country == "Other/Unknown":
                        products_list.append({
                            "ASIN": asin,
                            "Title Name": title,
                            "Product Link": link,
                            "Seller Country": seller_country
                        })
                        
            progress_bar.progress(int((page / pages) * 100))
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            break
            
    return pd.DataFrame(products_list)

# Main App Execution Trigger
if st.sidebar.button("Start Product Hunt 🚀"):
    if keyword_input:
        with st.spinner("Scraping Amazon USA... Please wait"):
            df_results = search_amazon_generic(keyword_input, num_pages)
            
        if not df_results.empty:
            st.success(f"Successfully fetched {len(df_results)} potential Generic items!")
            st.dataframe(df_results, use_container_width=True)
            
            csv = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"amazon_generic_{keyword_input.replace(' ', '_')}.csv",
                mime='text/csv',
            )
        else:
            st.info("No matching Generic items found due to strict Amazon anti-bot shields. Try later or scale down the scan pages.")
    else:
        st.error("Please enter a keyword first.")
