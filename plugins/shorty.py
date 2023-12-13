import os
import requests
import logging
import pyshorteners
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

urlshortx_api_token = os.environ.get('URL_SHORTENER_API_KEY')

def shorten_url(url):
    try:
        api_url = f"https://urlshortx.com/api"
        params = {
            "api": urlshortx_api_token,
            "url": url,
            "format": "text"
        }
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            return response.text.strip()
        else:
            logger.error(
                f"URL shortening failed. Status code: {response.status_code}, Response: {response.text}")
            return url
    except Exception as e:
        logger.error(f"URL shortening failed: {e}")
        return url
    
def tiny(long_url):
    s = pyshorteners.Shortener()
    try:
        short_url = s.clckru.short(long_url)
        return short_url
    except Exception:
        logger.error(f'Failed to shorten URL: {long_url}')
        return long_url
