"""
定时任务服务 - 自动更新股票数据
按北京时间统一时间点触发：
- 实时股价：每分钟更新
- 日K/周K：每小时更新
"""
from threading import Thread
import time
from datetime import datetime
from services.stock_service import stock_service
from services.watchlist_service import watchlist_service


class SchedulerService:
    """定时任务服务类"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_realtime_trigger = None  # 上次实时价格触发时间
        self.last_hourly_trigger = None    # 上次小时触发时间
    
    def start(self):
        """启动定时任务"""
        if self.running:
            print("定时任务已在运行中")
            return
        
        self.running = True
        self.thread = Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("✅ 定时任务已启动（实时股价：每分钟，日K/周K：每小时）")
    
    def stop(self):
        """停止定时任务"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("❌ 定时任务已停止")
    
    def _run_scheduler(self):
        """运行定时任务主循环"""
        while self.running:
            try:
                now = datetime.now()
                
                # 每分钟更新实时股价
                if self._is_minute_mark(now):
                    if not self._is_same_minute(now, self.last_realtime_trigger):
                        print(f"\n⏰ 更新实时股价: {now.strftime('%H:%M')}")
                        self._update_realtime_price()
                        self.last_realtime_trigger = now
                
                # 每小时更新日K/周K（整点）
                if self._is_hourly_update_time(now):
                    if not self._is_same_hour(now, self.last_hourly_trigger):
                        print(f"\n⏰ 小时更新时间: {now.strftime('%Y-%m-%d %H:%M')}")
                        self._update_kline_data()
                        self.last_hourly_trigger = now
                
                # 每20秒检查一次（降低CPU占用）
                time.sleep(20)
            except Exception as e:
                print(f"定时任务执行出错: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(20)
    
    def _is_minute_mark(self, now):
        """判断是否是整分钟时刻"""
        return now.second < 20
    
    def _is_hourly_update_time(self, now):
        """判断是否是整点时间"""
        return now.minute == 0 and now.second < 20
    
    def _is_same_minute(self, time1, time2):
        """判断两个时间是否在同一分钟内"""
        if time2 is None:
            return False
        return (time1.year == time2.year and 
                time1.month == time2.month and 
                time1.day == time2.day and 
                time1.hour == time2.hour and 
                time1.minute == time2.minute)
    
    def _is_same_hour(self, time1, time2):
        """判断两个时间是否在同一小时内"""
        if time2 is None:
            return False
        return (time1.year == time2.year and 
                time1.month == time2.month and 
                time1.day == time2.day and 
                time1.hour == time2.hour)
    
    def _update_realtime_price(self):
        """更新所有自选股的实时股价（跨所有用户，去重）"""
        try:
            # 获取所有用户的自选股（去重）
            watchlist = watchlist_service.get_all_unique_stocks()
            if not watchlist:
                print("  ⚠️ 自选股列表为空，跳过更新")
                return
            
            print(f"💰 开始更新实时股价（共{len(watchlist)}只股票）...")
            
            success_count = 0
            for stock in watchlist:
                stock_code = stock['stock_code']
                try:
                    # 获取实时价格
                    price_data = stock_service.fetch_realtime_price(stock_code)
                    if price_data:
                        stock_service.save_realtime_price(price_data)
                        success_count += 1
                        print(f"  ✓ {stock_code} 当前价格: {price_data.get('price', 'N/A')}")
                    
                    # 避免触发频率限制
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  ✗ {stock_code} 实时价格更新失败: {e}")
            
            print(f"✅ 实时股价更新完成（成功{success_count}/{len(watchlist)}）\n")
        except Exception as e:
            print(f"❌ 更新实时股价失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_kline_data(self):
        """更新所有自选股的日K/周K数据（跨所有用户，去重）"""
        try:
            # 获取所有用户的自选股（去重）
            watchlist = watchlist_service.get_all_unique_stocks()
            if not watchlist:
                print("  ⚠️ 自选股列表为空，跳过更新")
                return
            
            print(f"📊 开始更新日K/周K数据（共{len(watchlist)}只股票）...")
            
            success_count = 0
            for stock in watchlist:
                stock_code = stock['stock_code']
                try:
                    # 更新日K和周K（不包含分钟K）
                    stock_service.update_kline_data_only(stock_code)
                    success_count += 1
                    print(f"  ✓ {stock_code} 日K/周K已更新")
                    
                    # 避免触发频率限制，每只股票间隔1秒
                    time.sleep(1)
                except Exception as e:
                    print(f"  ✗ {stock_code} 日K/周K更新失败: {e}")
            
            print(f"✅ 日K/周K更新完成（成功{success_count}/{len(watchlist)}）\n")
        except Exception as e:
            print(f"❌ 更新日K/周K数据失败: {e}")


# 创建全局调度器实例
scheduler_service = SchedulerService()
