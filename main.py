import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# 設定你的目標網址
TARGET_URL = "https://www.pcsh.ntpc.edu.tw/"

# 你指定的重點關鍵字清單
KEYWORDS = [
    "交換", "姊妹校", "研習", "跨國", "遊學", 
    "段考", "實習", "交流", "留學", "參訪", "高一"
]

def scrape_website():
    print(f"正在抓取網頁: {TARGET_URL}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(TARGET_URL, headers=headers)
    response.encoding = 'utf-8'
    
    soup = BeautifulSoup(response.text, 'html.parser')
    text_content = soup.get_text(separator="\n", strip=True)
    return text_content

def check_keywords(content):
    found_keywords = [kw for kw in KEYWORDS if kw in content]
    return found_keywords

def send_to_discord(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ 找不到 DISCORD_WEBHOOK_URL，跳過發送 Discord 通知。")
        return
    
    # Discord 訊息若太長需做簡單切割或取前 2000 字
    payload = {"content": message[:2000]}
    response = requests.post(webhook_url, json=payload)
    if response.status_code == 204:
        print("✅ Discord 通知發送成功！")
    else:
        print(f"❌ Discord 通知發送失敗，錯誤碼: {response.status_code}")

def ask_gemini(content, found_keywords):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("找不到 GEMINI_API_KEY，請確認 GitHub Secrets 是否設定正確。")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = f"""
    以下是從學校網站抓取到的最新內容：
    {content[:8000]}

    【重要指令】
    我們特別關注以下關鍵字：{KEYWORDS}
    經過程式初步比對，本次網頁中出現了以下符合的關鍵字：{found_keywords if found_keywords else "無"}

    請根據上述內容幫我整理：
    1. 如果有出現上述關鍵字, 請在最上方用顯眼的格式「🔴 重點標註」特別摘要該活動、考試或公告的詳細時間與內容。
    2. 提供整體網頁內容的簡要重點摘要。
    """
    
    response = model.generate_content(prompt)
    ai_result = response.text
    
    print("=== AI 分析與關鍵字提醒結果 ===")
    print(ai_result)
    
    # 將 AI 的結果包裝後發送到 Discord
    discord_message = f"🔔 **每日學校公告 AI 摘要報告**\n{ai_result}"
    send_to_discord(discord_message)

if __name__ == "__main__":
    data = scrape_website()
    matched = check_keywords(data)
    
    if matched:
        print(f"🎯 成功捕捉到關鍵字：{matched}")
    else:
        print("ℹ️ 本次未直接命中指定關鍵字，但仍進行一般摘要。")
    
    ask_gemini(data, matched)
