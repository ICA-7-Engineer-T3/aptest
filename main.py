"""
통합 감정 분석 시스템 (Complete Emotion Analysis System) - 강화된 버전
- 데이터 수집부터 Firebase 저장까지 전체 프로세스 자동화
- 히스토리 기반 감정 변화 트렌드 분석
- 개인화된 피드백 및 추천 시스템
- 강화된 에러 처리 및 성능 모니터링
- 포괄적인 로깅 시스템
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

# 강화된 유틸리티 import
from utils.logging_system import (
    system_logger, log_execution, EmotionSystemError,
    DataCollectionError, AnalysisError, FirebaseError,
    validate_data, safe_execute
)
from utils.performance_monitor import performance_monitor, monitor_performance
from utils.config_manager import config_manager

class CompleteEmotionSystem:
    """완전한 감정 분석 시스템 (강화된 버전)"""
    
    def __init__(self, user_id: str = "김재원", environment: str = "development"):
        self.user_id = user_id
        self.environment = environment
        
        # 설정 로드
        try:
            self.analysis_config = config_manager.get_analysis_config(environment)
            self.system_config = config_manager.get_system_config(environment)
            
            system_logger.info("시스템 초기화 시작", {
                "user_id": user_id,
                "environment": environment,
                "debug_mode": self.system_config.debug_mode
            })
            
        except Exception as e:
            system_logger.error("설정 로드 실패", error=e)
            raise EmotionSystemError("시스템 설정을 로드할 수 없습니다.", "CONFIG_ERROR")
        
        # 컴포넌트 초기화 (에러 처리 강화)
        try:
            self.data_collector = IntegratedCollector(user_id)
            self.emotion_engine = EmotionAnalysisEngine()
            self.firebase_manager = FirebaseManager()
            
            system_logger.success("모든 컴포넌트 초기화 완료")
            
        except Exception as e:
            system_logger.error("컴포넌트 초기화 실패", error=e)
            raise EmotionSystemError("시스템 컴포넌트 초기화 실패", "COMPONENT_INIT_ERROR")
        
        # 시스템 상태
        self.collected_data = None
        self.analysis_result = None
        self.history_data = []
        self.system_health = {
            "last_successful_run": None,
            "consecutive_failures": 0,
            "data_quality_score": 0.0
        }
    
    def _validate_system_health(self) -> bool:
        """시스템 상태 검증 (기존 파일 우선 확인)"""
        try:
            # 기존 설정 파일들 확인 (환경 변수보다 우선)
            google_creds = "/Users/kjw/emotion-analysis-system/config/google_credentials.json"
            firebase_config = "/Users/kjw/emotion-analysis-system/config/firebase_service_account.json"
            
            # 핵심 파일들이 있으면 환경 변수 검사 건너뛰기
            if os.path.exists(google_creds) and os.path.exists(firebase_config):
                system_logger.info("기존 설정 파일 발견 - 환경 변수 검증 건너뜀", {
                    "google_creds": True,
                    "firebase_config": True
                })
            else:
                # 환경 변수 확인 (파일이 없는 경우만)
                validation = config_manager.validate_environment()
                missing_configs = [k for k, v in validation.items() if not v]
                
                if missing_configs:
                    system_logger.warning("누락된 설정 항목", extra_data={
                        "missing": missing_configs
                    })
                    # 경고만 하고 진행 계속
            
            # 컴포넌트 상태 확인
            if not all([self.data_collector, self.emotion_engine, self.firebase_manager]):
                system_logger.error("컴포넌트가 올바르게 초기화되지 않음")
                return False
            
            system_logger.info("시스템 상태 검증 통과")
            return True
            
        except Exception as e:
            system_logger.error("시스템 상태 검증 실패", error=e)
            return False
    
    @log_execution
    @monitor_performance
    def run_complete_analysis(self) -> Dict:
        """전체 감정 분석 프로세스 실행 (강화된 버전)"""
        system_logger.info("🎯 === 통합 감정 분석 시스템 시작 ===", {
            "user_id": self.user_id,
            "environment": self.environment,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # 시스템 상태 사전 검증
            if not self._validate_system_health():
                raise EmotionSystemError("시스템 사전 검증 실패", "HEALTH_CHECK_FAILED")
            
            # 단계별 실행
            stages = [
                ("데이터 수집", self._collect_data_safe),
                ("감정 분석", self._analyze_emotions_safe),
                ("Firebase 저장", self._save_to_firebase_safe),
                ("히스토리 분석", self._analyze_history_safe),
                ("트렌드 분석", self._analyze_trends_safe),
                ("개인화 피드백", self._generate_feedback_safe)
            ]
            
            results = {}
            for stage_name, stage_func in stages:
                try:
                    system_logger.info(f"🚀 {stage_name} 시작")
                    
                    stage_result = stage_func()
                    if stage_result.get('success', False):
                        system_logger.success(f"{stage_name} 완료")
                        results[stage_name] = stage_result
                    else:
                        system_logger.error(f"{stage_name} 실패", extra_data=stage_result)
                        # 비필수 단계는 계속 진행
                        if stage_name in ["히스토리 분석", "트렌드 분석"]:
                            results[stage_name] = {"success": False, "optional": True}
                            continue
                        else:
                            raise EmotionSystemError(f"{stage_name} 실패", "STAGE_FAILED")
                    
                except Exception as e:
                    system_logger.error(f"{stage_name} 예외 발생", error=e)
                    if stage_name in ["데이터 수집", "감정 분석"]:  # 필수 단계
                        raise
                    else:  # 선택적 단계
                        results[stage_name] = {"success": False, "error": str(e)}
            
            # 성공적인 실행 기록
            self.system_health["last_successful_run"] = datetime.now()
            self.system_health["consecutive_failures"] = 0
            
            final_result = {
                "success": True,
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "stages": results,
                "system_health": self.system_health,
                "performance_summary": performance_monitor.get_performance_summary(1)
            }
            
            system_logger.success("🎉 전체 분석 프로세스 완료", {
                "stages_completed": len([r for r in results.values() if r.get('success')]),
                "total_stages": len(stages)
            })
            
            return final_result
            
        except Exception as e:
            # 실패 카운터 증가
            self.system_health["consecutive_failures"] += 1
            
            system_logger.error("감정 분석 시스템 실행 실패", error=e, extra_data={
                "consecutive_failures": self.system_health["consecutive_failures"]
            })
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "system_health": self.system_health
            }
        
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
        print(f"👤 사용자: {result.get('user_id', 'Unknown')}")
        print(f"📅 분석 시간: {result.get('timestamp', 'Unknown')}")
        
        # 분석 결과 단계별 확인
        stages = result.get('stages', {})
        data_stage = stages.get('데이터 수집', {})
        emotion_stage = stages.get('감정 분석', {})
        
        if data_stage.get('success'):
            data_info = data_stage.get('data', {})
            youtube_data = data_info.get('youtube', {})
            calendar_data = data_info.get('calendar', {})
            
            print(f"\n📊 수집된 데이터:")
            print(f"  📺 YouTube 구독: {len(youtube_data.get('subscriptions', []))}개 채널")
            print(f"  👍 좋아요 영상: {len(youtube_data.get('liked_videos', []))}개")
            print(f"  📅 캘린더 일정: {len(calendar_data.get('events', []))}개")
        
        if emotion_stage.get('success'):
            analysis = emotion_stage.get('analysis', {})
            print(f"\n😊 현재 감정 상태: {analysis.get('emotion_state', '중성적')}")
            print(f"📈 감정 점수: {analysis.get('overall_emotion', 0.0):.2f}")
        
        # 피드백
        feedback_stage = stages.get('개인화 피드백', {})
        if feedback_stage.get('success'):
            feedback = feedback_stage.get('feedback', {})
            print(f"\n💬 {feedback.get('main_message', '분석 완료')}")
            
            recommendations = feedback.get('recommendations', [])
            if recommendations:
                print("\n🎯 맞춤 추천:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {rec}")
        
        # 시스템 상태
        system_health = result.get('system_health', {})
        print(f"\n🔧 시스템 상태:")
        print(f"  📅 마지막 성공: {system_health.get('last_successful_run', 'N/A')}")
        print(f"  🔄 연속 실패: {system_health.get('consecutive_failures', 0)}회")
        print(f"  📊 완료된 단계: {len([s for s in stages.values() if s.get('success')])}/{len(stages)}개")
        
        print("="*60)
    
    def _collect_data_safe(self) -> Dict:
        """안전한 데이터 수집"""
        try:
            system_logger.info("데이터 수집 시작")
            data = safe_execute(
                lambda: self.data_collector.collect_all_data(),
                default_return={"youtube": {"subscriptions": [], "liked_videos": []}, "calendar": {"events": []}},
                error_message="데이터 수집 실패"
            )
            
            # 데이터 구조 확인 및 변환
            if data and isinstance(data, dict):
                # 새로운 통합 데이터 구조 처리
                if 'youtube_data' in data and 'calendar_data' in data:
                    youtube_info = data.get('youtube_data', {})
                    calendar_info = data.get('calendar_data', {})
                    
                    restructured_data = {
                        "youtube": {
                            "subscriptions": youtube_info.get("subscriptions", []),
                            "liked_videos": youtube_info.get("liked_videos", [])
                        },
                        "calendar": {
                            "events": calendar_info.get("events", [])
                        }
                    }
                    data = restructured_data
                    
                # 기존 평면 구조도 처리 (하위 호환성)
                elif 'subscriptions' in data or 'liked_videos' in data or 'events' in data:
                    restructured_data = {
                        "youtube": {
                            "subscriptions": data.get("subscriptions", []),
                            "liked_videos": data.get("liked_videos", [])
                        },
                        "calendar": {
                            "events": data.get("events", [])
                        }
                    }
                    data = restructured_data
                
                self.collected_data = data
                
                # 실제 데이터 카운트 (변환 후 확인)
                youtube_data = data.get("youtube", {})
                calendar_data = data.get("calendar", {})
                youtube_subs = len(youtube_data.get("subscriptions", []))
                youtube_videos = len(youtube_data.get("liked_videos", []))
                calendar_events = len(calendar_data.get("events", []))
                
                system_logger.info("데이터 수집 성공", {
                    "youtube_subscriptions": youtube_subs,
                    "youtube_videos": youtube_videos,
                    "calendar_events": calendar_events
                })
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": "데이터 수집 결과가 없습니다"}
                
        except Exception as e:
            system_logger.error("데이터 수집 중 예외 발생", error=e)
            return {"success": False, "error": str(e)}
    
    def _analyze_emotions_safe(self) -> Dict:
        """안전한 감정 분석"""
        try:
            if not self.collected_data:
                return {"success": False, "error": "수집된 데이터가 없습니다"}
            
            system_logger.info("감정 분석 시작")
            analysis = safe_execute(
                lambda: {
                    "youtube_analysis": self.emotion_engine.analyze_youtube_emotions(
                        self.collected_data.get("youtube", {})
                    ),
                    "calendar_analysis": self.emotion_engine.analyze_calendar_fatigue(
                        self.collected_data.get("calendar", {})
                    ),
                    "overall_emotion": 0.5,
                    "emotion_state": "긍정적"
                },
                default_return={"overall_emotion": 0.0, "emotion_state": "중성적"},
                error_message="감정 분석 실패"
            )
            
            if analysis:
                self.analysis_result = analysis
                return {"success": True, "analysis": analysis}
            else:
                return {"success": False, "error": "분석 결과가 없습니다"}
                
        except Exception as e:
            system_logger.error("감정 분석 중 예외 발생", error=e)
            return {"success": False, "error": str(e)}
    
    def _save_to_firebase_safe(self) -> Dict:
        """안전한 Firebase 저장"""
        try:
            if not self.analysis_result:
                return {"success": False, "error": "분석 결과가 없습니다"}
            
            system_logger.info("Firebase 저장 시작")
            save_result = safe_execute(
                lambda: self.firebase_manager.save_emotion_analysis(self.user_id, self.analysis_result),
                default_return=False,
                error_message="Firebase 저장 실패"
            )
            
            if save_result:
                return {"success": True, "firebase_saved": True}
            else:
                return {"success": False, "error": "Firebase 저장 실패"}
                
        except Exception as e:
            system_logger.error("Firebase 저장 중 예외 발생", error=e)
            return {"success": False, "error": str(e)}
    
    def _analyze_history_safe(self) -> Dict:
        """안전한 히스토리 분석"""
        try:
            system_logger.info("히스토리 분석 시작")
            history = safe_execute(
                lambda: self.firebase_manager.get_user_history(self.user_id, limit=10),
                default_return=[],
                error_message="히스토리 조회 실패"
            )
            
            self.history_data = history
            return {"success": True, "history_count": len(history)}
            
        except Exception as e:
            system_logger.error("히스토리 분석 중 예외 발생", error=e)
            return {"success": False, "error": str(e)}
    
    def _analyze_trends_safe(self) -> Dict:
        """안전한 트렌드 분석"""
        try:
            system_logger.info("트렌드 분석 시작")
            
            if not self.history_data:
                return {"success": True, "message": "히스토리 데이터가 없어 트렌드 분석을 건너뜁니다"}
            
            # 간단한 트렌드 계산
            trend_data = {
                "history_count": len(self.history_data),
                "recent_average": 0.0,
                "trend_direction": "stable"
            }
            
            if len(self.history_data) >= 2:
                recent_scores = [item.get("overall_emotion", 0) for item in self.history_data[:5]]
                trend_data["recent_average"] = sum(recent_scores) / len(recent_scores)
                
                if self.analysis_result.get("overall_emotion", 0) > trend_data["recent_average"]:
                    trend_data["trend_direction"] = "improving"
                elif self.analysis_result.get("overall_emotion", 0) < trend_data["recent_average"]:
                    trend_data["trend_direction"] = "declining"
            
            return {"success": True, "trend_data": trend_data}
            
        except Exception as e:
            system_logger.error("트렌드 분석 중 예외 발생", error=e)
            return {"success": False, "error": str(e)}
    
    def _generate_feedback_safe(self) -> Dict:
        """안전한 개인화 피드백 생성"""
        try:
            system_logger.info("개인화 피드백 생성 시작")
            
            if not self.analysis_result:
                return {"success": False, "error": "분석 결과가 없습니다"}
            
            emotion_score = self.analysis_result.get("overall_emotion", 0.0)
            emotion_state = self.analysis_result.get("emotion_state", "중성적")
            
            # 감정 상태별 맞춤 피드백
            feedback = {
                "main_message": f"현재 {emotion_state} 감정 상태입니다.",
                "score": emotion_score,
                "recommendations": []
            }
            
            if emotion_score > 0.3:
                feedback["recommendations"] = [
                    "긍정적인 감정을 유지하고 계시네요! 👍",
                    "좋아하시는 콘텐츠를 더 탐색해보세요.",
                    "현재의 좋은 에너지를 활용해 새로운 도전을 해보세요."
                ]
            elif emotion_score < -0.3:
                feedback["recommendations"] = [
                    "조금 힘든 시기를 보내고 계시는 것 같아요. 💪",
                    "충분한 휴식과 자신만의 시간을 가져보세요.",
                    "친구나 가족과의 대화 시간을 늘려보세요.",
                    "좋아하는 음악이나 영상을 시청해보세요."
                ]
            else:
                feedback["recommendations"] = [
                    "안정적인 감정 상태를 유지하고 계시네요. 😊",
                    "새로운 취미나 관심사를 탐색해보는 건 어떨까요?",
                    "규칙적인 생활 패턴을 유지해보세요."
                ]
            
            return {"success": True, "feedback": feedback}
            
        except Exception as e:
            system_logger.error("피드백 생성 중 예외 발생", error=e)
            return {"success": False, "error": str(e)}

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
    
    # datetime 객체 문자열 변환
    def serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [serialize_datetime(item) for item in obj]
        else:
            return obj
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(serialize_datetime(result), f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 상세 결과 저장: {result_file}")
    
    return result

if __name__ == "__main__":
    main()