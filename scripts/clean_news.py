import json, os

SPORTS_KEYWORDS = [
    "스포츠", "야구", "축구", "농구", "배구", "골프", "테니스", "수영", "육상",
    "올림픽", "월드컵", "kbo", "mlb", "nba", "k리그", "epl", "v리그", "kbl",
    "프로야구", "프로축구", "프로농구", "선수권", "경기장", "감독", "코치",
    "홈런", "득점", "우승", "준우승", "챔피언", "리그", "토너먼트", "매치",
]

def is_sports(title: str, desc: str) -> bool:
    combined = (title + " " + desc).lower()
    return any(kw in combined for kw in SPORTS_KEYWORDS)

SUBSIDIARIES = {
    'DB손해보험': 'db손해보험',
    'DB생명':     'db생명',
    'DB증권':     'db증권',
    'DB자산운용': 'db자산운용',
    'DB저축은행': 'db저축은행',
    'DB캐피탈':   'db캐피탈',
    'DBINC':     'db inc',
    'DB하이텍':   'db하이텍',
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, 'data', 'news.json')
JS_PATH   = os.path.join(ROOT, 'data', 'news-data.js')

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

before = len(data['articles'])
filtered = []
for a in data['articles']:
    keyword = SUBSIDIARIES.get(a['subsidiary'], a['subsidiary'].lower())
    title = a.get('title', '').lower()
    desc  = a.get('description', '').lower()
    if keyword in title or keyword in desc:
        if not is_sports(title, desc):
            filtered.append(a)

data['articles'] = filtered
after = len(filtered)

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

today = data['lastUpdated']
with open(JS_PATH, 'w', encoding='utf-8') as f:
    f.write('// ' + today + '\nconst NEWS_DATA = ')
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write(';\n')

print(f'정리 완료: {before}건 → {after}건 ({before - after}건 제거)')
