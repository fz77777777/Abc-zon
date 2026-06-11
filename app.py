import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

# Page Configuration
st.set_page_config(page_title="Amazon USA - Fast Generic Finder", layout="wide")
st.title("⚡ Amazon USA Generic Product Finder (Fast Mode)")
st.write("This updated version extracts products instantly in a single request to prevent hanging/freezing.")

# User Input Sidebar
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your ScraperAPI Key:", type="password")
keyword_input = st.sidebar.text_input("Enter Product Keyword:", "macrame wall hanging")
num_pages = st.sidebar.slider("Number of Pages to Scan", min_value=1, max_value=3, value=1)

def search_amazon_fast(keyword, pages, key):
    products_list = []
    
    # Cleaning keyword for URL
    clean_keyword = keyword.replace(' ', '+')
    
    for page in range(1, pages + 1):
        st.write(f"🔄 Scanning Page {page}...")
        search_url = f"https://www.amazon.com/s?k=generic+{clean_keyword}&page={page}"
        proxy_url = f"http://api.scraperapi.com?api_key={key}&url={urllib.parse.quote(search_url)}"
        
        try:
            # Single proxy call per page
            response = requests.get(proxy_url, timeout=30)
            
            if response.status_code != 200:
                st.error(f"Proxy issues or Key limit reached (Status: {response.status_code})")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # Amazon search results container list
            results = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for item in results:
                asin = item.get('data-asin')
                if not asin:
                    continue
                    
                # Extract Title
                title_element = item.find('h2', {'class': 'a-size-mini'})
                title = title_element.text.strip() if title_element else "Generic Item"
                
                # Check for South Asian foot-print directly in the snippet text
                item_text = item.get_text().upper()
                
                # Default logic: track if likely from South Asia, or label as Generic FBM
                seller_type = "Generic FBM / Potential South Asian"
                if any(x in item_text for x in ["INDIA", "PAKISTAN", "BANGLADESH", "SHIPS FROM INTERNATIONAL"]):
                    seller_type = "Verified South Asian Origin"
                
                products_list.append({
                    "ASIN": asin,
                    "Title Name": title[:90] + "..." if len(title) > 90 else title,
                    "Product Link": f"https://www.amazon.com/dp/{asin}",
                    "Status/Origin": seller_type
                })
                
        except Exception as e:
            st.error(f"Error on page {page}: {e}")
            break
            
    return pd.DataFrame(products_list)

# Execution Button
if st.sidebar.button("Start Fast Hunt 🚀"):
    if not api_key:
        st.error("⚠️ Sidebar me apni ScraperAPI Key paste kijiye!")
    elif keyword_input:
        with st.spinner("Fetching listings directly from Amazon USA... Please wait 10 seconds."):
            df_results = search_amazon_fast(keyword_input, num_pages, api_key)
            
        if not df_results.empty:
            st.success(f"Boom! Found {len(df_results)} active Generic items!")
            st.dataframe(df_results, use_container_width=True)
            
            csv = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV File",
                data=csv,
                file_name=f"amazon_generic_listings.csv",
                mime='text/csv',
            )
        else:
            st.warning("No Generic items captured. Try changing the keyword (e.g., 'handmade wooden spoon' or 'oxidized jewelry').")
