"""
Firebase Firestore 데이터베이스 관리자
- 감정 분석 결과를 클라우드에 저장
- 사용자별 히스토리 관리
- 시계열 데이터 추적
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Firebase 설정 파일이 있을 때만 임포트
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    print("⚠️ Firebase 라이브러리가 설치되지 않았거나 설정이 필요합니다.")
    FIREBASE_AVAILABLE = False

class FirebaseManager:
    """Firebase Firestore 데이터베이스 관리 클래스"""
    
    def __init__(self):
        self.db = None
        self.initialized = False
        
        # Firebase 서비스 계정 키 파일 경로
        self.service_account_path = "/Users/kjw/emotion-analysis-system/config/firebase_service_account.json"
        
    def initialize_firebase(self):
        """Firebase 초기화"""
        if not FIREBASE_AVAILABLE:
            print("❌ Firebase 라이브러리를 먼저 설치해주세요: pip install firebase-admin")
            return False
            
        try:
            # Firebase 서비스 계정 키 확인
            if not os.path.exists(self.service_account_path):
                print(f"⚠️ Firebase 서비스 계정 키 파일이 없습니다: {self.service_account_path}")
                print("💡 Firebase 콘솔에서 서비스 계정 키를 다운로드하고 설정해주세요.")
                return False
            
            # Firebase 앱 초기화 (이미 초기화된 경우 스킵)
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.service_account_path)
                firebase_admin.initialize_app(cred)
                
            # Firestore 클라이언트 생성
            self.db = firestore.client()
            self.initialized = True
            
            print("✅ Firebase 초기화 완료!")
            return True
            
        except Exception as e:
            print(f"❌ Firebase 초기화 실패: {e}")
            return False
    
    def save_emotion_analysis(self, user_id: str, analysis_data: Dict) -> Optional[str]:
        """감정 분석 결과를 Firestore에 저장"""
        if not self.initialized:
            print("⚠️ Firebase가 초기화되지 않았습니다.")
            return None
            
        try:
            # 컬렉션 구조: users/{user_id}/analyses/{analysis_id}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            analysis_id = f"analysis_{timestamp}"
            
            # 저장할 데이터 구조 정리
            save_data = {
                'user_id': user_id,
                'analysis_id': analysis_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'analysis_date': analysis_data.get('analysis_date'),
                
                # YouTube 분석 결과
                'youtube_analysis': analysis_data.get('youtube_analysis', {}),
                
                # Calendar 분석 결과  
                'calendar_analysis': analysis_data.get('calendar_analysis', {}),
                
                # 종합 감정 분석
                'overall_emotion': analysis_data.get('overall_emotion', {}),
                
                # 메타 데이터
                'data_source': 'emotion_analysis_system',
                'version': '1.0'
            }
            
            # Firestore에 데이터 저장
            doc_ref = self.db.collection('users').document(user_id).collection('analyses').document(analysis_id)
            doc_ref.set(save_data)
            
            print(f"✅ 감정 분석 결과 저장 완료!")
            print(f"   📊 분석 ID: {analysis_id}")
            print(f"   👤 사용자: {user_id}")
            
            return analysis_id
            
        except Exception as e:
            print(f"❌ 데이터 저장 실패: {e}")
            return None
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """사용자의 감정 분석 히스토리 가져오기"""
        if not self.initialized:
            print("⚠️ Firebase가 초기화되지 않았습니다.")
            return []
            
        try:
            # 최근 분석 결과들을 시간순으로 가져오기
            analyses_ref = self.db.collection('users').document(user_id).collection('analyses')
            query = analyses_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            
            results = []
            for doc in query.stream():
                data = doc.to_dict()
                results.append(data)
                
            print(f"✅ 사용자 히스토리 {len(results)}개 조회 완료")
            return results
            
        except Exception as e:
            print(f"❌ 히스토리 조회 실패: {e}")
            return []
    
    def get_emotion_trends(self, user_id: str, days: int = 7) -> Dict:
        """감정 변화 트렌드 분석"""
        if not self.initialized:
            return {}
            
        try:
            # 최근 N일간 데이터 가져오기
            history = self.get_user_history(user_id, limit=days*3)  # 여유분 포함
            
            if not history:
                return {}
                
            trends = {
                'emotion_scores': [],
                'stress_levels': [],
                'fatigue_indices': [],
                'dates': []
            }
            
            for analysis in history:
                overall = analysis.get('overall_emotion', {})
                calendar = analysis.get('calendar_analysis', {})
                
                trends['emotion_scores'].append(overall.get('emotion_score', 0))
                trends['stress_levels'].append(calendar.get('stress_level', 'unknown'))
                trends['fatigue_indices'].append(calendar.get('fatigue_index', 0))
                trends['dates'].append(analysis.get('analysis_date', ''))
            
            print(f"📈 감정 트렌드 분석 완료: {len(trends['dates'])}개 데이터")
            return trends
            
        except Exception as e:
            print(f"❌ 트렌드 분석 실패: {e}")
            return {}

class MockFirebaseManager:
    """Firebase가 설정되지 않았을 때 사용할 Mock 클래스"""
    
    def __init__(self):
        self.initialized = False
        self.local_storage = "/Users/kjw/emotion-analysis-system/config/mock_firebase_data.json"
        
    def initialize_firebase(self):
        """Mock 초기화"""
        print("🔧 Firebase 설정이 없어서 로컬 파일로 테스트합니다.")
        self.initialized = True
        return True
    
    def save_emotion_analysis(self, user_id: str, analysis_data: Dict) -> Optional[str]:
        """로컬 파일에 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            analysis_id = f"analysis_{timestamp}"
            
            # 기존 데이터 로드
            if os.path.exists(self.local_storage):
                with open(self.local_storage, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            # 새 데이터 추가
            if user_id not in data:
                data[user_id] = []
                
            save_entry = {
                'analysis_id': analysis_id,
                'timestamp': datetime.now().isoformat(),
                **analysis_data
            }
            
            data[user_id].append(save_entry)
            
            # 파일에 저장
            with open(self.local_storage, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ Mock Firebase에 저장 완료! (실제로는 로컬 파일)")
            print(f"   📁 저장 위치: {self.local_storage}")
            print(f"   📊 분석 ID: {analysis_id}")
            
            return analysis_id
            
        except Exception as e:
            print(f"❌ Mock 저장 실패: {e}")
            return None
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """로컬 파일에서 히스토리 조회"""
        try:
            if not os.path.exists(self.local_storage):
                return []
                
            with open(self.local_storage, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            user_data = data.get(user_id, [])
            return user_data[-limit:] if user_data else []
            
        except Exception as e:
            print(f"❌ Mock 히스토리 조회 실패: {e}")
            return []

def test_firebase_integration():
    """Firebase 연동 테스트"""
    print("=== Firebase 연동 테스트 ===")
    
    # Firebase 매니저 초기화
    firebase_mgr = FirebaseManager()
    
    if not firebase_mgr.initialize_firebase():
        print("🔧 Firebase 설정이 없어서 Mock으로 테스트합니다.")
        firebase_mgr = MockFirebaseManager()
        firebase_mgr.initialize_firebase()
    
    # 최근 감정 분석 결과 로드
    try:
        analysis_files = [f for f in os.listdir('/Users/kjw/emotion-analysis-system/config/') 
                         if f.startswith('emotion_analysis_') and f.endswith('.json')]
        
        if not analysis_files:
            print("❌ 저장된 감정 분석 결과가 없습니다.")
            return False
            
        # 가장 최신 파일 사용
        latest_file = sorted(analysis_files)[-1]
        file_path = f"/Users/kjw/emotion-analysis-system/config/{latest_file}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
            
        print(f"📁 분석 결과 파일 로드: {latest_file}")
        
    except Exception as e:
        print(f"❌ 분석 결과 파일 로드 실패: {e}")
        return False
    
    # Firebase에 저장
    user_id = analysis_data.get('user_id', 'test_user')
    analysis_id = firebase_mgr.save_emotion_analysis(user_id, analysis_data)
    
    if analysis_id:
        print(f"🎉 Firebase 저장 성공!")
        
        # 히스토리 조회 테스트
        history = firebase_mgr.get_user_history(user_id, limit=5)
        print(f"📊 사용자 히스토리: {len(history)}개 조회")
        
        return True
    else:
        print("❌ Firebase 저장 실패")
        return False

if __name__ == "__main__":
    test_firebase_integration()