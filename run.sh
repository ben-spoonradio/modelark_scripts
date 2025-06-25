#!/bin/bash

# 🎥 쉬운 동영상 생성기 실행 스크립트
# 이 스크립트를 실행하면 자동으로 동영상 생성기가 시작됩니다.

echo "🎬 쉬운 동영상 생성기를 시작합니다..."
echo "📁 작업 폴더: /Users/moonbc/source/modelark_scripts"
echo ""

# 작업 폴더로 이동
cd /Users/moonbc/source/modelark_scripts

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
python3 easy_video_maker.py

echo ""
echo "🏁 프로그램이 종료되었습니다."
echo "💡 다시 실행하려면 이 스크립트를 다시 실행하세요."
