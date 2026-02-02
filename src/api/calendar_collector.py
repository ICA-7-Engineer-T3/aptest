"""
Google Calendar 데이터 수집기
- Calendar API를 사용해서 일정 데이터 가져오기
- 일정 밀도와 피로도 분석을 위한 기초 데이터 수집
"""

import json
import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build

class CalendarCollector:
    """Google Calendar 데이터를 수집하는 클래스"""
    
    def __init__(self):
        self.service = None
        
    def connect(self):
        """Calendar API에 연결 (저장된 토큰 우선 사용)"""
        try:
            print("📅 Calendar API 연결 중...")
            
            # 먼저 저장된 토큰으로 시도
            token_file = "/Users/kjw/emotion-analysis-system/config/token.json"
            if os.path.exists(token_file):
                print("🎫 저장된 토큰 사용...")
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(token_file)
                
                # Calendar API 서비스 생성
                self.service = build('calendar', 'v3', credentials=creds)
                print("✅ Calendar API 연결 성공! (토큰 재사용)")
                return True
            
            # 토큰이 없으면 새로 인증
            from google_auth_oauthlib.flow import InstalledAppFlow
            credentials_file = "/Users/kjw/emotion-analysis-system/config/google_credentials.json"
            scopes = ['https://www.googleapis.com/auth/calendar.readonly']
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=8080)
            
            # Calendar API 서비스 생성
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Calendar API 연결 성공! (새 인증)")
            return True
            
        except Exception as e:
            print(f"❌ Calendar API 연결 실패: {e}")
            return False
    
    def get_calendars_list(self):
        """내 캘린더 목록 가져오기"""
        try:
            print("📋 캘린더 목록 가져오는 중...")
            
            request = self.service.calendarList().list()
            response = request.execute()
            
            calendars = []
            for calendar in response['items']:
                cal_info = {
                    'id': calendar['id'],
                    'name': calendar['summary'],
                    'primary': calendar.get('primary', False)
                }
                calendars.append(cal_info)
                
            print(f"✅ 캘린더 {len(calendars)}개 발견!")
            
            # 결과 미리보기
            for i, cal in enumerate(calendars[:3], 1):
                primary = " (기본)" if cal['primary'] else ""
                print(f"   {i}. {cal['name']}{primary}")
            
            if len(calendars) > 3:
                print(f"   ... 외 {len(calendars)-3}개")
                
            return calendars
            
        except Exception as e:
            print(f"❌ 캘린더 목록 가져오기 실패: {e}")
            return []
    
    def get_recent_events(self, days_back=7, max_results=10):
        """최근 일정 가져오기"""
        try:
            print(f"📅 최근 {days_back}일간 일정 {max_results}개 가져오는 중...")
            
            # 시간 범위 설정 (최근 7일)
            now = datetime.utcnow()
            time_min = (now - timedelta(days=days_back)).isoformat() + 'Z'
            time_max = now.isoformat() + 'Z'
            
            request = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            )
            response = request.execute()
            
            events = []
            for item in response['items']:
                # 시작 시간 처리
                start = item['start'].get('dateTime', item['start'].get('date'))
                if 'T' in start:
                    start_date = start[:10]
                    start_time = start[11:16]
                else:
                    start_date = start
                    start_time = "종일"
                
                event_info = {
                    'title': item.get('summary', '제목 없음'),
                    'start_date': start_date,
                    'start_time': start_time,
                    'description': item.get('description', ''),
                    'location': item.get('location', '')
                }
                events.append(event_info)
                
            print(f"✅ 일정 {len(events)}개 수집 완료!")
            
            # 결과 미리보기
            for i, event in enumerate(events[:3], 1):
                print(f"   {i}. {event['title'][:30]}... ({event['start_date']} {event['start_time']})")
            
            if len(events) > 3:
                print(f"   ... 외 {len(events)-3}개")
                
            return events
            
        except Exception as e:
            print(f"❌ 일정 가져오기 실패: {e}")
            return []
    
    def analyze_schedule_density(self, events):
        """일정 밀도 분석 (하루별 일정 개수)"""
        try:
            print("📊 일정 밀도 분석 중...")
            
            # 날짜별 일정 개수 계산
            daily_counts = {}
            for event in events:
                date = event['start_date']
                daily_counts[date] = daily_counts.get(date, 0) + 1
            
            # 평균 계산
            if daily_counts:
                total_events = sum(daily_counts.values())
                total_days = len(daily_counts)
                avg_events_per_day = total_events / total_days
                
                max_day = max(daily_counts, key=daily_counts.get)
                max_events = daily_counts[max_day]
                
                print(f"✅ 일정 밀도 분석 완료!")
                print(f"   📊 평균 일정/일: {avg_events_per_day:.1f}개")
                print(f"   📈 최대 일정: {max_events}개 ({max_day})")
                
                # 피로도 추정 (간단한 기준)
                if avg_events_per_day > 5:
                    fatigue_level = "높음"
                elif avg_events_per_day > 3:
                    fatigue_level = "중간"
                else:
                    fatigue_level = "낮음"
                    
                print(f"   😴 추정 피로도: {fatigue_level}")
                
                return {
                    'daily_counts': daily_counts,
                    'avg_per_day': avg_events_per_day,
                    'max_events': max_events,
                    'max_day': max_day,
                    'fatigue_level': fatigue_level
                }
            else:
                print("📊 분석할 일정이 없습니다")
                return {}
                
        except Exception as e:
            print(f"❌ 밀도 분석 실패: {e}")
            return {}

def test_calendar_api():
    """Calendar API 테스트 실행"""
    collector = CalendarCollector()
    
    # 1단계: API 연결
    if not collector.connect():
        return False
        
    # 2단계: 캘린더 목록 확인
    calendars = collector.get_calendars_list()
    if not calendars:
        print("⚠️ 사용 가능한 캘린더가 없습니다")
        return True  # 에러가 아닐 수 있음
        
    # 3단계: 최근 일정 가져오기
    events = collector.get_recent_events(7, 10)
    
    # 4단계: 일정 밀도 분석
    if events:
        analysis = collector.analyze_schedule_density(events)
        
    print(f"\n🎉 테스트 완료!")
    print(f"   📋 캘린더: {len(calendars)}개")
    print(f"   📅 일정: {len(events)}개")
    
    return True

if __name__ == "__main__":
    print("=== Google Calendar 데이터 수집 테스트 ===")
    result = test_calendar_api()
    
    if result:
        print("🎉 모든 테스트 통과!")
    else:
        print("❌ 테스트 실패")