"""
🧱 Brick3 MEV Dashboard
Real-time MEV Monitoring Dashboard for Monad
Streamlit Frontend
"""

import streamlit as st
import requests
import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque
import random

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🧱 Brick3 MEV Dashboard",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONFIG ====================
import os
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "brick3_unlimited_master")

# ==================== SESSION STATE ====================
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "opportunities" not in st.session_state:
    st.session_state.opportunities = []
if "stats" not in st.session_state:
    st.session_state.stats = {
        "total_opportunities": 0,
        "total_profit_usd": 0.0,
        "avg_profit_usd": 0.0,
        "opportunities_by_type": {"sandwich": 0, "large_transfer": 0, "contract": 0, "transfer": 0},
        "last_block": 0,
        "uptime_hours": 0
    }
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = None

# ==================== STYLES ====================
st.markdown("""
<style>
/* Dark theme */
.stApp {
    background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
}

/* Cards */
.metric-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    border: 1px solid #3d3d5c;
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
}

/* Header */
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em;
    font-weight: 800;
    text-align: center;
    margin-bottom: 20px;
}

/* Type badges */
.badge-sandwich { background: #ff6b6b; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
.badge-large-transfer { background: #4ecdc4; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
.badge-contract { background: #ffd93d; color: black; padding: 4px 12px; border-radius: 20px; font-weight: 600; }
.badge-transfer { background: #95a5a6; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; }

/* Opportunity card */
.opp-card {
    background: rgba(30, 30, 46, 0.8);
    border: 1px solid #3d3d5c;
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    transition: transform 0.2s;
}

.opp-card:hover {
    transform: translateY(-2px);
    border-color: #667eea;
}

/* Status indicators */
.status-ok { color: #4ecdc4; font-weight: bold; }
.status-error { color: #ff6b6b; font-weight: bold; }

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Sidebar - Her Zaman Açık */
section[data-testid="stSidebar"] {
    min-width: 300px !important;
    max-width: 300px !important;
}

section[data-testid="stSidebar"] > div {
    min-width: 300px !important;
    max-width: 300px !important;
}

/* Sidebar collapse button'u gizle */
button[kind="header"] {
    display: none !important;
}

section[data-testid="stSidebar"][aria-expanded="false"] {
    display: block !important;
    margin-left: 0 !important;
}

/* Sidebar arka plan */
section[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
}
</style>
""", unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ====================

def fetch_opportunities(type_filter=None, min_profit=None, limit=50):
    """Fetch opportunities from API"""
    try:
        params = {"limit": limit}
        if type_filter and type_filter != "all":
            params["type"] = type_filter
        if min_profit:
            params["min_profit"] = min_profit
        
        response = requests.get(
            f"{API_URL}/api/v1/opportunities",
            params=params,
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("opportunities", [])
    except:
        pass
    return []

def fetch_stats():
    """Fetch stats from API"""
    try:
        response = requests.get(f"{API_URL}/api/v1/stats", headers={"X-API-Key": API_KEY}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("stats", {})
    except:
        pass
    return {}

def fetch_health():
    """Check API health"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_type_emoji(mev_type: str) -> str:
    """Get emoji for MEV type"""
    emojis = {
        "sandwich": "🥪",
        "large_transfer": "🐋",
        "contract": "🔄",
        "transfer": "💸"
    }
    return emojis.get(mev_type, "❓")

def get_type_color(mev_type: str) -> str:
    """Get color for MEV type"""
    colors = {
        "sandwich": "#ff6b6b",
        "large_transfer": "#4ecdc4",
        "contract": "#ffd93d",
        "transfer": "#95a5a6"
    }
    return colors.get(mev_type, "#666")

def format_profit(profit: float) -> str:
    """Format profit display"""
    if profit >= 100:
        return f"${profit:,.0f}"
    elif profit >= 10:
        return f"${profit:.1f}"
    else:
        return f"${profit:.2f}"

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown("## 🧱 Brick3 MEV")
    st.markdown("---")
    
    # 🚀 Start/Stop Monitoring
    st.markdown("### 🚀 Monitoring")
    
    if st.session_state.monitoring:
        if st.button("⏹️ Stop Monitoring", use_container_width=True, type="secondary"):
            st.session_state.monitoring = False
            st.success("Monitoring stopped!")
            st.rerun()
        st.success("✅ Monitoring Active")
    else:
        if st.button("▶️ Start Monitoring", use_container_width=True, type="primary"):
            st.session_state.monitoring = True
            st.success("Monitoring started!")
            st.rerun()
        st.info("⏸️ Monitoring Paused")
    
    st.markdown("---")
    
    # 🎛️ Controls
    st.markdown("### 🎛️ Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        auto_refresh = st.toggle("Auto", value=False)
    
    refresh_interval = st.slider("Interval (s)", 2, 30, 5)
    st.markdown("---")
    
    # 🔍 Filters
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
    min_profit = st.number_input("Min Profit ($)", min_value=0.0, value=0.0, step=1.0)
    result_limit = st.slider("Results Limit", 10, 200, 50)
    st.markdown("---")
    
    # ⚙️ Settings
    st.markdown("### ⚙️ Settings")
    api_endpoint = st.text_input("API URL", value=API_URL)
    st.markdown("**🔑 API Key**")
    st.code("brick3_unlimited_master", language=None)
    
    with st.expander("📋 Available Keys"):
        st.markdown("""
        - `brick3_unlimited_master` - Master
        - `brick3_monmev_prod` - Production
        - `bk3_fastlane_partner` - FastLane
        - `bk3_apriori_validator` - aPriori
        - `bk3_kuru_integration` - Kuru
        """)
    
    st.markdown("---")
    
    # 📦 Data
    st.markdown("### 📦 Data")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export", use_container_width=True):
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "stats": fetch_stats(),
                "opportunities": fetch_opportunities(limit=500)
            }
            st.download_button(
                label="💾 JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"mev_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col2:
        uploaded_file = st.file_uploader("📥", type=['json'], label_visibility="collapsed")
    
    if uploaded_file is not None:
        try:
            imported_data = json.load(uploaded_file)
            st.success(f"✅ Imported {len(imported_data.get('opportunities', []))} opportunities")
        except Exception as e:
            st.error(f"❌ Import error: {str(e)}")
    
    with st.expander("📊 More Export"):
        if st.button("📄 CSV", use_container_width=True):
            opps = fetch_opportunities(limit=500)
            if opps:
                import pandas as pd
                df = pd.DataFrame(opps)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="💾 CSV",
                    data=csv,
                    file_name=f"mev_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    st.markdown("---")
    
    # Connection Status
    health = fetch_health()
    if health and health.get("status") == "ok":
        st.success("✅ API Connected")
        if health.get("rpc_connected"):
            st.success("✅ RPC Connected")
        else:
            st.warning("⚠️ RPC Disconnected")
    else:
        st.error("❌ API Offline")

# ==================== MAIN CONTENT ====================

# Header
st.markdown('<h1 class="main-header">🧱 Brick3 MEV Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #888;">Real-time MEV Monitoring for Monad</p>', unsafe_allow_html=True)

# Fetch data
opportunities = fetch_opportunities(
    type_filter=type_filter if type_filter != "all" else None,
    min_profit=min_profit if min_profit > 0 else None,
    limit=result_limit
)
stats = fetch_stats()

# Network Info Banner
health = fetch_health()
if health:
    st.success(f"🔴 **LIVE MODE** - Monad Mainnet (Chain ID: 143) - Gerçek blockchain verileri")
else:
    st.error("⚠️ API bağlantı hatası")

# Stats Row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "📊 Opportunities",
        f"{stats.get('total_opportunities', 0):,}",
        help="Total MEV opportunities detected"
    )

with col2:
    st.metric(
        "💰 Total Profit",
        f"${stats.get('total_profit_usd', 0):,.2f}",
        help="Total potential profit USD"
    )

with col3:
    st.metric(
        "📈 Avg Profit",
        f"${stats.get('avg_profit_usd', 0):.2f}",
        help="Average profit per opportunity"
    )

with col4:
    st.metric(
        "📦 Last Block",
        f"{stats.get('last_block', 0):,}",
        help="Last processed block"
    )

with col5:
    st.metric(
        "⏱️ Uptime",
        f"{stats.get('uptime_hours', 0):.1f}h",
        help="API uptime"
    )

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📡 Live Feed", "📊 Analytics", "⚡ FastLane", "🔌 API Status"])

# ==================== TAB 1: LIVE FEED ====================
with tab1:
    st.markdown("### 🔥 Latest MEV Opportunities")
    
    if opportunities:
        for i, opp in enumerate(opportunities[:20]):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 2, 1])
                
                with col1:
                    mev_type = opp.get("type", "unknown")
                    emoji = get_type_emoji(mev_type)
                    st.markdown(f"**{emoji} {mev_type.upper()}**")
                    st.caption(f"ID: `{opp.get('id', 'N/A')}`")
                
                with col2:
                    profit = opp.get("potential_profit_usd", 0)
                    st.markdown(f"**{format_profit(profit)}**")
                    st.caption("Profit")
                
                with col3:
                    confidence = opp.get("confidence", 0)
                    conf_color = "#4ecdc4" if confidence > 0.7 else "#ffd93d" if confidence > 0.5 else "#ff6b6b"
                    st.markdown(f"**<span style='color:{conf_color}'>{confidence:.0%}</span>**", unsafe_allow_html=True)
                    st.caption("Confidence")
                
                with col4:
                    tx_hash = opp.get("tx_hash", "N/A")
                    short_hash = f"{tx_hash[:10]}...{tx_hash[-8:]}" if len(tx_hash) > 20 else tx_hash
                    st.markdown(f"[`{short_hash}`](https://monadexplorer.com/tx/{tx_hash})")
                    st.caption(f"Block: {opp.get('block', 'N/A')}")
                
                with col5:
                    details = opp.get("details", {})
                    value = details.get("value_mon", 0)
                    st.markdown(f"**{value:.2f} MON**")
                    st.caption(details.get("swap_type", "Transfer"))
                
                st.markdown("---")
    else:
        st.info("🔍 No opportunities found. Waiting for transactions...")
        
        # Demo data button
        if st.button("📊 Load Demo Data"):
            st.session_state.opportunities = [
                {
                    "id": f"opp_demo_{i}",
                    "type": random.choice(["sandwich", "large_transfer", "contract", "transfer"]),
                    "tx_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                    "potential_profit_usd": random.uniform(10, 200),
                    "confidence": random.uniform(0.5, 0.95),
                    "block": 2530000 + random.randint(0, 1000),
                    "timestamp": datetime.now().isoformat(),
                    "details": {
                        "value_mon": random.uniform(10, 500),
                        "swap_type": random.choice(["DEX Swap", "Transfer"])
                    }
                }
                for i in range(10)
            ]
            st.rerun()

# ==================== TAB 2: ANALYTICS ====================
with tab2:
    st.markdown("### 📈 MEV Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🥧 Opportunities by Type")
        
        type_data = stats.get("opportunities_by_type", {})
        if any(type_data.values()):
            import pandas as pd
            
            df = pd.DataFrame({
                "Type": [f"{get_type_emoji(k)} {k.title()}" for k in type_data.keys()],
                "Count": list(type_data.values())
            })
            
            st.bar_chart(df.set_index("Type"))
        else:
            st.info("No data available yet")
    
    with col2:
        st.markdown("#### 📊 Statistics")
        
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | 🥪 Sandwich | {type_data.get('sandwich', 0)} |
        | 🐋 Large Transfer | {type_data.get('large_transfer', 0)} |
        | 🔄 Contract | {type_data.get('contract', 0)} |
        | 💸 Transfer | {type_data.get('transfer', 0)} |
        | **Total** | **{stats.get('total_opportunities', 0)}** |
        """)
    
    st.markdown("---")
    
    st.markdown("#### 💰 Profit Distribution")
    
    if opportunities:
        profits = [o.get("potential_profit_usd", 0) for o in opportunities]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Min", f"${min(profits):.2f}" if profits else "$0")
        with col2:
            st.metric("Max", f"${max(profits):.2f}" if profits else "$0")
        with col3:
            avg = sum(profits) / len(profits) if profits else 0
            st.metric("Average", f"${avg:.2f}")
        with col4:
            st.metric("Total", f"${sum(profits):.2f}")

# ==================== TAB 3: FASTLANE ====================
with tab3:
    st.markdown("### ⚡ FastLane MEV Protection - Atlas Protocol Integration")
    
    # FastLane Stats Section
    st.markdown("---")
    
    # Fetch FastLane stats
    fastlane_stats = None
    try:
        response = requests.get(f"{API_URL}/api/v1/fastlane/stats", headers={"X-API-Key": API_KEY}, timeout=5)
        if response.status_code == 200:
            fastlane_stats = response.json()
    except:
        pass
    
    # Top metrics row
    if fastlane_stats:
        stats_data = fastlane_stats.get("stats", {})
        shmon_data = fastlane_stats.get("shmon_integration", {})
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("🎯 MEV Opportunities", stats_data.get("total_mev_opportunities", 0))
        with m2:
            st.metric("💰 Total Captured", f"${stats_data.get('total_mev_captured_usd', 0):.2f}")
        with m3:
            st.metric("📊 24h Volume", f"${stats_data.get('last_24h_volume', 0):.2f}")
        with m4:
            st.metric("📈 APY Boost", shmon_data.get("estimated_apy_boost", "+0%"))
    else:
        st.warning("⚠️ FastLane stats unavailable - API might be offline")
    
    st.markdown("---")
    
    # Three columns layout
    col1, col2, col3 = st.columns(3)
    
    # Column 1: MEV Protection Calculator
    with col1:
        st.markdown("#### 🛡️ MEV Protection Calculator")
        
        swap_value = st.number_input("Swap Value (MON)", min_value=1.0, value=100.0, step=10.0, key="fl_swap")
        refund_percent = st.slider("Protocol Refund %", 0, 90, 10, key="fl_refund")
        
        if st.button("🔮 Calculate Savings", type="primary", use_container_width=True):
            try:
                response = requests.get(
                    f"{API_URL}/api/v1/fastlane/quote",
                    params={"swap_value": swap_value, "refund_percent": refund_percent},
                    headers={"X-API-Key": API_KEY},
                    timeout=5
                )
                
                if response.status_code == 200:
                    quote = response.json()
                    
                    st.success("✅ Quote received!")
                    
                    # Show results in a nice format
                    st.markdown(f"""
                    <div style="background: rgba(102, 126, 234, 0.1); border-radius: 10px; padding: 15px; margin: 10px 0;">
                        <h4 style="margin: 0 0 10px 0;">📊 Results</h4>
                        <table style="width: 100%;">
                            <tr><td>Swap Value</td><td><b>{quote.get('swap_value_mon', 0)} MON</b></td></tr>
                            <tr><td>Large Swap?</td><td>{'✅ Yes' if quote.get('is_large_swap') else '❌ No'}</td></tr>
                            <tr><td>MEV Rate</td><td>{quote.get('mev_rate_percent', 0):.2f}%</td></tr>
                            <tr><td>MEV Extraction</td><td>{quote.get('estimated_mev_extraction', 0):.6f} MON</td></tr>
                            <tr><td style="color: #4ecdc4;"><b>Your Savings</b></td><td style="color: #4ecdc4;"><b>{quote.get('user_savings_mon', 0):.6f} MON</b></td></tr>
                            <tr><td>Protocol Revenue</td><td>{quote.get('protocol_revenue_mon', 0):.6f} MON</td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info(f"💡 {quote.get('recommendation', '')}")
                else:
                    st.error("❌ Failed to get quote")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Column 2: MEV Simulation
    with col2:
        st.markdown("#### 🔬 MEV Simulation")
        
        sim_amount = st.number_input("Swap Amount (MON)", min_value=10.0, value=500.0, step=50.0, key="fl_sim")
        
        if st.button("🚀 Simulate MEV", type="secondary", use_container_width=True):
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/fastlane/simulate",
                    params={"swap_amount": sim_amount},
                    headers={"X-API-Key": API_KEY},
                    timeout=5
                )
                
                if response.status_code == 200:
                    sim = response.json().get("simulation", {})
                    mev = sim.get("extractable_mev", {})
                    protection = sim.get("with_protection", {})
                    
                    st.success(f"✅ Simulation: {sim.get('recommendation', 'STANDARD')}")
                    
                    # Extractable MEV
                    st.markdown("**📈 Extractable MEV:**")
                    st.markdown(f"""
                    - 🥪 Sandwich: `{mev.get('sandwich', 0):.4f}` MON
                    - 🏃 Backrun: `{mev.get('backrun', 0):.4f}` MON
                    - **Total: `{mev.get('total', 0):.4f}` MON**
                    """)
                    
                    # With Protection
                    st.markdown("**🛡️ With FastLane Protection:**")
                    st.markdown(f"""
                    - 👤 User Savings: `{protection.get('user_savings', 0):.4f}` MON (70%)
                    - 🏢 Protocol: `{protection.get('protocol_share', 0):.4f}` MON (20%)
                    - ✅ Validator: `{protection.get('validator_share', 0):.4f}` MON (10%)
                    """)
                else:
                    st.error("❌ Simulation failed")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        
        # Revenue Distribution Pie
        st.markdown("**💰 Revenue Distribution:**")
        st.markdown("""
        ```
        ┌─────────────────────────┐
        │   70% → shMON Holders   │
        │   20% → Brick3          │
        │   10% → Validators      │
        └─────────────────────────┘
        ```
        """)
    
    # Column 3: FastLane Info & Links
    with col3:
        st.markdown("#### 📋 FastLane Info")
        
        try:
            response = requests.get(f"{API_URL}/api/v1/fastlane/info", headers={"X-API-Key": API_KEY}, timeout=5)
            if response.status_code == 200:
                info = response.json()
                
                st.markdown(f"""
                **🔗 Protocol:** {info.get('protocol', 'Atlas')}
                
                **📜 Contracts:**
                """)
                
                contracts = info.get('contracts', {})
                atlas_router = contracts.get('atlas_router', 'N/A')
                st.code(atlas_router, language=None)
                st.caption(f"Chain ID: {contracts.get('chain_id', 'N/A')}")
                
                st.markdown("**✨ Features:**")
                for feature in info.get('features', []):
                    st.markdown(f"- {feature}")
                
                st.markdown("---")
                
                endpoints = info.get('endpoints', {})
                st.markdown("**🔗 Quick Links:**")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.link_button("📚 Docs", endpoints.get('docs', '#'), use_container_width=True)
                with col_b:
                    st.link_button("🥩 Stake", endpoints.get('stake', '#'), use_container_width=True)
        except:
            st.warning("⚠️ FastLane info unavailable")
        
        st.markdown("---")
        
        # shMONAD Section
        st.markdown("#### 🥩 shMONAD Staking")
        st.info("Stake MON → Get shMONAD → Earn MEV Rewards!")
        
        if fastlane_stats:
            revenue = fastlane_stats.get("shmon_integration", {}).get("revenue_share", {})
            st.markdown(f"""
            **Revenue Share:**
            - shMON Holders: **{revenue.get('shmon_holders', '70%')}**
            - Brick3: {revenue.get('brick3', '20%')}
            - Validators: {revenue.get('validators', '10%')}
            """)
        
        st.link_button("🚀 Go to shMONAD", "https://shmonad.xyz/", use_container_width=True, type="primary")
    
    # APY Calculator Section
    st.markdown("---")
    st.markdown("### 📊 APY Boost Calculator")
    
    apy_col1, apy_col2, apy_col3 = st.columns([1, 1, 2])
    
    with apy_col1:
        daily_mev = st.number_input("Daily MEV Volume ($)", min_value=1000.0, value=5000.0, step=1000.0, key="apy_mev")
    
    with apy_col2:
        tvl = st.number_input("TVL ($)", min_value=100000.0, value=1000000.0, step=100000.0, key="apy_tvl")
    
    with apy_col3:
        if st.button("📈 Calculate APY Boost", use_container_width=True):
            try:
                response = requests.get(
                    f"{API_URL}/api/v1/revenue/estimate-apy",
                    params={"daily_mev_volume_usd": daily_mev, "tvl_usd": tvl},
                    headers={"X-API-Key": API_KEY},
                    timeout=5
                )
                
                if response.status_code == 200:
                    estimate = response.json().get("estimate", {})
                    
                    r1, r2, r3 = st.columns(3)
                    with r1:
                        st.metric("Daily shMON Earnings", f"${estimate.get('daily_shmon_earnings_usd', 0):,.2f}")
                    with r2:
                        st.metric("Yearly Earnings", f"${estimate.get('yearly_shmon_earnings_usd', 0):,.2f}")
                    with r3:
                        apy_boost = estimate.get('estimated_apy_boost_percent', 0)
                        st.metric("APY Boost", f"+{apy_boost:.2f}%", delta=f"+{apy_boost:.2f}%")
                    
                    st.success(f"💡 {estimate.get('note', 'APY boost added to base staking rewards')}")
                else:
                    st.error("❌ Calculation failed")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ==================== TAB 4: API STATUS ====================
with tab4:
    st.markdown("### 🔌 API Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏥 Health Check")
        
        health = fetch_health()
        
        if health:
            st.success("✅ API Online")
            st.json(health)
        else:
            st.error("❌ API Offline")
            st.warning("Start API: `python3 monmev_api.py`")
    
    with col2:
        st.markdown("#### 📡 Endpoints")
        
        st.markdown("""
        | Endpoint | Description |
        |----------|-------------|
        | `GET /` | API Info |
        | `GET /health` | Health Check |
        | `GET /api/v1/opportunities` | MEV Opportunities |
        | `GET /api/v1/stats` | Statistics |
        | `GET /api/v1/bots/status` | Bot Status |
        | `POST /api/v1/bots/start/{type}` | Start Bot |
        | `GET /api/v1/fastlane/info` | FastLane Info |
        | `GET /api/v1/fastlane/quote` | MEV Quote |
        | `GET /api/v1/fastlane/stats` | FastLane Stats |
        | `POST /api/v1/fastlane/simulate` | MEV Simulation |
        | `GET /api/v1/revenue/summary` | Revenue Summary |
        | `GET /api/v1/revenue/estimate-apy` | APY Calculator |
        | `GET /api/v1/mainnet/status` | Mainnet Status |
        | `WS /ws/opportunities` | WebSocket |
        """)
    
    st.markdown("---")
    
    st.markdown("#### 🔑 Key Generator")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_key_name = st.text_input("Key Name", placeholder="MyNewKey")
    
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("🔑 Generate"):
            if new_key_name:
                try:
                    response = requests.get(
                        f"{API_URL}/api/v1/keys/generate",
                        params={"name": new_key_name},
                        timeout=5
                    )
                    if response.status_code == 200:
                        key_data = response.json()
                        st.success(f"✅ Key generated!")
                        st.code(key_data.get("api_key", ""))
                except:
                    st.error("❌ Failed to generate key")
            else:
                st.warning("Enter a key name")

# ==================== AUTO REFRESH ====================
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# ==================== FOOTER ====================
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #666;">🧱 <a href="https://www.brick3.fun/" target="_blank">brick3.fun</a> | Built for Monad</p>',
    unsafe_allow_html=True
)
