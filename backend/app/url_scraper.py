"""
url_scraper.py — Job URL Scraper
Selenium optional — works without it on Railway/cloud
"""
import requests
from bs4 import BeautifulSoup

# Try Selenium — optional
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    pass

def scrape_job_from_url(url: str) -> dict:
    """Scrape job details from URL — requests first, Selenium fallback."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res  = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script","style","nav","footer"]): tag.decompose()

        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        # Main content
        body = soup.get_text(separator=" ", strip=True)[:3000]

        return {
            "success":         True,
            "job_title":       title_text,
            "job_description": body,
            "url":             url,
            "method":          "requests+bs4",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "job_description": ""}

# Alias
scrape_job_url = scrape_job_from_url
