"""
감정 분석 시스템 테스트 코드
- 단위 테스트
- 통합 테스트
- API 테스트
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import json

# 프로젝트 모듈 import
sys.path.append('/Users/kjw/emotion-analysis-system/src')
from auth.google_auth import GoogleAuthenticator
from analysis.emotion_engine import EmotionAnalysisEngine
from utils.logging_system import EmotionSystemLogger, validate_data
from utils.config_manager import ConfigManager

class TestGoogleAuthenticator(unittest.TestCase):
    """Google 인증 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_credentials = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        }
        
        # 테스트용 자격 증명 파일 생성
        creds_file = os.path.join(self.temp_dir, "google_credentials.json")
        with open(creds_file, 'w') as f:
            json.dump(self.test_credentials, f)
        
        # 환경 변수 설정
        os.environ['GOOGLE_CLIENT_ID'] = 'test_client_id'
        os.environ['GOOGLE_CLIENT_SECRET'] = 'test_client_secret'
        
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_credentials_validation_success(self):
        """자격 증명 파일 검증 성공 테스트"""
        auth = GoogleAuthenticator(config_path=self.temp_dir)
        self.assertTrue(auth._validate_credentials_file())
    
    def test_credentials_validation_missing_file(self):
        """자격 증명 파일 없음 테스트"""
        empty_dir = tempfile.mkdtemp()
        auth = GoogleAuthenticator(config_path=empty_dir)
        self.assertFalse(auth._validate_credentials_file())
        
        import shutil
        shutil.rmtree(empty_dir)
    
    def test_token_expiry_check(self):
        """토큰 만료 체크 테스트"""
        from google.oauth2.credentials import Credentials
        
        auth = GoogleAuthenticator(config_path=self.temp_dir)
        
        # 곧 만료되는 토큰
        soon_expired_creds = Mock(spec=Credentials)
        soon_expired_creds.expiry = datetime.utcnow() + timedelta(minutes=2)
        self.assertTrue(auth._is_token_expired_soon(soon_expired_creds))
        
        # 아직 유효한 토큰
        valid_creds = Mock(spec=Credentials)
        valid_creds.expiry = datetime.utcnow() + timedelta(hours=1)
        self.assertFalse(auth._is_token_expired_soon(valid_creds))

class TestEmotionAnalysisEngine(unittest.TestCase):
    """감정 분석 엔진 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.engine = EmotionAnalysisEngine()
        self.sample_youtube_data = {
            "videos": [
                {
                    "title": "행복한 음악 플레이리스트",
                    "description": "기분 좋은 음악들",
                    "published_at": "2024-01-01T10:00:00Z",
                    "channel_title": "음악 채널"
                },
                {
                    "title": "슬픈 영화 리뷰",
                    "description": "우울한 영화에 대한 감상",
                    "published_at": "2024-01-02T15:00:00Z",
                    "channel_title": "영화 리뷰"
                }
            ]
        }
        
        self.sample_calendar_data = {
            "events": [
                {
                    "summary": "중요한 회의",
                    "description": "스트레스 받는 회의",
                    "start": {"dateTime": "2024-01-01T09:00:00Z"},
                    "end": {"dateTime": "2024-01-01T11:00:00Z"}
                },
                {
                    "summary": "친구와 만남",
                    "description": "즐거운 시간",
                    "start": {"dateTime": "2024-01-01T19:00:00Z"},
                    "end": {"dateTime": "2024-01-01T21:00:00Z"}
                }
            ]
        }
    
    def test_emotion_scoring_basic(self):
        """기본 감정 점수 계산 테스트"""
        positive_text = "행복하고 즐거운 하루였습니다"
        negative_text = "슬프고 우울한 기분입니다"
        
        positive_score = self.engine._calculate_emotion_score(positive_text)
        negative_score = self.engine._calculate_emotion_score(negative_text)
        
        # 긍정 텍스트는 양수, 부정 텍스트는 음수여야 함
        self.assertGreater(positive_score, 0)
        self.assertLess(negative_score, 0)
    
    def test_time_decay_calculation(self):
        """시간 감쇠 계산 테스트"""
        recent_datetime = datetime.now() - timedelta(hours=1)
        old_datetime = datetime.now() - timedelta(days=7)
        
        recent_factor = self.engine._calculate_time_decay(recent_datetime)
        old_factor = self.engine._calculate_time_decay(old_datetime)
        
        # 최근 데이터가 더 높은 가중치를 가져야 함
        self.assertGreater(recent_factor, old_factor)
        self.assertLessEqual(recent_factor, 1.0)
        self.assertGreaterEqual(old_factor, 0.0)
    
    def test_youtube_analysis(self):
        """YouTube 데이터 분석 테스트"""
        result = self.engine.analyze_youtube_data(self.sample_youtube_data)
        
        # 결과 구조 검증
        self.assertIn('overall_emotion', result)
        self.assertIn('trend_analysis', result)
        self.assertIn('video_emotions', result)
        self.assertIn('summary', result)
        
        # 감정 점수가 유효한 범위에 있는지 확인
        self.assertIsInstance(result['overall_emotion'], (int, float))
        self.assertGreaterEqual(result['overall_emotion'], -1.0)
        self.assertLessEqual(result['overall_emotion'], 1.0)
    
    def test_calendar_fatigue_analysis(self):
        """캘린더 피로도 분석 테스트"""
        result = self.engine.analyze_calendar_data(self.sample_calendar_data)
        
        # 결과 구조 검증
        self.assertIn('fatigue_level', result)
        self.assertIn('stress_indicators', result)
        self.assertIn('event_analysis', result)
        
        # 피로도가 유효한 범위에 있는지 확인
        self.assertIsInstance(result['fatigue_level'], (int, float))
        self.assertGreaterEqual(result['fatigue_level'], 0.0)
        self.assertLessEqual(result['fatigue_level'], 1.0)

class TestDataValidation(unittest.TestCase):
    """데이터 검증 테스트"""
    
    def test_validate_data_success(self):
        """데이터 검증 성공 테스트"""
        valid_data = {
            "name": "테스트",
            "email": "test@example.com",
            "age": 25
        }
        required_fields = ["name", "email"]
        
        self.assertTrue(validate_data(valid_data, required_fields))
    
    def test_validate_data_missing_fields(self):
        """필수 필드 누락 테스트"""
        invalid_data = {
            "name": "테스트"
        }
        required_fields = ["name", "email", "age"]
        
        self.assertFalse(validate_data(invalid_data, required_fields))
    
    def test_validate_data_empty(self):
        """빈 데이터 테스트"""
        empty_data = None
        required_fields = ["name"]
        
        self.assertFalse(validate_data(empty_data, required_fields))

class TestConfigManager(unittest.TestCase):
    """설정 관리자 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_environment_validation(self):
        """환경 설정 검증 테스트"""
        # 필수 환경 변수 설정
        os.environ['YOUTUBE_API_KEY'] = 'test_key'
        os.environ['GOOGLE_CLIENT_ID'] = 'test_client'
        os.environ['GOOGLE_CLIENT_SECRET'] = 'test_secret'
        
        config_manager = ConfigManager()
        validation_result = config_manager.validate_environment()
        
        # 환경 변수가 올바르게 감지되는지 확인
        self.assertTrue(validation_result.get('env_YOUTUBE_API_KEY', False))
        self.assertTrue(validation_result.get('env_GOOGLE_CLIENT_ID', False))
        self.assertTrue(validation_result.get('env_GOOGLE_CLIENT_SECRET', False))

class TestLoggingSystem(unittest.TestCase):
    """로깅 시스템 테스트"""
    
    def test_logger_initialization(self):
        """로거 초기화 테스트"""
        logger = EmotionSystemLogger("TestLogger")
        self.assertIsNotNone(logger.logger)
    
    def test_log_execution_decorator(self):
        """실행 로깅 데코레이터 테스트"""
        from utils.logging_system import log_execution
        
        @log_execution
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
    
    def test_retry_decorator(self):
        """재시도 데코레이터 테스트"""
        from utils.logging_system import retry_operation
        
        call_count = 0
        
        @retry_operation(max_attempts=3)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("테스트 에러")
            return "success"
        
        result = failing_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)

# 통합 테스트
class TestSystemIntegration(unittest.TestCase):
    """시스템 통합 테스트"""
    
    @patch('src.auth.google_auth.InstalledAppFlow')
    @patch('src.auth.google_auth.Credentials')
    def test_full_analysis_workflow(self, mock_credentials, mock_flow):
        """전체 분석 워크플로우 테스트"""
        # Mock 설정
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.refresh_token = "test_refresh_token"
        mock_credentials.from_authorized_user_file.return_value = mock_creds
        
        # 테스트 실행 (실제 API 호출 없이)
        engine = EmotionAnalysisEngine()
        
        # 샘플 데이터로 분석 테스트
        sample_youtube = {"videos": []}
        sample_calendar = {"events": []}
        
        youtube_result = engine.analyze_youtube_data(sample_youtube)
        calendar_result = engine.analyze_calendar_data(sample_calendar)
        
        # 결과 검증
        self.assertIsInstance(youtube_result, dict)
        self.assertIsInstance(calendar_result, dict)

def run_tests():
    """테스트 실행 함수"""
    print("🧪 감정 분석 시스템 테스트 시작\n")
    
    # 테스트 로더 설정
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 클래스들 추가
    test_classes = [
        TestGoogleAuthenticator,
        TestEmotionAnalysisEngine,
        TestDataValidation,
        TestConfigManager,
        TestLoggingSystem,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestClass(test_class)
        suite.addTests(tests)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 요약
    print(f"\n📊 테스트 결과 요약:")
    print(f"✅ 성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 실패: {len(result.failures)}")
    print(f"🚨 에러: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    if result.errors:
        print("\n🚨 에러가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)