import re
import logging
from typing import TYPE_CHECKING
from bs4 import BeautifulSoup
from fastapi import HTTPException
from curl_cffi import requests
from dtos import SearchItem
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from api.models import FetchInitialRequest


def build_query_params(request: "FetchInitialRequest") -> str:
    """Translate a fetch_initial request into Vinted catalog query params."""
    keyword = request.keyword.replace(" ", "+")
    from service.static.CONSTANTS import COLOUR_MAP, VINTED_CATEGORY_MAP as _CAT

    catalog_id = _CAT.get(request.selectedCategory, "")
    colour_ids = []
    for c_name in request.selectedColors.split(","):
        if c_name in COLOUR_MAP.keys():
            colour_ids.extend(COLOUR_MAP.get(c_name))

    query_params = f"search_text={keyword}"
    if catalog_id:
        query_params += f"&catalog[]={catalog_id}"
    if colour_ids:
        for c_id in colour_ids:
            query_params += f"&color_ids[]={c_id}"
    if request.selectedSizes:
        for size_id in request.selectedSizes.split(","):
            query_params += f"&size_ids[]={size_id}"
    if request.maxPrice:
        query_params += f"&price_to={request.maxPrice}&currency=GBP"
    if request.selectedConditions:
        for cid in request.selectedConditions.split(","):
            if cid:
                query_params += f"&status_ids[]={cid}"
    return query_params

def scrape_vinted_pool(query_params: str) -> set[SearchItem]:
    """Hits the public Vinted catalog endpoint with exact profile constraints."""
    url = f"https://www.vinted.co.uk/catalog?&{query_params}"

    logger.info(f"\nTarget Scraping URL Generated: {url}\n")

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Connection": "keep-alive"
    }

    try:
        response = requests.get(url, headers=headers, impersonate="chrome124", timeout=10)
        
        if response.status_code != 200:
            logger.error(f"\nVinted responded with bad status: {response.status_code} \n {response.text}")
            raise HTTPException(status_code=502, detail="Vinted protection wall blocked request")
        
        soup = BeautifulSoup(response.text, "html.parser")
        items_pool = set()
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
                    items_pool.add(SearchItem(title=title, url=full_href, image_url=img_url))
            if len(items_pool) >= 150: 
                break
                
        logger.info(f"Collected {len(items_pool)} unique, deduplicated items.")
        return items_pool
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper sub-system error: {str(e)}")