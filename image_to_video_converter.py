#!/usr/bin/env python3
"""
BytePlus API를 사용한 동영상 생성 및 다운로드 스크립트
seedance-1-0-lite-i2v-250428 모델을 사용하여 이미지에서 동영상을 생성합니다.
"""

import requests
import time
import json
import os
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BytePlusVideoGenerator:
    """BytePlus API를 사용한 동영상 생성 클래스"""
    
    def __init__(self, api_key: str, base_url: str = "https://ark.ap-southeast.bytepluses.com"):
        """
        초기화
        
        Args:
            api_key (str): BytePlus API 키
            base_url (str): API 기본 URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
    def create_video_task(self, prompt_text: str, image_url: str, model: str = "seedance-1-0-lite-i2v-250428") -> Optional[str]:
        """
        동영상 생성 작업을 시작합니다.
        
        Args:
            prompt_text (str): 동영상 생성을 위한 텍스트 프롬프트
            image_url (str): 참조할 이미지 URL
            model (str): 사용할 모델명
            
        Returns:
            Optional[str]: 생성된 작업 ID, 실패시 None
        """
        url = f"{self.base_url}/api/v3/contents/generations/tasks"
        
        payload = {
            "model": model,
            "content": [
                {
                    "type": "text",
                    "text": prompt_text
                },
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
        
        try:
            logger.info("동영상 생성 작업을 시작합니다...")
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            task_id = data.get("id")
            
            if task_id:
                logger.info(f"작업이 성공적으로 생성되었습니다. Task ID: {task_id}")
                return task_id
            else:
                logger.error("작업 ID를 받지 못했습니다.")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 중 오류 발생: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 응답 파싱 오류: {e}")
            return None
    
    def check_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        작업 상태를 확인합니다.
        
        Args:
            task_id (str): 확인할 작업 ID
            
        Returns:
            Dict[str, Any]: 작업 상태 정보
        """
        url = f"{self.base_url}/api/v3/contents/generations/tasks/{task_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"상태 확인 중 오류 발생: {e}")
            return {"status": "error", "error": str(e)}
    
    def wait_for_completion(self, task_id: str, max_wait_time: int = 300, check_interval: int = 10) -> Optional[str]:
        """
        작업 완료까지 대기하고 결과 URL을 반환합니다.
        
        Args:
            task_id (str): 대기할 작업 ID
            max_wait_time (int): 최대 대기 시간 (초)
            check_interval (int): 상태 확인 간격 (초)
            
        Returns:
            Optional[str]: 생성된 동영상 URL, 실패시 None
        """
        logger.info(f"작업 완료를 기다리는 중... (최대 {max_wait_time}초)")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_data = self.check_task_status(task_id)
            status = status_data.get("status")
            
            if status == "succeeded":
                video_url = status_data.get("content", {}).get("video_url")
                if video_url:
                    logger.info("동영상 생성이 완료되었습니다!")
                    return video_url
                else:
                    logger.error("성공했지만 동영상 URL을 찾을 수 없습니다.")
                    return None
                    
            elif status == "failed":
                logger.error("동영상 생성이 실패했습니다.")
                return None
                
            elif status == "running":
                logger.info(f"작업 진행 중... ({int(time.time() - start_time)}초 경과)")
                
            else:
                logger.warning(f"알 수 없는 상태: {status}")
            
            time.sleep(check_interval)
        
        logger.error(f"시간 초과: {max_wait_time}초 내에 작업이 완료되지 않았습니다.")
        return None
    
    def download_video(self, video_url: str, output_dir: str = "downloads") -> Optional[str]:
        """
        동영상을 다운로드합니다.
        
        Args:
            video_url (str): 다운로드할 동영상 URL
            output_dir (str): 저장할 디렉토리
            
        Returns:
            Optional[str]: 저장된 파일 경로, 실패시 None
        """
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # URL에서 파일명 추출
            parsed_url = urlparse(video_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not filename.endswith('.mp4'):
                filename = f"generated_video_{int(time.time())}.mp4"
            
            output_path = os.path.join(output_dir, filename)
            
            logger.info(f"동영상 다운로드 중: {filename}")
            
            # 동영상 다운로드
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"다운로드 완료: {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"다운로드 중 오류 발생: {e}")
            return None
        except IOError as e:
            logger.error(f"파일 저장 중 오류 발생: {e}")
            return None
    
    def generate_and_download(self, prompt_text: str, image_url: str, output_dir: str = "downloads") -> Optional[str]:
        """
        동영상 생성부터 다운로드까지 전체 프로세스를 실행합니다.
        
        Args:
            prompt_text (str): 동영상 생성을 위한 텍스트 프롬프트
            image_url (str): 참조할 이미지 URL
            output_dir (str): 저장할 디렉토리
            
        Returns:
            Optional[str]: 저장된 파일 경로, 실패시 None
        """
        # 1. 작업 생성
        task_id = self.create_video_task(prompt_text, image_url)
        if not task_id:
            return None
        
        # 2. 작업 완료 대기
        video_url = self.wait_for_completion(task_id)
        if not video_url:
            return None
        
        # 3. 동영상 다운로드
        return self.download_video(video_url, output_dir)


def get_user_input() -> tuple[str, str]:
    """
    사용자로부터 프롬프트 텍스트와 이미지 URL을 입력받습니다.
    
    Returns:
        tuple[str, str]: (prompt_text, image_url)
    """
    print("=== BytePlus 동영상 생성기 ===\n")
    
    # 프롬프트 텍스트 입력
    print("1. 동영상 생성을 위한 프롬프트를 입력하세요:")
    print("   (예: A dramatic cinematic zoom-in on a warrior girl...)")
    print("   빈 값을 입력하면 기본 예시를 사용합니다.\n")
    
    prompt_text = input("프롬프트: ").strip()
    
    # 기본값 설정
    if not prompt_text:
        prompt_text = ("A dramatic cinematic zoom-in on a warrior girl in traditional Korean hanbok armor, "
                      "standing still in the center of a battlefield. Her long dark hair flows gently in the wind. "
                      "The background shows falling cherry blossoms and misty mountains. The atmosphere is tense, "
                      "with ambient lighting and epic orchestral music in the background. hd, ultra detailed, "
                      "slow motion, 10 seconds.")
        print(f"✅ 기본 프롬프트를 사용합니다.")
    
    print()
    
    # 이미지 URL 입력
    print("2. 참조할 이미지 URL을 입력하세요:")
    print("   (예: https://example.com/image.jpg)")
    print("   빈 값을 입력하면 기본 예시를 사용합니다.\n")
    
    image_url = input("이미지 URL: ").strip()
    
    # 기본값 설정
    if not image_url:
        image_url = "https://postfiles.pstatic.net/MjAyNTA2MjNfMTc1/MDAxNzUwNjU1OTg4NDYz.__ZDL8WNidqRd0AZIInN33dlQy0nbJAQitbt2LYyvncg.lvhFfYHN8P1qyRGMZemZiJLnqkpkfNIcySPnkPudZ_Ug.JPEG/SE-4cc39538-ad4c-4149-a7c8-815e81d4b3bc.jpg?type=w3840"
        print(f"✅ 기본 이미지 URL을 사용합니다.")
    
    # URL 유효성 간단 체크
    if not (image_url.startswith('http://') or image_url.startswith('https://')):
        print("⚠️  경고: 유효하지 않은 URL 형식일 수 있습니다.")
    
    return prompt_text, image_url


def main():
    """메인 실행 함수"""
    
    # [확실] 환경변수에서 API 키 읽기
    API_KEY = os.getenv("ARK_API_KEY")
    if not API_KEY:
        logger.error("ARK_API_KEY 환경변수가 설정되지 않았습니다.")
        print("❌ 오류: ARK_API_KEY 환경변수를 설정해주세요.")
        print("예시: export ARK_API_KEY=your-api-key")
        return
    
    # [확실] 사용자 입력 받기
    try:
        prompt_text, image_url = get_user_input()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 중단되었습니다.")
        return
    except Exception as e:
        print(f"\n❌ 입력 중 오류가 발생했습니다: {e}")
        return
    
    print(f"\n{'='*50}")
    print("입력 정보 확인:")
    print(f"프롬프트: {prompt_text[:100]}{'...' if len(prompt_text) > 100 else ''}")
    print(f"이미지 URL: {image_url}")
    print(f"{'='*50}\n")
    
    # 사용자 확인
    confirm = input("동영상 생성을 시작하시겠습니까? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ 작업이 취소되었습니다.")
        return
    
    # VideoGenerator 인스턴스 생성
    generator = BytePlusVideoGenerator(API_KEY)
    
    # 동영상 생성 및 다운로드 실행
    print("\n=== 동영상 생성 시작 ===")
    output_path = generator.generate_and_download(prompt_text, image_url)
    
    if output_path:
        print(f"\n✅ 성공! 동영상이 저장되었습니다: {output_path}")
        print(f"파일 크기: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
    else:
        print("\n❌ 동영상 생성에 실패했습니다.")


if __name__ == "__main__":
    main()
