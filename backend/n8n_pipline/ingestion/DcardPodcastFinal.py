# 操作 browser 的 API
import os
import re

# 強制等待
from time import sleep
from typing import List

# 其他套件
import requests as req

# 使用 undetected_chromedriver（避免被反爬蟲偵測）
import undetected_chromedriver as uc
from bs4 import BeautifulSoup as bs
from selenium import webdriver

# 例外處理
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

"""
設定 Chrome 選項
"""
options = uc.ChromeOptions()
# 建議除錯時先關閉 headless 模式
# options.add_argument('--headless')
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
url_relationship = "https://www.dcard.tw/f/podcast"

"""
啟動瀏覽器
"""
driver = uc.Chrome(options=options, version_main=136)
driver.get(url_relationship)
sleep(3)

sleep(2)


def scroll_until_bottom(
    driver: webdriver.Chrome, max_scroll: int = 30, wait_time: float = 3.0
) -> List[str]:
    url_list: List[str] = []

    for i in range(max_scroll):
        print(f"🔽 滾動次數: {i + 1}")

        # 慢慢滾動
        # driver.execute_script(f"window.scrollBy(0, 1000);")
        # sleep(wait_time)

        # 抓取文章連結
        post_elements = driver.find_elements(
            By.CSS_SELECTOR, 'a[href^="/f/podcast/p/"]'
        )
        for post in post_elements:
            href = post.get_attribute("href")
            if href and href not in url_list:
                url_list.append(href)
        print(f"目前抓到文章數: {len(url_list)}")

        # 滾到底(x, y)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(wait_time)

        # 判斷是否到底
        is_bottom = driver.execute_script(
            "return (window.pageYOffset + window.innerHeight) >= document.body.scrollHeight;"
        )
        if is_bottom:
            print("✅ 已到底部，停止滾動")
            break

    return url_list


# ✅ 呼叫函式並接收資料
url_list = scroll_until_bottom(driver, max_scroll=30, wait_time=3)

# 🔍 顯示所有收集到的網址
for url in url_list:
    print(url)

# 關閉瀏覽器
driver.quit()

from time import sleep
from typing import List

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

# max_scroll=30	最多滾動 30 次，防止陷入無限滾動


def scroll_until_bottom_comment_text(
    driver: webdriver.Chrome, max_scroll: int = 999, wait_time: float = 3.0
) -> List[str]:
    comment_texts: List[str] = []

    for i in range(max_scroll):
        print(f"🔽 滾動次數: {i + 1}")
        action = ActionChains(driver)

        # 重新取得所有按鈕，避免 stale element
        toggle_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            'section div[data-key^="subCommentToggle-"] button, section div[data-key^="subCommentLoader"] button',
        )

        for btn in toggle_buttons:
            try:
                text = btn.text.strip()
            except Exception:
                # 如果元素失效，跳過
                continue

            if text.startswith("查看其他"):
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", btn
                    )
                    sleep(0.2)
                    action.move_to_element(btn).perform()
                    btn.click()
                    print(f"🔘 點擊按鈕：{text}")
                    sleep(0.2)
                except (
                    ElementClickInterceptedException,
                    ElementNotInteractableException,
                ):
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"⚠️ 改用 JS 點擊按鈕：{text}")
                        sleep(0.2)
                    except Exception as e:
                        print(f"❌ 無法點擊按鈕：{e}")

        try:
            comment_divs = driver.find_elements(
                By.CSS_SELECTOR, 'section div[data-key^="comment-"]'
            )
            for div in comment_divs:
                try:
                    spans = div.find_elements(By.TAG_NAME, "span")
                    for span in spans:
                        text = span.text.strip()
                        if text and text not in comment_texts:
                            comment_texts.append(text)
                except StaleElementReferenceException:
                    continue
        except StaleElementReferenceException:
            pass

        # 滾動到最底部
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollBy(0, 500);")
        sleep(wait_time)

        # 判斷是否到底
        is_bottom = driver.execute_script(
            "return (window.pageYOffset + window.innerHeight) >= document.body.scrollHeight;"
        )
        if is_bottom:
            print("✅ 已到底部，停止滾動")
            break

    return comment_texts


folder_path = "dcard_test_all"
os.makedirs(folder_path, exist_ok=True)

# driver = webdriver.Chrome()


# 🔄 依序處理每篇文章
for url in url_list:
    try:
        options = uc.ChromeOptions()
        # 建議除錯時先關閉 headless 模式
        # options.add_argument('--headless')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(options=options, version_main=136)
        driver.get(url)
        sleep(3)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        sleep(1)

        # 抓取標題
        element = driver.find_element(By.CSS_SELECTOR, "h1")
        title = element.text.strip()
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        post_id = url.split("/")[-1]
        file_path = os.path.join(folder_path, f"{safe_title}_{post_id}.json")

        # 抓取內容
        spans = driver.find_elements(By.CSS_SELECTOR, "article span")
        paragraphs = [span.text.strip() for span in spans if span.text.strip()]

        comments = scroll_until_bottom_comment_text(driver)
        print("\n全部留言：")
        for i, text in enumerate(comments, 1):
            print(f"{i}. {text}")

        # 寫入檔案
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n\n")  # 空兩行分隔
            # 寫入 comments
            file.write("\n".join(paragraphs))
            file.write("\n".join(comments))

        print(f"✅ 儲存成功：{file_path}")

        url_list2 = scroll_until_bottom_comment_text(driver, max_scroll=30, wait_time=3)

        # 關閉瀏覽器
        driver.quit()
    except Exception as e:
        print(f"❌ 發生錯誤：{url}")
        print("錯誤原因：", e)
