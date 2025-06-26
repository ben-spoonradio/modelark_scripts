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

# Python 설치 확인
if ! command -v python &> /dev/null; then
    echo "🐍 Python을 설치하는 중..."
    brew install python
fi

# 필요한 Python 모듈들 설치 확인
echo "📦 필요한 Python 모듈들을 확인하는 중..."

# requests 모듈 확인
if ! python -c "import requests" &> /dev/null; then
    echo "📦 requests 모듈 설치 중..."
    python -m pip install requests
fi

# Pillow (이미지 처리) 모듈 확인
if ! python -c "import PIL" &> /dev/null; then
    echo "🖼️ Pillow 모듈 설치 중..."
    python -m pip install Pillow
fi

# Python 패키지 업그레이드
echo "📦 pip 업그레이드 중..."
python -m pip install --upgrade pip

# OpenCV (동영상 처리) 모듈 확인
if ! python -c "import cv2" &> /dev/null; then
    echo "🎥 OpenCV 모듈 설치 중..."
    python -m pip install opencv-python opencv-python-headless
fi

# 추가 필수 모듈들 확인
echo "📦 추가 필수 모듈들을 확인하는 중..."

# numpy 모듈 확인 (OpenCV 의존성)
if ! python -c "import numpy" &> /dev/null; then
    echo "🔢 numpy 모듈 설치 중..."
    python -m pip install numpy
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
python easy_video_maker.py

echo ""
echo "🏁 프로그램이 종료되었습니다."
echo "💡 다시 실행하려면 이 스크립트를 다시 실행하세요."
