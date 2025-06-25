#!/usr/bin/env python3
"""
🖼️ 이미지 도우미 - Base64 인코딩 및 검증 도구
=============================================

이 도구는 로컬 이미지 파일을 동영상 생성에 사용할 수 있도록
Base64로 인코딩하고 API 요구사항에 맞는지 검증합니다.

사용법:
1. python image_helper.py check <이미지파일>     # 이미지 검증
2. python image_helper.py encode <이미지파일>    # Base64 인코딩
3. python image_helper.py auto <이미지파일>      # 자동으로 config.txt 업데이트
"""

import os
import sys
import base64
import mimetypes

def check_image(image_path: str) -> bool:
    """이미지 파일 검증"""
    print(f"🔍 이미지 검증: {image_path}")
    print("=" * 50)
    
    # 파일 존재 확인
    if not os.path.exists(image_path):
        print("❌ 파일을 찾을 수 없습니다.")
        return False
    
    # 파일 크기 확인
    file_size = os.path.getsize(image_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"📏 파일 크기: {file_size_mb:.2f} MB")
    
    if file_size > 10 * 1024 * 1024:
        print("❌ 파일이 너무 큽니다 (최대 10MB)")
        return False
    else:
        print("✅ 파일 크기 적합")
    
    # MIME 타입 확인
    mime_type, _ = mimetypes.guess_type(image_path)
    print(f"🔖 파일 형식: {mime_type}")
    
    supported_formats = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff', 'image/gif']
    if mime_type not in supported_formats:
        print("❌ 지원되지 않는 형식")
        print("💡 지원 형식: JPEG, PNG, WEBP, BMP, TIFF, GIF")
        return False
    else:
        print("✅ 지원되는 형식")
    
    # 이미지 크기 검증 (PIL이 있는 경우)
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            width, height = img.size
            aspect_ratio = width / height
            
            print(f"📐 이미지 크기: {width} x {height}")
            print(f"📊 화면비: {aspect_ratio:.2f}")
            
            # 화면비 확인 (0.4 ~ 2.5)
            if aspect_ratio < 0.4 or aspect_ratio > 2.5:
                print("❌ 화면비가 범위를 벗어남 (허용: 0.4 ~ 2.5)")
                return False
            else:
                print("✅ 화면비 적합")
            
            # 픽셀 크기 확인
            min_side = min(width, height)
            max_side = max(width, height)
            
            if min_side < 300:
                print(f"❌ 이미지가 너무 작음 (최소: 300px, 현재: {min_side}px)")
                return False
            
            if max_side > 6000:
                print(f"❌ 이미지가 너무 큼 (최대: 6000px, 현재: {max_side}px)")
                return False
            
            print("✅ 이미지 크기 적합")
            
    except ImportError:
        print("⚠️  PIL 라이브러리가 없어서 크기 검증을 건너뜁니다.")
        print("💡 정확한 검증을 위해 'pip install Pillow'를 실행하세요.")
    except Exception as e:
        print(f"⚠️  이미지 크기 검증 실패: {e}")
    
    print("✅ 모든 검증 통과!")
    return True

def encode_image(image_path: str) -> str:
    """이미지를 Base64로 인코딩"""
    print(f"🔄 Base64 인코딩: {image_path}")
    
    if not check_image(image_path):
        return None
    
    print("📦 인코딩 중...")
    
    try:
        mime_type, _ = mimetypes.guess_type(image_path)
        
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        data_url = f"data:{mime_type};base64,{encoded_string}"
        
        print("✅ 인코딩 완료!")
        print(f"📊 Base64 크기: {len(data_url):,} 문자")
        print()
        print("📋 결과:")
        print(data_url[:100] + "..." if len(data_url) > 100 else data_url)
        
        return data_url
        
    except Exception as e:
        print(f"❌ 인코딩 실패: {e}")
        return None

def auto_update_config(image_path: str) -> bool:
    """자동으로 config.txt 업데이트"""
    print(f"🔧 config.txt 자동 업데이트: {image_path}")
    
    if not check_image(image_path):
        return False
    
    # 절대 경로로 변환
    abs_path = os.path.abspath(image_path)
    print(f"📁 절대 경로: {abs_path}")
    
    try:
        # config.txt 읽기
        config_lines = []
        if os.path.exists("config.txt"):
            with open("config.txt", "r", encoding="utf-8") as f:
                config_lines = f.readlines()
        
        # 기존 image_url/image_file 주석 처리
        updated_lines = []
        found_image_setting = False
        
        for line in config_lines:
            stripped = line.strip()
            if stripped.startswith("image_url=") or stripped.startswith("image_file="):
                updated_lines.append(f"# {line}")  # 주석 처리
                found_image_setting = True
            else:
                updated_lines.append(line)
        
        # 새로운 image_file 설정 추가
        if found_image_setting:
            # 기존 이미지 설정 뒤에 추가
            for i, line in enumerate(updated_lines):
                if line.strip().startswith("# image_"):
                    updated_lines.insert(i + 1, f"image_file={abs_path}\n")
                    break
        else:
            # 파일 시작 부분에 추가
            updated_lines.insert(0, f"image_file={abs_path}\n")
            updated_lines.insert(1, "\n")
        
        # config.txt 저장
        with open("config.txt", "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
        
        print("✅ config.txt 업데이트 완료!")
        print(f"📝 설정: image_file={abs_path}")
        print()
        print("💡 이제 동영상 생성기를 실행하세요:")
        print("   python easy_video_maker.py")
        
        return True
        
    except Exception as e:
        print(f"❌ config.txt 업데이트 실패: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("🖼️ 이미지 도우미")
        print("=" * 30)
        print()
        print("사용법:")
        print("  python image_helper.py check <이미지파일>   # 이미지 검증")
        print("  python image_helper.py encode <이미지파일>  # Base64 인코딩")
        print("  python image_helper.py auto <이미지파일>    # config.txt 자동 업데이트")
        print()
        print("예시:")
        print("  python image_helper.py check ./my_image.jpg")
        print("  python image_helper.py auto ~/Desktop/photo.png")
        return
    
    command = sys.argv[1]
    image_path = sys.argv[2]
    
    if command == "check":
        check_image(image_path)
    elif command == "encode":
        encode_image(image_path)
    elif command == "auto":
        auto_update_config(image_path)
    else:
        print("❌ 알 수 없는 명령어입니다.")
        print("💡 사용 가능한 명령어: check, encode, auto")

if __name__ == "__main__":
    main()