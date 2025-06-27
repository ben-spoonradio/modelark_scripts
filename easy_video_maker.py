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
import sys
import base64
import mimetypes
from typing import Optional
import logging
import subprocess
from PIL import Image
import cv2

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
    
    def check_task_status(self, task_id: str) -> Optional[dict]:
        """특정 작업의 상태 확인"""
        print(f"🔍 작업 상태를 확인합니다: {task_id}")
        
        check_url = f"{self.base_url}/api/v3/contents/generations/tasks/{task_id}"
        
        try:
            response = requests.get(check_url, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status")
            created_at = result.get("created_at")
            updated_at = result.get("updated_at")
            
            print(f"📊 작업 정보:")
            print(f"   ID: {task_id}")
            print(f"   상태: {status}")
            
            if created_at:
                created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_at))
                print(f"   생성 시간: {created_time}")
            
            if updated_at:
                updated_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(updated_at))
                print(f"   업데이트 시간: {updated_time}")
            
            if status == "succeeded":
                video_url = result.get("content", {}).get("video_url")
                if video_url:
                    print(f"✅ 완료! 동영상 다운로드 가능")
                    print(f"   다운로드 URL: {video_url}")
                    
                    # 토큰 사용량 표시
                    usage = result.get("usage", {})
                    if usage.get("completion_tokens"):
                        print(f"   토큰 사용량: {usage['completion_tokens']:,}")
                    
                    # 다운로드 옵션 제공
                    download = input("\n📥 지금 다운로드하시겠습니까? (y/n): ").strip().lower()
                    if download == 'y':
                        return self._download_video(video_url)
                    
            elif status == "failed":
                error_info = result.get("error", {})
                error_code = error_info.get("code", "Unknown")
                error_message = error_info.get("message", "알 수 없는 오류")
                
                print(f"❌ 실패:")
                print(f"   오류 코드: {error_code}")
                print(f"   오류 내용: {error_message}")
                
            elif status in ["queued", "running"]:
                print(f"⏳ 진행 중... 잠시 후 다시 확인해보세요.")
                
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 오류: 상태 확인 실패 - {e}")
            return None
    
    def create_video_batch(self, prompts: list, image_url: str = None, video_config: dict = None, start_index: int = 1, end_index: int = None) -> list:
        """여러 프롬프트로 배치 동영상 생성"""
        if video_config is None:
            video_config = {}
        
        # 인덱스 범위 조정
        total_prompts = len(prompts)
        if end_index is None:
            end_index = total_prompts
        
        # 범위 검증
        start_index = max(1, start_index)
        end_index = min(end_index, total_prompts)
        
        if start_index > end_index:
            print("❌ 오류: 시작 인덱스가 종료 인덱스보다 큽니다.")
            return []
        
        # 범위에 해당하는 프롬프트만 선택
        selected_prompts = prompts[start_index-1:end_index]
        batch_size = len(selected_prompts)
        
        print(f"🎬 배치 동영상 생성을 시작합니다")
        print(f"📋 범위: {start_index}-{end_index} ({batch_size}개 / 전체 {total_prompts}개)")
        print("=" * 50)
        
        results = []
        
        for i, prompt in enumerate(selected_prompts, start_index):
            print(f"\n📝 [{i}/{end_index}] 프롬프트: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
            
            if image_url:
                if os.path.exists(image_url):
                    print(f"🖼️  이미지: {os.path.basename(image_url)}")
                else:
                    print(f"🖼️  이미지: URL")
            else:
                print("📝 텍스트-to-비디오")
            
            # 동영상 생성
            task_id = self._start_generation(prompt.strip(), image_url, video_config)
            
            if task_id:
                print(f"✅ 작업 접수: {task_id}")
                
                result = {
                    'index': i,
                    'prompt': prompt.strip(),
                    'task_id': task_id,
                    'status': 'submitted',
                    'video_path': None
                }
                
                # 콜백 URL이 설정되지 않은 경우에만 대기
                if not video_config.get('callback_url'):
                    print("⏳ 완료 대기 중...")
                    video_url = self._wait_for_video(task_id)
                    
                    if video_url:
                        # 파일명에 인덱스 추가
                        timestamp = int(time.time())
                        filename = f"batch_{i:02d}_{timestamp}.mp4"
                        filepath = os.path.join("videos", filename)
                        
                        # 다운로드 폴더 확인
                        if not os.path.exists("videos"):
                            os.makedirs("videos")
                        
                        # 다운로드
                        downloaded_path = self._download_video_to_path(video_url, filepath)
                        if downloaded_path:
                            result['status'] = 'completed'
                            result['video_path'] = downloaded_path
                            print(f"✅ [{i}/{end_index}] 완료: {downloaded_path}")
                        else:
                            result['status'] = 'download_failed'
                            print(f"❌ [{i}/{end_index}] 다운로드 실패")
                    else:
                        result['status'] = 'generation_failed'
                        print(f"❌ [{i}/{end_index}] 생성 실패")
                else:
                    print(f"📞 [{i}/{end_index}] 콜백 대기 중...")
                    result['status'] = 'callback_pending'
            else:
                result = {
                    'index': i,
                    'prompt': prompt.strip(),
                    'task_id': None,
                    'status': 'submission_failed',
                    'video_path': None
                }
                print(f"❌ [{i}/{end_index}] 작업 접수 실패")
            
            results.append(result)
            
            # 다음 작업 전에 잠시 대기 (API 제한 방지)
            if i < end_index:
                print("⏸️  잠시 대기 중... (3초)")
                time.sleep(3)
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("📊 배치 처리 결과:")
        
        completed = sum(1 for r in results if r['status'] == 'completed')
        failed = sum(1 for r in results if r['status'] in ['generation_failed', 'download_failed', 'submission_failed'])
        pending = sum(1 for r in results if r['status'] in ['callback_pending'])
        
        print(f"✅ 완료: {completed}개")
        print(f"❌ 실패: {failed}개")
        if pending > 0:
            print(f"📞 콜백 대기: {pending}개")
        
        return results
    
    def extract_last_frame(self, video_path: str, output_path: str = None) -> Optional[str]:
        """동영상에서 마지막 프레임을 추출하여 이미지로 저장"""
        if not os.path.exists(video_path):
            print(f"❌ 동영상 파일을 찾을 수 없습니다: {video_path}")
            return None
            
        if output_path is None:
            # 자동으로 경로 생성 (동영상명_last_frame.jpg)
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = os.path.dirname(video_path)
            output_path = os.path.join(output_dir, f"{base_name}_last_frame.jpg")
        
        try:
            # OpenCV로 동영상 읽기
            cap = cv2.VideoCapture(video_path)
            
            # 마지막 프레임으로 이동
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count == 0:
                print(f"❌ 동영상에서 프레임을 읽을 수 없습니다: {video_path}")
                return None
                
            # 마지막 프레임 추출
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count - 1)
            ret, frame = cap.read()
            
            if not ret:
                print(f"❌ 마지막 프레임을 읽을 수 없습니다: {video_path}")
                return None
            
            # 이미지 저장 (BGR을 RGB로 변환)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # 이미지 크기 최적화 (Base64 인코딩을 위해 더 작게)
            max_dimension = 1280  # 더 작은 크기로 제한
            if pil_image.width > max_dimension or pil_image.height > max_dimension:
                ratio = min(max_dimension / pil_image.width, max_dimension / pil_image.height)
                new_width = int(pil_image.width * ratio)
                new_height = int(pil_image.height * ratio)
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"🔧 이미지 크기 조정: {new_width}x{new_height}")
            
            # 파일 크기 최적화를 위해 더 낮은 품질로 저장
            pil_image.save(output_path, "JPEG", quality=60, optimize=True)
            
            cap.release()
            
            print(f"✅ 마지막 프레임 추출 완료: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ 프레임 추출 실패: {e}")
            return None
    
    def create_video_chain(self, prompts: list, initial_image_url: str = None, video_config: dict = None, start_index: int = 1) -> list:
        """연속된 동영상 체인 생성 (이전 클립의 마지막 프레임을 다음 클립의 첫 프레임으로 사용)"""
        print(f"🎬 연속 동영상 체인 생성을 시작합니다! ({len(prompts)}개 클립)")
        print("🔗 각 클립의 마지막 프레임이 다음 클립의 시작 이미지로 사용됩니다.")
        print()
        
        results = []
        current_image_url = initial_image_url
        
        for i, prompt in enumerate(prompts):
            clip_number = start_index + i
            print(f"\n{'='*50}")
            print(f"🎥 클립 {clip_number}/{start_index + len(prompts) - 1} 생성 중...")
            print(f"📝 프롬프트: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            if current_image_url:
                print(f"🖼️  시작 이미지: 이전 클립의 마지막 프레임 사용")
            else:
                print(f"🖼️  시작 이미지: 없음 (텍스트 전용)")
            
            # 동영상 생성
            video_path = self.create_video(
                description=prompt,
                image_url=current_image_url,
                video_config=video_config
            )
            
            # 결과 정리
            result = {
                'clip_number': clip_number,
                'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                'status': 'completed' if video_path else 'failed',
                'local_path': video_path if video_path else None
            }
            
            if video_path and os.path.exists(video_path):
                # 마지막 프레임 추출
                frame_path = self.extract_last_frame(video_path)
                
                if frame_path:
                    # Base64로 인코딩하여 다음 클립에서 사용
                    encoded_image = self.encode_image_to_base64(frame_path)
                    if encoded_image:
                        current_image_url = f"data:image/jpeg;base64,{encoded_image}"
                        result['extracted_frame_path'] = frame_path
                        print(f"✅ 다음 클립용 프레임 준비 완료")
                    else:
                        print(f"⚠️  프레임 인코딩 실패, 다음 클립은 텍스트 전용으로 진행")
                        current_image_url = None
                else:
                    print(f"⚠️  프레임 추출 실패, 다음 클립은 텍스트 전용으로 진행")
                    current_image_url = None
            else:
                print(f"⚠️  클립 {clip_number} 생성 실패, 다음 클립은 텍스트 전용으로 진행")
                current_image_url = None
            
            results.append(result)
            
            # 다음 작업 전에 잠시 대기 (API 제한 방지)
            if i < len(prompts) - 1:
                print("⏸️  잠시 대기 중... (5초)")
                time.sleep(5)
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("🔗 연속 동영상 체인 생성 결과:")
        
        completed = sum(1 for r in results if r and r.get('status') == 'completed')
        failed = sum(1 for r in results if not r or r.get('status') in ['generation_failed', 'download_failed', 'submission_failed'])
        
        print(f"✅ 완료: {completed}개")
        print(f"❌ 실패: {failed}개")
        
        successful_clips = [r for r in results if r and r.get('status') == 'completed']
        if successful_clips:
            print(f"\n📁 생성된 동영상 파일들:")
            for i, result in enumerate(successful_clips):
                clip_num = start_index + results.index(result)
                print(f"   {clip_num}. {result.get('local_path', '파일 없음')}")
        
        return results
    
    def _download_video_to_path(self, video_url: str, filepath: str) -> Optional[str]:
        """동영상을 지정된 경로에 다운로드"""
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return filepath
            
        except Exception as e:
            print(f"❌ 다운로드 실패: {e}")
            return None

    def list_recent_tasks(self, limit: int = 10) -> Optional[list]:
        """최근 작업 목록 조회"""
        print(f"📋 최근 작업 {limit}개를 조회합니다...")
        
        list_url = f"{self.base_url}/api/v3/contents/generations/tasks"
        params = {
            "page_num": 1,
            "page_size": limit
        }
        
        try:
            response = requests.get(list_url, headers=self.headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            tasks = result.get("items", [])
            total = result.get("total", 0)
            
            if not tasks:
                print("📭 최근 작업이 없습니다.")
                return []
            
            print(f"📊 총 {total}개 작업 중 최근 {len(tasks)}개:")
            print()
            
            for i, task in enumerate(tasks, 1):
                task_id = task.get("id", "")
                status = task.get("status", "")
                created_at = task.get("created_at")
                model = task.get("model", "")
                
                status_emoji = {
                    "succeeded": "✅",
                    "failed": "❌", 
                    "running": "⏳",
                    "queued": "🔄"
                }.get(status, "❓")
                
                created_time = ""
                if created_at:
                    created_time = time.strftime('%m-%d %H:%M', time.localtime(created_at))
                
                print(f"{i:2d}. {status_emoji} {task_id} [{status}] {created_time}")
                if model:
                    model_short = model.split('-')[-1] if '-' in model else model
                    print(f"     모델: {model_short}")
                
                # 실패한 경우 오류 정보 표시
                if status == "failed":
                    error_info = task.get("error", {})
                    if error_info.get("code"):
                        print(f"     오류: {error_info.get('code', '')}")
                
                print()
            
            return tasks
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 오류: 작업 목록 조회 실패 - {e}")
            return None
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """로컬 이미지 파일을 Base64로 인코딩"""
        try:
            # 파일 존재 확인
            if not os.path.exists(image_path):
                print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
                return None
            
            # 파일 크기 확인 (5MB 제한)
            file_size = os.path.getsize(image_path)
            if file_size > 5 * 1024 * 1024:
                print(f"❌ 이미지 파일이 너무 큽니다: {file_size / (1024*1024):.1f}MB (최대 5MB)")
                return None
            
            # MIME 타입 확인
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                print(f"❌ 지원되지 않는 이미지 형식입니다: {image_path}")
                print("💡 지원 형식: JPEG, PNG, WEBP, BMP, TIFF, GIF")
                return None
            
            # 지원되는 형식 확인
            supported_formats = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff', 'image/gif']
            if mime_type not in supported_formats:
                print(f"❌ 지원되지 않는 이미지 형식입니다: {mime_type}")
                print("💡 지원 형식: JPEG, PNG, WEBP, BMP, TIFF, GIF")
                return None
            
            print(f"📸 이미지를 Base64로 인코딩하는 중... ({file_size / 1024:.1f}KB)")
            
            # 이미지 최적화 (크기 줄이기)
            from PIL import Image
            with Image.open(image_path) as img:
                # 이미지 크기를 최대 1024x1024로 제한
                max_size = 1024
                if img.width > max_size or img.height > max_size:
                    ratio = min(max_size / img.width, max_size / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"🔧 Base64용 이미지 크기 조정: {new_width}x{new_height}")
                
                # RGB로 변환 (RGBA인 경우)
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 메모리에서 JPEG로 압축
                import io
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=75, optimize=True)
                img_buffer.seek(0)
                
                # Base64 인코딩
                encoded_string = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            # Base64 크기 확인 (API 제한 확인을 위해)
            base64_size_mb = len(encoded_string) / (1024 * 1024)
            print(f"✅ Base64 인코딩 완료! (크기: {base64_size_mb:.2f}MB)")
            
            if base64_size_mb > 8:  # Base64 크기 제한
                print("⚠️  Base64 데이터가 너무 큽니다. 이미지를 더 작게 만들어보세요.")
                return None
            
            # 순수 Base64 문자열만 반환 (data: prefix 없이)
            return encoded_string
            
        except Exception as e:
            print(f"❌ Base64 인코딩 실패: {e}")
            return None
    
    def validate_image_dimensions(self, image_path: str) -> bool:
        """이미지 크기 검증 (API 요구사항 확인)"""
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                width, height = img.size
                
                # 화면비 확인 (0.4 ~ 2.5)
                aspect_ratio = width / height
                if aspect_ratio < 0.4 or aspect_ratio > 2.5:
                    print(f"❌ 이미지 화면비가 범위를 벗어났습니다: {aspect_ratio:.2f}")
                    print("💡 허용 범위: 0.4 ~ 2.5 (2:5 ~ 5:2)")
                    return False
                
                # 픽셀 크기 확인
                min_side = min(width, height)
                max_side = max(width, height)
                
                if min_side < 300:
                    print(f"❌ 이미지가 너무 작습니다: {min_side}px (최소 300px)")
                    return False
                
                if max_side > 6000:
                    print(f"❌ 이미지가 너무 큽니다: {max_side}px (최대 6000px)")
                    return False
                
                print(f"✅ 이미지 크기 검증 통과: {width}x{height} (비율: {aspect_ratio:.2f})")
                return True
                
        except ImportError:
            print("⚠️  PIL 라이브러리가 없어서 이미지 크기 검증을 건너뜁니다.")
            print("💡 정확한 검증을 위해 'pip install Pillow'를 실행하세요.")
            return True
        except Exception as e:
            print(f"⚠️  이미지 크기 검증 실패: {e}")
            return True
    
    def create_video(self, description: str, image_url: str = None, video_config: dict = None) -> Optional[str]:
        """동영상을 만들고 파일로 저장합니다"""
        
        if video_config is None:
            video_config = {}
        
        print("🎬 동영상 생성을 시작합니다...")
        print(f"📝 설명: {description[:50]}{'...' if len(description) > 50 else ''}")
        if image_url:
            print(f"🖼️  이미지: {image_url}")
        else:
            print("📝 텍스트만으로 동영상을 생성합니다")
        
        # 비디오 설정 표시
        display_ratio = video_config.get('ratio', '16:9')
        if image_url and display_ratio not in ['adaptive', 'keep_ratio']:
            display_ratio = f"{display_ratio} → adaptive (i2v 제한)"
        
        print(f"⚙️  설정: {video_config.get('resolution', '720p')} | {display_ratio} | {video_config.get('duration', 5)}초 | {video_config.get('fps', 24)}fps")
        print()
        
        # 1단계: 동영상 생성 요청
        task_id = self._start_generation(description, image_url, video_config)
        if not task_id:
            return None
        
        # 콜백 URL이 설정된 경우 기다리지 않고 task_id만 반환
        if video_config.get('callback_url'):
            print("📞 콜백 URL이 설정되어 있습니다.")
            print("🔔 작업 완료 시 자동으로 알림을 받게 됩니다.")
            print(f"📋 작업 ID: {task_id}")
            print("💡 수동으로 상태를 확인하려면:")
            print(f"   python easy_video_maker.py --check {task_id}")
            return task_id
        
        # 2단계: 완료까지 기다리기
        video_url = self._wait_for_video(task_id)
        if not video_url:
            return None
        
        # 3단계: 동영상 다운로드
        return self._download_video(video_url)
    
    def _start_generation(self, description: str, image_url: str = None, video_config: dict = None) -> Optional[str]:
        """동영상 생성 시작"""
        url = f"{self.base_url}/api/v3/contents/generations/tasks"
        
        if video_config is None:
            video_config = {}
        
        # 텍스트 프롬프트에 파라미터 추가
        text_prompt = description
        
        # API 문서에 따른 파라미터 추가
        params = []
        
        # 이미지가 있는 경우 (i2v)와 없는 경우 (t2v)에 따라 파라미터 제한
        if image_url:
            # i2v 모델에서는 ratio가 adaptive만 지원
            if video_config.get('ratio') and video_config['ratio'] != 'keep_ratio':
                params.append("--ratio adaptive")
            elif video_config.get('ratio') == 'keep_ratio':
                params.append("--ratio keep_ratio")
        else:
            # t2v 모델에서는 모든 ratio 지원
            if video_config.get('ratio'):
                params.append(f"--ratio {video_config['ratio']}")
        
        if video_config.get('resolution'):
            params.append(f"--resolution {video_config['resolution']}")
        if video_config.get('duration'):
            params.append(f"--duration {video_config['duration']}")
        if video_config.get('fps'):
            params.append(f"--fps {video_config['fps']}")
        if video_config.get('watermark', False):
            params.append(f"--watermark {str(video_config['watermark']).lower()}")
        if video_config.get('seed', -1) != -1:
            params.append(f"--seed {video_config['seed']}")
        if video_config.get('camerafixed', False):
            params.append(f"--camerafixed {str(video_config['camerafixed']).lower()}")
        
        if params:
            text_prompt += " " + " ".join(params)
        
        # 이미지가 있으면 i2v 모델, 없으면 t2v 모델 사용
        if image_url:
            model = "seedance-1-0-lite-i2v-250428"
            
            # 로컬 파일인지 URL인지 확인
            if os.path.exists(image_url):
                print(f"📁 로컬 이미지 파일 감지: {image_url}")
                
                # 이미지 크기 검증
                if not self.validate_image_dimensions(image_url):
                    print("❌ 이미지 크기 검증 실패")
                    return None
                
                # Base64로 인코딩
                base64_image = self.encode_image_to_base64(image_url)
                if not base64_image:
                    return None
                
                # MIME 타입 확인하여 data URL 형식으로 변환
                mime_type, _ = mimetypes.guess_type(image_url)
                if not mime_type or not mime_type.startswith('image/'):
                    # 파일 확장자로 MIME 타입 결정
                    ext = os.path.splitext(image_url.lower())[1]
                    if ext in ['.jpg', '.jpeg']:
                        mime_type = "image/jpeg"
                    elif ext == '.png':
                        mime_type = "image/png"
                    elif ext == '.webp':
                        mime_type = "image/webp"
                    elif ext == '.gif':
                        mime_type = "image/gif"
                    elif ext == '.bmp':
                        mime_type = "image/bmp"
                    elif ext in ['.tiff', '.tif']:
                        mime_type = "image/tiff"
                    else:
                        mime_type = "image/jpeg"  # 기본값
                
                final_image_url = f"data:{mime_type};base64,{base64_image}"
                print("🔄 로컬 이미지를 Base64로 변환하여 사용합니다")
            else:
                final_image_url = image_url
                print("🌐 URL 이미지를 사용합니다")
            
            content = [
                {"type": "text", "text": text_prompt},
                {"type": "image_url", "image_url": {"url": final_image_url}}
            ]
            print("🎬 이미지-to-비디오 모드로 생성합니다")
        else:
            model = "seedance-1-0-lite-t2v-250428"
            content = [
                {"type": "text", "text": text_prompt}
            ]
            print("📝 텍스트-to-비디오 모드로 생성합니다")
        
        data = {
            "model": model,
            "content": content
        }
        
        # 콜백 URL이 설정되어 있으면 추가
        if video_config.get('callback_url'):
            data['callback_url'] = video_config['callback_url']
            print(f"📞 콜백 URL 설정: {video_config['callback_url']}")
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code != 200:
                print(f"❌ API 오류: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"📋 오류 상세:")
                    print(f"   {error_data}")
                except:
                    print(f"📋 오류 내용: {response.text}")
                return None
            
            result = response.json()
            
            task_id = result.get("id")
            if task_id:
                print("✅ 동영상 생성 요청이 접수되었습니다!")
                return task_id
            else:
                print("❌ 오류: 작업 ID를 받지 못했습니다.")
                print(f"📋 응답 내용: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return None
    
    def _wait_for_video(self, task_id: str) -> Optional[str]:
        """동영상 완성까지 기다리기"""
        print("⏳ 동영상을 만들고 있습니다. 잠시만 기다려주세요...")
        print("   (보통 1-3분 정도 걸립니다)")
        print(f"   작업 ID: {task_id}")
        print()
        
        check_url = f"{self.base_url}/api/v3/contents/generations/tasks/{task_id}"
        start_time = time.time()
        
        for i in range(60):  # 최대 10분 대기 (10초씩 60번)
            try:
                response = requests.get(check_url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
                
                status = result.get("status")
                elapsed_time = int(time.time() - start_time)
                
                if status == "succeeded":
                    video_url = result.get("content", {}).get("video_url")
                    if video_url:
                        print(f"\n🎉 동영상이 완성되었습니다! (소요시간: {elapsed_time}초)")
                        # 토큰 사용량 표시
                        usage = result.get("usage", {})
                        if usage.get("completion_tokens"):
                            print(f"📊 토큰 사용량: {usage['completion_tokens']:,} 토큰")
                        return video_url
                    else:
                        print("\n❌ 오류: 동영상 주소를 찾을 수 없습니다.")
                        return None
                
                elif status == "failed":
                    error_info = result.get("error", {})
                    error_code = error_info.get("code", "Unknown")
                    error_message = error_info.get("message", "알 수 없는 오류")
                    
                    print(f"\n❌ 동영상 생성 실패:")
                    print(f"   오류 코드: {error_code}")
                    print(f"   오류 내용: {error_message}")
                    
                    # 일반적인 오류에 대한 안내
                    if "SensitiveContent" in error_code:
                        print("💡 해결방법: 프롬프트 내용을 수정해서 다시 시도해보세요.")
                    elif "QuotaExceeded" in error_code:
                        print("💡 해결방법: 잠시 후 다시 시도해보세요. (할당량 초과)")
                    
                    return None
                
                elif status == "queued":
                    dots = "." * ((i % 3) + 1)
                    print(f"\r   대기 중{dots} ({elapsed_time}초 경과)   ", end="", flush=True)
                    time.sleep(5)  # 대기중일 때는 5초마다 확인
                    
                elif status == "running":
                    dots = "." * ((i % 3) + 1)
                    print(f"\r   생성 중{dots} ({elapsed_time}초 경과)   ", end="", flush=True)
                    time.sleep(10)  # 실행중일 때는 10초마다 확인
                    
                else:  # 기타 상태
                    dots = "." * ((i % 3) + 1)
                    print(f"\r   작업 중{dots} 상태: {status} ({elapsed_time}초 경과)   ", end="", flush=True)
                    time.sleep(10)
            
            except requests.exceptions.RequestException as e:
                print(f"\n❌ 네트워크 오류: {e}")
                print("💡 인터넷 연결을 확인하고 다시 시도해주세요.")
                return None
            except Exception as e:
                print(f"\n❌ 오류: 상태 확인 실패 - {e}")
                return None
        
        print(f"\n⏰ 시간 초과: 10분이 지났습니다.")
        print("💡 작업이 계속 진행 중일 수 있습니다. 잠시 후 다음 명령어로 확인해보세요:")
        print(f"   python easy_video_maker.py --check {task_id}")
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


def read_batch_prompts_file() -> Optional[list]:
    """batch_prompts.txt 파일에서 여러 프롬프트 읽기"""
    try:
        with open("batch_prompts.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        prompts = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            # 빈 줄이나 주석 줄 무시
            if line and not line.startswith("#"):
                prompts.append(line)
        
        if prompts:
            print(f"📝 {len(prompts)}개의 프롬프트를 읽었습니다.")
            return prompts
        else:
            print("⚠️  경고: batch_prompts.txt 파일에 유효한 프롬프트가 없습니다.")
            return None
            
    except FileNotFoundError:
        print("❌ 오류: batch_prompts.txt 파일을 찾을 수 없습니다.")
        print("📝 batch_prompts.txt 파일을 만들고 각 줄에 프롬프트를 작성해주세요.")
        return None
    except Exception as e:
        print(f"❌ 오류: batch_prompts.txt 파일 읽기 실패 - {e}")
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


def select_image_from_folder() -> Optional[str]:
    """images 폴더에서 이미지 선택"""
    images_dir = "images"
    
    # images 폴더가 없으면 생성
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
        print(f"📁 {images_dir} 폴더를 생성했습니다.")
        print("💡 이 폴더에 이미지 파일을 넣고 다시 실행하세요.")
        return None
    
    # 지원되는 이미지 확장자
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}
    
    # 이미지 파일 찾기
    image_files = []
    for file in os.listdir(images_dir):
        if os.path.splitext(file.lower())[1] in image_extensions:
            image_files.append(file)
    
    if not image_files:
        print(f"❌ {images_dir} 폴더에 이미지 파일이 없습니다.")
        print("💡 지원 형식: JPEG, PNG, WEBP, BMP, TIFF, GIF")
        return None
    
    # 이미지 파일 목록 표시
    print(f"📁 {images_dir} 폴더의 이미지 파일들:")
    print()
    
    for i, file in enumerate(image_files, 1):
        file_path = os.path.join(images_dir, file)
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"  {i:2d}. {file} ({file_size:.1f}KB)")
    
    print(f"  {len(image_files) + 1:2d}. 이미지 없이 텍스트만 사용")
    print()
    
    # 사용자 선택
    while True:
        try:
            choice = input(f"이미지를 선택하세요 (1-{len(image_files) + 1}): ").strip()
            
            if not choice:
                print("❌ 선택해주세요.")
                continue
                
            choice_num = int(choice)
            
            if choice_num == len(image_files) + 1:
                # 텍스트만 사용
                return None
            elif 1 <= choice_num <= len(image_files):
                selected_file = image_files[choice_num - 1]
                selected_path = os.path.join(images_dir, selected_file)
                print(f"✅ 선택된 이미지: {selected_file}")
                return selected_path
            else:
                print(f"❌ 1-{len(image_files) + 1} 사이의 숫자를 입력하세요.")
                
        except ValueError:
            print("❌ 숫자를 입력하세요.")
        except KeyboardInterrupt:
            print("\n❌ 사용자가 취소했습니다.")
            return None

def read_config_file() -> dict:
    """config.txt 파일에서 설정 읽기 (이미지 URL과 비디오 파라미터)"""
    config = {
        'resolution': '720p',
        'ratio': '16:9', 
        'duration': 5,
        'fps': 24,
        'watermark': False,
        'seed': -1,
        'camerafixed': False,
        'callback_url': None,
        'image_file': None
    }
    try:
        with open("config.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 주석이 아닌 설정 줄들 처리
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "resolution" and value in ["480p", "720p"]:
                        config['resolution'] = value
                    elif key == "ratio" and value in ["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "9:21", "keep_ratio"]:
                        config['ratio'] = value
                    elif key == "duration" and value.isdigit() and int(value) in [5, 10]:
                        config['duration'] = int(value)
                    elif key == "fps" and value.isdigit() and int(value) in [16, 24]:
                        config['fps'] = int(value)
                    elif key == "watermark" and value.lower() in ["true", "false"]:
                        config['watermark'] = value.lower() == "true"
                    elif key == "seed" and (value == "-1" or (value.isdigit() and 0 <= int(value) <= 4294967295)):
                        config['seed'] = int(value)
                    elif key == "camerafixed" and value.lower() in ["true", "false"]:
                        config['camerafixed'] = value.lower() == "true"
                    elif key == "callback_url" and value.startswith("http"):
                        config['callback_url'] = value
                    elif key == "image_file" and value:
                        config['image_file'] = value
        
        return config
        
    except FileNotFoundError:
        print("ℹ️  config.txt 파일이 없습니다. 기본 설정을 사용합니다.")
        return config
    except Exception as e:
        print(f"❌ 오류: config.txt 파일 읽기 실패 - {e}")
        return config


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
    
    # batch_prompts.txt 예시 파일
    if not os.path.exists("batch_prompts.txt"):
        example_batch_prompts = """# 배치 동영상 생성용 프롬프트 파일
# 각 줄에 하나씩 프롬프트를 작성하세요
# # 으로 시작하는 줄은 주석으로 무시됩니다

한국 전통 의상을 입은 여성이 벚꽃 나무 아래에서 춤을 춥니다
고양이가 눈 내리는 정원에서 뛰어다니고 있습니다
바다 위에서 돌고래들이 점프하며 놀고 있습니다
산속 계곡에서 폭포가 떨어지고 무지개가 나타납니다
밤하늘에 별들이 반짝이며 유성이 지나갑니다

# 더 많은 프롬프트를 추가하세요
# 로봇이 미래 도시를 걸어다닙니다
# 마법사가 마법의 숲에서 주문을 외웁니다"""
        
        with open("batch_prompts.txt", "w", encoding="utf-8") as f:
            f.write(example_batch_prompts)
        print("📝 예시 batch_prompts.txt 파일을 만들었습니다.")
    
    # config.txt 예시 파일
    if not os.path.exists("config.txt"):
        example_config = """# 🎬 동영상 생성 설정 파일
# 이미지는 실행 시 images/ 폴더에서 선택할 수 있습니다.

# 🎥 비디오 파라미터 설정

# 해상도 (480p, 720p)
resolution=720p

# 화면비 
# - 텍스트-to-비디오: 16:9, 4:3, 1:1, 3:4, 9:16, 21:9, 9:21, keep_ratio
# - 이미지-to-비디오: adaptive, keep_ratio만 지원 (다른 값 설정시 자동으로 adaptive 사용)
ratio=9:16

# 동영상 길이 (5, 10) - 초 단위
duration=5

# 프레임율 (16, 24) - fps
fps=24

# 워터마크 (true, false)
watermark=false

# 시드 값 (-1은 랜덤, 0~4294967295 사이의 숫자)
seed=-1

# 카메라 고정 (true, false)
camerafixed=false

# 콜백 URL (작업 완료 시 알림받을 웹훅 URL)
# callback_url=https://your-server.com/webhook

# 🔔 콜백 URL 설정 방법:
# 1. 웹훅을 받을 수 있는 서버나 서비스 준비
# 2. 위 callback_url 주석을 해제하고 URL 입력
# 3. 작업 완료 시 자동으로 POST 요청이 전송됩니다
# 4. 콜백이 설정되면 프로그램이 바로 종료되고 알림을 기다립니다

# 💡 사용법:
# 1. images/ 폴더에 사용할 이미지 파일을 넣으세요
# 2. 프로그램 실행 시 이미지를 선택할 수 있습니다
# 3. 이미지 없이 텍스트만으로도 동영상 생성 가능

# 📋 지원 이미지 형식: JPEG, PNG, WEBP, BMP, TIFF, GIF
# 📏 이미지 제한: 최대 10MB, 300px~6000px, 화면비 0.4~2.5"""
        
        with open("config.txt", "w", encoding="utf-8") as f:
            f.write(example_config)
        print("⚙️  예시 config.txt 파일을 만들었습니다.")
    
    # images 폴더 생성
    if not os.path.exists("images"):
        os.makedirs("images")
        print("📁 images 폴더를 생성했습니다.")
        print("💡 이 폴더에 이미지 파일을 넣으면 실행 시 선택할 수 있습니다.")


def main():
    """메인 실행 함수"""
    
    # 커맨드라인 인수 처리
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        # API 키 확인
        api_key = os.getenv("ARK_API_KEY")
        if not api_key:
            print("❌ 오류: API 키가 설정되지 않았습니다.")
            print("💡 export ARK_API_KEY=your_api_key 를 먼저 실행하세요.")
            return
        
        video_maker = EasyVideoMaker(api_key)
        
        if command == "--check" and len(sys.argv) > 2:
            # 특정 작업 상태 확인
            task_id = sys.argv[2]
            video_maker.check_task_status(task_id)
            return
        
        elif command == "--list":
            # 최근 작업 목록 조회
            limit = 10
            if len(sys.argv) > 2 and sys.argv[2].isdigit():
                limit = int(sys.argv[2])
            video_maker.list_recent_tasks(limit)
            return
        
        elif command == "--batch":
            # 배치 모드
            print("🎬 배치 동영상 생성 모드")
            print("=" * 40)
            
            # 범위 파라미터 파싱
            start_index = 1
            end_index = None
            
            # --batch start end 형태로 파라미터 받기
            if len(sys.argv) > 2:
                try:
                    start_index = int(sys.argv[2])
                    if len(sys.argv) > 3:
                        end_index = int(sys.argv[3])
                except ValueError:
                    print("❌ 오류: 시작/종료 인덱스는 숫자여야 합니다.")
                    print("💡 사용법: python easy_video_maker.py --batch [시작번호] [종료번호]")
                    return
        
        elif command == "--chain":
            # 연속 체인 모드
            print("🔗 연속 동영상 체인 생성 모드")
            print("=" * 40)
            
            # 범위 파라미터 파싱
            start_index = 1
            end_index = None
            
            # --chain start end 형태로 파라미터 받기
            if len(sys.argv) > 2:
                try:
                    start_index = int(sys.argv[2])
                    if len(sys.argv) > 3:
                        end_index = int(sys.argv[3])
                except ValueError:
                    print("❌ 오류: 시작/종료 인덱스는 숫자여야 합니다.")
                    print("💡 사용법: python easy_video_maker.py --chain [시작번호] [종료번호]")
                    return
            
            # 배치 프롬프트 읽기
            batch_prompts = read_batch_prompts_file()
            if not batch_prompts:
                return
            
            # 인덱스 범위 조정
            if end_index is None:
                end_index = len(batch_prompts)
            else:
                end_index = min(end_index, len(batch_prompts))
            
            if start_index > len(batch_prompts):
                print(f"❌ 시작 인덱스 {start_index}가 프롬프트 개수 {len(batch_prompts)}보다 큽니다.")
                return
            
            selected_prompts = batch_prompts[start_index-1:end_index]
            
            print(f"📝 선택된 프롬프트: {start_index}~{end_index} ({len(selected_prompts)}개)")
            
            # 설정 파일 읽기
            video_config = read_config_file()
            
            # 첫 번째 클립용 초기 이미지 선택
            initial_image_path = None
            initial_image_url = None
            
            if video_config.get('image_file'):
                initial_image_path = video_config['image_file']
                print(f"🖼️ 설정된 초기 이미지: {initial_image_path}")
                if not os.path.exists(initial_image_path):
                    print(f"❌ 오류: 이미지 파일을 찾을 수 없습니다: {initial_image_path}")
                    print("💡 텍스트 전용으로 진행합니다")
                    initial_image_path = None
            else:
                initial_image_path = select_image_from_folder()
            
            if initial_image_path:
                encoded_image = video_maker.encode_image_to_base64(initial_image_path)
                if encoded_image:
                    initial_image_url = f"data:image/jpeg;base64,{encoded_image}"
                    print(f"✅ 초기 이미지 설정: {os.path.basename(initial_image_path)}")
                else:
                    print("❌ 초기 이미지 인코딩 실패, 텍스트 전용으로 진행")
            
            # 연속 체인 생성 실행
            results = video_maker.create_video_chain(
                prompts=selected_prompts,
                initial_image_url=initial_image_url,
                video_config=video_config,
                start_index=start_index
            )
            
            # 결과 저장 (간단한 출력으로 대체)
            print(f"\n📊 체인 생성 완료: {len([r for r in results if r.get('status') == 'completed'])}개 성공")
            return
            
            # 배치 프롬프트 읽기
            prompts = read_batch_prompts_file()
            if not prompts:
                return
            
            # 범위 검증 및 조정
            total_prompts = len(prompts)
            if end_index is None:
                end_index = total_prompts
            
            start_index = max(1, start_index)
            end_index = min(end_index, total_prompts)
            
            if start_index > end_index:
                print(f"❌ 오류: 시작 인덱스({start_index})가 종료 인덱스({end_index})보다 큽니다.")
                return
            
            # 설정 읽기
            video_config = read_config_file()
            
            # 이미지 선택
            print("\n🖼️ 이미지 선택 (모든 동영상에 동일한 이미지 사용):")
            image_url = select_image_from_folder()
            
            print(f"\n📋 배치 설정 확인:")
            print(f"   전체 프롬프트: {total_prompts}개")
            print(f"   실행 범위: {start_index}-{end_index} ({end_index - start_index + 1}개)")
            if image_url:
                if os.path.exists(image_url):
                    print(f"   이미지: {os.path.basename(image_url)} (로컬)")
                else:
                    print(f"   이미지: URL")
                print("   모드: 이미지-to-비디오 (i2v)")
            else:
                print("   모드: 텍스트-to-비디오 (t2v)")
            
            # 선택된 프롬프트 미리보기
            print(f"\n📝 실행될 프롬프트 미리보기:")
            for i in range(start_index, min(start_index + 3, end_index + 1)):
                prompt = prompts[i-1]
                print(f"   {i:2d}. {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            
            if end_index - start_index + 1 > 3:
                print(f"   ... (총 {end_index - start_index + 1}개)")
            
            # 배치 처리 확인
            print()
            confirm = input("🚀 배치 생성을 시작할까요? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ 배치 작업이 취소되었습니다.")
                return
            
            # 배치 실행
            results = video_maker.create_video_batch(prompts, image_url, video_config, start_index, end_index)
            
            # 결과 저장
            timestamp = int(time.time())
            report_file = f"batch_report_{start_index}-{end_index}_{timestamp}.json"
            try:
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"\n📄 결과 리포트: {report_file}")
            except Exception as e:
                print(f"⚠️  리포트 저장 실패: {e}")
            
            return
        
        elif command == "--help":
            print("🎥 쉬운 동영상 생성기 - 명령어 도움말")
            print("=" * 50)
            print()
            print("사용법:")
            print("  python easy_video_maker.py                         # 일반 실행 (단일 동영상)")
            print("  python easy_video_maker.py --batch                 # 배치 실행 (전체)")
            print("  python easy_video_maker.py --batch <시작> <끝>     # 배치 실행 (범위 지정)")
            print("  python easy_video_maker.py --check <task_id>       # 작업 상태 확인")
            print("  python easy_video_maker.py --list [개수]           # 최근 작업 목록")
            print("  python easy_video_maker.py --help                  # 이 도움말")
            print()
            print("배치 모드:")
            print("  1. batch_prompts.txt 파일에 각 줄마다 프롬프트 작성")
            print("  2. --batch 옵션으로 실행 (범위 지정 가능)")
            print("  3. 부분적으로 동영상 생성 (예: 1-5번만)")
            print()
            print("예시:")
            print("  python easy_video_maker.py --batch              # 전체 실행")
            print("  python easy_video_maker.py --batch 1 5          # 1-5번만 실행")
            print("  python easy_video_maker.py --batch 10 15        # 10-15번만 실행")
            print("  python easy_video_maker.py --check cgt-2024****-**")
            print("  python easy_video_maker.py --list 20")
            return
        
        else:
            print("❌ 알 수 없는 명령어입니다.")
            print("💡 python easy_video_maker.py --help 를 실행해보세요.")
            return
    
    # 일반 실행 모드
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
    print("📂 설정을 준비하는 중...")
    
    prompt_text = read_prompt_file()
    if not prompt_text:
        print("\n💡 prompt.txt 파일을 확인하고 다시 실행해주세요.")
        input("아무 키나 눌러서 종료하세요...")
        return
    
    # config.txt에서 비디오 설정 읽기
    video_config = read_config_file()
    
    # 이미지 선택 (config 파일 우선, 없으면 인터랙티브)
    print()
    if video_config.get('image_file'):
        image_url = video_config['image_file']
        print(f"🖼️ 설정된 이미지 파일: {image_url}")
        if not os.path.exists(image_url):
            print(f"❌ 오류: 이미지 파일을 찾을 수 없습니다: {image_url}")
            print("💡 config.txt의 image_file 경로를 확인하거나 파일을 생성하세요")
            input("아무 키나 눌러서 종료하세요...")
            return
    else:
        print("🖼️ 이미지 선택:")
        image_url = select_image_from_folder()
    
    print("✅ 설정 파일을 모두 읽었습니다!")
    print()
    
    # 설정 내용 확인
    print("📋 확인된 설정:")
    print(f"   동영상 설명: {prompt_text[:60]}{'...' if len(prompt_text) > 60 else ''}")
    if image_url:
        if os.path.exists(image_url):
            print(f"   이미지 파일: {image_url}")
            print("   모드: 이미지-to-비디오 (i2v) - 로컬 파일")
        else:
            print(f"   이미지 주소: {image_url[:60]}{'...' if len(image_url) > 60 else ''}")
            print("   모드: 이미지-to-비디오 (i2v) - URL")
    else:
        print("   모드: 텍스트-to-비디오 (t2v)")
    
    # 비디오 설정 표시
    print("   비디오 설정:")
    print(f"     해상도: {video_config['resolution']}")
    
    # 화면비 표시 (i2v 제한사항 포함)
    display_ratio = video_config['ratio']
    if image_url and display_ratio not in ['adaptive', 'keep_ratio']:
        print(f"     화면비: {display_ratio} → adaptive (i2v 모드 제한)")
    else:
        print(f"     화면비: {display_ratio}")
    
    print(f"     길이: {video_config['duration']}초")
    print(f"     프레임율: {video_config['fps']}fps")
    if video_config.get('watermark'):
        print(f"     워터마크: 있음")
    if video_config.get('seed', -1) != -1:
        print(f"     시드: {video_config['seed']}")
    if video_config.get('camerafixed'):
        print(f"     카메라 고정: 예")
    if video_config.get('callback_url'):
        print(f"     콜백 URL: {video_config['callback_url']}")
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
        result_path = video_maker.create_video(prompt_text, image_url, video_config)
        
        if result_path:
            # 콜백 URL이 설정된 경우 task_id가 반환됨
            if video_config.get('callback_url'):
                print()
                print("📞 작업이 접수되었습니다!")
                print(f"📋 작업 ID: {result_path}")
                print()
                print("🔔 콜백 URL로 완료 알림이 전송됩니다.")
                print("💡 수동 확인하려면:")
                print(f"   python easy_video_maker.py --check {result_path}")
                print()
                print("🌐 웹훅 서버를 실행하려면:")
                print("   python webhook_server.py")
            else:
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
