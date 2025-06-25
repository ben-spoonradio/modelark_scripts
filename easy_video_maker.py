#!/usr/bin/env python3
"""
🎥 쉬운 동영상 생성기 (Easy Video Maker)
===========================================

이 프로그램은 이미지와 텍스트 설명을 이용해 자동으로 동영상을 만들어줍니다.

사용 방법:
1. prompt.txt 파일에 원하는 동영상 설명을 작성하세요
2. config.txt 파일에 이미지 주소를 입력하세요
3. 이 프로그램을 실행하세요

필요한 파일들:
- prompt.txt: 동영상에 대한 설명 (한글 가능)
- config.txt: 이미지 주소와 설정들
- 환경변수: ARK_API_KEY (API 키)
"""

import requests
import time
import json
import os
from typing import Optional
import logging

# 로그 설정 (사용자가 볼 필요 없는 기술적 정보는 숨김)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class EasyVideoMaker:
    """쉬운 동영상 생성기"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://ark.ap-southeast.bytepluses.com"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def create_video(self, description: str, image_url: str) -> Optional[str]:
        """동영상을 만들고 파일로 저장합니다"""
        
        print("🎬 동영상 생성을 시작합니다...")
        print(f"📝 설명: {description[:50]}{'...' if len(description) > 50 else ''}")
        print(f"🖼️  이미지: {image_url}")
        print()
        
        # 1단계: 동영상 생성 요청
        task_id = self._start_generation(description, image_url)
        if not task_id:
            return None
        
        # 2단계: 완료까지 기다리기
        video_url = self._wait_for_video(task_id)
        if not video_url:
            return None
        
        # 3단계: 동영상 다운로드
        return self._download_video(video_url)
    
    def _start_generation(self, description: str, image_url: str) -> Optional[str]:
        """동영상 생성 시작"""
        url = f"{self.base_url}/api/v3/contents/generations/tasks"
        
        data = {
            "model": "seedance-1-0-lite-i2v-250428",
            "content": [
                {"type": "text", "text": description},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            task_id = result.get("id")
            if task_id:
                print("✅ 동영상 생성 요청이 접수되었습니다!")
                return task_id
            else:
                print("❌ 오류: 작업 ID를 받지 못했습니다.")
                return None
                
        except Exception as e:
            print(f"❌ 오류: 동영상 생성 요청 실패 - {e}")
            return None
    
    def _wait_for_video(self, task_id: str) -> Optional[str]:
        """동영상 완성까지 기다리기"""
        print("⏳ 동영상을 만들고 있습니다. 잠시만 기다려주세요...")
        print("   (보통 1-3분 정도 걸립니다)")
        
        check_url = f"{self.base_url}/api/v3/contents/generations/tasks/{task_id}"
        
        for i in range(30):  # 최대 5분 대기 (10초씩 30번)
            try:
                response = requests.get(check_url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
                
                status = result.get("status")
                
                if status == "succeeded":
                    video_url = result.get("content", {}).get("video_url")
                    if video_url:
                        print("🎉 동영상이 완성되었습니다!")
                        return video_url
                    else:
                        print("❌ 오류: 동영상 주소를 찾을 수 없습니다.")
                        return None
                
                elif status == "failed":
                    print("❌ 오류: 동영상 생성에 실패했습니다.")
                    return None
                
                else:  # 진행 중
                    dots = "." * ((i % 3) + 1)
                    print(f"\r   작업 중{dots}   ", end="", flush=True)
                    time.sleep(10)
            
            except Exception as e:
                print(f"\n❌ 오류: 상태 확인 실패 - {e}")
                return None
        
        print("\n❌ 오류: 시간이 너무 오래 걸립니다. 나중에 다시 시도해주세요.")
        return None
    
    def _download_video(self, video_url: str) -> Optional[str]:
        """동영상 다운로드"""
        print("\n📥 동영상을 다운로드합니다...")
        
        try:
            # 다운로드 폴더 만들기
            if not os.path.exists("videos"):
                os.makedirs("videos")
            
            # 파일명 만들기
            timestamp = int(time.time())
            filename = f"generated_video_{timestamp}.mp4"
            filepath = os.path.join("videos", filename)
            
            # 다운로드
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total_size += len(chunk)
                    if total_size > 1024 * 1024:  # 1MB마다 표시
                        print(".", end="", flush=True)
            
            print(f"\n✅ 완료! 동영상이 저장되었습니다: {filepath}")
            
            # 파일 크기 표시
            file_size = os.path.getsize(filepath) / (1024 * 1024)
            print(f"📊 파일 크기: {file_size:.1f} MB")
            
            return filepath
            
        except Exception as e:
            print(f"❌ 오류: 다운로드 실패 - {e}")
            return None


def read_prompt_file() -> str:
    """prompt.txt 파일에서 동영상 설명 읽기"""
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return content
            else:
                print("⚠️  경고: prompt.txt 파일이 비어있습니다.")
                return None
    except FileNotFoundError:
        print("❌ 오류: prompt.txt 파일을 찾을 수 없습니다.")
        print("📝 prompt.txt 파일을 만들고 동영상 설명을 작성해주세요.")
        return None
    except Exception as e:
        print(f"❌ 오류: prompt.txt 파일 읽기 실패 - {e}")
        return None


def read_config_file() -> Optional[str]:
    """config.txt 파일에서 이미지 주소 읽기"""
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("image_url="):
                    url = line.replace("image_url=", "").strip()
                    if url:
                        return url
            
        print("⚠️  경고: config.txt 파일에서 image_url을 찾을 수 없습니다.")
        return None
        
    except FileNotFoundError:
        print("❌ 오류: config.txt 파일을 찾을 수 없습니다.")
        print("📝 config.txt 파일을 만들고 이미지 주소를 입력해주세요.")
        return None
    except Exception as e:
        print(f"❌ 오류: config.txt 파일 읽기 실패 - {e}")
        return None


def create_example_files():
    """예시 파일들 생성"""
    
    # prompt.txt 예시 파일
    if not os.path.exists("prompt.txt"):
        example_prompt = """한국 전통 의상을 입은 여성 전사가 벚꽃이 흩날리는 전장 한복판에 서있습니다.
그녀의 긴 검은 머리가 바람에 부드럽게 흩날리고 있습니다.
배경에는 안개 낀 산과 떨어지는 벚꽃잎들이 보입니다.
분위기는 긴장감이 돌지만 아름답고, 조명은 부드럽고 영화같습니다.
느린 동작으로 10초간 진행됩니다."""
        
        with open("prompt.txt", "w", encoding="utf-8") as f:
            f.write(example_prompt)
        print("📝 예시 prompt.txt 파일을 만들었습니다.")
    
    # config.txt 예시 파일
    if not os.path.exists("config.txt"):
        example_config = """# 동영상 생성 설정 파일
# 아래 주소를 원하는 이미지 주소로 바꾸세요

image_url=https://postfiles.pstatic.net/MjAyNTA2MjNfMTc1/MDAxNzUwNjU1OTg4NDYz.__ZDL8WNidqRd0AZIInN33dlQy0nbJAQitbt2LYyvncg.lvhFfYHN8P1qyRGMZemZiJLnqkpkfNIcySPnkPudZ_Ug.JPEG/SE-4cc39538-ad4c-4149-a7c8-815e81d4b3bc.jpg?type=w3840

# 참고: 이미지는 인터넷에서 접근 가능한 주소여야 합니다
# 예시: https://example.com/my-image.jpg"""
        
        with open("config.txt", "w", encoding="utf-8") as f:
            f.write(example_config)
        print("⚙️  예시 config.txt 파일을 만들었습니다.")


def main():
    """메인 실행 함수"""
    
    print("🎥 쉬운 동영상 생성기")
    print("=" * 40)
    print()
    
    # API 키 확인
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        print("❌ 오류: API 키가 설정되지 않았습니다.")
        print()
        print("💡 해결 방법:")
        print("   1. 터미널(Terminal)을 열어주세요")
        print("      - Spotlight 검색(⌘+Space)에서 'terminal' 입력")
        print("      - 또는 Applications > Utilities > Terminal")
        print("   2. 다음 명령어를 입력하세요:")
        print("      export ARK_API_KEY=여기에_실제_API_키_입력")
        print("   3. 이 프로그램을 다시 실행하세요")
        print()
        input("아무 키나 눌러서 종료하세요...")
        return
    
    # 예시 파일 생성
    create_example_files()
    
    # 설정 파일들 읽기
    print("📂 설정 파일을 읽는 중...")
    
    prompt_text = read_prompt_file()
    if not prompt_text:
        print("\n💡 prompt.txt 파일을 확인하고 다시 실행해주세요.")
        input("아무 키나 눌러서 종료하세요...")
        return
    
    image_url = read_config_file()
    if not image_url:
        print("\n💡 config.txt 파일을 확인하고 다시 실행해주세요.")
        input("아무 키나 눌러서 종료하세요...")
        return
    
    print("✅ 설정 파일을 모두 읽었습니다!")
    print()
    
    # 설정 내용 확인
    print("📋 확인된 설정:")
    print(f"   동영상 설명: {prompt_text[:60]}{'...' if len(prompt_text) > 60 else ''}")
    print(f"   이미지 주소: {image_url[:60]}{'...' if len(image_url) > 60 else ''}")
    print()
    
    # 사용자 확인
    confirm = input("🚀 동영상 생성을 시작할까요? (엔터를 누르면 시작, 'n' 입력하면 취소): ").strip().lower()
    if confirm == 'n':
        print("❌ 작업이 취소되었습니다.")
        input("아무 키나 눌러서 종료하세요...")
        return
    
    # 동영상 생성기 시작
    try:
        video_maker = EasyVideoMaker(api_key)
        result_path = video_maker.create_video(prompt_text, image_url)
        
        if result_path:
            print()
            print("🎊 축하합니다! 동영상 생성이 완료되었습니다!")
            print(f"📁 저장 위치: {os.path.abspath(result_path)}")
            print()
            print("💡 팁: 다른 동영상을 만들려면 prompt.txt나 config.txt를 수정하고 다시 실행하세요!")
        else:
            print()
            print("😔 동영상 생성에 실패했습니다.")
            print("💡 잠시 후 다시 시도해보세요.")
        
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
    
    print()
    input("아무 키나 눌러서 종료하세요...")


if __name__ == "__main__":
    main()
