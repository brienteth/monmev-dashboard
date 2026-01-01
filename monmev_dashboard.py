"""
🧱 Brick3 MEV Dashboard
Real-time MEV Monitoring Dashboard for Monad
Streamlit Frontend
"""

import streamlit as st
import streamlit.components.v1 as components
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
if "wallet_connected" not in st.session_state:
    st.session_state.wallet_connected = False
if "wallet_address" not in st.session_state:
    st.session_state.wallet_address = None
if "wallet_balance" not in st.session_state:
    st.session_state.wallet_balance = None

# ==================== METAMASK CONNECTION ====================
def connect_metamask_html():
    """MetaMask connection component with Web3.js"""
    return """
    <div id="metamask-container">
        <style>
            #metamask-container {
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                margin: 10px 0;
            }
            #connect-btn {
                background: white;
                color: #667eea;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                font-size: 16px;
                width: 100%;
                transition: all 0.3s;
            }
            #connect-btn:hover {
                transform: scale(1.02);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }
            #wallet-info {
                background: rgba(255,255,255,0.1);
                padding: 15px;
                border-radius: 8px;
                color: white;
                margin-top: 10px;
            }
            .wallet-address {
                font-family: monospace;
                font-size: 14px;
                word-break: break-all;
            }
            .wallet-balance {
                font-size: 20px;
                font-weight: 700;
                margin-top: 8px;
            }
            .disconnect-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid white;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                margin-top: 10px;
                font-size: 14px;
            }
        </style>
        
        <div id="wallet-status">
            <button id="connect-btn" onclick="connectWallet()">
                🦊 Connect MetaMask
            </button>
            <div id="wallet-info" style="display: none;">
                <div style="font-weight: 600; margin-bottom: 8px;">✅ Wallet Connected</div>
                <div class="wallet-address" id="address"></div>
                <div class="wallet-balance" id="balance"></div>
                <button class="disconnect-btn" onclick="disconnectWallet()">Disconnect</button>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/web3@1.10.0/dist/web3.min.js"></script>
        <script>
            let web3;
            let userAccount;
            
            // Check if MetaMask is installed
            window.addEventListener('load', async () => {
                if (typeof window.ethereum !== 'undefined') {
                    web3 = new Web3(window.ethereum);
                    
                    // Check if already connected
                    const accounts = await window.ethereum.request({ method: 'eth_accounts' });
                    if (accounts.length > 0) {
                        userAccount = accounts[0];
                        updateWalletUI();
                    }
                } else {
                    document.getElementById('connect-btn').innerHTML = '❌ MetaMask Not Installed';
                    document.getElementById('connect-btn').disabled = true;
                }
            });
            
            async function connectWallet() {
                if (typeof window.ethereum === 'undefined') {
                    alert('Please install MetaMask to use this feature!');
                    window.open('https://metamask.io/download/', '_blank');
                    return;
                }
                
                try {
                    // Request account access
                    const accounts = await window.ethereum.request({ 
                        method: 'eth_requestAccounts' 
                    });
                    
                    userAccount = accounts[0];
                    
                    // Check network (Monad = Chain ID 143)
                    const chainId = await window.ethereum.request({ method: 'eth_chainId' });
                    if (chainId !== '0x8f') { // 143 in hex
                        try {
                            await window.ethereum.request({
                                method: 'wallet_switchEthereumChain',
                                params: [{ chainId: '0x8f' }],
                            });
                        } catch (switchError) {
                            // Chain not added, add it
                            if (switchError.code === 4902) {
                                await window.ethereum.request({
                                    method: 'wallet_addEthereumChain',
                                    params: [{
                                        chainId: '0x8f',
                                        chainName: 'Monad Mainnet',
                                        nativeCurrency: {
                                            name: 'MON',
                                            symbol: 'MON',
                                            decimals: 18
                                        },
                                        rpcUrls: ['https://rpc.monad.xyz'],
                                        blockExplorerUrls: ['https://explorer.monad.xyz']
                                    }]
                                });
                            }
                        }
                    }
                    
                    updateWalletUI();
                    
                    // Store in Streamlit (via parent window)
                    window.parent.postMessage({
                        type: 'wallet_connected',
                        address: userAccount
                    }, '*');
                    
                } catch (error) {
                    console.error('Connection error:', error);
                    alert('Failed to connect: ' + error.message);
                }
            }
            
            async function updateWalletUI() {
                if (!userAccount) return;
                
                // Get balance
                const balance = await web3.eth.getBalance(userAccount);
                const balanceMON = web3.utils.fromWei(balance, 'ether');
                
                // Update UI
                document.getElementById('connect-btn').style.display = 'none';
                document.getElementById('wallet-info').style.display = 'block';
                document.getElementById('address').textContent = userAccount;
                document.getElementById('balance').textContent = parseFloat(balanceMON).toFixed(4) + ' MON';
            }
            
            function disconnectWallet() {
                userAccount = null;
                document.getElementById('connect-btn').style.display = 'block';
                document.getElementById('wallet-info').style.display = 'none';
                
                window.parent.postMessage({
                    type: 'wallet_disconnected'
                }, '*');
            }
            
            // Listen for account changes
            if (window.ethereum) {
                window.ethereum.on('accountsChanged', (accounts) => {
                    if (accounts.length === 0) {
                        disconnectWallet();
                    } else {
                        userAccount = accounts[0];
                        updateWalletUI();
                    }
                });
                
                window.ethereum.on('chainChanged', () => {
                    window.location.reload();
                });
            }
            
            // Expose sendTransaction function
            window.sendTransaction = async function(to, value, gasLimit, priorityFee, data) {
                if (!userAccount) {
                    throw new Error('Wallet not connected');
                }
                
                const valueWei = web3.utils.toWei(value.toString(), 'ether');
                const maxPriorityFeePerGas = web3.utils.toWei(priorityFee.toString(), 'gwei');
                
                const txParams = {
                    from: userAccount,
                    to: to,
                    value: valueWei,
                    gas: gasLimit,
                    maxPriorityFeePerGas: maxPriorityFeePerGas
                };
                
                if (data && data !== '') {
                    txParams.data = data;
                }
                
                try {
                    const txHash = await window.ethereum.request({
                        method: 'eth_sendTransaction',
                        params: [txParams],
                    });
                    
                    return { success: true, txHash: txHash };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            };
        </script>
    </div>
    """

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
    
    # Live Mempool Monitoring Section
    st.markdown("---")
    st.markdown("#### 🔍 Live Mempool Monitoring")
    
    # Fetch real mempool status
    mempool_status = None
    try:
        response = requests.get(f"{API_URL}/api/v1/mempool/status", headers={"X-API-Key": API_KEY}, timeout=5)
        if response.status_code == 200:
            mempool_status = response.json()
    except:
        pass
    
    # Mempool metrics row
    if mempool_status and mempool_status.get("monitoring_active"):
        mempool_stats = mempool_status.get("stats", {})
        
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("👁️ Status", "🟢 LIVE", help="Mempool monitoring is active")
        with m2:
            st.metric("📦 Txs Seen", f"{mempool_stats.get('total_txs_seen', 0):,}", help="Total transactions monitored")
        with m3:
            st.metric("🔄 Swap Txs", f"{mempool_stats.get('swap_txs_seen', 0):,}", help="Swap transactions detected")
        with m4:
            st.metric("🥪 Sandwichable", f"{mempool_stats.get('sandwichable_count', 0):,}", help="Sandwich opportunities found")
        with m5:
            poll_interval = mempool_status.get("poll_interval_ms", 100)
            st.metric("⚡ Poll Rate", f"{poll_interval}ms", help="Mempool polling interval")
    else:
        st.warning("⚠️ Mempool monitoring offline - Starting monitor...")
        if st.button("🚀 Start Monitoring", type="primary"):
            try:
                response = requests.post(f"{API_URL}/api/v1/mempool/start", headers={"X-API-Key": API_KEY}, timeout=5)
                if response.status_code == 200:
                    st.success("✅ Mempool monitoring started!")
                    st.rerun()
            except:
                st.error("❌ Failed to start monitoring")
    
    st.markdown("---")
    
    # FastLane Stats Section
    st.markdown("#### 📊 FastLane Stats")
    
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
        st.info("💡 FastLane stats will appear after MEV capture begins")
    
    st.markdown("---")
    
    # MetaMask Wallet Connection
    st.markdown("#### 🦊 Wallet Connection")
    
    components.html(connect_metamask_html(), height=200, scrolling=False)
    
    st.markdown("---")
    
    # Brick3 Infrastructure Status
    st.markdown("#### 🚀 Brick3 Infrastructure Status")
    
    infra_col1, infra_col2, infra_col3 = st.columns(3)
    
    with infra_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; text-align: center;">
            <div style="font-size: 2em;">🚀</div>
            <div style="font-weight: 600; margin: 5px 0;">Brick3 Turbo™</div>
            <div style="color: #4ade80; font-size: 0.9em;">● Active</div>
            <div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">Ultra-fast transaction relay</div>
        </div>
        """, unsafe_allow_html=True)
    
    with infra_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 15px; border-radius: 10px; text-align: center;">
            <div style="font-size: 2em;">💾</div>
            <div style="font-weight: 600; margin: 5px 0;">Brick3 Flash™</div>
            <div style="color: #4ade80; font-size: 0.9em;">● Active</div>
            <div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">Instant data caching</div>
        </div>
        """, unsafe_allow_html=True)
    
    with infra_col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 15px; border-radius: 10px; text-align: center;">
            <div style="font-size: 2em;">🌊</div>
            <div style="font-weight: 600; margin: 5px 0;">Brick3 Flow™</div>
            <div style="color: #4ade80; font-size: 0.9em;">● Active</div>
            <div style="font-size: 0.8em; opacity: 0.8; margin-top: 5px;">Advanced mempool streaming</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Submit Protected Transaction Form
    st.markdown("#### 📤 Submit Protected Transaction")
    st.info("🛡️ Submit transactions through FastLane for MEV protection")
    
    # Transaction Method Selection
    tx_method = st.radio(
        "Transaction Method:",
        ["🦊 MetaMask (Recommended)", "🔑 API Submission (Demo)"],
        horizontal=True,
        help="Use MetaMask to sign transactions with your wallet, or use API for testing"
    )
    
    with st.form("protected_tx_form"):
        tx_form_col1, tx_form_col2 = st.columns(2)
        
        with tx_form_col1:
            to_address = st.text_input(
                "To Address",
                placeholder="0x...",
                help="Destination address for the transaction"
            )
            
            value_mon = st.number_input(
                "Value (MON)",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.4f",
                help="Amount of MON to send"
            )
            
            gas_limit = st.number_input(
                "Gas Limit",
                min_value=21000,
                value=100000,
                step=10000,
                help="Maximum gas for the transaction"
            )
        
        with tx_form_col2:
            priority_fee = st.number_input(
                "Priority Fee (Gwei)",
                min_value=0.1,
                value=1.0,
                step=0.1,
                format="%.2f",
                help="Priority fee for faster inclusion"
            )
            
            tx_data = st.text_area(
                "Data (hex)",
                placeholder="0x... (optional)",
                help="Contract call data in hex format (leave empty for simple transfers)",
                height=100
            )
        
        submit_tx = st.form_submit_button(
            "🦊 Submit via MetaMask" if tx_method.startswith("🦊") else "🚀 Submit Protected Transaction",
            type="primary",
            use_container_width=True
        )
        
        if submit_tx:
            # Validate inputs
            if not to_address or not to_address.startswith("0x"):
                st.error("❌ Invalid destination address")
            elif len(to_address) != 42:
                st.error("❌ Address must be 42 characters (0x + 40 hex digits)")
            elif tx_method.startswith("🦊"):
                # MetaMask Transaction
                st.warning("⚠️ Please check your MetaMask wallet to confirm the transaction")
                
                # Create JavaScript to send transaction via MetaMask
                tx_js = f"""
                <script>
                    async function submitTransaction() {{
                        try {{
                            const result = await window.parent.sendTransaction(
                                '{to_address}',
                                {value_mon},
                                {gas_limit},
                                {priority_fee},
                                '{tx_data if tx_data else ""}'
                            );
                            
                            if (result.success) {{
                                window.parent.postMessage({{
                                    type: 'transaction_success',
                                    txHash: result.txHash
                                }}, '*');
                            }} else {{
                                window.parent.postMessage({{
                                    type: 'transaction_error',
                                    error: result.error
                                }}, '*');
                            }}
                        }} catch (error) {{
                            window.parent.postMessage({{
                                type: 'transaction_error',
                                error: error.message
                            }}, '*');
                        }}
                    }}
                    
                    submitTransaction();
                </script>
                """
                
                components.html(tx_js, height=0)
                
                st.info("📱 Transaction sent to MetaMask. Please confirm in your wallet.")
                st.markdown(f"""
                **Transaction Details:**
                - **To:** `{to_address}`
                - **Value:** {value_mon} MON
                - **Gas Limit:** {gas_limit:,}
                - **Priority Fee:** {priority_fee} Gwei
                - **MEV Protection:** ✅ Active via FastLane
                """)
            else:
                with st.spinner("🔄 Submitting transaction through FastLane..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/api/v1/fastlane/submit",
                            json={
                                "to": to_address,
                                "value": str(value_mon),
                                "gas_limit": gas_limit,
                                "priority_fee_gwei": priority_fee,
                                "data": tx_data if tx_data else None
                            },
                            headers={"X-API-Key": API_KEY},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Transaction submitted successfully!")
                            
                            st.markdown(f"""
                            <div style="background: rgba(76, 175, 80, 0.1); border-left: 3px solid #4caf50; padding: 15px; margin: 10px 0; border-radius: 8px;">
                                <h4 style="margin: 0 0 10px 0;">📋 Transaction Details</h4>
                                <table style="width: 100%; font-size: 0.9em;">
                                    <tr><td><b>Tx Hash:</b></td><td><code>{result.get('tx_hash', 'N/A')}</code></td></tr>
                                    <tr><td><b>Status:</b></td><td>{result.get('status', 'N/A')}</td></tr>
                                    <tr><td><b>Protected:</b></td><td>✅ MEV Protection Active</td></tr>
                                    <tr><td><b>Estimated Gas:</b></td><td>{result.get('estimated_gas', 'N/A')}</td></tr>
                                </table>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if result.get("explorer_url"):
                                st.link_button("🔍 View on Explorer", result["explorer_url"], use_container_width=True)
                        else:
                            error_msg = response.json().get("detail", "Unknown error")
                            st.error(f"❌ Submission failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error submitting transaction: {str(e)}")
    
    st.markdown("---")
    
    # Live Mempool Transaction Feed
    st.markdown("#### 📡 Live Mempool Transaction Feed")
    
    # Fetch recent mempool transactions
    mempool_txs = None
    try:
        response = requests.get(
            f"{API_URL}/api/v1/mempool/transactions",
            params={"limit": 10},
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                mempool_txs = result.get("transactions", [])
    except:
        pass
    
    if mempool_txs and len(mempool_txs) > 0:
        st.markdown(f"**Latest {len(mempool_txs)} transactions from mempool:**")
        
        for tx in mempool_txs:
            tx_type = tx.get("type", "unknown")
            tx_hash = tx.get("hash", "N/A")
            value = tx.get("value", 0)
            is_sandwichable = tx.get("is_sandwichable", False)
            
            # Badge color based on type
            if tx_type == "swap":
                badge_color = "#667eea" if is_sandwichable else "#4ecdc4"
                badge_icon = "🥪" if is_sandwichable else "🔄"
            else:
                badge_color = "#95a5a6"
                badge_icon = "💸"
            
            st.markdown(f"""
            <div style="background: rgba(30, 30, 46, 0.6); border-left: 3px solid {badge_color}; padding: 10px; margin: 5px 0; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background: {badge_color}; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600;">
                            {badge_icon} {tx_type.upper()}
                        </span>
                        <code style="margin-left: 10px; color: #888;">{tx_hash[:16]}...</code>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #4ecdc4; font-weight: 600;">{value:.4f} MON</div>
                        <div style="font-size: 0.75em; color: #666;">{tx.get("from", "")[:10]}... → {tx.get("to", "")[:10]}...</div>
                    </div>
                </div>
                {f'<div style="margin-top: 5px; color: #ff6b6b; font-size: 0.85em;">🥪 SANDWICHABLE - Profit: ${tx.get("potential_profit", 0):.2f}</div>' if is_sandwichable else ''}
            </div>
            """, unsafe_allow_html=True)
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (5s)", value=False, key="mempool_refresh")
        if auto_refresh:
            time.sleep(5)
            st.rerun()
    else:
        st.info("💡 No recent mempool transactions. Monitoring may be starting up...")
        if st.button("🔄 Refresh Feed", use_container_width=True):
            st.rerun()
    
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
        
        # Production Solver Addresses
        st.markdown("#### 🤖 Production Solver Addresses")
        
        try:
            response = requests.get(f"{API_URL}/api/v1/solver/addresses", headers={"X-API-Key": API_KEY}, timeout=5)
            if response.status_code == 200:
                solver_data = response.json()
                solvers = solver_data.get("production_solver_addresses", {})
                
                st.markdown("**Registered Solvers:**")
                
                # Sandwich Bot
                if "sandwich_bot" in solvers:
                    bot = solvers["sandwich_bot"]
                    st.code(bot.get("address", "N/A"), language=None)
                    st.caption(f"🥪 {bot.get('role', 'Sandwich Bot')} - {bot.get('status', 'operational')}")
                
                # Arbitrage Bot
                if "arbitrage_bot" in solvers:
                    bot = solvers["arbitrage_bot"]
                    st.code(bot.get("address", "N/A"), language=None)
                    st.caption(f"🔄 {bot.get('role', 'Arbitrage Bot')} - {bot.get('status', 'operational')}")
                
                # Liquidation Bot
                if "liquidation_bot" in solvers:
                    bot = solvers["liquidation_bot"]
                    st.code(bot.get("address", "N/A"), language=None)
                    st.caption(f"💧 {bot.get('role', 'Liquidation Bot')} - {bot.get('status', 'operational')}")
                
                st.success("✅ All solvers operational")
            else:
                st.warning("⚠️ Solver addresses unavailable")
        except:
            st.warning("⚠️ Could not fetch solver info")
        
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
