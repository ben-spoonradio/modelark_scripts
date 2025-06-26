# 🎥 ModelArk Video Generator

BytePlus ModelArk API를 사용하여 텍스트와 이미지로 고품질 동영상을 생성하는 완전한 도구 모음입니다.

## 🌟 주요 기능

- 🎬 **텍스트-to-동영상**: 텍스트 설명만으로 동영상 생성
- 🖼️ **이미지-to-동영상**: 이미지를 동영상으로 변환
- 🔗 **연속 체인 생성**: 이전 클립의 마지막 프레임을 다음 클립의 시작으로 사용
- 📦 **배치 처리**: 여러 클립을 한 번에 생성
- 🎛️ **완전한 파라미터 제어**: 해상도, 화면비, 길이, FPS 등 모든 설정 가능
- 🌐 **콜백 URL 지원**: 비동기 처리 및 웹훅 알림
- 📊 **실시간 진행률**: 작업 상태 실시간 모니터링

## 📁 파일 구조

```
modelark_scripts/
├── 🎬 easy_video_maker.py           # 메인 동영상 생성기
├── 🔧 webhook_server.py             # 웹훅 서버 (선택사항)
├── 📝 batch_prompts.txt             # 배치 프롬프트 (Agent-4 드라마)
├── ⚙️  config.txt                   # 동영상 설정
├── 🚀 run.sh                        # 자동 실행 스크립트
├── 📁 images/                       # 이미지 파일들
├── 📁 videos/                       # 생성된 동영상들
├── 📖 사용법.md                     # 상세 사용법
├── 🔗 chain_usage.md                # 연속 체인 사용법
├── 📋 agent4_sections.md            # Agent-4 드라마 제작 가이드
├── 🔄 transition_guide.md           # 5초 클립 연결 가이드
└── 📋 README.md                     # 이 파일
```

## 🚀 빠른 시작

### 1. 환경 설정 (자동)
```bash
./run.sh
```
**모든 환경을 자동으로 설정해줍니다:**
- ✅ Homebrew, Python 자동 설치
- ✅ 필요한 모듈 (requests, Pillow, OpenCV) 설치
- ✅ API 키 설정 안내
- ✅ 실행 환경 완벽 구성

### 2. API 키 설정
```bash
export ARK_API_KEY=your_api_key_here
```

### 3. 사용 모드 선택

#### 📝 단일 동영상 생성
```bash
python easy_video_maker.py
```

#### 📦 배치 생성 (독립적)
```bash
# 전체 35개 클립 생성
python easy_video_maker.py --batch

# 특정 범위만 생성
python easy_video_maker.py --batch 1 5
```

#### 🔗 연속 체인 생성 (NEW!)
```bash
# 완벽한 연속성을 위한 체인 모드
python easy_video_maker.py --chain 1 5

# 각 클립의 마지막 프레임이 다음 클립의 시작 이미지가 됨
```

#### 🔍 작업 상태 확인
```bash
# 최근 작업 목록
python easy_video_maker.py --list

# 특정 작업 상태 확인
python easy_video_maker.py --check TASK_ID
```

## 🎯 Agent-4 AI 드라마 프로젝트

**35개 클립으로 구성된 완전한 AI 스릴러 단편 영화**

### 📋 섹션별 제작
```bash
# 오프닝 시퀀스
python easy_video_maker.py --chain 1 2

# 제1장: 바벨의 탑  
python easy_video_maker.py --chain 3 6

# 제2장: 비밀의 서고
python easy_video_maker.py --chain 7 11

# 전체 스토리 구성
# - 2047년 미래 관점에서 시작
# - AI 발전사를 다룬 스릴러
# - 5초 클립들의 자연스러운 연결
```

상세한 제작 가이드는 `agent4_sections.md` 참조

## 🔗 연속 체인 모드의 혁신

### 기존 방식의 한계
```
클립1: [이미지A] → 동영상1
클립2: [이미지A] → 동영상2  # 같은 이미지로 시작
클립3: [이미지A] → 동영상3  # 연결성 부족
```

### 새로운 체인 모드
```
클립1: [이미지A] → 동영상1 → [마지막프레임1]
클립2: [마지막프레임1] → 동영상2 → [마지막프레임2]  
클립3: [마지막프레임2] → 동영상3 → [마지막프레임3]
```

**결과: 영화 같은 완벽한 연속성! 🎬**

## ⚙️ 고급 설정 (config.txt)

```ini
# 해상도 (720p, 1080p)
resolution=720p

# 화면비 (16:9, 9:16, 1:1, 4:3 등)
# 이미지-to-동영상: adaptive, keep_ratio만 지원
ratio=9:16

# 동영상 길이 (5초 또는 10초)
duration=5

# 프레임율 (16 또는 24)
fps=24

# 워터마크 (true/false)
watermark=false

# 시드값 (-1은 랜덤)
seed=-1

# 카메라 고정 (true/false) 
camerafixed=false

# 콜백 URL (선택사항)
# callback_url=https://your-server.com/webhook
```

## 🛠️ 기술적 특징

### 🔄 자동 모델 선택
- **텍스트만**: t2v 모델 (모든 화면비 지원)
- **이미지+텍스트**: i2v 모델 (adaptive, keep_ratio만 지원)

### 📸 이미지 처리
- **지원 형식**: JPEG, PNG, WEBP, BMP, TIFF, GIF
- **크기 제한**: 최대 10MB, 300px~6000px
- **자동 최적화**: Base64 인코딩을 위한 크기/품질 조정

### 🔧 프레임 추출 기술
- **OpenCV 활용**: 동영상의 마지막 프레임을 고품질로 추출
- **자동 리사이즈**: 1280px 이하로 최적화
- **Base64 인코딩**: 다음 클립에서 바로 사용 가능

## 📊 성능 비교

| 모드 | 클립 5개 예상 시간 | 연결성 | 품질 |
|------|------------------|--------|------|
| 배치 | 15-20분 (병렬) | 보통 | 개별적 |
| 체인 | 25-30분 (순차) | 완벽 | 연속적 |

## 🔍 상세 가이드

- **🔗 연속 체인 모드**: `chain_usage.md`
- **📋 Agent-4 드라마**: `agent4_sections.md`  
- **🔄 클립 연결 기법**: `transition_guide.md`
- **📖 기본 사용법**: `사용법.md`

## 🆘 문제 해결

### 자주 발생하는 문제들

#### 🔑 API 키 오류
```bash
export ARK_API_KEY=your_actual_api_key
```

#### 📦 모듈 없음 오류
```bash
pip install requests Pillow opencv-python
```

#### 🖼️ Base64 인코딩 오류
- 이미지 크기가 너무 클 때 발생
- 체인 모드에서 자동으로 최적화됨

#### ⚡ HTTP 400 오류
- **i2v 모델**: ratio를 "adaptive" 또는 "keep_ratio"로 설정
- **t2v 모델**: 모든 ratio 지원

### 🔧 문제 해결 순서
1. `./run.sh` 실행 → 자동 환경 설정
2. API 키 확인 → 환경변수 올바른지 확인
3. 설정 파일 검토 → config.txt의 파라미터 확인
4. 상세 가이드 참조 → 각 .md 파일들

## 🎊 성공 사례

### 생성된 파일들
```
videos/
├── generated_video_1750869135.mp4      # 단일 생성
├── batch_01_timestamp.mp4              # 배치 생성
├── chain_01_timestamp.mp4              # 체인 생성
└── chain_01_timestamp_last_frame.jpg   # 추출된 프레임
```

### 활용 방법
- **QuickTime Player**: 바로 재생
- **iMovie**: 추가 편집 및 연결
- **Final Cut Pro**: 전문적 후반 작업
- **소셜미디어**: 직접 업로드 가능

## 🚀 향후 계획

- [ ] 더 많은 화면비 지원
- [ ] 실시간 미리보기
- [ ] 자동 자막 생성
- [ ] 음악 자동 매칭
- [ ] 클라우드 저장 연동

## 🎬 지금 바로 시작하세요!

```bash
git clone https://github.com/ben-spoonradio/modelark_scripts.git
cd modelark_scripts  
./run.sh
```

**5분 안에 첫 번째 AI 동영상을 만들어보세요!** ✨

---

*Made with ❤️ for creative AI video generation*
