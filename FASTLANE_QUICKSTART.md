# 🧱 Brick3 MEV API - FastLane Partnership Package

## Quick Start for FastLane Team

### Demo API Access (Immediate)

**Base URL:** `https://brick3-api.onrender.com`

**Demo API Key:** `fastlane_demo_2025`

**Dashboard:** `https://brick3.streamlit.app`

---

### Test the API in 30 Seconds

```bash
# 1. Health Check
curl https://brick3-api.onrender.com/health

# 2. Get MEV Opportunities
curl -H "X-API-Key: fastlane_demo_2025" \
  https://brick3-api.onrender.com/api/v1/opportunities?limit=5

# 3. Check Bot Status
curl -H "X-API-Key: fastlane_demo_2025" \
  https://brick3-api.onrender.com/api/v1/bots/status

# 4. Simulate Sandwich Attack
curl -X POST -H "X-API-Key: fastlane_demo_2025" \
  "https://brick3-api.onrender.com/api/v1/simulate/sandwich?victim_value_mon=100"

# 5. Revenue Distribution Calculator
curl -X POST -H "X-API-Key: fastlane_demo_2025" \
  "https://brick3-api.onrender.com/api/v1/revenue/calculate?profit_mon=100"

# 6. FastLane Integration Info
curl -H "X-API-Key: fastlane_demo_2025" \
  https://brick3-api.onrender.com/api/v1/fastlane/info
```

---

### What's Included

#### ✅ Demo Version (fastlane_demo_2025)
- Real-time MEV opportunity detection
- 4 bot types: Sandwich, Arbitrage, Liquidation, Backrun
- Transaction simulation
- Revenue distribution calculator
- APY boost estimator
- WebSocket streaming
- 100 requests/minute

#### ✅ Production Version (fastlane_production_atlas)
- Everything in Demo +
- Real trade execution through Atlas
- Unlimited API access
- Priority WebSocket connections
- Custom bot configurations
- Dedicated support

---

### Revenue Model

| Recipient | Share | Purpose |
|-----------|-------|---------|
| **shMON Holders** | 70% | Staker rewards boost |
| **Brick3** | 20% | Protocol development |
| **Validators** | 10% | Priority fees |

**APY Boost Example:**
- Daily MEV: $5,000
- TVL: $10M
- shMON Earnings: $3,500/day (70%)
- **Annual APY Boost: +12.78%**

---

### API Documentation

📖 **Full Docs:** [FASTLANE_INTEGRATION_DOCS.md](./FASTLANE_INTEGRATION_DOCS.md)

📊 **Interactive Docs:** https://brick3-api.onrender.com/docs

🖥️ **Dashboard:** https://brick3.streamlit.app

---

### Contact

**Technical Integration:** support@brick3.xyz

**Partnership:** partnership@brick3.xyz

---

### Next Steps

1. ✅ Test demo API with `fastlane_demo_2025` key
2. 📝 Review full documentation
3. 🤝 Schedule technical call for production setup
4. 🚀 Get production API key `fastlane_production_atlas`
5. 🔧 Configure Atlas integration
6. 💰 Start earning MEV revenue

---

*Brick3 x FastLane x shMON - Better MEV for Monad*
