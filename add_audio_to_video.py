#!/usr/bin/env python3
"""
🎵 동영상에 음성 추가하기 (Add Audio to Video)
=================================================

이 프로그램은 기존 동영상에 음성 파일을 추가하여 새로운 동영상을 만들어줍니다.

사용 방법:
1. videos/ 폴더에 동영상 파일을 넣으세요
2. audio/ 폴더에 음성 파일을 넣으세요
3. 이 프로그램을 실행하세요

지원 형식:
- 동영상: MP4, AVI, MOV, MKV
- 음성: MP3, WAV, AAC, M4A, OGG
"""

import os
import sys
import subprocess
import shutil
import time
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
import tempfile
import re

# Rich Console 초기화
console = Console()

class AudioVideoMerger:
    """동영상과 음성 파일을 합치는 클래스"""
    
    def __init__(self):
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        self.audio_extensions = {'.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac', '.wma'}
        self.videos_dir = "videos"
        self.audio_dir = "audio"
        self.output_dir = "videos_with_audio"
        
        # 필요한 폴더 생성
        self.create_directories()
        
        # Whisper 설치 확인
        self.whisper_available = self.check_whisper()
    
    def create_directories(self):
        """필요한 폴더들 생성"""
        for directory in [self.videos_dir, self.audio_dir, self.output_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                console.print(f"[bold blue]📁 {directory} 폴더를 생성했습니다.[/bold blue]")
    
    def check_ffmpeg(self) -> bool:
        """ffmpeg 설치 확인"""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_whisper(self) -> bool:
        """Whisper 설치 확인"""
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    def show_ffmpeg_install_guide(self):
        """ffmpeg 설치 안내"""
        console.print(Panel(
            "[bold red]❌ ffmpeg가 설치되지 않았습니다.[/bold red]\n\n"
            "[bold yellow]설치 방법:[/bold yellow]\n"
            "• [cyan]macOS:[/cyan] brew install ffmpeg\n"
            "• [cyan]Ubuntu/Debian:[/cyan] sudo apt install ffmpeg\n"
            "• [cyan]Windows:[/cyan] https://ffmpeg.org/download.html\n\n"
            "[bold yellow]💡 ffmpeg 설치 후 다시 실행해주세요.[/bold yellow]",
            title="[bold red]ffmpeg 필요[/bold red]",
            border_style="red"
        ))
    
    def show_whisper_install_guide(self):
        """Whisper 설치 안내"""
        console.print(Panel(
            "[bold yellow]🎤 자막 생성 기능을 사용하려면 Whisper 설치가 필요합니다.[/bold yellow]\n\n"
            "[bold yellow]설치 방법:[/bold yellow]\n"
            "• pip install openai-whisper\n\n"
            "[bold cyan]💡 Whisper 없이도 기본 음성 합치기 기능은 사용 가능합니다.[/bold cyan]",
            title="[bold yellow]Whisper 권장[/bold yellow]",
            border_style="yellow"
        ))
    
    def get_video_files(self) -> list:
        """videos 폴더에서 동영상 파일 목록 가져오기"""
        video_files = []
        if os.path.exists(self.videos_dir):
            for file in os.listdir(self.videos_dir):
                if Path(file).suffix.lower() in self.video_extensions:
                    video_files.append(file)
        return sorted(video_files)
    
    def get_audio_files(self) -> list:
        """audio 폴더에서 음성 파일 목록 가져오기"""
        audio_files = []
        if os.path.exists(self.audio_dir):
            for file in os.listdir(self.audio_dir):
                if Path(file).suffix.lower() in self.audio_extensions:
                    audio_files.append(file)
        return sorted(audio_files)
    
    def get_subtitle_files(self) -> list:
        """output 폴더에서 자막 파일 목록 가져오기"""
        subtitle_files = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if Path(file).suffix.lower() in {'.srt', '.ass', '.ssa', '.vtt'}:
                    subtitle_files.append(os.path.join(self.output_dir, file))
        return sorted(subtitle_files, key=lambda x: os.path.getmtime(x), reverse=True)  # 최신 파일 먼저
    
    def select_video_file(self) -> str:
        """동영상 파일 선택"""
        video_files = self.get_video_files()
        
        if not video_files:
            console.print(Panel(
                f"[bold red]❌ {self.videos_dir} 폴더에 동영상 파일이 없습니다.[/bold red]\n\n"
                "[bold yellow]💡 지원 형식:[/bold yellow] MP4, AVI, MOV, MKV, WMV, FLV, WEBM",
                title="[bold red]동영상 파일 없음[/bold red]",
                border_style="red"
            ))
            return None
        
        # 동영상 파일 목록 표시
        video_table = Table(title="[bold blue]📹 동영상 파일 선택[/bold blue]", show_header=True, header_style="bold magenta")
        video_table.add_column("번호", style="cyan", width=6)
        video_table.add_column("파일명", style="white", width=40)
        video_table.add_column("크기", style="green", width=10)
        
        for i, file in enumerate(video_files, 1):
            file_path = os.path.join(self.videos_dir, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            video_table.add_row(str(i), file, f"{file_size:.1f}MB")
        
        console.print(video_table)
        console.print()
        
        # 사용자 선택
        while True:
            try:
                choice = Prompt.ask("동영상 파일을 선택하세요", choices=[str(i) for i in range(1, len(video_files) + 1)])
                choice_num = int(choice)
                selected_file = video_files[choice_num - 1]
                console.print(f"[bold green]✅ 선택된 동영상:[/bold green] {selected_file}")
                return os.path.join(self.videos_dir, selected_file)
            except (ValueError, IndexError):
                console.print("[bold red]❌ 올바른 번호를 입력하세요.[/bold red]")
            except KeyboardInterrupt:
                console.print("\n[bold red]❌ 사용자가 취소했습니다.[/bold red]")
                return None
    
    def select_audio_file(self) -> str:
        """음성 파일 선택"""
        audio_files = self.get_audio_files()
        
        if not audio_files:
            console.print(Panel(
                f"[bold red]❌ {self.audio_dir} 폴더에 음성 파일이 없습니다.[/bold red]\n\n"
                "[bold yellow]💡 지원 형식:[/bold yellow] MP3, WAV, AAC, M4A, OGG, FLAC, WMA",
                title="[bold red]음성 파일 없음[/bold red]",
                border_style="red"
            ))
            return None
        
        # 음성 파일 목록 표시
        audio_table = Table(title="[bold blue]🎵 음성 파일 선택[/bold blue]", show_header=True, header_style="bold magenta")
        audio_table.add_column("번호", style="cyan", width=6)
        audio_table.add_column("파일명", style="white", width=40)
        audio_table.add_column("크기", style="green", width=10)
        
        for i, file in enumerate(audio_files, 1):
            file_path = os.path.join(self.audio_dir, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            audio_table.add_row(str(i), file, f"{file_size:.1f}MB")
        
        console.print(audio_table)
        console.print()
        
        # 사용자 선택
        while True:
            try:
                choice = Prompt.ask("음성 파일을 선택하세요", choices=[str(i) for i in range(1, len(audio_files) + 1)])
                choice_num = int(choice)
                selected_file = audio_files[choice_num - 1]
                console.print(f"[bold green]✅ 선택된 음성:[/bold green] {selected_file}")
                return os.path.join(self.audio_dir, selected_file)
            except (ValueError, IndexError):
                console.print("[bold red]❌ 올바른 번호를 입력하세요.[/bold red]")
            except KeyboardInterrupt:
                console.print("\n[bold red]❌ 사용자가 취소했습니다.[/bold red]")
                return None
    
    def get_media_duration(self, file_path: str) -> float:
        """미디어 파일의 길이 가져오기 (초 단위)"""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json", "-show_entries",
                "format=duration", file_path
            ], capture_output=True, text=True, check=True)
            
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except:
            return 0.0
    
    def transcribe_audio(self, audio_path: str) -> dict:
        """오디오 파일에서 텍스트 추출"""
        if not self.whisper_available:
            console.print("[bold red]❌ Whisper가 설치되지 않아 자막 생성을 건너뜁니다.[/bold red]")
            return None
            
        try:
            import whisper
            
            console.print("[bold yellow]🎤 음성 인식 시작...[/bold yellow]")
            
            # Whisper 모델 로드 (base 모델 사용)
            model = whisper.load_model("base")
            
            # 음성 인식 수행
            result = model.transcribe(audio_path, language="ko")
            
            console.print(f"[bold green]✅ 음성 인식 완료: {len(result['segments'])}개 세그먼트[/bold green]")
            
            return result
            
        except Exception as e:
            console.print(f"[bold red]❌ 음성 인식 오류: {str(e)}[/bold red]")
            return None
    
    def create_subtitle_file(self, transcription: dict, subtitle_path: str) -> bool:
        """자막 파일 생성 (SRT 형식)"""
        try:
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                
                # 제목은 동영상에 직접 추가되므로 자막 파일에서는 제외
                
                # 음성 인식 자막 추가
                if transcription and transcription.get('segments'):
                    for segment in transcription['segments']:
                        start_time = self.format_time(segment['start'])
                        end_time = self.format_time(segment['end'])
                        text = segment['text'].strip()
                        
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
                        subtitle_index += 1
                
            console.print(f"[bold green]✅ 자막 파일 생성: {subtitle_path}[/bold green]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]❌ 자막 파일 생성 오류: {str(e)}[/bold red]")
            return False
    
    def format_time(self, seconds: float) -> str:
        """시간을 SRT 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')
    
    def add_subtitles_to_video(self, video_path: str, subtitle_path: str, output_path: str) -> bool:
        """동영상에 자막 추가"""
        try:
            # 경로에서 특수 문자 이스케이프 처리
            escaped_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
            
            # 자막 필터 명령어 구성
            subtitle_filter = f"subtitles='{escaped_subtitle_path}':force_style='FontName=NanumGothic,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&HFF000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=20'"
            
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vf", subtitle_filter,
                "-c:v", "libx264",  # 비디오 재인코딩 필요
                "-preset", "fast",
                "-c:a", "copy",
                "-y", output_path
            ]
            
            console.print("[bold yellow]🎬 자막 추가 중...[/bold yellow]")
            console.print(f"[dim]자막 파일: {subtitle_path}[/dim]")
            
            # Progress 표시와 함께 실행
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("자막 합성 중...", total=100)
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 진행률 업데이트
                for i in range(0, 101, 10):
                    if process.poll() is not None:
                        break
                    progress.update(task, completed=i)
                    time.sleep(0.5)
                
                stdout, stderr = process.communicate()
                progress.update(task, completed=100)
                
                if process.returncode == 0:
                    console.print("[bold green]✅ 자막 추가 완료[/bold green]")
                    return True
                else:
                    console.print(f"[bold red]❌ 자막 추가 실패:[/bold red]\n{stderr}")
                    return False
                
        except Exception as e:
            console.print(f"[bold red]❌ 자막 추가 오류: {str(e)}[/bold red]")
            return False
    
    def show_subtitle_preview(self, subtitle_path: str) -> None:
        """자막 파일 미리보기"""
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 처음 5개 자막만 표시
            lines = content.strip().split('\n\n')
            preview_lines = lines[:5]
            
            console.print(Panel(
                '\n\n'.join(preview_lines) + 
                (f"\n\n[dim]... 외 {len(lines)-5}개 자막[/dim]" if len(lines) > 5 else ""),
                title=f"[bold blue]📝 자막 미리보기 (총 {len(lines)}개)[/bold blue]",
                border_style="blue"
            ))
        except Exception as e:
            console.print(f"[bold red]❌ 자막 미리보기 오류: {str(e)}[/bold red]")
    
    def edit_subtitle_file(self, subtitle_path: str) -> bool:
        """자막 파일 간단 편집"""
        try:
            # 현재 자막 읽기
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            console.print("\n[bold yellow]✏️ 자막 편집 옵션:[/bold yellow]")
            console.print("1. 전체 자막에서 특정 단어 찾기/바꾸기")
            console.print("2. 자막 시간 전체 조정 (앞당기기/늦추기)")
            console.print("3. 편집 건너뛰기")
            
            choice = Prompt.ask("선택", choices=["1", "2", "3"], default="3")
            
            if choice == "1":
                # 찾기/바꾸기
                find_text = Prompt.ask("\n찾을 텍스트")
                if find_text in content:
                    replace_text = Prompt.ask("바꿀 텍스트")
                    content = content.replace(find_text, replace_text)
                    
                    with open(subtitle_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    console.print(f"[bold green]✅ '{find_text}' → '{replace_text}' 변경 완료[/bold green]")
                    return True
                else:
                    console.print(f"[bold yellow]⚠️ '{find_text}'를 찾을 수 없습니다.[/bold yellow]")
                    
            elif choice == "2":
                # 시간 조정
                offset = Prompt.ask("\n시간 조정 (초 단위, 음수는 앞당기기)", default="0")
                try:
                    offset_seconds = float(offset)
                    if offset_seconds != 0:
                        # SRT 시간 형식 파싱 및 조정
                        import re
                        
                        def adjust_time(match):
                            time_str = match.group(0)
                            # HH:MM:SS,mmm 형식 파싱
                            parts = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_str)
                            if parts:
                                h, m, s, ms = map(int, parts.groups())
                                total_seconds = h * 3600 + m * 60 + s + ms / 1000
                                total_seconds += offset_seconds
                                
                                # 음수 방지
                                if total_seconds < 0:
                                    total_seconds = 0
                                
                                # 다시 포맷팅
                                h = int(total_seconds // 3600)
                                m = int((total_seconds % 3600) // 60)
                                s = int(total_seconds % 60)
                                ms = int((total_seconds % 1) * 1000)
                                
                                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                            return time_str
                        
                        # 모든 시간 조정
                        content = re.sub(r'\d{2}:\d{2}:\d{2},\d{3}', adjust_time, content)
                        
                        with open(subtitle_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        console.print(f"[bold green]✅ 자막 시간 {offset_seconds:+.1f}초 조정 완료[/bold green]")
                        return True
                except ValueError:
                    console.print("[bold red]❌ 올바른 숫자를 입력하세요.[/bold red]")
            
            return False
            
        except Exception as e:
            console.print(f"[bold red]❌ 자막 편집 오류: {str(e)}[/bold red]")
            return False
    
    def select_subtitle_file(self, subtitle_files: list) -> str:
        """자막 파일 선택"""
        if not subtitle_files:
            console.print("[bold red]❌ 자막 파일이 없습니다.[/bold red]")
            return None
        
        # 자막 파일 목록 표시
        subtitle_table = Table(title="[bold blue]📝 자막 파일 선택[/bold blue]", show_header=True, header_style="bold magenta")
        subtitle_table.add_column("번호", style="cyan", width=6)
        subtitle_table.add_column("파일명", style="white", width=50)
        subtitle_table.add_column("수정시간", style="green", width=20)
        subtitle_table.add_column("크기", style="yellow", width=10)
        
        for i, file_path in enumerate(subtitle_files[:10], 1):  # 최대 10개만 표시
            file_name = os.path.basename(file_path)
            mod_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(file_path)))
            file_size = os.path.getsize(file_path) / 1024  # KB
            subtitle_table.add_row(str(i), file_name, mod_time, f"{file_size:.1f}KB")
        
        console.print(subtitle_table)
        console.print()
        
        # 사용자 선택
        while True:
            try:
                max_choice = min(10, len(subtitle_files))
                choice = Prompt.ask("자막 파일을 선택하세요", choices=[str(i) for i in range(1, max_choice + 1)])
                choice_num = int(choice)
                selected_file = subtitle_files[choice_num - 1]
                return selected_file
            except (ValueError, IndexError):
                console.print("[bold red]❌ 올바른 번호를 입력하세요.[/bold red]")
            except KeyboardInterrupt:
                console.print("\n[bold red]❌ 사용자가 취소했습니다.[/bold red]")
                return None
    
    def merge_audio_video(self, video_path: str, audio_path: str, output_path: str, audio_mode: str = "replace", 
                          music_title: str = None, artist_name: str = None, title_font_size: int = 64, artist_font_size: int = 36) -> bool:
        """동영상과 음성 파일 합치기"""
        try:
            # 파일 길이 확인
            video_duration = self.get_media_duration(video_path)
            audio_duration = self.get_media_duration(audio_path)
            
            console.print(f"[bold cyan]📹 동영상 길이:[/bold cyan] {video_duration:.1f}초")
            console.print(f"[bold cyan]🎵 음성 길이:[/bold cyan] {audio_duration:.1f}초")
            
            # ffmpeg 명령어 구성
            if music_title:
                # 제목이 있는 경우 drawtext 필터 추가
                # 제목 텍스트 준비
                title_text = music_title.replace("'", "\\'").replace(":", "\\:")
                artist_text = artist_name.replace("'", "\\'").replace(":", "\\:") if artist_name else ""
                
                # drawtext 필터 구성 - 한글 지원 폰트 사용
                # macOS 한글 폰트 경로들
                korean_fonts = [
                    "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # Apple SD Gothic Neo
                    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",  # Apple Gothic
                    "/Library/Fonts/NanumGothic.ttf",  # 나눔고딕 (설치된 경우)
                    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # Arial Unicode
                ]
                
                # 사용 가능한 첫 번째 폰트 찾기
                font_path = None
                for font in korean_fonts:
                    if os.path.exists(font):
                        font_path = font
                        break
                
                if not font_path:
                    console.print("[bold yellow]⚠️ 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.[/bold yellow]")
                    font_path = "/System/Library/Fonts/Helvetica.ttc"
                
                title_filter = (
                    f"drawtext=text='{title_text}':fontfile='{font_path}':fontsize={title_font_size}:"
                    f"fontcolor=white:borderw=4:bordercolor=black:x=(w-text_w)/2:y=(h/2-text_h)-30:"
                    f"enable='between(t,0.5,5.5)':alpha='if(lt(t,1),t-0.5,if(gt(t,5),1-(t-5)/0.5,1))'"
                )
                
                if artist_text:
                    # 아티스트 이름 추가
                    artist_filter = (
                        f"drawtext=text='{artist_text}':fontfile='{font_path}':fontsize={artist_font_size}:"
                        f"fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=(h/2)+30:"
                        f"enable='between(t,0.5,5.5)':alpha='if(lt(t,1),t-0.5,if(gt(t,5),1-(t-5)/0.5,1))'"
                    )
                    video_filter = f"{title_filter},{artist_filter}"
                else:
                    video_filter = title_filter
                
                if audio_mode == "replace":
                    # 기존 음성 대체 + 제목
                    cmd = [
                        "ffmpeg", "-i", video_path, "-i", audio_path,
                        "-filter_complex", f"[0:v]{video_filter}[v]",
                        "-map", "[v]", "-map", "1:a:0",
                        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
                        "-shortest", "-y", output_path
                    ]
                else:  # mix
                    # 기존 음성과 믹싱 + 제목
                    cmd = [
                        "ffmpeg", "-i", video_path, "-i", audio_path,
                        "-filter_complex", 
                        f"[0:v]{video_filter}[v];[0:a][1:a]amix=inputs=2:duration=shortest[a]",
                        "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
                        "-y", output_path
                    ]
            else:
                # 제목 없는 경우 (기존 코드)
                if audio_mode == "replace":
                    # 기존 음성 대체
                    cmd = [
                        "ffmpeg", "-i", video_path, "-i", audio_path,
                        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
                        "-shortest", "-y", output_path
                    ]
                else:  # mix
                    # 기존 음성과 믹싱
                    cmd = [
                        "ffmpeg", "-i", video_path, "-i", audio_path,
                        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=shortest[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                        "-y", output_path
                    ]
            
            console.print(f"[bold yellow]🔄 음성 합치기 시작...[/bold yellow]")
            if music_title:
                console.print(f"[bold cyan]🎵 제목 추가: {music_title}{' - ' + artist_name if artist_name else ''}[/bold cyan]")
            
            # 진행률 표시와 함께 ffmpeg 실행
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("음성 합치는 중...", total=100)
                
                # ffmpeg 실행
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 진행률 업데이트 (간단한 시뮬레이션)
                import time
                for i in range(0, 101, 5):
                    if process.poll() is not None:
                        break
                    progress.update(task, completed=i)
                    time.sleep(0.5)
                
                # 프로세스 완료 대기
                stdout, stderr = process.communicate()
                progress.update(task, completed=100)
                
                if process.returncode == 0:
                    console.print(f"[bold green]✅ 성공적으로 완료되었습니다![/bold green]")
                    console.print(f"[bold cyan]📁 저장 위치:[/bold cyan] {output_path}")
                    return True
                else:
                    console.print(f"[bold red]❌ 오류 발생:[/bold red] {stderr}")
                    return False
                    
        except Exception as e:
            console.print(f"[bold red]❌ 예외 발생:[/bold red] {str(e)}")
            return False
    
    def run(self):
        """메인 실행 함수"""
        console.print(Panel(
            "[bold cyan]🎵 동영상에 음성 추가하기[/bold cyan]\n\n"
            "[bold yellow]기능:[/bold yellow]\n"
            "• 동영상 파일에 음성 파일 추가\n"
            "• 기존 음성 대체 또는 믹싱\n"
            "• 다양한 형식 지원\n"
            "• 자동 길이 조정",
            title="[bold blue]Audio Video Merger[/bold blue]",
            border_style="blue"
        ))
        
        # ffmpeg 확인
        if not self.check_ffmpeg():
            self.show_ffmpeg_install_guide()
            return
        
        # 설정 파일 링크 표시
        self.show_folder_links()
        
        # 동영상 파일 선택
        video_path = self.select_video_file()
        if not video_path:
            return
        
        # 음성 파일 선택
        audio_path = self.select_audio_file()
        if not audio_path:
            return
        
        # 음성 모드 선택
        console.print("\n[bold yellow]🎛️ 음성 처리 모드 선택:[/bold yellow]")
        audio_mode = Prompt.ask(
            "음성 처리 방식을 선택하세요",
            choices=["replace", "mix"],
            default="replace"
        )
        
        if audio_mode == "replace":
            console.print("[bold cyan]🔄 기존 음성을 새 음성으로 대체합니다.[/bold cyan]")
        else:
            console.print("[bold cyan]🔄 기존 음성과 새 음성을 믹싱합니다.[/bold cyan]")
        
        # 자막 생성 옵션
        add_subtitles = False
        music_title = None
        artist_name = None
        title_font_size = 64
        artist_font_size = 36
        
        if self.whisper_available:
            add_subtitles = Confirm.ask("\n[bold yellow]🎤 음성에서 자막을 생성하시겠습니까?[/bold yellow]", default=False)
            
            # 뮤직비디오 스타일 제목 추가 옵션 (자막과 별개로 물어봄)
            if Confirm.ask("\n[bold yellow]🎵 뮤직비디오 스타일 제목을 추가하시겠습니까?[/bold yellow]", default=False):
                music_title = Prompt.ask("[bold cyan]노래 제목[/bold cyan]")
                artist_name = Prompt.ask("[bold cyan]아티스트 이름 (선택사항, Enter로 건너뛰기)[/bold cyan]", default="")
                
                # 폰트 크기 옵션
                console.print("\n[bold yellow]📏 제목 크기 선택:[/bold yellow]")
                console.print("1. 작게 (48pt)")
                console.print("2. 보통 (64pt) [기본값]")
                console.print("3. 크게 (80pt)")
                console.print("4. 매우 크게 (96pt)")
                console.print("5. 사용자 지정")
                
                size_choice = Prompt.ask("선택", choices=["1", "2", "3", "4", "5"], default="2")
                
                if size_choice == "1":
                    title_font_size = 48
                    artist_font_size = 28
                elif size_choice == "2":
                    title_font_size = 64
                    artist_font_size = 36
                elif size_choice == "3":
                    title_font_size = 80
                    artist_font_size = 44
                elif size_choice == "4":
                    title_font_size = 96
                    artist_font_size = 52
                else:  # 사용자 지정
                    title_font_size = int(Prompt.ask("[bold cyan]제목 폰트 크기 (픽셀)[/bold cyan]", default="64"))
                    artist_font_size = int(Prompt.ask("[bold cyan]아티스트 폰트 크기 (픽셀)[/bold cyan]", default="36"))
        else:
            self.show_whisper_install_guide()
        
        # 출력 파일명 생성
        video_name = Path(video_path).stem
        audio_name = Path(audio_path).stem
        timestamp = int(time.time())
        output_filename = f"{video_name}_with_{audio_name}_{timestamp}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # 최종 확인
        if not Confirm.ask(f"\n[bold yellow]동영상과 음성을 합치시겠습니까?[/bold yellow]"):
            console.print("[bold red]❌ 작업이 취소되었습니다.[/bold red]")
            return
        
        # 합치기 실행
        if music_title:
            success = self.merge_audio_video(video_path, audio_path, output_path, audio_mode, 
                                           music_title, artist_name, title_font_size, artist_font_size)
        else:
            success = self.merge_audio_video(video_path, audio_path, output_path, audio_mode)
        
        # 자막 처리
        subtitle_path = None
        final_output_path = output_path
        
        if success and add_subtitles:
            # 음성 인식 및 자막 생성
            transcription = self.transcribe_audio(audio_path)
            
            if transcription:
                # 자막 파일 생성
                subtitle_filename = f"{video_name}_with_{audio_name}_{timestamp}.srt"
                subtitle_path = os.path.join(self.output_dir, subtitle_filename)
                
                if self.create_subtitle_file(transcription, subtitle_path):
                    # 자막 미리보기 표시
                    self.show_subtitle_preview(subtitle_path)
                    
                    # 자막 파일 경로 안내
                    console.print(f"\n[bold cyan]📁 자막 파일 위치:[/bold cyan] {subtitle_path}")
                    console.print("[dim]자막 파일을 외부 편집기로 수정할 수 있습니다.[/dim]\n")
                    
                    # 자막 편집 여부 확인
                    if Confirm.ask("[bold yellow]자막을 편집하시겠습니까?[/bold yellow]", default=False):
                        self.edit_subtitle_file(subtitle_path)
                        # 편집 후 다시 미리보기
                        console.print("\n[bold yellow]📝 편집된 자막:[/bold yellow]")
                        self.show_subtitle_preview(subtitle_path)
                    
                    # 외부에서 편집한 자막 파일 사용 옵션
                    if Confirm.ask("\n[bold yellow]외부에서 편집한 자막 파일을 사용하시겠습니까?[/bold yellow]", default=False):
                        # 기존 자막 파일 목록 표시
                        subtitle_files = self.get_subtitle_files()
                        if subtitle_files:
                            selected_subtitle = self.select_subtitle_file(subtitle_files)
                            if selected_subtitle:
                                subtitle_path = selected_subtitle
                                console.print(f"[bold green]✅ 선택된 자막 파일: {os.path.basename(subtitle_path)}[/bold green]")
                                self.show_subtitle_preview(subtitle_path)
                    
                    # 자막 적용 여부 최종 확인
                    if Confirm.ask("\n[bold yellow]이 자막을 동영상에 적용하시겠습니까?[/bold yellow]", default=True):
                        # 자막이 포함된 최종 동영상 생성
                        final_output_filename = f"{video_name}_with_{audio_name}_subtitled_{timestamp}.mp4"
                        final_output_path = os.path.join(self.output_dir, final_output_filename)
                        
                        if self.add_subtitles_to_video(output_path, subtitle_path, final_output_path):
                            # 임시 파일 삭제 (자막 없는 버전)
                            os.remove(output_path)
                            success = True
                        else:
                            # 자막 추가 실패시 기본 버전 유지
                            final_output_path = output_path
                    else:
                        console.print("[bold cyan]자막 적용을 건너뛰었습니다. 자막 파일은 별도로 저장되었습니다.[/bold cyan]")
                        final_output_path = output_path
        
        if success:
            # 결과 표시
            file_size = os.path.getsize(final_output_path) / (1024 * 1024)  # MB
            final_filename = os.path.basename(final_output_path)
            
            result_text = f"[bold green]✅ 성공적으로 완료되었습니다![/bold green]\n\n"
            result_text += f"[cyan]출력 파일:[/cyan] {final_filename}\n"
            result_text += f"[cyan]파일 크기:[/cyan] {file_size:.1f}MB\n"
            result_text += f"[cyan]저장 위치:[/cyan] {final_output_path}\n"
            
            if subtitle_path and os.path.exists(subtitle_path):
                result_text += f"[cyan]자막 파일:[/cyan] {os.path.basename(subtitle_path)}\n"
            
            console.print(Panel(
                result_text,
                title="[bold green]완료[/bold green]",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[bold red]❌ 음성 합치기에 실패했습니다.[/bold red]\n\n"
                "[bold yellow]해결 방법:[/bold yellow]\n"
                "• 파일 형식 확인\n"
                "• 파일 경로 확인\n"
                "• ffmpeg 설치 상태 확인",
                title="[bold red]실패[/bold red]",
                border_style="red"
            ))
    
    def show_folder_links(self):
        """폴더 링크 표시"""
        videos_path = os.path.abspath(self.videos_dir)
        audio_path = os.path.abspath(self.audio_dir)
        output_path = os.path.abspath(self.output_dir)
        
        console.print(Panel(
            f"[bold yellow]📁 폴더 링크:[/bold yellow]\n\n"
            f"[cyan]동영상 폴더:[/cyan] [link=file://{videos_path}]{videos_path}[/link]\n"
            f"[cyan]음성 폴더:[/cyan] [link=file://{audio_path}]{audio_path}[/link]\n"
            f"[cyan]출력 폴더:[/cyan] [link=file://{output_path}]{output_path}[/link]\n\n"
            "[dim]위 링크를 클릭하면 폴더를 열 수 있습니다.[/dim]",
            title="[bold blue]📂 폴더 링크[/bold blue]",
            border_style="blue"
        ))
        console.print()

def main():
    """메인 함수"""
    try:
        merger = AudioVideoMerger()
        merger.run()
    except KeyboardInterrupt:
        console.print("\n[bold red]❌ 사용자가 프로그램을 종료했습니다.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ 예상치 못한 오류가 발생했습니다: {str(e)}[/bold red]")

if __name__ == "__main__":
    main()