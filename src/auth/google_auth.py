"""
Google OAuth 로그인 구현 (강화된 버전)
- 실제 Google 계정으로 로그인
- YouTube, Calendar API 접근 권한 요청
- 강화된 에러 처리 및 로깅
- 자동 재시도 및 복구 기능
"""

import os
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time

# 로깅 시스템 import
import sys
sys.path.append('/Users/kjw/emotion-analysis-system/src')

try:
    from utils.logging_system import system_logger, log_execution, retry_operation, DataCollectionError
    from utils.config_manager import config_manager
except ImportError:
    # 테스트 환경에서는 기본 로깅 사용
    class MockLogger:
        def info(self, msg, extra_data=None): print(f"INFO: {msg}")
        def success(self, msg, extra_data=None): print(f"SUCCESS: {msg}")
        def error(self, msg, error=None, extra_data=None): print(f"ERROR: {msg}")
        def warning(self, msg, extra_data=None): print(f"WARNING: {msg}")
    
    system_logger = MockLogger()
    
    def log_execution(func): return func
    def retry_operation(max_attempts=3, delay_seconds=2): 
        def decorator(func): return func
        return decorator
    
    class DataCollectionError(Exception): pass
    class MockConfigManager:
        def get_api_config(self): 
            from dataclasses import dataclass
            @dataclass
            class APIConfig:
                google_client_id: str = ""
                google_client_secret: str = ""
                redirect_uri: str = "http://localhost:8080/auth/callback"
            return APIConfig()
    config_manager = MockConfigManager()

class GoogleAuthenticator:
    """Google OAuth 인증을 관리하는 클래스 (강화된 버전)"""
    
    def __init__(self, config_path="/Users/kjw/emotion-analysis-system/config"):
        self.config_path = config_path
        self.credentials_file = f"{config_path}/google_credentials.json"
        self.token_file = f"{config_path}/token.json"
        
        # 설정 매니저에서 API 설정 가져오기
        try:
            api_config = config_manager.get_api_config()
            self.client_id = api_config.google_client_id
            self.client_secret = api_config.google_client_secret
            self.redirect_uri = api_config.redirect_uri
        except Exception as e:
            system_logger.error("API 설정 로드 실패", error=e)
        
        # 필요한 권한 범위 (Google에서 권장하는 형식)
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid'
        ]
        
        # 인증 상태 추적
        self.last_auth_time = None
        self.auth_failures = 0
        self.max_auth_failures = 3
        
        system_logger.info("GoogleAuthenticator 초기화 완료", {
            "scopes_count": len(self.scopes),
            "config_path": self.config_path
        })
    
    def _validate_credentials_file(self) -> bool:
        """자격 증명 파일 검증"""
        if not os.path.exists(self.credentials_file):
            system_logger.error("Google 자격 증명 파일이 없습니다")
            return False
        
        try:
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
                required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
                
                if 'installed' in creds_data:
                    creds_data = creds_data['installed']
                elif 'web' in creds_data:
                    creds_data = creds_data['web']
                
                missing_fields = [field for field in required_fields if field not in creds_data]
                if missing_fields:
                    system_logger.error("자격 증명 파일에 필수 필드가 없습니다")
                    return False
                
            system_logger.info("자격 증명 파일 검증 성공")
            return True
            
        except json.JSONDecodeError as e:
            system_logger.error("자격 증명 파일 형식 오류", error=e)
            return False
        except Exception as e:
            system_logger.error("자격 증명 파일 검증 실패", error=e)
            return False
    
    def _is_token_expired_soon(self, creds: Credentials, threshold_minutes: int = 5) -> bool:
        """토큰이 곧 만료되는지 확인"""
        if not creds.expiry:
            return False
        
        time_until_expiry = creds.expiry - datetime.utcnow()
        return time_until_expiry.total_seconds() < (threshold_minutes * 60)
    
    @log_execution
    def login(self):
        """Google 계정으로 로그인 (강화된 버전)"""
        system_logger.info("🔐 Google 로그인을 시작합니다...")
        
        # 자격 증명 파일 검증
        if not self._validate_credentials_file():
            print("Google 자격 증명 파일이 없습니다. 직접 브라우저 인증을 진행합니다.")
        
        creds = None
        
        try:
            # 기존 토큰이 있고 유효하면 사용
            if os.path.exists(self.token_file):
                try:
                    creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
                    
                    # 토큰이 유효하고 곧 만료되지 않음
                    if creds and creds.valid and not self._is_token_expired_soon(creds):
                        system_logger.success("기존 토큰 사용 (유효함)")
                        self.auth_failures = 0
                        self.last_auth_time = datetime.now()
                        return creds
                    
                    # 토큰이 만료되었지만 refresh_token이 있음
                    elif creds and creds.expired and creds.refresh_token:
                        system_logger.info("토큰 갱신 중...")
                        creds.refresh(Request())
                        
                        # 갱신된 토큰 저장
                        with open(self.token_file, 'w') as token:
                            token.write(creds.to_json())
                        
                        system_logger.success("토큰 갱신 완료")
                        self.auth_failures = 0
                        self.last_auth_time = datetime.now()
                        return creds
                    
                    else:
                        system_logger.warning("토큰이 유효하지 않거나 refresh_token이 없습니다")
                        
                except Exception as e:
                    system_logger.warning("기존 토큰 사용 실패", extra_data={"error": str(e)})
                    # 문제가 있는 토큰 파일 삭제
                    if os.path.exists(self.token_file):
                        os.remove(self.token_file)
                        system_logger.info("문제가 있는 토큰 파일 삭제")
            
            # 새로운 인증이 필요한 경우
            system_logger.info("새로운 Google 인증이 필요합니다")
            
            if os.path.exists(self.credentials_file):
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
            else:
                # 자격증명 파일이 없는 경우 환경변수에서 가져오기
                client_config = {
                    "installed": {
                        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost:8080"]
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, self.scopes)
            
            # 로컬 서버 포트 동적 설정
            import socket
            def get_free_port():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))
                    return s.getsockname()[1]
            
            port = get_free_port()
            system_logger.info(f"인증 서버를 포트 {port}에서 시작합니다")
            
            creds = flow.run_local_server(
                port=port,
                access_type='offline',
                prompt='consent',
                include_granted_scopes='true'
            )
            
            # 토큰 저장
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            
            system_logger.success("새로운 Google 인증 완료")
            
            self.auth_failures = 0
            self.last_auth_time = datetime.now()
            return creds
            
        except Exception as e:
            self.auth_failures += 1
            system_logger.error("Google 인증 실패", error=e)
            raise DataCollectionError(f"Google 인증 중 오류 발생: {str(e)}", "AUTH_ERROR")
    
    @log_execution
    def get_user_info(self, creds):
        """사용자 기본 정보 가져오기"""
        try:
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            
            system_logger.success("사용자 정보 조회 성공", {
                "user_name": user_info.get('name', 'N/A'),
                "user_email": user_info.get('email', 'N/A')
            })
            
            return user_info
            
        except Exception as e:
            system_logger.error("사용자 정보 가져오기 실패", error=e)
            return None

def test_google_login():
    """Google 로그인 테스트"""
    try:
        auth = GoogleAuthenticator()
        
        # 로그인 실행
        creds = auth.login()
        
        if creds:
            system_logger.success("인증 성공!")
            
            # 사용자 정보 가져오기
            user_info = auth.get_user_info(creds)
            
            return True
        else:
            system_logger.error("인증 실패")
            return False
            
    except Exception as e:
        system_logger.error("오류 발생", error=e)
        return False

if __name__ == "__main__":
    print("=== 감정 분석 시스템: Google 로그인 테스트 ===")
    result = test_google_login()
    
    if result:
        print("🎉 모든 테스트 통과!")
    else:
        print("❌ 테스트 실패")