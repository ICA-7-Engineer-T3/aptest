"""
감정 분석 엔진
- YouTube와 Calendar 데이터를 분석해서 감정 상태 추정
- Time Decay와 Forgetting Factor 적용
- 실제 수집된 데이터 기반 분석
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class EmotionAnalysisEngine:
    """감정 분석을 수행하는 클래스"""
    
    def __init__(self):
        # Time Decay 파라미터 (λ - 람다값)
        self.lambda_decay = 0.1  # 하루에 10%씩 영향도 감소
        
        # Forgetting Factor (망각 인수)
        self.forgetting_factor = 0.05  # 하루에 5%씩 가중치 감소
        
        # 감정 키워드 사전 (실제 데이터에 맞게 확장)
        self.emotion_keywords = {
            'positive': ['힐링', '치유', '행복', '즐거', '웃음', '재미', '놀이', '게임', '음악', '재즈', 'jazz', 
                        '영화', '리뷰', '찐뷰', '네고막', '책임', '연습', '베이스'],
            'negative': ['스트레스', '피곤', '힘들', '우울', '불안', '걱정', '급', '재해'],
            'neutral': ['정보', '뉴스', '공부', '학습', '회의', '센터', '풋살']
        }
        
        # 관심사 카테고리 분류 (실제 데이터 반영)
        self.interest_categories = {
            'entertainment': ['영화', '리뷰', '게임', '음악', '재즈', 'jazz', '찐뷰', '네고막', '애니'],
            'lifestyle': ['힐링', '센터', '연습', '풋살', '베이스', '강남'],
            'education': ['공부', '학습', '정보', '책임'],
            'social': ['모임', '회의', '만남', '앱']
        }
    
    def analyze_youtube_emotions(self, youtube_data: Dict) -> Dict:
        """YouTube 데이터에서 감정 성향 분석"""
        print("📺 YouTube 감정 분석 중...")
        
        # 구독 채널 분석
        subscriptions = youtube_data.get('subscriptions', [])
        liked_videos = youtube_data.get('liked_videos', [])
        
        emotion_scores = {'positive': 0, 'negative': 0, 'neutral': 0}
        interests = {'entertainment': 0, 'lifestyle': 0, 'education': 0, 'social': 0}
        
        # 구독 채널명 분석
        for sub in subscriptions:
            channel_name = sub['channel_name'].lower()
            subscribed_date = sub['subscribed_at']
            
            # 시간 가중치 계산 (최근일수록 높은 가중치)
            days_ago = self._calculate_days_ago(subscribed_date)
            time_weight = math.exp(-self.lambda_decay * days_ago)
            
            # 감정 분석
            for emotion, keywords in self.emotion_keywords.items():
                for keyword in keywords:
                    if keyword in channel_name:
                        emotion_scores[emotion] += time_weight
                        
            # 관심사 분석
            for category, keywords in self.interest_categories.items():
                for keyword in keywords:
                    if keyword in channel_name:
                        interests[category] += time_weight
        
        # 좋아요한 동영상 제목 분석
        for video in liked_videos:
            title = video['title'].lower()
            published_date = video['published_at']
            
            days_ago = self._calculate_days_ago(published_date)
            time_weight = math.exp(-self.lambda_decay * days_ago)
            
            # 감정 키워드 분석
            for emotion, keywords in self.emotion_keywords.items():
                for keyword in keywords:
                    if keyword in title:
                        emotion_scores[emotion] += time_weight * 1.5  # 좋아요는 더 높은 가중치
        
        # 정규화
        total_emotion = sum(emotion_scores.values())
        if total_emotion > 0:
            emotion_scores = {k: v/total_emotion for k, v in emotion_scores.items()}
            
        total_interest = sum(interests.values())
        if total_interest > 0:
            interests = {k: v/total_interest for k, v in interests.items()}
        
        print(f"   😊 긍정 성향: {emotion_scores['positive']:.2f}")
        print(f"   😔 부정 성향: {emotion_scores['negative']:.2f}")
        print(f"   😐 중립 성향: {emotion_scores['neutral']:.2f}")
        
        return {
            'emotion_scores': emotion_scores,
            'interests': interests,
            'total_channels': len(subscriptions),
            'total_liked': len(liked_videos)
        }
    
    def analyze_calendar_fatigue(self, calendar_data: Dict) -> Dict:
        """Calendar 데이터에서 피로도 분석"""
        print("📅 Calendar 피로도 분석 중...")
        
        events = calendar_data.get('events', [])
        schedule_analysis = calendar_data.get('schedule_analysis', {})
        
        if not events:
            return {'fatigue_index': 0, 'stress_level': 'low'}
        
        # 피로도 계산 변수들
        daily_counts = {}
        time_distribution = {'morning': 0, 'afternoon': 0, 'evening': 0, 'night': 0}
        
        for event in events:
            date = event['start_date']
            time_str = event['start_time']
            
            # 날짜별 일정 카운트
            daily_counts[date] = daily_counts.get(date, 0) + 1
            
            # 시간대별 분포 (종일 일정이 아닌 경우)
            if time_str != "종일" and ":" in time_str:
                hour = int(time_str.split(':')[0])
                if 6 <= hour < 12:
                    time_distribution['morning'] += 1
                elif 12 <= hour < 18:
                    time_distribution['afternoon'] += 1
                elif 18 <= hour < 22:
                    time_distribution['evening'] += 1
                else:
                    time_distribution['night'] += 1
        
        # 피로도 지수 계산
        days_with_events = len(daily_counts)
        if days_with_events > 0:
            # 1. 일정 밀도 (Fatigue_density)
            total_events = len(events)
            fatigue_density = total_events / days_with_events
            
            # 2. 일정 간격 피로도 (연속된 일정이 많을수록 피로도 증가)
            max_daily_events = max(daily_counts.values()) if daily_counts else 0
            fatigue_gap = max_daily_events / 10.0  # 10개 이상이면 최대
            
            # 3. 시간대 피로도 (밤 일정이 많을수록 피로도 증가)
            total_timed_events = sum(time_distribution.values())
            if total_timed_events > 0:
                night_ratio = time_distribution['night'] / total_timed_events
                fatigue_time = night_ratio
            else:
                fatigue_time = 0
            
            # 전체 피로도 지수 (가중 평균)
            alpha, beta, gamma = 0.5, 0.3, 0.2  # 가중치
            fatigue_index = (alpha * fatigue_density + 
                           beta * fatigue_gap + 
                           gamma * fatigue_time)
        else:
            fatigue_index = 0
        
        # 스트레스 레벨 결정
        if fatigue_index > 2.0:
            stress_level = 'high'
        elif fatigue_index > 1.0:
            stress_level = 'medium'
        else:
            stress_level = 'low'
        
        print(f"   📊 피로도 지수: {fatigue_index:.2f}")
        print(f"   😰 스트레스 레벨: {stress_level}")
        print(f"   🌙 밤 일정 비율: {time_distribution['night']}/{sum(time_distribution.values()) if sum(time_distribution.values()) > 0 else 1}")
        
        return {
            'fatigue_index': fatigue_index,
            'stress_level': stress_level,
            'daily_counts': daily_counts,
            'time_distribution': time_distribution,
            'max_daily_events': max_daily_events
        }
    
    def calculate_overall_emotion(self, youtube_analysis: Dict, calendar_analysis: Dict) -> Dict:
        """전체적인 감정 상태 계산"""
        print("🎯 전체 감정 상태 분석 중...")
        
        # YouTube 감정 점수
        yt_emotions = youtube_analysis['emotion_scores']
        yt_positive = yt_emotions.get('positive', 0)
        yt_negative = yt_emotions.get('negative', 0)
        
        # Calendar 스트레스
        stress_level = calendar_analysis['stress_level']
        stress_impact = {'low': 0.1, 'medium': 0.3, 'high': 0.5}[stress_level]
        
        # 전체 감정 점수 계산
        base_emotion = yt_positive - yt_negative
        stress_adjusted_emotion = base_emotion - stress_impact
        
        # 감정 상태 분류
        if stress_adjusted_emotion > 0.3:
            emotion_state = "매우 긍정적"
            mood_emoji = "😊"
        elif stress_adjusted_emotion > 0.1:
            emotion_state = "긍정적"
            mood_emoji = "🙂"
        elif stress_adjusted_emotion > -0.1:
            emotion_state = "보통"
            mood_emoji = "😐"
        elif stress_adjusted_emotion > -0.3:
            emotion_state = "다소 부정적"
            mood_emoji = "😔"
        else:
            emotion_state = "부정적"
            mood_emoji = "😞"
        
        # 관심사 기반 추천
        top_interest = max(youtube_analysis['interests'].items(), key=lambda x: x[1])
        
        print(f"   {mood_emoji} 감정 상태: {emotion_state}")
        print(f"   🎯 주요 관심사: {top_interest[0]}")
        
        return {
            'emotion_score': stress_adjusted_emotion,
            'emotion_state': emotion_state,
            'mood_emoji': mood_emoji,
            'top_interest': top_interest[0],
            'recommendations': self._generate_recommendations(emotion_state, stress_level, top_interest[0])
        }
    
    def _calculate_days_ago(self, date_str: str) -> int:
        """날짜로부터 며칠 전인지 계산"""
        try:
            if len(date_str) == 10:  # YYYY-MM-DD 형식
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            else:  # ISO 형식
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            days_ago = (datetime.now() - date_obj).days
            return max(0, days_ago)
        except:
            return 0
    
    def _generate_recommendations(self, emotion_state: str, stress_level: str, interest: str) -> List[str]:
        """상태 기반 맞춤형 추천"""
        recommendations = []
        
        if stress_level == 'high':
            recommendations.append("😌 휴식이 필요한 시간입니다. 잠시 일정을 조정해보세요.")
            
        if '부정적' in emotion_state:
            if interest == 'entertainment':
                recommendations.append("🎬 좋아하는 영화나 음악으로 기분 전환을 해보세요.")
            elif interest == 'lifestyle':
                recommendations.append("🧘 힐링센터나 운동으로 스트레스를 풀어보세요.")
        
        if emotion_state == "매우 긍정적":
            recommendations.append("✨ 좋은 컨디션이네요! 새로운 도전을 해보는 것도 좋겠어요.")
            
        return recommendations

def test_emotion_analysis():
    """실제 수집된 데이터로 감정 분석 테스트"""
    print("=== 감정 분석 엔진 테스트 ===")
    
    # 실제 수집된 데이터 로드
    try:
        with open('/Users/kjw/emotion-analysis-system/config/collected_data_20260202_194351.json', 'r', encoding='utf-8') as f:
            collected_data = json.load(f)
    except FileNotFoundError:
        print("❌ 수집된 데이터 파일을 찾을 수 없습니다.")
        return False
    
    engine = EmotionAnalysisEngine()
    
    # YouTube 데이터 분석
    youtube_analysis = engine.analyze_youtube_emotions(collected_data['youtube_data'])
    
    # Calendar 데이터 분석
    calendar_analysis = engine.analyze_calendar_fatigue(collected_data['calendar_data'])
    
    # 전체 감정 상태 계산
    overall_emotion = engine.calculate_overall_emotion(youtube_analysis, calendar_analysis)
    
    # 결과 요약
    print("\n" + "="*50)
    print("🧠 감정 분석 결과")
    print("="*50)
    
    print(f"📺 YouTube 분석:")
    print(f"   📊 감정 점수: {youtube_analysis['emotion_scores']}")
    print(f"   🎯 관심사: {youtube_analysis['interests']}")
    
    print(f"\n📅 Calendar 분석:")
    print(f"   😰 스트레스 레벨: {calendar_analysis['stress_level']}")
    print(f"   📊 피로도 지수: {calendar_analysis['fatigue_index']:.2f}")
    
    print(f"\n🎯 종합 결과:")
    print(f"   {overall_emotion['mood_emoji']} 현재 감정: {overall_emotion['emotion_state']}")
    print(f"   🎯 주요 관심사: {overall_emotion['top_interest']}")
    
    print(f"\n💡 맞춤 추천:")
    for i, rec in enumerate(overall_emotion['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # 분석 결과 저장
    analysis_result = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': collected_data['user_id'],
        'youtube_analysis': youtube_analysis,
        'calendar_analysis': calendar_analysis,
        'overall_emotion': overall_emotion
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"/Users/kjw/emotion-analysis-system/config/emotion_analysis_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 분석 결과 저장: {result_file}")
    print("="*50)
    
    return True

    def analyze_youtube_data(self, youtube_data: Dict) -> Dict:
        """YouTube 데이터 분석 (통합 인터페이스)"""
        return self.analyze_youtube_emotions(youtube_data)
    
    def analyze_calendar_data(self, calendar_data: Dict) -> Dict:
        """Calendar 데이터 분석 (통합 인터페이스)"""
        return self.analyze_calendar_fatigue(calendar_data)
    
    def get_comprehensive_analysis(self, youtube_data: Dict, calendar_data: Dict) -> Dict:
        """YouTube와 Calendar 데이터를 종합 분석"""
        youtube_result = self.analyze_youtube_emotions(youtube_data)
        calendar_result = self.analyze_calendar_fatigue(calendar_data)
        
        # 전체 감정 점수 계산
        youtube_score = youtube_result.get('overall_emotion_score', 0.0)
        calendar_fatigue = calendar_result.get('fatigue_level', 0.0)
        
        # 종합 점수 (YouTube 감정에서 Calendar 피로도 차감)
        overall_score = youtube_score - (calendar_fatigue * 0.5)
        overall_score = max(-1.0, min(1.0, overall_score))  # -1 ~ 1 범위로 제한
        
        # 감정 상태 분류
        if overall_score > 0.3:
            emotion_state = "긍정적"
            emoji = "😊"
        elif overall_score < -0.3:
            emotion_state = "부정적"
            emoji = "😔"
        else:
            emotion_state = "중성적"
            emoji = "😐"
        
        return {
            "overall_emotion": overall_score,
            "emotion_state": emotion_state,
            "emoji": emoji,
            "youtube_analysis": youtube_result,
            "calendar_analysis": calendar_result,
            "trend_analysis": {
                "entertainment_level": youtube_result.get('interests', {}).get('entertainment', 0),
                "stress_level": calendar_fatigue,
                "work_life_balance": 1.0 - calendar_fatigue
            },
            "summary": f"{emoji} 전체적으로 {emotion_state} 감정 상태입니다. "
                      f"감정 점수: {overall_score:.2f}, 피로도: {calendar_fatigue:.2f}"
        }

if __name__ == "__main__":
    test_emotion_analysis()