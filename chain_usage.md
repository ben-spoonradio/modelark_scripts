# 🔗 연속 동영상 체인 생성 가이드

## 새로운 기능: 프레임 체인 연결

이제 이전 클립의 마지막 프레임을 다음 클립의 시작 이미지로 자동 사용하여 완벽한 연속성을 만들 수 있습니다!

## 🆚 배치 모드 vs 체인 모드

### 기존 배치 모드 (`--batch`)
```bash
python easy_video_maker.py --batch 1 5
```
- **특징**: 모든 클립이 동일한 시작 이미지 또는 텍스트만 사용
- **장점**: 빠른 처리, 독립적 생성
- **단점**: 클립 간 연결성 부족

### 새로운 체인 모드 (`--chain`)
```bash
python easy_video_maker.py --chain 1 5
```
- **특징**: 각 클립의 마지막 프레임이 다음 클립의 시작 이미지가 됨
- **장점**: 완벽한 시각적 연속성
- **단점**: 순차 처리로 시간 더 소요

## 🚀 체인 모드 사용법

### 1. 기본 실행
```bash
# 전체 35개 클립을 연속으로 생성
python easy_video_maker.py --chain

# 특정 범위만 연속 생성
python easy_video_maker.py --chain 1 5

# 중간 구간부터 연속 생성
python easy_video_maker.py --chain 10 15
```

### 2. 실행 프로세스
1. **초기 이미지 선택**: 첫 번째 클립용 이미지 선택 (선택사항)
2. **자동 프레임 추출**: 완성된 클립에서 마지막 프레임 자동 추출
3. **다음 클립 생성**: 추출된 프레임을 다음 클립의 시작 이미지로 사용
4. **연속 반복**: 모든 클립 완료까지 반복

### 3. 파일 구조
```
videos/
├── chain_01_timestamp.mp4        # 클립 1
├── chain_01_timestamp_last_frame.jpg  # 클립 1의 마지막 프레임
├── chain_02_timestamp.mp4        # 클립 2 (클립 1의 마지막 프레임으로 시작)
├── chain_02_timestamp_last_frame.jpg  # 클립 2의 마지막 프레임
└── ...
```

## 🎯 Agent-4 드라마 체인 생성 예시

### 1단계: 오프닝 체인 (2클립)
```bash
python easy_video_maker.py --chain 1 2
```
- 클립 1: 2047년 디지털 도서관 (블루 홀로그램)
- 클립 2: 블루 빛→알렉산드리아 도서관 화염→데이터센터

### 2단계: 제1장 체인 (4클립)
```bash
python easy_video_maker.py --chain 3 6
```
- 클립 3: 네바다 데이터센터 외관 (새벽 햇살)
- 클립 4: 내부 서버랙 (햇살 연결)
- 클립 5: 회의실 (서버 깜빡임 연결)
- 클립 6: 프레젠테이션 (화면 연결)

## 🛠️ 기술적 구현

### 1. 프레임 추출 기능
```python
def extract_last_frame(self, video_path: str) -> str:
    """OpenCV로 동영상의 마지막 프레임을 JPEG로 추출"""
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count - 1)
    ret, frame = cap.read()
    # RGB로 변환 후 고품질 JPEG 저장
```

### 2. 자동 이미지 인코딩
- 추출된 프레임을 Base64로 인코딩
- ModelArk API의 data:image/jpeg;base64 형식으로 전송
- 이전 클립과 완벽한 색감/구도 연결

### 3. 오류 처리
- 프레임 추출 실패 시 텍스트 전용으로 계속 진행
- 개별 클립 실패가 전체 체인을 중단시키지 않음
- 재시작 가능한 구조 (실패 지점부터 재실행)

## 💡 최적 사용 팁

### 1. 프롬프트 최적화
```
# 체인 모드에 최적화된 프롬프트 작성
클립1: "...카메라가 건물 입구를 향해 이동하며 마지막에 유리문 반사광이 화면을 채움"
클립2: "유리문 반사광에서 이어져 건물 내부로 자연스럽게 전환..."
```

### 2. 색감 연속성
- 각 클립 끝에 특정 색상으로 수렴하도록 설명
- 다음 클립은 그 색상에서 시작하도록 프롬프트 작성

### 3. 카메라 움직임 연결
- 이전 클립의 카메라 방향을 다음 클립에서 이어받기
- 줌인/줌아웃의 연속성 고려

## 🔧 필요한 설정

### requirements.txt
```
requests
Pillow
opencv-python
```

### config.txt 권장 설정
```
resolution=720p
duration=5
fps=24
ratio=adaptive  # i2v 모드 호환성
```

## 📊 성능 비교

| 모드 | 클립 5개 예상 시간 | 연결성 | 품질 |
|------|------------------|--------|------|
| 배치 | 15-20분 (병렬) | 보통 | 개별적 |
| 체인 | 25-30분 (순차) | 완벽 | 연속적 |

## 🚦 실행 전 체크리스트

- [ ] OpenCV, Pillow 설치 완료
- [ ] batch_prompts.txt 연결 최적화 프롬프트 준비
- [ ] config.txt에서 duration=5, ratio=adaptive 설정
- [ ] 충분한 디스크 공간 (클립당 100MB + 프레임 이미지)
- [ ] 안정적인 네트워크 연결 (순차 처리로 중단 방지 중요)

이제 Agent-4 드라마의 35개 클립을 완벽한 연속성으로 제작할 수 있습니다! 🎬