import json
import os
import re
import time
from typing import Dict, List, Optional

import feedparser
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
            for _ in range(5):
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
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
    driver = get_driver()
    driver.get(url)
    time.sleep(5)
    try:
        wait = WebDriverWait(driver, 10)
        title = wait.until(lambda d: d.find_element(By.TAG_NAME, 'h1')).text
        prov = driver.find_element(By.CSS_SELECTOR, 'span.provider').text if driver.find_elements(By.CSS_SELECTOR, 'span.provider') else ''
        rating = driver.find_element(By.XPATH, '//li[contains(@aria-label, "則評分")]').text if driver.find_elements(By.XPATH, '//li[contains(@aria-label, "則評分")]') else ''
        cat = driver.find_element(By.CSS_SELECTOR, 'li.category a').text if driver.find_elements(By.CSS_SELECTOR, 'li.category a') else ''
        # 修正：先取得元素列表，再取第一個的 .text
        els_desc = driver.find_elements(By.CSS_SELECTOR, 'p[data-testid="truncate-text"]')
        desc = els_desc[0].text if els_desc else ''
        comments = []
        for _ in range(10):
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)
        for li in driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="grid-item"]'):
            txt = li.text.strip()
            if txt:
                comments.append(txt)
        pid_match = re.search(r"id(\d+)", url)
        pid = pid_match.group(1) if pid_match else str(idx)
        out_path = f"{out_dir}/podcast_{pid}.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({
                "title": title,
                "provider": prov,
                "rating": rating,
                "category": cat,
                "description": desc,
                "comments": comments,
                "url": url,
                "id": pid
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Metadata error {url}: {e}")
    finally:
        driver.quit()


def process_rss(item: Dict[str, str], idx: int, total: int, out_dir: str) -> None:
    rss = item.get('feed_url')
    if not rss:
        print(f"[{idx}/{total}] 無 RSS URL，跳過")
        return
    feed = feedparser.parse(rss)
    if not feed.entries:
        print(f"[{idx}/{total}] RSS 無內容，跳過")
        return
    pid_match = re.search(r"id(\d+)", item.get('apple_url', ''))
    pid = pid_match.group(1) if pid_match else str(idx)
    out_path = f"{out_dir}/RSS_{pid}.json"
    episodes = []
    for e in feed.entries:
        episodes.append({
            "id": e.get('id') or safe_filename(e.get('title', '')),
            "title": e.get('title', ''),
            "published": e.get('published', ''),
            "description": e.get('summary', ''),
            "audio_url": e.enclosures[0].href if e.enclosures else None
        })
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)
    print(f"[{idx}/{total}] 已輸出 RSS_{pid}.json")


def main() -> None:
    print("開始擷取 Apple 節目 URL...")
    extract_apple_urls("https://podcasts.apple.com/tw/charts?genre=1304")

    print("開始分割 URL 清單...")
    urls = json.load(open('apple_urls.json', 'r', encoding='utf-8'))
    part = urls[:100]
    with open('apple_urls_part_0_100.json', 'w', encoding='utf-8') as f:
        json.dump(part, f, ensure_ascii=False, indent=2)

    print("開始擷取 RSS URL...")
    rss_list = []
    for idx, u in enumerate(part, start=1):
        rss_url = extract_feed_url(u['apple_url'])
        rss_list.append({**u, 'feed_url': rss_url})
        print(f"[{idx}/{len(part)}] 抓取 RSS URL: {rss_url}")
        time.sleep(1)
    with open('podcast_with_rss.json', 'w', encoding='utf-8') as f:
        json.dump(rss_list, f, ensure_ascii=False, indent=2)

    meta_dir = "/data/data_outputs_1304"
    print(f"開始 Metadata scraping，輸出到 {meta_dir}...")
    os.makedirs(meta_dir, exist_ok=True)
    for idx, item in enumerate(rss_list, start=1):
        pid_match = re.search(r"id(\d+)", item.get('apple_url', ''))
        pid = pid_match.group(1) if pid_match else str(idx)
        meta_file = f"{meta_dir}/podcast_{pid}.json"
        if os.path.exists(meta_file):
            print(f"[{idx}/{len(rss_list)}] 已存在 Metadata 檔 podcast_{pid}.json，跳過")
        else:
            process_metadata(item, idx, len(rss_list), meta_dir)

    rss_dir = "/data/rss_outputs_1304"
    print(f"開始 RSS scraping，輸出到 {rss_dir}...")
    os.makedirs(rss_dir, exist_ok=True)
    for idx, item in enumerate(rss_list, start=1):
        pid_match = re.search(r"id(\d+)", item.get('apple_url', ''))
        pid = pid_match.group(1) if pid_match else str(idx)
        rss_file = f"{rss_dir}/RSS_{pid}.json"
        if os.path.exists(rss_file):
            print(f"[{idx}/{len(rss_list)}] 已存在 RSS 檔 RSS_{pid}.json，跳過")
        else:
            process_rss(item, idx, len(rss_list), rss_dir)

    print("✅ 全部處理完成！")


if __name__ == '__main__':
    main()
