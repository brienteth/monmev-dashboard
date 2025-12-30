# 🧱 Brick3 x FastLane Partnership Package

> **Prepared for:** FastLane Team  
> **Date:** December 30, 2025  
> **Version:** 2.0 Production  
> **Contact:** partnership@brick3.fun

---

## 📋 Executive Summary

Brick3 is a comprehensive MEV (Maximal Extractable Value) infrastructure platform built specifically for **Monad blockchain**. We provide real-time MEV detection, automated bot execution, and transparent revenue distribution through our partnership with FastLane's Atlas Protocol.

### Key Value Propositions

| 🎯 For FastLane | 💰 Revenue Impact |
|-----------------|-------------------|
| MEV detection infrastructure | 70% revenue to shMON holders |
| Bot execution layer | +12-30% APY boost for stakers |
| Real-time mempool analysis | $50K+ monthly MEV volume potential |
| Seamless Atlas integration | Transparent on-chain distribution |

---

## 🔌 Live Services & Endpoints

### Production URLs

| Service | URL | Status |
|---------|-----|--------|
| 📊 **Dashboard** | https://brick3.streamlit.app | ✅ Live |
| 🔌 **API Base** | https://api.brick3.fun/v1 | ✅ Live |
| 📚 **API Docs** | https://api.brick3.fun/docs | ✅ Live |
| 🌐 **Website** | https://www.brick3.fun | ✅ Live |
| 🔑 **Get API Key** | https://www.brick3.fun/get-api-key | ✅ Live |

### Demo & Testing URLs

| Service | URL | Purpose |
|---------|-----|---------|
| 🧪 **Demo API** | https://brick3-api.onrender.com | Testing |
| 📊 **Demo Dashboard** | https://brick3.streamlit.app | Evaluation |

---

## 🔑 API Key Tiers & Pricing

### Tier Comparison

| Feature | 🆓 Free Trial | ⚡ Pro | 👑 Enterprise |
|---------|---------------|--------|---------------|
| **Price** | $0/mo | $49/mo | $199/mo |
| **Duration** | 7 days | Monthly | Monthly |
| **API Calls/Day** | 100 | 10,000 | Unlimited |
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
│  API Key: fastlane_production_atlas                         │
│  Rate Limit: Unlimited                                      │
│  Access: Full Platform + Priority                           │
│  Revenue Share: Custom Agreement                            │
│  Support: Dedicated Technical Contact                       │
│  Features: All Brick3 Technologies                          │
└─────────────────────────────────────────────────────────────┘
```

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
  -H "X-API-Key: brick3_pro_xxxxx" \
  -d '{"tx": "0x...", "priority": "high"}'
```

### 💾 Brick3 Flash™
**Instant Data Caching**

- Real-time price feeds
- Mempool snapshot caching
- Historical data access
- Response time: <10ms

```bash
# Flash™ price query
curl "https://api.brick3.fun/v1/flash/prices" \
  -H "X-API-Key: brick3_ent_xxxxx"
```

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

```bash
# Link™ private RPC
BRICK3_LINK_RPC="https://link.brick3.fun/v1/rpc?key=brick3_ent_xxxxx"
```

---

## 💰 Revenue Distribution Model

### Standard Distribution (70/20/10)

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

### APY Boost Calculator

| Daily MEV Volume | TVL | shMON Daily | Annual APY Boost |
|------------------|-----|-------------|------------------|
| $5,000 | $1M | $3,500 | +127.75% |
| $10,000 | $5M | $7,000 | +51.10% |
| $25,000 | $10M | $17,500 | +63.88% |
| $50,000 | $20M | $35,000 | +63.88% |
| $100,000 | $50M | $70,000 | +51.10% |

### Enterprise Tier (80/15/5)

For Enterprise customers, enhanced revenue share:
- **80%** to shMON Holders
- **15%** to Brick3
- **5%** to Validators

---

## 🧪 Demo API Access

### Immediate Testing

**Demo API Key:** `brick3_demo_fastlane_2025`

**Demo Endpoints:**
```bash
# Base URL for demo
DEMO_URL="https://brick3-api.onrender.com"
API_KEY="brick3_demo_fastlane_2025"
```

### Quick Test Commands

```bash
# 1. Health Check (No auth required)
curl $DEMO_URL/health

# 2. Get Bot Status
curl -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/bots/status"

# 3. Start Sandwich Bot
curl -X POST -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/bots/start/sandwich"

# 4. Simulate Sandwich Attack
curl -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/simulate/sandwich?victim_value_mon=100"

# 5. Simulate Arbitrage
curl -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/simulate/arbitrage?amount_in_mon=50&hops=3"

# 6. Get Revenue Summary
curl -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/revenue/summary"

# 7. Calculate Distribution
curl -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/revenue/calculate?profit_mon=100"

# 8. Estimate APY Boost
curl -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/revenue/estimate-apy?daily_mev_volume_usd=5000&tvl_usd=1000000"

# 9. FastLane Info
curl -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/fastlane/info"

# 10. FastLane Stats
curl -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/fastlane/stats"

# 11. Stop All Bots
curl -X POST -H "X-API-Key: $API_KEY" \
  "$DEMO_URL/api/v1/bots/stop-all"
```

### Python Demo Script

```python
import requests

# Configuration
DEMO_URL = "https://brick3-api.onrender.com"
API_KEY = "brick3_demo_fastlane_2025"
HEADERS = {"X-API-Key": API_KEY}

def demo_brick3_api():
    """Demonstrate Brick3 API capabilities"""
    
    # 1. Health Check
    print("🏥 Health Check:")
    r = requests.get(f"{DEMO_URL}/health")
    print(r.json())
    
    # 2. Get Bot Status
    print("\n🤖 Bot Status:")
    r = requests.get(f"{DEMO_URL}/api/v1/bots/status", headers=HEADERS)
    print(r.json())
    
    # 3. Simulate Sandwich Attack
    print("\n🥪 Sandwich Simulation (100 MON victim):")
    r = requests.get(
        f"{DEMO_URL}/api/v1/simulate/sandwich",
        params={"victim_value_mon": 100},
        headers=HEADERS
    )
    print(r.json())
    
    # 4. Calculate Revenue Distribution
    print("\n💰 Revenue Distribution (100 MON profit):")
    r = requests.get(
        f"{DEMO_URL}/api/v1/revenue/calculate",
        params={"profit_mon": 100},
        headers=HEADERS
    )
    print(r.json())
    
    # 5. APY Boost Estimate
    print("\n📈 APY Boost Estimate:")
    r = requests.get(
        f"{DEMO_URL}/api/v1/revenue/estimate-apy",
        params={"daily_mev_volume_usd": 5000, "tvl_usd": 1000000},
        headers=HEADERS
    )
    print(r.json())

if __name__ == "__main__":
    demo_brick3_api()
```

### JavaScript Demo

```javascript
const DEMO_URL = "https://brick3-api.onrender.com";
const API_KEY = "brick3_demo_fastlane_2025";

async function demoBrick3API() {
  const headers = { "X-API-Key": API_KEY };
  
  // Health Check
  console.log("🏥 Health Check:");
  let res = await fetch(`${DEMO_URL}/health`);
  console.log(await res.json());
  
  // Bot Status
  console.log("\n🤖 Bot Status:");
  res = await fetch(`${DEMO_URL}/api/v1/bots/status`, { headers });
  console.log(await res.json());
  
  // Sandwich Simulation
  console.log("\n🥪 Sandwich Simulation:");
  res = await fetch(
    `${DEMO_URL}/api/v1/simulate/sandwich?victim_value_mon=100`,
    { headers }
  );
  console.log(await res.json());
  
  // Revenue Distribution
  console.log("\n💰 Revenue Distribution:");
  res = await fetch(
    `${DEMO_URL}/api/v1/revenue/calculate?profit_mon=100`,
    { headers }
  );
  console.log(await res.json());
}

demoBrick3API();
```

---

## 📡 API Reference

### Core Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/health` | GET | API health status | ❌ |
| `/api/v1/bots/status` | GET | All bot statuses | ✅ |
| `/api/v1/bots/start/{type}` | POST | Start a bot | ✅ |
| `/api/v1/bots/stop/{type}` | POST | Stop a bot | ✅ |
| `/api/v1/bots/stop-all` | POST | Stop all bots | ✅ |
| `/api/v1/bots/config/{type}` | POST | Configure bot | ✅ |

### Simulation Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/simulate/sandwich` | GET | Sandwich simulation | ✅ |
| `/api/v1/simulate/arbitrage` | GET | Arbitrage simulation | ✅ |

### Revenue Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/revenue/summary` | GET | Revenue statistics | ✅ |
| `/api/v1/revenue/calculate` | GET | Calculate distribution | ✅ |
| `/api/v1/revenue/estimate-apy` | GET | APY boost estimate | ✅ |

### FastLane Integration

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/v1/fastlane/info` | GET | FastLane integration info | ✅ |
| `/api/v1/fastlane/stats` | GET | Partnership statistics | ✅ |
| `/api/v1/fastlane/quote` | GET | MEV protection quote | ✅ |
| `/api/v1/fastlane/simulate` | POST | MEV extraction simulation | ✅ |

### WebSocket Streaming

```javascript
// Connect to MEV opportunity stream
const ws = new WebSocket('wss://api.brick3.fun/v1/ws/opportunities');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    api_key: 'brick3_pro_xxxxx'
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

## 📊 Example API Responses

### Health Check Response
```json
{
  "status": "ok",
  "timestamp": "2025-12-30T10:00:00.000Z",
  "rpc_connected": true,
  "monitoring_active": true,
  "opportunities_count": 15
}
```

### Bot Status Response
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
        "max_position_size_mon": 1000.0
      }
    },
    "arbitrage": {
      "status": "stopped",
      "config": {
        "min_profit_usd": 20.0,
        "max_gas_gwei": 100.0,
        "slippage_percent": 0.5,
        "max_position_size_mon": 1000.0
      }
    }
  }
}
```

### Sandwich Simulation Response
```json
{
  "success": true,
  "simulation": {
    "gross_profit_mon": 2.5,
    "gas_cost_mon": 0.015,
    "net_profit_mon": 2.485,
    "net_profit_usd": 3.73,
    "confidence": 0.85,
    "price_impact_percent": 0.5,
    "execution_path": [
      "1. Frontrun: Buy 25.00 MON",
      "2. Victim swap: 100.00 MON",
      "3. Backrun: Sell 25.00 MON"
    ],
    "warnings": []
  }
}
```

### Revenue Distribution Response
```json
{
  "success": true,
  "distribution": {
    "total_profit_mon": 100.0,
    "total_profit_usd": 150.0,
    "breakdown": {
      "shmon_holders": {
        "percentage": 70.0,
        "amount_mon": 70.0,
        "amount_usd": 105.0
      },
      "brick3": {
        "percentage": 20.0,
        "amount_mon": 20.0,
        "amount_usd": 30.0
      },
      "validators": {
        "percentage": 10.0,
        "amount_mon": 10.0,
        "amount_usd": 15.0
      }
    }
  }
}
```

### APY Estimate Response
```json
{
  "success": true,
  "estimate": {
    "daily_mev_volume_usd": 5000.0,
    "tvl_usd": 1000000.0,
    "daily_shmon_earnings_usd": 3500.0,
    "yearly_shmon_earnings_usd": 1277500.0,
    "estimated_apy_boost_percent": 127.75,
    "note": "APY boost added to base staking rewards"
  }
}
```

---

## 🛠️ Integration Steps

### Step 1: Get API Key
1. Visit https://www.brick3.fun/get-api-key
2. Create account
3. Start free trial or select a plan
4. Copy your API key

### Step 2: Test with Demo
```bash
# Verify your key works
curl -H "X-API-Key: YOUR_API_KEY" \
  https://api.brick3.fun/v1/bots/status
```

### Step 3: Integrate into Atlas
```python
# Example Atlas integration
from brick3_sdk import Brick3Client

client = Brick3Client(api_key="brick3_pro_xxxxx")

# Monitor for MEV opportunities
opportunities = client.get_opportunities(
    types=['sandwich', 'arbitrage'],
    min_profit_usd=50
)

# Execute via Atlas
for opp in opportunities:
    if opp.confidence > 0.8:
        client.execute(opp, via='atlas')
```

### Step 4: Configure Revenue Distribution
```python
# Set up revenue distribution
client.configure_revenue(
    shmon_holders_percent=70,
    brick3_percent=20,
    validators_percent=10
)
```

---

## 📞 Contact & Support

| Type | Contact |
|------|---------|
| 🤝 **Partnership** | partnership@brick3.fun |
| 🛠️ **Technical Support** | support@brick3.fun |
| 📧 **General Inquiries** | hello@brick3.fun |
| 🐦 **Twitter** | @Brick3MEV |
| 💬 **Discord** | discord.gg/brick3 |

### Dedicated FastLane Support
- **Slack Channel:** #brick3-fastlane-integration
- **Technical Contact:** fastlane-support@brick3.fun
- **Response Time:** <2 hours during business hours

---

## 📎 Additional Resources

- [Full API Documentation](./FASTLANE_API_DOCS.md)
- [Integration Guide](./FASTLANE_INTEGRATION_DOCS.md)
- [Quick Start Guide](./FASTLANE_QUICKSTART.md)
- [SDK Documentation](https://docs.brick3.fun/sdk)
- [Dashboard](https://brick3.streamlit.app)

---

**© 2025 Brick3 MEV Platform. All rights reserved.**

*Built for Monad. Powered by FastLane Atlas.*
