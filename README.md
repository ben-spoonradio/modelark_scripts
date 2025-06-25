# 🎥 ModelArk Video Generator

BytePlus API를 사용하여 이미지를 동영상으로 변환하는 스크립트들입니다.

## 📁 파일 구조

```
modelark_scripts/
├── 🎬 easy_video_maker.py      # 쉬운 동영상 생성기 (메인)
├── 🔧 image_to_video_converter.py  # 원본 고급 스크립트
├── 📝 prompt.txt               # 동영상 설명 (한글 가능)
├── ⚙️  config.txt               # 이미지 설정
├── 🚀 run.sh                   # 실행 스크립트
├── 📖 사용법.md                 # 상세 사용법
├── 📋 README.md                # 이 파일
└── 📁 videos/                  # 생성된 동영상들 (자동 생성)
```

## 🚀 빠른 시작 (비개발자용)

### 1. 터미널 열기
- Spotlight 검색(⌘+Space) → "terminal" 입력

### 2. 폴더로 이동
```bash
cd /Users/moonbc/source/modelark_scripts
```

### 3. 쉬운 실행 스크립트 사용
```bash
./run.sh
```

이 스크립트가 모든 것을 자동으로 처리해줍니다:
- API 키 설정 도움
- 동영상 생성기 실행
- 문제 해결 안내

## 📝 파일 편집 방법

### prompt.txt 수정
- Finder에서 `prompt.txt` 더블클릭
- TextEdit에서 동영상 설명을 한글로 작성
- ⌘+S로 저장

### config.txt 수정  
- Finder에서 `config.txt` 더블클릭
- `image_url=` 뒤에 이미지 주소 입력
- ⌘+S로 저장

## 🛠 개발자용 (고급)

### 직접 실행
```bash
# API 키 설정
export ARK_API_KEY=your_api_key

# 쉬운 버전 실행
python3 easy_video_maker.py

# 또는 고급 버전 실행
python3 image_to_video_converter.py
```

### 의존성 설치
```bash
pip3 install requests
```

## 🔍 스크립트 차이점

| 특징 | easy_video_maker.py | image_to_video_converter.py |
|------|---------------------|----------------------------|
| 대상 | 비개발자 | 개발자 |
| 설정 | 파일 기반 (txt) | 코드 수정 또는 CLI |
| 언어 | 한글 메시지 | 영어 메시지 |
| 에러 처리 | 친절한 안내 | 기술적 정보 |
| 사용법 | 파일 편집만 | 코드 이해 필요 |

## 📖 상세 정보

- **사용법**: `사용법.md` 파일 참조
- **문제 해결**: 사용법.md의 "문제 해결" 섹션 참조
- **API 정보**: [BytePlus 공식 문서](https://www.bytepluses.com)

## 💡 프롬프트 예시

### 자연 풍경
```
아름다운 해변에서 파도가 천천히 밀려옵니다.
석양빛이 바다에 반사되어 황금빛으로 반짝입니다.
평화롭고 고요한 분위기입니다.
```

### 도시 풍경
```
비 오는 밤의 네온사인이 켜진 도시 거리입니다.
사람들이 우산을 쓰고 걸어다니고 있습니다.
현대적이고 활기찬 분위기입니다.
```

## 🆘 도움이 필요하면

1. **먼저 확인**: `사용법.md` 파일
2. **API 키 문제**: `./run.sh` 스크립트 사용
3. **파일 편집**: TextEdit에서 Plain Text 모드로
4. **한글 깨짐**: UTF-8 인코딩으로 저장

## 🎊 성공 사례

생성된 동영상은 `videos/` 폴더에 저장됩니다:
- QuickTime Player로 바로 재생 가능
- iMovie로 추가 편집 가능
- 소셜미디어 공유 가능

즐겁게 동영상을 만들어보세요! 🎬✨
