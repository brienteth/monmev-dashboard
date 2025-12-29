"""
🧱 Brick3 MEV Discovery API
Real-time MEV Monitoring for Monad
Version: 1.0.0

Features:
- Unlimited API access
- Real-time WebSocket streaming
- aPriori validator integration
- FastLane MEV Protection
"""

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import asyncio
import json
import uuid
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3
import threading
import time
import random

load_dotenv()

# ==================== CONFIG ====================
MONAD_RPC = os.getenv("MONAD_RPC", "https://rpc.monad.xyz")  # Monad Mainnet
CHAIN_ID = 143  # Monad Mainnet
REFRESH_INTERVAL = 2  # seconds
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"  # Demo mode for testing
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"  # Toggle API key auth

# Web3 Connection
try:
    w3 = Web3(Web3.HTTPProvider(MONAD_RPC, request_kwargs={'timeout': 30}))
except:
    w3 = None

# ==================== UNLIMITED API KEYS ====================
API_KEYS = {
    "brick3_unlimited_master": {
        "name": "Master Key",
        "tier": "unlimited",
        "rate_limit": None,
        "created": "2025-01-01",
        "expires": None
    },
    "brick3_monmev_prod": {
        "name": "MonMev Production",
        "tier": "unlimited", 
        "rate_limit": None,
        "created": "2025-01-01",
        "expires": None
    },
    "bk3_fastlane_partner": {
        "name": "FastLane Partnership",
        "tier": "unlimited",
        "rate_limit": None,
        "created": "2025-01-01",
        "expires": None
    },
    "bk3_apriori_validator": {
        "name": "aPriori Validator",
        "tier": "unlimited",
        "rate_limit": None,
        "created": "2025-01-01",
        "expires": None
    },
    "bk3_kuru_integration": {
        "name": "Kuru Integration",
        "tier": "unlimited",
        "rate_limit": None,
        "created": "2025-01-01",
        "expires": None
    }
}

# ==================== DATA STORES ====================
opportunities_store: List[Dict] = []
stats_store: Dict = {
    "total_opportunities": 0,
    "total_profit_usd": 0.0,
    "opportunities_by_type": {
        "sandwich": 0,
        "large_transfer": 0,
        "contract": 0,
        "transfer": 0
    },
    "last_block": 0,
    "start_time": datetime.now(),
    "rpc_connected": False
}

# WebSocket connections
active_connections: List[WebSocket] = []

# ==================== APP SETUP ====================
app = FastAPI(
    title="🧱 Brick3 MEV Discovery API",
    description="Real-time MEV Monitoring for Monad - Unlimited Access",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================
class Opportunity(BaseModel):
    id: str
    type: str
    tx_hash: str
    potential_profit_usd: float
    confidence: float
    block: int
    timestamp: str
    details: Dict[str, Any]

class StatsResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]

# ==================== HELPER FUNCTIONS ====================
SWAP_SIGNATURES = [
    '0x38ed1739', '0x7ff36ab5', '0x18cbafe5', '0x8803dbee',
    '0xfb3bdb41', '0x4a25d94a', '0x5c11d795', '0xb6f9de95',
    '0x791ac947', '0xc04b8d59', '0xdb3e2198', '0xf28c0498', '0x414bf389'
]

def generate_opportunity_id():
    """Generate unique opportunity ID"""
    return f"opp_{uuid.uuid4().hex[:12]}"

def generate_api_key(name: str):
    """Generate new API key"""
    hash_input = f"{name}{datetime.now().isoformat()}{random.random()}"
    key_hash = hashlib.md5(hash_input.encode()).hexdigest()
    return f"bk3_{key_hash}"

def is_swap_transaction(tx) -> bool:
    """Check if transaction is a swap"""
    try:
        input_data = tx.get('input', '0x')
        return any(input_data.startswith(sig) for sig in SWAP_SIGNATURES)
    except:
        return False

def classify_mev_type(tx) -> str:
    """Classify MEV opportunity type - Daha akıllı sınıflandırma"""
    try:
        input_data = tx.get('input', '0x')
        value_eth = float(w3.from_wei(tx.get('value', 0), 'ether')) if w3 else 0
        
        # DEX swap işlemleri - en yüksek MEV potansiyeli
        if is_swap_transaction(tx):
            return "sandwich"
        
        # Büyük transferler - frontrun potansiyeli
        if value_eth > 100:
            return "large_transfer"
        
        # Contract etkileşimleri - arbitraj potansiyeli
        if len(input_data) > 100 and value_eth > 50:
            return "contract"
        
        # Basit transferler - düşük MEV potansiyeli
        return "transfer"
    except:
        return "transfer"

def estimate_profit_usd(tx, mev_type: str) -> float:
    """Estimate potential profit in USD - Daha gerçekçi değerler"""
    try:
        value_eth = float(w3.from_wei(tx.get('value', 0), 'ether')) if w3 else 0
        mon_price = 1.5  # Gerçekçi MON fiyatı
        
        if mev_type == "sandwich":
            # Sandwich saldırıları için gerçekçi kar marjları
            if value_eth > 1000:
                return round(value_eth * 0.012 * mon_price, 2)  # %1.2
            elif value_eth > 500:
                return round(value_eth * 0.010 * mon_price, 2)  # %1.0
            elif value_eth > 100:
                return round(value_eth * 0.008 * mon_price, 2)  # %0.8
            elif value_eth > 50:
                return round(value_eth * 0.006 * mon_price, 2)  # %0.6
            return round(value_eth * 0.004 * mon_price, 2)  # %0.4
        
        if mev_type == "large_transfer":
            # Büyük transferler için frontrun potansiyeli
            if value_eth > 500:
                return round(value_eth * 0.003 * mon_price, 2)
            return round(value_eth * 0.002 * mon_price, 2)
        
        # Contract ve transfer - çok düşük kar
        return round(value_eth * 0.001 * mon_price, 2)
    except:
        return 0.0

def process_transaction(tx, block_number: int) -> Optional[Dict]:
    """Process transaction and create opportunity"""
    try:
        value_eth = float(w3.from_wei(tx.value, 'ether'))
        
        # Mainnet için gerçekçi ama esnek filtreler
        if value_eth < 5.0:  # Minimum 5 MON
            return None
        
        mev_type = classify_mev_type(tx)
        
        # Tür bazlı filtreler
        if mev_type == "sandwich" and value_eth < 10:
            return None
        if mev_type == "large_transfer" and value_eth < 50:
            return None
        if mev_type in ["contract", "transfer"] and value_eth < 20:
            return None
        
        profit_usd = estimate_profit_usd(tx, mev_type)
        
        if profit_usd < 0.1:  # Minimum $0.10 profit
            return None
        
        # Calculate confidence based on value and type
        confidence = min(0.95, 0.6 + (value_eth / 500) + (0.15 if mev_type == "sandwich" else 0))
        
        tx_hash = tx['hash'].hex()
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash

        return {
            "id": generate_opportunity_id(),
            "type": mev_type,
            "tx_hash": tx_hash,
            "potential_profit_usd": profit_usd,
            "confidence": round(confidence, 2),
            "block": block_number,
            "timestamp": datetime.now().isoformat(),
            "details": {
                "value_mon": round(value_eth, 4),
                "from": tx['from'],
                "to": tx['to'] if tx['to'] else "Contract Creation",
                "swap_type": "DEX Swap" if is_swap_transaction(tx) else "Transfer",
                "frontrun_potential": mev_type == "sandwich" and value_eth > 10
            }
        }
    except:
        return None

def generate_demo_opportunity(block_number: int) -> Dict:
    """Generate realistic demo MEV opportunity"""
    mev_types = ["sandwich", "large_transfer", "contract", "transfer"]
    weights = [40, 30, 20, 10]  # Sandwich attacks most common
    mev_type = random.choices(mev_types, weights=weights)[0]
    
    # Realistic values based on type
    if mev_type == "sandwich":
        value_mon = random.uniform(20, 500)
        profit_usd = round(value_mon * random.uniform(0.004, 0.012) * 1.5, 2)
        confidence = random.uniform(0.75, 0.95)
    elif mev_type == "large_transfer":
        value_mon = random.uniform(100, 2000)
        profit_usd = round(value_mon * random.uniform(0.002, 0.004) * 1.5, 2)
        confidence = random.uniform(0.65, 0.85)
    elif mev_type == "contract":
        value_mon = random.uniform(50, 300)
        profit_usd = round(value_mon * random.uniform(0.001, 0.003) * 1.5, 2)
        confidence = random.uniform(0.60, 0.80)
    else:  # transfer
        value_mon = random.uniform(10, 100)
        profit_usd = round(value_mon * random.uniform(0.001, 0.002) * 1.5, 2)
        confidence = random.uniform(0.55, 0.75)
    
    # Generate realistic addresses
    from_addr = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
    to_addr = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
    tx_hash = '0x' + ''.join(random.choices('0123456789abcdef', k=64))
    
    return {
        "id": generate_opportunity_id(),
        "type": mev_type,
        "tx_hash": tx_hash,
        "potential_profit_usd": profit_usd,
        "confidence": round(confidence, 2),
        "block": block_number,
        "timestamp": datetime.now().isoformat(),
        "details": {
            "value_mon": round(value_mon, 4),
            "from": from_addr,
            "to": to_addr,
            "swap_type": "DEX Swap" if mev_type == "sandwich" else "Transfer",
            "frontrun_potential": mev_type == "sandwich" and value_mon > 50
        }
    }

# ==================== BACKGROUND MONITORING ====================
monitoring_active = False
last_processed_block = 0

def background_monitor():
    """Background blockchain monitoring with demo mode"""
    global monitoring_active, last_processed_block, stats_store, opportunities_store
    
    while monitoring_active:
        try:
            if DEMO_MODE:
                # Demo mode - generate realistic fake data
                stats_store["rpc_connected"] = True
                last_processed_block += 1
                current_block = last_processed_block
                
                # Generate 1-3 opportunities per block (realistic MEV rate)
                num_opps = random.choices([0, 1, 2, 3], weights=[60, 25, 10, 5])[0]
                
                for _ in range(num_opps):
                    opp = generate_demo_opportunity(current_block)
                    opportunities_store.insert(0, opp)
                    stats_store["total_opportunities"] += 1
                    stats_store["total_profit_usd"] += opp["potential_profit_usd"]
                    stats_store["opportunities_by_type"][opp["type"]] += 1
                    
                    # Keep last 500 opportunities
                    if len(opportunities_store) > 500:
                        opportunities_store = opportunities_store[:500]
                
                stats_store["last_block"] = current_block
                
            elif w3 and w3.is_connected():
                # Real blockchain monitoring
                stats_store["rpc_connected"] = True
                current_block = w3.eth.block_number
                
                if current_block > last_processed_block:
                    try:
                        block = w3.eth.get_block(current_block, full_transactions=True)
                        
                        for tx in block.transactions:
                            opp = process_transaction(tx, current_block)
                            
                            if opp:
                                opportunities_store.insert(0, opp)
                                stats_store["total_opportunities"] += 1
                                stats_store["total_profit_usd"] += opp["potential_profit_usd"]
                                stats_store["opportunities_by_type"][opp["type"]] += 1
                                
                                # Keep last 500 opportunities
                                if len(opportunities_store) > 500:
                                    opportunities_store = opportunities_store[:500]
                        
                        stats_store["last_block"] = current_block
                        last_processed_block = current_block
                        
                    except Exception as e:
                        pass
            else:
                stats_store["rpc_connected"] = False
                
        except Exception as e:
            pass
        
        time.sleep(REFRESH_INTERVAL)

# ==================== API KEY VALIDATION ====================

async def validate_api_key(x_api_key: str = Header(None)):
    """Validate API key from header"""
    # Public mode: skip authentication entirely
    if not AUTH_ENABLED:
        return x_api_key or "public-access"
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key header."
        )
    
    if x_api_key not in API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Please use a valid key."
        )
    
    return x_api_key
    
    return x_api_key

# ==================== API ENDPOINTS ====================

@app.get("/", tags=["Info"])
def root():
    """API Information"""
    return {
        "service": "🧱 Brick3 MEV Discovery API",
        "version": "1.0.0",
        "chain": "Monad",
        "chain_id": CHAIN_ID,
        "status": "✅ UNLIMITED ACCESS - NO RATE LIMITS",
        "documentation": "/docs",
        "endpoints": {
            "opportunities": "/api/v1/opportunities",
            "stats": "/api/v1/stats",
            "health": "/health",
            "keys_generate": "/api/v1/keys/generate",
            "keys_list": "/api/v1/keys/list",
            "apriori_status": "/api/v1/apriori/status",
            "apriori_submit": "/api/v1/apriori/submit",
            "websocket": "/ws/opportunities"
        }
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "rpc_connected": w3.is_connected() if w3 else False,
        "monitoring_active": monitoring_active,
        "opportunities_count": len(opportunities_store)
    }

@app.get("/api/v1/opportunities", tags=["MEV"])
def get_opportunities(
    type: Optional[str] = Query(None, description="Filter by MEV type: sandwich, large_transfer, contract, transfer"),
    min_profit: Optional[float] = Query(None, description="Minimum profit in USD"),
    limit: int = Query(50, ge=1, le=500, description="Number of results"),
    api_key: str = Depends(validate_api_key)
):
    """
    Get MEV opportunities
    
    - **type**: Filter by opportunity type
    - **min_profit**: Minimum profit threshold in USD
    - **limit**: Maximum results to return
    """
    filtered = opportunities_store.copy()
    
    if type:
        filtered = [o for o in filtered if o["type"] == type]
    
    if min_profit:
        filtered = [o for o in filtered if o["potential_profit_usd"] >= min_profit]
    
    return {
        "success": True,
        "count": len(filtered[:limit]),
        "opportunities": filtered[:limit]
    }

@app.get("/api/v1/stats", tags=["MEV"])
def get_stats(api_key: str = Depends(validate_api_key)):
    """Get MEV monitoring statistics"""
    uptime = datetime.now() - stats_store["start_time"]
    uptime_hours = round(uptime.total_seconds() / 3600, 2)
    
    avg_profit = (
        stats_store["total_profit_usd"] / stats_store["total_opportunities"]
        if stats_store["total_opportunities"] > 0 else 0
    )
    
    return {
        "success": True,
        "stats": {
            "total_opportunities": stats_store["total_opportunities"],
            "total_profit_usd": round(stats_store["total_profit_usd"], 2),
            "avg_profit_usd": round(avg_profit, 2),
            "opportunities_by_type": stats_store["opportunities_by_type"],
            "last_block": stats_store["last_block"],
            "uptime_hours": uptime_hours,
            "rpc_connected": stats_store["rpc_connected"]
        }
    }

# ==================== API KEY MANAGEMENT ====================

@app.get("/api/v1/keys/generate", tags=["Keys"])
def generate_key(name: str = Query(..., description="Name for the new API key")):
    """Generate new unlimited API key"""
    new_key = generate_api_key(name)
    
    API_KEYS[new_key] = {
        "name": name,
        "tier": "unlimited",
        "rate_limit": None,
        "created": datetime.now().isoformat(),
        "expires": None
    }
    
    return {
        "success": True,
        "api_key": new_key,
        "tier": "unlimited",
        "rate_limit": "unlimited",
        "expires_at": "never"
    }

@app.get("/api/v1/keys/list", tags=["Keys"])
def list_keys():
    """List all API keys"""
    keys_list = []
    for key, info in API_KEYS.items():
        keys_list.append({
            "key": key[:20] + "..." if len(key) > 20 else key,
            "name": info["name"],
            "tier": info["tier"],
            "created": info["created"]
        })
    
    return {
        "success": True,
        "count": len(keys_list),
        "keys": keys_list
    }

# ==================== APRIORI INTEGRATION ====================

apriori_submissions: List[Dict] = []

@app.get("/api/v1/apriori/status", tags=["aPriori"])
def apriori_status(api_key: str = Depends(validate_api_key)):
    """aPriori integration status"""
    return {
        "success": True,
        "integration": "aPriori Validator",
        "status": "active",
        "validator_address": os.getenv("APRIORI_VALIDATOR_ADDRESS", "0x..."),
        "relay_url": os.getenv("APRIORI_RELAY_URL", "https://relay.apriori.xyz"),
        "total_submissions": len(apriori_submissions),
        "successful_submissions": len([s for s in apriori_submissions if s.get("success")]),
        "features": [
            "MEV yield boost for stakers",
            "Validator backrun opportunities",
            "APY enhancement via MEV capture"
        ]
    }

@app.post("/api/v1/apriori/submit", tags=["aPriori"])
def apriori_submit(opportunity_id: str = Query(..., description="Opportunity ID to submit"), api_key: str = Depends(validate_api_key)):
    """Submit opportunity to aPriori relay"""
    # Find opportunity
    opp = None
    for o in opportunities_store:
        if o["id"] == opportunity_id:
            opp = o
            break
    
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    submission = {
        "id": f"sub_{uuid.uuid4().hex[:8]}",
        "opportunity_id": opportunity_id,
        "submitted_at": datetime.now().isoformat(),
        "success": True,  # Simulated
        "validator": os.getenv("APRIORI_VALIDATOR_ADDRESS", "0x..."),
        "estimated_boost": f"+{round(opp['potential_profit_usd'] * 0.001, 4)}% APY"
    }
    
    apriori_submissions.append(submission)
    
    return {
        "success": True,
        "submission": submission,
        "message": "Opportunity submitted to aPriori relay"
    }

# ==================== FASTLANE INTEGRATION ====================

@app.get("/api/v1/fastlane/info", tags=["FastLane"])
def fastlane_info(api_key: str = Depends(validate_api_key)):
    """FastLane MEV Protection info"""
    return {
        "success": True,
        "name": "FastLane MEV Protection",
        "protocol": "Atlas",
        "contracts": {
            "atlas_router": "0xbB010Cb7e71D44d7323aE1C267B333A48D05907C",
            "chain_id": "0x279f"
        },
        "features": [
            "Smart contract-based MEV protection",
            "Better pricing via output token bidding",
            "Revenue generation for dApps (0-90% refund)",
            "Multi-chain support"
        ],
        "endpoints": {
            "auctioneer": "https://auctioneer-fra.fastlane-labs.xyz",
            "docs": "https://dev.shmonad.xyz/products/mev-protection",
            "stake": "https://shmonad.xyz/"
        }
    }

@app.get("/api/v1/fastlane/quote", tags=["FastLane"])
def fastlane_quote(
    swap_value: float = Query(..., description="Swap value in MON"),
    refund_percent: int = Query(10, ge=0, le=90, description="Protocol refund percentage"),
    api_key: str = Depends(validate_api_key)
):
    """Get MEV protection quote"""
    is_large_swap = swap_value > 10
    mev_rate = 0.008 if is_large_swap else 0.003
    
    total_mev = swap_value * mev_rate
    user_savings = total_mev * (1 - refund_percent / 100)
    protocol_revenue = total_mev * (refund_percent / 100)
    
    return {
        "success": True,
        "swap_value_mon": swap_value,
        "is_large_swap": is_large_swap,
        "estimated_mev_extraction": round(total_mev, 6),
        "user_savings_mon": round(user_savings, 6),
        "protocol_revenue_mon": round(protocol_revenue, 6),
        "refund_percent": refund_percent,
        "mev_rate_percent": mev_rate * 100,
        "recommendation": "Enable FastLane for MEV protection" if total_mev > 0.01 else "MEV protection optional"
    }

@app.get("/api/v1/fastlane/stats", tags=["FastLane"])
def fastlane_stats(api_key: str = Depends(validate_api_key)):
    """FastLane MEV statistics for shMON integration"""
    # Calculate stats from opportunities
    sandwich_opps = [o for o in opportunities_store if o["type"] == "sandwich"]
    total_mev_captured = sum(o["potential_profit_usd"] for o in sandwich_opps)
    
    return {
        "success": True,
        "partnership": "Brick3 x FastLane",
        "stats": {
            "total_mev_opportunities": len(sandwich_opps),
            "total_mev_captured_usd": round(total_mev_captured, 2),
            "avg_mev_per_block": round(total_mev_captured / max(1, stats_store["total_opportunities"]) * 10, 2),
            "last_24h_volume": round(total_mev_captured * 24, 2),
            "current_block": stats_store["last_block"]
        },
        "shmon_integration": {
            "estimated_apy_boost": f"+{round(total_mev_captured * 0.001, 2)}%",
            "revenue_share": {
                "shmon_holders": "70%",
                "brick3": "20%",
                "validators": "10%"
            }
        },
        "endpoints_available": [
            "/api/v1/fastlane/info",
            "/api/v1/fastlane/quote",
            "/api/v1/fastlane/stats",
            "/api/v1/fastlane/simulate",
            "/api/v1/opportunities"
        ]
    }

@app.post("/api/v1/fastlane/simulate", tags=["FastLane"])
def fastlane_simulate(
    tx_hash: str = Query(None, description="Transaction hash to simulate"),
    swap_amount: float = Query(100, description="Swap amount in MON"),
    api_key: str = Depends(validate_api_key)
):
    """Simulate MEV extraction for a swap transaction"""
    # Simulated MEV extraction analysis
    base_mev = swap_amount * 0.005  # 0.5% base MEV
    sandwich_profit = swap_amount * 0.003  # 0.3% sandwich
    backrun_profit = swap_amount * 0.002  # 0.2% backrun
    
    total_extractable = base_mev + sandwich_profit + backrun_profit
    
    return {
        "success": True,
        "simulation": {
            "tx_hash": tx_hash or f"0x{uuid.uuid4().hex}",
            "swap_amount_mon": swap_amount,
            "extractable_mev": {
                "sandwich": round(sandwich_profit, 4),
                "backrun": round(backrun_profit, 4),
                "total": round(total_extractable, 4)
            },
            "with_protection": {
                "user_savings": round(total_extractable * 0.7, 4),
                "protocol_share": round(total_extractable * 0.2, 4),
                "validator_share": round(total_extractable * 0.1, 4)
            },
            "recommendation": "HIGH_VALUE_TARGET" if swap_amount > 500 else "STANDARD"
        },
        "atlas_contract": "0xbB010Cb7e71D44d7323aE1C267B333A48D05907C"
    }

# ==================== BOT ENGINE ENDPOINTS ====================

# Import bot systems
try:
    from mev_bot_engine import get_bot_engine, BotType
    from transaction_simulator import get_simulator
    from revenue_distribution import get_revenue_system
    BOT_SYSTEMS_AVAILABLE = True
except ImportError:
    BOT_SYSTEMS_AVAILABLE = False

@app.get("/api/v1/bots/status", tags=["Bots"])
def get_bots_status(api_key: str = Depends(validate_api_key)):
    """Get status of all MEV bots"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Bot systems not available"}
    
    engine = get_bot_engine()
    return {
        "success": True,
        "bots": engine.get_bot_status()
    }

@app.post("/api/v1/bots/start/{bot_type}", tags=["Bots"])
def start_bot(bot_type: str, api_key: str = Depends(validate_api_key)):
    """Start a specific bot (sandwich, arbitrage, liquidation, backrun)"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Bot systems not available"}
    
    try:
        engine = get_bot_engine()
        bt = BotType(bot_type)
        result = engine.start_bot(bt)
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid bot type: {bot_type}")

@app.post("/api/v1/bots/stop/{bot_type}", tags=["Bots"])
def stop_bot(bot_type: str, api_key: str = Depends(validate_api_key)):
    """Stop a specific bot"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Bot systems not available"}
    
    try:
        engine = get_bot_engine()
        bt = BotType(bot_type)
        result = engine.stop_bot(bt)
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid bot type: {bot_type}")

@app.post("/api/v1/bots/start-all", tags=["Bots"])
def start_all_bots(api_key: str = Depends(validate_api_key)):
    """Start all enabled bots"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Bot systems not available"}
    
    engine = get_bot_engine()
    return engine.start_all_bots()

@app.post("/api/v1/bots/stop-all", tags=["Bots"])
def stop_all_bots(api_key: str = Depends(validate_api_key)):
    """Stop all bots"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Bot systems not available"}
    
    engine = get_bot_engine()
    return engine.stop_all_bots()

@app.get("/api/v1/bots/executions", tags=["Bots"])
def get_bot_executions(
    limit: int = Query(50, ge=1, le=500),
    api_key: str = Depends(validate_api_key)
):
    """Get bot execution history"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Bot systems not available"}
    
    engine = get_bot_engine()
    return {
        "success": True,
        "executions": engine.get_executions(limit)
    }

@app.put("/api/v1/bots/config/{bot_type}", tags=["Bots"])
def update_bot_config(
    bot_type: str,
    min_profit_usd: float = Query(None),
    max_gas_gwei: float = Query(None),
    slippage_percent: float = Query(None),
    enabled: bool = Query(None),
    api_key: str = Depends(validate_api_key)
):
    """Update bot configuration"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Bot systems not available"}
    
    try:
        engine = get_bot_engine()
        bt = BotType(bot_type)
        
        updates = {}
        if min_profit_usd is not None:
            updates["min_profit_usd"] = min_profit_usd
        if max_gas_gwei is not None:
            updates["max_gas_gwei"] = max_gas_gwei
        if slippage_percent is not None:
            updates["slippage_percent"] = slippage_percent
        if enabled is not None:
            updates["enabled"] = enabled
        
        return engine.update_bot_config(bt, **updates)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid bot type: {bot_type}")

# ==================== SIMULATION ENDPOINTS ====================

@app.post("/api/v1/simulate/sandwich", tags=["Simulation"])
def simulate_sandwich(
    victim_value_mon: float = Query(..., description="Victim swap value in MON"),
    frontrun_amount_mon: float = Query(None, description="Frontrun amount (optional, auto-calculated if not provided)"),
    api_key: str = Depends(validate_api_key)
):
    """Simulate a sandwich attack"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Simulation not available"}
    
    sim = get_simulator()
    
    # Auto-calculate optimal frontrun if not provided
    if frontrun_amount_mon is None:
        optimal = sim.calculate_optimal_frontrun_amount(victim_value_mon, victim_value_mon)
        frontrun_amount_mon = optimal["optimal_amount_mon"]
    
    result = sim.simulate_sandwich(
        victim_tx={"value": int(victim_value_mon * 1e18), "gasPrice": 50 * 10**9},
        frontrun_amount_mon=frontrun_amount_mon
    )
    
    return {
        "success": result.success,
        "simulation": {
            "gross_profit_mon": result.gross_profit_mon,
            "gas_cost_mon": result.gas_cost_mon,
            "net_profit_mon": result.net_profit_mon,
            "net_profit_usd": result.net_profit_usd,
            "confidence": result.confidence,
            "price_impact_percent": result.price_impact_percent,
            "execution_path": result.execution_path,
            "warnings": result.warnings,
            "details": result.details
        }
    }

@app.post("/api/v1/simulate/arbitrage", tags=["Simulation"])
def simulate_arbitrage(
    amount_in_mon: float = Query(..., description="Starting amount in MON"),
    hops: int = Query(3, ge=2, le=5, description="Number of hops"),
    api_key: str = Depends(validate_api_key)
):
    """Simulate an arbitrage trade"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Simulation not available"}
    
    sim = get_simulator()
    
    # Generate token path
    token_path = [f"0xToken{i}" for i in range(hops + 1)]
    
    result = sim.simulate_arbitrage(token_path, amount_in_mon)
    
    return {
        "success": result.success,
        "simulation": {
            "gross_profit_mon": result.gross_profit_mon,
            "gas_cost_mon": result.gas_cost_mon,
            "net_profit_mon": result.net_profit_mon,
            "net_profit_usd": result.net_profit_usd,
            "confidence": result.confidence,
            "execution_path": result.execution_path,
            "warnings": result.warnings,
            "details": result.details
        }
    }

# ==================== REVENUE ENDPOINTS ====================

@app.get("/api/v1/revenue/summary", tags=["Revenue"])
def get_revenue_summary(api_key: str = Depends(validate_api_key)):
    """Get revenue distribution summary"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Revenue system not available"}
    
    system = get_revenue_system()
    return {
        "success": True,
        "revenue": system.get_summary()
    }

@app.get("/api/v1/revenue/stats", tags=["Revenue"])
def get_revenue_stats(
    period: str = Query("all_time", description="Period: hourly, daily, weekly, monthly, all_time"),
    api_key: str = Depends(validate_api_key)
):
    """Get revenue statistics for a period"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Revenue system not available"}
    
    system = get_revenue_system()
    from dataclasses import asdict
    stats = system.get_stats(period)
    
    return {
        "success": True,
        "stats": asdict(stats)
    }

@app.get("/api/v1/revenue/pending", tags=["Revenue"])
def get_pending_revenue(api_key: str = Depends(validate_api_key)):
    """Get pending (accumulated but not distributed) revenue"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Revenue system not available"}
    
    system = get_revenue_system()
    return {
        "success": True,
        "pending": system.get_pending_amount()
    }

@app.get("/api/v1/revenue/distribution-history", tags=["Revenue"])
def get_distribution_history(
    limit: int = Query(50, ge=1, le=500),
    api_key: str = Depends(validate_api_key)
):
    """Get revenue distribution history"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Revenue system not available"}
    
    system = get_revenue_system()
    return {
        "success": True,
        "distributions": system.get_distribution_history(limit)
    }

@app.get("/api/v1/revenue/estimate-apy", tags=["Revenue"])
def estimate_apy_boost(
    daily_mev_volume_usd: float = Query(10000, description="Daily MEV capture volume in USD"),
    tvl_usd: float = Query(10000000, description="Total Value Locked in shMON"),
    api_key: str = Depends(validate_api_key)
):
    """Estimate APY boost from MEV earnings"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Revenue system not available"}
    
    system = get_revenue_system()
    estimate = system.estimate_apy_boost(daily_mev_volume_usd, tvl_usd)
    
    return {
        "success": True,
        "estimate": estimate
    }

@app.post("/api/v1/revenue/calculate", tags=["Revenue"])
def calculate_distribution(
    profit_mon: float = Query(..., description="Profit amount in MON"),
    api_key: str = Depends(validate_api_key)
):
    """Calculate revenue distribution for a given profit"""
    if not BOT_SYSTEMS_AVAILABLE:
        return {"success": False, "error": "Revenue system not available"}
    
    system = get_revenue_system()
    distribution = system.calculate_distribution(profit_mon)
    
    return {
        "success": True,
        "distribution": distribution
    }

@app.get("/api/v1/fastlane/demo", tags=["FastLane"])
def fastlane_demo():
    """FastLane demo endpoint - No API key required for testing"""
    return {
        "success": True,
        "message": "Welcome to Brick3 MEV API Demo",
        "partnership": "Brick3 x FastLane x shMON",
        "demo_data": {
            "sample_opportunities": opportunities_store[:5] if opportunities_store else [],
            "current_stats": {
                "total_opportunities": stats_store["total_opportunities"],
                "total_profit_usd": round(stats_store["total_profit_usd"], 2),
                "last_block": stats_store["last_block"]
            }
        },
        "api_access": {
            "demo_key": "bk3_fastlane_partner",
            "docs": "/docs",
            "dashboard": "https://brick3.streamlit.app"
        },
        "revenue_model": {
            "shmon_holders": "70% of MEV earnings",
            "brick3": "20% of MEV earnings",
            "validators": "10% of MEV earnings"
        }
    }

# ==================== WEBSOCKET ====================

@app.websocket("/ws/opportunities")
async def websocket_opportunities(websocket: WebSocket, api_key: str = Depends(validate_api_key)):
    """Real-time MEV opportunities stream"""
    await websocket.accept()
    active_connections.append(websocket)
    
    last_count = 0
    
    try:
        while True:
            # Check for new opportunities
            current_count = len(opportunities_store)
            
            if current_count > last_count and opportunities_store:
                # Send latest opportunities
                await websocket.send_json({
                    "type": "opportunities",
                    "count": min(10, current_count - last_count),
                    "data": opportunities_store[:10],
                    "timestamp": datetime.now().isoformat()
                })
                last_count = current_count
            
            # Handle incoming messages (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                pass
            
            # Send heartbeat every 5 seconds
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    "total": stats_store["total_opportunities"],
                    "last_block": stats_store["last_block"]
                }
            })
            
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        if websocket in active_connections:
            active_connections.remove(websocket)

# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    global monitoring_active, last_processed_block

    # Reset stores on each startup to avoid stale demo data
    opportunities_store.clear()
    stats_store.update({
        "total_opportunities": 0,
        "total_profit_usd": 0.0,
        "opportunities_by_type": {
            "sandwich": 0,
            "large_transfer": 0,
            "contract": 0,
            "transfer": 0
        },
        "last_block": 0,
        "start_time": datetime.now(),
        "rpc_connected": False
    })
    last_processed_block = 0
    
    mode_indicator = "🎮 DEMO MODE" if DEMO_MODE else "🔴 LIVE MODE"
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           🧱 BRICK3 MEV DISCOVERY API                     ║
║                                                           ║
║   API:    http://localhost:8000                          ║
║   Docs:   http://localhost:8000/docs                     ║
║   WS:     ws://localhost:8000/ws/opportunities           ║
║                                                           ║
║   ✅ UNLIMITED ACCESS - NO RATE LIMITS                   ║
║   {mode_indicator}                                        ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    if DEMO_MODE:
        print("🎮 Demo mode enabled - generating realistic MEV opportunities")
        last_processed_block = 2540000
        stats_store["last_block"] = last_processed_block
        stats_store["rpc_connected"] = True
    elif w3 and w3.is_connected():
        print(f"✅ Connected to Monad RPC: {MONAD_RPC}")
        try:
            last_processed_block = w3.eth.block_number
            stats_store["last_block"] = last_processed_block
            stats_store["rpc_connected"] = True
            print(f"📦 Current block: {last_processed_block}")
        except:
            pass
    else:
        print("⚠️ RPC connection failed - monitoring disabled")
        return
    
    # Start background monitoring
    monitoring_active = True
    thread = threading.Thread(target=background_monitor, daemon=True)
    thread.start()
    print("🚀 Background monitoring started")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    global monitoring_active
    monitoring_active = False
    print("👋 Brick3 MEV API shutting down...")

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
