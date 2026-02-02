"""
YouTube 데이터 수집기
- YouTube API를 사용해서 사용자 데이터 가져오기
- 초보자를 위한 단계별 구현
"""

import json
import os
from googleapiclient.discovery import build

class YouTubeCollector:
    """YouTube 데이터를 수집하는 클래스"""
    
    def __init__(self):
        self.token_file = "/Users/kjw/emotion-analysis-system/config/token.json"
        self.service = None
        
    def connect(self):
        """YouTube API에 연결 (저장된 토큰 우선 사용)"""
        try:
            print("🔗 YouTube API 연결 중...")
            
            # 먼저 저장된 토큰으로 시도
            token_file = "/Users/kjw/emotion-analysis-system/config/token.json"
            if os.path.exists(token_file):
                print("🎫 저장된 토큰 사용...")
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(token_file)
                
                # YouTube API 서비스 생성
                self.service = build('youtube', 'v3', credentials=creds)
                print("✅ YouTube API 연결 성공! (토큰 재사용)")
                return True
            
            # 토큰이 없으면 새로 인증
            from google_auth_oauthlib.flow import InstalledAppFlow
            credentials_file = "/Users/kjw/emotion-analysis-system/config/google_credentials.json"
            scopes = ['https://www.googleapis.com/auth/youtube.readonly']
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=8080)
            
            # YouTube API 서비스 생성
            self.service = build('youtube', 'v3', credentials=creds)
            print("✅ YouTube API 연결 성공! (새 인증)")
            return True
            
        except Exception as e:
            print(f"❌ YouTube API 연결 실패: {e}")
            return False
    
    def test_connection(self):
        """연결 테스트 - 내 채널 정보 가져오기"""
        try:
            print("🧪 YouTube API 테스트 중...")
            
            # 내 채널 정보 요청
            request = self.service.channels().list(
                part="snippet,statistics",
                mine=True
            )
            response = request.execute()
            
            if response['items']:
                channel = response['items'][0]
                print(f"📺 채널명: {channel['snippet']['title']}")
                print(f"📊 구독자 수: {channel['statistics'].get('subscriberCount', '비공개')}")
                print(f"🎥 동영상 수: {channel['statistics'].get('videoCount', '0')}")
                return True
            else:
                print("ℹ️ YouTube 채널이 없거나 비공개 설정입니다")
                return True  # 에러가 아니므로 True 반환
                
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def get_subscriptions(self, max_results=10):
        """구독한 채널 목록 가져오기 (처음에는 10개만)"""
        try:
            print(f"📺 구독 채널 {max_results}개 가져오는 중...")
            
            request = self.service.subscriptions().list(
                part="snippet",
                mine=True,
                maxResults=max_results
            )
            response = request.execute()
            
            subscriptions = []
            for item in response['items']:
                channel_info = {
                    'channel_name': item['snippet']['title'],
                    'channel_id': item['snippet']['resourceId']['channelId'],
                    'subscribed_at': item['snippet']['publishedAt'][:10]  # 날짜만
                }
                subscriptions.append(channel_info)
                
            print(f"✅ 구독 채널 {len(subscriptions)}개 수집 완료!")
            
            # 결과 미리보기
            for i, sub in enumerate(subscriptions[:3], 1):
                print(f"   {i}. {sub['channel_name']} (구독일: {sub['subscribed_at']})")
            
            if len(subscriptions) > 3:
                print(f"   ... 외 {len(subscriptions)-3}개")
                
            return subscriptions
            
        except Exception as e:
            print(f"❌ 구독 채널 가져오기 실패: {e}")
    def get_liked_videos(self, max_results=10):
        """좋아요한 동영상 목록 가져오기"""
        try:
            print(f"👍 좋아요한 동영상 {max_results}개 가져오는 중...")
            
            request = self.service.videos().list(
                part="snippet",
                myRating="like",
                maxResults=max_results
            )
            response = request.execute()
            
            liked_videos = []
            for item in response['items']:
                video_info = {
                    'title': item['snippet']['title'],
                    'video_id': item['id'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'][:10]
                }
                liked_videos.append(video_info)
                
            print(f"✅ 좋아요한 동영상 {len(liked_videos)}개 수집 완료!")
            
            # 결과 미리보기
            for i, video in enumerate(liked_videos[:3], 1):
                print(f"   {i}. {video['title'][:50]}... ({video['channel']})")
            
            if len(liked_videos) > 3:
                print(f"   ... 외 {len(liked_videos)-3}개")
                
            return liked_videos
            
        except Exception as e:
            print(f"❌ 좋아요한 동영상 가져오기 실패: {e}")
            return []

def test_youtube_api():
    """YouTube API 테스트 실행"""
    collector = YouTubeCollector()
    
    # 1단계: API 연결
    if not collector.connect():
        return False
        
    # 2단계: 연결 테스트
    if not collector.test_connection():
        return False
        
    # 3단계: 구독 채널 가져오기
    subscriptions = collector.get_subscriptions(5)  # 처음엔 5개만
    
    # 4단계: 좋아요한 동영상 가져오기
    liked_videos = collector.get_liked_videos(5)
    
    if subscriptions or liked_videos:
        print(f"\n🎉 테스트 완료!")
        print(f"   📺 구독 채널: {len(subscriptions)}개")
        print(f"   👍 좋아요 동영상: {len(liked_videos)}개")
        return True
    else:
        print("\n⚠️ 데이터가 없거나 가져오기 실패")
        return True  # 에러가 아닐 수 있음

if __name__ == "__main__":
    print("=== YouTube 데이터 수집 테스트 ===")
    result = test_youtube_api()
    
    if result:
        print("🎉 모든 테스트 통과!")
    else:
        print("❌ 테스트 실패")