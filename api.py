"""
Brick3 MEV API Backend
FastAPI REST API + WebSocket for real-time MEV opportunities
Version: 0.1
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3
import threading
import time

load_dotenv()

# ==================== APP CONFIG ====================
app = FastAPI(
    title="Brick3 MEV API",
    description="Monad MEV Discovery API - Real-time opportunity monitoring",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da domain'leri sınırla
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== WEB3 CONFIG ====================
RPC_URL = os.getenv("MONAD_RPC", "https://testnet-rpc.monad.xyz")
try:
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 30}))
except:
    w3 = None

CHAIN_ID = 10143

# ==================== DATA STORAGE ====================
# In-memory storage (Production'da Redis/DB kullan)
opportunities_store: List[Dict] = []
stats_store: Dict = {
    "total_opportunities": 0,
    "total_profit_mon": 0.0,
    "sandwich_count": 0,
    "large_transfer_count": 0,
    "last_block": 0,
    "last_update": None
}

# WebSocket bağlantıları
active_connections: List[WebSocket] = []

# ==================== API KEY AUTH ====================
VALID_API_KEYS = {
    "demo_key_123": {"tier": "free", "rate_limit": 10, "max_results": 50},
    "pro_key_xyz": {"tier": "pro", "rate_limit": 1000, "max_results": 500},
    "enterprise_key": {"tier": "enterprise", "rate_limit": 10000, "max_results": 5000}
}

def verify_api_key(api_key: str = Header(None, alias="api-key")):
    """API key doğrulama"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Add 'api-key' header."
        )
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return VALID_API_KEYS[api_key]

# ==================== MODELS ====================
class MEVOpportunity(BaseModel):
    hash: str = Field(..., description="Transaction hash")
    block: int = Field(..., description="Block number")
    timestamp: str = Field(..., description="Detection timestamp")
    value_mon: float = Field(..., description="Transaction value in MON")
    estimated_profit: float = Field(..., description="Estimated profit in MON")
    mev_type: str = Field(..., description="MEV opportunity type")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Receiver address")
    gas_price_gwei: Optional[float] = Field(None, description="Gas price in Gwei")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hash": "0xabc123def456...",
                "block": 1234567,
                "timestamp": "2025-12-28T12:00:00Z",
                "value_mon": 100.5,
                "estimated_profit": 0.5,
                "mev_type": "🥪 Sandwich Potential",
                "from_address": "0x123...",
                "to_address": "0x456...",
                "gas_price_gwei": 25.5
            }
        }

class OpportunitiesResponse(BaseModel):
    success: bool
    count: int
    tier: str
    rate_limit: int
    opportunities: List[MEVOpportunity]

class StatsResponse(BaseModel):
    success: bool
    total_opportunities: int
    total_profit_mon: float
    avg_profit_per_opp: float
    sandwich_count: int
    large_transfer_count: int
    last_block: int
    last_update: Optional[str]
    rpc_connected: bool

class HealthResponse(BaseModel):
    status: str
    rpc_connected: bool
    block_number: Optional[int]
    chain_id: int
    uptime: str

# ==================== HELPER FUNCTIONS ====================

SWAP_SIGNATURES = [
    '0x38ed1739', '0x7ff36ab5', '0x18cbafe5', '0x8803dbee',
    '0xfb3bdb41', '0x4a25d94a', '0x5c11d795', '0xb6f9de95',
    '0x791ac947', '0xc04b8d59', '0xdb3e2198', '0xf28c0498', '0x414bf389'
]

def is_swap_transaction(tx) -> bool:
    """Swap işlemi kontrolü"""
    try:
        input_data = tx.get('input', '0x')
        return any(input_data.startswith(sig) for sig in SWAP_SIGNATURES)
    except:
        return False

def classify_mev_type(tx) -> str:
    """MEV türü sınıflandırma"""
    try:
        input_data = tx.get('input', '0x')
        value_eth = float(w3.from_wei(tx.get('value', 0), 'ether')) if w3 else 0
        
        if is_swap_transaction(tx):
            if value_eth > 10:
                return "🥪 Sandwich Potential"
            return "🔄 Swap"
        if value_eth > 50:
            return "🐋 Large Transfer"
        if len(input_data) > 10:
            return "🔄 Contract Interaction"
        return "💸 Transfer"
    except:
        return "❓ Unknown"

def estimate_profit(tx) -> float:
    """Profit tahmini"""
    try:
        value_eth = float(w3.from_wei(tx.get('value', 0), 'ether')) if w3 else 0
        
        if is_swap_transaction(tx):
            if value_eth > 100:
                return round(value_eth * 0.008, 4)
            elif value_eth > 50:
                return round(value_eth * 0.006, 4)
            elif value_eth > 10:
                return round(value_eth * 0.004, 4)
            elif value_eth > 5:
                return round(value_eth * 0.003, 4)
        
        if value_eth > 100:
            return round(value_eth * 0.001, 4)
        return 0
    except:
        return 0

def process_block_transactions(block_number: int):
    """Blok transaction'larını işle"""
    global opportunities_store, stats_store
    
    try:
        if not w3 or not w3.is_connected():
            return
        
        block = w3.eth.get_block(block_number, full_transactions=True)
        
        for tx in block.transactions:
            try:
                value_eth = float(w3.from_wei(tx.value, 'ether'))
                
                if value_eth < 0.1:
                    continue
                
                profit = estimate_profit(tx)
                if profit <= 0:
                    continue
                
                mev_type = classify_mev_type(tx)
                gas_price = tx.get('gasPrice', tx.get('maxFeePerGas', 0))
                gas_price_gwei = float(w3.from_wei(gas_price, 'gwei'))
                
                opp = {
                    "hash": tx['hash'].hex(),
                    "block": block_number,
                    "timestamp": datetime.now().isoformat(),
                    "value_mon": round(value_eth, 4),
                    "estimated_profit": profit,
                    "mev_type": mev_type,
                    "from_address": tx['from'],
                    "to_address": tx['to'] if tx['to'] else "Contract Creation",
                    "gas_price_gwei": round(gas_price_gwei, 2)
                }
                
                opportunities_store.insert(0, opp)
                
                # Stats güncelle
                stats_store["total_opportunities"] += 1
                stats_store["total_profit_mon"] += profit
                if "Sandwich" in mev_type:
                    stats_store["sandwich_count"] += 1
                if "Large" in mev_type:
                    stats_store["large_transfer_count"] += 1
                
                # Son 1000'i tut
                if len(opportunities_store) > 1000:
                    opportunities_store = opportunities_store[:1000]
                    
            except Exception as e:
                continue
        
        stats_store["last_block"] = block_number
        stats_store["last_update"] = datetime.now().isoformat()
        
    except Exception as e:
        print(f"Block processing error: {e}")

# Background monitoring thread
monitoring_active = False
last_processed_block = 0

def background_monitor():
    """Background blok monitoring"""
    global monitoring_active, last_processed_block
    
    while monitoring_active:
        try:
            if w3 and w3.is_connected():
                current_block = w3.eth.block_number
                
                if current_block > last_processed_block:
                    process_block_transactions(current_block)
                    last_processed_block = current_block
        except Exception as e:
            print(f"Monitor error: {e}")
        
        time.sleep(2)

# ==================== ENDPOINTS ====================

@app.get("/", tags=["Info"])
def root():
    """API bilgileri"""
    return {
        "service": "Brick3 MEV Discovery API",
        "version": "0.1.0",
        "chain": "Monad",
        "chain_id": CHAIN_ID,
        "documentation": "/docs",
        "endpoints": {
            "opportunities": "/api/v1/opportunities",
            "stats": "/api/v1/stats",
            "health": "/api/v1/health",
            "websocket": "/ws/opportunities"
        }
    }

@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Sistem sağlık kontrolü"""
    rpc_connected = w3.is_connected() if w3 else False
    block_number = None
    
    if rpc_connected:
        try:
            block_number = w3.eth.block_number
        except:
            pass
    
    return HealthResponse(
        status="healthy" if rpc_connected else "degraded",
        rpc_connected=rpc_connected,
        block_number=block_number,
        chain_id=CHAIN_ID,
        uptime="running"
    )

@app.get("/api/v1/opportunities", response_model=OpportunitiesResponse, tags=["MEV"])
def get_opportunities(
    min_profit: float = Query(0.01, description="Minimum profit filter (MON)"),
    mev_type: Optional[str] = Query(None, description="Filter by MEV type"),
    limit: int = Query(50, description="Maximum results to return"),
    offset: int = Query(0, description="Pagination offset"),
    user_tier: dict = Depends(verify_api_key)
):
    """
    MEV fırsatlarını getir
    
    - **min_profit**: Minimum kar filtresi (MON cinsinden)
    - **mev_type**: MEV türü filtresi (sandwich, large_transfer, swap, etc.)
    - **limit**: Maksimum sonuç sayısı
    - **offset**: Sayfalama için offset
    """
    max_limit = user_tier["max_results"]
    limit = min(limit, max_limit)
    
    # Filtrele
    filtered = opportunities_store
    
    if min_profit > 0:
        filtered = [o for o in filtered if o["estimated_profit"] >= min_profit]
    
    if mev_type:
        filtered = [o for o in filtered if mev_type.lower() in o["mev_type"].lower()]
    
    # Paginate
    paginated = filtered[offset:offset + limit]
    
    # Response model'e çevir
    opportunities = [
        MEVOpportunity(
            hash=o["hash"],
            block=o["block"],
            timestamp=o["timestamp"],
            value_mon=o["value_mon"],
            estimated_profit=o["estimated_profit"],
            mev_type=o["mev_type"],
            from_address=o["from_address"],
            to_address=o["to_address"],
            gas_price_gwei=o.get("gas_price_gwei")
        )
        for o in paginated
    ]
    
    return OpportunitiesResponse(
        success=True,
        count=len(opportunities),
        tier=user_tier["tier"],
        rate_limit=user_tier["rate_limit"],
        opportunities=opportunities
    )

@app.get("/api/v1/stats", response_model=StatsResponse, tags=["MEV"])
def get_stats(user_tier: dict = Depends(verify_api_key)):
    """Dashboard istatistikleri"""
    avg_profit = 0.0
    if stats_store["total_opportunities"] > 0:
        avg_profit = stats_store["total_profit_mon"] / stats_store["total_opportunities"]
    
    return StatsResponse(
        success=True,
        total_opportunities=stats_store["total_opportunities"],
        total_profit_mon=round(stats_store["total_profit_mon"], 4),
        avg_profit_per_opp=round(avg_profit, 4),
        sandwich_count=stats_store["sandwich_count"],
        large_transfer_count=stats_store["large_transfer_count"],
        last_block=stats_store["last_block"],
        last_update=stats_store["last_update"],
        rpc_connected=w3.is_connected() if w3 else False
    )

@app.get("/api/v1/opportunity/{tx_hash}", tags=["MEV"])
def get_opportunity_by_hash(
    tx_hash: str,
    user_tier: dict = Depends(verify_api_key)
):
    """Belirli bir transaction hash ile fırsat detayı"""
    for opp in opportunities_store:
        if opp["hash"].lower() == tx_hash.lower():
            return {"success": True, "opportunity": opp}
    
    raise HTTPException(status_code=404, detail="Opportunity not found")

@app.post("/api/v1/monitor/start", tags=["Control"])
def start_monitoring(user_tier: dict = Depends(verify_api_key)):
    """Monitoring'i başlat"""
    global monitoring_active
    
    if user_tier["tier"] not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=403,
            detail="Monitoring control requires Pro or Enterprise tier"
        )
    
    if not monitoring_active:
        monitoring_active = True
        thread = threading.Thread(target=background_monitor, daemon=True)
        thread.start()
        return {"success": True, "message": "Monitoring started"}
    
    return {"success": True, "message": "Monitoring already active"}

@app.post("/api/v1/monitor/stop", tags=["Control"])
def stop_monitoring(user_tier: dict = Depends(verify_api_key)):
    """Monitoring'i durdur"""
    global monitoring_active
    
    if user_tier["tier"] not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=403,
            detail="Monitoring control requires Pro or Enterprise tier"
        )
    
    monitoring_active = False
    return {"success": True, "message": "Monitoring stopped"}

# ==================== FASTLANE INTEGRATION ====================

@app.get("/api/v1/fastlane/info", tags=["FastLane"])
def get_fastlane_info():
    """FastLane MEV Protection bilgileri"""
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
def get_mev_protection_quote(
    swap_value: float = Query(..., description="Swap value in MON"),
    refund_percent: int = Query(10, ge=0, le=90, description="Protocol refund percentage"),
    user_tier: dict = Depends(verify_api_key)
):
    """
    MEV koruma tahmini al
    
    Swap işlemi için potansiyel MEV tasarrufunu hesaplar
    """
    is_large_swap = swap_value > 10
    
    # Typical MEV extraction rates
    if is_large_swap:
        estimated_mev_rate = 0.008  # 0.8% for large swaps
    else:
        estimated_mev_rate = 0.003  # 0.3% for normal swaps
    
    total_mev = swap_value * estimated_mev_rate
    user_refund = total_mev * (1 - refund_percent / 100)
    protocol_refund = total_mev * (refund_percent / 100)
    
    return {
        "success": True,
        "swap_value_mon": swap_value,
        "is_large_swap": is_large_swap,
        "estimated_mev_extraction": round(total_mev, 6),
        "user_savings_mon": round(user_refund, 6),
        "protocol_revenue_mon": round(protocol_refund, 6),
        "refund_percent": refund_percent,
        "mev_rate_percent": estimated_mev_rate * 100,
        "recommendation": "Enable FastLane for MEV protection" if total_mev > 0.01 else "MEV protection optional for this swap size"
    }

@app.get("/api/v1/fastlane/shmonad", tags=["FastLane"])
def get_shmonad_info():
    """shMONAD staking bilgileri"""
    return {
        "success": True,
        "name": "shMONAD",
        "description": "Liquid Staking Token for Monad",
        "stake_url": "https://shmonad.xyz/",
        "features": [
            "Staking rewards",
            "MEV yield sharing",
            "Gas payment support",
            "Restaking enabled"
        ],
        "yield_channels": [
            {"name": "Staking", "description": "Base validator rewards"},
            {"name": "MEV", "description": "MEV capture via FastLane"},
            {"name": "Paymaster", "description": "Gas abstraction fees"},
            {"name": "Task Manager", "description": "Automation services"},
            {"name": "FastLane RPC", "description": "Priority transaction fees"}
        ],
        "estimated_apy": {
            "base_staking": 8.0,
            "mev_boost": 0.5,
            "total": 8.5,
            "note": "APY varies based on network activity"
        }
    }

# ==================== WEBSOCKET ====================

@app.websocket("/ws/opportunities")
async def websocket_opportunities(websocket: WebSocket):
    """Real-time MEV opportunity stream"""
    await websocket.accept()
    active_connections.append(websocket)
    
    last_sent_count = 0
    
    try:
        while True:
            # Yeni fırsatlar varsa gönder
            current_count = len(opportunities_store)
            
            if current_count > last_sent_count and opportunities_store:
                # En son fırsatı gönder
                latest = opportunities_store[0]
                await websocket.send_json({
                    "type": "new_opportunity",
                    "data": latest
                })
                last_sent_count = current_count
            
            # Heartbeat
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "total_opportunities": current_count
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
    """Uygulama başlangıcı"""
    global monitoring_active, last_processed_block
    
    print("🧱 Brick3 MEV API starting...")
    
    if w3 and w3.is_connected():
        print(f"✅ Connected to Monad RPC: {RPC_URL}")
        try:
            last_processed_block = w3.eth.block_number
            print(f"📦 Current block: {last_processed_block}")
        except:
            pass
        
        # Auto-start monitoring
        monitoring_active = True
        thread = threading.Thread(target=background_monitor, daemon=True)
        thread.start()
        print("🚀 Background monitoring started")
    else:
        print("⚠️ RPC connection failed - monitoring disabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapanışı"""
    global monitoring_active
    monitoring_active = False
    print("👋 Brick3 MEV API shutting down...")

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"""
    ╔══════════════════════════════════════════╗
    ║     🧱 Brick3 MEV Discovery API          ║
    ║     Version: 0.1.0                       ║
    ║     Host: {host}:{port}                  ║
    ║     Docs: http://localhost:{port}/docs   ║
    ╚══════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
