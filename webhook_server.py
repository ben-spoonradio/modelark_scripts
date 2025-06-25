#!/usr/bin/env python3
"""
🔔 동영상 생성 완료 알림 웹훅 서버
==================================

이 서버는 동영상 생성 작업이 완료되면 자동으로 알림을 받고
완성된 동영상을 자동으로 다운로드합니다.

사용법:
1. 이 서버를 실행: python webhook_server.py
2. config.txt에 콜백 URL 설정: callback_url=http://localhost:8000/webhook
3. 동영상 생성기 실행
4. 작업 완료 시 자동으로 알림받고 다운로드
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time
import os
import requests

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/webhook':
            try:
                # 요청 본문 읽기
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # JSON 파싱
                webhook_data = json.loads(post_data.decode('utf-8'))
                
                print("🔔 웹훅 알림을 받았습니다!")
                print("=" * 50)
                
                # 작업 정보 출력
                task_id = webhook_data.get('id', '')
                status = webhook_data.get('status', '')
                model = webhook_data.get('model', '')
                
                print(f"📋 작업 ID: {task_id}")
                print(f"📊 상태: {status}")
                print(f"🤖 모델: {model}")
                
                if status == "succeeded":
                    print("🎉 동영상 생성이 완료되었습니다!")
                    
                    # 동영상 URL 추출
                    content = webhook_data.get('content', {})
                    video_url = content.get('video_url', '')
                    
                    if video_url:
                        print(f"📹 동영상 URL: {video_url}")
                        
                        # 토큰 사용량 표시
                        usage = webhook_data.get('usage', {})
                        if usage.get('completion_tokens'):
                            print(f"💰 토큰 사용량: {usage['completion_tokens']:,}")
                        
                        # 자동 다운로드
                        print("\n📥 자동 다운로드를 시작합니다...")
                        download_video(video_url, task_id)
                        
                elif status == "failed":
                    print("❌ 동영상 생성에 실패했습니다.")
                    error_info = webhook_data.get('error', {})
                    if error_info:
                        print(f"🚨 오류 코드: {error_info.get('code', 'Unknown')}")
                        print(f"📝 오류 메시지: {error_info.get('message', '알 수 없는 오류')}")
                
                print("=" * 50)
                print()
                
                # 응답 전송
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "received"}).encode())
                
            except Exception as e:
                print(f"❌ 웹훅 처리 오류: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        if self.path == '/':
            # 간단한 상태 페이지
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>동영상 생성 웹훅 서버</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial; margin: 40px; background: #f5f5f5; }
                    .container { background: white; padding: 30px; border-radius: 10px; }
                    .status { color: #28a745; font-weight: bold; }
                    code { background: #f8f9fa; padding: 4px 8px; border-radius: 4px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔔 동영상 생성 웹훅 서버</h1>
                    <p class="status">✅ 서버가 정상적으로 실행 중입니다!</p>
                    
                    <h2>📋 사용법</h2>
                    <ol>
                        <li><code>config.txt</code>에 다음 줄 추가:<br>
                            <code>callback_url=http://localhost:8000/webhook</code></li>
                        <li>동영상 생성기 실행</li>
                        <li>작업 완료 시 자동으로 알림받고 다운로드</li>
                    </ol>
                    
                    <h2>🔍 웹훅 엔드포인트</h2>
                    <p><code>POST /webhook</code> - 작업 완료 알림 수신</p>
                    
                    <p><small>이 서버를 중단하려면 터미널에서 Ctrl+C를 누르세요.</small></p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # 기본 로그 메시지 숨기기 (깔끔한 출력을 위해)
        pass

def download_video(video_url: str, task_id: str) -> bool:
    """동영상 자동 다운로드"""
    try:
        # 다운로드 폴더 만들기
        if not os.path.exists("videos"):
            os.makedirs("videos")
        
        # 파일명 만들기
        timestamp = int(time.time())
        filename = f"webhook_{task_id}_{timestamp}.mp4"
        filepath = os.path.join("videos", filename)
        
        # 다운로드
        print(f"💾 저장 경로: {filepath}")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total_size += len(chunk)
                if total_size > 1024 * 1024:  # 1MB마다 표시
                    print(".", end="", flush=True)
        
        print(f"\n✅ 다운로드 완료!")
        
        # 파일 크기 표시
        file_size = os.path.getsize(filepath) / (1024 * 1024)
        print(f"📊 파일 크기: {file_size:.1f} MB")
        print(f"📁 저장 위치: {os.path.abspath(filepath)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        return False

def main():
    print("🔔 동영상 생성 웹훅 서버")
    print("=" * 40)
    print()
    
    server_address = ('localhost', 8000)
    
    try:
        httpd = HTTPServer(server_address, WebhookHandler)
        
        print(f"🌐 서버 시작: http://localhost:8000")
        print(f"📞 웹훅 URL: http://localhost:8000/webhook")
        print()
        print("💡 config.txt에 다음 줄을 추가하세요:")
        print("   callback_url=http://localhost:8000/webhook")
        print()
        print("🔄 알림을 기다리는 중... (Ctrl+C로 종료)")
        print()
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 서버를 종료합니다.")
    except Exception as e:
        print(f"❌ 서버 오류: {e}")

if __name__ == "__main__":
    main()