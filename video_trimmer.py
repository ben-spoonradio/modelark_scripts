#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime

def get_video_files():
    """videos 폴더에서 동영상 파일 목록을 가져옵니다."""
    videos_dir = "videos"
    if not os.path.exists(videos_dir):
        print(f"Error: '{videos_dir}' 폴더가 존재하지 않습니다.")
        return []
    
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
    video_files = []
    
    for file in os.listdir(videos_dir):
        if file.lower().endswith(video_extensions):
            video_files.append(file)
    
    return sorted(video_files)

def format_time(seconds):
    """초를 HH:MM:SS 형태로 변환합니다."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def parse_time(time_str):
    """HH:MM:SS, MM:SS 또는 초 단위 문자열을 초로 변환합니다."""
    try:
        # 숫자만 입력된 경우 (초 단위)
        if ':' not in time_str:
            return float(time_str)
        
        # HH:MM:SS 또는 MM:SS 형태
        time_parts = time_str.split(':')
        if len(time_parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(float, time_parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(time_parts) == 2:  # MM:SS
            minutes, seconds = map(float, time_parts)
            return minutes * 60 + seconds
        else:
            raise ValueError("잘못된 시간 형식입니다.")
    except ValueError:
        raise ValueError("시간 형식이 올바르지 않습니다. (예: 120 또는 2:30 또는 1:02:30)")

def get_video_duration(video_path):
    """ffprobe를 사용하여 동영상의 길이를 가져옵니다."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return None

def trim_video(input_path, output_path, start_time, end_time):
    """ffmpeg을 사용하여 동영상을 자릅니다."""
    try:
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', format_time(start_time),
            '-to', format_time(end_time),
            '-c', 'copy',  # 빠른 복사를 위해 re-encoding 하지 않음
            '-avoid_negative_ts', 'make_zero',
            output_path, '-y'  # 기존 파일 덮어쓰기
        ]
        
        print(f"\n동영상 자르는 중...")
        print(f"명령어: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 성공적으로 저장되었습니다: {output_path}")
            return True
        else:
            print(f"❌ 오류가 발생했습니다:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("❌ ffmpeg이 설치되어 있지 않습니다. ffmpeg을 먼저 설치해주세요.")
        return False

def main():
    print("=== 동영상 자르기 도구 ===")
    
    # 동영상 파일 목록 가져오기
    video_files = get_video_files()
    
    if not video_files:
        print("videos 폴더에 동영상 파일이 없습니다.")
        return
    
    # 동영상 파일 선택
    print("\n사용 가능한 동영상 파일:")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {file}")
    
    try:
        choice = int(input(f"\n동영상을 선택하세요 (1-{len(video_files)}): ")) - 1
        if choice < 0 or choice >= len(video_files):
            print("잘못된 선택입니다.")
            return
    except ValueError:
        print("숫자를 입력해주세요.")
        return
    
    selected_file = video_files[choice]
    input_path = os.path.join("videos", selected_file)
    
    # 동영상 정보 가져오기
    duration = get_video_duration(input_path)
    if duration:
        print(f"\n선택된 파일: {selected_file}")
        print(f"동영상 길이: {format_time(duration)} ({duration:.1f}초)")
    else:
        print(f"\n선택된 파일: {selected_file}")
        print("동영상 길이를 가져올 수 없습니다.")
    
    # 시작 시간 입력
    print("\n시작 시간을 입력하세요 (예: 30, 1:30, 0:01:30)")
    try:
        start_str = input("시작 시간: ").strip()
        start_time = parse_time(start_str)
        
        if duration and start_time >= duration:
            print(f"❌ 시작 시간이 동영상 길이({format_time(duration)})보다 큽니다.")
            return
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # 종료 시간 입력
    print("종료 시간을 입력하세요 (예: 90, 2:30, 0:02:30)")
    try:
        end_str = input("종료 시간: ").strip()
        end_time = parse_time(end_str)
        
        if end_time <= start_time:
            print("❌ 종료 시간이 시작 시간보다 작거나 같습니다.")
            return
        
        if duration and end_time > duration:
            print(f"❌ 종료 시간이 동영상 길이({format_time(duration)})보다 큽니다.")
            return
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # 출력 파일명 생성
    base_name = os.path.splitext(selected_file)[0]
    extension = os.path.splitext(selected_file)[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{base_name}_trimmed_{timestamp}{extension}"
    output_path = os.path.join("videos", output_filename)
    
    # 요약 정보 출력
    print(f"\n=== 작업 요약 ===")
    print(f"입력 파일: {selected_file}")
    print(f"시작 시간: {format_time(start_time)}")
    print(f"종료 시간: {format_time(end_time)}")
    print(f"잘린 길이: {format_time(end_time - start_time)}")
    print(f"출력 파일: {output_filename}")
    
    # 확인
    confirm = input("\n작업을 진행하시겠습니까? (y/N): ").strip().lower()
    if confirm != 'y':
        print("작업이 취소되었습니다.")
        return
    
    # 동영상 자르기 실행
    success = trim_video(input_path, output_path, start_time, end_time)
    
    if success:
        print(f"\n🎉 작업 완료!")
        print(f"저장 위치: {output_path}")
    else:
        print(f"\n💥 작업 실패!")

if __name__ == "__main__":
    main()