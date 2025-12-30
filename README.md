# 🧱 Brick3 MEV Platform

> **Real-time MEV Infrastructure for Monad Blockchain**

[![API Status](https://img.shields.io/badge/API-Live-green)](https://brick3-api.onrender.com/health)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-blue)](https://brick3.streamlit.app)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎯 Overview

Brick3 is a comprehensive MEV (Maximal Extractable Value) infrastructure platform built for **Monad blockchain**. We provide real-time MEV detection, automated bot execution, and transparent revenue distribution.

### Key Features

- 🔍 **Real-time Mempool Monitoring** - Track pending transactions on Monad
- 🤖 **Automated MEV Bots** - Sandwich, Arbitrage, Liquidation, Backrun
- 💰 **Revenue Distribution** - 70% to shMON holders, 20% Brick3, 10% Validators
- 🔗 **FastLane Atlas Integration** - Bundle submission via Atlas Protocol
- 📊 **Live Dashboard** - Monitor opportunities and executions

---

## 🔌 Live Services

| Service | URL | Status |
|---------|-----|--------|
| 📊 **Dashboard** | https://brick3.streamlit.app | ✅ Live |
| 🔌 **API** | https://brick3-api.onrender.com | ✅ Live |
| 📚 **API Docs** | https://brick3-api.onrender.com/docs | ✅ Live |
| 🌐 **Website** | https://www.brick3.fun | ✅ Live |
| 🔑 **Get API Key** | https://www.brick3.fun/get-api-key | ✅ Live |

---

## 🚀 Quick Start

### 1. Get API Key

Request your API key at: **https://www.brick3.fun/get-api-key**

Or contact: **partnership@brick3.fun**

### 2. Test Connection

```bash
# Health check (no auth required)
curl https://brick3-api.onrender.com/health

# Check bot status (requires API key)
curl -H "X-API-Key: YOUR_API_KEY" \
  https://brick3-api.onrender.com/api/v1/bots/status
```

### 3. Explore API Docs

Interactive documentation: **https://brick3-api.onrender.com/docs**

---

## 📡 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API status |
| `/api/v1/bots/status` | GET | All bot statuses |
| `/api/v1/bots/start/{type}` | POST | Start a bot |
| `/api/v1/bots/stop-all` | POST | Stop all bots |

### Simulation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/simulate/sandwich` | GET | Simulate sandwich attack |
| `/api/v1/simulate/arbitrage` | GET | Simulate arbitrage |

### Revenue

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/revenue/summary` | GET | Revenue statistics |
| `/api/v1/revenue/calculate` | GET | Distribution calculator |
| `/api/v1/revenue/estimate-apy` | GET | APY boost estimation |

### Mainnet Engine

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/mainnet/status` | GET | Engine status |
| `/api/v1/mainnet/start` | POST | Start engine (Enterprise) |
| `/api/v1/mainnet/opportunities` | GET | Live opportunities |
| `/api/v1/mainnet/stats` | GET | Performance stats |

### FastLane Integration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/fastlane/info` | GET | Integration details |
| `/api/v1/fastlane/stats` | GET | Partnership metrics |
| `/api/v1/fastlane/execute` | POST | Execute opportunity |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BRICK3 MEV PLATFORM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   Monad      │──▶│   Mempool    │──▶│ Opportunity  │    │
│  │   RPC        │   │   Monitor    │   │  Detector    │    │
│  └──────────────┘   └──────────────┘   └──────┬───────┘    │
│                                                │            │
│                                                ▼            │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │  FastLane    │◀──│   Bundle     │◀──│ Transaction  │    │
│  │  Atlas       │   │   Submitter  │   │  Builder     │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Revenue Distribution                     │  │
│  │   70% shMON Holders │ 20% Brick3 │ 10% Validators    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 Revenue Model

All MEV profits are automatically distributed:

| Recipient | Share | Description |
|-----------|-------|-------------|
| **shMON Holders** | 70% | Passive income for stakers |
| **Brick3** | 20% | Platform development |
| **Validators** | 10% | Network security |

### APY Boost Calculator

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://brick3-api.onrender.com/api/v1/revenue/estimate-apy?daily_mev_volume_usd=5000&tvl_usd=1000000"
```

---

## 🔐 API Key Tiers

| Tier | Price | API Calls/Day | Features |
|------|-------|---------------|----------|
| **Free Trial** | $0 | 1,000 | 7-day full access |
| **Pro** | $49/mo | 10,000 | Full bot access |
| **Enterprise** | $199/mo | Unlimited | Mainnet execution |

---

## 🤝 FastLane Partnership

Brick3 integrates with FastLane's Atlas Protocol for MEV bundle submission.

For FastLane integration documentation, see: **[FastLaneREADME.md](./FastLaneREADME.md)**

### Partner Benefits

- Priority bundle submission
- Custom revenue share
- Dedicated technical support
- Co-branded dashboard

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API Docs](https://brick3-api.onrender.com/docs) | Interactive API documentation |
| [FastLaneREADME.md](./FastLaneREADME.md) | FastLane integration guide |
| [BRICK3_FASTLANE_PARTNERSHIP.md](./BRICK3_FASTLANE_PARTNERSHIP.md) | Partnership details |
| [BRICK3_FASTLANE_FREE_TRIAL.md](./BRICK3_FASTLANE_FREE_TRIAL.md) | Free trial guide |

---

## 🛠️ Local Development

```bash
# Clone repository
git clone https://github.com/brienteth/monmev-dashboard.git
cd monmev-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (see .env.example)
cp .env.example .env

# Run API
python monmev_api.py

# Run Dashboard (separate terminal)
streamlit run monmev_dashboard.py
```

### Project Structure

```
monmev-dashboard/
├── monmev_api.py           # FastAPI backend
├── monmev_dashboard.py     # Streamlit dashboard
├── mainnet_mev_engine.py   # Mainnet MEV engine
├── apriori_integration.py  # Validator integration
├── fastlane_integration.py # FastLane integration
├── requirements.txt        # Python dependencies
├── README.md              # This file (general project)
├── FastLaneREADME.md      # FastLane integration docs
├── BRICK3_FASTLANE_PARTNERSHIP.md
├── BRICK3_FASTLANE_FREE_TRIAL.md
└── start.sh               # Startup script
```

---

## 🔧 Environment Variables

Create `.env` file with required variables. Contact partnership@brick3.fun for production credentials.

```env
# Required for production
MONAD_RPC_URL=https://rpc.monad.xyz
BOT_PRIVATE_KEY=<provided_separately>
FASTLANE_API_KEY=<provided_separately>
ATLAS_CONTRACT=<provided_separately>

# API Configuration
PORT=8000
HOST=0.0.0.0
```

---

## 📞 Contact

| Purpose | Contact |
|---------|---------|
| **Partnership** | partnership@brick3.fun |
| **Technical** | info@brick3.fun |
| **Website** | https://www.brick3.fun |
| **Dashboard** | https://brick3.streamlit.app |
| **Twitter** | @Brick3MEV |
| **Discord** | discord.gg/brick3 |

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 📜 Changelog

### v3.0.0 (December 30, 2025)
- ✅ Mainnet MEV Engine with real mempool monitoring
- ✅ FastLane Atlas Protocol integration
- ✅ Transaction Builder for MEV bundles
- ✅ Opportunity Detector (Sandwich + Arbitrage)

### v2.0.0 (December 30, 2025)
- ✅ Production-ready MEV bot engine
- ✅ 4 bot types: sandwich, arbitrage, liquidation, backrun
- ✅ Revenue distribution system (70/20/10)
- ✅ Transaction simulation endpoints

### v1.0.0 (December 28, 2025)
- Initial release with basic MEV detection

---

**Built for Monad. Powered by FastLane Atlas.**

© 2025 Brick3 MEV Platform
