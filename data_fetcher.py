#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
data_fetcher.py - 真實數據獲取與指標運算模組
============================================================

本模組負責：
1. 從 Yahoo Finance 抓取即時股價數據
2. 使用自定義函數計算技術指標
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
import requests

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
    
    def get_historical_data(self, symbol: str, period: str = "3mo", interval: str = "1d") -> Optional[pd.DataFrame]:
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
    
    # ==================== 自定義技術指標函數 ====================
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """
        計算簡單移動平均線 (Simple Moving Average)
        
        參數:
            data: 價格數據（通常是收盤價）
            period: 移動平均週期
        
        返回:
            SMA 數據序列
        """
        return data.rolling(window=period).mean()
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        計算指數移動平均線 (Exponential Moving Average)
        
        參數:
            data: 價格數據
            period: EMA 週期
        
        返回:
            EMA 數據序列
        """
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """
        計算布林通道 (Bollinger Bands)
        
        參數:
            data: 收盤價序列
            period: 週期（預設20天）
            std_dev: 標準差倍數（預設2倍）
        
        返回:
            包含上軌、中軌、下軌的 DataFrame
        """
        sma = self.calculate_sma(data, period)
        std = data.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return pd.DataFrame({
            'BB_upper': upper,
            'BB_middle': sma,
            'BB_lower': lower
        }, index=data.index)
    
    def calculate_macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        計算 MACD（平滑異同移動平均線）
        
        參數:
            data: 收盤價序列
            fast: 快線週期（預設12）
            slow: 慢線週期（預設26）
            signal: 信號線週期（預設9）
        
        返回:
            包含 MACD線、信號線、柱狀圖的 DataFrame
        """
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'MACD': macd_line,
            'Signal': signal_line,
            'Histogram': histogram
        }, index=data.index)
    
    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """
        計算 RSI（相對强弱指數）
        
        參數:
            data: 收盤價序列
            period: RSI 週期（預設14）
        
        返回:
            RSI 數值序列
        """
        delta = data.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        計算技術指標
        
        參數:
            df: 歷史價格 DataFrame
        
        返回:
            包含各項指標數值的字典
        """
        if df is None or df.empty:
            return {}
        
        # 確保有 Close 欄位
        if 'Close' not in df.columns:
            logger.error("數據中沒有 Close 欄位")
            return {}
        
        close = df['Close']
        
        # 計算各項指標
        bb = self.calculate_bollinger_bands(close)
        macd = self.calculate_macd(close)
        rsi = self.calculate_rsi(close)
        
        # 計算 SMA
        sma20 = self.calculate_sma(close, 20)
        sma50 = self.calculate_sma(close, 50)
        sma200 = self.calculate_sma(close, 200)
        
        # 取得最新一根 K 線的指標數值
        latest = df.iloc[-1] if not df.empty else None
        prev = df.iloc[-2] if len(df) > 1 else None
        
        indicators = {}
        
        if latest is not None:
            current_price = close.iloc[-1]
            
            # === Bollinger Bands 解析 ===
            bb_upper = bb['BB_upper'].iloc[-1]
            bb_mid = bb['BB_middle'].iloc[-1]
            bb_lower = bb['BB_lower'].iloc[-1]
            
            if current_price > bb_upper:
                bb_position = "上軌上方（可能過熱）"
            elif current_price < bb_lower:
                bb_position = "下軌下方（可能超賣）"
            elif current_price > bb_mid:
                bb_position = "中軌與上軌之間（偏多）"
            else:
                bb_position = "中軌與下軌之間（偏空）"
            
            indicators["bollinger_bands"] = {
                "upper": round(bb_upper, 2) if pd.notna(bb_upper) else None,
                "middle": round(bb_mid, 2) if pd.notna(bb_mid) else None,
                "lower": round(bb_lower, 2) if pd.notna(bb_lower) else None,
                "current_price": round(current_price, 2),
                "position": bb_position
            }
            
            # === MACD 解析 ===
            macd_line = macd['MACD'].iloc[-1]
            macd_signal = macd['Signal'].iloc[-1]
            macd_hist = macd['Histogram'].iloc[-1]
            
            # 判斷MACD交叉
            macd_cross = "無交叉"
            if prev is not None and len(macd) > 1:
                prev_macd = macd['MACD'].iloc[-2]
                prev_signal = macd['Signal'].iloc[-2]
                
                # 金叉（多頭訊號）
                if prev_macd <= prev_signal and macd_line > macd_signal:
                    macd_cross = "金叉（多頭訊號）"
                # 死叉（空頭訊號）
                elif prev_macd >= prev_signal and macd_line < macd_signal:
                    macd_cross = "死叉（空頭訊號）"
            
            # 柱狀圖方向
            hist_direction = "紅柱（空頭）" if macd_hist < 0 else "綠柱（多頭）"
            
            indicators["macd"] = {
                "macd_line": round(macd_line, 4) if pd.notna(macd_line) else None,
                "signal_line": round(macd_signal, 4) if pd.notna(macd_signal) else None,
                "histogram": round(macd_hist, 4) if pd.notna(macd_hist) else None,
                "direction": hist_direction,
                "crossover": macd_cross
            }
            
            # === RSI 解析 ===
            rsi_value = rsi.iloc[-1]
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
                "value": round(rsi_value, 2) if pd.notna(rsi_value) else None,
                "signal": rsi_signal
            }
            
            # === 移動平均線 ===
            indicators["sma"] = {
                "sma20": round(sma20.iloc[-1], 2) if pd.notna(sma20.iloc[-1]) else None,
                "sma50": round(sma50.iloc[-1], 2) if pd.notna(sma50.iloc[-1]) else None,
                "sma200": round(sma200.iloc[-1], 2) if pd.notna(sma200.iloc[-1]) else None
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
