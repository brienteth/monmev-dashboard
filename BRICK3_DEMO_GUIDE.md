# 🧪 Brick3 API - Demo Guide for FastLane

> **Ready to test in 2 minutes!**  
> No signup required. Just copy & paste.

---

## 🔑 Demo Credentials

```bash
# Demo API Key (ready to use)
API_KEY="brick3_demo_fastlane_2025"

# Demo Base URL
BASE_URL="https://brick3-api.onrender.com"

# Live Dashboard
DASHBOARD="https://brick3.streamlit.app"
```

---

## ⚡ Quick Test (30 seconds)

### 1. Health Check
```bash
curl https://brick3-api.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "rpc_connected": true,
  "monitoring_active": true
}
```

---

## 🤖 Bot Operations

### 2. Check Bot Status
```bash
curl -H "X-API-Key: brick3_demo_fastlane_2025" \
  https://brick3-api.onrender.com/api/v1/bots/status
```

### 3. Start Sandwich Bot
```bash
curl -X POST -H "X-API-Key: brick3_demo_fastlane_2025" \
  https://brick3-api.onrender.com/api/v1/bots/start/sandwich
```

### 4. Start Arbitrage Bot
```bash
curl -X POST -H "X-API-Key: brick3_demo_fastlane_2025" \
  https://brick3-api.onrender.com/api/v1/bots/start/arbitrage
```

### 5. Stop All Bots
```bash
curl -X POST -H "X-API-Key: brick3_demo_fastlane_2025" \
  https://brick3-api.onrender.com/api/v1/bots/stop-all
```

---

## 🥪 MEV Simulations

### 6. Simulate Sandwich Attack
```bash
# Simulate sandwich on 100 MON swap
curl -H "X-API-Key: brick3_demo_fastlane_2025" \
  "https://brick3-api.onrender.com/api/v1/simulate/sandwich?victim_value_mon=100"
```

**Expected Response:**
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

### 7. Simulate Arbitrage (Multi-hop)
```bash
# Simulate 3-hop arbitrage with 50 MON
curl -H "X-API-Key: brick3_demo_fastlane_2025" \
  "https://brick3-api.onrender.com/api/v1/simulate/arbitrage?amount_in_mon=50&hops=3"
```

---

## 💰 Revenue Distribution

### 8. Get Revenue Summary
```bash
curl -H "X-API-Key: brick3_demo_fastlane_2025" \
  https://brick3-api.onrender.com/api/v1/revenue/summary
```

### 9. Calculate Profit Distribution
```bash
# Calculate how 100 MON profit is distributed
curl -H "X-API-Key: brick3_demo_fastlane_2025" \
  "https://brick3-api.onrender.com/api/v1/revenue/calculate?profit_mon=100"
```

**Expected Response:**
```json
{
  "distribution": {
    "total_profit_mon": 100.0,
    "breakdown": {
      "shmon_holders": { "percentage": 70, "amount_mon": 70.0 },
      "brick3": { "percentage": 20, "amount_mon": 20.0 },
      "validators": { "percentage": 10, "amount_mon": 10.0 }
    }
  }
}
```

### 10. Estimate APY Boost
```bash
# Estimate APY with $5000 daily MEV and $1M TVL
curl -H "X-API-Key: brick3_demo_fastlane_2025" \
  "https://brick3-api.onrender.com/api/v1/revenue/estimate-apy?daily_mev_volume_usd=5000&tvl_usd=1000000"
```

**Expected Response:**
```json
{
  "estimate": {
    "daily_mev_volume_usd": 5000.0,
    "tvl_usd": 1000000.0,
    "daily_shmon_earnings_usd": 3500.0,
    "estimated_apy_boost_percent": 127.75
  }
}
```

---

## 🔗 FastLane Integration Endpoints

### 11. FastLane Info
```bash
curl -H "X-API-Key: brick3_demo_fastlane_2025" \
  https://brick3-api.onrender.com/api/v1/fastlane/info
```

### 12. FastLane Stats
```bash
curl -H "X-API-Key: brick3_demo_fastlane_2025" \
  https://brick3-api.onrender.com/api/v1/fastlane/stats
```

---

## 🐍 Python Demo Script

```python
import requests

API_KEY = "brick3_demo_fastlane_2025"
BASE = "https://brick3-api.onrender.com"
HEADERS = {"X-API-Key": API_KEY}

# 1. Health
print("🏥 Health:", requests.get(f"{BASE}/health").json())

# 2. Bot Status
print("🤖 Bots:", requests.get(f"{BASE}/api/v1/bots/status", headers=HEADERS).json())

# 3. Start Sandwich Bot
print("🥪 Start:", requests.post(f"{BASE}/api/v1/bots/start/sandwich", headers=HEADERS).json())

# 4. Simulate Sandwich
print("🎯 Simulate:", requests.get(f"{BASE}/api/v1/simulate/sandwich?victim_value_mon=100", headers=HEADERS).json())

# 5. Revenue Distribution
print("💰 Revenue:", requests.get(f"{BASE}/api/v1/revenue/calculate?profit_mon=100", headers=HEADERS).json())

# 6. APY Estimate
print("📈 APY:", requests.get(f"{BASE}/api/v1/revenue/estimate-apy?daily_mev_volume_usd=5000&tvl_usd=1000000", headers=HEADERS).json())

# 7. Stop All
print("⏹️ Stop:", requests.post(f"{BASE}/api/v1/bots/stop-all", headers=HEADERS).json())
```

---

## 🌐 JavaScript Demo

```javascript
const API_KEY = "brick3_demo_fastlane_2025";
const BASE = "https://brick3-api.onrender.com";

async function demo() {
  const headers = { "X-API-Key": API_KEY };
  
  // Health
  console.log("🏥", await (await fetch(`${BASE}/health`)).json());
  
  // Bot Status
  console.log("🤖", await (await fetch(`${BASE}/api/v1/bots/status`, { headers })).json());
  
  // Start Bot
  console.log("🥪", await (await fetch(`${BASE}/api/v1/bots/start/sandwich`, { method: "POST", headers })).json());
  
  // Simulate
  console.log("🎯", await (await fetch(`${BASE}/api/v1/simulate/sandwich?victim_value_mon=100`, { headers })).json());
  
  // Revenue
  console.log("💰", await (await fetch(`${BASE}/api/v1/revenue/calculate?profit_mon=100`, { headers })).json());
}

demo();
```

---

## 📋 All Demo Endpoints Summary

| # | Endpoint | Method | Description |
|---|----------|--------|-------------|
| 1 | `/health` | GET | API status |
| 2 | `/api/v1/bots/status` | GET | All bot statuses |
| 3 | `/api/v1/bots/start/sandwich` | POST | Start sandwich bot |
| 4 | `/api/v1/bots/start/arbitrage` | POST | Start arbitrage bot |
| 5 | `/api/v1/bots/stop-all` | POST | Stop all bots |
| 6 | `/api/v1/simulate/sandwich?victim_value_mon=X` | GET | Sandwich simulation |
| 7 | `/api/v1/simulate/arbitrage?amount_in_mon=X&hops=Y` | GET | Arbitrage simulation |
| 8 | `/api/v1/revenue/summary` | GET | Revenue stats |
| 9 | `/api/v1/revenue/calculate?profit_mon=X` | GET | Distribution calc |
| 10 | `/api/v1/revenue/estimate-apy?daily_mev_volume_usd=X&tvl_usd=Y` | GET | APY estimation |
| 11 | `/api/v1/fastlane/info` | GET | FastLane integration info |
| 12 | `/api/v1/fastlane/stats` | GET | Partnership stats |

---

## 🖥️ Interactive Dashboard

Visit **https://brick3.streamlit.app** to:

1. Click **🔑 API Keys** in sidebar
2. Click **⚡ Use Pro Demo** button
3. Explore all features with full access

---

## ❓ Quick FAQ

**Q: Is this real MEV execution?**  
A: Demo mode simulates MEV calculations. Production keys enable real execution via Atlas.

**Q: What's the rate limit?**  
A: Demo key: 100 req/min. Production: unlimited.

**Q: How does revenue sharing work?**  
A: 70% shMON holders, 20% Brick3, 10% Validators

---

## 📞 Contact

- **Technical:** support@brick3.fun
- **Partnership:** partnership@brick3.fun
- **Dashboard:** https://brick3.streamlit.app
- **Get Production Key:** https://www.brick3.fun/get-api-key

---

**Happy Testing! 🧪**
