# 🧱 Brick3 MEV Discovery API - FastLane Integration Guide

> **Version:** 2.0 Production Ready  
> **Last Updated:** December 30, 2025  
> **Base URL:** `https://brick3-api.onrender.com`  
> **Dashboard:** `https://brick3.streamlit.app`

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Bot Control System](#bot-control-system)
5. [Revenue Distribution](#revenue-distribution)
6. [WebSocket Streaming](#websocket-streaming)
7. [Integration Examples](#integration-examples)
8. [SDK & Libraries](#sdk--libraries)
9. [Rate Limits & Quotas](#rate-limits--quotas)
10. [Error Handling](#error-handling)

---

## 🎯 Overview

Brick3 MEV Discovery API provides real-time MEV (Maximal Extractable Value) opportunity detection, automated bot execution, and revenue distribution for the Monad blockchain.

### Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **MEV Detection** | Real-time sandwich, arbitrage, liquidation, backrun detection |
| 🤖 **Bot Automation** | 4 specialized bots with configurable parameters |
| 💰 **Revenue Sharing** | 70/20/10 split (shMON holders/Brick3/Validators) |
| 📊 **Analytics** | Detailed profit/loss tracking and APY calculations |
| 🔄 **WebSocket** | Live opportunity streaming with <100ms latency |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastLane Atlas Protocol                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Brick3 API   │───▶│  MEV Bots    │───▶│  Execution   │   │
│  │              │    │              │    │              │   │
│  │ - Detection  │    │ - Sandwich   │    │ - Trade      │   │
│  │ - Simulation │    │ - Arbitrage  │    │ - Settlement │   │
│  │ - Revenue    │    │ - Liquidate  │    │ - Revenue    │   │
│  └──────────────┘    │ - Backrun    │    └──────────────┘   │
│                      └──────────────┘                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Revenue Distribution (70/20/10)          │   │
│  │  ┌────────┐      ┌────────┐      ┌────────┐          │   │
│  │  │ shMON  │      │ Brick3 │      │Validator│          │   │
│  │  │  70%   │      │  20%   │      │  10%   │          │   │
│  │  └────────┘      └────────┘      └────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication

All API requests require authentication via API key in the header.

### Request Header

```http
X-API-Key: your_api_key_here
```

### API Key Types

| Key Type | Rate Limit | Access Level | Use Case |
|----------|------------|--------------|----------|
| `demo` | 10 req/min | Read-only | Testing & Evaluation |
| `standard` | 100 req/min | Full access | Integration Development |
| `unlimited` | No limit | Full access + Priority | Production |

### Example Request

```bash
curl -X GET "https://brick3-api.onrender.com/api/v1/opportunities" \
  -H "X-API-Key: fastlane_demo_key"
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

#### `GET /api/v1/stats`
Get system statistics.

**Response:**
```json
{
  "success": true,
  "stats": {
    "opportunities_today": 156,
    "total_value_detected_usd": 45678.90,
    "avg_profit_per_opportunity": 89.50,
    "active_bots": 3
  }
}
```

---

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

#### `GET /api/v1/opportunities/stream`
WebSocket endpoint for real-time opportunities.

**Connection:**
```javascript
const ws = new WebSocket('wss://brick3-api.onrender.com/ws/opportunities');
ws.onmessage = (event) => {
  const opportunity = JSON.parse(event.data);
  console.log('New MEV opportunity:', opportunity);
};
```

---

### Bot Control

#### `GET /api/v1/bots/status`
Get status of all MEV bots.

**Response:**
```json
{
  "success": true,
  "bots": {
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
}
```

#### `POST /api/v1/bots/start/{bot_type}`
Start a specific bot.

**Bot Types:** `sandwich`, `arbitrage`, `liquidation`, `backrun`

**Response:**
```json
{
  "success": true,
  "bot_type": "sandwich",
  "status": "running",
  "config": {
    "min_profit_usd": 50.0,
    "max_gas_gwei": 100.0,
    "slippage_percent": 0.5
  }
}
```

#### `POST /api/v1/bots/stop/{bot_type}`
Stop a specific bot.

#### `POST /api/v1/bots/start-all`
Start all enabled bots.

#### `POST /api/v1/bots/stop-all`
Stop all bots.

#### `PUT /api/v1/bots/config/{bot_type}`
Update bot configuration.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `min_profit_usd` | float | Minimum profit to execute |
| `max_gas_gwei` | float | Maximum gas price |
| `slippage_percent` | float | Slippage tolerance |
| `enabled` | bool | Enable/disable bot |

---

### Simulation

#### `POST /api/v1/simulate/sandwich`
Simulate a sandwich attack.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `victim_value_mon` | float | Victim swap value in MON |
| `frontrun_amount_mon` | float | (optional) Frontrun amount |

**Response:**
```json
{
  "success": true,
  "simulation": {
    "gross_profit_mon": 2.5,
    "gas_cost_mon": 0.015,
    "net_profit_mon": 2.485,
    "net_profit_usd": 3.73,
    "confidence": 0.82,
    "execution_path": [
      "1. Frontrun: Buy 50 MON",
      "2. Victim swap: 100 MON",
      "3. Backrun: Sell 50 MON"
    ],
    "warnings": []
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

### Revenue Distribution

#### `GET /api/v1/revenue/summary`
Get revenue distribution summary.

**Response:**
```json
{
  "success": true,
  "revenue": {
    "distribution_model": {
      "shmon_holders": "70%",
      "brick3": "20%",
      "validators": "10%"
    },
    "all_time_stats": {
      "total_revenue_mon": 12500,
      "total_revenue_usd": 18750,
      "shmon_holders_total_mon": 8750,
      "brick3_total_mon": 2500,
      "validators_total_mon": 1250,
      "distribution_count": 156
    }
  }
}
```

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

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `profit_mon` | float | Profit amount in MON |

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

---

### FastLane Atlas Integration

#### `POST /api/v1/fastlane/submit`
Submit transaction through FastLane Atlas for MEV protection.

**Request Body:**
```json
{
  "tx_data": "0x...",
  "user_address": "0x...",
  "deadline": 1735516800,
  "max_slippage_bps": 50
}
```

**Response:**
```json
{
  "success": true,
  "bundle_hash": "0xbundle...",
  "estimated_savings_usd": 12.50,
  "protection_status": "active"
}
```

#### `POST /api/v1/fastlane/simulate`
Simulate MEV extraction on a transaction.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `tx_hash` | string | Transaction hash to analyze |
| `swap_amount` | float | Swap amount in MON |

---

## 💡 Integration Examples

### Python SDK

```python
import requests

class Brick3Client:
    def __init__(self, api_key: str):
        self.base_url = "https://brick3-api.onrender.com"
        self.headers = {"X-API-Key": api_key}
    
    def get_opportunities(self, limit=20, min_profit=0):
        response = requests.get(
            f"{self.base_url}/api/v1/opportunities",
            headers=self.headers,
            params={"limit": limit, "min_profit_usd": min_profit}
        )
        return response.json()
    
    def start_bot(self, bot_type: str):
        response = requests.post(
            f"{self.base_url}/api/v1/bots/start/{bot_type}",
            headers=self.headers
        )
        return response.json()
    
    def get_revenue_summary(self):
        response = requests.get(
            f"{self.base_url}/api/v1/revenue/summary",
            headers=self.headers
        )
        return response.json()

# Usage
client = Brick3Client("your_api_key")
opportunities = client.get_opportunities(limit=10, min_profit=50)
```

### JavaScript/TypeScript SDK

```typescript
class Brick3Client {
  private baseUrl = "https://brick3-api.onrender.com";
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        "X-API-Key": this.apiKey,
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
    return response.json();
  }

  async getOpportunities(limit = 20, minProfit = 0) {
    return this.request(`/api/v1/opportunities?limit=${limit}&min_profit_usd=${minProfit}`);
  }

  async startBot(botType: string) {
    return this.request(`/api/v1/bots/start/${botType}`, { method: "POST" });
  }

  async simulateSandwich(victimValue: number) {
    return this.request(`/api/v1/simulate/sandwich?victim_value_mon=${victimValue}`, { 
      method: "POST" 
    });
  }
}

// Usage
const client = new Brick3Client("your_api_key");
const opportunities = await client.getOpportunities(10, 50);
```

### WebSocket Real-time Streaming

```javascript
const ws = new WebSocket('wss://brick3-api.onrender.com/ws/opportunities');

ws.onopen = () => {
  console.log('Connected to Brick3 MEV stream');
  // Authenticate
  ws.send(JSON.stringify({ type: 'auth', api_key: 'your_api_key' }));
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

## 🔗 Contact & Support

- **Technical Support:** support@brick3.xyz
- **Integration Help:** integration@brick3.xyz
- **API Status:** https://status.brick3.xyz
- **Documentation:** https://docs.brick3.xyz

---

## 📜 Changelog

### v2.0.0 (December 30, 2025)
- ✅ Production-ready MEV bot engine
- ✅ 4 bot types: sandwich, arbitrage, liquidation, backrun
- ✅ Revenue distribution system (70/20/10)
- ✅ Transaction simulation endpoints
- ✅ APY boost calculator
- ✅ WebSocket real-time streaming

### v1.0.0 (December 28, 2025)
- Initial release with basic MEV detection
