import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

# Page Configuration
st.set_page_config(page_title="Amazon USA - Anti-Block Generic Finder", layout="wide")
st.title("🛡️ Amazon USA Generic Product Finder (Anti-Block Version)")
st.write("This version uses residential proxies to bypass Amazon's 503 block screen.")

# User Input Sidebar
st.sidebar.header("Configuration")
# Input box for ScraperAPI Key
api_key = st.sidebar.text_input("Enter your ScraperAPI Key:", type="password")
st.sidebar.markdown("[Get a Free API Key here](https://www.scraperapi.com/) (5,000 free credits/month)")

keyword_input = st.sidebar.text_input("Enter Product Keyword:", "macrame wall hanging")
num_pages = st.sidebar.slider("Number of Pages to Scan", min_value=1, max_value=3, value=1)

# Target Countries for Sellers
TARGET_COUNTRIES = ["IN", "PK", "BD", "INDIA", "PAKISTAN", "BANGLADESH"]

def get_seller_country(asin, key):
    offers_url = f"https://www.amazon.com/gp/offer-listing/{asin}/"
    # Routing through ScraperAPI proxy
    proxy_url = f"http://api.scraperapi.com?api_key={key}&url={urllib.parse.quote(offers_url)}"
    
    try:
        response = requests.get(proxy_url, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().upper()
            for country in TARGET_COUNTRIES:
                if country in page_text:
                    return country
            return "Other/Unknown"
        return f"Proxy Error ({response.status_code})"
    except Exception:
        return "Timeout"

def search_amazon_generic(keyword, pages, key):
    products_list = []
    progress_bar = st.progress(0)
    
    for page in range(1, pages + 1):
        st.write(f"Scanning Page {page} via Secure Proxies...")
        search_url = f"https://www.amazon.com/s?k=generic+{keyword.replace(' ', '+')}&page={page}"
        # Routing search page through ScraperAPI proxy
        proxy_url = f"http://api.scraperapi.com?api_key={key}&url={urllib.parse.quote(search_url)}"
        
        try:
            response = requests.get(proxy_url, timeout=25)
            
            if response.status_code != 200:
                st.error(f"Proxy provider returned status code: {response.status_code}. Credits might be over.")
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
                    # Deep scan for target countries
                    seller_country = get_seller_country(asin, key)
                    
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

# Execution Trigger
if st.sidebar.button("Start Anti-Block Hunt 🚀"):
    if not api_key:
        st.error("⚠️ Please enter your ScraperAPI key in the sidebar first!")
    elif keyword_input:
        with st.spinner("Scraping Amazon USA securely via Rotating Proxies... Please wait."):
            df_results = search_amazon_generic(keyword_input, num_pages, api_key)
            
        if not df_results.empty:
            st.success(f"Successfully fetched {len(df_results)} safe Generic items!")
            st.dataframe(df_results, use_container_width=True)
            
            csv = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"amazon_generic_{keyword_input.replace(' ', '_')}.csv",
                mime='text/csv',
            )
        else:
            st.info("No matching items found. Try a different keyword or check API credits.")
