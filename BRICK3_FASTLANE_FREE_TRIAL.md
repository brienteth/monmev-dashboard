# 🚀 Brick3 MEV API - 7-Day Free Trial for FastLane

> **Full Mainnet Access - No Credit Card Required**  
> Test our complete MEV infrastructure on Monad Mainnet for 7 days.

---

## 🎯 What You Get

| Feature | Free Trial (7 Days) | After Trial |
|---------|---------------------|-------------|
| **Network** | ✅ Monad Mainnet | Monad Mainnet |
| **MEV Bots** | ✅ Full Access | Paid Plans |
| **Simulations** | ✅ Unlimited | Paid Plans |
| **API Calls** | ✅ 1,000/day | Based on Plan |
| **Real MEV Extraction** | ✅ Enabled | Enabled |
| **FastLane Integration** | ✅ Full Atlas Protocol | Full Atlas Protocol |

---

## 🔑 Your Free Trial Access

```bash
# Free Trial API Key (Valid for 7 days from first use)
API_KEY="brick3_fastlane_trial_2025"

# Production Mainnet API
BASE_URL="https://brick3-api.onrender.com"

# Live Dashboard
DASHBOARD="https://brick3.streamlit.app"

# Network: Monad Mainnet
RPC="https://rpc.monad.xyz"
```

**⚠️ Important:** This key connects to **real Monad Mainnet** - all operations are live.

---

## ⚡ Quick Start (2 minutes)

### Step 1: Verify Mainnet Connection
```bash
curl https://brick3-api.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "rpc_connected": true,
  "monitoring_active": true,
  "environment": "production",
  "network": "monad_mainnet"
}
```

### Step 2: Check Your Trial Status
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  https://brick3-api.onrender.com/api/v1/account/status
```

---

## 🤖 MEV Bot Operations (Live on Mainnet)

### Check All Bot Status
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  https://brick3-api.onrender.com/api/v1/bots/status
```

### Start Sandwich Bot (Real Mempool Monitoring)
```bash
curl -X POST -H "X-API-Key: brick3_fastlane_trial_2025" \
  https://brick3-api.onrender.com/api/v1/bots/start/sandwich
```
**What it does:** Monitors Monad mempool for large swaps and executes frontrun/backrun strategies.

### Start Arbitrage Bot (Cross-DEX)
```bash
curl -X POST -H "X-API-Key: brick3_fastlane_trial_2025" \
  https://brick3-api.onrender.com/api/v1/bots/start/arbitrage
```
**What it does:** Detects price differences across DEXs and executes multi-hop trades.

### Emergency Stop All
```bash
curl -X POST -H "X-API-Key: brick3_fastlane_trial_2025" \
  https://brick3-api.onrender.com/api/v1/bots/stop-all
```

---

## 🎯 MEV Simulations (Pre-Execution Analysis)

### Simulate Sandwich Attack
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  "https://brick3-api.onrender.com/api/v1/simulate/sandwich?victim_value_mon=100"
```

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

### Simulate Multi-Hop Arbitrage
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  "https://brick3-api.onrender.com/api/v1/simulate/arbitrage?amount_in_mon=50&hops=3"
```

---

## 💰 Revenue Distribution Model

All MEV profits are automatically distributed:

| Recipient | Share | Description |
|-----------|-------|-------------|
| **shMON Holders** | 70% | Stakers earn passive MEV income |
| **Brick3** | 20% | Platform development & operations |
| **Validators** | 10% | Network security incentives |

### Calculate Distribution
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  "https://brick3-api.onrender.com/api/v1/revenue/calculate?profit_mon=100"
```

**Response:**
```json
{
  "distribution": {
    "total_profit_mon": 100.0,
    "breakdown": {
      "shmon_holders": { "percentage": 70, "amount_mon": 70.0, "amount_usd": 105.0 },
      "brick3": { "percentage": 20, "amount_mon": 20.0, "amount_usd": 30.0 },
      "validators": { "percentage": 10, "amount_mon": 10.0, "amount_usd": 15.0 }
    }
  }
}
```

### Estimate APY Boost
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  "https://brick3-api.onrender.com/api/v1/revenue/estimate-apy?daily_mev_volume_usd=5000&tvl_usd=1000000"
```

### Get Revenue Summary
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  https://brick3-api.onrender.com/api/v1/revenue/summary
```

---

## 🔗 FastLane Integration (Atlas Protocol)

### Get Integration Details
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  https://brick3-api.onrender.com/api/v1/fastlane/info
```

**Response:**
```json
{
  "partnership_status": "active",
  "integration_version": "1.0.0",
  "atlas_integration": {
    "enabled": true,
    "contract_address": "0xFastLane...Atlas",
    "supported_operations": ["swap", "liquidation", "arbitrage"]
  },
  "enabled_features": [
    "mev_sharing",
    "priority_ordering", 
    "bundle_submission",
    "flashbots_protect"
  ]
}
```

### Get Partnership Stats
```bash
curl -H "X-API-Key: brick3_fastlane_trial_2025" \
  https://brick3-api.onrender.com/api/v1/fastlane/stats
```

---

## 🐍 Python Integration Example

```python
import requests

# Free Trial Credentials
API_KEY = "brick3_fastlane_trial_2025"
BASE = "https://brick3-api.onrender.com"
HEADERS = {"X-API-Key": API_KEY}

# 1. Verify Mainnet Connection
health = requests.get(f"{BASE}/health").json()
print(f"✅ Connected to: {health.get('environment', 'production')}")

# 2. Start MEV Bot
result = requests.post(f"{BASE}/api/v1/bots/start/sandwich", headers=HEADERS).json()
print(f"🤖 Bot Status: {result['status']}")

# 3. Run Simulation
sim = requests.get(
    f"{BASE}/api/v1/simulate/sandwich?victim_value_mon=500",
    headers=HEADERS
).json()
print(f"💰 Estimated Profit: {sim['simulation']['net_profit_mon']} MON")

# 4. Check Revenue Distribution
rev = requests.get(
    f"{BASE}/api/v1/revenue/calculate?profit_mon=100",
    headers=HEADERS
).json()
print(f"📊 shMON Holders Get: {rev['distribution']['breakdown']['shmon_holders']['amount_mon']} MON")

# 5. Stop Bots
requests.post(f"{BASE}/api/v1/bots/stop-all", headers=HEADERS)
print("⏹️ All bots stopped")
```

---

## 🌐 JavaScript Integration Example

```javascript
const API_KEY = "brick3_fastlane_trial_2025";
const BASE = "https://brick3-api.onrender.com";
const headers = { "X-API-Key": API_KEY };

async function testBrick3() {
  // 1. Health Check
  const health = await fetch(`${BASE}/health`).then(r => r.json());
  console.log("✅ API Status:", health.status);

  // 2. Start Sandwich Bot
  const bot = await fetch(`${BASE}/api/v1/bots/start/sandwich`, {
    method: "POST", headers
  }).then(r => r.json());
  console.log("🤖 Bot:", bot.status);

  // 3. Simulate MEV
  const sim = await fetch(
    `${BASE}/api/v1/simulate/sandwich?victim_value_mon=100`,
    { headers }
  ).then(r => r.json());
  console.log("💰 Profit:", sim.simulation?.net_profit_mon, "MON");

  // 4. FastLane Stats
  const stats = await fetch(`${BASE}/api/v1/fastlane/stats`, { headers })
    .then(r => r.json());
  console.log("📊 FastLane Stats:", stats);
}

testBrick3();
```

---

## 📋 Complete API Reference

| # | Endpoint | Method | Description |
|---|----------|--------|-------------|
| 1 | `/health` | GET | API & Mainnet status |
| 2 | `/api/v1/bots/status` | GET | All bot statuses |
| 3 | `/api/v1/bots/start/sandwich` | POST | Start sandwich bot |
| 4 | `/api/v1/bots/start/arbitrage` | POST | Start arbitrage bot |
| 5 | `/api/v1/bots/stop-all` | POST | Emergency stop all |
| 6 | `/api/v1/simulate/sandwich` | GET | Sandwich simulation |
| 7 | `/api/v1/simulate/arbitrage` | GET | Arbitrage simulation |
| 8 | `/api/v1/revenue/summary` | GET | Revenue statistics |
| 9 | `/api/v1/revenue/calculate` | GET | Distribution calculator |
| 10 | `/api/v1/revenue/estimate-apy` | GET | APY estimation |
| 11 | `/api/v1/fastlane/info` | GET | FastLane integration |
| 12 | `/api/v1/fastlane/stats` | GET | Partnership metrics |

---

## 🖥️ Interactive Dashboard

**URL:** https://brick3.streamlit.app

1. Open dashboard
2. Enter your trial API key: `brick3_fastlane_trial_2025`
3. Full access to all features for 7 days

---

## 📈 After Your Trial

| Plan | Price | API Calls | Features |
|------|-------|-----------|----------|
| **Free** | $0 | 100/day | Basic monitoring |
| **Pro** | $49/mo | 10,000/day | Full bot access |
| **Enterprise** | $199/mo | Unlimited | Priority support + Custom |

**Upgrade:** https://www.brick3.fun/get-api-key

---

## ❓ FAQ

**Q: Is this connecting to real Monad Mainnet?**  
A: Yes! All operations use the live Monad network via `rpc.monad.xyz`.

**Q: Will I see real MEV opportunities?**  
A: Yes, the bots monitor real mempool transactions and identify actual opportunities.

**Q: What happens after 7 days?**  
A: Your trial key expires. Upgrade to continue using the service.

**Q: Is there a rate limit?**  
A: Free trial: 1,000 API calls/day. Sufficient for comprehensive testing.

---

## 📞 Contact

| Purpose | Contact |
|---------|---------|
| **Technical Support** | info@brick3.fun |
| **Partnership** | info@brick3.fun |
| **Dashboard** | https://brick3.streamlit.app |
| **Get Production Key** | https://www.brick3.fun/get-api-key |
| **Website** | https://www.brick3.fun |

---

**🎉 Welcome to Brick3 - Start your 7-day Free Trial now!**
