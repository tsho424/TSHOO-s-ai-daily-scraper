import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from urllib.parse import urljoin

# 設定你的目標網址
TARGET_URL = "https://www.pcsh.ntpc.edu.tw/"

# 關鍵字清單（已加入「學生研習」）
KEYWORDS = [
    "交換", "姊妹校", "研習", "跨國", "遊學", 
    "段考", "實習", "交流", "留學", "參訪", "高一", "學生研習"
]

def scrape_website():
    print(f"正在抓取網頁: {TARGET_URL}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(TARGET_URL, headers=headers)
    response.encoding = 'utf-8'
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    items = []
    for a_tag in soup.find_all('a', href=True):
        title = a_tag.get_text(strip=True)
        href = a_tag['href']
        if title and len(title) > 2:
            full_url = urljoin(TARGET_URL, href)
            items.append({"title": title, "url": full_url})
            
    text_content = soup.get_text(separator="\n", strip=True)
    return text_content, items

def check_keywords_in_items(items):
    matched_items = []
    for item in items:
        title = item["title"]
        
        # 🔴 絕對排除包含「教師研習」的項目
        if "教師研習" in title:
            continue
            
        # 檢查是否包含指定的關鍵字
        if any(kw in title for kw in KEYWORDS):
            matched_items.append(item)
            
    return matched_items

def send_to_discord(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ 找不到 DISCORD_WEBHOOK_URL，跳過發送 Discord 通知。")
        return
    
    payload = {"content": message[:2000]}
    response = requests.post(webhook_url, json=payload)
    if response.status_code == 204:
        print("✅ Discord 通知發送成功！")
    else:
        print(f"❌ Discord 通知發送失敗，錯誤碼: {response.status_code}")

def ask_gemini(content, matched_items):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("找不到 GEMINI_API_KEY，請確認 GitHub Secrets 是否設定正確。")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    matched_str = "\n".join([f"- [{item['title']}]({item['url']})" for item in matched_items]) if matched_items else "無直接匹配的公告連結"
    
    prompt = f"""
    以下是從學校網站抓取到的最新網頁內容摘要：
    {content[:6000]}

    【程式初步篩選出的關鍵字符合項目與連結（已排除教師研習）】
    {matched_str}

    【重要指令】
    我們特別關注以下關鍵字：{KEYWORDS}
    請注意：公告標題若含有「教師研習」請務必排除，僅保留學生相關或符合上述清單的項目。
    請根據上述內容幫我整理：
    1. 如果有上述的「匹配項目與連結」，請在最上方用顯眼的格式「🔴 重點標註與連結」把這些項目的標題與對應網址列出來，方便使用者直接點擊。
    2. 提供整體網頁內容的簡要重點摘要。
    """
    
    response = model.generate_content(prompt)
    ai_result = response.text
    
    print("=== AI 分析與連結結果 ===")
    print(ai_result)
    
    discord_message = f"🔔 **每日學校公告 AI 摘要報告**\n{ai_result}"
    send_to_discord(discord_message)

if __name__ == "__main__":
    data, items = scrape_website()
    matched_items = check_keywords_in_items(items)
    
    if matched_items:
        print(f"🎯 成功捕捉到 {len(matched_items)} 個符合關鍵字的項目！")
    else:
        print("ℹ️ 本次未直接命中指定關鍵字項目，但仍進行一般摘要。")
    
    ask_gemini(data, matched_items)
