"""
시스템 설정 및 환경 변수 관리
- 환경별 설정 분리
- 보안 강화
- 설정 검증
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class APIConfig:
    """API 설정"""
    youtube_api_key: str
    google_client_id: str
    google_client_secret: str
    redirect_uri: str
    firebase_config_path: str

@dataclass
class AnalysisConfig:
    """분석 설정"""
    time_decay_lambda: float = 0.1
    forgetting_factor: float = 0.05
    emotion_threshold: float = 0.3
    max_video_count: int = 50
    max_calendar_days: int = 30

@dataclass
class SystemConfig:
    """전체 시스템 설정"""
    debug_mode: bool = False
    log_level: str = "INFO"
    max_retries: int = 3
    timeout_seconds: int = 30
    data_backup_enabled: bool = True

class ConfigManager:
    """설정 관리자"""
    
    def __init__(self):
        self.base_path = Path("/Users/kjw/emotion-analysis-system")
        self.config_path = self.base_path / "config"
        self.ensure_config_directory()
    
    def ensure_config_directory(self):
        """설정 디렉토리 확인/생성"""
        self.config_path.mkdir(exist_ok=True)
        
        # 환경별 설정 파일 생성
        env_configs = {
            "development.yaml": {
                "api": {
                    "youtube_quota_limit": 1000,
                    "request_timeout": 10
                },
                "analysis": {
                    "time_decay_lambda": 0.1,
                    "forgetting_factor": 0.05,
                    "emotion_threshold": 0.3
                },
                "system": {
                    "debug_mode": True,
                    "log_level": "DEBUG",
                    "max_retries": 2
                }
            },
            "production.yaml": {
                "api": {
                    "youtube_quota_limit": 10000,
                    "request_timeout": 30
                },
                "analysis": {
                    "time_decay_lambda": 0.05,
                    "forgetting_factor": 0.03,
                    "emotion_threshold": 0.4
                },
                "system": {
                    "debug_mode": False,
                    "log_level": "INFO",
                    "max_retries": 5
                }
            }
        }
        
        for filename, config_data in env_configs.items():
            config_file = self.config_path / filename
            if not config_file.exists():
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
    
    def load_config(self, environment: str = "development") -> Dict[str, Any]:
        """환경별 설정 로드"""
        config_file = self.config_path / f"{environment}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_api_config(self, environment: str = "development") -> APIConfig:
        """API 설정 가져오기"""
        # 환경 변수에서 민감한 정보 로드
        return APIConfig(
            youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/callback"),
            firebase_config_path=str(self.config_path / "firebase_config.json")
        )
    
    def get_analysis_config(self, environment: str = "development") -> AnalysisConfig:
        """분석 설정 가져오기"""
        config = self.load_config(environment)
        analysis_config = config.get("analysis", {})
        
        return AnalysisConfig(
            time_decay_lambda=analysis_config.get("time_decay_lambda", 0.1),
            forgetting_factor=analysis_config.get("forgetting_factor", 0.05),
            emotion_threshold=analysis_config.get("emotion_threshold", 0.3),
            max_video_count=analysis_config.get("max_video_count", 50),
            max_calendar_days=analysis_config.get("max_calendar_days", 30)
        )
    
    def get_system_config(self, environment: str = "development") -> SystemConfig:
        """시스템 설정 가져오기"""
        config = self.load_config(environment)
        system_config = config.get("system", {})
        
        return SystemConfig(
            debug_mode=system_config.get("debug_mode", False),
            log_level=system_config.get("log_level", "INFO"),
            max_retries=system_config.get("max_retries", 3),
            timeout_seconds=system_config.get("timeout_seconds", 30),
            data_backup_enabled=system_config.get("data_backup_enabled", True)
        )
    
    def validate_environment(self) -> Dict[str, bool]:
        """환경 설정 검증"""
        validation_results = {}
        
        # 필수 환경 변수 확인
        required_env_vars = [
            "YOUTUBE_API_KEY",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET"
        ]
        
        for var in required_env_vars:
            validation_results[f"env_{var}"] = bool(os.getenv(var))
        
        # 설정 파일 확인
        config_files = ["development.yaml", "production.yaml"]
        for config_file in config_files:
            file_path = self.config_path / config_file
            validation_results[f"config_{config_file}"] = file_path.exists()
        
        # Firebase 설정 파일 확인
        firebase_config = self.config_path / "firebase_config.json"
        validation_results["firebase_config"] = firebase_config.exists()
        
        # 로그 디렉토리 확인
        log_dir = self.base_path / "logs"
        validation_results["log_directory"] = log_dir.exists()
        
        return validation_results
    
    def create_env_template(self):
        """환경 변수 템플릿 파일 생성"""
        env_template = """# 감정 분석 시스템 환경 변수
# 실제 값으로 수정한 후 .env 파일로 저장하세요

# Google API 설정
YOUTUBE_API_KEY=your_youtube_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/callback

# Firebase 설정
FIREBASE_PROJECT_ID=your_firebase_project_id

# 시스템 설정
ENVIRONMENT=development
DEBUG_MODE=true
LOG_LEVEL=INFO

# API 설정
API_SERVER_PORT=8080
API_SERVER_HOST=0.0.0.0
"""
        
        env_file = self.base_path / ".env.template"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_template)
        
        print(f"환경 변수 템플릿이 생성되었습니다: {env_file}")

# 글로벌 설정 매니저
config_manager = ConfigManager()

# 사용 예시
if __name__ == "__main__":
    # 설정 검증
    validation = config_manager.validate_environment()
    print("환경 설정 검증 결과:")
    for key, value in validation.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
    
    # 환경 변수 템플릿 생성
    config_manager.create_env_template()
    
    # 설정 로드 테스트
    try:
        api_config = config_manager.get_api_config()
        analysis_config = config_manager.get_analysis_config()
        system_config = config_manager.get_system_config()
        print("\n설정 로드 성공!")
    except Exception as e:
        print(f"설정 로드 실패: {e}")