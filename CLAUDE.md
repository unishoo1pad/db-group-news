# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

DB그룹 8개 계열사(DB손해보험, DB생명, DB증권, DB자산운용, DB저축은행, DB캐피탈, DBINC, DB하이텍)의 뉴스를 네이버 뉴스 검색 API로 자동 수집해 정적 웹페이지로 표시하는 프로젝트. Vercel에 배포되며 GitHub Actions로 매일 13:30 KST 자동 실행.

## 데이터 흐름

```
fetch_news.py
  → 네이버 API 호출 (계열사별 쿼리)
  → 관련성 필터 (계열사명 포함 여부)
  → 스포츠 뉴스 필터 (SPORTS_KEYWORDS)
  → data/news.json 저장
  → data/news-data.js 생성 (브라우저용 전역변수 NEWS_DATA)
  → 카카오톡 알림 발송 (KAKAO_REFRESH_TOKEN으로 access_token 갱신)

index.html + app.js
  → <script src="data/news-data.js"> 로 NEWS_DATA 로드
  → 계열사별 탭 필터 + 검색 + 날짜별 그룹 렌더링
```

백엔드 없음 — news-data.js가 정적 파일로 데이터를 브라우저에 직접 전달.

## 스크립트 실행

```bash
# 뉴스 수집 (로컬 테스트)
NAVER_CLIENT_ID=xxx NAVER_CLIENT_SECRET=yyy python scripts/fetch_news.py

# 기존 news.json에서 스포츠/관련성 재필터링 (API 호출 없음)
python scripts/clean_news.py

# 카카오 Refresh Token 최초 발급 (브라우저 로그인 필요)
python scripts/get_kakao_token.py
```

## GitHub Secrets

| 키 | 용도 |
|---|---|
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` | 네이버 검색 API |
| `KAKAO_REST_API_KEY` | 카카오 앱 Client ID |
| `KAKAO_CLIENT_SECRET` | 카카오 앱 Client Secret |
| `KAKAO_REFRESH_TOKEN` | 카카오톡 알림 발송용 (만료 시 get_kakao_token.py로 재발급) |

## 주요 상수 (fetch_news.py)

- `START_DATE`: 수집 시작일 — 이 날짜 이전 기사는 무시
- `SPORTS_KEYWORDS`: 필터링할 스포츠 관련 키워드 목록
- `SUBSIDIARIES`: 계열사명 → 네이버 검색 쿼리 매핑

## 배포

- Vercel 자동 배포: main 브랜치 push 시 트리거
- 커스텀 도메인: `dbnews.unishoo1.xyz`
- 기본 도메인: `db-group-news.vercel.app`
