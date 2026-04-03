#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
main.py - 自動化投資系統主程式
============================================================

本程式負責：
1. 排程管理（美股盤前、盤中、盤後）
2. 整合 data_fetcher 與 expert_analyst
3. 支援 systemd 背景運行

作者：Investment Bot
建立日期：2026-04-03
============================================================
"""

import os
import sys
import json
import logging
import signal
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 將当前目錄加入 Python 路徑（確保可以 import 同目錄的模組）
sys.path.insert(0, str(Path(__file__).parent))

import schedule
import time

# 匯入自定義模組
from data_fetcher import StockDataFetcher
from expert_analyst import ExpertAnalyst

# 設定日誌記錄
LOG_FILE = "investment-bot.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class InvestmentBot:
    """
    自動化投資機器人
    
    用途：定時抓取數據、進行分析、推送到 Telegram
    """
    
    def __init__(self):
        """
        初始化機器人
        """
        # 從環境變數取得監控名單
        watchlist_str = os.getenv("WATCHLIST", "TSLA,NVDA,COIN")
        self.watchlist = [s.strip() for s in watchlist_str.split(",")]
        
        # 初始化各模組
        self.data_fetcher = StockDataFetcher(self.watchlist)
        self.analyst = ExpertAnalyst()
        
        # 標記是否繼續運行
        self.running = True
        
        logger.info(f"🚀 投資機器人啟動，監控標的: {self.watchlist}")
    
    def signal_handler(self, signum, frame):
        """
        處理系統訊號（優雅關閉）
        """
        logger.info("📡 收到停止訊號，正在優雅關閉...")
        self.running = False
    
    def run_analysis(self) -> bool:
        """
        執行完整分析流程
        
        返回:
            是否成功
        """
        try:
            logger.info("=" * 50)
            logger.info(f"🕐 開始分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 50)
            
            # 1. 抓取數據
            logger.info("📥 步驟1: 抓取市場數據...")
            stock_data = self.data_fetcher.fetch_all_data()
            
            # 保存原始數據供日誌查看
            with open(f"data_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
                json.dump(stock_data, f, indent=2, ensure_ascii=False)
            
            # 2. OpenClaw 分析 + Telegram 推播
            logger.info("🤖 步驟2: 進行專家分析並推播...")
            success = self.analyst.analyze_and_broadcast(stock_data)
            
            if success:
                logger.info("✅ 分析與推播完成")
            else:
                logger.warning("⚠️ 推播失敗，請檢查 Telegram 配置")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 分析過程發生錯誤: {e}")
            return False
    
    def schedule_jobs(self):
        """
        設定排程任務
        
        美股交易時間（台北時間）：
        - 盤前: 16:00-21:30
        - 盤中: 21:30-04:00  
        - 盤後: 04:00-05:00
        
        設定:
        - 盤前分析: 19:00（台北）= 03:00 ET
        - 盤後分析: 21:00（台北）= 05:00 ET
        - 盤中更新: 每4小時
        """
        # 盤前分析（台北時間 19:00 = 美東 03:00，盤前）
        schedule.every().day.at("19:00").do(self.run_analysis)
        logger.info("📅 已設定: 盤前分析 19:00")
        
        # 盤中分析（台北時間 13:00 = 美東 01:00，盤中）
        schedule.every().day.at("13:00").do(self.run_analysis)
        logger.info("📅 已設定: 盤中分析 13:00")
        
        # 盤後分析（台北時間 21:30 = 美東 05:30，盤後）
        schedule.every().day.at("21:30").do(self.run_analysis)
        logger.info("📅 已設定: 盤後分析 21:30")
        
        # 每4小時持續更新（適用於盤中時段）
        schedule.every(4).hours.do(self.run_analysis)
        logger.info("📅 已設定: 每4小時持續更新")
    
    def run(self):
        """
        啟動機器人，進入排程循環
        """
        # 設定訊號處理（優雅關閉）
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 設定排程
        self.schedule_jobs()
        
        # 首次運行（啟動時執行一次）
        logger.info("▶️ 執行首次分析...")
        self.run_analysis()
        
        # 进入排程循環
        logger.info("⏳ 進入排程等待...")
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
        
        logger.info("👋 投資機器人已停止")


def main():
    """
    主入口點
    """
    parser = argparse.ArgumentParser(description="自動化投資分析系統")
    parser.add_argument(
        "--once",
        action="store_true",
        help="僅執行一次（不進入排程循環）"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="測試模式：使用模擬數據"
    )
    
    args = parser.parse_args()
    
    if args.test:
        # 測試模式
        logger.info("🧪 測試模式啟動...")
        bot = InvestmentBot()
        bot.run_analysis()
        logger.info("🧪 測試完成")
        
    elif args.once:
        # 單次執行
        logger.info("▶️ 單次執行模式...")
        bot = InvestmentBot()
        bot.run_analysis()
        logger.info("▶️ 執行完成")
        
    else:
        # 持續運行模式
        logger.info("🚀 持續運行模式...")
        bot = InvestmentBot()
        bot.run()


if __name__ == "__main__":
    main()
