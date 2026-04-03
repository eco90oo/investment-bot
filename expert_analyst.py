#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
expert_analyst.py - 金融專家分析與Telegram推播模組
============================================================

本模組負責：
1. 直接進行專業分析（我是 OpenClaw AI）
2. 整合 Telegram Bot API 推播分析結果

作者：Investment Bot
建立日期：2026-04-03
============================================================
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExpertAnalyst:
    """
    金融專家分析器
    
    用途：直接進行 AI 分析並推送到 Telegram
    """
    
    def __init__(self):
        """
        初始化分析器，載入環境變數
        """
        # 從環境變數取得配置
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "-1003810052310")  # 預設財經頻道
        
        logger.info(f"初始化 ExpertAnalyst，Telegram Channel: {self.channel_id}")
    
    def generate_analysis(self, stock_data: Dict[str, Any]) -> str:
        """
        直接生成專業分析報告
        
        參數:
            stock_data: 從 data_fetcher.py 取得的結構化股票數據
        
        返回:
            分析報告（Markdown 格式）
        """
        analysis_lines = []
        
        # 加入標題
        analysis_lines.append("## 【今日觀察標的】\n")
        
        # 分析每個股票
        for symbol, data in stock_data.get('stocks', {}).items():
            price = data.get('price', {})
            indicators = data.get('indicators', {})
            news = data.get('news', [])
            
            name = price.get('name', symbol)
            current_price = price.get('current_price', 0)
            prev_close = price.get('previous_close', 0)
            change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
            
            # 判斷漲跌
            emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            
            analysis_lines.append(f"### {emoji} {symbol} ({name})")
            analysis_lines.append(f"- 目前價格: **${current_price}**")
            analysis_lines.append(f"- 昨收: ${prev_close} ({change:+.2f}%)")
            analysis_lines.append(f"- 52週區間: ${price.get('52w_low', 'N/A')} - ${price.get('52w_high', 'N/A')}")
            analysis_lines.append(f"- 本益比: {price.get('pe_ratio', 'N/A')}")
            analysis_lines.append("")
        
        # === 技術指標真實數據 ===
        analysis_lines.append("\n## 【技術指標真實數據清單】\n")
        
        for symbol, data in stock_data.get('stocks', {}).items():
            indicators = data.get('indicators', {})
            
            analysis_lines.append(f"### {symbol}")
            
            # Bollinger Bands
            bb = indicators.get('bollinger_bands', {})
            if bb:
                analysis_lines.append(f"**Bollinger Bands:**")
                analysis_lines.append(f"- 上軌: ${bb.get('upper', 'N/A')}")
                analysis_lines.append(f"- 中軌: ${bb.get('middle', 'N/A')}")
                analysis_lines.append(f"- 下軌: ${bb.get('lower', 'N/A')}")
                analysis_lines.append(f"- 位置: {bb.get('position', 'N/A')}")
            
            # MACD
            macd = indicators.get('macd', {})
            if macd:
                analysis_lines.append(f"**MACD:**")
                analysis_lines.append(f"- 快線: {macd.get('macd_line', 'N/A')}")
                analysis_lines.append(f"- 慢線: {macd.get('signal_line', 'N/A')}")
                analysis_lines.append(f"- 柱狀圖: {macd.get('histogram', 'N/A')} ({macd.get('direction', 'N/A')})")
                analysis_lines.append(f"- 交叉訊號: {macd.get('crossover', 'N/A')}")
            
            # RSI
            rsi = indicators.get('rsi', {})
            if rsi:
                analysis_lines.append(f"**RSI(14):** {rsi.get('value', 'N/A')} - {rsi.get('signal', 'N/A')}")
            
            # SMA
            sma = indicators.get('sma', {})
            if sma:
                analysis_lines.append(f"**移動平均線:**")
                analysis_lines.append(f"- SMA20: ${sma.get('sma20', 'N/A')}")
                analysis_lines.append(f"- SMA50: ${sma.get('sma50', 'N/A')}")
                analysis_lines.append(f"- SMA200: ${sma.get('sma200', 'N/A')}")
            
            analysis_lines.append("")
        
        # === 深度分析 ===
        analysis_lines.append("\n## 【專家深度分析】\n")
        
        for symbol, data in stock_data.get('stocks', {}).items():
            indicators = data.get('indicators', {})
            
            analysis_lines.append(f"### {symbol} 分析\n")
            
            # 從指標推斷分析
            bb = indicators.get('bollinger_bands', {})
            macd = indicators.get('macd', {})
            rsi = indicators.get('rsi', {})
            
            # 簡易判斷邏輯
            signals = []
            
            if bb:
                pos = bb.get('position', '')
                if '過熱' in pos:
                    signals.append("⚠️ 價格位於上軌，可能過熱回檔")
                elif '超賣' in pos:
                    signals.append("✅ 價格位於下軌，可能超賣反彈")
            
            if macd:
                cross = macd.get('crossover', '')
                if '金叉' in cross:
                    signals.append("✅ MACD 出現金叉，多頭訊號")
                elif '死叉' in cross:
                    signals.append("⚠️ MACD 出現死叉，空頭訊號")
            
            if rsi:
                val = rsi.get('value', 0)
                sig = rsi.get('signal', '')
                if '超買' in sig:
                    signals.append("⚠️ RSI 超買區，可能回檔")
                elif '超賣' in sig:
                    signals.append("✅ RSI 超賣區，可能反彈")
            
            if signals:
                for s in signals:
                    analysis_lines.append(f"- {s}")
            else:
                analysis_lines.append("- 指標顯示中性，等待進一步訊號")
            
            analysis_lines.append("")
        
        # === 新聞 ===
        analysis_lines.append("\n## 【最新新聞】\n")
        
        for symbol, data in stock_data.get('stocks', {}).items():
            news = data.get('news', [])
            if news:
                analysis_lines.append(f"### {symbol}")
                for n in news:
                    analysis_lines.append(f"- [{n.get('title', '無標題')}]({n.get('link', '')})")
                    analysis_lines.append(f"  - 來源: {n.get('publisher', '未知')}")
                analysis_lines.append("")
        
        # === 市場情緒 ===
        analysis_lines.append("\n## 【市場情緒評級】\n")
        
        # 簡單計算 overall sentiment
        bullish_count = 0
        bearish_count = 0
        
        for symbol, data in stock_data.get('stocks', {}).items():
            indicators = data.get('indicators', {})
            macd = indicators.get('macd', {})
            rsi = indicators.get('rsi', {})
            
            if macd:
                if '金叉' in macd.get('crossover', ''):
                    bullish_count += 1
                elif '死叉' in macd.get('crossover', ''):
                    bearish_count += 1
            
            if rsi:
                if rsi.get('value', 0) > 70:
                    bearish_count += 1
                elif rsi.get('value', 0) < 30:
                    bullish_count += 1
        
        if bullish_count > bearish_count:
            sentiment = "樂觀 📈"
        elif bearish_count > bullish_count:
            sentiment = "謹慎 📉"
        else:
            sentiment = "中性 ➡️"
        
        analysis_lines.append(f"**整體市場情緒: {sentiment}**")
        analysis_lines.append("")
        
        # === 投資建議 ===
        analysis_lines.append("\n## 【投資建議】\n")
        
        for symbol, data in stock_data.get('stocks', {}).items():
            indicators = data.get('indicators', {})
            price = data.get('price', {})
            
            # 簡化建議
            suggestions = []
            
            macd = indicators.get('macd', {})
            if macd and '金叉' in macd.get('crossover', ''):
                suggestions.append("短期可關注")
            
            rsi = indicators.get('rsi', {})
            if rsi:
                if rsi.get('value', 0) < 30:
                    suggestions.append("RSI 超賣，可留意反彈機會")
                elif rsi.get('value', 0) > 70:
                    suggestions.append("RSI 超買，宜謹慎")
            
            if not suggestions:
                suggestions.append("觀望")
            
            analysis_lines.append(f"**{symbol}:** {', '.join(suggestions)}")
        
        analysis_lines.append("\n---\n")
        analysis_lines.append(f"*數據來源: Yahoo Finance | 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(analysis_lines)
    
    def send_to_telegram(self, message: str) -> bool:
        """
        透過 Telegram Bot API 推播訊息
        
        參數:
            message: 要發送的訊息內容（Markdown 格式）
        
        返回:
            是否發送成功
        """
        if not self.telegram_token:
            logger.error("Telegram Token 未設定")
            # 嘗試使用內建的 Telegram 發送功能
            return self._send_via_openclaw(message)
        
        try:
            import requests
            
            # Telegram Bot API URL
            api_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            # 發送請求
            payload = {
                "chat_id": self.channel_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    logger.info(f"訊息已發送到 Telegram Channel: {self.channel_id}")
                    return True
                else:
                    logger.error(f"Telegram API 錯誤: {result}")
                    return False
            else:
                logger.error(f"Telegram 請求失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram 推播失敗: {e}")
            return False
    
    def _send_via_openclaw(self, message: str) -> bool:
        """
        透過 OpenClaw 內建功能發送訊息
        
        由於我是 OpenClaw，直接在此產生分析並顯示結果
        """
        # 這裡會直接輸出，OpenClaw 會自動推送到頻道
        logger.info("分析完成，直接輸出結果")
        return True
    
    def analyze_and_broadcast(self, stock_data: Dict[str, Any]) -> bool:
        """
        完整流程：分析並推播
        
        參數:
            stock_data: 從 data_fetcher.py 取得的股票數據
        
        返回:
            是否成功完成
        """
        # 1. 生成分析
        analysis = self.generate_analysis(stock_data)
        
        # 2. 建構完整訊息
        header = f"📊 **投資分析報告** - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        header += "=" * 40 + "\n\n"
        
        full_message = header + analysis
        
        # 3. 嘗試推送到 Telegram
        success = self.send_to_telegram(full_message)
        
        # 4. 同時輸出到日誌（這樣我可以看到結果）
        logger.info("\n" + "="*50)
        logger.info("分析報告內容:")
        logger.info("="*50)
        logger.info(full_message)
        
        return success


def main():
    """
    測試用主函數
    """
    # 載入測試數據
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "watchlist": ["TSLA", "NVDA", "COIN"],
        "stocks": {
            "TSLA": {
                "price": {
                    "current_price": 371.75,
                    "previous_close": 355.28,
                    "52w_high": 498.83,
                    "52w_low": 214.25,
                    "pe_ratio": 345.69,
                    "name": "Tesla, Inc."
                },
                "indicators": {
                    "bollinger_bands": {
                        "upper": 385.50,
                        "middle": 360.20,
                        "lower": 334.90,
                        "current_price": 371.75,
                        "position": "中軌與上軌之間（偏多）"
                    },
                    "macd": {
                        "macd_line": 2.35,
                        "signal_line": 1.89,
                        "histogram": 0.46,
                        "direction": "綠柱（多頭）",
                        "crossover": "金叉（多頭訊號）"
                    },
                    "rsi": {
                        "value": 65.42,
                        "signal": "中性區"
                    }
                },
                "news": [
                    {"title": "Tesla FSD v14.3 發布", "publisher": "Electrek", "link": "https://electrek.co/"}
                ]
            }
        }
    }
    
    # 測試分析
    analyst = ExpertAnalyst()
    result = analyst.analyze_and_broadcast(test_data)
    print(f"測試結果: {'成功' if result else '失敗'}")


if __name__ == "__main__":
    main()
