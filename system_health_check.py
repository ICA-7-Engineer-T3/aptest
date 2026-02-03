"""
시스템 상태 검증 스크립트
- 모든 컴포넌트 상태 확인
- 설정 파일 검증
- 성능 지표 요약
"""

import sys
import os
from datetime import datetime
import json

sys.path.append('/Users/kjw/emotion-analysis-system/src')

def check_system_health():
    """전체 시스템 상태 검사"""
    print("🔍 === 감정 분석 시스템 상태 검증 ===")
    print(f"📅 검사 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "components": {},
        "overall_status": "UNKNOWN"
    }
    
    try:
        # 1. 로깅 시스템 확인
        print("\n🧾 로깅 시스템 확인...")
        try:
            from utils.logging_system import system_logger, EmotionSystemLogger
            logger_test = EmotionSystemLogger("HealthCheck")
            logger_test.info("헬스 체크 시작")
            health_status["components"]["logging"] = "OK"
            print("✅ 로깅 시스템: 정상")
        except Exception as e:
            health_status["components"]["logging"] = f"ERROR: {e}"
            print(f"❌ 로깅 시스템: 오류 - {e}")
        
        # 2. 설정 관리자 확인
        print("\n⚙️ 설정 관리자 확인...")
        try:
            from utils.config_manager import config_manager
            validation = config_manager.validate_environment()
            missing_configs = [k for k, v in validation.items() if not v]
            
            if missing_configs:
                health_status["components"]["config"] = f"WARNING: Missing {missing_configs}"
                print(f"⚠️ 설정 관리자: 누락된 설정 - {missing_configs}")
            else:
                health_status["components"]["config"] = "OK"
                print("✅ 설정 관리자: 정상")
        except Exception as e:
            health_status["components"]["config"] = f"ERROR: {e}"
            print(f"❌ 설정 관리자: 오류 - {e}")
        
        # 3. 성능 모니터링 확인
        print("\n📊 성능 모니터링 확인...")
        try:
            from utils.performance_monitor import performance_monitor
            summary = performance_monitor.get_performance_summary(1)
            health_status["components"]["performance"] = "OK"
            health_status["performance_summary"] = {
                "total_operations": summary.get("total_operations", 0),
                "uptime_hours": summary.get("system_stats", {}).get("uptime_hours", 0)
            }
            print("✅ 성능 모니터링: 정상")
        except Exception as e:
            health_status["components"]["performance"] = f"ERROR: {e}"
            print(f"❌ 성능 모니터링: 오류 - {e}")
        
        # 4. Google 인증 시스템 확인
        print("\n🔐 Google 인증 시스템 확인...")
        try:
            from auth.google_auth import GoogleAuthenticator
            auth = GoogleAuthenticator()
            # 자격 증명 파일만 확인 (실제 로그인은 하지 않음)
            if auth._validate_credentials_file():
                health_status["components"]["google_auth"] = "OK"
                print("✅ Google 인증: 정상 (자격증명 파일 확인됨)")
            else:
                health_status["components"]["google_auth"] = "WARNING: No credentials file"
                print("⚠️ Google 인증: 자격증명 파일 없음")
        except Exception as e:
            health_status["components"]["google_auth"] = f"ERROR: {e}"
            print(f"❌ Google 인증: 오류 - {e}")
        
        # 5. 감정 분석 엔진 확인
        print("\n🧠 감정 분석 엔진 확인...")
        try:
            from analysis.emotion_engine import EmotionAnalysisEngine
            engine = EmotionAnalysisEngine()
            # 간단한 테스트 실행 (실제 메서드명 사용)
            test_data = {"subscriptions": [], "liked_videos": []}
            result = engine.analyze_youtube_emotions(test_data)
            if result and 'emotion_scores' in result:
                health_status["components"]["emotion_engine"] = "OK"
                print("✅ 감정 분석 엔진: 정상")
            else:
                health_status["components"]["emotion_engine"] = "WARNING: Invalid result"
                print("⚠️ 감정 분석 엔진: 결과 형식 이상")
        except Exception as e:
            health_status["components"]["emotion_engine"] = f"ERROR: {e}"
            print(f"❌ 감정 분석 엔진: 오류 - {e}")
        
        # 6. Firebase 관리자 확인
        print("\n🔥 Firebase 관리자 확인...")
        try:
            from database.firebase_manager import FirebaseManager
            fb_manager = FirebaseManager()
            # Firebase 설정 파일 확인 (여러 경로 시도)
            config_paths = [
                "/Users/kjw/emotion-analysis-system/config/firebase_config.json",
                "/Users/kjw/emotion-analysis-system/config/firebase_service_account.json"
            ]
            
            config_found = False
            for config_path in config_paths:
                if os.path.exists(config_path):
                    config_found = True
                    break
            
            if config_found:
                health_status["components"]["firebase"] = "OK"
                print("✅ Firebase 관리자: 정상 (설정 파일 확인됨)")
            else:
                health_status["components"]["firebase"] = "WARNING: No config file"
                print("⚠️ Firebase 관리자: 설정 파일 없음")
        except Exception as e:
            health_status["components"]["firebase"] = f"ERROR: {e}"
            print(f"❌ Firebase 관리자: 오류 - {e}")
        
        # 7. 디렉토리 구조 확인
        print("\n📁 디렉토리 구조 확인...")
        required_dirs = [
            "/Users/kjw/emotion-analysis-system/src",
            "/Users/kjw/emotion-analysis-system/config",
            "/Users/kjw/emotion-analysis-system/logs",
            "/Users/kjw/emotion-analysis-system/tests"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            health_status["components"]["directory_structure"] = f"WARNING: Missing {missing_dirs}"
            print(f"⚠️ 디렉토리 구조: 누락된 디렉토리 - {missing_dirs}")
        else:
            health_status["components"]["directory_structure"] = "OK"
            print("✅ 디렉토리 구조: 정상")
        
        # 전체 상태 결정
        error_count = len([v for v in health_status["components"].values() if v.startswith("ERROR")])
        warning_count = len([v for v in health_status["components"].values() if v.startswith("WARNING")])
        ok_count = len([v for v in health_status["components"].values() if v == "OK"])
        
        if error_count == 0 and warning_count == 0:
            health_status["overall_status"] = "HEALTHY"
            status_emoji = "🟢"
            status_text = "모든 컴포넌트 정상"
        elif error_count == 0:
            health_status["overall_status"] = "WARNING"
            status_emoji = "🟡"
            status_text = f"경고 {warning_count}개 (정상 {ok_count}개)"
        else:
            health_status["overall_status"] = "ERROR"
            status_emoji = "🔴"
            status_text = f"오류 {error_count}개, 경고 {warning_count}개 (정상 {ok_count}개)"
        
        print(f"\n{status_emoji} === 전체 시스템 상태: {health_status['overall_status']} ===")
        print(f"📋 상태 요약: {status_text}")
        
        # 상태 보고서 저장
        report_path = "/Users/kjw/emotion-analysis-system/logs/system_health_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(health_status, f, indent=2, ensure_ascii=False)
        
        print(f"💾 상태 보고서 저장: {report_path}")
        
        return health_status
        
    except Exception as e:
        print(f"❌ 시스템 상태 검사 중 치명적 오류: {e}")
        return {"overall_status": "CRITICAL_ERROR", "error": str(e)}

if __name__ == "__main__":
    health_status = check_system_health()
    
    # 종료 코드 설정
    if health_status["overall_status"] == "HEALTHY":
        exit(0)
    elif health_status["overall_status"] == "WARNING":
        exit(1)
    else:
        exit(2)