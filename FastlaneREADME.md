# 🧱 Brick3 MEV Platform - FastLane Integration Complete Documentation

> **Prepared for:** FastLane Team  
> **Version:** 3.0 Production Mainnet  
> **Date:** December 30, 2025  
> **Contact:** partnership@brick3.fun

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Live Services](#live-services)
3. [Quick Start Guide](#quick-start-guide)
4. [Mainnet MEV Engine](#mainnet-mev-engine)
5. [API Endpoints](#api-endpoints)
6. [Bot Control System](#bot-control-system)
7. [Revenue Distribution](#revenue-distribution)
8. [Brick3 Technologies](#brick3-technologies)
9. [Integration Examples](#integration-examples)
10. [SDK & Libraries](#sdk--libraries)
11. [7-Day Free Trial](#7-day-free-trial)
12. [Pricing & Tiers](#pricing--tiers)
13. [WebSocket Streaming](#websocket-streaming)
14. [Error Handling](#error-handling)
15. [Contact & Support](#contact--support)

---

## 🎯 Executive Summary

Brick3 is a comprehensive MEV (Maximal Extractable Value) infrastructure platform built specifically for **Monad blockchain**. We provide real-time MEV detection, automated bot execution, and transparent revenue distribution through our partnership with FastLane's Atlas Protocol.

### ⚡ What's New in v3.0

| Feature | Status | Description |
|---------|--------|-------------|
| **Mainnet Engine** | ✅ Live | Real mempool monitoring on Monad |
| **FastLane Bundle Submission** | ✅ Ready | Atlas Protocol integration |
| **Transaction Builder** | ✅ Ready | Sign and build MEV bundles |
| **Opportunity Detector** | ✅ Live | Sandwich & Arbitrage detection |

### Key Value Propositions

| 🎯 For FastLane | 💰 Revenue Impact |
|-----------------|-------------------|
| MEV detection infrastructure | 70% revenue to shMON holders |
| Bot execution layer | +12-30% APY boost for stakers |
| Real-time mempool analysis | $50K+ monthly MEV volume potential |
| Seamless Atlas integration | Transparent on-chain distribution |

### Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **MEV Detection** | Real-time sandwich, arbitrage, liquidation, backrun detection |
| 🤖 **Bot Automation** | 4 specialized bots with configurable parameters |
| 💰 **Revenue Sharing** | 70/20/10 split (shMON holders/Brick3/Validators) |
| 📊 **Analytics** | Detailed profit/loss tracking and APY calculations |
| 🔄 **WebSocket** | Live opportunity streaming with <100ms latency |

---

## 🔌 Live Services

### Production URLs

| Service | URL | Status |
|---------|-----|--------|
| 📊 **Dashboard** | https://brick3.streamlit.app | ✅ Live |
| 🔌 **API** | https://brick3-api.onrender.com | ✅ Live |
| 📚 **API Docs** | https://brick3-api.onrender.com/docs | ✅ Live |
| 🌐 **Website** | https://www.brick3.fun | ✅ Live |
| 🔑 **Get API Key** | https://www.brick3.fun/get-api-key | ✅ Live |

---

## ⚡ Quick Start Guide

### Test the API in 30 Seconds

```bash
# Base URL
BASE_URL="https://brick3-api.onrender.com"

# 1. Health Check (No auth required)
curl $BASE_URL/health

# 2. Get Bot Status
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/bots/status"

# 3. Start Sandwich Bot
curl -X POST -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/bots/start/sandwich"

# 4. Simulate Sandwich Attack
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/simulate/sandwich?victim_value_mon=100"

# 5. Simulate Arbitrage
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/simulate/arbitrage?amount_in_mon=50&hops=3"

# 6. Get Revenue Summary
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/revenue/summary"

# 7. Calculate Distribution
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/revenue/calculate?profit_mon=100"

# 8. Estimate APY Boost
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/revenue/estimate-apy?daily_mev_volume_usd=5000&tvl_usd=1000000"

# 9. FastLane Info
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/fastlane/info"

# 10. FastLane Stats
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/fastlane/stats"

# 11. Stop All Bots
curl -X POST -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/bots/stop-all"
```

---

## 🚀 Mainnet MEV Engine

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    BRICK3 MAINNET MEV ENGINE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│   │   Monad     │───▶│   Mempool    │───▶│  Opportunity    │  │
│   │   RPC       │    │   Monitor    │    │  Detector       │  │
│   └─────────────┘    └──────────────┘    └────────┬────────┘  │
│                                                    │           │
│                                                    ▼           │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│   │  FastLane   │◀───│   Bundle     │◀───│  Transaction    │  │
│   │  Atlas      │    │   Submitter  │    │  Builder        │  │
│   └─────────────┘    └──────────────┘    └─────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Revenue Distribution (70/20/10)              │  │
│  │   70% shMON Holders │ 20% Brick3 │ 10% Validators        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mainnet API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/mainnet/status` | GET | Engine status & wallet info |
| `/api/v1/mainnet/start` | POST | Start MEV engine (Enterprise) |
| `/api/v1/mainnet/stop` | POST | Stop MEV engine |
| `/api/v1/mainnet/bot/{type}` | POST | Enable/disable bot |
| `/api/v1/mainnet/opportunities` | GET | Live opportunities |
| `/api/v1/mainnet/executions` | GET | Execution history |
| `/api/v1/mainnet/stats` | GET | Performance stats |
| `/api/v1/mainnet/configure` | POST | Configure engine |

### Quick Start - Mainnet Engine

```bash
# 1. Check mainnet engine status
curl -H "X-API-Key: YOUR_API_KEY" \
  https://brick3-api.onrender.com/api/v1/mainnet/status

# 2. View live opportunities (Enterprise key required for execution)
curl -H "X-API-Key: YOUR_API_KEY" \
  https://brick3-api.onrender.com/api/v1/mainnet/opportunities

# 3. Get mainnet stats
curl -H "X-API-Key: YOUR_API_KEY" \
  https://brick3-api.onrender.com/api/v1/mainnet/stats
```

---

## 📡 API Endpoints

### Health & Status

#### `GET /health`
Check API health status.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-30T00:00:00Z",
  "rpc_connected": true,
  "monitoring_active": true,
  "opportunities_count": 42
}
```

### MEV Opportunities

#### `GET /api/v1/opportunities`
Get detected MEV opportunities.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | int | 20 | Max results (1-100) |
| `min_profit_usd` | float | 0 | Minimum profit threshold |
| `mev_type` | string | all | Filter by type: sandwich, arbitrage, liquidation, backrun |

**Response:**
```json
{
  "success": true,
  "opportunities": [
    {
      "id": "opp_abc123",
      "type": "sandwich",
      "tx_hash": "0x1234...",
      "target_contract": "0xDEX...",
      "estimated_profit_usd": 125.50,
      "confidence": 0.85,
      "timestamp": "2025-12-30T00:00:00Z",
      "details": {
        "victim_swap_amount": 5000,
        "token_pair": "MON/USDC",
        "dex": "MonadSwap"
      }
    }
  ],
  "total": 156,
  "page": 1
}
```

---

## 🤖 Bot Control System

### Bot Types

| Bot | Description | Risk Level |
|-----|-------------|------------|
| **Sandwich** | Frontrun/backrun large swaps | Medium |
| **Arbitrage** | Cross-DEX price differences | Low |
| **Liquidation** | DeFi liquidation opportunities | Medium |
| **Backrun** | Follow large transactions | Low |

### Bot Control Endpoints

#### `GET /api/v1/bots/status`
Get status of all MEV bots.

**Response:**
```json
{
  "success": true,
  "bots": {
    "sandwich": {
      "status": "running",
      "config": {
        "min_profit_usd": 50.0,
        "max_gas_gwei": 100.0,
        "slippage_percent": 0.5,
        "enabled": true
      }
    },
    "arbitrage": {
      "status": "stopped",
      "config": {...}
    },
    "liquidation": {
      "status": "stopped",
      "config": {...}
    },
    "backrun": {
      "status": "running",
      "config": {...}
    }
  },
  "engine_running": true,
  "stats": {
    "total_opportunities": 156,
    "executed_trades": 45,
    "successful_trades": 42,
    "total_profit_mon": 1250.5,
    "total_profit_usd": 1875.75
  }
}
```

#### `POST /api/v1/bots/start/{bot_type}`
Start a specific bot. Bot Types: `sandwich`, `arbitrage`, `liquidation`, `backrun`

#### `POST /api/v1/bots/stop/{bot_type}`
Stop a specific bot.

#### `POST /api/v1/bots/stop-all`
Stop all bots.

### Simulation Endpoints

#### `POST /api/v1/simulate/sandwich`
Simulate a sandwich attack.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `victim_value_mon` | float | Victim swap value in MON |

**Response:**
```json
{
  "success": true,
  "simulation": {
    "gross_profit_mon": 2.5,
    "gas_cost_mon": 0.015,
    "net_profit_mon": 2.485,
    "net_profit_usd": 3.73,
    "confidence": 0.85,
    "execution_path": [
      "1. Frontrun: Buy 25.00 MON",
      "2. Victim swap: 100.00 MON",
      "3. Backrun: Sell 25.00 MON"
    ]
  }
}
```

#### `POST /api/v1/simulate/arbitrage`
Simulate an arbitrage trade.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `amount_in_mon` | float | Starting amount |
| `hops` | int | Number of DEX hops (2-5) |

---

## 💰 Revenue Distribution

### Standard Distribution Model (70/20/10)

```
┌─────────────────────────────────────────────────────────────┐
│                    MEV REVENUE FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     MEV Captured ──────────────────────────┐                │
│         │                                  │                │
│         ▼                                  │                │
│    ┌─────────┐                             │                │
│    │ Total   │                             │                │
│    │ Revenue │                             │                │
│    └────┬────┘                             │                │
│         │                                  │                │
│    ┌────┴────┬────────────┬───────────┐   │                │
│    ▼         ▼            ▼           │   │                │
│ ┌──────┐ ┌──────┐    ┌──────────┐     │   │                │
│ │ 70%  │ │ 20%  │    │   10%    │     │   │                │
│ │shMON │ │Brick3│    │Validators│     │   │                │
│ │Holders│ │      │    │          │     │   │                │
│ └──────┘ └──────┘    └──────────┘     │   │                │
│                                        │   │                │
└────────────────────────────────────────┴───┴────────────────┘
```

| Recipient | Share | Description |
|-----------|-------|-------------|
| **shMON Holders** | 70% | Passive income for stakers |
| **Brick3** | 20% | Platform development |
| **Validators** | 10% | Network security |

### Revenue Endpoints

#### `GET /api/v1/revenue/summary`
Get revenue distribution summary.

#### `GET /api/v1/revenue/estimate-apy`
Estimate APY boost from MEV.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `daily_mev_volume_usd` | float | 10000 | Daily MEV capture |
| `tvl_usd` | float | 10000000 | Total Value Locked |

**Response:**
```json
{
  "success": true,
  "estimate": {
    "daily_mev_volume_usd": 10000,
    "tvl_usd": 10000000,
    "daily_shmon_earnings_usd": 7000,
    "yearly_shmon_earnings_usd": 2555000,
    "estimated_apy_boost_percent": 25.55,
    "note": "APY boost added to base staking rewards"
  }
}
```

#### `POST /api/v1/revenue/calculate`
Calculate distribution for a profit amount.

**Response:**
```json
{
  "success": true,
  "distribution": {
    "total_profit_mon": 100,
    "total_profit_usd": 150,
    "breakdown": {
      "shmon_holders": {
        "percentage": 70,
        "amount_mon": 70,
        "amount_usd": 105
      },
      "brick3": {
        "percentage": 20,
        "amount_mon": 20,
        "amount_usd": 30
      },
      "validators": {
        "percentage": 10,
        "amount_mon": 10,
        "amount_usd": 15
      }
    }
  }
}
```

### APY Boost Calculator

| Daily MEV Volume | TVL | shMON Daily | Annual APY Boost |
|------------------|-----|-------------|------------------|
| $5,000 | $1M | $3,500 | +127.75% |
| $10,000 | $5M | $7,000 | +51.10% |
| $25,000 | $10M | $17,500 | +63.88% |
| $50,000 | $20M | $35,000 | +63.88% |
| $100,000 | $50M | $70,000 | +51.10% |

---

## 🚀 Brick3 Technologies

### 🚀 Brick3 Turbo™
**Ultra-Fast Transaction Relay**

- Sub-millisecond transaction propagation
- Direct validator connections
- Priority block inclusion
- Latency: <50ms average

```bash
# Turbo™ enabled request
curl -X POST "https://api.brick3.fun/v1/turbo/submit" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"tx": "0x...", "priority": "high"}'
```

### 💾 Brick3 Flash™
**Instant Data Caching**

- Real-time price feeds
- Mempool snapshot caching
- Historical data access
- Response time: <10ms

### 🌊 Brick3 Flow™
**Advanced Mempool Streaming**

- Real-time pending transaction stream
- MEV opportunity detection
- WebSocket + REST support
- Latency: <100ms

```javascript
// Flow™ WebSocket connection
const ws = new WebSocket('wss://api.brick3.fun/v1/flow/stream');
ws.onmessage = (event) => {
  const opportunity = JSON.parse(event.data);
  console.log('MEV Opportunity:', opportunity);
};
```

### 🔗 Brick3 Link™
**Private RPC Connection**

- Dedicated infrastructure
- No rate limits
- Geographic optimization
- 99.9% uptime SLA

---

## 💻 Integration Examples

### Python SDK

```python
import requests

class Brick3Client:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://brick3-api.onrender.com"
        self.headers = {"X-API-Key": api_key}
    
    def health(self):
        return requests.get(f"{self.base_url}/health").json()
    
    def get_bot_status(self):
        return requests.get(
            f"{self.base_url}/api/v1/bots/status",
            headers=self.headers
        ).json()
    
    def start_bot(self, bot_type: str):
        return requests.post(
            f"{self.base_url}/api/v1/bots/start/{bot_type}",
            headers=self.headers
        ).json()
    
    def simulate_sandwich(self, victim_value_mon: float):
        return requests.get(
            f"{self.base_url}/api/v1/simulate/sandwich",
            params={"victim_value_mon": victim_value_mon},
            headers=self.headers
        ).json()
    
    def calculate_distribution(self, profit_mon: float):
        return requests.get(
            f"{self.base_url}/api/v1/revenue/calculate",
            params={"profit_mon": profit_mon},
            headers=self.headers
        ).json()
    
    def get_opportunities(self, limit=20, min_profit=0):
        return requests.get(
            f"{self.base_url}/api/v1/opportunities",
            headers=self.headers,
            params={"limit": limit, "min_profit_usd": min_profit}
        ).json()

# Usage
client = Brick3Client("YOUR_API_KEY")
print(client.health())
print(client.get_bot_status())
```

### JavaScript SDK

```javascript
class Brick3Client {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = "https://brick3-api.onrender.com";
  }

  async request(endpoint, options = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        "X-API-Key": this.apiKey,
        ...options.headers
      }
    });
    return response.json();
  }

  health() {
    return fetch(`${this.baseUrl}/health`).then(r => r.json());
  }

  getBotStatus() {
    return this.request("/api/v1/bots/status");
  }

  startBot(botType) {
    return this.request(`/api/v1/bots/start/${botType}`, { method: "POST" });
  }

  simulateSandwich(victimValueMon) {
    return this.request(`/api/v1/simulate/sandwich?victim_value_mon=${victimValueMon}`);
  }

  calculateDistribution(profitMon) {
    return this.request(`/api/v1/revenue/calculate?profit_mon=${profitMon}`);
  }
}

// Usage
const client = new Brick3Client("YOUR_API_KEY");
await client.health();
await client.getBotStatus();
```

### Python Demo Script

```python
import requests

# Configuration
BASE_URL = "https://brick3-api.onrender.com"
API_KEY = "YOUR_API_KEY"
HEADERS = {"X-API-Key": API_KEY}

def demo_brick3_api():
    """Demonstrate Brick3 API capabilities"""
    
    # 1. Health Check
    print("🏥 Health Check:")
    r = requests.get(f"{BASE_URL}/health")
    print(r.json())
    
    # 2. Get Bot Status
    print("\n🤖 Bot Status:")
    r = requests.get(f"{BASE_URL}/api/v1/bots/status", headers=HEADERS)
    print(r.json())
    
    # 3. Simulate Sandwich Attack
    print("\n🥪 Sandwich Simulation (100 MON victim):")
    r = requests.get(
        f"{BASE_URL}/api/v1/simulate/sandwich",
        params={"victim_value_mon": 100},
        headers=HEADERS
    )
    print(r.json())
    
    # 4. Calculate Revenue Distribution
    print("\n💰 Revenue Distribution (100 MON profit):")
    r = requests.get(
        f"{BASE_URL}/api/v1/revenue/calculate",
        params={"profit_mon": 100},
        headers=HEADERS
    )
    print(r.json())
    
    # 5. APY Boost Estimate
    print("\n📈 APY Boost Estimate:")
    r = requests.get(
        f"{BASE_URL}/api/v1/revenue/estimate-apy",
        params={"daily_mev_volume_usd": 5000, "tvl_usd": 1000000},
        headers=HEADERS
    )
    print(r.json())

if __name__ == "__main__":
    demo_brick3_api()
```

---

## 🔐 7-Day Free Trial

### What You Get

| Feature | Free Trial (7 Days) | After Trial |
|---------|---------------------|-------------|
| **Network** | ✅ Monad Mainnet | Monad Mainnet |
| **MEV Bots** | ✅ Full Access | Paid Plans |
| **Simulations** | ✅ Unlimited | Paid Plans |
| **API Calls** | ✅ 1,000/day | Based on Plan |
| **Real MEV Extraction** | ✅ Enabled | Enabled |
| **FastLane Integration** | ✅ Full Atlas Protocol | Full Atlas Protocol |

### Quick Start

```bash
# Base URL
BASE_URL="https://brick3-api.onrender.com"

# Step 1: Verify Mainnet Connection
curl $BASE_URL/health

# Step 2: Check Bot Status
curl -H "X-API-Key: YOUR_API_KEY" \
  $BASE_URL/api/v1/bots/status

# Step 3: Start a Bot
curl -X POST -H "X-API-Key: YOUR_API_KEY" \
  $BASE_URL/api/v1/bots/start/sandwich

# Step 4: Run Simulation
curl -H "X-API-Key: YOUR_API_KEY" \
  "$BASE_URL/api/v1/simulate/sandwich?victim_value_mon=500"
```

**⚠️ Important:** API key connects to **real Monad Mainnet** - all operations are live.

---

## 💳 Pricing & Tiers

### Tier Comparison

| Feature | 🆓 Free Trial | ⚡ Pro | 👑 Enterprise |
|---------|---------------|--------|---------------|
| **Price** | $0/mo | $499/mo | $999/mo |
| **Duration** | 7 days | Monthly | Monthly |
| **API Calls/Day** | 1,000 | 10,000 | Unlimited |
| **Dashboard Access** | Basic | Full | Full |
| **Transaction Monitoring** | ✅ | ✅ | ✅ |
| **MEV Simulator** | Limited | ✅ | ✅ |
| **Sandwich Bot** | ❌ | ✅ | ✅ |
| **Arbitrage Bot** | ❌ | ❌ | ✅ |
| **Liquidation Bot** | ❌ | ❌ | ✅ |
| **Backrun Bot** | ❌ | ❌ | ✅ |
| **Brick3 Turbo™** | ❌ | ✅ | ✅ Priority |
| **Brick3 Flash™** | ❌ | ❌ | ✅ |
| **Brick3 Flow™** | ❌ | ❌ | ✅ |
| **Brick3 Link™** | ❌ | ❌ | ✅ |
| **Revenue Share** | 0% | 70% | 80% |
| **Support** | Community | Email | Priority |

### FastLane Partner Tier (Custom)

```
┌─────────────────────────────────────────────────────────────┐
│                 🤝 FASTLANE PARTNER TIER                    │
├─────────────────────────────────────────────────────────────┤
│  Rate Limit: Unlimited                                      │
│  Access: Full Platform + Priority                           │
│  Revenue Share: Custom Agreement                            │
│  Support: Dedicated Technical Contact                       │
│  Features: All Brick3 Technologies                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌐 WebSocket Streaming

### Real-time Opportunity Stream

```javascript
const ws = new WebSocket('wss://brick3-api.onrender.com/ws/opportunities');

ws.onopen = () => {
  console.log('Connected to Brick3 MEV stream');
  // Authenticate
  ws.send(JSON.stringify({ type: 'auth', api_key: 'YOUR_API_KEY' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'opportunity') {
    console.log('New MEV opportunity:', data.opportunity);
    
    if (data.opportunity.estimated_profit_usd > 100) {
      // High value opportunity - take action
      executeBot(data.opportunity);
    }
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### Flow™ WebSocket

```javascript
// Connect to MEV opportunity stream
const ws = new WebSocket('wss://api.brick3.fun/v1/ws/opportunities');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    api_key: 'YOUR_API_KEY'
  }));
  
  // Subscribe to opportunities
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['sandwich', 'arbitrage', 'liquidation']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'opportunity') {
    console.log('New MEV Opportunity:', data.opportunity);
  }
};
```

---

## ⚙️ Rate Limits & Quotas

| Tier | Requests/min | WebSocket Connections | Bot Executions/day |
|------|--------------|----------------------|-------------------|
| Demo | 10 | 1 | 0 (simulation only) |
| Standard | 100 | 5 | 100 |
| Unlimited | No limit | Unlimited | Unlimited |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1735516800
```

---

## ⚠️ Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please slow down.",
    "retry_after": 60
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_API_KEY` | 401 | Invalid or missing API key |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_PARAMETERS` | 400 | Invalid request parameters |
| `BOT_NOT_FOUND` | 404 | Bot type doesn't exist |
| `INSUFFICIENT_FUNDS` | 402 | Not enough balance for execution |
| `EXECUTION_FAILED` | 500 | Trade execution failed |

---

## 📋 Complete API Reference

### Core Endpoints

| # | Endpoint | Method | Description | Auth |
|---|----------|--------|-------------|------|
| 1 | `/health` | GET | API & Mainnet status | ❌ |
| 2 | `/api/v1/bots/status` | GET | All bot statuses | ✅ |
| 3 | `/api/v1/bots/start/{type}` | POST | Start a bot | ✅ |
| 4 | `/api/v1/bots/stop/{type}` | POST | Stop a bot | ✅ |
| 5 | `/api/v1/bots/stop-all` | POST | Emergency stop all | ✅ |
| 6 | `/api/v1/bots/config/{type}` | POST | Configure bot | ✅ |

### Simulation Endpoints

| # | Endpoint | Method | Description | Auth |
|---|----------|--------|-------------|------|
| 7 | `/api/v1/simulate/sandwich` | GET | Sandwich simulation | ✅ |
| 8 | `/api/v1/simulate/arbitrage` | GET | Arbitrage simulation | ✅ |

### Revenue Endpoints

| # | Endpoint | Method | Description | Auth |
|---|----------|--------|-------------|------|
| 9 | `/api/v1/revenue/summary` | GET | Revenue statistics | ✅ |
| 10 | `/api/v1/revenue/calculate` | GET | Distribution calculator | ✅ |
| 11 | `/api/v1/revenue/estimate-apy` | GET | APY estimation | ✅ |

### FastLane Integration

| # | Endpoint | Method | Description | Auth |
|---|----------|--------|-------------|------|
| 12 | `/api/v1/fastlane/info` | GET | FastLane integration info | ✅ |
| 13 | `/api/v1/fastlane/stats` | GET | Partnership statistics | ✅ |
| 14 | `/api/v1/fastlane/quote` | GET | MEV protection quote | ✅ |
| 15 | `/api/v1/fastlane/simulate` | POST | MEV extraction simulation | ✅ |

### Mainnet Engine

| # | Endpoint | Method | Description | Auth |
|---|----------|--------|-------------|------|
| 16 | `/api/v1/mainnet/status` | GET | Engine status | ✅ |
| 17 | `/api/v1/mainnet/start` | POST | Start engine | ✅ |
| 18 | `/api/v1/mainnet/stop` | POST | Stop engine | ✅ |
| 19 | `/api/v1/mainnet/opportunities` | GET | Live opportunities | ✅ |
| 20 | `/api/v1/mainnet/stats` | GET | Performance stats | ✅ |

---

## 📞 Contact & Support

| Type | Contact |
|------|---------|
| 🤝 **Partnership** | partnership@brick3.fun |
| 🛠️ **Technical Support** | info@brick3.fun |
| 📧 **General Inquiries** | hello@brick3.fun |
| 🐦 **Twitter** | @Brick3MEV |
| 💬 **Discord** | discord.gg/brick3 |

### Dedicated FastLane Support
- **Slack Channel:** #brick3-fastlane-integration
- **Technical Contact:** fastlane-support@brick3.fun
- **Response Time:** <2 hours during business hours

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

# Set environment variables (contact partnership@brick3.fun)

# Run API
python monmev_api.py

# Run Dashboard (separate terminal)
streamlit run monmev_dashboard.py
```

---

## ❓ FAQ

**Q: Is this connecting to real Monad Mainnet?**  
A: Yes! All operations use the live Monad network via `rpc.monad.xyz`.

**Q: Will I see real MEV opportunities?**  
A: Yes, the bots monitor real mempool transactions and identify actual opportunities.

**Q: What happens after 7 days trial?**  
A: Your trial key expires. Upgrade to continue using the service.

**Q: Is there a rate limit?**  
A: Free trial: 1,000 API calls/day. Pro: 10,000/day. Enterprise: Unlimited.

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
- ✅ APY boost calculator
- ✅ WebSocket real-time streaming

### v1.0.0 (December 28, 2025)
- Initial release with basic MEV detection

---

**© 2025 Brick3 MEV Platform. All rights reserved.**

*Built for Monad. Powered by FastLane Atlas.*
