"""
🧱 Brick3 MEV Platform - Full Featured Dashboard
Monad Blockchain MEV Monitoring & Bot Management
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
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
    "refresh_interval": 5
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==================== RPC FUNCTIONS ====================
def rpc_call(method, params=None):
    """Direct JSON-RPC call to Monad"""
    try:
        response = requests.post(
            MONAD_RPC,
            json={"jsonrpc": "2.0", "method": method, "params": params or [], "id": 1},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        if response.status_code == 200:
            return response.json().get("result")
    except:
        pass
    return None

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

# ==================== BOT MANAGEMENT ====================
def get_bot_status():
    """Get bot status from API"""
    try:
        response = requests.get(f"{API_URL}/api/v1/bots/status", 
                               headers={"X-API-Key": "brick3_unlimited_master"},
                               timeout=5)
        if response.status_code == 200:
            return response.json().get("bots", {}).get("bots", {})
    except:
        pass
    return None

def start_bot(bot_type):
    """Start a bot"""
    try:
        response = requests.post(f"{API_URL}/api/v1/bots/start/{bot_type}",
                                headers={"X-API-Key": "brick3_unlimited_master"},
                                timeout=5)
        return response.status_code == 200
    except:
        return False

def stop_bot(bot_type):
    """Stop a bot"""
    try:
        response = requests.post(f"{API_URL}/api/v1/bots/stop/{bot_type}",
                                headers={"X-API-Key": "brick3_unlimited_master"},
                                timeout=5)
        return response.status_code == 200
    except:
        return False

def simulate_sandwich(victim_value):
    """Simulate sandwich attack"""
    try:
        response = requests.get(f"{API_URL}/api/v1/simulate/sandwich",
                               params={"victim_value_mon": victim_value},
                               headers={"X-API-Key": "brick3_unlimited_master"},
                               timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def simulate_arbitrage(amount, hops):
    """Simulate arbitrage"""
    try:
        response = requests.get(f"{API_URL}/api/v1/simulate/arbitrage",
                               params={"amount_in_mon": amount, "hops": hops},
                               headers={"X-API-Key": "brick3_unlimited_master"},
                               timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_revenue_summary():
    """Get revenue summary"""
    try:
        response = requests.get(f"{API_URL}/api/v1/revenue/summary",
                               headers={"X-API-Key": "brick3_unlimited_master"},
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
        
        st.markdown("---")
        st.markdown("### 📈 Quick Stats")
        st.metric("Block", f"{st.session_state.last_block:,}")
        st.metric("Scans", st.session_state.scan_count)
        
        st.markdown("---")
        st.markdown("### 🔗 Network")
        st.success("🟢 Monad Mainnet")
        st.caption(f"RPC: {MONAD_RPC[:30]}...")

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
    """Bot management page"""
    st.markdown('<h1 class="main-header">🤖 Bot Management</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Control and monitor your MEV bots</p>', unsafe_allow_html=True)
    
    st.divider()
    
    # Fetch bot status
    bots = get_bot_status()
    
    if not bots:
        st.warning("⚠️ Could not connect to API. Make sure the API server is running.")
        st.code("python monmev_api.py")
        return
    
    # Bot cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥪 Sandwich Bot")
        sandwich = bots.get("sandwich", {})
        status = sandwich.get("status", "stopped")
        config = sandwich.get("config", {})
        
        status_class = "bot-running" if status == "running" else "bot-stopped"
        st.markdown(f"""
        <div class="bot-card {status_class}">
            <h4>Status: <span class="status-{'running' if status == 'running' else 'stopped'}">{status.upper()}</span></h4>
            <p>Min Profit: ${config.get('min_profit_usd', 50)}</p>
            <p>Max Gas: {config.get('max_gas_gwei', 100)} Gwei</p>
            <p>Slippage: {config.get('slippage_percent', 0.5)}%</p>
            <p>Max Position: {config.get('max_position_size_mon', 1000)} MON</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("▶️ Start Sandwich", use_container_width=True, disabled=status=="running"):
                if start_bot("sandwich"):
                    st.success("Sandwich bot started!")
                    st.rerun()
        with col_b:
            if st.button("⏹️ Stop Sandwich", use_container_width=True, disabled=status=="stopped"):
                if stop_bot("sandwich"):
                    st.success("Sandwich bot stopped!")
                    st.rerun()
    
    with col2:
        st.markdown("### 🔄 Arbitrage Bot")
        arbitrage = bots.get("arbitrage", {})
        status = arbitrage.get("status", "stopped")
        config = arbitrage.get("config", {})
        
        status_class = "bot-running" if status == "running" else "bot-stopped"
        st.markdown(f"""
        <div class="bot-card {status_class}">
            <h4>Status: <span class="status-{'running' if status == 'running' else 'stopped'}">{status.upper()}</span></h4>
            <p>Min Profit: ${config.get('min_profit_usd', 20)}</p>
            <p>Max Gas: {config.get('max_gas_gwei', 100)} Gwei</p>
            <p>Slippage: {config.get('slippage_percent', 0.5)}%</p>
            <p>Max Position: {config.get('max_position_size_mon', 1000)} MON</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("▶️ Start Arbitrage", use_container_width=True, disabled=status=="running"):
                if start_bot("arbitrage"):
                    st.success("Arbitrage bot started!")
                    st.rerun()
        with col_b:
            if st.button("⏹️ Stop Arbitrage", use_container_width=True, disabled=status=="stopped"):
                if stop_bot("arbitrage"):
                    st.success("Arbitrage bot stopped!")
                    st.rerun()
    
    st.divider()
    
    # Bot Configuration
    st.markdown("### ⚙️ Bot Configuration")
    
    with st.expander("Configure Sandwich Bot"):
        col1, col2 = st.columns(2)
        with col1:
            min_profit = st.number_input("Min Profit (USD)", value=50.0, min_value=1.0, key="sand_profit")
            max_gas = st.number_input("Max Gas (Gwei)", value=100.0, min_value=1.0, key="sand_gas")
        with col2:
            slippage = st.number_input("Slippage (%)", value=0.5, min_value=0.1, max_value=5.0, key="sand_slip")
            max_position = st.number_input("Max Position (MON)", value=1000.0, min_value=10.0, key="sand_pos")
        
        if st.button("💾 Save Sandwich Config"):
            st.info("Configuration saved (API endpoint needed)")
    
    with st.expander("Configure Arbitrage Bot"):
        col1, col2 = st.columns(2)
        with col1:
            min_profit = st.number_input("Min Profit (USD)", value=20.0, min_value=1.0, key="arb_profit")
            max_gas = st.number_input("Max Gas (Gwei)", value=100.0, min_value=1.0, key="arb_gas")
        with col2:
            slippage = st.number_input("Slippage (%)", value=0.5, min_value=0.1, max_value=5.0, key="arb_slip")
            max_position = st.number_input("Max Position (MON)", value=1000.0, min_value=10.0, key="arb_pos")
        
        if st.button("💾 Save Arbitrage Config"):
            st.info("Configuration saved (API endpoint needed)")

def show_simulator():
    """Transaction simulator page"""
    st.markdown('<h1 class="main-header">🧪 MEV Simulator</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Simulate MEV strategies before execution</p>', unsafe_allow_html=True)
    
    st.divider()
    
    tab1, tab2 = st.tabs(["🥪 Sandwich Attack", "🔄 Arbitrage"])
    
    with tab1:
        st.markdown("### Sandwich Attack Simulator")
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
            response = requests.get(f"{API_URL}/api/v1/revenue/estimate-apy",
                                   params={"daily_mev_volume_usd": daily_volume, "tvl_usd": tvl},
                                   headers={"X-API-Key": "brick3_unlimited_master"},
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
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
else:
    main()
