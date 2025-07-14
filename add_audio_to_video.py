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
    
    def merge_audio_video(self, video_path: str, audio_path: str, output_path: str, audio_mode: str = "replace") -> bool:
        """동영상과 음성 파일 합치기"""
        try:
            # 파일 길이 확인
            video_duration = self.get_media_duration(video_path)
            audio_duration = self.get_media_duration(audio_path)
            
            console.print(f"[bold cyan]📹 동영상 길이:[/bold cyan] {video_duration:.1f}초")
            console.print(f"[bold cyan]🎵 음성 길이:[/bold cyan] {audio_duration:.1f}초")
            
            # ffmpeg 명령어 구성
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
        success = self.merge_audio_video(video_path, audio_path, output_path, audio_mode)
        
        if success:
            # 결과 표시
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            console.print(Panel(
                f"[bold green]✅ 성공적으로 완료되었습니다![/bold green]\n\n"
                f"[cyan]출력 파일:[/cyan] {output_filename}\n"
                f"[cyan]파일 크기:[/cyan] {file_size:.1f}MB\n"
                f"[cyan]저장 위치:[/cyan] {output_path}",
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