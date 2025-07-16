import json
import os
import re
import time
from typing import Dict, List, Optional

import feedparser
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 全域設定：工作目錄為 /data
os.makedirs("/data", exist_ok=True)
os.chdir("/data")

# 瀏覽器二進位與 driver 路徑
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium-browser")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")


def get_driver() -> webdriver.Chrome:
    options = Options()
    options.binary_location = CHROME_BIN
    for arg in ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]:
        options.add_argument(arg)
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)


def extract_apple_urls(podcast_url: str, output_file: str = "apple_urls.json") -> None:
    driver = get_driver()
    driver.get(podcast_url)
    try:
        wait = WebDriverWait(driver, 15)
        tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="熱門節目"]')))
        tab.click()
        time.sleep(3)
        prev, stable = 0, 0
        while stable < 10:
            driver.find_element(By.TAG_NAME, "body").send_keys("\ue00f")  # PAGE_DOWN
            time.sleep(0.5)
            els = driver.find_elements(By.XPATH, '//a[@data-testid="product-lockup-link"]')
            cnt = len(els)
            if cnt == prev:
                stable += 1
            else:
                prev, stable = cnt, 0
        seen, urls = set(), []
        for el in els:
            href = el.get_attribute("href")
            if href and href not in seen:
                seen.add(href)
                urls.append({"apple_url": href})
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(urls, f, ensure_ascii=False, indent=2)
    finally:
        driver.quit()


def extract_feed_url(apple_url: str) -> Optional[str]:
    try:
        res = requests.get(apple_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        m = re.search(r'"feedUrl"\s*:\s*"([^"]+)"', res.text)
        if m:
            u = m.group(1)
            if u.startswith("//"):
                u = "https:" + u
            return u
    except:
        pass
    return None


def safe_filename(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z_\-]", "_", text)[:80]


def process_metadata(item: Dict[str, str], idx: int, total: int, out_dir: str) -> None:
    url = item.get('apple_url', '')
    print(f"[{idx}/{total}] Scraping metadata: {url}")
    # 先爬前端資訊
    driver = get_driver()
    try:
        driver.get(url)
        time.sleep(5)
        wait = WebDriverWait(driver, 10)
        title = wait.until(lambda d: d.find_element(By.TAG_NAME, 'h1')).text
        prov_elems = driver.find_elements(By.CSS_SELECTOR, 'span.provider')
        provider = prov_elems[0].text if prov_elems else ''
        rating_elems = driver.find_elements(By.XPATH, '//li[contains(@aria-label, "則評分")]')
        rating = rating_elems[0].text if rating_elems else ''
        cat_elems = driver.find_elements(By.CSS_SELECTOR, 'li.category a')
        category = cat_elems[0].text if cat_elems else ''
        desc_elems = driver.find_elements(By.CSS_SELECTOR, 'p[data-testid="truncate-text"]')
        description = desc_elems[0].text if desc_elems else ''
    except Exception as e:
        print(f"Error scraping metadata fields for {url}: {e}")
    finally:
        driver.quit()

    # 透過 iTunes RSS API 抓取評論
    pid_match = re.search(r"id(\d+)", url)
    pid = pid_match.group(1) if pid_match else ''
    comments: List[str] = []
    if pid:
        review_url = f"https://itunes.apple.com/tw/rss/customerreviews/id={pid}/sortBy=mostRecent/json"
        try:
            resp = requests.get(review_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            data = resp.json()
            entries = data.get('feed', {}).get('entry', [])
            # 第一筆是節目本身，從第二筆開始是評論
            for rev in entries[1:]:
                text = rev.get('content', {}).get('label', '').strip()
                if text:
                    comments.append(text)
            print(f"  Retrieved {len(comments)} comments via RSS API")
        except Exception as e:
            print(f"Error fetching reviews API: {e}")

    # 組裝並寫出 JSON
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"podcast_{pid}.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            "title": title,
            "provider": provider,
            "rating": rating,
            "category": category,
            "description": description,
            "comments": comments,
            "url": url,
            "id": pid
        }, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {out_path}")


def process_rss(item: Dict[str, str], idx: int, total: int, out_dir: str) -> None:
    rss = item.get('feed_url')
    if not rss:
        return
    try:
        feed = feedparser.parse(rss)
        episodes = []
        for e in feed.entries:
            episodes.append({
                "id": e.get('id') or safe_filename(e.get('title', '')),
                "title": e.get('title', ''),
                "published": e.get('published', ''),
                "description": e.get('summary', ''),
                "audio_url": e.enclosures[0].href if e.enclosures else None
            })
        os.makedirs(out_dir, exist_ok=True)
        pid_match = re.search(r"id(\d+)", item.get('apple_url', ''))
        pid = pid_match.group(1) if pid_match else ''
        out_path = os.path.join(out_dir, f"RSS_{pid}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(episodes, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def main() -> None:
    extract_apple_urls("https://podcasts.apple.com/tw/charts?genre=1304")
    urls = json.load(open('apple_urls.json', 'r', encoding='utf-8'))
    part = urls[:100]
    with open('apple_urls_part_0_100.json', 'w', encoding='utf-8') as f:
        json.dump(part, f, ensure_ascii=False, indent=2)
    rss_list = []
    for u in part:
        rss_list.append({**u, 'feed_url': extract_feed_url(u['apple_url'])})
    meta_dir = "/data/data_outputs_1304"
    for idx, item in enumerate(rss_list, start=1):
        process_metadata(item, idx, len(rss_list), meta_dir)
    rss_dir = "/data/rss_outputs_1304"
    for idx, item in enumerate(rss_list, start=1):
        process_rss(item, idx, len(rss_list), rss_dir)

if __name__ == '__main__':
    main()
