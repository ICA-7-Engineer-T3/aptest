"""
로깅 및 에러 처리 시스템
- 구조화된 로깅
- 에러 추적 및 복구
- 성능 모니터링
"""

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import traceback
import functools

class EmotionSystemLogger:
    """감정 분석 시스템 전용 로거"""
    
    def __init__(self, name: str = "EmotionSystem"):
        self.logger = logging.getLogger(name)
        self.setup_logging()
    
    def setup_logging(self):
        """로깅 설정 초기화"""
        # 로그 레벨 설정
        self.logger.setLevel(logging.INFO)
        
        # 로그 디렉토리 생성
        log_dir = "/Users/kjw/emotion-analysis-system/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 파일 핸들러 (일별 로그)
        today = datetime.now().strftime("%Y%m%d")
        log_file = f"{log_dir}/emotion_system_{today}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 포매터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가 (중복 방지)
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str, extra_data: Optional[Dict] = None):
        """정보 로그"""
        log_message = f"{message}"
        if extra_data:
            log_message += f" | Data: {extra_data}"
        self.logger.info(log_message)
    
    def warning(self, message: str, extra_data: Optional[Dict] = None):
        """경고 로그"""
        log_message = f"{message}"
        if extra_data:
            log_message += f" | Data: {extra_data}"
        self.logger.warning(log_message)
    
    def error(self, message: str, error: Exception = None, extra_data: Optional[Dict] = None):
        """에러 로그"""
        log_message = f"{message}"
        if error:
            log_message += f" | Error: {str(error)}"
        if extra_data:
            log_message += f" | Data: {extra_data}"
        self.logger.error(log_message)
        
        # 상세 스택 트레이스
        if error:
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
    
    def success(self, message: str, extra_data: Optional[Dict] = None):
        """성공 로그"""
        log_message = f"✅ SUCCESS: {message}"
        if extra_data:
            log_message += f" | Data: {extra_data}"
        self.logger.info(log_message)

# 글로벌 로거 인스턴스
system_logger = EmotionSystemLogger()

def log_execution(func):
    """함수 실행을 로깅하는 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        function_name = func.__name__
        
        try:
            system_logger.info(f"🚀 Starting {function_name}")
            result = func(*args, **kwargs)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            system_logger.success(
                f"Completed {function_name}",
                {"execution_time_seconds": execution_time}
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            system_logger.error(
                f"Failed {function_name}",
                error=e,
                extra_data={"execution_time_seconds": execution_time}
            )
            raise
            
    return wrapper

class EmotionSystemError(Exception):
    """감정 분석 시스템 커스텀 예외"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class DataCollectionError(EmotionSystemError):
    """데이터 수집 관련 에러"""
    pass

class AnalysisError(EmotionSystemError):
    """분석 관련 에러"""
    pass

class FirebaseError(EmotionSystemError):
    """Firebase 관련 에러"""
    pass

def safe_execute(func, default_return=None, error_message="Operation failed"):
    """안전한 함수 실행 (에러 시 기본값 반환)"""
    try:
        return func()
    except Exception as e:
        system_logger.error(error_message, error=e)
        return default_return

def validate_data(data: Any, required_fields: list, data_name: str = "data") -> bool:
    """데이터 유효성 검사"""
    try:
        if not data:
            raise ValueError(f"{data_name} is empty or None")
        
        if isinstance(data, dict):
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields in {data_name}: {missing_fields}")
        
        system_logger.info(f"✅ Data validation passed for {data_name}")
        return True
        
    except Exception as e:
        system_logger.error(f"Data validation failed for {data_name}", error=e)
        return False

def retry_operation(max_attempts: int = 3, delay_seconds: int = 1):
    """재시도 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        system_logger.error(
                            f"Final attempt {attempt} failed for {func.__name__}",
                            error=e
                        )
                        raise
                    else:
                        system_logger.warning(
                            f"Attempt {attempt} failed for {func.__name__}, retrying...",
                            extra_data={"error": str(e)}
                        )
                        time.sleep(delay_seconds)
                        
        return wrapper
    return decorator

# 사용 예시
if __name__ == "__main__":
    # 로깅 테스트
    system_logger.info("시스템 시작", {"version": "1.0", "user": "test"})
    system_logger.success("작업 완료", {"items_processed": 10})
    
    try:
        raise ValueError("테스트 에러")
    except Exception as e:
        system_logger.error("테스트 에러 발생", error=e, extra_data={"test": True})
    
    print("로깅 시스템 테스트 완료!")