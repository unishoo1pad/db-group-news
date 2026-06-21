#!/usr/bin/env python3
"""카카오 토큰 발급 도우미 — 브라우저 로그인 후 자동으로 토큰을 받아옵니다."""

import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse, request as urllib_request

CLIENT_ID     = os.environ.get('KAKAO_REST_API_KEY', '')
CLIENT_SECRET = os.environ.get('KAKAO_CLIENT_SECRET', '')
REDIRECT_URI  = 'http://localhost:8080'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse.parse_qs(parse.urlparse(self.path).query)
        code = qs.get('code', [None])[0]

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        if not code:
            self.wfile.write('<h2>코드를 받지 못했습니다. 다시 시도해주세요.</h2>'.encode())
            return

        # 토큰 교환
        data = parse.urlencode({
            'grant_type':    'authorization_code',
            'client_id':     CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri':  REDIRECT_URI,
            'code':          code,
        }).encode()

        req = urllib_request.Request('https://kauth.kakao.com/oauth/token', data=data, method='POST')
        try:
            with urllib_request.urlopen(req, timeout=10) as res:
                result = json.loads(res.read().decode())
                access  = result.get('access_token', '')
                refresh = result.get('refresh_token', '')

            print('\n[SUCCESS] 토큰 발급 성공!')
            print(f'\nKAKAO_REST_API_KEY  : {CLIENT_ID}')
            print(f'KAKAO_REFRESH_TOKEN : {refresh}')

            html = f'''<html><body style="font-family:sans-serif;padding:40px">
            <h2>[완료] 토큰 발급 성공!</h2>
            <p>이 창을 닫고 터미널에서 값을 확인하세요.</p>
            </body></html>'''
            self.wfile.write(html.encode())
        except Exception as e:
            self.wfile.write(f'<h2>오류: {e}</h2>'.encode())
            print(f'오류: {e}')

        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args):
        pass

if __name__ == '__main__':
    # Redirect URI 를 localhost 로 임시 변경 안내
    print('브라우저가 열립니다. 카카오 계정으로 로그인해주세요...\n', flush=True)

    auth_url = (
        f'https://kauth.kakao.com/oauth/authorize'
        f'?client_id={CLIENT_ID}'
        f'&redirect_uri={parse.quote(REDIRECT_URI)}'
        f'&response_type=code'
        f'&scope=talk_message'
    )

    server = HTTPServer(('localhost', 8080), Handler)
    threading.Thread(target=lambda: webbrowser.open(auth_url), daemon=True).start()
    server.serve_forever()
