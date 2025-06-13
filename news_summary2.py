import requests
import os
import yaml
from datetime import datetime, timedelta

NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY") # 从环境变量中获取

if not NEWSAPI_KEY:
    raise ValueError("NEWSAPI_KEY environment variable not set. Please set it in GitHub Secrets or your local environment.")

# 读取 config.yaml
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 关键词
KEYWORDS = config.get("keywords", [])

# 添加过滤：排除低质量来源（比如 Yahoo Entertainment）
LOW_QUALITY_SOURCES = config.get("low_quality_sources", [])

# 保存目录和文件名
SAVE_DIR = "output"
os.makedirs(SAVE_DIR, exist_ok=True)
HTML_PATH = os.path.join(SAVE_DIR, "news_summary.html")

# NewsAPI 网址和参数模板
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# 获取最近3天新闻（防止没新闻，时间段稍微长点）
to_date = datetime.utcnow()
from_date = to_date - timedelta(days=7)

def fetch_news(query):
    params = {
        "q": query,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,  # 每个关键词最多抓20条新闻
        "apiKey": NEWSAPI_KEY,
    }
    resp = requests.get(NEWSAPI_URL, params=params)
    if resp.status_code != 200:
        print(f"请求失败，状态码: {resp.status_code}，关键词: {query}")
        return []
    data = resp.json()
    return data.get("articles", [])

def build_html_section(title, articles):
    html = f"<h2>{title}</h2>\n<ul>"
    if not articles:
        html += "<li>没有找到相关新闻。</li>"
    else:
        for art in articles:
            if art["source"]["name"] in LOW_QUALITY_SOURCES:
                continue  # 跳过低质量来源
            url = art.get("url", "#")
            headline = art.get("title", "无标题")
            source = art.get("source", {}).get("name", "")
            published_at = art.get("publishedAt", "")[:10]
            html += (
                f'<li><a href="{url}" target="_blank">{headline}</a> '
                f'(<em>{source}</em>, {published_at})</li>\n'
            )
    html += "</ul>"
    return html

def main():
    print("开始抓取新闻...")
    html_body = f"<h1>新闻总结 ({datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')})</h1>\n"

    for kw in KEYWORDS:
        articles = fetch_news(kw)
        section_html = build_html_section(kw, articles)
        html_body += section_html + "\n"

    html_page = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <title>新闻总结</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; }}
        h1 {{ color: #222; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        ul {{ line-height: 1.6; padding-left: 20px; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
        em {{ color: #999; font-size: 0.9em; }}
    </style>
    </head>
    <body>
    {html_body}
    </body>
    </html>
    """

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_page)

    print(f"新闻总结已生成：{HTML_PATH}")

if __name__ == "__main__":
    main()
