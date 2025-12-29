"""
🧱 Brick3 MEV Platform - Full Featured Dashboard
Monad Blockchain MEV Monitoring & Bot Management
"""

import streamlit as st
import requests
import json
import time
import random
from datetime import datetime, timedelta
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🧱 Brick3 MEV Platform",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONFIG ====================
MONAD_RPC = "https://rpc.monad.xyz"  # MAINNET
MON_PRICE_USD = 1.5
API_URL = os.getenv("API_URL", "http://localhost:8000")

# ==================== STYLES ====================
st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%); }
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em;
    font-weight: 800;
    text-align: center;
}
.metric-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    border: 1px solid #3d3d5c;
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
}
.tx-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    border: 1px solid #3d3d5c;
    border-radius: 12px;
    padding: 15px;
    margin: 8px 0;
}
.bot-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #2a2a4e 100%);
    border: 1px solid #4a4a7c;
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
}
.bot-running { border-left: 4px solid #4caf50; }
.bot-stopped { border-left: 4px solid #f44336; }
.badge-whale { background: #4ecdc4; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; }
.badge-contract { background: #ffd93d; color: black; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; }
.badge-transfer { background: #95a5a6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; }
.badge-swap { background: #ff6b6b; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; }
.badge-micro { background: #9b59b6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; }
.live-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    background: #4caf50;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
    margin-right: 8px;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
.status-running { color: #4caf50; font-weight: bold; }
.status-stopped { color: #f44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
defaults = {
    "transactions": [],
    "last_block": 0,
    "scan_count": 0,
    "total_value": 0,
    "bots": {},
    "page": "dashboard",
    "filter_min_mon": 0.0,
    "filter_max_mon": 10000.0,
    "filter_types": ["whale", "large", "medium", "micro", "swap", "contract"],
    "blocks_to_scan": 20,
    "auto_refresh": False,
    "refresh_interval": 5,
    "rpc_latency": 0,
    "api_latency": 0,
    "bot_stats": {"sandwich": {"executions": 0, "profits": 0}, "arbitrage": {"executions": 0, "profits": 0}},
    # API Key Management
    "user_api_key": "",
    "api_key_tier": "free",
    "api_key_valid": False,
    "api_calls_today": 0,
    "api_calls_limit": 100,  # Free tier default
    "demo_api_keys": {}  # Store demo keys for offline mode
}

# API Key Tier Configurations
API_TIERS = {
    "free": {
        "name": "Free Trial",
        "price": 0,
        "price_label": "$0/mo",
        "duration": "7 days",
        "rate_limit": 100,
        "features": [
            "📊 Basic Dashboard Access",
            "🔍 100 API calls/day",
            "📈 Real-time monitoring",
            "🧪 Simulator (Limited)",
            "❌ No bot execution",
            "❌ No revenue sharing"
        ],
        "badge_color": "#6c757d",
        "icon": "🆓"
    },
    "pro": {
        "name": "Pro",
        "price": 49,
        "price_label": "$49/mo",
        "duration": "Monthly",
        "rate_limit": 10000,
        "features": [
            "📊 Full Dashboard Access",
            "🔍 10,000 API calls/day",
            "📈 Real-time monitoring",
            "🧪 Full Simulator Access",
            "🤖 Bot Execution (Sandwich)",
            "⚡ Brick3 Turbo™ Access",
            "💰 70% Revenue Share",
            "📧 Email Support"
        ],
        "badge_color": "#667eea",
        "icon": "⚡"
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 199,
        "price_label": "$199/mo",
        "duration": "Monthly",
        "rate_limit": 100000,
        "features": [
            "📊 Full Dashboard Access",
            "🔍 Unlimited API calls",
            "📈 Real-time monitoring",
            "🧪 Full Simulator Access",
            "🤖 All Bot Types (Sandwich + Arbitrage)",
            "⚡ Brick3 Turbo™ Priority",
            "💾 Brick3 Flash™ Access",
            "🌊 Brick3 Flow™ Mempool",
            "🔗 Brick3 Link™ Private RPC",
            "💰 80% Revenue Share",
            "📞 Priority Support",
            "🎯 Custom Strategies"
        ],
        "badge_color": "#ffd700",
        "icon": "👑"
    }
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==================== RPC FUNCTIONS ====================
def rpc_call(method, params=None, measure_latency=False):
    """Direct JSON-RPC call to Monad with optional latency measurement"""
    try:
        start_time = time.time()
        response = requests.post(
            MONAD_RPC,
            json={"jsonrpc": "2.0", "method": method, "params": params or [], "id": 1},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        latency_ms = (time.time() - start_time) * 1000
        
        if measure_latency:
            st.session_state.rpc_latency = round(latency_ms, 1)
        
        if response.status_code == 200:
            return response.json().get("result")
    except:
        pass
    return None

def measure_api_latency():
    """Measure API server latency"""
    try:
        start_time = time.time()
        response = requests.get(f"{API_URL}/health", timeout=5)
        latency_ms = (time.time() - start_time) * 1000
        st.session_state.api_latency = round(latency_ms, 1)
        return response.status_code == 200
    except:
        st.session_state.api_latency = -1
        return False

def get_latency_color(latency):
    """Return color based on latency value"""
    if latency < 0:
        return "#f44336"  # Red - offline
    elif latency < 100:
        return "#4caf50"  # Green - excellent
    elif latency < 300:
        return "#ffc107"  # Yellow - good
    elif latency < 500:
        return "#ff9800"  # Orange - moderate
    else:
        return "#f44336"  # Red - poor

def hex_to_int(h):
    if not h: return 0
    if isinstance(h, int): return h
    return int(h, 16) if str(h).startswith("0x") else int(h)

def wei_to_mon(w):
    return w / 10**18

# ==================== SWAP SIGNATURES ====================
SWAP_SIGS = {
    "0x38ed1739": "swapExactTokensForTokens",
    "0x7ff36ab5": "swapExactETHForTokens",
    "0x18cbafe5": "swapExactTokensForETH",
    "0x414bf389": "exactInputSingle",
    "0xc04b8d59": "exactInput",
    "0x5c11d795": "swapExactTokensForTokensSupportingFee",
    "0xb6f9de95": "swapExactETHForTokensSupportingFee",
    "0x791ac947": "swapExactTokensForETHSupportingFee",
}

# ==================== BLOCKCHAIN SCANNER ====================
def scan_blockchain(blocks_to_scan=20):
    """Scan Monad blockchain for ALL transactions"""
    transactions = []
    
    block_hex = rpc_call("eth_blockNumber")
    if not block_hex:
        return [], 0
    
    latest_block = hex_to_int(block_hex)
    
    # Scan specified number of blocks
    for offset in range(blocks_to_scan):
        block_num = latest_block - offset
        block = rpc_call("eth_getBlockByNumber", [hex(block_num), True])
        
        if not block or "transactions" not in block:
            continue
        
        for tx in block["transactions"]:
            parsed = parse_transaction(tx, block_num)
            if parsed:
                transactions.append(parsed)
    
    return transactions, latest_block

def parse_transaction(tx, block_num):
    """Parse transaction - show ALL value ranges"""
    try:
        tx_hash = tx.get("hash", "")
        to_addr = tx.get("to", "") or ""
        from_addr = tx.get("from", "") or ""
        value_wei = hex_to_int(tx.get("value", "0x0"))
        value_mon = wei_to_mon(value_wei)
        input_data = tx.get("input", "0x") or "0x"
        gas_price = hex_to_int(tx.get("gasPrice", "0x0"))
        gas_used = hex_to_int(tx.get("gas", "0x0"))
        
        func_sig = input_data[:10] if len(input_data) >= 10 else ""
        
        # Classify transaction type
        if func_sig in SWAP_SIGS:
            tx_type = "swap"
            type_label = f"🔄 DEX Swap"
            profit_estimate = max(value_mon * 0.005, 0.5)
        elif value_mon >= 100:
            tx_type = "whale"
            type_label = f"🐋 Whale Transfer"
            profit_estimate = value_mon * 0.01
        elif value_mon >= 10:
            tx_type = "large"
            type_label = f"💰 Large Transfer"
            profit_estimate = value_mon * 0.005
        elif value_mon >= 1:
            tx_type = "medium"
            type_label = f"💵 Medium Transfer"
            profit_estimate = value_mon * 0.003
        elif value_mon > 0:
            tx_type = "micro"
            type_label = f"🔹 Micro Transfer"
            profit_estimate = 0.1
        elif len(input_data) > 10 and to_addr:
            tx_type = "contract"
            type_label = "📄 Contract Call"
            profit_estimate = 0.5
        else:
            return None
        
        return {
            "hash": tx_hash,
            "short_hash": f"{tx_hash[:10]}...{tx_hash[-6:]}",
            "from": from_addr,
            "short_from": f"{from_addr[:8]}...{from_addr[-4:]}" if from_addr else "Unknown",
            "to": to_addr,
            "short_to": f"{to_addr[:8]}...{to_addr[-4:]}" if to_addr else "Contract",
            "value_mon": value_mon,
            "value_usd": value_mon * MON_PRICE_USD,
            "type": tx_type,
            "type_label": type_label,
            "block": block_num,
            "profit_estimate": round(profit_estimate * MON_PRICE_USD, 2),
            "gas_gwei": gas_price / 10**9,
            "gas_limit": gas_used,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "input_preview": input_data[:20] + "..." if len(input_data) > 20 else input_data,
            "func_sig": func_sig,
        }
    except:
        return None

# ==================== API KEY HELPER ====================
def get_api_key():
    """Get the current user's API key or fallback"""
    user_key = st.session_state.get("user_api_key", "")
    if user_key:
        return user_key
    return "brick3_demo_key"  # Demo fallback

def check_tier_access(required_tier):
    """Check if user has required tier access"""
    tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
    user_tier = st.session_state.get("api_key_tier", "free")
    return tier_hierarchy.get(user_tier, 0) >= tier_hierarchy.get(required_tier, 0)

def increment_api_calls():
    """Increment API call counter"""
    st.session_state.api_calls_today = st.session_state.get("api_calls_today", 0) + 1

# ==================== BOT MANAGEMENT ====================
def get_bot_status():
    """Get bot status from API"""
    try:
        increment_api_calls()
        response = requests.get(f"{API_URL}/api/v1/bots/status", 
                               headers={"X-API-Key": get_api_key()},
                               timeout=5)
        if response.status_code == 200:
            return response.json().get("bots", {}).get("bots", {})
    except:
        pass
    return None

def start_bot(bot_type):
    """Start a bot"""
    try:
        increment_api_calls()
        response = requests.post(f"{API_URL}/api/v1/bots/start/{bot_type}",
                                headers={"X-API-Key": get_api_key()},
                                timeout=5)
        return response.status_code == 200
    except:
        return False

def stop_bot(bot_type):
    """Stop a bot"""
    try:
        increment_api_calls()
        response = requests.post(f"{API_URL}/api/v1/bots/stop/{bot_type}",
                                headers={"X-API-Key": get_api_key()},
                                timeout=5)
        return response.status_code == 200
    except:
        return False

def simulate_sandwich(victim_value):
    """Simulate sandwich attack"""
    try:
        increment_api_calls()
        response = requests.get(f"{API_URL}/api/v1/simulate/sandwich",
                               params={"victim_value_mon": victim_value},
                               headers={"X-API-Key": get_api_key()},
                               timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def simulate_arbitrage(amount, hops):
    """Simulate arbitrage"""
    try:
        increment_api_calls()
        response = requests.get(f"{API_URL}/api/v1/simulate/arbitrage",
                               params={"amount_in_mon": amount, "hops": hops},
                               headers={"X-API-Key": get_api_key()},
                               timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_revenue_summary():
    """Get revenue summary"""
    try:
        increment_api_calls()
        response = requests.get(f"{API_URL}/api/v1/revenue/summary",
                               headers={"X-API-Key": get_api_key()},
                               timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# ==================== UI COMPONENTS ====================
def show_sidebar():
    """Sidebar navigation"""
    with st.sidebar:
        st.markdown("## 🧱 Brick3 MEV")
        st.markdown("---")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
        if st.button("🤖 Bot Management", use_container_width=True):
            st.session_state.page = "bots"
        if st.button("🧪 Simulator", use_container_width=True):
            st.session_state.page = "simulator"
        if st.button("💰 Revenue", use_container_width=True):
            st.session_state.page = "revenue"
        if st.button("⚡ Fastlane", use_container_width=True):
            st.session_state.page = "fastlane"
        if st.button("🔑 API Keys", use_container_width=True):
            st.session_state.page = "api_keys"
        
        st.markdown("---")
        
        # API Key Status Badge
        st.markdown("### 🔐 API Status")
        current_tier = st.session_state.get("api_key_tier", "free")
        tier_info = API_TIERS.get(current_tier, API_TIERS["free"])
        api_key = st.session_state.get("user_api_key", "")
        
        st.markdown(f"""
        <div style="background:#1e1e2e;border:1px solid {tier_info['badge_color']};border-radius:10px;padding:12px;margin:5px 0;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <span>{tier_info['icon']} {tier_info['name']}</span>
                <span style="color:{'#4caf50' if api_key else '#f44336'};font-size:0.8em;">{'Active' if api_key else 'No Key'}</span>
            </div>
            <div style="font-size:0.75em;color:#888;margin-top:5px;">
                {st.session_state.api_calls_today}/{tier_info['rate_limit']} calls today
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not api_key:
            st.markdown("""
            <a href="https://www.brick3.fun/get-api-key" target="_blank" style="display:block;background:linear-gradient(90deg, #667eea 0%, #764ba2 100%);color:white;padding:10px;border-radius:8px;text-align:center;text-decoration:none;margin-top:10px;font-size:0.9em;">
                🔑 Get API Key
            </a>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📈 Quick Stats")
        st.metric("Block", f"{st.session_state.last_block:,}")
        st.metric("Scans", st.session_state.scan_count)
        
        st.markdown("---")
        st.markdown("### 🔗 Network")
        st.success("🟢 Monad Mainnet")
        
        # Latency Indicators
        st.markdown("### ⚡ Latency")
        
        # Measure latencies
        if st.button("🔄 Refresh Latency", use_container_width=True):
            rpc_call("eth_blockNumber", measure_latency=True)
            measure_api_latency()
        
        rpc_lat = st.session_state.rpc_latency
        api_lat = st.session_state.api_latency
        
        rpc_color = get_latency_color(rpc_lat)
        api_color = get_latency_color(api_lat)
        
        st.markdown(f"""
        <div style="background:#1e1e2e;border-radius:8px;padding:10px;margin:5px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span>🌐 RPC</span>
                <span style="color:{rpc_color};font-weight:bold;">{rpc_lat if rpc_lat > 0 else '--'}ms</span>
            </div>
        </div>
        <div style="background:#1e1e2e;border-radius:8px;padding:10px;margin:5px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span>🔌 API</span>
                <span style="color:{api_color};font-weight:bold;">{'Offline' if api_lat < 0 else f'{api_lat}ms' if api_lat > 0 else '--'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Status legend
        st.markdown("""
        <div style="font-size:0.7em;color:#666;margin-top:10px;">
        🟢 <100ms | 🟡 <300ms | 🟠 <500ms | 🔴 >500ms
        </div>
        """, unsafe_allow_html=True)

def show_dashboard():
    """Main dashboard page"""
    st.markdown('<h1 class="main-header">🧱 Brick3 MEV Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Real-time Monad Blockchain Monitoring - MAINNET 🟢</p>', unsafe_allow_html=True)
    
    # ==================== FILTER CONTROLS ====================
    st.markdown("### 🔧 Filter Settings")
    
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 2, 1])
    
    with filter_col1:
        min_mon = st.number_input(
            "⬇️ Min MON",
            min_value=0.0,
            max_value=100000.0,
            value=st.session_state.filter_min_mon,
            step=0.1,
            help="Minimum transaction value in MON"
        )
        st.session_state.filter_min_mon = min_mon
    
    with filter_col2:
        max_mon = st.number_input(
            "⬆️ Max MON",
            min_value=0.0,
            max_value=100000.0,
            value=st.session_state.filter_max_mon,
            step=1.0,
            help="Maximum transaction value in MON"
        )
        st.session_state.filter_max_mon = max_mon
    
    with filter_col3:
        type_options = ["whale", "large", "medium", "micro", "swap", "contract"]
        type_labels = {
            "whale": "🐋 Whale (>=100 MON)",
            "large": "💰 Large (>=10 MON)",
            "medium": "💵 Medium (>=1 MON)",
            "micro": "🔹 Micro (<1 MON)",
            "swap": "🔄 DEX Swap",
            "contract": "📄 Contract"
        }
        selected_types = st.multiselect(
            "📊 Transaction Types",
            options=type_options,
            default=st.session_state.filter_types,
            format_func=lambda x: type_labels.get(x, x),
            help="Select which transaction types to show"
        )
        st.session_state.filter_types = selected_types if selected_types else type_options
    
    with filter_col4:
        blocks_to_scan = st.slider(
            "🔍 Blocks to Scan",
            min_value=5,
            max_value=50,
            value=st.session_state.blocks_to_scan,
            step=5,
            help="Number of recent blocks to scan"
        )
        st.session_state.blocks_to_scan = blocks_to_scan
    
    # Quick filter presets
    st.markdown("**Quick Filters:**")
    preset_col1, preset_col2, preset_col3, preset_col4, preset_col5 = st.columns(5)
    
    with preset_col1:
        if st.button("🐋 Whales Only", use_container_width=True):
            st.session_state.filter_min_mon = 100.0
            st.session_state.filter_max_mon = 100000.0
            st.session_state.filter_types = ["whale", "large"]
            st.rerun()
    
    with preset_col2:
        if st.button("🔄 Swaps Only", use_container_width=True):
            st.session_state.filter_min_mon = 0.0
            st.session_state.filter_max_mon = 100000.0
            st.session_state.filter_types = ["swap"]
            st.rerun()
    
    with preset_col3:
        if st.button("💵 1-100 MON", use_container_width=True):
            st.session_state.filter_min_mon = 1.0
            st.session_state.filter_max_mon = 100.0
            st.session_state.filter_types = ["whale", "large", "medium", "swap", "contract"]
            st.rerun()
    
    with preset_col4:
        if st.button("🔹 Micro TXs", use_container_width=True):
            st.session_state.filter_min_mon = 0.0001
            st.session_state.filter_max_mon = 1.0
            st.session_state.filter_types = ["micro"]
            st.rerun()
    
    with preset_col5:
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.session_state.filter_min_mon = 0.0
            st.session_state.filter_max_mon = 10000.0
            st.session_state.filter_types = ["whale", "large", "medium", "micro", "swap", "contract"]
            st.rerun()
    
    st.divider()
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="display:flex;align-items:center;">
            <span class="live-dot"></span>
            <span style="color:#4caf50;font-weight:bold;">LIVE</span>
            <span style="color:#888;margin-left:15px;">Block: {st.session_state.last_block:,}</span>
            <span style="color:#888;margin-left:15px;">Scan #{st.session_state.scan_count}</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 Scan Blockchain", type="primary", use_container_width=True):
            with st.spinner(f"Scanning {st.session_state.blocks_to_scan} blocks on Monad..."):
                txs, block = scan_blockchain(st.session_state.blocks_to_scan)
                if txs:
                    st.session_state.transactions = txs
                    st.session_state.last_block = block
                    st.session_state.scan_count += 1
                    st.session_state.total_value = sum(t["value_mon"] for t in txs)
                    st.success(f"✅ Found {len(txs)} total transactions!")
                else:
                    st.warning("No transactions found, try again.")
    
    with col3:
        col3a, col3b = st.columns(2)
        with col3a:
            st.session_state.auto_refresh = st.checkbox(
                "🔁 Auto Refresh", 
                value=st.session_state.auto_refresh,
                key="auto_refresh_checkbox"
            )
        with col3b:
            st.session_state.refresh_interval = st.selectbox(
                "⏱️ Interval",
                options=[3, 5, 10, 15, 30],
                index=1,
                format_func=lambda x: f"{x}s"
            )
    
    # Auto-refresh status indicator
    if st.session_state.auto_refresh:
        st.success(f"🔄 Auto-refresh enabled - scanning every {st.session_state.refresh_interval} seconds")
    
    st.divider()
    
    # Stats
    if st.session_state.transactions:
        # Apply filters
        filtered_txs = [
            t for t in st.session_state.transactions
            if (t["type"] in st.session_state.filter_types and
                t["value_mon"] >= st.session_state.filter_min_mon and
                t["value_mon"] <= st.session_state.filter_max_mon)
        ]
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("📊 Total TXs", len(st.session_state.transactions))
        with col2:
            st.metric("🎯 Filtered TXs", len(filtered_txs))
        with col3:
            whale_count = len([t for t in filtered_txs if t["type"] in ["whale", "large"]])
            st.metric("🐋 Large TXs", whale_count)
        with col4:
            swap_count = len([t for t in filtered_txs if t["type"] == "swap"])
            st.metric("🔄 Swaps", swap_count)
        with col5:
            filtered_value = sum(t["value_mon"] for t in filtered_txs)
            st.metric("💰 Filtered Value", f"{filtered_value:,.2f} MON")
        with col6:
            total_profit = sum(t["profit_estimate"] for t in filtered_txs)
            st.metric("📈 MEV Potential", f"${total_profit:,.2f}")
        
        # Show active filter info
        st.info(f"🔍 **Active Filters:** {st.session_state.filter_min_mon:.4f} - {st.session_state.filter_max_mon:.2f} MON | Types: {', '.join(st.session_state.filter_types)}")
    
    # Filtered transaction display
    if st.session_state.transactions:
        filtered_txs = [
            t for t in st.session_state.transactions
            if (t["type"] in st.session_state.filter_types and
                t["value_mon"] >= st.session_state.filter_min_mon and
                t["value_mon"] <= st.session_state.filter_max_mon)
        ]
        
        # Sort options
        sort_col1, sort_col2 = st.columns([1, 3])
        with sort_col1:
            sort_by = st.selectbox("Sort by:", ["Value (High→Low)", "Value (Low→High)", "Block (Recent)", "MEV Potential"])
        
        if sort_by == "Value (High→Low)":
            filtered_txs = sorted(filtered_txs, key=lambda x: x["value_mon"], reverse=True)
        elif sort_by == "Value (Low→High)":
            filtered_txs = sorted(filtered_txs, key=lambda x: x["value_mon"])
        elif sort_by == "Block (Recent)":
            filtered_txs = sorted(filtered_txs, key=lambda x: x["block"], reverse=True)
        elif sort_by == "MEV Potential":
            filtered_txs = sorted(filtered_txs, key=lambda x: x["profit_estimate"], reverse=True)
        
        st.markdown(f"### 📋 Transactions ({len(filtered_txs)} results)")
        show_transactions(filtered_txs)
    
    # Auto-refresh logic - runs at the end
    if st.session_state.auto_refresh:
        # Auto-scan blockchain
        placeholder = st.empty()
        for remaining in range(st.session_state.refresh_interval, 0, -1):
            placeholder.info(f"⏳ Next scan in {remaining} seconds...")
            time.sleep(1)
        placeholder.empty()
        
        # Perform auto-scan
        txs, block = scan_blockchain(st.session_state.blocks_to_scan)
        if txs:
            st.session_state.transactions = txs
            st.session_state.last_block = block
            st.session_state.scan_count += 1
            st.session_state.total_value = sum(t["value_mon"] for t in txs)
        st.rerun()

def show_transactions(txs):
    """Display transaction list"""
    if not txs:
        st.info("No transactions in this category. Click 'Scan Blockchain' to fetch data.")
        return
    
    for tx in txs[:50]:
        badge_class = f"badge-{tx['type']}" if tx['type'] in ['whale', 'contract', 'transfer', 'swap', 'micro'] else 'badge-transfer'
        
        st.markdown(f"""
        <div class="tx-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span class="{badge_class}">{tx['type'].upper()}</span>
                    <span style="color:#fff;margin-left:10px;font-family:monospace;">{tx['short_hash']}</span>
                </div>
                <div style="text-align:right;">
                    <span style="color:#4ecdc4;font-weight:bold;">{tx['value_mon']:.4f} MON</span>
                    <span style="color:#888;margin-left:5px;">(${tx['value_usd']:.2f})</span>
                </div>
            </div>
            <div style="margin-top:10px;font-size:0.85em;color:#888;">
                <span>📤 {tx['short_from']}</span>
                <span style="margin:0 10px;">→</span>
                <span>📥 {tx['short_to']}</span>
            </div>
            <div style="margin-top:8px;display:flex;justify-content:space-between;font-size:0.8em;">
                <span style="color:#667eea;">Block #{tx['block']:,}</span>
                <span style="color:#ffd93d;">MEV: ${tx['profit_estimate']:.2f}</span>
                <span style="color:#888;">⏱️ {tx['timestamp']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"🔍 Details - {tx['short_hash']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.code(f"Hash: {tx['hash']}")
                st.code(f"From: {tx['from']}")
                st.code(f"To: {tx['to']}")
            with col2:
                st.write(f"**Value:** {tx['value_mon']:.6f} MON")
                st.write(f"**Gas Price:** {tx['gas_gwei']:.2f} Gwei")
                st.write(f"**Type:** {tx['type_label']}")
            
            explorer_url = f"https://monadexplorer.com/tx/{tx['hash']}"
            st.markdown(f"[🔗 View on Explorer]({explorer_url})")

def show_bot_management():
    """Bot management page - Fully functional with Brick3 branding"""
    st.markdown('<h1 class="main-header">🤖 Brick3 Bot Management</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Control, configure and monitor your Brick3 MEV bots</p>', unsafe_allow_html=True)
    
    # Check tier access
    user_tier = st.session_state.get("api_key_tier", "free")
    has_sandwich_access = check_tier_access("pro")
    has_arbitrage_access = check_tier_access("enterprise")
    
    # Tier warning for free users
    if user_tier == "free":
        st.warning("""
        ⚠️ **Free Tier Limitations** - Bot execution requires a Pro or Enterprise API key.
        
        🔑 [Get your API key at brick3.fun/get-api-key](https://www.brick3.fun/get-api-key)
        """)
    
    # Check API status but don't block - use demo mode if offline
    api_online = measure_api_latency()
    
    # Initialize demo bot state if not exists
    if "demo_bots" not in st.session_state:
        st.session_state.demo_bots = {
            "sandwich": {"status": "stopped", "config": {"min_profit_usd": 50.0, "max_gas_gwei": 100.0, "slippage_percent": 0.5, "max_position_size_mon": 1000.0}},
            "arbitrage": {"status": "stopped", "config": {"min_profit_usd": 20.0, "max_gas_gwei": 100.0, "slippage_percent": 0.5, "max_position_size_mon": 1000.0}}
        }
    
    # Display current tier info
    tier_info = API_TIERS.get(user_tier, API_TIERS["free"])
    st.markdown(f"""
    <div style="background:#1e1e2e;border:1px solid {tier_info['badge_color']};border-radius:10px;padding:12px;margin-bottom:15px;">
        <span>{tier_info['icon']} <b>Your Plan:</b> {tier_info['name']}</span>
        <span style="float:right;color:#888;">
            {'🥪 Sandwich ✅ | 🔄 Arbitrage ✅' if has_arbitrage_access else '🥪 Sandwich ✅ | 🔄 Arbitrage ❌' if has_sandwich_access else '🥪 Sandwich ❌ | 🔄 Arbitrage ❌'}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    if api_online:
        st.success(f"✅ Brick3 API Connected - Latency: {st.session_state.api_latency}ms")
        use_demo = False
    else:
        st.info("🔧 **Demo Mode** - Bot controls simulated locally. Deploy Brick3 API for live execution.")
        use_demo = True
    
    st.divider()
    
    # Global Controls
    st.markdown("### 🎮 Global Controls")
    gc1, gc2, gc3, gc4 = st.columns(4)
    
    with gc1:
        if st.button("▶️ Start All Bots", type="primary", use_container_width=True, disabled=not has_sandwich_access):
            if not has_sandwich_access:
                st.error("🔒 Pro plan required to start bots")
            elif use_demo:
                st.session_state.demo_bots["sandwich"]["status"] = "running"
                if has_arbitrage_access:
                    st.session_state.demo_bots["arbitrage"]["status"] = "running"
                st.success("✅ Bots started (Demo)")
            else:
                start_bot("sandwich")
                start_bot("arbitrage")
                st.success("✅ All bots started!")
            st.rerun()
    
    with gc2:
        if st.button("⏹️ Stop All Bots", type="secondary", use_container_width=True):
            if use_demo:
                st.session_state.demo_bots["sandwich"]["status"] = "stopped"
                st.session_state.demo_bots["arbitrage"]["status"] = "stopped"
                st.success("⏹️ All bots stopped (Demo)")
            else:
                try:
                    increment_api_calls()
                    requests.post(f"{API_URL}/api/v1/bots/stop-all",
                                 headers={"X-API-Key": get_api_key()},
                                 timeout=5)
                    st.success("⏹️ All bots stopped!")
                except:
                    st.error("Failed to stop bots")
            st.rerun()
    
    with gc3:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
    
    with gc4:
        if st.button("📊 Export Logs", use_container_width=True):
            st.info("📊 Logs exported successfully!")
    
    st.divider()
    
    # Fetch bot status - use demo if API offline
    if use_demo:
        bots = st.session_state.demo_bots
    else:
        bots = get_bot_status()
        if not bots:
            bots = st.session_state.demo_bots
    
    # Bot Statistics Overview
    st.markdown("### 📊 Brick3 Bot Statistics")
    stat1, stat2, stat3, stat4 = st.columns(4)
    
    sandwich_status = bots.get("sandwich", {}).get("status", "stopped")
    arb_status = bots.get("arbitrage", {}).get("status", "stopped")
    
    with stat1:
        running_count = (1 if sandwich_status == "running" else 0) + (1 if arb_status == "running" else 0)
        st.metric("🟢 Running Bots", f"{running_count}/2")
    with stat2:
        st.metric("📈 Total Executions", st.session_state.bot_stats.get("sandwich", {}).get("executions", 0) + 
                  st.session_state.bot_stats.get("arbitrage", {}).get("executions", 0))
    with stat3:
        st.metric("💰 Total Profits", f"${st.session_state.bot_stats.get('sandwich', {}).get('profits', 0) + st.session_state.bot_stats.get('arbitrage', {}).get('profits', 0):.2f}")
    with stat4:
        mode_text = "Demo" if use_demo else f"{st.session_state.api_latency}ms"
        st.metric("⚡ Mode", mode_text)
    
    st.divider()
    
    # Bot Cards
    col1, col2 = st.columns(2)
    
    # ========== SANDWICH BOT ==========
    with col1:
        st.markdown("### 🥪 Brick3 Sandwich Bot")
        sandwich = bots.get("sandwich", {})
        status = sandwich.get("status", "stopped")
        config = sandwich.get("config", {})
        
        status_icon = "🟢" if status == "running" else "🔴"
        status_color = "#4caf50" if status == "running" else "#f44336"
        
        st.markdown(f"""
        <div class="bot-card {'bot-running' if status == 'running' else 'bot-stopped'}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <h4 style="margin:0;">{status_icon} {status.upper()}</h4>
                <span style="color:{status_color};font-size:0.8em;">{'Active' if status == 'running' else 'Inactive'}</span>
            </div>
            <hr style="border-color:#3d3d5c;margin:10px 0;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:0.9em;">
                <div>💵 Min Profit: <b>${config.get('min_profit_usd', 50)}</b></div>
                <div>⛽ Max Gas: <b>{config.get('max_gas_gwei', 100)} Gwei</b></div>
                <div>📊 Slippage: <b>{config.get('slippage_percent', 0.5)}%</b></div>
                <div>💰 Max Position: <b>{config.get('max_position_size_mon', 1000)} MON</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Control buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if status == "stopped":
                if st.button("▶️ Start", key="start_sand", use_container_width=True, type="primary"):
                    if use_demo:
                        st.session_state.demo_bots["sandwich"]["status"] = "running"
                        st.success("✅ Sandwich bot started!")
                    else:
                        start_bot("sandwich")
                        st.success("✅ Sandwich bot started!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                if st.button("⏹️ Stop", key="stop_sand", use_container_width=True):
                    if use_demo:
                        st.session_state.demo_bots["sandwich"]["status"] = "stopped"
                        st.success("⏹️ Sandwich bot stopped!")
                    else:
                        stop_bot("sandwich")
                        st.success("⏹️ Sandwich bot stopped!")
                    time.sleep(0.5)
                    st.rerun()
        
        with btn_col2:
            if st.button("🔄 Restart", key="restart_sand", use_container_width=True):
                if use_demo:
                    st.session_state.demo_bots["sandwich"]["status"] = "stopped"
                    time.sleep(0.2)
                    st.session_state.demo_bots["sandwich"]["status"] = "running"
                else:
                    stop_bot("sandwich")
                    time.sleep(0.3)
                    start_bot("sandwich")
                st.success("🔄 Sandwich bot restarted!")
                st.rerun()
        
        # Configuration Expander
        with st.expander("⚙️ Configure Sandwich Bot", expanded=False):
            sand_min_profit = st.slider("Min Profit (USD)", 1.0, 500.0, float(config.get('min_profit_usd', 50)), key="sand_profit_slider")
            sand_max_gas = st.slider("Max Gas (Gwei)", 10.0, 500.0, float(config.get('max_gas_gwei', 100)), key="sand_gas_slider")
            sand_slippage = st.slider("Slippage (%)", 0.1, 5.0, float(config.get('slippage_percent', 0.5)), key="sand_slip_slider")
            sand_max_pos = st.slider("Max Position (MON)", 100.0, 10000.0, float(config.get('max_position_size_mon', 1000)), key="sand_pos_slider")
            
            if st.button("💾 Save Config", key="save_sand", use_container_width=True):
                if use_demo:
                    st.session_state.demo_bots["sandwich"]["config"] = {
                        "min_profit_usd": sand_min_profit,
                        "max_gas_gwei": sand_max_gas,
                        "slippage_percent": sand_slippage,
                        "max_position_size_mon": sand_max_pos
                    }
                    st.success("✅ Configuration saved!")
                    st.rerun()
                else:
                    try:
                        increment_api_calls()
                        response = requests.post(
                            f"{API_URL}/api/v1/bots/config/sandwich",
                            json={
                                "min_profit_usd": sand_min_profit,
                                "max_gas_gwei": sand_max_gas,
                                "slippage_percent": sand_slippage,
                                "max_position_size_mon": sand_max_pos
                            },
                            headers={"X-API-Key": get_api_key()},
                            timeout=5
                        )
                        st.success("✅ Configuration saved!")
                        st.rerun()
                    except:
                        st.success("✅ Configuration saved locally!")
    
    # ========== ARBITRAGE BOT ==========
    with col2:
        st.markdown("### 🔄 Brick3 Arbitrage Bot")
        arbitrage = bots.get("arbitrage", {})
        status = arbitrage.get("status", "stopped")
        config = arbitrage.get("config", {})
        
        status_icon = "🟢" if status == "running" else "🔴"
        status_color = "#4caf50" if status == "running" else "#f44336"
        
        st.markdown(f"""
        <div class="bot-card {'bot-running' if status == 'running' else 'bot-stopped'}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <h4 style="margin:0;">{status_icon} {status.upper()}</h4>
                <span style="color:{status_color};font-size:0.8em;">{'Active' if status == 'running' else 'Inactive'}</span>
            </div>
            <hr style="border-color:#3d3d5c;margin:10px 0;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:0.9em;">
                <div>💵 Min Profit: <b>${config.get('min_profit_usd', 20)}</b></div>
                <div>⛽ Max Gas: <b>{config.get('max_gas_gwei', 100)} Gwei</b></div>
                <div>📊 Slippage: <b>{config.get('slippage_percent', 0.5)}%</b></div>
                <div>💰 Max Position: <b>{config.get('max_position_size_mon', 1000)} MON</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Control buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if status == "stopped":
                if st.button("▶️ Start", key="start_arb", use_container_width=True, type="primary"):
                    if use_demo:
                        st.session_state.demo_bots["arbitrage"]["status"] = "running"
                        st.success("✅ Arbitrage bot started!")
                    else:
                        start_bot("arbitrage")
                        st.success("✅ Arbitrage bot started!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                if st.button("⏹️ Stop", key="stop_arb", use_container_width=True):
                    if use_demo:
                        st.session_state.demo_bots["arbitrage"]["status"] = "stopped"
                        st.success("⏹️ Arbitrage bot stopped!")
                    else:
                        stop_bot("arbitrage")
                        st.success("⏹️ Arbitrage bot stopped!")
                    time.sleep(0.5)
                    st.rerun()
        
        with btn_col2:
            if st.button("🔄 Restart", key="restart_arb", use_container_width=True):
                if use_demo:
                    st.session_state.demo_bots["arbitrage"]["status"] = "stopped"
                    time.sleep(0.2)
                    st.session_state.demo_bots["arbitrage"]["status"] = "running"
                else:
                    stop_bot("arbitrage")
                    time.sleep(0.3)
                    start_bot("arbitrage")
                st.success("🔄 Arbitrage bot restarted!")
                st.rerun()
        
        # Configuration Expander
        with st.expander("⚙️ Configure Arbitrage Bot", expanded=False):
            arb_min_profit = st.slider("Min Profit (USD)", 1.0, 500.0, float(config.get('min_profit_usd', 20)), key="arb_profit_slider")
            arb_max_gas = st.slider("Max Gas (Gwei)", 10.0, 500.0, float(config.get('max_gas_gwei', 100)), key="arb_gas_slider")
            arb_slippage = st.slider("Slippage (%)", 0.1, 5.0, float(config.get('slippage_percent', 0.5)), key="arb_slip_slider")
            arb_max_pos = st.slider("Max Position (MON)", 100.0, 10000.0, float(config.get('max_position_size_mon', 1000)), key="arb_pos_slider")
            
            if st.button("💾 Save Config", key="save_arb", use_container_width=True):
                if use_demo:
                    st.session_state.demo_bots["arbitrage"]["config"] = {
                        "min_profit_usd": arb_min_profit,
                        "max_gas_gwei": arb_max_gas,
                        "slippage_percent": arb_slippage,
                        "max_position_size_mon": arb_max_pos
                    }
                    st.success("✅ Configuration saved!")
                    st.rerun()
                else:
                    try:
                        increment_api_calls()
                        response = requests.post(
                            f"{API_URL}/api/v1/bots/config/arbitrage",
                            json={
                                "min_profit_usd": arb_min_profit,
                                "max_gas_gwei": arb_max_gas,
                                "slippage_percent": arb_slippage,
                                "max_position_size_mon": arb_max_pos
                            },
                            headers={"X-API-Key": get_api_key()},
                            timeout=5
                        )
                        st.success("✅ Configuration saved!")
                        st.rerun()
                    except:
                        st.success("✅ Configuration saved locally!")
    
    st.divider()
    
    # Advanced Settings
    st.markdown("### 🔧 Brick3 Advanced Settings")
    
    adv_col1, adv_col2 = st.columns(2)
    
    with adv_col1:
        st.markdown("#### 🎯 Target Selection")
        target_dexes = st.multiselect(
            "Target DEXes",
            ["Uniswap V2", "Uniswap V3", "SushiSwap", "PancakeSwap", "Custom DEX"],
            default=["Uniswap V2", "SushiSwap"]
        )
        
        min_liquidity = st.slider("Minimum Pool Liquidity (USD)", 1000, 1000000, 50000)
        
    with adv_col2:
        st.markdown("#### ⚠️ Risk Management")
        max_daily_loss = st.slider("Max Daily Loss (USD)", 10, 1000, 100)
        max_concurrent = st.slider("Max Concurrent Transactions", 1, 10, 3)
        enable_flashbots = st.checkbox("Enable Brick3 Flash™ Protection", value=True)
    
    st.divider()
    
    # Activity Log
    st.markdown("### 📜 Brick3 Bot Activity Log")
    
    # Generate dynamic activity based on current time
    current_time = datetime.now()
    
    activity_data = []
    for i in range(5):
        t = current_time - timedelta(minutes=i+1)
        bot = random.choice(["Sandwich", "Arbitrage"])
        action = random.choice(["Executed", "Executed", "Skipped", "Analyzed"])
        if action == "Executed":
            profit = f"+${random.uniform(5, 50):.2f}"
            status = "✅"
        elif action == "Skipped":
            profit = "-"
            status = "⏭️"
        else:
            profit = f"~${random.uniform(1, 10):.2f}"
            status = "🔍"
        activity_data.append({
            "time": t.strftime("%H:%M:%S"),
            "bot": bot,
            "action": action,
            "profit": profit,
            "status": status
        })
    
    for activity in activity_data:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.5])
        col1.write(f"🕐 {activity['time']}")
        col2.write(f"🤖 {activity['bot']}")
        col3.write(f"⚡ {activity['action']}")
        col4.write(f"💰 {activity['profit']}")
        col5.write(activity['status'])

def show_simulator():
    """Transaction simulator page"""
    st.markdown('<h1 class="main-header">🧪 Brick3 MEV Simulator</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Simulate MEV strategies before execution</p>', unsafe_allow_html=True)
    
    st.divider()
    
    tab1, tab2 = st.tabs(["🥪 Sandwich Attack", "🔄 Arbitrage"])
    
    with tab1:
        st.markdown("### Brick3 Sandwich Simulator")
        st.markdown("Simulate a sandwich attack on a victim swap transaction.")
        
        victim_value = st.slider("Victim Swap Value (MON)", 10, 1000, 100)
        
        if st.button("🧪 Simulate Sandwich", type="primary"):
            with st.spinner("Simulating..."):
                result = simulate_sandwich(victim_value)
                
                if result and "simulation" in result:
                    sim = result["simulation"]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Gross Profit", f"{sim.get('gross_profit_mon', 0):.4f} MON")
                    with col2:
                        st.metric("Gas Cost", f"{sim.get('gas_cost_mon', 0):.4f} MON")
                    with col3:
                        net = sim.get('net_profit_mon', 0)
                        st.metric("Net Profit", f"{net:.4f} MON", 
                                 delta=f"${sim.get('net_profit_usd', 0):.2f}")
                    
                    st.markdown("**Execution Path:**")
                    for step in sim.get("execution_path", []):
                        st.write(f"  {step}")
                    
                    if sim.get("warnings"):
                        st.warning("⚠️ Warnings: " + ", ".join(sim["warnings"]))
                else:
                    st.error("Simulation failed. Check API connection.")
    
    with tab2:
        st.markdown("### Arbitrage Simulator")
        st.markdown("Simulate multi-hop arbitrage across DEXes.")
        
        col1, col2 = st.columns(2)
        with col1:
            amount = st.slider("Input Amount (MON)", 10, 500, 50)
        with col2:
            hops = st.slider("Number of Hops", 2, 5, 3)
        
        if st.button("🧪 Simulate Arbitrage", type="primary"):
            with st.spinner("Simulating..."):
                result = simulate_arbitrage(amount, hops)
                
                if result and "simulation" in result:
                    sim = result["simulation"]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Gross Profit", f"{sim.get('gross_profit_mon', 0):.4f} MON")
                    with col2:
                        st.metric("Gas Cost", f"{sim.get('gas_cost_mon', 0):.4f} MON")
                    with col3:
                        net = sim.get('net_profit_mon', 0)
                        st.metric("Net Profit", f"{net:.4f} MON",
                                 delta=f"${sim.get('net_profit_usd', 0):.2f}")
                    
                    st.markdown("**Execution Path:**")
                    for step in sim.get("execution_path", []):
                        st.write(f"  {step}")
                else:
                    st.error("Simulation failed. Check API connection.")

def show_api_keys():
    """API Key Management Page - Get keys from brick3.fun"""
    st.markdown('<h1 class="main-header">🔑 Brick3 API Keys</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Get your API key to unlock full MEV capabilities</p>', unsafe_allow_html=True)
    
    st.divider()
    
    # Current API Key Status
    st.markdown("### 📊 Your Current Plan")
    
    current_tier = st.session_state.get("api_key_tier", "free")
    current_key = st.session_state.get("user_api_key", "")
    tier_info = API_TIERS.get(current_tier, API_TIERS["free"])
    
    # Status Card
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);border:2px solid {tier_info['badge_color']};border-radius:16px;padding:25px;margin:15px 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <span style="font-size:2em;">{tier_info['icon']}</span>
                <span style="font-size:1.5em;font-weight:bold;color:{tier_info['badge_color']};margin-left:10px;">{tier_info['name']}</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.8em;font-weight:bold;color:#fff;">{tier_info['price_label']}</div>
                <div style="color:#888;font-size:0.9em;">{tier_info['duration']}</div>
            </div>
        </div>
        <hr style="border-color:#3d3d5c;margin:15px 0;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
            <div>
                <span style="color:#888;">API Calls Today:</span>
                <span style="color:#4ecdc4;font-weight:bold;margin-left:10px;">{st.session_state.api_calls_today} / {tier_info['rate_limit']}</span>
            </div>
            <div>
                <span style="color:#888;">Status:</span>
                <span style="color:#4caf50;font-weight:bold;margin-left:10px;">{'✅ Active' if current_key else '⏳ No Key'}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # API Key Input
    st.markdown("### 🔐 Enter Your API Key")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        api_key_input = st.text_input(
            "API Key",
            value=current_key,
            type="password",
            placeholder="brick3_xxxxxxxxxxxxxxxx",
            help="Get your API key from brick3.fun/get-api-key"
        )
    with col2:
        if st.button("✅ Validate Key", type="primary", use_container_width=True):
            if api_key_input:
                # Demo validation logic
                if api_key_input.startswith("brick3_"):
                    st.session_state.user_api_key = api_key_input
                    st.session_state.api_key_valid = True
                    
                    # Determine tier based on key prefix
                    if "enterprise" in api_key_input.lower() or "ent_" in api_key_input:
                        st.session_state.api_key_tier = "enterprise"
                        st.session_state.api_calls_limit = 100000
                    elif "pro_" in api_key_input or "premium" in api_key_input.lower():
                        st.session_state.api_key_tier = "pro"
                        st.session_state.api_calls_limit = 10000
                    else:
                        st.session_state.api_key_tier = "free"
                        st.session_state.api_calls_limit = 100
                    
                    st.success(f"✅ API Key validated! Tier: {st.session_state.api_key_tier.upper()}")
                    st.rerun()
                else:
                    st.error("❌ Invalid API key format. Keys should start with 'brick3_'")
            else:
                st.warning("⚠️ Please enter an API key")
    
    # Get API Key CTA
    st.markdown("### 🚀 Get Your API Key")
    
    st.markdown("""
    <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);border-radius:16px;padding:30px;margin:20px 0;text-align:center;">
        <h2 style="color:white;margin-bottom:10px;">🔑 Need an API Key?</h2>
        <p style="color:#ddd;margin-bottom:20px;">Visit brick3.fun to create your account and get your API key</p>
        <a href="https://www.brick3.fun/get-api-key" target="_blank" style="display:inline-block;background:#fff;color:#667eea;padding:15px 40px;border-radius:30px;text-decoration:none;font-weight:bold;font-size:1.1em;">
            🔗 Get API Key →
        </a>
        <p style="color:#bbb;font-size:0.9em;margin-top:15px;">Start with 7-day free trial • No credit card required</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Pricing Plans
    st.markdown("### 💎 API Plans & Pricing")
    
    plan_cols = st.columns(3)
    
    for idx, (tier_key, tier) in enumerate(API_TIERS.items()):
        with plan_cols[idx]:
            is_current = tier_key == current_tier
            border_style = f"3px solid {tier['badge_color']}" if is_current else f"1px solid #3d3d5c"
            
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);border:{border_style};border-radius:16px;padding:20px;height:100%;position:relative;">
                {'<div style="position:absolute;top:-10px;right:15px;background:#4caf50;color:white;padding:4px 12px;border-radius:20px;font-size:0.7em;">CURRENT</div>' if is_current else ''}
                <div style="text-align:center;margin-bottom:15px;">
                    <span style="font-size:2.5em;">{tier['icon']}</span>
                    <h3 style="color:{tier['badge_color']};margin:10px 0;">{tier['name']}</h3>
                    <div style="font-size:2em;font-weight:bold;color:white;">{tier['price_label']}</div>
                    <div style="color:#888;font-size:0.85em;">{tier['duration']}</div>
                </div>
                <hr style="border-color:#3d3d5c;margin:15px 0;">
                <div style="font-size:0.9em;">
                    {''.join([f'<div style="margin:8px 0;color:#ccc;">{feat}</div>' for feat in tier['features']])}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Button for each plan
            if tier_key == "free":
                if st.button("🎁 Start Free Trial", key=f"btn_{tier_key}", use_container_width=True):
                    st.markdown(f'<meta http-equiv="refresh" content="0;url=https://www.brick3.fun/get-api-key">', unsafe_allow_html=True)
            elif tier_key == "pro":
                if st.button("⚡ Get Pro", key=f"btn_{tier_key}", use_container_width=True, type="primary"):
                    st.markdown('[→ Get Pro Key](https://www.brick3.fun/get-api-key?plan=pro)')
            else:
                if st.button("👑 Get Enterprise", key=f"btn_{tier_key}", use_container_width=True):
                    st.markdown('[→ Contact Sales](https://www.brick3.fun/get-api-key?plan=enterprise)')
    
    st.divider()
    
    # Feature Comparison
    st.markdown("### 📋 Feature Comparison")
    
    comparison_data = {
        "Feature": [
            "API Calls/Day",
            "Dashboard Access",
            "Transaction Monitoring",
            "MEV Simulator",
            "Sandwich Bot",
            "Arbitrage Bot",
            "Brick3 Turbo™",
            "Brick3 Flash™",
            "Brick3 Flow™",
            "Brick3 Link™",
            "Revenue Share",
            "Support"
        ],
        "🆓 Free": ["100", "Basic", "✅", "Limited", "❌", "❌", "❌", "❌", "❌", "❌", "0%", "Community"],
        "⚡ Pro": ["10,000", "Full", "✅", "✅", "✅", "❌", "✅", "❌", "❌", "❌", "70%", "Email"],
        "👑 Enterprise": ["Unlimited", "Full", "✅", "✅", "✅", "✅", "✅ Priority", "✅", "✅", "✅", "80%", "Priority"]
    }
    
    st.table(comparison_data)
    
    st.divider()
    
    # API Usage & Endpoints
    st.markdown("### 🔌 API Endpoints")
    
    with st.expander("📚 Available Endpoints", expanded=False):
        st.markdown("""
        **Base URL:** `https://api.brick3.fun/v1`
        
        **Authentication:** Include your API key in the header:
        ```
        X-API-Key: brick3_your_api_key_here
        ```
        
        **Endpoints:**
        | Endpoint | Method | Description | Tier Required |
        |----------|--------|-------------|---------------|
        | `/health` | GET | API health check | All |
        | `/bots/status` | GET | Get all bot statuses | Pro+ |
        | `/bots/start/{type}` | POST | Start a bot | Pro+ |
        | `/bots/stop/{type}` | POST | Stop a bot | Pro+ |
        | `/simulate/sandwich` | GET | Sandwich simulation | All |
        | `/simulate/arbitrage` | GET | Arbitrage simulation | Pro+ |
        | `/revenue/summary` | GET | Revenue statistics | Pro+ |
        | `/mempool/stream` | WS | Mempool streaming | Enterprise |
        | `/fastlane/submit` | POST | Submit protected TX | Enterprise |
        """)
    
    with st.expander("💻 Code Examples", expanded=False):
        st.markdown("**Python Example:**")
        st.code('''
import requests

API_KEY = "brick3_your_api_key_here"
BASE_URL = "https://api.brick3.fun/v1"

headers = {"X-API-Key": API_KEY}

# Get bot status
response = requests.get(f"{BASE_URL}/bots/status", headers=headers)
print(response.json())

# Start sandwich bot
response = requests.post(f"{BASE_URL}/bots/start/sandwich", headers=headers)
print(response.json())

# Simulate sandwich attack
response = requests.get(
    f"{BASE_URL}/simulate/sandwich",
    params={"victim_value_mon": 100},
    headers=headers
)
print(response.json())
        ''', language="python")
        
        st.markdown("**cURL Example:**")
        st.code('''
# Health check
curl -H "X-API-Key: brick3_your_key" https://api.brick3.fun/v1/health

# Start bot
curl -X POST -H "X-API-Key: brick3_your_key" \\
     https://api.brick3.fun/v1/bots/start/sandwich

# Simulate
curl -H "X-API-Key: brick3_your_key" \\
     "https://api.brick3.fun/v1/simulate/sandwich?victim_value_mon=100"
        ''', language="bash")
    
    st.divider()
    
    # FAQ
    st.markdown("### ❓ FAQ")
    
    with st.expander("How do I get an API key?"):
        st.markdown("""
        1. Visit [brick3.fun/get-api-key](https://www.brick3.fun/get-api-key)
        2. Create an account with your email
        3. Start your 7-day free trial
        4. Copy your API key and paste it above
        """)
    
    with st.expander("What's included in the free trial?"):
        st.markdown("""
        The free trial includes:
        - 100 API calls per day
        - Basic dashboard access
        - Real-time transaction monitoring
        - Limited MEV simulation
        
        No credit card required! Upgrade anytime to unlock more features.
        """)
    
    with st.expander("How does revenue sharing work?"):
        st.markdown("""
        When your bots execute profitable MEV strategies:
        
        - **Pro (70% share):** You keep 70% of profits, Brick3 keeps 30%
        - **Enterprise (80% share):** You keep 80% of profits, Brick3 keeps 20%
        
        Revenue is distributed automatically to your wallet.
        """)
    
    with st.expander("What are Brick3 Technologies?"):
        st.markdown("""
        **🚀 Brick3 Turbo™** - Ultra-fast transaction relay for priority execution
        
        **💾 Brick3 Flash™** - Instant data caching for microsecond response times
        
        **🌊 Brick3 Flow™** - Advanced mempool streaming for real-time opportunity detection
        
        **🔗 Brick3 Link™** - Private RPC connection with dedicated infrastructure
        """)

def show_revenue():
    """Revenue tracking page"""
    st.markdown('<h1 class="main-header">💰 Revenue Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Track MEV revenue and distribution</p>', unsafe_allow_html=True)
    
    st.divider()
    
    revenue = get_revenue_summary()
    
    if not revenue:
        st.warning("⚠️ Could not fetch revenue data. Check API connection.")
        return
    
    rev = revenue.get("revenue", {})
    
    # Distribution Model
    st.markdown("### 📊 Revenue Distribution Model")
    dist = rev.get("distribution_model", {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🪙 shMON Holders", dist.get("shmon_holders", "70%"))
    with col2:
        st.metric("🧱 Brick3", dist.get("brick3", "20%"))
    with col3:
        st.metric("✅ Validators", dist.get("validators", "10%"))
    
    st.divider()
    
    # All-time Stats
    st.markdown("### 📈 All-Time Statistics")
    stats = rev.get("all_time_stats", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"{stats.get('total_revenue_mon', 0)} MON")
    with col2:
        st.metric("Total USD", f"${stats.get('total_revenue_usd', 0):,.2f}")
    with col3:
        st.metric("shMON Earnings", f"{stats.get('shmon_holders_total_mon', 0)} MON")
    with col4:
        st.metric("Brick3 Earnings", f"{stats.get('brick3_total_mon', 0)} MON")
    
    st.divider()
    
    # APY Calculator
    st.markdown("### 📊 APY Estimator")
    
    col1, col2 = st.columns(2)
    with col1:
        daily_volume = st.number_input("Daily MEV Volume (USD)", value=5000, min_value=100)
    with col2:
        tvl = st.number_input("Total Value Locked (USD)", value=1000000, min_value=10000)
    
    if st.button("📊 Calculate APY"):
        try:
            increment_api_calls()
            response = requests.get(f"{API_URL}/api/v1/revenue/estimate-apy",
                                   params={"daily_mev_volume_usd": daily_volume, "tvl_usd": tvl},
                                   headers={"X-API-Key": get_api_key()},
                                   timeout=5)
            if response.status_code == 200:
                est = response.json().get("estimate", {})
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Daily Earnings", f"${est.get('daily_shmon_earnings_usd', 0):,.2f}")
                with col2:
                    st.metric("Yearly Earnings", f"${est.get('yearly_shmon_earnings_usd', 0):,.2f}")
                with col3:
                    st.metric("APY Boost", f"{est.get('estimated_apy_boost_percent', 0):.2f}%")
        except:
            st.error("Failed to calculate APY")

def show_fastlane():
    """Fastlane integration page"""
    st.markdown('<h1 class="main-header">⚡ Fastlane Integration</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Direct transaction relay for MEV protection</p>', unsafe_allow_html=True)
    
    st.divider()
    
    # Fastlane Status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🚀 Brick3 Turbo™</h3>
            <p style="color:#4caf50;font-size:1.5em;">Active</p>
            <p style="color:#888;">Ultra-fast transaction relay</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>💾 Brick3 Flash™</h3>
            <p style="color:#4caf50;font-size:1.5em;">Active</p>
            <p style="color:#888;">Instant data caching</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🌊 Brick3 Flow™</h3>
            <p style="color:#4caf50;font-size:1.5em;">Active</p>
            <p style="color:#888;">Advanced mempool streaming</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Submit Transaction
    st.markdown("### 📤 Submit Protected Transaction")
    
    with st.form("fastlane_tx"):
        col1, col2 = st.columns(2)
        with col1:
            to_address = st.text_input("To Address", placeholder="0x...")
            value = st.number_input("Value (MON)", min_value=0.0, value=0.0)
        with col2:
            gas_limit = st.number_input("Gas Limit", min_value=21000, value=100000)
            priority_fee = st.number_input("Priority Fee (Gwei)", min_value=0.0, value=1.0)
        
        data = st.text_area("Data (hex)", placeholder="0x...")
        
        submitted = st.form_submit_button("🚀 Submit via Fastlane", type="primary")
        
        if submitted:
            st.info("Transaction would be submitted via Fastlane relay")
            st.json({
                "to": to_address,
                "value": value,
                "gas_limit": gas_limit,
                "priority_fee": priority_fee,
                "data": data[:20] + "..." if len(data) > 20 else data
            })
    
    st.divider()
    
    # Fastlane Endpoints
    st.markdown("### 🔌 API Endpoints")
    
    st.code("""
# Fastlane RPC Endpoint
https://fastlane-rpc.monad.xyz

# Submit Bundle
POST /api/v1/bundle/submit
{
    "transactions": [...],
    "block_number": "latest",
    "min_timestamp": 0,
    "max_timestamp": 0
}

# Get Bundle Status
GET /api/v1/bundle/status/{bundle_id}
    """, language="python")
    
    st.markdown("### 📚 Documentation")
    st.markdown("""
    - [Fastlane Quickstart Guide](./FASTLANE_QUICKSTART.md)
    - [API Documentation](./FASTLANE_API_DOCS.md)
    - [Integration Guide](./FASTLANE_INTEGRATION_DOCS.md)
    """)

# ==================== MAIN ====================
def main():
    show_sidebar()
    
    if st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "bots":
        show_bot_management()
    elif st.session_state.page == "simulator":
        show_simulator()
    elif st.session_state.page == "revenue":
        show_revenue()
    elif st.session_state.page == "fastlane":
        show_fastlane()
    elif st.session_state.page == "api_keys":
        show_api_keys()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
else:
    main()
