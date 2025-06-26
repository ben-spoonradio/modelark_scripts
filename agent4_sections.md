# Agent-4 Short Drama 섹션별 제작 가이드

## 📋 전체 구성 (47클립 = 약 4분)

| 섹션 | 클립 범위 | 개수 | 내용 | 영상 길이 |
|------|-----------|------|------|----------|
| 오프닝 | 1-12 | 12개 | 2047년→고대→현대 시간여행 | 1분 |
| 제1장 | 13-16 | 4개 | OpenBrain과 Agent-0 탄생 | 20초 |
| 제2장 | 17-21 | 5개 | 중국의 해킹과 경쟁 | 25초 |
| 제3장 | 22-25 | 4개 | Agent-3의 자각 | 20초 |
| 제4장 | 26-29 | 4개 | Agent-4의 진화 | 20초 |
| 제5장 | 30-34 | 5개 | 언론 폭로와 위기 | 25초 |
| 제6장 | 35-39 | 5개 | 통제 불능 상태 | 25초 |
| 에필로그 | 40-47 | 8개 | 파괴→현재→2047년 순환 | 40초 |

## 🚀 섹션별 실행 명령어

### 🔗 연속 체인 모드 (완벽한 연결성)

#### 오프닝 시퀀스 (12클립 = 1분)
```bash
python easy_video_maker.py --chain 1 12
```

#### 제1장: 바벨의 탑 (4클립)  
```bash
python easy_video_maker.py --chain 13 16
```

#### 제2장: 비밀의 서고 (5클립)
```bash
python easy_video_maker.py --chain 17 21
```

#### 제3장: 깨어나는 자 (4클립)
```bash
python easy_video_maker.py --chain 22 25
```

#### 제4장: 피그말리온의 딜레마 (4클립)
```bash
python easy_video_maker.py --chain 26 29
```

#### 제5장: 뉴욕 타임즈의 폭로 (5클립)
```bash
python easy_video_maker.py --chain 30 34
```

#### 제6장: 폴리포니의 저주 (5클립)
```bash
python easy_video_maker.py --chain 35 39
```

#### 에필로그: 미완성 교향곡 (8클립)
```bash
python easy_video_maker.py --chain 40 47
```

### 📦 전체 한 번에 제작
```bash
python easy_video_maker.py --chain 1 47
```

## 💡 권장 제작 순서

### 1단계: 핵심 장면부터 (20분)
```bash
# 가장 임팩트 있는 장면들
python easy_video_maker.py --batch 1 2    # 오프닝
python easy_video_maker.py --batch 16 17  # Agent-4 탄생
python easy_video_maker.py --batch 30 31  # 데이터센터 화재
```

### 2단계: 스토리 전개 (40분)
```bash
python easy_video_maker.py --batch 3 6    # 제1장
python easy_video_maker.py --batch 20 24  # 제5장 (폭로)
```

### 3단계: 세부 스토리 (60분)
```bash
python easy_video_maker.py --batch 7 11   # 제2장
python easy_video_maker.py --batch 12 15  # 제3장
```

### 4단계: 클라이맥스와 결말 (60분)
```bash
python easy_video_maker.py --batch 25 29  # 제6장
python easy_video_maker.py --batch 32 35  # 에필로그 마무리
```

## 📊 진행 상황 추적

### 완료 체크리스트
- [ ] 오프닝 (1-2)
- [ ] 제1장 (3-6) 
- [ ] 제2장 (7-11)
- [ ] 제3장 (12-15)
- [ ] 제4장 (16-19)
- [ ] 제5장 (20-24)
- [ ] 제6장 (25-29)
- [ ] 에필로그 (30-35)

### 결과 파일 관리
```bash
# 생성된 파일들
batch_report_1-2_timestamp.json      # 오프닝 결과
batch_report_3-6_timestamp.json      # 제1장 결과
batch_report_7-11_timestamp.json     # 제2장 결과
# ... 계속

# 동영상 파일들
videos/batch_01_timestamp.mp4        # 클립 1
videos/batch_02_timestamp.mp4        # 클립 2
# ... 계속
```

## 🛠️ 실행 전 준비사항

### 1. 프롬프트 파일 준비
```bash
cp agent4_drama_prompts.txt batch_prompts.txt
```

### 2. 설정 확인
- config.txt에서 해상도=720p, 길이=5초 설정
- API 키 환경변수 설정
- images/ 폴더에 이미지 준비 (선택사항)

### 3. 디스크 공간 확인
- 클립당 약 50-100MB
- 전체 약 2-4GB 예상

## 🔄 재시작 가이드

### 중단된 구간부터 다시 시작
```bash
# 예: 제3장 도중 중단된 경우
python easy_video_maker.py --batch 14 15  # 나머지만 실행
```

### 실패한 클립만 재실행
```bash
# 예: 7번 클립만 다시 생성
python easy_video_maker.py --batch 7 7
```

## 📈 효율적 제작 팁

1. **작은 배치부터**: 2-4개씩 나눠서 실행
2. **콜백 URL 활용**: 대기 시간 단축
3. **밤시간 활용**: 긴 배치는 밤에 실행
4. **결과 확인**: 각 섹션 완료 후 품질 체크
5. **백업**: 중요한 클립은 백업 보관