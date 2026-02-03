"""
성능 모니터링 및 최적화 시스템
- 실행 시간 추적
- 메모리 사용량 모니터링
- API 호출 횟수 추적
- 시스템 리소스 분석
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import os

@dataclass
class PerformanceMetric:
    """성능 지표 데이터 클래스"""
    function_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_delta: Optional[float] = None
    cpu_usage: Optional[float] = None
    api_calls: int = 0
    errors: List[str] = field(default_factory=list)
    
    def calculate_execution_time(self):
        """실행 시간 계산"""
        if self.end_time and self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
    
    def calculate_memory_delta(self):
        """메모리 사용량 변화 계산"""
        if self.memory_before is not None and self.memory_after is not None:
            self.memory_delta = self.memory_after - self.memory_before

class PerformanceMonitor:
    """성능 모니터링 시스템"""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.metrics_history: deque = deque(maxlen=max_history_size)
        self.current_metrics: Dict[str, PerformanceMetric] = {}
        self.api_call_counter = defaultdict(int)
        self.system_stats = {
            'startup_time': datetime.now(),
            'total_operations': 0,
            'total_api_calls': 0,
            'total_errors': 0
        }
        
        # 백그라운드 시스템 모니터링 시작
        self._start_system_monitoring()
        
        # 로그 파일 경로
        self.log_dir = "/Users/kjw/emotion-analysis-system/logs/performance"
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _start_system_monitoring(self):
        """백그라운드에서 시스템 리소스 모니터링"""
        def monitor_system():
            while True:
                try:
                    # CPU 사용률
                    cpu_percent = psutil.cpu_percent(interval=1)
                    
                    # 메모리 사용률
                    memory = psutil.virtual_memory()
                    memory_percent = memory.percent
                    
                    # 디스크 사용률
                    disk = psutil.disk_usage('/')
                    disk_percent = disk.percent
                    
                    # 현재 시간에 시스템 상태 기록
                    timestamp = datetime.now()
                    system_state = {
                        'timestamp': timestamp.isoformat(),
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_percent,
                        'memory_available_gb': memory.available / (1024**3),
                        'disk_percent': disk_percent,
                        'active_operations': len(self.current_metrics)
                    }
                    
                    # 시스템 상태 로그 저장 (5분마다)
                    if timestamp.minute % 5 == 0 and timestamp.second < 2:
                        self._save_system_log(system_state)
                    
                    time.sleep(60)  # 1분마다 모니터링
                    
                except Exception as e:
                    print(f"시스템 모니터링 오류: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def start_operation(self, function_name: str) -> str:
        """작업 시작 모니터링"""
        operation_id = f"{function_name}_{datetime.now().timestamp()}"
        
        # 현재 메모리 사용량 측정
        process = psutil.Process()
        memory_before = process.memory_info().rss / (1024**2)  # MB 단위
        
        metric = PerformanceMetric(
            function_name=function_name,
            start_time=datetime.now(),
            memory_before=memory_before
        )
        
        self.current_metrics[operation_id] = metric
        self.system_stats['total_operations'] += 1
        
        return operation_id
    
    def end_operation(self, operation_id: str, error: Optional[str] = None):
        """작업 종료 모니터링"""
        if operation_id not in self.current_metrics:
            return
        
        metric = self.current_metrics[operation_id]
        metric.end_time = datetime.now()
        
        # 실행 시간 계산
        metric.calculate_execution_time()
        
        # 현재 메모리 사용량 측정
        try:
            process = psutil.Process()
            metric.memory_after = process.memory_info().rss / (1024**2)  # MB 단위
            metric.cpu_usage = psutil.cpu_percent()
            metric.calculate_memory_delta()
        except:
            pass
        
        # 에러 기록
        if error:
            metric.errors.append(error)
            self.system_stats['total_errors'] += 1
        
        # 히스토리에 추가
        self.metrics_history.append(metric)
        
        # 현재 작업에서 제거
        del self.current_metrics[operation_id]
        
        return metric
    
    def record_api_call(self, api_name: str):
        """API 호출 기록"""
        self.api_call_counter[api_name] += 1
        self.system_stats['total_api_calls'] += 1
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """성능 요약 통계"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.start_time >= cutoff_time]
        
        if not recent_metrics:
            return {"message": "최근 데이터가 없습니다"}
        
        # 함수별 통계
        function_stats = defaultdict(list)
        for metric in recent_metrics:
            function_stats[metric.function_name].append(metric)
        
        summary = {
            "period_hours": hours,
            "total_operations": len(recent_metrics),
            "functions": {}
        }
        
        for func_name, metrics in function_stats.items():
            execution_times = [m.execution_time for m in metrics if m.execution_time]
            memory_deltas = [m.memory_delta for m in metrics if m.memory_delta]
            error_count = sum(len(m.errors) for m in metrics)
            
            function_summary = {
                "call_count": len(metrics),
                "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
                "max_execution_time": max(execution_times) if execution_times else 0,
                "min_execution_time": min(execution_times) if execution_times else 0,
                "avg_memory_delta": sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
                "error_count": error_count,
                "success_rate": (len(metrics) - error_count) / len(metrics) * 100 if metrics else 0
            }
            
            summary["functions"][func_name] = function_summary
        
        # API 호출 통계
        summary["api_calls"] = dict(self.api_call_counter)
        
        # 전체 시스템 통계
        summary["system_stats"] = self.system_stats.copy()
        summary["system_stats"]["uptime_hours"] = (
            datetime.now() - self.system_stats['startup_time']
        ).total_seconds() / 3600
        
        return summary
    
    def get_slow_operations(self, threshold_seconds: float = 5.0) -> List[Dict]:
        """느린 작업 식별"""
        slow_ops = []
        
        for metric in self.metrics_history:
            if metric.execution_time and metric.execution_time > threshold_seconds:
                slow_ops.append({
                    "function_name": metric.function_name,
                    "execution_time": metric.execution_time,
                    "start_time": metric.start_time.isoformat(),
                    "memory_delta": metric.memory_delta,
                    "errors": metric.errors
                })
        
        # 실행 시간 기준 정렬
        slow_ops.sort(key=lambda x: x["execution_time"], reverse=True)
        
        return slow_ops
    
    def get_memory_intensive_operations(self, threshold_mb: float = 50.0) -> List[Dict]:
        """메모리 집약적 작업 식별"""
        memory_ops = []
        
        for metric in self.metrics_history:
            if metric.memory_delta and abs(metric.memory_delta) > threshold_mb:
                memory_ops.append({
                    "function_name": metric.function_name,
                    "memory_delta": metric.memory_delta,
                    "execution_time": metric.execution_time,
                    "start_time": metric.start_time.isoformat()
                })
        
        # 메모리 사용량 기준 정렬
        memory_ops.sort(key=lambda x: abs(x["memory_delta"]), reverse=True)
        
        return memory_ops
    
    def _save_system_log(self, system_state: Dict):
        """시스템 상태 로그 저장"""
        today = datetime.now().strftime("%Y%m%d")
        log_file = f"{self.log_dir}/system_performance_{today}.json"
        
        try:
            # 기존 로그 읽기
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 새로운 로그 추가
            logs.append(system_state)
            
            # 로그 저장 (최대 1000개 유지)
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"시스템 로그 저장 실패: {e}")
    
    def save_performance_report(self):
        """성능 리포트 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.log_dir}/performance_report_{timestamp}.json"
        
        def serialize_datetime(obj):
            """datetime 객체를 JSON 직렬화 가능한 문자열로 변환"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            else:
                return obj
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary_24h": serialize_datetime(self.get_performance_summary(24)),
            "slow_operations": self.get_slow_operations(),
            "memory_intensive_operations": self.get_memory_intensive_operations(),
            "recent_metrics": [
                {
                    "function_name": m.function_name,
                    "execution_time": m.execution_time,
                    "memory_delta": m.memory_delta,
                    "start_time": m.start_time.isoformat(),
                    "errors": m.errors
                }
                for m in list(self.metrics_history)[-100:]  # 최근 100개
            ]
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"📊 성능 리포트 저장 완료: {report_file}")
            return report_file
            
        except Exception as e:
            print(f"성능 리포트 저장 실패: {e}")
            return None

# 글로벌 성능 모니터 인스턴스
performance_monitor = PerformanceMonitor()

def monitor_performance(func):
    """성능 모니터링 데코레이터"""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        operation_id = performance_monitor.start_operation(func.__name__)
        
        try:
            result = func(*args, **kwargs)
            performance_monitor.end_operation(operation_id)
            return result
            
        except Exception as e:
            performance_monitor.end_operation(operation_id, str(e))
            raise
    
    return wrapper

# 사용 예시
if __name__ == "__main__":
    # 성능 모니터링 테스트
    @monitor_performance
    def test_function():
        import time
        time.sleep(1)
        return "완료"
    
    # API 호출 기록 테스트
    performance_monitor.record_api_call("YouTube_API")
    performance_monitor.record_api_call("Calendar_API")
    
    # 테스트 실행
    result = test_function()
    
    # 성능 요약 출력
    summary = performance_monitor.get_performance_summary(1)
    # datetime 객체를 문자열로 변환
    import copy
    summary_copy = copy.deepcopy(summary)
    if 'system_stats' in summary_copy and 'startup_time' in summary_copy['system_stats']:
        summary_copy['system_stats']['startup_time'] = summary_copy['system_stats']['startup_time'].isoformat()
    
    print("성능 요약:", json.dumps(summary_copy, indent=2, ensure_ascii=False))
    
    # 리포트 저장
    performance_monitor.save_performance_report()