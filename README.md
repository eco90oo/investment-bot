# 📈 Investment Bot - 自動化投資分析系統

[![Python Version](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

自動化投資分析系統，整合真實市場數據、專業技術分析與 Telegram 推播。

## ✨ 功能特色

- 📊 **即時股價監控**：支援 TSLA、NVDA、COIN 等多標的
- 📈 **技術指標計算**：布林通道、MACD、RSI、均線
- 🤖 **AI 專家分析**：結合 OpenClaw API 進行深度分析
- 📱 **Telegram 推播**：自動將分析結果推送到指定 Channel
- ⏰ **智能排程**：美股盤前、盤中、盤後自動執行
- 🔄 **背景持續運行**：支援 systemd Daemon 部署

---

## 🛠️ 安裝步驟

### 1. 複製專案

```bash
cd /home/node/.openclaw/workspace
git clone https://github.com/your-username/investment-bot.git
cd investment-bot
```

### 2. 建立虛擬環境（使用 uv）

```bash
# 如果還沒安裝 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 建立虛擬環境
uv venv
uv sync
```

### 3. 設定環境變數

```bash
# 複製範例檔案
cp .env.example .env

# 編輯 .env 檔案，填入真實數值
nano .env
```

`.env` 檔案內容：
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here
OPENCLAW_API_URL=http://localhost:8000/v1/chat/completions
WATCHLIST=TSLA,NVDA,COIN
```

### 4. 取得 Telegram Bot Token

1. 開啟 Telegram，搜尋 @BotFather
2. 傳送 `/newbot` 建立新機器人
3. 取得 Bot Token（例如：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）
4. 將機器人加入你的 Channel 並設為管理員

---

## 🚀 使用方式

### 測試執行

```bash
# 測試模式（單次執行）
uv run python main.py --test

# 單次執行
uv run python main.py --once
```

### 持續運行（systemd）

```bash
# 複製 service 檔案到 systemd 目錄
sudo cp investment-bot.service /etc/systemd/system/

# 重新載入 systemd
sudo systemctl daemon-reload

# 啟動服務
sudo systemctl start investment-bot

# 設定開機自動啟動
sudo systemctl enable investment-bot

# 查看服務狀態
sudo systemctl status investment-bot

# 查看即時日誌
sudo journalctl -fu investment-bot -n 100
```

---

## 📋 排程說明

| 時間（台北）| 時間（美東）| 說明 |
|-------------|-------------|------|
| 13:00 | 01:00 ET | 盤中分析 |
| 19:00 | 03:00 ET | 盤前分析 |
| 21:30 | 05:30 ET | 盤後分析 |
| 每4小時 | - | 持續更新 |

---

## 📁 專案結構

```
investment-bot/
├── .env.example      # 環境變數範例
├── .gitignore       # Git 忽略規則
├── pyproject.toml   # uv 專案配置
├── README.md        # 說明文件
├── main.py          # 主程式
├── data_fetcher.py  # 數據獲取模組
├── expert_analyst.py # 專家分析模組
└── investment-bot.service # systemd 服務檔
```

---

## 🔧 技術棧

- **Python 3.10+**
- **uv** - 環境管理
- **yfinance** - Yahoo Finance 數據
- **pandas** - 數據處理
- **pandas_ta** - 技術指標
- **python-telegram-bot** - Telegram API
- **schedule** - 排程管理
- **OpenClaw** - AI 分析引擎

---

## 📝 License

MIT License
