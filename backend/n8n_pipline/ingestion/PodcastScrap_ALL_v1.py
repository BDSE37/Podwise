import json
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from time import sleep
from typing import Dict, List

import feedparser
import requests
import requests as req
import undetected_chromedriver as uc
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def extract_apple_urls(
    podcast_url: str,
    tab_text: str = "熱門節目",
    max_attempts: int = 10,
    output_file: str = "apple_urls.json",
) -> None:
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options, version_main=136)
    driver.get(podcast_url)

    try:
        wait = WebDriverWait(driver, 15)
        tab = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//span[text()="{tab_text}"]'))
        )
        tab.click()
        print(f"✅ 點擊標籤：{tab_text}")
        time.sleep(3)

        body = driver.find_element(By.TAG_NAME, "body")
        prev_count = 0
        stable_attempts = 0

        while stable_attempts < max_attempts:
            for _ in range(5):
                body.send_keys(Keys.END)
                time.sleep(0.5)

            elements = driver.find_elements(
                By.XPATH, '//a[@data-testid="product-lockup-link"]'
            )
            curr_count = len(elements)
            print(f"🎯 已擷取節目數：{curr_count}")

            if curr_count == prev_count:
                stable_attempts += 1
                print(f"⚠️ 無新增內容，第 {stable_attempts}/{max_attempts} 次確認")
            else:
                stable_attempts = 0
                prev_count = curr_count

        seen_links = set()
        result: List[Dict[str, str]] = []

        for el in elements:
            href = el.get_attribute("href")
            if href and href not in seen_links:
                seen_links.add(href)
                print(f"🔗 Apple URL: {href}")
                result.append({"apple_url": href})

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ 已儲存至 {output_file}")

    finally:
        driver.quit()


def split_apple_urls(input_file: str, start_idx: int, end_idx: int) -> None:
    with open(input_file, "r", encoding="utf-8") as f:
        data: List[Dict[str, str]] = json.load(f)

    selected = data[start_idx:end_idx]
    out_file = f"{os.path.splitext(input_file)[0]}_part_{start_idx}_{end_idx}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    print(f"✅ 已輸出第 {start_idx} 到 {end_idx} 筆資料 -> {out_file}")


if __name__ == "__main__":
    podcast_url = "https://podcasts.apple.com/tw/charts?genre=1304"
    extract_apple_urls(podcast_url)

    # 🔍 從 URL 自動擷取 genre_id
    genre_match = re.search(r"genre=(\d+)", podcast_url)
    genre_id = genre_match.group(1) if genre_match else "unknown"
    print(f"🎯 擷取到 genre_id: {genre_id}")

    # ✅ 可自定控制分割範圍
    part_start = 0
    part_end = 100

    # 分割 JSON
    split_apple_urls("apple_urls.json", start_idx=part_start, end_idx=part_end)

    # 結果檔案命名
    part_file = f"apple_urls_part_{part_start}_{part_end}.json"
    print(f"📄 你可以接著處理這個檔案：{part_file}")

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional


class PodcastRSSExtractor:
    def __init__(
        self,
        input_file: str,
        output_file: str,
        threads: int = 5,
        delay: float = 1.5,
    ) -> None:
        self.input_file: str = input_file
        self.output_file: str = output_file
        self.threads: int = threads
        self.delay: float = delay

    def is_valid_rss(self, url: str) -> bool:
        """用 feedparser 驗證該 URL 是否為可用 RSS feed"""
        try:
            feed = feedparser.parse(url)
            return bool(feed.entries)
        except Exception:
            return False

    def extract_feed_url(self, apple_url: str) -> Optional[str]:
        """從 Apple Podcast 頁面內嵌 JSON 中擷取 feedUrl"""
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            res = requests.get(apple_url, headers=headers, timeout=10)
            match = re.search(r'"feedUrl"\s*:\s*"([^"]+)"', res.text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    def process_item(
        self, item: Dict[str, str], index: int, total: int
    ) -> Dict[str, Optional[str]]:
        apple_url: str = item.get("apple_url", "")
        print(f"[{index}/{total}] 🔍 抓取 RSS for {apple_url}")
        rss_url: Optional[str] = self.extract_feed_url(apple_url)
        time.sleep(self.delay)
        return {"apple_url": apple_url, "feed_url": rss_url}

    def enrich(self) -> None:
        with open(self.input_file, "r", encoding="utf-8") as f:
            podcast_list: List[Dict[str, str]] = json.load(f)

        total: int = len(podcast_list)
        enriched_list: List[Dict[str, Optional[str]]] = []

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_index = {
                executor.submit(self.process_item, item, idx + 1, total): idx
                for idx, item in enumerate(podcast_list)
            }
            for future in as_completed(future_to_index):
                result = future.result()
                enriched_list.append(result)

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_list, f, ensure_ascii=False, indent=2)
        print(f"✅ 已寫入結果至 {self.output_file}")


if __name__ == "__main__":
    # 手動指定要使用哪個區段

    input_file = f"apple_urls_part_{part_start}_{part_end}.json"
    output_file = f"podcast_with_rss.json"

    extractor = PodcastRSSExtractor(
        input_file=input_file,
        output_file=output_file,
        threads=10,
        delay=1.5,
    )
    extractor.enrich()

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

# 配置
INPUT_FILE = "podcast_with_rss.json"
OUTPUT_DIR = f"rss_outputs_{genre_id}"  # 單一輸出資料夾
NUM_THREADS = 10  # 同時處理執行緒數

# 確保資料夾存在
os.makedirs(OUTPUT_DIR, exist_ok=True)


def safe_filename(text: str) -> str:
    """清理檔名：移除特殊符號並限制長度"""
    return re.sub(r"[^0-9A-Za-z_\- ]", "_", text)[:80].strip()


def process_podcast(podcast: Dict[str, str], index: int, total: int) -> Optional[str]:
    """解析單一 RSS 並將結果寫入單一資料夾，回傳檔案路徑"""
    feed_url = podcast.get("feed_url")
    apple_url = podcast.get("apple_url", "")
    if not feed_url:
        print(f"❌ [第{index}/{total}] 沒有 feed_url，跳過")
        return None

    # 解析 podcast_id
    match = re.search(r"id(\d+)", apple_url)
    podcast_id = match.group(1) if match else str(index)
    print(f"🔍 [{index}/{total}] 處理 RSS: {feed_url}")

    feed = feedparser.parse(feed_url)
    if not feed.entries:
        print(f"⚠️ [第{index}] RSS 無內容，跳過")
        return None

    # 擷取集數資料
    episodes = []
    for entry in feed.entries:
        audio_url = entry.enclosures[0].href if entry.enclosures else None
        title = entry.get("title", "")
        episodes.append(
            {
                "id": entry.get("id") or safe_filename(title),
                "title": title,
                "published": entry.get("published", ""),
                "description": entry.get("summary", ""),
                "audio_url": audio_url,
            }
        )

    # 寫入同一資料夾
    filename = f"RSS_{podcast_id}.json"
    output_path = os.path.join(OUTPUT_DIR, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)

    print(f"✅ [{index}/{total}] 已寫入: {output_path} ({len(episodes)} 集)")
    return output_path


def main():
    # 讀取 RSS 列表
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        podcast_list: List[Dict[str, str]] = json.load(f)
    total = len(podcast_list)

    results = []
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = {
            executor.submit(process_podcast, podcast, idx + 1, total): idx
            for idx, podcast in enumerate(podcast_list)
        }
        for future in as_completed(futures):
            path = future.result()
            if path:
                results.append(path)

    print(f"\n所有任務完成，共寫入 {len(results)} 個檔案到 `{OUTPUT_DIR}`。")


if __name__ == "__main__":
    main()


# genre_id="1321"


# 並行執行緒數量
NUM_THREADS = 4
# 輸入/輸出設定
INPUT_FILE = f"apple_urls_part_{part_start}_{part_end}.json"
OUTPUT_DIR = f"data_outputs_{genre_id}"  # 最終資料夾  # 最終資料夾
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 定義留言擷取函式


def Comment(driver):
    """
    嘗試點擊『評分與評論』按鈕，若失敗則直接從當前頁面 ul 擷取留言。
    回傳 (comments, is_comment_tab)
    """
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "html"))
        )
    except TimeoutException:
        return [], False

    # 簡單滾動
    actions = ActionChains(driver)
    for _ in range(30):
        actions.send_keys(Keys.ARROW_DOWN).perform()
        time.sleep(0.05)

    # 找按鈕
    buttons = driver.find_elements(
        By.CSS_SELECTOR, "button.title__button.svelte-rnrb59"
    )
    target = None
    for btn in buttons:
        if btn.text.strip() == "評分與評論":
            target = btn
            break

    is_tab = False
    if target:
        try:
            driver.execute_script("arguments[0].scrollIntoView();", target)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", target)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'ul[data-testid="shelf-item-list"]')
                )
            )
            is_tab = True
        except Exception:
            pass

    # 抓留言
    comments = []
    try:
        shelf = driver.find_elements(By.CSS_SELECTOR, "div.shelf-content")
        if shelf:
            ul = shelf[0].find_element(
                By.CSS_SELECTOR, 'ul[data-testid="shelf-item-list"]'
            )
            items = ul.find_elements(By.TAG_NAME, "li")
            comments = [li.text.strip() for li in items if li.text.strip()]
    except Exception:
        pass

    return comments, is_tab


def scroll_until_fully_loaded(driver, max_attempts: int = 10) -> List[str]:
    try:
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), "評分與評論")
        )
    except TimeoutException:
        return []

    try:
        scroll_area = driver.find_element(By.ID, "scrollable-page")
    except Exception:
        return []

    prev = 0
    stable = 0
    while stable < max_attempts:
        for _ in range(20):
            scroll_area.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.1)
        curr = len(driver.find_elements(By.XPATH, '//div[contains(@class, "review")]'))
        if curr == prev:
            stable += 1
        else:
            prev = curr
            stable = 0
    elements = driver.find_elements(By.CSS_SELECTOR, 'li[data-testid="grid-item"]')
    return [el.text.strip() for el in elements if el.text.strip()]


def worker(q: Queue):
    while True:
        try:
            item = q.get(timeout=3)
        except:
            break
        try:
            crawl_task(item)
        except Exception as e:
            print(f"❌ 執行任務失敗: {e}")
        q.task_done()


chrome_lock = threading.Lock()


def crawl_task(item: Dict[str, str]) -> None:
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    url = item.get("apple_url")
    driver = None

    try:
        pid = url.split("id")[-1]
        safe = re.sub(r'[\\/:*?"<>|]', "_", pid)
        path = os.path.join(OUTPUT_DIR, f"podcast_{safe}.json")
        with chrome_lock:
            driver = uc.Chrome(options=options, version_main=137)
        wait = WebDriverWait(driver, 10)
        time.sleep(1)
        driver.get(url)
        time.sleep(8)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
        title = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span[dir="auto"]'))
        ).text

        provider = (
            driver.find_element(By.CSS_SELECTOR, "span.provider").text
            if driver.find_elements(By.CSS_SELECTOR, "span.provider")
            else "無"
        )
        rating_el = driver.find_elements(
            By.XPATH, '//li[contains(@aria-label, "則評分")]'
        )
        rating = rating_el[0].text if rating_el else "無"

        category = (
            driver.find_element(
                By.CSS_SELECTOR,
                'li.category.svelte-123qhuj > a.link-action[data-testid="click-action"]',
            ).text
            if driver.find_elements(
                By.CSS_SELECTOR,
                'li.category.svelte-123qhuj > a.link-action[data-testid="click-action"]',
            )
            else "無"
        )

        update_freq = driver.find_elements(By.CSS_SELECTOR, "li.svelte-123qhuj")[
            -1
        ].text
        description = driver.find_element(
            By.CSS_SELECTOR, 'p[data-testid="truncate-text"]'
        ).text
        time.sleep(2)
        comments, is_tab = Comment(driver)
        time.sleep(2)
        if is_tab:
            comments = scroll_until_fully_loaded(driver)

        podcast_data = {
            "title": title,
            "provider": provider,
            "rating": rating,
            "category": category,
            "update_frequency": update_freq,
            "description": description,
            "comments": comments,
            "url": url,
            "id": pid,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(podcast_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已輸出: {path}")

    except Exception as e:
        print(f"❌ 發生錯誤（{url}）: {e}")
        return  # 🔥 防止 thread 卡住

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    from undetected_chromedriver import Chrome, ChromeOptions

    Chrome(version_main=137).quit()
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        podcast_urls = json.load(f)

    task_queue = Queue()
    for item in podcast_urls:
        pid = item.get("apple_url", "").split("id")[-1]
        if not pid:
            continue
        safe = re.sub(r'[\\/:*?"<>|]', "_", pid)
        path = os.path.join(OUTPUT_DIR, f"podcast_{safe}.json")
        if os.path.exists(path):
            print(f"🔍 已存在檔案，略過: {path}")
            continue
        task_queue.put(item)

    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(task_queue,))
        t.start()
        threads.append(t)

    task_queue.join()

    for t in threads:
        t.join()

    print("✅ 全部Podcast處理完成！")
