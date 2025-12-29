# Brick3 MEV Discovery API - FastLane Partnership

## 🔗 Live Endpoints

| Service | URL |
|---------|-----|
| 📊 Dashboard | https://brick3.streamlit.app |
| 📚 API Docs | [Coming Soon - Render Deploy] |
| 🔌 API Base | [Coming Soon - Render Deploy] |

## 🔑 FastLane Partner API Key

```
API Key: bk3_fastlane_partner
Tier: Unlimited
Rate Limit: None
```

## 📋 Available Endpoints

### MEV Opportunities
```bash
# Get MEV opportunities
GET /api/v1/opportunities
GET /api/v1/opportunities?type=sandwich&min_profit=100&limit=50

# Get statistics
GET /api/v1/stats
```

### FastLane Integration
```bash
# FastLane info
GET /api/v1/fastlane/info

# Get MEV protection quote
GET /api/v1/fastlane/quote?swap_value=100&refund_percent=10

# FastLane stats (shMON integration)
GET /api/v1/fastlane/stats

# Simulate MEV extraction
POST /api/v1/fastlane/simulate?swap_amount=500

# Demo endpoint (no auth)
GET /api/v1/fastlane/demo
```

### aPriori Validator Integration
```bash
# aPriori status
GET /api/v1/apriori/status

# Submit opportunity to validator
POST /api/v1/apriori/submit?opportunity_id=opp_xxx
```

### WebSocket (Real-time)
```bash
# Connect to real-time stream
WS /ws/opportunities
```

## 📊 Example Responses

### GET /api/v1/fastlane/stats
```json
{
  "success": true,
  "partnership": "Brick3 x FastLane",
  "stats": {
    "total_mev_opportunities": 45,
    "total_mev_captured_usd": 28500.50,
    "avg_mev_per_block": 12.35,
    "last_24h_volume": 684012.00,
    "current_block": 45051191
  },
  "shmon_integration": {
    "estimated_apy_boost": "+28.5%",
    "revenue_share": {
      "shmon_holders": "70%",
      "brick3": "20%",
      "validators": "10%"
    }
  }
}
```

### GET /api/v1/fastlane/simulate?swap_amount=1000
```json
{
  "success": true,
  "simulation": {
    "swap_amount_mon": 1000,
    "extractable_mev": {
      "sandwich": 3.0,
      "backrun": 2.0,
      "total": 10.0
    },
    "with_protection": {
      "user_savings": 7.0,
      "protocol_share": 2.0,
      "validator_share": 1.0
    },
    "recommendation": "HIGH_VALUE_TARGET"
  }
}
```

## 💰 Revenue Share Model

| Recipient | Share | Description |
|-----------|-------|-------------|
| shMON Holders | 70% | Direct APY boost |
| Brick3 | 20% | API & Infrastructure |
| Validators | 10% | Block production incentive |

## 🔧 Integration Example

```python
import requests

API_URL = "https://[brick3-api-url]"
API_KEY = "bk3_fastlane_partner"

headers = {"X-API-Key": API_KEY}

# Get MEV opportunities
response = requests.get(f"{API_URL}/api/v1/opportunities", headers=headers)
opportunities = response.json()

# Get FastLane quote
response = requests.get(
    f"{API_URL}/api/v1/fastlane/quote",
    params={"swap_value": 500, "refund_percent": 10},
    headers=headers
)
quote = response.json()

# Simulate MEV for a swap
response = requests.post(
    f"{API_URL}/api/v1/fastlane/simulate",
    params={"swap_amount": 1000},
    headers=headers
)
simulation = response.json()
```

## 📞 Contact

- **Brick3 Team**: [Contact Info]
- **Dashboard**: https://brick3.streamlit.app
- **GitHub**: https://github.com/brienteth/monmev-dashboard
