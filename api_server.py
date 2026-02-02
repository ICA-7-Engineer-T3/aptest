"""
감정 분석 시스템 웹 API 서버
- FastAPI 기반 REST API
- Cloud Run 배포 대응
- 감정 분석 엔드포인트 제공
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 로컬 모듈 임포트를 위한 경로 추가
sys.path.append('/app/src' if os.path.exists('/app/src') else 'src')

try:
    from main import CompleteEmotionSystem
except ImportError:
    print("⚠️ 로컬 모듈 임포트 실패 - 개발 모드로 실행")
    CompleteEmotionSystem = None

# 전역 변수
emotion_system = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 함수"""
    global emotion_system
    
    # 시작 시 초기화
    print("🚀 감정 분석 API 서버 시작...")
    try:
        if CompleteEmotionSystem:
            emotion_system = CompleteEmotionSystem()
            print("✅ 감정 분석 시스템 초기화 완료")
        else:
            print("⚠️ 개발 모드 - 감정 분석 시스템 없이 실행")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
    
    yield
    
    # 종료 시 정리
    print("🛑 감정 분석 API 서버 종료...")

# FastAPI 앱 생성
app = FastAPI(
    title="감정 분석 시스템 API",
    description="YouTube와 Calendar 데이터 기반 개인 맞춤형 감정 분석",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (모든 도메인에서 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델 정의
class AnalysisRequest(BaseModel):
    user_id: str = "default_user"
    force_refresh: bool = False

class AnalysisResponse(BaseModel):
    success: bool
    user_id: str
    timestamp: str
    emotion_summary: Optional[Dict] = None
    personalized_feedback: Optional[Dict] = None
    error_message: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

@app.get("/", response_model=Dict)
async def root():
    """루트 엔드포인트"""
    return {
        "message": "감정 분석 시스템 API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "history": "/history/{user_id}"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_emotion(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """감정 분석 실행 엔드포인트"""
    try:
        if not emotion_system:
            raise HTTPException(
                status_code=503, 
                detail="감정 분석 시스템이 초기화되지 않았습니다"
            )
        
        print(f"🎯 감정 분석 요청: {request.user_id}")
        
        # 사용자별 시스템 인스턴스 생성
        user_system = CompleteEmotionSystem(request.user_id)
        
        # 감정 분석 실행
        result = user_system.run_complete_analysis()
        
        if result.get('success', False):
            return AnalysisResponse(
                success=True,
                user_id=request.user_id,
                timestamp=result['analysis_timestamp'],
                emotion_summary=result['emotion_summary'],
                personalized_feedback=result['personalized_feedback']
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"분석 실패: {result.get('error', '알 수 없는 오류')}"
            )
            
    except Exception as e:
        print(f"❌ 분석 오류: {e}")
        return AnalysisResponse(
            success=False,
            user_id=request.user_id,
            timestamp=datetime.now().isoformat(),
            error_message=str(e)
        )

@app.get("/history/{user_id}")
async def get_user_history(user_id: str, limit: int = 10):
    """사용자 감정 분석 히스토리 조회"""
    try:
        if not emotion_system:
            raise HTTPException(
                status_code=503,
                detail="감정 분석 시스템이 초기화되지 않았습니다"
            )
        
        print(f"📊 히스토리 조회: {user_id}")
        
        # Firebase에서 히스토리 조회
        history = emotion_system.firebase_manager.get_user_history(user_id, limit)
        
        return {
            "success": True,
            "user_id": user_id,
            "history_count": len(history),
            "history": history
        }
        
    except Exception as e:
        print(f"❌ 히스토리 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends/{user_id}")
async def get_emotion_trends(user_id: str, days: int = 7):
    """감정 변화 트렌드 조회"""
    try:
        if not emotion_system:
            raise HTTPException(
                status_code=503,
                detail="감정 분석 시스템이 초기화되지 않았습니다"
            )
        
        print(f"📈 트렌드 분석: {user_id}")
        
        # Firebase에서 트렌드 데이터 조회
        trends = emotion_system.firebase_manager.get_emotion_trends(user_id, days)
        
        return {
            "success": True,
            "user_id": user_id,
            "analysis_period": f"{days}일",
            "trends": trends
        }
        
    except Exception as e:
        print(f"❌ 트렌드 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 개발용 실행 함수
def run_dev_server():
    """개발 서버 실행"""
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    run_dev_server()