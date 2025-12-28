# 🧱 Brick3 MEV Discovery Dashboard

**Monad Mainnet Real-time MEV Monitoring Platform**

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Kur

```bash
cd MonMev
pip install -r requirements.txt
```

### 2. Environment Variables

```bash
cp .env.example .env
# .env dosyasını düzenle
```

### 3. Uygulamaları Başlat

**Backend API:**
```bash
python api.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Streamlit Dashboard:**
```bash
streamlit run app.py
# Dashboard: http://localhost:8501
```

## 📂 Proje Yapısı

```
MonMev/
├── app.py                    # Streamlit Dashboard (Frontend)
├── api.py                    # FastAPI Backend
├── apriori_integration.py    # aPriori Validator Entegrasyonu
├── requirements.txt          # Python bağımlılıkları
├── .env                      # Environment variables
└── README.md                 # Bu dosya
```

## 🔧 Özellikler

### Dashboard (app.py)
- ✅ Real-time transaction monitoring
- ✅ MEV opportunity detection
- ✅ Sandwich attack potential tespit
- ✅ Large transfer tracking
- ✅ Filtreleme (profit, value, type)
- ✅ Block explorer entegrasyonu

### API (api.py)
- ✅ REST API endpoints
- ✅ WebSocket real-time updates
- ✅ API key authentication
- ✅ Rate limiting (tier-based)
- ✅ Swagger/OpenAPI docs

### aPriori Integration
- ✅ Validator MEV feed
- ✅ APY boost calculation
- ✅ Opportunity submission

## 🔑 API Endpoints

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/` | GET | API info |
| `/api/v1/opportunities` | GET | MEV fırsatları |
| `/api/v1/stats` | GET | Dashboard istatistikleri |
| `/ws/opportunities` | WS | Real-time updates |

### Örnek API Kullanımı

```bash
# Opportunities
curl -H "api-key: demo_key_123" http://localhost:8000/api/v1/opportunities

# Stats
curl -H "api-key: demo_key_123" http://localhost:8000/api/v1/stats
```

## 📊 MEV Türleri

| Tür | Emoji | Açıklama |
|-----|-------|----------|
| Sandwich | 🥪 | Swap arbitraj potansiyeli |
| Large Transfer | 🐋 | Büyük token transferleri |
| Contract | 🔄 | Contract etkileşimleri |
| Transfer | 💸 | Normal transferler |

## ⚙️ Konfigürasyon

### RPC Ayarları
```python
# .env dosyasında
MONAD_RPC=https://testnet-rpc.monad.xyz  # Testnet
# MONAD_RPC=https://rpc.monad.xyz        # Mainnet
```

### API Key Tiers
- **Free**: 10 req/min, max 50 results
- **Pro**: 1000 req/min, max 500 results

## 🛡️ Güvenlik Notları

- Production'da `.env` dosyasını paylaşma
- API key'leri gizli tut
- CORS ayarlarını sınırla
- Rate limiting aktif tut

## 📈 Gelecek Özellikler

- [ ] Transaction execution
- [ ] Multi-chain support
- [ ] Advanced MEV strategies
- [ ] Database persistence
- [ ] Redis caching
- [ ] Telegram/Discord alerts

## 📄 Lisans

MIT License

---

**[brick3.fun](https://www.brick3.fun/)** | Built for Monad
