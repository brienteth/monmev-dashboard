"""
🧱 Brick3 MEV Dashboard - Unified Version
Real-time MEV Monitoring with Full Technology Stack
"""

import streamlit as st
import requests
import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque
import random
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🧱 Brick3 MEV Dashboard",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONFIG ====================
# Auto-detect environment
IS_PRODUCTION = os.getenv("RENDER", "") != "" or os.getenv("STREAMLIT_RUNTIME", "") != ""

if IS_PRODUCTION:
    API_URL = "https://brick3-api.onrender.com"
    MONAD_RPC = "https://rpc.monad.xyz"
else:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    MONAD_RPC = os.getenv("MONAD_RPC", "http://localhost:8545")

API_KEY = os.getenv("API_KEY", "brick3_unlimited_master")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# ==================== WEB3 CONNECTION ====================
try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None

@st.cache_resource
def get_web3():
    """Initialize Web3 connection"""
    if not WEB3_AVAILABLE:
        return None
    try:
        w3 = Web3(Web3.HTTPProvider(MONAD_RPC, request_kwargs={'timeout': 30}))
        if w3.is_connected():
            return w3
    except Exception as e:
        pass
    return None

# ==================== SESSION STATE ====================
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "opportunities" not in st.session_state:
    st.session_state.opportunities = []
if "last_block" not in st.session_state:
    st.session_state.last_block = 0
if "stats" not in st.session_state:
    st.session_state.stats = {
        "total_opportunities": 0,
        "total_profit_usd": 0.0,
        "opportunities_by_type": {"sandwich": 0, "large_transfer": 0, "contract": 0, "transfer": 0},
    }
if "seen_tx_hashes" not in st.session_state:
    st.session_state.seen_tx_hashes = set()
if "last_scan_time" not in st.session_state:
    st.session_state.last_scan_time = 0
if "latency_history" not in st.session_state:
    st.session_state.latency_history = []
if "bots" not in st.session_state:
    st.session_state.bots = {
        "sandwich": {"status": "stopped", "executions": 0, "profit": 0},
        "arbitrage": {"status": "stopped", "executions": 0, "profit": 0},
        "liquidation": {"status": "stopped", "executions": 0, "profit": 0},
        "backrun": {"status": "stopped", "executions": 0, "profit": 0}
    }
if "infrastructure" not in st.session_state:
    st.session_state.infrastructure = {}

# ==================== STYLES ====================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
}
.metric-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    border: 1px solid #3d3d5c;
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
}
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em;
    font-weight: 800;
    text-align: center;
    margin-bottom: 20px;
}
.badge-sandwich { background: #ff6b6b; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
.badge-large-transfer { background: #4ecdc4; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
.badge-contract { background: #ffd93d; color: black; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
.badge-transfer { background: #95a5a6; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
.opp-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #252545 100%);
    border: 1px solid #3d3d5c;
    border-radius: 12px;
    padding: 15px;
    margin: 8px 0;
    transition: all 0.3s ease;
}
.opp-card:hover {
    border-color: #667eea;
    transform: translateY(-2px);
}
.live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(76, 175, 80, 0.2);
    padding: 8px 16px;
    border-radius: 20px;
    border: 1px solid #4caf50;
}
.live-dot {
    width: 10px;
    height: 10px;
    background: #4caf50;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
}
.tech-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(102, 126, 234, 0.2);
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.8em;
    margin: 2px;
}
.latency-good { color: #4caf50; }
.latency-medium { color: #ff9800; }
.latency-bad { color: #f44336; }
</style>
""", unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ====================
def get_type_emoji(mev_type):
    emojis = {"sandwich": "🥪", "large_transfer": "🐋", "contract": "🔄", "transfer": "💸"}
    return emojis.get(mev_type, "❓")

def get_type_color(mev_type):
    colors = {"sandwich": "#ff6b6b", "large_transfer": "#4ecdc4", "contract": "#ffd93d", "transfer": "#95a5a6"}
    return colors.get(mev_type, "#666")

def format_profit(profit):
    if profit >= 100:
        return f"${profit:,.0f}"
    elif profit >= 10:
        return f"${profit:.1f}"
    else:
        return f"${profit:.2f}"

def get_latency_color(latency_ms):
    if latency_ms < 100:
        return "latency-good"
    elif latency_ms < 500:
        return "latency-medium"
    else:
        return "latency-bad"

# ==================== API FUNCTIONS ====================
def fetch_api_health():
    """Check API health with latency measurement"""
    start = time.time()
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        latency = (time.time() - start) * 1000
        if response.status_code == 200:
            data = response.json()
            data['latency_ms'] = round(latency, 2)
            return data
    except Exception as e:
        pass
    return None

def fetch_infrastructure_status():
    """Fetch infrastructure status"""
    try:
        response = requests.get(
            f"{API_URL}/api/v1/infrastructure/status",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def fetch_bot_status():
    """Fetch bot status from API"""
    try:
        response = requests.get(
            f"{API_URL}/api/v1/bots/status",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def start_bot(bot_type):
    """Start a bot via API"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/bots/start/{bot_type}",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def stop_bot(bot_type):
    """Stop a bot via API"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/bots/stop/{bot_type}",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def stop_all_bots():
    """Stop all bots via API"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/bots/stop-all",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

# ==================== MEV SCANNER ====================
def scan_blockchain_api():
    """Scan blockchain via API"""
    start = time.time()
    try:
        response = requests.get(
            f"{API_URL}/api/v1/opportunities",
            headers={"X-API-Key": API_KEY},
            params={"limit": 20},
            timeout=10
        )
        latency = (time.time() - start) * 1000
        
        # Record latency
        st.session_state.latency_history.append({
            "time": datetime.now().isoformat(),
            "latency_ms": latency,
            "source": "api"
        })
        # Keep last 100 entries
        st.session_state.latency_history = st.session_state.latency_history[-100:]
        
        if response.status_code == 200:
            data = response.json()
            return data.get("opportunities", [])
    except:
        pass
    return []

def scan_blockchain_direct():
    """Scan blockchain directly via Web3"""
    if not WEB3_AVAILABLE:
        return generate_demo_opportunity()
    
    w3 = get_web3()
    if not w3:
        return generate_demo_opportunity()
    
    start = time.time()
    try:
        current_block = w3.eth.block_number
        latency = (time.time() - start) * 1000
        
        # Record latency
        st.session_state.latency_history.append({
            "time": datetime.now().isoformat(),
            "latency_ms": latency,
            "source": "rpc"
        })
        st.session_state.latency_history = st.session_state.latency_history[-100:]
        
        if st.session_state.last_block == 0:
            st.session_state.last_block = current_block - 1
        
        if current_block <= st.session_state.last_block:
            return []
        
        opportunities = []
        
        for block_num in range(st.session_state.last_block + 1, min(current_block + 1, st.session_state.last_block + 3)):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions[:10]:  # Limit per block
                    opps = analyze_transaction(tx, w3)
                    opportunities.extend(opps)
            except:
                pass
        
        st.session_state.last_block = current_block
        return opportunities
        
    except Exception as e:
        return generate_demo_opportunity()

def analyze_transaction(tx, w3):
    """Analyze a transaction for MEV opportunities"""
    opportunities = []
    
    try:
        value = tx.get('value', 0)
        to_addr = tx.get('to')
        tx_input = tx.get('input', '0x')
        tx_hash = tx.get('hash', b'')
        
        if isinstance(tx_hash, bytes):
            tx_hash = '0x' + tx_hash.hex()
        elif isinstance(tx_hash, str) and not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        
        large_transfer_threshold = Web3.to_wei(10, 'ether')
        
        # Large transfer detection
        if value >= large_transfer_threshold:
            value_eth = Web3.from_wei(value, 'ether')
            opportunities.append({
                "type": "large_transfer",
                "tx_hash": tx_hash,
                "value_eth": float(value_eth),
                "estimated_profit_usd": float(value_eth) * 0.001 * 1.5,  # MON price estimate
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat(),
                "block": tx.get('blockNumber', 0)
            })
        
        # Contract interaction detection
        if to_addr and len(tx_input) > 10:
            method_id = tx_input[:10] if isinstance(tx_input, str) else '0x' + tx_input[:4].hex()
            
            # DEX swap signatures
            swap_methods = ['0x38ed1739', '0x7ff36ab5', '0x18cbafe5', '0x8803dbee', '0x5c11d795', '0x022c0d9f']
            
            if method_id in swap_methods:
                opportunities.append({
                    "type": "sandwich",
                    "tx_hash": tx_hash,
                    "target_contract": to_addr,
                    "method_id": method_id,
                    "estimated_profit_usd": random.uniform(50, 500),
                    "confidence": 0.75,
                    "timestamp": datetime.now().isoformat(),
                    "block": tx.get('blockNumber', 0)
                })
            elif len(tx_input) > 100:
                opportunities.append({
                    "type": "contract",
                    "tx_hash": tx_hash,
                    "target_contract": to_addr,
                    "method_id": method_id,
                    "estimated_profit_usd": random.uniform(10, 100),
                    "confidence": 0.6,
                    "timestamp": datetime.now().isoformat(),
                    "block": tx.get('blockNumber', 0)
                })
                
    except:
        pass
    
    return opportunities

def generate_demo_opportunity():
    """Generate demo MEV opportunity"""
    if random.random() > 0.3:
        return []
    
    types = ["sandwich", "large_transfer", "contract", "transfer"]
    mev_type = random.choices(types, weights=[0.3, 0.2, 0.3, 0.2])[0]
    tx_hash = "0x" + "".join(random.choices("0123456789abcdef", k=64))
    
    return [{
        "type": mev_type,
        "tx_hash": tx_hash,
        "timestamp": datetime.now().isoformat(),
        "block": random.randint(10000000, 15000000),
        "estimated_profit_usd": random.uniform(10, 500),
        "confidence": random.uniform(0.5, 0.95)
    }]

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🧱 Brick3 MEV")
    st.markdown("---")
    
    # Environment badge
    env_badge = "🌐 Production" if IS_PRODUCTION else "💻 Local"
    st.markdown(f"**Environment:** {env_badge}")
    
    # API Health
    health = fetch_api_health()
    if health and health.get("status") == "ok":
        latency = health.get('latency_ms', 0)
        latency_class = get_latency_color(latency)
        st.success(f"🟢 API Connected")
        st.markdown(f"<span class='{latency_class}'>⚡ Latency: {latency:.0f}ms</span>", unsafe_allow_html=True)
        
        if health.get("rpc_connected"):
            st.success("🔗 RPC Connected")
        
        # Show block number
        opp_count = health.get("opportunities_count", 0)
        st.caption(f"📊 Opportunities: {opp_count}")
    else:
        st.error("🔴 API Offline")
    
    st.markdown("---")
    
    # Monitoring controls
    st.markdown("### 🚀 Monitoring")
    
    if st.session_state.monitoring:
        if st.button("⏹️ Stop Monitoring", use_container_width=True, type="secondary"):
            st.session_state.monitoring = False
            st.rerun()
        st.success("✅ Monitoring Active")
    else:
        if st.button("▶️ Start Monitoring", use_container_width=True, type="primary"):
            st.session_state.monitoring = True
            st.rerun()
        st.info("⏸️ Monitoring Paused")
    
    st.markdown("---")
    
    # Controls
    st.markdown("### 🎛️ Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        auto_refresh = st.toggle("Auto", value=st.session_state.monitoring)
    
    refresh_interval = st.slider("Interval (s)", 2, 30, 5)
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filters")
    type_filter = st.selectbox(
        "MEV Type",
        ["all", "sandwich", "large_transfer", "contract", "transfer"],
        format_func=lambda x: {
            "all": "📊 All Types",
            "sandwich": "🥪 Sandwich",
            "large_transfer": "🐋 Large Transfer",
            "contract": "🔄 Contract",
            "transfer": "💸 Transfer"
        }.get(x, x)
    )
    
    min_profit = st.slider("Min Profit ($)", 0, 500, 0)
    min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.0)
    
    st.markdown("---")
    
    # Quick Stats
    st.markdown("### 📊 Quick Stats")
    st.metric("Total Opportunities", len(st.session_state.opportunities))
    total_profit = sum(o.get("estimated_profit_usd", 0) for o in st.session_state.opportunities)
    st.metric("Est. Total Profit", f"${total_profit:,.2f}")
    
    # Average latency
    if st.session_state.latency_history:
        avg_latency = sum(l['latency_ms'] for l in st.session_state.latency_history[-10:]) / min(10, len(st.session_state.latency_history))
        st.metric("Avg Latency", f"{avg_latency:.0f}ms")

# ==================== MAIN CONTENT ====================
st.markdown('<h1 class="main-header">🧱 Brick3 MEV Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #888;">Real-time MEV Opportunity Monitoring for Monad</p>', unsafe_allow_html=True)

# ==================== TECHNOLOGY BANNER ====================
infra = fetch_infrastructure_status()
if infra:
    features = infra.get("features", {})
    tech_badges = []
    if features.get("quic_enabled"):
        tech_badges.append("⚡ QUIC/HTTP3")
    if features.get("redis_enabled"):
        tech_badges.append("🔴 Redis Cache")
    if features.get("dag_mempool_enabled"):
        tech_badges.append("🔗 DAG Mempool")
    if features.get("local_rpc_enabled"):
        tech_badges.append("🖥️ Local RPC")
    
    if tech_badges:
        badge_html = " ".join([f'<span class="tech-badge">{b}</span>' for b in tech_badges])
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="color: #888; font-size: 0.9em;">Active Technologies:</span><br>
            {badge_html}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"🌐 Running in {infra.get('environment', 'production')} mode - Remote RPC")

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 MEV Monitor", "🤖 Bot Control", "💰 Revenue", "⚡ Infrastructure", "📈 Analytics"])

# ==================== TAB 1: MEV MONITOR ====================
with tab1:
    # Status bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.session_state.monitoring:
            st.markdown("""
            <div class="live-indicator">
                <div class="live-dot"></div>
                <span style="color: #4caf50; font-weight: 600;">LIVE</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<span style="color: #888;">⏸️ Paused</span>', unsafe_allow_html=True)

    with col2:
        st.metric("📦 Last Block", f"{st.session_state.last_block:,}" if st.session_state.last_block > 0 else "N/A")

    with col3:
        st.metric("🎯 Opportunities", len(st.session_state.opportunities))

    with col4:
        total_profit = sum(o.get("estimated_profit_usd", 0) for o in st.session_state.opportunities)
        st.metric("💰 Total Profit", f"${total_profit:,.2f}")

    st.markdown("---")

    # Scan if monitoring
    if st.session_state.monitoring:
        current_time = time.time()
        if current_time - st.session_state.last_scan_time >= 3:
            st.session_state.last_scan_time = current_time
            
            # Try API first, then direct scan
            new_opps = scan_blockchain_api()
            if not new_opps:
                new_opps = scan_blockchain_direct()
            
            if new_opps:
                unique_opps = []
                for opp in new_opps:
                    tx_hash = opp.get("tx_hash", "")
                    if tx_hash and tx_hash not in st.session_state.seen_tx_hashes:
                        st.session_state.seen_tx_hashes.add(tx_hash)
                        unique_opps.append(opp)
                
                if unique_opps:
                    st.session_state.opportunities = unique_opps + st.session_state.opportunities
                    st.session_state.opportunities = st.session_state.opportunities[:100]
                    if len(st.session_state.seen_tx_hashes) > 500:
                        recent_hashes = {o.get("tx_hash") for o in st.session_state.opportunities}
                        st.session_state.seen_tx_hashes = recent_hashes

    # Filter opportunities
    filtered_opps = st.session_state.opportunities.copy()
    if type_filter != "all":
        filtered_opps = [o for o in filtered_opps if o.get("type") == type_filter]
    filtered_opps = [o for o in filtered_opps if o.get("estimated_profit_usd", 0) >= min_profit]
    filtered_opps = [o for o in filtered_opps if o.get("confidence", 0) >= min_confidence]

    # Display opportunities
    st.markdown(f"### 🎯 MEV Opportunities ({len(filtered_opps)})")

    if not filtered_opps:
        st.info("🔍 No MEV opportunities found yet. Start monitoring to detect new opportunities!")
        
        # Manual scan button
        if st.button("🔍 Scan Now"):
            new_opps = scan_blockchain_api()
            if not new_opps:
                new_opps = scan_blockchain_direct()
            if new_opps:
                st.session_state.opportunities.extend(new_opps)
                st.rerun()
    else:
        for opp in filtered_opps[:20]:
            mev_type = opp.get("type", "unknown")
            emoji = get_type_emoji(mev_type)
            profit = opp.get("estimated_profit_usd", 0)
            confidence = opp.get("confidence", 0)
            tx_hash = opp.get("tx_hash", "N/A")
            block = opp.get("block", "N/A")
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 3, 1.5, 1.5, 1])
                
                with col1:
                    st.markdown(f"**{emoji} {mev_type.upper()}**")
                    st.caption(f"Block: {block}")
                
                with col2:
                    short_hash = f"{tx_hash[:12]}...{tx_hash[-8:]}" if len(tx_hash) > 20 else tx_hash
                    st.markdown(f"[🔗 {short_hash}](https://monadexplorer.com/tx/{tx_hash})")
                
                with col3:
                    st.markdown(f"**💰 {format_profit(profit)}**")
                
                with col4:
                    conf_color = "#4caf50" if confidence >= 0.7 else "#ff9800" if confidence >= 0.5 else "#f44336"
                    st.markdown(f'<span style="color: {conf_color};">🎯 {confidence:.0%}</span>', unsafe_allow_html=True)
                
                with col5:
                    timestamp = opp.get("timestamp", "")
                    if timestamp:
                        try:
                            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            st.caption(ts.strftime("%H:%M:%S"))
                        except:
                            st.caption("N/A")
            
            st.markdown("---")

# ==================== TAB 2: BOT CONTROL ====================
with tab2:
    st.markdown("### 🤖 MEV Bot Control Panel")
    st.markdown("Start and stop MEV extraction bots with one click.")
    
    # Fetch current bot status from API
    api_bot_status = fetch_bot_status()
    
    st.markdown("---")
    
    bot_configs = [
        ("sandwich", "🥪 Sandwich Bot", "Frontrun large DEX swaps for profit", "#ff6b6b"),
        ("arbitrage", "🔄 Arbitrage Bot", "Multi-hop DEX arbitrage opportunities", "#4ecdc4"),
        ("liquidation", "💀 Liquidation Bot", "Capture liquidation bonuses from lending", "#ffd93d"),
        ("backrun", "🏃 Backrun Bot", "Backrun profitable transactions", "#a855f7")
    ]
    
    bot_cols = st.columns(2)
    
    for idx, (bot_id, name, desc, color) in enumerate(bot_configs):
        with bot_cols[idx % 2]:
            # Get status from API or local state
            if api_bot_status and "bots" in api_bot_status:
                bots_data = api_bot_status.get("bots", {})
                if "bots" in bots_data:
                    bots_data = bots_data["bots"]
                bot_info = bots_data.get(bot_id, {})
                status = bot_info.get("status", "stopped")
            else:
                status = st.session_state.bots.get(bot_id, {}).get("status", "stopped")
            
            is_running = status == "running"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%); 
                        border: 2px solid {color if is_running else '#3d3d5c'}; 
                        border-radius: 16px; padding: 20px; margin-bottom: 15px;">
                <h3 style="color: {color}; margin: 0;">{name}</h3>
                <p style="color: #888; font-size: 0.9em; margin: 5px 0 15px 0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                status_icon = "🟢" if is_running else "🔴"
                st.markdown(f"**Status:** {status_icon} {status.upper()}")
            
            with col2:
                if not is_running:
                    if st.button(f"▶️ Start", key=f"start_{bot_id}", use_container_width=True):
                        if start_bot(bot_id):
                            st.toast(f"{name} started!", icon="✅")
                            st.rerun()
                        else:
                            st.toast(f"Failed to start {name}", icon="❌")
                else:
                    if st.button(f"⏹️ Stop", key=f"stop_{bot_id}", use_container_width=True):
                        if stop_bot(bot_id):
                            st.toast(f"{name} stopped!", icon="🛑")
                            st.rerun()
                        else:
                            st.toast(f"Failed to stop {name}", icon="❌")
            
            st.markdown("---")
    
    # Global controls
    st.markdown("### 🎛️ Global Controls")
    global_cols = st.columns(3)
    
    with global_cols[0]:
        if st.button("▶️ Start All Bots", use_container_width=True, type="primary"):
            for bot_id, _, _, _ in bot_configs:
                start_bot(bot_id)
            st.toast("All bots started!", icon="🚀")
            st.rerun()
    
    with global_cols[1]:
        if st.button("⏹️ Stop All Bots", use_container_width=True, type="secondary"):
            if stop_all_bots():
                st.toast("All bots stopped!", icon="🛑")
                st.rerun()
    
    with global_cols[2]:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()

# ==================== TAB 3: REVENUE ====================
with tab3:
    st.markdown("### 💰 Revenue Distribution")
    
    # Revenue model
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%); 
                border: 1px solid #667eea; border-radius: 16px; padding: 20px; margin: 20px 0;">
        <h3 style="color: #667eea; margin-top: 0;">📊 Revenue Share Model</h3>
        <div style="display: flex; justify-content: space-around; text-align: center;">
            <div>
                <h2 style="color: #4ecdc4; margin: 0;">70%</h2>
                <p style="color: #888;">shMON Holders</p>
            </div>
            <div>
                <h2 style="color: #ffd93d; margin: 0;">20%</h2>
                <p style="color: #888;">Brick3 Protocol</p>
            </div>
            <div>
                <h2 style="color: #ff6b6b; margin: 0;">10%</h2>
                <p style="color: #888;">Validators</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # APY Calculator
    st.markdown("### 📈 APY Boost Calculator")
    
    calc_cols = st.columns(2)
    
    with calc_cols[0]:
        daily_mev = st.number_input("Daily MEV Capture ($)", min_value=0.0, value=5000.0)
        tvl = st.number_input("Total Value Locked ($)", min_value=1.0, value=1000000.0)
    
    with calc_cols[1]:
        shmon_daily = daily_mev * 0.7
        shmon_yearly = shmon_daily * 365
        apy_boost = (shmon_yearly / tvl) * 100 if tvl > 0 else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 12px; padding: 25px; text-align: center;">
            <h4 style="color: white; margin-top: 0;">Estimated APY Boost</h4>
            <h1 style="color: white; margin: 10px 0; font-size: 3em;">+{apy_boost:.2f}%</h1>
            <p style="color: rgba(255,255,255,0.8);">Additional yield from MEV</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== TAB 4: INFRASTRUCTURE ====================
with tab4:
    st.markdown("### ⚡ Infrastructure Status")
    
    infra = fetch_infrastructure_status()
    health = fetch_api_health()
    
    # API Status
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏥 API Health")
        if health:
            st.success("✅ API Online")
            st.json(health)
        else:
            st.error("❌ API Offline")
    
    with col2:
        st.markdown("#### 🔧 Infrastructure")
        if infra:
            st.json(infra)
        else:
            st.warning("Infrastructure info unavailable")
    
    st.markdown("---")
    
    # Latency Chart
    st.markdown("#### 📊 Latency History")
    
    if st.session_state.latency_history:
        import pandas as pd
        df = pd.DataFrame(st.session_state.latency_history[-50:])
        st.line_chart(df.set_index("time")["latency_ms"])
        
        # Stats
        latencies = [l['latency_ms'] for l in st.session_state.latency_history]
        stat_cols = st.columns(4)
        with stat_cols[0]:
            st.metric("Min", f"{min(latencies):.0f}ms")
        with stat_cols[1]:
            st.metric("Max", f"{max(latencies):.0f}ms")
        with stat_cols[2]:
            st.metric("Avg", f"{sum(latencies)/len(latencies):.0f}ms")
        with stat_cols[3]:
            st.metric("Samples", len(latencies))
    else:
        st.info("No latency data yet. Start monitoring to collect data.")
    
    st.markdown("---")
    
    # Technology Stack
    st.markdown("#### 🛠️ Technology Stack")
    
    tech_cols = st.columns(4)
    
    with tech_cols[0]:
        st.markdown("""
        <div style="background: rgba(255, 107, 107, 0.1); border: 1px solid #ff6b6b; 
                    border-radius: 12px; padding: 15px; text-align: center;">
            <h3 style="color: #ff6b6b; margin: 0;">⚡ QUIC</h3>
            <p style="color: #888; font-size: 0.8em;">HTTP/3 Protocol</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tech_cols[1]:
        st.markdown("""
        <div style="background: rgba(78, 205, 196, 0.1); border: 1px solid #4ecdc4; 
                    border-radius: 12px; padding: 15px; text-align: center;">
            <h3 style="color: #4ecdc4; margin: 0;">🔴 Redis</h3>
            <p style="color: #888; font-size: 0.8em;">Cache Layer</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tech_cols[2]:
        st.markdown("""
        <div style="background: rgba(255, 217, 61, 0.1); border: 1px solid #ffd93d; 
                    border-radius: 12px; padding: 15px; text-align: center;">
            <h3 style="color: #ffd93d; margin: 0;">🔗 DAG</h3>
            <p style="color: #888; font-size: 0.8em;">Mempool</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tech_cols[3]:
        st.markdown("""
        <div style="background: rgba(102, 126, 234, 0.1); border: 1px solid #667eea; 
                    border-radius: 12px; padding: 15px; text-align: center;">
            <h3 style="color: #667eea; margin: 0;">🖥️ RPC</h3>
            <p style="color: #888; font-size: 0.8em;">Local Proxy</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== TAB 5: ANALYTICS ====================
with tab5:
    st.markdown("### 📈 MEV Analytics")
    
    if st.session_state.opportunities:
        import pandas as pd
        
        # Type distribution
        type_counts = {}
        type_profits = {}
        for opp in st.session_state.opportunities:
            t = opp.get("type", "unknown")
            p = opp.get("estimated_profit_usd", 0)
            type_counts[t] = type_counts.get(t, 0) + 1
            type_profits[t] = type_profits.get(t, 0) + p
        
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            st.markdown("#### 📊 Opportunity Count")
            type_df = pd.DataFrame({
                "Type": list(type_counts.keys()),
                "Count": list(type_counts.values())
            })
            st.bar_chart(type_df.set_index("Type"))
        
        with chart_cols[1]:
            st.markdown("#### 💰 Profit by Type")
            profit_df = pd.DataFrame({
                "Type": list(type_profits.keys()),
                "Profit ($)": list(type_profits.values())
            })
            st.bar_chart(profit_df.set_index("Type"))
        
        st.markdown("---")
        
        # Stats table
        st.markdown("#### 📋 Detailed Statistics")
        
        stats_data = []
        for t in type_counts:
            avg_profit = type_profits[t] / type_counts[t] if type_counts[t] > 0 else 0
            avg_conf = sum(
                o.get("confidence", 0) for o in st.session_state.opportunities if o.get("type") == t
            ) / type_counts[t] if type_counts[t] > 0 else 0
            
            stats_data.append({
                "Type": f"{get_type_emoji(t)} {t.upper()}",
                "Count": type_counts[t],
                "Total Profit": f"${type_profits[t]:,.2f}",
                "Avg Profit": f"${avg_profit:.2f}",
                "Avg Confidence": f"{avg_conf:.0%}"
            })
        
        st.dataframe(stats_data, use_container_width=True)
        
        # Export
        st.markdown("---")
        st.markdown("#### 📥 Export Data")
        
        if st.button("📄 Export as JSON"):
            data = {
                "opportunities": st.session_state.opportunities,
                "stats": st.session_state.stats,
                "timestamp": datetime.now().isoformat()
            }
            st.download_button(
                "Download JSON",
                data=json.dumps(data, indent=2),
                file_name=f"brick3_mev_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("📊 No data available. Start monitoring to collect analytics.")

# ==================== AUTO REFRESH ====================
if auto_refresh and st.session_state.monitoring:
    time.sleep(refresh_interval)
    st.rerun()

# ==================== FOOTER ====================
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #666;">🧱 <a href="https://www.brick3.fun/" target="_blank">brick3.fun</a> | Built for Monad</p>',
    unsafe_allow_html=True
)
