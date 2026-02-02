# 감정 분석 시스템 (Emotion Analysis System)

YouTube와 Google Calendar 데이터를 활용한 개인 맞춤형 감정 분석 시스템입니다.

## 🌟 주요 기능

- **📊 데이터 수집**: YouTube (구독채널, 좋아요 동영상) + Google Calendar (일정, 피로도 분석)
- **🧠 AI 감정 분석**: Time Decay, Forgetting Factor 적용한 고급 알고리즘
- **☁️ 클라우드 저장**: Firebase Firestore를 통한 실시간 데이터 관리
- **📈 트렌드 분석**: 시간별 감정 변화 패턴 분석
- **💡 개인화 추천**: 사용자 맞춤형 피드백 및 액션 아이템

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 2. Google API 설정
1. [Google Cloud Console](https://console.cloud.google.com)에서 프로젝트 생성
2. YouTube Data API v3, Google Calendar API 활성화
3. OAuth 2.0 클라이언트 ID 생성 (데스크톱 애플리케이션)
4. 다운로드한 JSON 파일을 `config/google_credentials.json`으로 저장

### 3. Firebase 설정
1. [Firebase Console](https://console.firebase.google.com)에서 프로젝트 생성
2. Firestore Database 생성 (테스트 모드)
3. 서비스 계정 키 생성 및 다운로드
4. JSON 파일을 `config/firebase_service_account.json`으로 저장

### 4. 실행
```bash
# 완전한 감정 분석 시스템 실행
python main.py

# API 서버 실행 (개발용)
python api_server.py
```

## 📁 프로젝트 구조

```
emotion-analysis-system/
├── src/                    # 메인 소스 코드
│   ├── auth/              # Google OAuth 로그인
│   ├── api/               # YouTube, Calendar API 연동
│   ├── analysis/          # 감정 분석 알고리즘
│   └── database/          # Firebase 연동
├── config/                # 설정 파일들 (gitignore됨)
├── tests/                 # 테스트 코드
├── .github/workflows/     # CI/CD 배포 설정
├── main.py               # 통합 실행 스크립트
├── api_server.py         # FastAPI 웹 서버
├── Dockerfile           # Docker 컨테이너 설정
└── requirements.txt     # Python 패키지 목록
```

## 🔧 API 엔드포인트

- `GET /health` - 서버 상태 확인
- `POST /analyze` - 사용자 감정 분석 실행
- `GET /history/{user_id}` - 감정 분석 히스토리 조회

## 🎯 감정 분석 알고리즘

### Time Decay 공식
```
Emotion_score(t) = Σ (Emotion_i * exp(-λ * Δt_i))
```

### 피로도 계산
```
Fatigue_index = α * Fatigue_density + β * Fatigue_gap + γ * Fatigue_time
```

## 📊 데이터 구조

### YouTube 분석
- 구독 채널별 감정 키워드 분석
- 좋아요 동영상의 제목/설명 분석
- 관심사 카테고리 분류 (Entertainment, Lifestyle, Education, Social)

### Calendar 분석
- 일정 밀도 계산 (일별 이벤트 수)
- 시간대별 분포 분석 (아침/오후/저녁/밤)
- 피로도 지수 산출

## 🚀 배포

### Docker 컨테이너
```bash
# 이미지 빌드
docker build -t emotion-analysis .

# 컨테이너 실행
docker run -p 8000:8000 emotion-analysis
```

### Cloud Run 배포
GitHub Actions를 통한 자동 배포 지원

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

---

*개발 진행 상황과 상세 정보는 `llm.md` 파일을 참조하세요.*