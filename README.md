# 🧱 Brick3 MEV Platform

> **Real-time MEV Infrastructure for Monad Blockchain**  
> Built for FastLane Atlas Protocol Integration

[![API Status](https://img.shields.io/badge/API-Live-green)](https://brick3-api.onrender.com/health)
[![Dashboard](https://img.shields.io/badge/Dashboard-Online-blue)](https://brick3.streamlit.app)
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

---

## 🎯 Overview

Brick3 is a production-ready MEV (Maximal Extractable Value) detection and execution platform specifically designed for Monad blockchain. We provide real-time mempool monitoring, automated MEV bot execution, and transparent revenue distribution.

### Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **Mempool Monitor** | Real-time pending transaction analysis |
| 🤖 **MEV Bots** | Sandwich, Arbitrage, Liquidation, Backrun |
| 💰 **Revenue Sharing** | 70% shMON / 20% Brick3 / 10% Validators |
| ⚡ **FastLane Integration** | Atlas Protocol bundle submission |
| 📊 **Dashboard** | Live monitoring and analytics |

---

## 🚀 Quick Start

### 1. Test API Connection

```bash
# Health check (no auth required)
curl https://brick3-api.onrender.com/health
```

### 2. Get Bot Status

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  https://brick3-api.onrender.com/api/v1/bots/status
```

### 3. Run Simulation

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://brick3-api.onrender.com/api/v1/simulate/sandwich?victim_value_mon=100"
```

> 📧 **Get your API key:** Contact info@brick3.fun

---

## 📡 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API status check |
| `/api/v1/bots/status` | GET | All bot statuses |
| `/api/v1/bots/start/{type}` | POST | Start specific bot |
| `/api/v1/bots/stop-all` | POST | Emergency stop |
| `/api/v1/simulate/sandwich` | GET | Sandwich simulation |
| `/api/v1/simulate/arbitrage` | GET | Arbitrage simulation |
| `/api/v1/revenue/summary` | GET | Revenue statistics |
| `/api/v1/revenue/calculate` | GET | Distribution calculator |

### Mainnet Engine Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/mainnet/status` | GET | Engine status |
| `/api/v1/mainnet/start` | POST | Start engine (Enterprise) |
| `/api/v1/mainnet/opportunities` | GET | Live opportunities |
| `/api/v1/mainnet/executions` | GET | Execution history |
| `/api/v1/mainnet/stats` | GET | Performance stats |

### FastLane Integration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/fastlane/info` | GET | Integration details |
| `/api/v1/fastlane/stats` | GET | Partnership metrics |
| `/api/v1/fastlane/execute` | POST | Execute via Atlas |

---

## 🔧 FastLane Integration Guide

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BRICK3 MEV ENGINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Monad RPC ──▶ Mempool Monitor ──▶ Opportunity Detector   │
│                                              │              │
│                                              ▼              │
│   FastLane Atlas ◀── Bundle Submitter ◀── TX Builder       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Environment Configuration

Create a `.env` file with credentials (provided separately):

```bash
# Monad RPC
MONAD_RPC=https://rpc.monad.xyz

# API Configuration
API_KEY=<provided_separately>

# Mainnet Engine (Enterprise)
BOT_PRIVATE_KEY=<your_wallet_private_key>
FASTLANE_API_KEY=<provided_separately>
ATLAS_CONTRACT=<provided_separately>
```

### Python Integration

```python
import requests

BASE_URL = "https://brick3-api.onrender.com"
API_KEY = "<your_api_key>"  # Get from info@brick3.fun
HEADERS = {"X-API-Key": API_KEY}

# Check status
status = requests.get(f"{BASE_URL}/api/v1/bots/status", headers=HEADERS)
print(status.json())

# Run simulation
sim = requests.get(
    f"{BASE_URL}/api/v1/simulate/sandwich",
    params={"victim_value_mon": 100},
    headers=HEADERS
)
print(sim.json())

# Calculate revenue distribution
rev = requests.get(
    f"{BASE_URL}/api/v1/revenue/calculate",
    params={"profit_mon": 100},
    headers=HEADERS
)
print(rev.json())
```

### JavaScript Integration

```javascript
const BASE_URL = "https://brick3-api.onrender.com";
const API_KEY = "<your_api_key>"; // Get from info@brick3.fun

async function brick3Demo() {
  const headers = { "X-API-Key": API_KEY };
  
  // Bot status
  const status = await fetch(`${BASE_URL}/api/v1/bots/status`, { headers });
  console.log(await status.json());
  
  // Simulation
  const sim = await fetch(
    `${BASE_URL}/api/v1/simulate/sandwich?victim_value_mon=100`,
    { headers }
  );
  console.log(await sim.json());
}

brick3Demo();
```

---

## 💰 Revenue Distribution Model

All MEV profits are automatically distributed:

```
┌────────────────────────────────────────┐
│         MEV PROFIT (100%)              │
├────────────────────────────────────────┤
│                                        │
│   ┌──────────┐  70%                    │
│   │  shMON   │────────▶ Stakers        │
│   │ Holders  │                         │
│   └──────────┘                         │
│                                        │
│   ┌──────────┐  20%                    │
│   │  Brick3  │────────▶ Platform       │
│   └──────────┘                         │
│                                        │
│   ┌──────────┐  10%                    │
│   │Validators│────────▶ Network        │
│   └──────────┘                         │
│                                        │
└────────────────────────────────────────┘
```

---

## 📊 Live Dashboard

Access the interactive dashboard at: **https://brick3.streamlit.app**

Features:
- Real-time MEV opportunity monitoring
- Bot management interface
- Revenue analytics
- Simulation tools

---

## 🔐 Security

- API keys are required for all authenticated endpoints
- Rate limiting applied per tier
- Enterprise tier required for mainnet execution
- Private keys never stored on servers

---

## 📞 Contact

| Purpose | Contact |
|---------|---------|
| 🔑 **API Access** | info@brick3.fun |
| 🤝 **Partnership** | info@brick3.fun |
| 🌐 **Website** | https://www.brick3.fun |
| 📊 **Dashboard** | https://brick3.streamlit.app |

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

**Built for Monad. Powered by FastLane Atlas.**

© 2025 Brick3 Technologies
