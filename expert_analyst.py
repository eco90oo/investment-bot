#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
expert_analyst.py - 金融專家分析與Telegram推播模組
============================================================

本模組負責：
1. 呼叫 OpenClaw API 進行專業分析
2. 整合 Telegram Bot API 推播分析結果

作者：Investment Bot
建立日期：2026-04-03
============================================================
"""

import os
import json
import logging
import requests
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
    
    用途：結合 OpenClaw API 與 Telegram 實現自動化投資分析推播
    """
    
    def __init__(self):
        """
        初始化分析器，載入環境變數
        """
        # 從環境變數取得配置
        self.openclaw_url = os.getenv("OPENCLAW_API_URL", "http://localhost:8000/v1/chat/completions")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "")
        
        logger.info(f"初始化 ExpertAnalyst，OpenClaw API: {self.openclaw_url}")
    
    def analyze_with_openclaw(self, stock_data: Dict[str, Any]) -> str:
        """
        呼叫 OpenClaw API 進行專業分析
        
        參數:
            stock_data: 從 data_fetcher.py 取得的結構化股票數據
        
        返回:
            OpenClaw 產出的分析報告（Markdown 格式）
        """
        # 構建系統提示詞 - 扮演 20 年經驗的避險基金經理人
        system_prompt = """你是一位具備 20 年經驗的資深避險基金經理人，專精於：
- 總體經濟分析（GDP、利率、匯率、央行政策）
- 技術分析（布林通道、MACD、RSI、均線）
- 產業趨勢與供應鏈分析
- 風險管理與部位控制

你的分析風格：
- 數據驅動，邏輯嚴謹
- 擅長發現指標背離與過熱預警
- 提供具體的進場/退場建議
- 會清楚標示樂觀與保守情境

請根據以下真實市場數據，進行深度邏輯推理分析：

"""
        
        # 構建用戶提示詞 - 包含所有股票數據
        user_prompt = f"""
=== 市場數據時間 ===
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 監控標的 ===
{', '.join(stock_data.get('watchlist', []))}

"""
        
        # 逐一添加各股票的詳細數據
        for symbol, data in stock_data.get('stocks', {}).items():
            price = data.get('price', {})
            indicators = data.get('indicators', {})
            news = data.get('news', [])
            
            user_prompt += f"""
--- {symbol} ({price.get('name', symbol)}) ---
【即時價格】
- 目前價格: ${price.get('current_price', 'N/A')}
- 昨收價: ${price.get('previous_close', 'N/A')}
- 開盤: ${price.get('open', 'N/A')}
- 52週區間: ${price.get('52w_low', 'N/A')} - ${price.get('52w_high', 'N/A')}
- 本益比: {price.get('pe_ratio', 'N/A')}

【技術指標】
"""
            
            # 添加布林通道
            bb = indicators.get('bollinger_bands', {})
            if bb:
                user_prompt += f"""
- Bollinger Bands:
  * 上軌: ${bb.get('upper', 'N/A')}
  * 中軌: ${bb.get('middle', 'N/A')}
  * 下軌: ${bb.get('lower', 'N/A')}
  * 位置: {bb.get('position', 'N/A')}
"""
            
            # 添加 MACD
            macd = indicators.get('macd', {})
            if macd:
                user_prompt += f"""
- MACD:
  * 快線: {macd.get('macd_line', 'N/A')}
  * 慢線: {macd.get('signal_line', 'N/A')}
  * 柱狀圖: {macd.get('histogram', 'N/A')} ({macd.get('direction', 'N/A')})
  * 交叉訊號: {macd.get('crossover', 'N/A')}
"""
            
            # 添加 RSI
            rsi = indicators.get('rsi', {})
            if rsi:
                user_prompt += f"""
- RSI(14): {rsi.get('value', 'N/A')} - {rsi.get('signal', 'N/A')}
"""
            
            # 添加 SMA
            sma = indicators.get('sma', {})
            if sma:
                user_prompt += f"""
- 移動平均線:
  * SMA20: ${sma.get('sma20', 'N/A')}
  * SMA50: ${sma.get('sma50', 'N/A')}
  * SMA200: ${sma.get('sma200', 'N/A')}
"""
            
            # 添加新聞
            if news:
                user_prompt += f"""
【最新新聞】（共 {len(news)} 則）
"""
                for i, n in enumerate(news, 1):
                    user_prompt += f"""
{i}. {n.get('title', '無標題')}
   - 來源: {n.get('publisher', '未知')}
   - 連結: {n.get('link', '無')}
"""
            
            user_prompt += "\n"
        
        # 添加輸出格式要求
        user_prompt += """
=== 輸出格式要求 ===

請產出以下結構的分析報告：

## 【今日觀察標的】
（列出今天需要特別關注的標的及原因）

## 【技術指標真實數據清單】
（列出關鍵指標的具體數值）

## 【專家深度分析】
（針對每個標的進行邏輯推理，重點包括：
- 指標背離分析
- 過熱/超賣預警
- 支撐/壓力位判斷
- 近期新聞影響評估）

## 【市場情緒評級】
（總體市場情緒：極度樂觀 / 樂觀 / 中性 / 謹慎 / 極度謹慎）

## 【投資建議】
（短期 1-7天 / 中期 1-3個月 / 長期 6個月+）

⚠️ 請確保所有建議都基於上述真實數據，切勿編造數值！
"""
        
        # 呼叫 OpenClaw API
        try:
            logger.info("正在呼叫 OpenClaw API 進行分析...")
            
            payload = {
                "model": "minimax-portal/MiniMax-M2.5",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            response = requests.post(
                self.openclaw_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # 2分鐘逾時
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info("OpenClaw API 分析完成")
                return analysis
            else:
                logger.error(f"OpenClaw API 錯誤: {response.status_code}")
                return f"❌ OpenClaw API 錯誤: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error("OpenClaw API 逾時")
            return "❌ 分析逾時，請稍後重試"
        except requests.exceptions.ConnectionError:
            logger.error("無法連接 OpenClaw API")
            return "❌ 無法連接 OpenClaw API，請檢查服務是否運行"
        except Exception as e:
            logger.error(f"分析過程發生錯誤: {e}")
            return f"❌ 分析錯誤: {str(e)}"
    
    def send_to_telegram(self, message: str) -> bool:
        """
        透過 Telegram Bot API 推播訊息
        
        參數:
            message: 要發送的訊息內容（Markdown 格式）
        
        返回:
            是否發送成功
        """
        if not self.telegram_token or not self.channel_id:
            logger.error("Telegram 配置不完整")
            return False
        
        try:
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
    
    def analyze_and_broadcast(self, stock_data: Dict[str, Any]) -> bool:
        """
        完整流程：分析並推播
        
        參數:
            stock_data: 從 data_fetcher.py 取得的股票數據
        
        返回:
            是否成功完成
        """
        # 1. OpenClaw 分析
        analysis = self.analyze_with_openclaw(stock_data)
        
        # 2. 建構完整訊息
        header = f"📊 **投資分析報告** - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        header += "=" * 40 + "\n\n"
        
        full_message = header + analysis
        
        # 3. 推送到 Telegram
        return self.send_to_telegram(full_message)


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
