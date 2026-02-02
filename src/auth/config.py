"""
Google API 설정 관리
- API 키와 인증 정보를 안전하게 관리
- 환경별로 다른 설정을 사용할 수 있게 함
"""

import os
import json
from pathlib import Path

class GoogleConfig:
    """Google API 설정을 관리하는 클래스"""
    
    def __init__(self):
        # 프로젝트 루트 디렉토리 설정
        self.project_root = Path("/Users/kjw/emotion-analysis-system")
        self.config_path = self.project_root / "config"
        
    def get_credentials_path(self):
        """Google OAuth 인증 파일 경로 반환"""
        return self.config_path / "google_credentials.json"
        
    def get_scopes(self):
        """필요한 권한 목록 반환"""
        return [
            'https://www.googleapis.com/auth/youtube.readonly',  # YouTube 데이터 읽기
            'https://www.googleapis.com/auth/calendar.readonly', # Calendar 데이터 읽기
            'openid',                                           # 사용자 기본 정보
            'email',                                            # 이메일 주소
            'profile'                                           # 프로필 정보
        ]
    
    def check_setup(self):
        """설정이 제대로 되어 있는지 확인"""
        credentials_file = self.get_credentials_path()
        
        if not credentials_file.exists():
            return False, f"인증 파일이 없습니다: {credentials_file}"
            
        try:
            with open(credentials_file, 'r') as f:
                data = json.load(f)
                if 'web' in data or 'installed' in data:
                    return True, "설정이 올바르게 되어 있습니다."
                else:
                    return False, "인증 파일 형식이 올바르지 않습니다."
        except Exception as e:
            return False, f"인증 파일 읽기 오류: {e}"

# 테스트
if __name__ == "__main__":
    print("=== Google API 설정 확인 ===")
    
    config = GoogleConfig()
    is_ok, message = config.check_setup()
    
    print(f"📁 설정 폴더: {config.config_path}")
    print(f"🔑 인증 파일: {config.get_credentials_path()}")
    print(f"📋 필요한 권한: {len(config.get_scopes())}개")
    
    if is_ok:
        print(f"✅ {message}")
    else:
        print(f"⚠️  {message}")
        print("\n📝 다음 단계: Google 개발자 콘솔에서 API 키 발급 필요")