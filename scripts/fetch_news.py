#!/usr/bin/env python3
"""
DB그룹 계열사 뉴스 자동 수집 스크립트 (네이버 뉴스 검색 API)

사전 준비:
  1. https://developers.naver.com 에서 애플리케이션 등록
  2. '검색' API 권한 추가
  3. Client ID / Secret 발급
  4. GitHub 저장소 Settings → Secrets 에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 등록

로컬 실행:
  NAVER_CLIENT_ID=xxx NAVER_CLIENT_SECRET=yyy python scripts/fetch_news.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from urllib import request, parse

# ── 설정 ──────────────────────────────────────────────
NAVER_CLIENT_ID     = os.environ.get('NAVER_CLIENT_ID', '')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET', '')
KAKAO_REST_API_KEY  = os.environ.get('KAKAO_REST_API_KEY', '')
KAKAO_REFRESH_TOKEN = os.environ.get('KAKAO_REFRESH_TOKEN', '')
SITE_URL            = 'https://db-group-news.vercel.app'
KST                 = timezone(timedelta(hours=9))
START_DATE          = datetime(2026, 6, 1, tzinfo=KST)
STORAGE_KEY         = 'todo-app-items'

ROOT_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_JSON_PATH  = os.path.join(ROOT_DIR, 'data', 'news.json')
NEWS_DATA_JS    = os.path.join(ROOT_DIR, 'data', 'news-data.js')

SUBSIDIARIES = [
    {"name": "DB손해보험", "query": "DB손해보험"},
    {"name": "DB생명",     "query": "DB생명보험"},
    {"name": "DB증권",     "query": "DB증권"},
    {"name": "DB자산운용", "query": "DB자산운용"},
    {"name": "DB저축은행", "query": "DB저축은행"},
    {"name": "DB캐피탈",   "query": "DB캐피탈"},
    {"name": "DBINC",     "query": "DB Inc OR DBINC"},
    {"name": "DB하이텍",   "query": "DB하이텍"},
]

# ── 네이버 API 호출 ────────────────────────────────────
def fetch_naver_news(query: str, display: int = 50) -> list:
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print(f"  [건너뜀] API 키 없음 — {query}")
        return []

    url = "https://openapi.naver.com/v1/search/news.json?" + parse.urlencode({
        "query":   query,
        "display": display,
        "sort":    "date",
    })
    req = request.Request(url, headers={
        "X-Naver-Client-Id":     NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    })
    try:
        with request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode())["items"]
    except Exception as e:
        print(f"  [오류] {query}: {e}")
        return []

# ── 파싱 유틸 ──────────────────────────────────────────
def parse_pub_date(s: str):
    # "Mon, 19 Jun 2026 09:00:00 +0900"
    try:
        return datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %z")
    except Exception:
        return None

def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    for ent, ch in [("&amp;","&"),("&lt;","<"),("&gt;",">"),("&quot;",'"'),("&#39;","'")]:
        text = text.replace(ent, ch)
    return text.strip()

def make_id(subsidiary: str, url: str) -> str:
    return f"{subsidiary}-{abs(hash(url)) % 0xFFFFFF:06x}"

# ── 카카오톡 알림 ──────────────────────────────────────
def get_kakao_access_token() -> str:
    if not KAKAO_REST_API_KEY or not KAKAO_REFRESH_TOKEN:
        return ''
    data = parse.urlencode({
        'grant_type':    'refresh_token',
        'client_id':     KAKAO_REST_API_KEY,
        'refresh_token': KAKAO_REFRESH_TOKEN,
    }).encode()
    req = request.Request('https://kauth.kakao.com/oauth/token',
                          data=data, method='POST')
    try:
        with request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode()).get('access_token', '')
    except Exception as e:
        print(f"  [카카오] 토큰 갱신 실패: {e}")
        return ''

def send_kakao_message(new_count: int, total_count: int, today: str):
    access_token = get_kakao_access_token()
    if not access_token:
        print("  [카카오] 토큰 없음 — 알림 건너뜀")
        return
    date_fmt = today.replace('-', '.')
    text = (
        f"📰 지현님께서 만드신 [DB그룹 뉴스수집 웹페이지]에 금일 기사 업데이트 완료!\n\n"
        f"📅 오늘은 {date_fmt} 입니다.\n"
        f"➕ 금일 추가건수 : {new_count}건.\n"
        f"📊 현재까지 총 {total_count}건의 기사가 있어요.\n\n"
        f"🔗 {SITE_URL}"
    )
    template = json.dumps({
        "object_type": "text",
        "text": text,
        "link": {"web_url": SITE_URL, "mobile_web_url": SITE_URL},
    })
    data = parse.urlencode({"template_object": template}).encode()
    req = request.Request(
        'https://kapi.kakao.com/v2/api/talk/memo/default/send',
        data=data,
        headers={"Authorization": f"Bearer {access_token}"},
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=10) as res:
            print(f"  [카카오] 알림 발송 완료 ({new_count}건 추가, 총 {total_count}건)")
    except Exception as e:
        print(f"  [카카오] 알림 발송 실패: {e}")

# ── 메인 ──────────────────────────────────────────────
def main():
    # 기존 데이터 로드
    existing: dict[str, dict] = {}
    if os.path.exists(NEWS_JSON_PATH):
        with open(NEWS_JSON_PATH, "r", encoding="utf-8") as f:
            for art in json.load(f).get("articles", []):
                existing[art["url"]] = art
    prev_count = len(existing)

    new_articles = []
    for sub in SUBSIDIARIES:
        print(f"  수집 중: {sub['name']} ({sub['query']})")
        items = fetch_naver_news(sub["query"])
        for item in items:
            pub_date = parse_pub_date(item.get("pubDate", ""))
            if pub_date is None or pub_date < START_DATE:
                continue
            url = item.get("link", "")
            if not url or url in existing:
                continue

            # 언론사 도메인 추출
            try:
                source_domain = item.get("originallink", url).split("/")[2]
            except Exception:
                source_domain = ""

            new_articles.append({
                "id":          make_id(sub["name"], url),
                "title":       clean(item.get("title", "")),
                "description": clean(item.get("description", "")),
                "url":         url,
                "source":      source_domain,
                "subsidiary":  sub["name"],
                "publishedAt": pub_date.isoformat(),
            })

    all_articles = list(existing.values()) + new_articles
    all_articles.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)

    today = datetime.now(KST).strftime("%Y-%m-%d")
    payload = {"lastUpdated": today, "articles": all_articles}

    # news.json 저장
    with open(NEWS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # news-data.js 생성 (브라우저용 전역 변수)
    with open(NEWS_DATA_JS, "w", encoding="utf-8") as f:
        f.write(f"// 자동 생성 파일 — {today}\nconst NEWS_DATA = ")
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    print(f"\n완료: 기존 {prev_count}건 + 신규 {len(new_articles)}건 = 총 {len(all_articles)}건")
    print(f"저장: {NEWS_JSON_PATH}")
    print(f"저장: {NEWS_DATA_JS}")

    send_kakao_message(len(new_articles), len(all_articles), today)

if __name__ == "__main__":
    main()
