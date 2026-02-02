"""
통합 데이터 수집기
- YouTube + Calendar 데이터를 한번에 수집
- 감정 분석을 위한 통합 데이터 구조 생성
"""

import json
import sys
import os
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append('/Users/kjw/emotion-analysis-system/src')

from api.youtube_collector import YouTubeCollector
from api.calendar_collector import CalendarCollector

class IntegratedCollector:
    """YouTube + Calendar 통합 데이터 수집"""
    
    def __init__(self, user_id="김재원"):
        self.user_id = user_id
        self.youtube_collector = YouTubeCollector()
        self.calendar_collector = CalendarCollector()
        
    def collect_all_data(self):
        """모든 데이터 수집"""
        print("🔄 통합 데이터 수집 시작...")
        
        # 수집된 데이터를 저장할 구조
        integrated_data = {
            'user_id': self.user_id,
            'collection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'youtube_data': {},
            'calendar_data': {},
            'analysis_ready': False
        }
        
        # YouTube 데이터 수집
        print("\n📺 YouTube 데이터 수집 중...")
        if self.youtube_collector.connect():
            # 구독 채널
            subscriptions = self.youtube_collector.get_subscriptions(10)
            # 좋아요 동영상  
            liked_videos = self.youtube_collector.get_liked_videos(10)
            
            integrated_data['youtube_data'] = {
                'subscriptions': subscriptions,
                'liked_videos': liked_videos,
                'subscription_count': len(subscriptions),
                'liked_count': len(liked_videos)
            }
            print("✅ YouTube 데이터 수집 완료!")
        else:
            print("❌ YouTube 데이터 수집 실패")
            
        # Calendar 데이터 수집
        print("\n📅 Calendar 데이터 수집 중...")
        if self.calendar_collector.connect():
            # 최근 일정
            events = self.calendar_collector.get_recent_events(14, 20)  # 2주간 20개
            # 일정 밀도 분석
            analysis = self.calendar_collector.analyze_schedule_density(events)
            
            integrated_data['calendar_data'] = {
                'events': events,
                'schedule_analysis': analysis,
                'event_count': len(events)
            }
            print("✅ Calendar 데이터 수집 완료!")
        else:
            print("❌ Calendar 데이터 수집 실패")
            
        # 수집 상태 체크
        youtube_ok = len(integrated_data['youtube_data']) > 0
        calendar_ok = len(integrated_data['calendar_data']) > 0
        integrated_data['analysis_ready'] = youtube_ok and calendar_ok
        
        return integrated_data
    
    def save_data(self, data, filename=None):
        """수집된 데이터를 JSON 파일로 저장"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"/Users/kjw/emotion-analysis-system/config/collected_data_{timestamp}.json"
                
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"💾 데이터 저장 완료: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 데이터 저장 실패: {e}")
            return None
    
    def print_summary(self, data):
        """수집 결과 요약 출력"""
        print("\n" + "="*50)
        print("📊 데이터 수집 결과 요약")
        print("="*50)
        
        print(f"👤 사용자: {data['user_id']}")
        print(f"📅 수집 시간: {data['collection_date']}")
        
        # YouTube 요약
        yt_data = data.get('youtube_data', {})
        print(f"\n📺 YouTube 데이터:")
        print(f"   📌 구독 채널: {yt_data.get('subscription_count', 0)}개")
        print(f"   👍 좋아요 동영상: {yt_data.get('liked_count', 0)}개")
        
        # Calendar 요약  
        cal_data = data.get('calendar_data', {})
        analysis = cal_data.get('schedule_analysis', {})
        print(f"\n📅 Calendar 데이터:")
        print(f"   📋 최근 일정: {cal_data.get('event_count', 0)}개")
        if analysis:
            print(f"   📊 평균 일정/일: {analysis.get('avg_per_day', 0):.1f}개")
            print(f"   😴 추정 피로도: {analysis.get('fatigue_level', 'N/A')}")
        
        # 분석 준비 상태
        ready = "✅ 준비완료" if data['analysis_ready'] else "❌ 데이터 부족"
        print(f"\n🎯 감정분석 준비상태: {ready}")
        print("="*50)

def test_integrated_collection():
    """통합 데이터 수집 테스트"""
    collector = IntegratedCollector()
    
    # 데이터 수집
    data = collector.collect_all_data()
    
    # 결과 요약
    collector.print_summary(data)
    
    # 데이터 저장
    saved_file = collector.save_data(data)
    
    return data, saved_file

if __name__ == "__main__":
    print("=== 통합 데이터 수집 테스트 ===")
    data, file = test_integrated_collection()
    
    if data['analysis_ready']:
        print("\n🎉 다음 단계: 감정 분석 알고리즘 준비!")
    else:
        print("\n⚠️ 데이터 보완 필요")