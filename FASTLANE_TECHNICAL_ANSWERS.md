# 🔧 Brick3 Technical Implementation Details

## FastLane Partnership - Technical Answers

Bu döküman FastLane ekibinin sorularına detaylı teknik cevaplar içerir.

---

## 📋 Soru 1: "How do you achieve mempool monitoring on monad?"

### Implementasyon: `mempool_monitor.py`

**Birincil Yöntem: RPC Polling**
```
Method: eth_getFilterChanges with 'pending' filter
Poll Interval: 100ms (10 polls/second)
Fallback: Block-by-block transaction scanning
```

**Teknik Detaylar:**
- Web3.py kullanarak Monad RPC'ye bağlanıyoruz (`https://rpc.monad.xyz`)
- `eth_filter('pending')` ile pending transaction filter oluşturuyoruz
- Her 100ms'de `get_new_entries()` ile yeni transaction hash'lerini alıyoruz
- Her hash için `eth_getTransaction()` ile detayları çekiyoruz

**Swap Detection:**
```python
# Desteklenen swap method signatures
SWAP_SIGNATURES = {
    "0x38ed1739": "swapExactTokensForTokens",      # V2
    "0x7ff36ab5": "swapExactETHForTokens",          # V2
    "0x414bf389": "exactInputSingle",               # V3
    "0xc04b8d59": "exactInput",                     # V3
    # ... ve diğerleri
}
```

**Data Storage:**
- SQLite database (`mempool_data.db`)
- Tüm pending transactions log'lanıyor
- Swap transactions ayrı indeksleniyor
- Sandwichable transactions işaretleniyor

**Limitasyonlar:**
1. Public RPC full mempool expose etmiyor
2. WebSocket henüz aktif değil Monad'da
3. Validator bağlantıları için çalışıyoruz

---

## 📋 Soru 2: "Do you have some example transactions of sandwich?"

### Implementasyon: `sandwich_detector.py`

**⚠️ ÖNEMLİ: Tüm örnekler SİMÜLASYONDUR, gerçek execution değil!**

### Sandwich Detection Algoritması:

```python
# 1. Eligible transaction tespiti
if target_value_usd >= 100 and target_value_usd <= 100000:
    if slippage_percent >= 0.3:
        # Sandwichable!
        
# 2. Optimal frontrun hesaplama
frontrun_percent = min(target_slippage * 0.5, 10%)  # Max %10
frontrun_amount = target_amount * frontrun_percent

# 3. Pool simulation (Constant Product AMM)
# k = x * y (değişmez)
amount_out = (amount_in * reserve_out) / (reserve_in + amount_in)
```

### Simülasyon Çıktısı:

```json
{
  "opportunity_id": "abc123...",
  "target_tx_hash": "0xvictim...",
  "target_value_usd": 5000.00,
  "frontrun_amount": 500.00,
  "expected_profit_usd": 12.50,
  "roi_percent": 2.5,
  "confidence": 0.75,
  "status": "SIMULATED"
}
```

### Neden Execute Etmiyoruz?
1. Resmi FastLane entegrasyonu bekliyoruz
2. Atlas'a solver kaydı yapmadan bundle gönderemiyoruz
3. Önce partnership'i onaylatmak istiyoruz

---

## 📋 Soru 3: "How are your bots using fastlane currently? through atlas?"

### Mevcut Durum: INTEGRATION PENDING

### Implementasyon Dosyaları:
- `solver_manager.py` - Solver wallet yönetimi
- `atlas_bundle_client.py` - Atlas bundle submission

### Hazır Olan Altyapı:

**1. Solver Wallet Management:**
```python
# Solver wallet oluşturma
solver = manager.create_solver_wallet(
    name="Brick3-Sandwich-Bot",
    description="Primary sandwich attack solver"
)

# Çıktı
{
    "address": "0x...",
    "status": "pending_registration",
    "bundles_submitted": 0
}
```

**2. Atlas Bundle Format:**
```python
bundle = MEVBundle(
    id="...",
    transactions=[frontrun_tx, backrun_tx],
    target_block=current_block + 1,
    opportunity_type="sandwich",
    expected_profit_wei=100000000000000000  # 0.1 MON
)
```

**3. Auctioneer Submission (Hazır, Aktif Değil):**
```python
payload = {
    "method": "atlas_submitBundle",
    "params": [{
        "chainId": "0x279f",  # 10143
        "transactions": signed_txs,
        "targetBlock": hex(target_block),
        "solver": solver_address
    }]
}
# POST to https://auctioneer-fra.fastlane-labs.xyz
```

### Ne Bekliyoruz?
1. **FastLane'den solver registration onayı**
2. **Atlas router'a resmi erişim**
3. **Production API key**

---

## 🔗 API Endpoints

Tüm teknik detaylara API üzerinden ulaşılabilir:

| Endpoint | Açıklama |
|----------|----------|
| `/api/v1/mempool/status` | Mempool monitoring durumu |
| `/api/v1/mempool/recent-swaps` | Son swap transactions |
| `/api/v1/mempool/sandwichable` | Sandwichable tx'ler |
| `/api/v1/sandwich/opportunities` | Tespit edilen fırsatlar |
| `/api/v1/sandwich/examples` | Örnek simülasyonlar |
| `/api/v1/solver/addresses` | Solver adresleri |
| `/api/v1/solver/info` | Detaylı solver bilgisi |
| `/api/v1/fastlane/technical-details` | Tüm teknik cevaplar |

---

## 📊 Sistem Özeti

```
┌─────────────────────────────────────────────────────────────┐
│                    BRICK3 MEV PLATFORM                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│   │   MEMPOOL    │───▶│  SANDWICH    │───▶│    ATLAS     │ │
│   │   MONITOR    │    │  DETECTOR    │    │   BUNDLE     │ │
│   └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│   │  SQLite DB   │    │  Simulation  │    │   FastLane   │ │
│   │  (Logging)   │    │   Engine     │    │  Auctioneer  │ │
│   └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                     │       │
│                              ┌──────────────────────┘       │
│                              ▼                              │
│                    ╔════════════════════╗                   │
│                    ║  AWAITING OFFICIAL ║                   │
│                    ║    PARTNERSHIP     ║                   │
│                    ╚════════════════════╝                   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Status: Infrastructure READY | Execution PENDING           │
│  Atlas Router: 0xbB010Cb7e71D44d7323aE1C267B333A48D05907C  │
│  Chain ID: 10143 (Monad)                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 Revenue Model

```
MEV Profit Distribution:
├── 70% → shMON Holders (Staking rewards)
├── 20% → Brick3 (Platform fee)
└── 10% → Validators (Block proposer rewards)
```

---

## 📞 Contact

- **Dashboard:** https://brick3.streamlit.app
- **API:** https://brick3-api.onrender.com
- **Docs:** https://brick3-api.onrender.com/docs
- **GitHub:** https://github.com/brienteth/monmev-dashboard

---

*Bu döküman FastLane partnership görüşmeleri için hazırlanmıştır.*
*Tüm sandwich örnekleri simülasyondur, gerçek MEV extraction FastLane entegrasyonu sonrası başlayacaktır.*
