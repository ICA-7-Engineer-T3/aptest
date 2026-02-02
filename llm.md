# 감정 분석 시스템 개발 브랜치 정리

## 📅 개발 일지

### 2026년 2월 2일 - 프로젝트 초기 설정

**진행 상황:** 1단계 - 환경 준비 ✅

**완료된 작업:**
- [x] Git 저장소 초기화
- [x] 프로젝트 폴더 구조 생성
- [x] README.md 작성
- [x] Python 3.13 환경 확인

**생성된 폴더 구조:**
```
emotion-analysis-system/
├── src/
│   ├── auth/              # OAuth 로그인 (다음 단계)
│   ├── api/               # YouTube, Calendar API
│   ├── analysis/          # 감정 분석 알고리즘
│   └── database/          # Firebase 연동
├── config/                # API 키, 설정 파일들
├── tests/                 # 테스트 코드
└── .github/workflows/     # 자동 배포 설정
```

**다음 단계 계획:**
1. Python 가상환경 설정
2. 필요한 라이브러리 설치
3. Google OAuth 인증 시작

**참고 사항:**
- 개발 초보자를 위해 단계별로 천천히 진행
- 각 단계마다 설명 → 코드 → 테스트 순서로 진행

---

## 🎯 전체 개발 로드맵

1. ✅ **환경 준비** - 폴더 구조, Python 환경
2. ⏳ **Google OAuth 로그인** - 인증 시스템 구축
3. ⏳ **YouTube API** - 구독, 좋아요, 재생목록 데이터 수집
4. ⏳ **Calendar API** - 일정 데이터 수집
5. ⏳ **Firebase 연동** - 데이터 저장 구조 설계
6. ⏳ **감정 분석** - Time Decay, 피로도 알고리즘
7. ⏳ **결과 저장** - 분석 결과를 Firebase에 저장
8. ⏳ **피드백 시스템** - 재로그인 시 맞춤형 피드백
9. ⏳ **배포 설정** - Cloud Run, GitHub Actions
10. ⏳ **고도화** - RAG, 벡터 DB 연동

---

*이 문서는 개발 진행에 따라 계속 업데이트됩니다.*