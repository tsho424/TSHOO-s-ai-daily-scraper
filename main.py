import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 1. 設定要爬取的目標網址 (請替換成你想抓的網頁)
TARGET_URL = "https://news.ycombinator.com/"

def scrape_website():
    print(f"正在抓取網頁: {TARGET_URL}")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(TARGET_URL, headers=headers)
    
    if response.status_code != 200:
        print("抓取網頁失敗！")
        return None

    # 解析網頁文字
    soup = BeautifulSoup(response.text, 'html.parser')
    # 這裡抓取該網頁所有的文字內容 (你也可以根據需求調整)
    text_content = soup.get_text()[:5000] # 限制字頭前 5000 字避免過長
    return text_content

def ask_gemini(content):
    # 從 GitHub 秘密設定中讀取 API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("找不到 GEMINI_API_KEY 密鑰！")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')

    prompt = f"請幫我閱讀以下網頁內容，並整理出 3 個最重要的重點摘要：\n\n{content}"
    
    response = model.generate_content(prompt)
    print("\n--- AI 分析結果 ---")
    print(response.text)

if __name__ == "__main__":
    data = scrape_website()
    if data:
        ask_gemini(data)
