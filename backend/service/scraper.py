import re
from bs4 import BeautifulSoup
from fastapi import HTTPException
from curl_cffi import requests

def scrape_vinted_pool(keyword: str, query_params: str) -> list:
    """Hits the public Vinted catalog endpoint with exact profile constraints."""
    url = f"https://www.vinted.co.uk/catalog?&{query_params}&order=newest_first"

    print(f"\n[INFO] Target Scraping URL Generated: {url}\n")

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Connection": "keep-alive"
    }

    try:
        response = requests.get(url, headers=headers, impersonate="chrome124", timeout=10)
        
        if response.status_code != 200:
            print(f"\n[ERROR] Vinted responded with bad status: {response.status_code} \n {response.text}")
            raise HTTPException(status_code=502, detail="Vinted protection wall blocked request")
        
        soup = BeautifulSoup(response.text, "html.parser")
        items_pool = []
        seen_urls = set()
        
        for item_div in soup.find_all("div", class_=re.compile(r"feed-grid__item|item-box")):
            img_tag = item_div.find("img")
            link_tag = item_div.find("a", href=True)
            
            if img_tag and link_tag:
                img_url = img_tag.get("src") or img_tag.get("data-src")
                href = link_tag["href"]
                title = img_tag.get("alt", "Secondhand Item")
                
                if img_url and "images1.vinted.net" in img_url:
                    full_href = href if href.startswith("http") else f"https://www.vinted.co.uk{href}"
                    
                    if full_href in seen_urls:
                        continue
                        
                    seen_urls.add(full_href)
                    items_pool.append({
                        "title": title,
                        "url": full_href,
                        "image_url": img_url
                    })
                    
            if len(items_pool) >= 150: 
                break
                
        print(f"[SUCCESS] Collected {len(items_pool)} unique, deduplicated items.")
        return items_pool
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper sub-system error: {str(e)}")