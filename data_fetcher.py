#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
data_fetcher.py - 真實數據獲取與指標運算模組
============================================================

本模組負責：
1. 從 Yahoo Finance 抓取即時股價數據
2. 使用 pandas_ta 計算技術指標
3. 組裝結構化 JSON 輸出

作者：Investment Bot
建立日期：2026-04-03
============================================================
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import yfinance as yf
import pandas as pd
import pandas_ta as ta

# 設定日誌記錄（監控數據獲取過程）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockDataFetcher:
    """
    股票數據獲取器
    
    用途：從 Yahoo Finance 獲取股價數據並計算技術指標
    """
    
    def __init__(self, watchlist: List[str]):
        """
        初始化數據獲取器
        
        參數:
            watchlist: 要監控的股票代碼列表，例如 ['TSLA', 'NVDA', 'COIN']
        """
        self.watchlist = watchlist
        logger.info(f"初始化 StockDataFetcher，監控標的: {watchlist}")
    
    def get_realtime_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        取得即時股價數據
        
        參數:
            symbol: 股票代碼，例如 'TSLA'
        
        返回:
            包含即時價格的字典，若失敗則返回 None
        """
        try:
            # 建立 Ticker 物件
            ticker = yf.Ticker(symbol)
            
            # 取得即時價格資訊
            info = ticker.info
            
            # 提取關鍵價格數據
            price_data = {
                "symbol": symbol,
                "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
                "previous_close": info.get("previousClose", info.get("regularMarketPreviousClose")),
                "open": info.get("open"),
                "high": info.get("dayHigh"),
                "low": info.get("dayLow"),
                "volume": info.get("volume"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "name": info.get("longName", info.get("shortName", symbol)),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"取得 {symbol} 即時價格: ${price_data['current_price']}")
            return price_data
            
        except Exception as e:
            logger.error(f"取得 {symbol} 價格失敗: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        取得歷史 K 線數據
        
        參數:
            symbol: 股票代碼
            period: 資料期間（例如 '1mo', '3mo', '1y'）
            interval: 資料區間（例如 '1d', '4h', '1h'）
        
        返回:
            pandas DataFrame，包含歷史價格數據
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"{symbol} 無歷史數據")
                return None
            
            logger.info(f"取得 {symbol} {period} 歷史數據，共 {len(df)} 筆")
            return df
            
        except Exception as e:
            logger.error(f"取得 {symbol} 歷史數據失敗: {e}")
            return None
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        使用 pandas_ta 計算技術指標
        
        參數:
            df: 歷史價格 DataFrame
        
        返回:
            包含各項指標數值的字典
        """
        if df is None or df.empty:
            return {}
        
        # 複製資料避免修改原始數據
        data = df.copy()
        
        # 確保必要的欄位存在
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in data.columns:
                # 嘗試轉換欄位名稱（小寫）
                col_lower = col.lower()
                if col_lower in data.columns:
                    data.columns = data.columns.str.replace(col_lower, col, regex=False)
        
        # 計算技術指標
        # 1. Bollinger Bands（布林通道）
        bbands = data.ta.bbands(length=20, std=2)
        if bbands is not None and not bbands.empty:
            data = pd.concat([data, bbands], axis=1)
        
        # 2. MACD（平滑異同移動平均線）
        macd = data.ta.macosl(fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            data = pd.concat([data, macd], axis=1)
        
        # 3. RSI（相對强弱指數）
        rsi = data.ta.rsi(length=14)
        if rsi is not None and not rsi.empty:
            data = pd.concat([data, rsi], axis=1)
        
        # 4. SMA（簡單移動平均線）
        sma20 = data.ta.sma(length=20)
        sma50 = data.ta.sma(length=50)
        sma200 = data.ta.sma(length=200)
        
        # 取得最新一根 K 線的指標數值
        latest = data.iloc[-1] if not data.empty else None
        prev = data.iloc[-2] if len(data) > 1 else None
        
        indicators = {}
        
        if latest is not None:
            # === Bollinger Bands 解析 ===
            # 判斷價格位於哪個軌道
            close = latest.get('Close', 0)
            bb_upper = latest.get('BBU_20_2.0')  # 上軌
            bb_mid = latest.get('BBM_20_2.0')    # 中軌
            bb_lower = latest.get('BBL_20_2.0')  # 下軌
            
            if bb_upper and bb_lower:
                if close > bb_upper:
                    bb_position = "上軌上方（可能過熱）"
                elif close < bb_lower:
                    bb_position = "下軌下方（可能超賣）"
                elif close > bb_mid:
                    bb_position = "中軌與上軌之間（偏多）"
                else:
                    bb_position = "中軌與下軌之間（偏空）"
            else:
                bb_position = "資料不足"
            
            indicators["bollinger_bands"] = {
                "upper": round(bb_upper, 2) if bb_upper else None,
                "middle": round(bb_mid, 2) if bb_mid else None,
                "lower": round(bb_lower, 2) if bb_lower else None,
                "current_price": round(close, 2),
                "position": bb_position
            }
            
            # === MACD 解析 ===
            macd_line = latest.get('MACD_12_26_9')
            macd_signal = latest.get('MACDs_12_26_9')
            macd_hist = latest.get('MACDh_12_26_9')
            
            # 判斷MACD交叉
            macd_cross = "無交叉"
            if prev is not None:
                prev_macd = prev.get('MACD_12_26_9', 0)
                prev_signal = prev.get('MACDs_12_26_9', 0)
                
                # 金叉（多頭訊號）
                if prev_macd <= prev_signal and macd_line > macd_signal:
                    macd_cross = "金叉（多頭訊號）"
                # 死叉（空頭訊號）
                elif prev_macd >= prev_signal and macd_line < macd_signal:
                    macd_cross = "死叉（空頭訊號）"
            
            # 柱狀圖方向
            if macd_hist:
                hist_direction = "紅柱（空頭）" if macd_hist < 0 else "綠柱（多頭）"
            else:
                hist_direction = "資料不足"
            
            indicators["macd"] = {
                "macd_line": round(macd_line, 4) if macd_line else None,
                "signal_line": round(macd_signal, 4) if macd_signal else None,
                "histogram": round(macd_hist, 4) if macd_hist else None,
                "direction": hist_direction,
                "crossover": macd_cross
            }
            
            # === RSI 解析 ===
            rsi_value = latest.get('RSI_14')
            if rsi_value:
                if rsi_value > 70:
                    rsi_signal = "超買區（可能回檔）"
                elif rsi_value < 30:
                    rsi_signal = "超賣區（可能反彈）"
                else:
                    rsi_signal = "中性區"
            else:
                rsi_signal = "資料不足"
                rsi_value = None
            
            indicators["rsi"] = {
                "value": round(rsi_value, 2) if rsi_value else None,
                "signal": rsi_signal
            }
            
            # === 移動平均線 ===
            indicators["sma"] = {
                "sma20": round(sma20.iloc[-1], 2) if sma20 is not None and not sma20.empty else None,
                "sma50": round(sma50.iloc[-1], 2) if sma50 is not None and not sma50.empty else None,
                "sma200": round(sma200.iloc[-1], 2) if sma200 is not None and not sma200.empty else None
            }
        
        return indicators
    
    def get_news(self, symbol: str, limit: int = 3) -> List[Dict[str, str]]:
        """
        取得該標的最近新聞
        
        參數:
            symbol: 股票代碼
            limit: 要取得的新聞數量
        
        返回:
            新聞列表，每則包含標題、摘要、連結
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                logger.info(f"{symbol} 無最新新聞")
                return []
            
            # 解析新聞資料
            news_list = []
            for item in news[:limit]:
                news_item = {
                    "title": item.get("title", "無標題"),
                    "publisher": item.get("publisher", "未知來源"),
                    "link": item.get("link", ""),
                    "pubDate": item.get("pubDate", ""),
                    "type": item.get("type", "")
                }
                news_list.append(news_item)
            
            logger.info(f"取得 {symbol} {len(news_list)} 則新聞")
            return news_list
            
        except Exception as e:
            logger.error(f"取得 {symbol} 新聞失敗: {e}")
            return []
    
    def fetch_all_data(self) -> Dict[str, Any]:
        """
        取得所有監控標的的综合數據
        
        返回:
            結構化 JSON，包含所有標的之價格、指標、新聞
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "watchlist": self.watchlist,
            "stocks": {}
        }
        
        for symbol in self.watchlist:
            logger.info(f"開始處理標的: {symbol}")
            
            # 1. 取得即時價格
            price_data = self.get_realtime_price(symbol)
            
            # 2. 取得歷史數據計算指標
            hist_data = self.get_historical_data(symbol, period="3mo", interval="1d")
            indicators = self.calculate_indicators(hist_data)
            
            # 3. 取得新聞
            news = self.get_news(symbol, limit=3)
            
            # 組裝結構化輸出
            stock_info = {
                "price": price_data,
                "indicators": indicators,
                "news": news
            }
            
            result["stocks"][symbol] = stock_info
        
        logger.info(f"完成所有標的數據獲取: {self.watchlist}")
        return result


def main():
    """
    測試用主函數
    """
    # 測試單一標的
    fetcher = StockDataFetcher(["TSLA", "NVDA", "COIN"])
    result = fetcher.fetch_all_data()
    
    # 輸出 JSON 格式
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
