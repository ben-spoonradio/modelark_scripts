#!/bin/bash

# 🎥 쉬운 동영상 생성기 실행 스크립트
# 이 스크립트를 실행하면 자동으로 동영상 생성기가 시작됩니다.

echo "🎬 쉬운 동영상 생성기를 시작합니다..."
echo "📁 작업 폴더: $(pwd)"
echo ""

# 작업 폴더로 이동 (스크립트가 있는 디렉토리)
cd "$(dirname "$0")"

# Homebrew 설치 확인
if ! command -v brew &> /dev/null; then
    echo "📦 Homebrew를 설치하는 중..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Homebrew Python 설치 및 PATH 설정
echo "🐍 Homebrew Python을 확인하는 중..."

# Homebrew Python이 없으면 설치
if ! brew list python@3.11 &> /dev/null && ! brew list python@3.12 &> /dev/null; then
    echo "🐍 Homebrew Python을 설치하는 중..."
    brew install python
fi

# Homebrew PATH를 .zshrc에 추가 (없으면)
ZSHRC_FILE="$HOME/.zshrc"
BREW_PATH_ARM64='export PATH="/opt/homebrew/bin:$PATH"'
BREW_PATH_INTEL='export PATH="/usr/local/bin:$PATH"'

# Apple Silicon vs Intel Mac 구분
if [[ $(uname -m) == "arm64" ]]; then
    BREW_BIN="/opt/homebrew/bin"
    BREW_PATH_EXPORT=$BREW_PATH_ARM64
else
    BREW_BIN="/usr/local/bin"
    BREW_PATH_EXPORT=$BREW_PATH_INTEL
fi

# .zshrc 파일이 없으면 생성
if [ ! -f "$ZSHRC_FILE" ]; then
    touch "$ZSHRC_FILE"
fi

# PATH가 .zshrc에 없으면 추가
if ! grep -q "$BREW_PATH_EXPORT" "$ZSHRC_FILE" 2>/dev/null; then
    echo "⚙️  .zshrc에 Homebrew PATH를 추가하는 중..."
    echo "" >> "$ZSHRC_FILE"
    echo "# Homebrew PATH" >> "$ZSHRC_FILE"
    echo "$BREW_PATH_EXPORT" >> "$ZSHRC_FILE"
    echo "✅ .zshrc에 PATH가 추가되었습니다."
fi

# 현재 세션에서 PATH 설정
export PATH="$BREW_BIN:$PATH"

# Python 명령어 설정
PYTHON_CMD="python3"
PIP_FLAGS="--break-system-packages"

echo "🐍 사용할 Python: $(which $PYTHON_CMD)"

# 필요한 Python 모듈들 설치 확인
echo "📦 필요한 Python 모듈들을 확인하는 중..."

# requests 모듈 확인
if ! $PYTHON_CMD -c "import requests" &> /dev/null; then
    echo "📦 requests 모듈 설치 중..."
    $PYTHON_CMD -m pip install $PIP_FLAGS requests
fi

# Pillow (이미지 처리) 모듈 확인
if ! $PYTHON_CMD -c "import PIL" &> /dev/null; then
    echo "🖼️ Pillow 모듈 설치 중..."
    $PYTHON_CMD -m pip install $PIP_FLAGS Pillow
fi

# Python 패키지 업그레이드
echo "📦 pip 업그레이드 중..."
$PYTHON_CMD -m pip install $PIP_FLAGS --upgrade pip

# OpenCV (동영상 처리) 모듈 확인
if ! $PYTHON_CMD -c "import cv2" &> /dev/null; then
    echo "🎥 OpenCV 모듈 설치 중..."
    $PYTHON_CMD -m pip install $PIP_FLAGS opencv-python opencv-python-headless
fi

# 추가 필수 모듈들 확인
echo "📦 추가 필수 모듈들을 확인하는 중..."

# numpy 모듈 확인 (OpenCV 의존성)
if ! $PYTHON_CMD -c "import numpy" &> /dev/null; then
    echo "🔢 numpy 모듈 설치 중..."
    $PYTHON_CMD -m pip install $PIP_FLAGS numpy
fi

# API 키 확인
if [ -z "$ARK_API_KEY" ]; then
    echo "⚠️  API 키가 설정되지 않았습니다."
    echo "💡 다음 중 하나를 선택하세요:"
    echo ""
    echo "1. 이번만 사용할 API 키 입력"
    echo "2. 영구적으로 저장 (추천)"
    echo ""
    read -p "선택 (1/2): " choice
    
    if [ "$choice" = "1" ]; then
        read -p "API 키를 입력하세요: " temp_key
        export ARK_API_KEY="$temp_key"
    elif [ "$choice" = "2" ]; then
        read -p "API 키를 입력하세요: " perm_key
        echo "export ARK_API_KEY=\"$perm_key\"" >> ~/.zshrc
        export ARK_API_KEY="$perm_key"
        echo "✅ API 키가 ~/.zshrc에 저장되었습니다."
        echo "💡 다음 터미널 세션부터는 자동으로 설정됩니다."
    else
        echo "❌ 잘못된 선택입니다."
        exit 1
    fi
fi

echo ""
echo "🚀 동영상 생성기를 실행합니다..."
echo ""

# Python 스크립트 실행
$PYTHON_CMD easy_video_maker.py

echo ""
echo "🏁 프로그램이 종료되었습니다."
echo "💡 다시 실행하려면 이 스크립트를 다시 실행하세요."
