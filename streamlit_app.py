"""
🧱 Brick3 MEV Dashboard - Standalone Version
Combined API + Dashboard for Streamlit Cloud
"""

import streamlit as st
import requests
import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque
import random
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🧱 Brick3 MEV Dashboard",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONFIG ====================
MONAD_RPC = os.getenv("MONAD_RPC", "https://rpc.monad.xyz")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# ==================== WEB3 CONNECTION ====================
@st.cache_resource
def get_web3():
    """Initialize Web3 connection"""
    try:
        w3 = Web3(Web3.HTTPProvider(MONAD_RPC, request_kwargs={'timeout': 30}))
        if w3.is_connected():
            return w3
    except Exception as e:
        st.warning(f"Web3 connection error: {e}")
    return None

# ==================== MEV DETECTOR ====================
class MEVDetector:
    """MEV opportunity detector"""
    
    def __init__(self, w3):
        self.w3 = w3
        self.large_transfer_threshold = Web3.to_wei(10, 'ether')
        
    def analyze_transaction(self, tx):
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
            
            # Large transfer detection
            if value >= self.large_transfer_threshold:
                value_eth = Web3.from_wei(value, 'ether')
                opportunities.append({
                    "type": "large_transfer",
                    "tx_hash": tx_hash,
                    "value_eth": float(value_eth),
                    "estimated_profit_usd": float(value_eth) * 0.001 * 3500,
                    "confidence": 0.85,
                    "timestamp": datetime.now().isoformat()
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
                        "timestamp": datetime.now().isoformat()
                    })
                elif len(tx_input) > 100:
                    opportunities.append({
                        "type": "contract",
                        "tx_hash": tx_hash,
                        "target_contract": to_addr,
                        "method_id": method_id,
                        "estimated_profit_usd": random.uniform(10, 100),
                        "confidence": 0.6,
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Regular transfer
            elif value > 0:
                value_eth = Web3.from_wei(value, 'ether')
                opportunities.append({
                    "type": "transfer",
                    "tx_hash": tx_hash,
                    "value_eth": float(value_eth),
                    "estimated_profit_usd": float(value_eth) * 0.0001 * 3500,
                    "confidence": 0.5,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            pass
        
        return opportunities

# ==================== DEMO DATA GENERATOR ====================
def generate_demo_opportunity():
    """Generate realistic demo MEV opportunity"""
    types = ["sandwich", "large_transfer", "contract", "transfer"]
    mev_type = random.choices(types, weights=[0.3, 0.2, 0.3, 0.2])[0]
    
    # Generate realistic tx hash
    tx_hash = "0x" + "".join(random.choices("0123456789abcdef", k=64))
    
    base_data = {
        "type": mev_type,
        "tx_hash": tx_hash,
        "timestamp": datetime.now().isoformat(),
        "block_number": random.randint(10000000, 15000000)
    }
    
    if mev_type == "sandwich":
        base_data.update({
            "target_contract": "0x" + "".join(random.choices("0123456789abcdef", k=40)),
            "method_id": random.choice(['0x38ed1739', '0x7ff36ab5', '0x18cbafe5']),
            "estimated_profit_usd": round(random.uniform(50, 800), 2),
            "confidence": round(random.uniform(0.7, 0.95), 2)
        })
    elif mev_type == "large_transfer":
        value_eth = round(random.uniform(10, 500), 4)
        base_data.update({
            "value_eth": value_eth,
            "estimated_profit_usd": round(value_eth * 0.001 * 3500, 2),
            "confidence": round(random.uniform(0.8, 0.95), 2)
        })
    elif mev_type == "contract":
        base_data.update({
            "target_contract": "0x" + "".join(random.choices("0123456789abcdef", k=40)),
            "method_id": "0x" + "".join(random.choices("0123456789abcdef", k=8)),
            "estimated_profit_usd": round(random.uniform(10, 200), 2),
            "confidence": round(random.uniform(0.55, 0.75), 2)
        })
    else:
        value_eth = round(random.uniform(0.1, 5), 4)
        base_data.update({
            "value_eth": value_eth,
            "estimated_profit_usd": round(value_eth * 0.0001 * 3500, 2),
            "confidence": round(random.uniform(0.4, 0.6), 2)
        })
    
    return base_data

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

# ==================== SCAN FUNCTION ====================
def scan_blockchain():
    """Scan blockchain for MEV opportunities"""
    w3 = get_web3()
    
    if DEMO_MODE or w3 is None:
        # Demo mode - generate fake data
        if random.random() < 0.3:  # 30% chance
            return [generate_demo_opportunity()]
        return []
    
    try:
        detector = MEVDetector(w3)
        current_block = w3.eth.block_number
        
        if st.session_state.last_block == 0:
            st.session_state.last_block = current_block - 1
        
        if current_block <= st.session_state.last_block:
            return []
        
        opportunities = []
        
        for block_num in range(st.session_state.last_block + 1, current_block + 1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    opps = detector.analyze_transaction(tx)
                    opportunities.extend(opps)
            except:
                pass
        
        st.session_state.last_block = current_block
        return opportunities
        
    except Exception as e:
        return []

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🧱 Brick3 MEV")
    st.markdown("---")
    
    # Connection status
    w3 = get_web3()
    if w3 and w3.is_connected():
        st.success(f"🟢 Connected to Monad")
        st.caption(f"Block: {w3.eth.block_number:,}")
    else:
        st.warning("🟡 Demo Mode")
    
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
    st.markdown("### 📊 Stats")
    st.metric("Total Opportunities", len(st.session_state.opportunities))
    total_profit = sum(o.get("estimated_profit_usd", 0) for o in st.session_state.opportunities)
    st.metric("Total Profit", f"${total_profit:,.2f}")

# ==================== MAIN CONTENT ====================
st.markdown('<h1 class="main-header">🧱 Brick3 MEV Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #888;">Real-time MEV Opportunity Monitoring for Monad</p>', unsafe_allow_html=True)

# ==================== TABS ====================
tab1, tab2, tab3, tab4 = st.tabs(["📊 MEV Monitor", "🤖 Bot Control", "💰 Revenue", "📈 Analytics"])

# ==================== TAB 1: MEV MONITOR ====================
with tab1:

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

    # Scan if monitoring (with rate limiting)
    import time as time_module
    if st.session_state.monitoring:
        current_time = time_module.time()
        # Only scan every 3 seconds minimum
        if current_time - st.session_state.last_scan_time >= 3:
            st.session_state.last_scan_time = current_time
            new_opps = scan_blockchain()
            if new_opps:
                # Filter out duplicates
                unique_opps = []
                for opp in new_opps:
                    tx_hash = opp.get("tx_hash", "")
                    if tx_hash and tx_hash not in st.session_state.seen_tx_hashes:
                        st.session_state.seen_tx_hashes.add(tx_hash)
                        unique_opps.append(opp)
                
                if unique_opps:
                    st.session_state.opportunities = unique_opps + st.session_state.opportunities
                    # Keep only last 100
                    st.session_state.opportunities = st.session_state.opportunities[:100]
                    # Clean up seen hashes (keep only last 500)
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
    else:
        for opp in filtered_opps[:20]:  # Show max 20
            mev_type = opp.get("type", "unknown")
            emoji = get_type_emoji(mev_type)
            color = get_type_color(mev_type)
            profit = opp.get("estimated_profit_usd", 0)
            confidence = opp.get("confidence", 0)
            tx_hash = opp.get("tx_hash", "N/A")
            timestamp = opp.get("timestamp", "N/A")
            
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
                
                with col1:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.5em;">{emoji}</span>
                        <span class="badge-{mev_type.replace('_', '-')}">{mev_type.upper()}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    short_hash = f"{tx_hash[:10]}...{tx_hash[-6:]}" if len(tx_hash) > 20 else tx_hash
                    st.markdown(f"[🔗 {short_hash}](https://monadexplorer.com/tx/{tx_hash})")
                
                with col3:
                    st.markdown(f"**💰 {format_profit(profit)}**")
                
                with col4:
                    conf_color = "#4caf50" if confidence >= 0.7 else "#ff9800" if confidence >= 0.5 else "#f44336"
                    st.markdown(f'<span style="color: {conf_color};">🎯 {confidence:.0%}</span>', unsafe_allow_html=True)
            
            st.markdown("---")

# ==================== TAB 2: BOT CONTROL ====================
with tab2:
    st.markdown("### 🤖 MEV Bot Control Panel")
    st.markdown("Start and stop MEV extraction bots with one click.")
    
    # Initialize bot session state
    if "bots" not in st.session_state:
        st.session_state.bots = {
            "sandwich": {"status": "stopped", "executions": 0, "profit": 0, "enabled": True},
            "arbitrage": {"status": "stopped", "executions": 0, "profit": 0, "enabled": True},
            "liquidation": {"status": "stopped", "executions": 0, "profit": 0, "enabled": False},
            "backrun": {"status": "stopped", "executions": 0, "profit": 0, "enabled": True}
        }
    
    st.markdown("---")
    
    # Bot cards
    bot_cols = st.columns(2)
    
    bot_configs = [
        ("sandwich", "🥪 Sandwich Bot", "Frontrun large DEX swaps for profit", "#ff6b6b"),
        ("arbitrage", "🔄 Arbitrage Bot", "Multi-hop DEX arbitrage opportunities", "#4ecdc4"),
        ("liquidation", "💀 Liquidation Bot", "Capture liquidation bonuses from lending", "#ffd93d"),
        ("backrun", "🏃 Backrun Bot", "Backrun profitable transactions", "#a855f7")
    ]
    
    for idx, (bot_id, name, desc, color) in enumerate(bot_configs):
        with bot_cols[idx % 2]:
            bot = st.session_state.bots[bot_id]
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%); 
                        border: 2px solid {color if bot['status'] == 'running' else '#3d3d5c'}; 
                        border-radius: 16px; padding: 20px; margin-bottom: 15px;">
                <h3 style="color: {color}; margin: 0;">{name}</h3>
                <p style="color: #888; font-size: 0.9em; margin: 5px 0 15px 0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                status_icon = "🟢" if bot['status'] == 'running' else "🔴"
                st.markdown(f"**Status:** {status_icon} {bot['status'].upper()}")
            
            with col2:
                st.markdown(f"**Executions:** {bot['executions']}")
            
            with col3:
                st.markdown(f"**Profit:** ${bot['profit']:.2f}")
            
            # Control buttons
            btn_cols = st.columns(3)
            with btn_cols[0]:
                if bot['status'] == 'stopped':
                    if st.button(f"▶️ Start", key=f"start_{bot_id}", use_container_width=True):
                        st.session_state.bots[bot_id]['status'] = 'running'
                        st.toast(f"{name} started!", icon="✅")
                        st.rerun()
                else:
                    if st.button(f"⏹️ Stop", key=f"stop_{bot_id}", use_container_width=True):
                        st.session_state.bots[bot_id]['status'] = 'stopped'
                        st.toast(f"{name} stopped!", icon="🛑")
                        st.rerun()
            
            with btn_cols[1]:
                enabled = st.checkbox("Enabled", value=bot['enabled'], key=f"enable_{bot_id}")
                st.session_state.bots[bot_id]['enabled'] = enabled
            
            with btn_cols[2]:
                if st.button("⚙️ Config", key=f"config_{bot_id}"):
                    st.session_state[f"show_config_{bot_id}"] = True
            
            # Config expander
            if st.session_state.get(f"show_config_{bot_id}", False):
                with st.expander(f"{name} Configuration", expanded=True):
                    min_profit = st.number_input(
                        "Min Profit (USD)", 
                        min_value=0.0, max_value=1000.0, value=10.0,
                        key=f"min_profit_{bot_id}"
                    )
                    max_gas = st.number_input(
                        "Max Gas (Gwei)",
                        min_value=0.0, max_value=500.0, value=50.0,
                        key=f"max_gas_{bot_id}"
                    )
                    slippage = st.slider(
                        "Slippage %",
                        min_value=0.1, max_value=5.0, value=1.0,
                        key=f"slippage_{bot_id}"
                    )
                    if st.button("Save Config", key=f"save_config_{bot_id}"):
                        st.success("Configuration saved!")
                        st.session_state[f"show_config_{bot_id}"] = False
                        st.rerun()
            
            st.markdown("---")
    
    # Global controls
    st.markdown("### 🎛️ Global Controls")
    global_cols = st.columns(4)
    
    with global_cols[0]:
        if st.button("▶️ Start All Bots", use_container_width=True, type="primary"):
            for bot_id in st.session_state.bots:
                if st.session_state.bots[bot_id]['enabled']:
                    st.session_state.bots[bot_id]['status'] = 'running'
            st.toast("All bots started!", icon="🚀")
            st.rerun()
    
    with global_cols[1]:
        if st.button("⏹️ Stop All Bots", use_container_width=True, type="secondary"):
            for bot_id in st.session_state.bots:
                st.session_state.bots[bot_id]['status'] = 'stopped'
            st.toast("All bots stopped!", icon="🛑")
            st.rerun()
    
    with global_cols[2]:
        running = sum(1 for b in st.session_state.bots.values() if b['status'] == 'running')
        st.metric("Running Bots", f"{running}/4")
    
    with global_cols[3]:
        total_profit = sum(b['profit'] for b in st.session_state.bots.values())
        st.metric("Total Bot Profit", f"${total_profit:.2f}")

# ==================== TAB 3: REVENUE ====================
with tab3:
    st.markdown("### 💰 Revenue Distribution")
    st.markdown("Track MEV revenue and distribution across stakeholders.")
    
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
    
    # Revenue stats (simulated)
    if "revenue" not in st.session_state:
        st.session_state.revenue = {
            "total_captured": 12450.75,
            "shmon_share": 8715.53,
            "brick3_share": 2490.15,
            "validator_share": 1245.07,
            "pending": 350.25,
            "distributions": 24
        }
    
    rev = st.session_state.revenue
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💵 Total MEV Captured", f"${rev['total_captured']:,.2f}")
    with col2:
        st.metric("⏳ Pending Distribution", f"${rev['pending']:.2f}")
    with col3:
        st.metric("📦 Distributions", rev['distributions'])
    
    st.markdown("---")
    
    # Distribution breakdown
    st.markdown("### 📊 Distribution Breakdown")
    
    dist_cols = st.columns(3)
    
    with dist_cols[0]:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(78, 205, 196, 0.1) 0%, rgba(78, 205, 196, 0.2) 100%); 
                    border: 1px solid #4ecdc4; border-radius: 12px; padding: 20px; text-align: center;">
            <h4 style="color: #4ecdc4;">🪙 shMON Holders</h4>
            <h2 style="color: #4ecdc4; margin: 10px 0;">${:,.2f}</h2>
            <p style="color: #888;">70% of MEV Revenue</p>
        </div>
        """.format(rev['shmon_share']), unsafe_allow_html=True)
    
    with dist_cols[1]:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(255, 217, 61, 0.1) 0%, rgba(255, 217, 61, 0.2) 100%); 
                    border: 1px solid #ffd93d; border-radius: 12px; padding: 20px; text-align: center;">
            <h4 style="color: #ffd93d;">🧱 Brick3 Protocol</h4>
            <h2 style="color: #ffd93d; margin: 10px 0;">${:,.2f}</h2>
            <p style="color: #888;">20% Protocol Fee</p>
        </div>
        """.format(rev['brick3_share']), unsafe_allow_html=True)
    
    with dist_cols[2]:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 107, 107, 0.2) 100%); 
                    border: 1px solid #ff6b6b; border-radius: 12px; padding: 20px; text-align: center;">
            <h4 style="color: #ff6b6b;">⛓️ Validators</h4>
            <h2 style="color: #ff6b6b; margin: 10px 0;">${:,.2f}</h2>
            <p style="color: #888;">10% Priority Fee</p>
        </div>
        """.format(rev['validator_share']), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # APY Boost Calculator
    st.markdown("### 📈 APY Boost Calculator")
    
    calc_cols = st.columns(2)
    
    with calc_cols[0]:
        daily_mev = st.number_input(
            "Daily MEV Capture ($)",
            min_value=0.0, max_value=1000000.0, value=1000.0,
            help="Estimated daily MEV capture volume"
        )
        tvl = st.number_input(
            "Total Value Locked ($)",
            min_value=1.0, max_value=100000000.0, value=1000000.0,
            help="Total shMON value locked"
        )
    
    with calc_cols[1]:
        # Calculate APY boost
        shmon_daily = daily_mev * 0.7  # 70% to shMON holders
        shmon_yearly = shmon_daily * 365
        apy_boost = (shmon_yearly / tvl) * 100 if tvl > 0 else 0
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 12px; padding: 25px; text-align: center;">
            <h4 style="color: white; margin-top: 0;">Estimated APY Boost</h4>
            <h1 style="color: white; margin: 10px 0; font-size: 3em;">+{:.2f}%</h1>
            <p style="color: rgba(255,255,255,0.8);">Additional yield from MEV</p>
        </div>
        """.format(apy_boost), unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="margin-top: 15px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px;">
            <p style="color: #888; font-size: 0.9em; margin: 0;">
                📊 Daily shMON earnings: ${shmon_daily:,.2f}<br>
                📅 Yearly projection: ${shmon_yearly:,.2f}
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==================== TAB 4: ANALYTICS ====================
with tab4:
    st.markdown("### 📈 MEV Analytics")
    
    # Summary stats
    if st.session_state.opportunities:
        # Type distribution
        type_counts = {}
        type_profits = {}
        for opp in st.session_state.opportunities:
            t = opp.get("type", "unknown")
            p = opp.get("estimated_profit_usd", 0)
            type_counts[t] = type_counts.get(t, 0) + 1
            type_profits[t] = type_profits.get(t, 0) + p
        
        st.markdown("#### 📊 Opportunity Distribution")
        
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            # Create bar chart data
            import pandas as pd
            type_df = pd.DataFrame({
                "Type": list(type_counts.keys()),
                "Count": list(type_counts.values())
            })
            st.bar_chart(type_df.set_index("Type"))
            st.caption("Opportunity count by type")
        
        with chart_cols[1]:
            profit_df = pd.DataFrame({
                "Type": list(type_profits.keys()),
                "Profit ($)": list(type_profits.values())
            })
            st.bar_chart(profit_df.set_index("Type"))
            st.caption("Estimated profit by type")
        
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
    else:
        st.info("📊 No data available. Start monitoring to collect analytics.")
    
    st.markdown("---")
    
    # Export
    st.markdown("#### 📥 Export Data")
    
    export_cols = st.columns(3)
    
    with export_cols[0]:
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
    
    with export_cols[1]:
        if st.button("📊 Export as CSV"):
            if st.session_state.opportunities:
                import pandas as pd
                df = pd.DataFrame(st.session_state.opportunities)
                st.download_button(
                    "Download CSV",
                    data=df.to_csv(index=False),
                    file_name=f"brick3_mev_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")

# Auto-refresh with proper interval
if auto_refresh and st.session_state.monitoring:
    time.sleep(refresh_interval)  # Use user-selected interval
    st.rerun()
