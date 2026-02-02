"""
통합 감정 분석 시스템 (Complete Emotion Analysis System)
- 데이터 수집부터 Firebase 저장까지 전체 프로세스 자동화
- 히스토리 기반 감정 변화 트렌드 분석
- 개인화된 피드백 및 추천 시스템
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 모듈 경로 추가
sys.path.append('/Users/kjw/emotion-analysis-system/src')

from data_integration import IntegratedCollector
from analysis.emotion_engine import EmotionAnalysisEngine
from database.firebase_manager import FirebaseManager

class CompleteEmotionSystem:
    """완전한 감정 분석 시스템"""
    
    def __init__(self, user_id: str = "김재원"):
        self.user_id = user_id
        self.data_collector = IntegratedCollector(user_id)
        self.emotion_engine = EmotionAnalysisEngine()
        self.firebase_manager = FirebaseManager()
        
        # 시스템 상태
        self.collected_data = None
        self.analysis_result = None
        self.history_data = []
        
    def run_complete_analysis(self) -> Dict:
        """전체 감정 분석 프로세스 실행"""
        print("🎯 === 통합 감정 분석 시스템 시작 ===")
        print(f"👤 사용자: {self.user_id}")
        print(f"📅 분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        # 1단계: 데이터 수집
        success = self._collect_data()
        if not success:
            return {'success': False, 'error': '데이터 수집 실패'}
        
        # 2단계: 감정 분석
        success = self._analyze_emotions()
        if not success:
            return {'success': False, 'error': '감정 분석 실패'}
        
        # 3단계: Firebase 저장
        success = self._save_to_firebase()
        if not success:
            return {'success': False, 'error': 'Firebase 저장 실패'}
        
        # 4단계: 히스토리 비교 분석
        self._analyze_trends()
        
        # 5단계: 개인화된 피드백 생성
        personalized_feedback = self._generate_personalized_feedback()
        
        # 6단계: 최종 결과 정리
        final_result = self._compile_final_result(personalized_feedback)
        
        print("🎉 === 통합 감정 분석 완료 ===")
        return final_result
    
    def _collect_data(self) -> bool:
        """1단계: 통합 데이터 수집"""
        try:
            print("\n📊 1단계: 데이터 수집 중...")
            self.collected_data = self.data_collector.collect_all_data()
            
            if not self.collected_data.get('analysis_ready', False):
                print("❌ 데이터 수집 실패 또는 데이터 부족")
                return False
                
            youtube_count = self.collected_data.get('youtube_data', {}).get('subscription_count', 0)
            calendar_count = self.collected_data.get('calendar_data', {}).get('event_count', 0)
            
            print(f"✅ 데이터 수집 완료!")
            print(f"   📺 YouTube: 구독 {youtube_count}개")
            print(f"   📅 Calendar: 일정 {calendar_count}개")
            
            return True
            
        except Exception as e:
            print(f"❌ 데이터 수집 오류: {e}")
            return False
    
    def _analyze_emotions(self) -> bool:
        """2단계: 감정 분석 실행"""
        try:
            print("\n🧠 2단계: 감정 분석 중...")
            
            # YouTube 감정 분석
            youtube_analysis = self.emotion_engine.analyze_youtube_emotions(
                self.collected_data['youtube_data']
            )
            
            # Calendar 피로도 분석
            calendar_analysis = self.emotion_engine.analyze_calendar_fatigue(
                self.collected_data['calendar_data']
            )
            
            # 전체 감정 상태 계산
            overall_emotion = self.emotion_engine.calculate_overall_emotion(
                youtube_analysis, calendar_analysis
            )
            
            # 분석 결과 정리
            self.analysis_result = {
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.user_id,
                'youtube_analysis': youtube_analysis,
                'calendar_analysis': calendar_analysis,
                'overall_emotion': overall_emotion
            }
            
            print(f"✅ 감정 분석 완료!")
            print(f"   {overall_emotion['mood_emoji']} 현재 감정: {overall_emotion['emotion_state']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 감정 분석 오류: {e}")
            return False
    
    def _save_to_firebase(self) -> bool:
        """3단계: Firebase에 결과 저장"""
        try:
            print("\n☁️ 3단계: Firebase 저장 중...")
            
            # Firebase 초기화
            if not self.firebase_manager.initialize_firebase():
                print("⚠️ Firebase 초기화 실패, 로컬 저장으로 진행")
                return True  # 로컬 저장은 성공으로 처리
            
            # Firebase에 저장
            analysis_id = self.firebase_manager.save_emotion_analysis(
                self.user_id, self.analysis_result
            )
            
            if analysis_id:
                print(f"✅ Firebase 저장 완료!")
                print(f"   📊 분석 ID: {analysis_id}")
                return True
            else:
                print("❌ Firebase 저장 실패")
                return False
                
        except Exception as e:
            print(f"❌ Firebase 저장 오류: {e}")
            return False
    
    def _analyze_trends(self):
        """4단계: 히스토리 기반 트렌드 분석"""
        try:
            print("\n📈 4단계: 감정 변화 트렌드 분석 중...")
            
            # 히스토리 조회
            self.history_data = self.firebase_manager.get_user_history(self.user_id, limit=7)
            
            if len(self.history_data) < 2:
                print("ℹ️ 트렌드 분석을 위한 히스토리가 부족합니다 (최소 2개 필요)")
                return
            
            # 감정 점수 변화 분석
            emotion_scores = []
            stress_levels = []
            dates = []
            
            for data in self.history_data:
                overall = data.get('overall_emotion', {})
                calendar = data.get('calendar_analysis', {})
                
                emotion_scores.append(overall.get('emotion_score', 0))
                stress_levels.append(calendar.get('stress_level', 'unknown'))
                dates.append(data.get('analysis_date', ''))
            
            # 트렌드 계산
            if len(emotion_scores) >= 2:
                recent_avg = sum(emotion_scores[:2]) / 2
                older_avg = sum(emotion_scores[2:]) / len(emotion_scores[2:]) if len(emotion_scores) > 2 else recent_avg
                
                trend = "상승" if recent_avg > older_avg else "하락" if recent_avg < older_avg else "유지"
                
                print(f"✅ 트렌드 분석 완료!")
                print(f"   📊 최근 평균 감정: {recent_avg:.2f}")
                print(f"   📈 감정 트렌드: {trend}")
                
                # 분석 결과에 트렌드 정보 추가
                self.analysis_result['trend_analysis'] = {
                    'emotion_trend': trend,
                    'recent_average': recent_avg,
                    'historical_average': older_avg,
                    'data_points': len(emotion_scores)
                }
                
        except Exception as e:
            print(f"❌ 트렌드 분석 오류: {e}")
    
    def _generate_personalized_feedback(self) -> Dict:
        """5단계: 개인화된 피드백 생성"""
        try:
            print("\n💡 5단계: 개인화된 피드백 생성 중...")
            
            overall = self.analysis_result['overall_emotion']
            calendar = self.analysis_result['calendar_analysis']
            youtube = self.analysis_result['youtube_analysis']
            trend = self.analysis_result.get('trend_analysis', {})
            
            feedback = {
                'current_state': overall['emotion_state'],
                'recommendations': [],
                'insights': [],
                'action_items': []
            }
            
            # 현재 상태 기반 추천
            emotion_state = overall['emotion_state']
            stress_level = calendar['stress_level']
            top_interest = overall['top_interest']
            
            # 기본 추천사항
            feedback['recommendations'].extend(overall.get('recommendations', []))
            
            # 트렌드 기반 추천
            emotion_trend = trend.get('emotion_trend', '')
            if emotion_trend == "하락":
                feedback['recommendations'].append("😔 최근 감정이 하락 추세입니다. 스트레스 관리에 더 신경써보세요.")
                feedback['action_items'].append("이번 주 휴식 시간을 늘려보세요")
            elif emotion_trend == "상승":
                feedback['recommendations'].append("😊 감정이 좋아지고 있어요! 현재 패턴을 유지해보세요.")
                feedback['action_items'].append("현재의 긍정적 활동들을 계속 이어가세요")
            
            # 관심사 기반 구체적 추천
            if top_interest == 'entertainment':
                if stress_level == 'high':
                    feedback['action_items'].append("좋아하는 음악이나 영화로 스트레스를 풀어보세요")
                else:
                    feedback['action_items'].append("새로운 엔터테인먼트 콘텐츠를 탐색해보세요")
            
            # 인사이트 생성
            youtube_positive = youtube['emotion_scores'].get('positive', 0)
            if youtube_positive > 0.7:
                feedback['insights'].append(f"🎯 관심사가 긍정적이에요! {top_interest} 분야에서 더 많은 활동을 추천합니다.")
            
            fatigue_index = calendar['fatigue_index']
            if fatigue_index > 1.5:
                feedback['insights'].append(f"📅 일정이 다소 빡빡해요. 피로도 지수: {fatigue_index:.1f}")
            else:
                feedback['insights'].append("📅 일정 관리가 잘 되고 있어요!")
            
            print(f"✅ 개인화된 피드백 생성 완료!")
            print(f"   💡 추천사항: {len(feedback['recommendations'])}개")
            print(f"   🔍 인사이트: {len(feedback['insights'])}개")
            print(f"   ✅ 액션 아이템: {len(feedback['action_items'])}개")
            
            return feedback
            
        except Exception as e:
            print(f"❌ 피드백 생성 오류: {e}")
            return {}
    
    def _compile_final_result(self, feedback: Dict) -> Dict:
        """6단계: 최종 결과 정리"""
        final_result = {
            'success': True,
            'user_id': self.user_id,
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # 핵심 결과
            'emotion_summary': {
                'current_mood': self.analysis_result['overall_emotion']['emotion_state'],
                'mood_emoji': self.analysis_result['overall_emotion']['mood_emoji'],
                'emotion_score': self.analysis_result['overall_emotion']['emotion_score'],
                'stress_level': self.analysis_result['calendar_analysis']['stress_level'],
                'fatigue_index': self.analysis_result['calendar_analysis']['fatigue_index']
            },
            
            # 상세 분석
            'detailed_analysis': self.analysis_result,
            
            # 개인화된 피드백
            'personalized_feedback': feedback,
            
            # 메타 정보
            'data_quality': {
                'youtube_items': self.analysis_result['youtube_analysis']['total_channels'] + 
                               self.analysis_result['youtube_analysis']['total_liked'],
                'calendar_events': self.analysis_result['calendar_analysis'].get('daily_counts', {}),
                'history_available': len(self.history_data)
            }
        }
        
        return final_result
    
    def print_beautiful_summary(self, result: Dict):
        """결과를 아름답게 출력"""
        if not result.get('success', False):
            print(f"❌ 분석 실패: {result.get('error', '알 수 없는 오류')}")
            return
            
        print("\n" + "="*60)
        print("🎯 감정 분석 종합 결과")
        print("="*60)
        
        # 기본 정보
        summary = result['emotion_summary']
        print(f"👤 사용자: {result['user_id']}")
        print(f"📅 분석 시간: {result['analysis_timestamp']}")
        
        # 현재 감정 상태
        print(f"\n{summary['mood_emoji']} 현재 감정 상태: {summary['current_mood']}")
        print(f"📊 감정 점수: {summary['emotion_score']:.2f}")
        print(f"😰 스트레스 레벨: {summary['stress_level']}")
        print(f"😴 피로도 지수: {summary['fatigue_index']:.2f}")
        
        # 개인화된 피드백
        feedback = result['personalized_feedback']
        if feedback.get('recommendations'):
            print(f"\n💡 맞춤 추천:")
            for i, rec in enumerate(feedback['recommendations'][:3], 1):
                print(f"   {i}. {rec}")
        
        if feedback.get('action_items'):
            print(f"\n✅ 실천 방안:")
            for i, action in enumerate(feedback['action_items'], 1):
                print(f"   {i}. {action}")
        
        if feedback.get('insights'):
            print(f"\n🔍 인사이트:")
            for i, insight in enumerate(feedback['insights'], 1):
                print(f"   {i}. {insight}")
        
        # 데이터 품질
        quality = result['data_quality']
        print(f"\n📊 데이터 품질:")
        print(f"   📺 YouTube 항목: {quality['youtube_items']}개")
        print(f"   📅 Calendar 이벤트: {len(quality['calendar_events'])}일")
        print(f"   📈 히스토리: {quality['history_available']}개 분석")
        
        print("="*60)

def main():
    """메인 실행 함수"""
    system = CompleteEmotionSystem()
    
    # 전체 분석 실행
    result = system.run_complete_analysis()
    
    # 결과 출력
    system.print_beautiful_summary(result)
    
    # 결과 파일 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"/Users/kjw/emotion-analysis-system/config/complete_analysis_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 상세 결과 저장: {result_file}")
    
    return result

if __name__ == "__main__":
    main()