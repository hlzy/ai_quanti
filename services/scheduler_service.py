"""
定时任务服务 - 自动更新股票数据
按北京时间统一时间点触发：
- 1分钟K线：每5分钟（12:00、12:05、12:10...）
- 日K/周K：每天凌晨2点
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
        self.last_minute_trigger = None  # 上次分钟K触发时间
        self.last_daily_trigger = None   # 上次日K触发时间
    
    def start(self):
        """启动定时任务"""
        if self.running:
            print("定时任务已在运行中")
            return
        
        self.running = True
        self.thread = Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("✅ 定时任务已启动（按北京时间整点触发）")
    
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
                
                # 检查是否到达整5分钟时刻（例如：12:00、12:05、12:10）
                if self._is_five_minute_mark(now):
                    if not self._is_same_minute(now, self.last_minute_trigger):
                        print(f"\n⏰ 触发时间点: {now.strftime('%H:%M')}")
                        self._update_minute_data()
                        self.last_minute_trigger = now
                
                # 检查是否到达凌晨2点（每天更新日K/周K）
                if self._is_daily_update_time(now):
                    if not self._is_same_hour(now, self.last_daily_trigger):
                        print(f"\n⏰ 每日更新时间: {now.strftime('%Y-%m-%d %H:%M')}")
                        self._update_daily_data()
                        self.last_daily_trigger = now
                
                # 每30秒检查一次（降低CPU占用）
                time.sleep(30)
            except Exception as e:
                print(f"定时任务执行出错: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(30)
    
    def _is_five_minute_mark(self, now):
        """判断是否是整5分钟时刻"""
        return now.minute % 5 == 0 and now.second < 30
    
    def _is_daily_update_time(self, now):
        """判断是否是每日更新时间（凌晨2点）"""
        return now.hour == 2 and now.minute == 0 and now.second < 30
    
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
    
    def _update_minute_data(self):
        """更新所有自选股的1分钟K线数据"""
        try:
            watchlist = watchlist_service.get_all_watchlist()
            if not watchlist:
                print("  ⚠️ 自选股列表为空，跳过更新")
                return
            
            print(f"📊 开始更新1分钟K线数据（共{len(watchlist)}只股票）...")
            
            success_count = 0
            for stock in watchlist:
                stock_code = stock['stock_code']
                try:
                    # 只更新1分钟数据
                    minute_data = stock_service.fetch_minute_data(stock_code)
                    if minute_data:
                        stock_service.save_minute_data(minute_data)
                        success_count += 1
                        print(f"  ✓ {stock_code} 1分钟K线已更新（{len(minute_data)}条）")
                    else:
                        print(f"  ⚠️ {stock_code} 无1分钟K线数据（可能需要权限）")
                    
                    # 避免触发频率限制，每只股票间隔1秒
                    time.sleep(1)
                except Exception as e:
                    print(f"  ✗ {stock_code} 1分钟K线更新失败: {e}")
            
            print(f"✅ 1分钟K线更新完成（成功{success_count}/{len(watchlist)}）\n")
        except Exception as e:
            print(f"❌ 更新1分钟K线数据失败: {e}")
    
    def _update_daily_data(self):
        """更新所有自选股的日K/周K数据"""
        try:
            watchlist = watchlist_service.get_all_watchlist()
            if not watchlist:
                print("  ⚠️ 自选股列表为空，跳过更新")
                return
            
            print(f"📊 开始更新日K/周K数据（共{len(watchlist)}只股票）...")
            
            success_count = 0
            for stock in watchlist:
                stock_code = stock['stock_code']
                try:
                    # 更新日K和周K
                    stock_service.update_stock_data(stock_code)
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
