"""
Google OAuth 로그인 구현
- 실제 Google 계정으로 로그인
- YouTube, Calendar API 접근 권한 요청
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GoogleAuthenticator:
    """Google OAuth 인증을 관리하는 클래스"""
    
    def __init__(self):
        self.credentials_file = "/Users/kjw/emotion-analysis-system/config/google_credentials.json"
        self.token_file = "/Users/kjw/emotion-analysis-system/config/token.json"
        
        # 필요한 권한 범위 (Google에서 권장하는 형식)
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid'
        ]
        
    def login(self):
        """Google 계정으로 로그인 (refresh_token 보장)"""
        print("🔐 Google 로그인을 시작합니다...")
        
        creds = None
        
        # 기존 토큰이 있고 유효하면 사용
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
                if creds and creds.valid:
                    print("✅ 기존 토큰 사용 (유효함)")
                    return creds
                elif creds and creds.expired and creds.refresh_token:
                    print("🔄 토큰 갱신 중...")
                    creds.refresh(Request())
                    # 갱신된 토큰 저장
                    with open(self.token_file, 'w') as token:
                        token.write(creds.to_json())
                    print("✅ 토큰 갱신 완료")
                    return creds
            except Exception as e:
                print(f"⚠️ 기존 토큰 문제: {e}")
                # 문제가 있는 토큰 파일 삭제
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                    print("🗑️ 문제가 있는 토큰 파일 삭제")
                
        # 새로운 인증이 필요한 경우
        print("🌐 브라우저에서 Google 로그인을 진행해주세요...")
        print("⚠️ 강제 재승인을 위해 기존 권한을 다시 확인합니다.")
        
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_file, self.scopes)
        
        # 강제 재승인으로 refresh_token 확보
        creds = flow.run_local_server(
            port=8080, 
            access_type='offline',  # refresh_token을 위한 offline access
            approval_prompt='force',  # 강제 재승인
            include_granted_scopes='true'
        )
                
        # 토큰 저장
        with open(self.token_file, 'w') as token:
            token.write(creds.to_json())
            
        # refresh_token 검증
        if creds.refresh_token:
            print("✅ Google 로그인 성공! (refresh_token 포함)")
        else:
            print("⚠️ 로그인 성공했지만 refresh_token이 없습니다.")
            print("💡 Google 계정 보안 설정에서 앱 권한을 삭제 후 다시 시도해보세요.")
            
        return creds
    
    def get_user_info(self, creds):
        """사용자 기본 정보 가져오기"""
        try:
            # People API로 사용자 정보 가져오기
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            
            print(f"👤 사용자: {user_info.get('name', 'N/A')}")
            print(f"📧 이메일: {user_info.get('email', 'N/A')}")
            
            return user_info
        except Exception as e:
            print(f"❌ 사용자 정보 가져오기 실패: {e}")
            return None

def test_google_login():
    """Google 로그인 테스트"""
    try:
        auth = GoogleAuthenticator()
        
        # 로그인 실행
        creds = auth.login()
        
        if creds:
            print("🎉 인증 성공!")
            
            # 사용자 정보 가져오기
            user_info = auth.get_user_info(creds)
            
            return True
        else:
            print("❌ 인증 실패")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("=== 감정 분석 시스템: Google 로그인 테스트 ===")
    result = test_google_login()
    
    if result:
        print("🎉 모든 테스트 통과!")
    else:
        print("❌ 테스트 실패")