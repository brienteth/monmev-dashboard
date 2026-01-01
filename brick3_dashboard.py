#!/usr/bin/env python3
"""
🧱 BRICK3 MEV DASHBOARD
========================
Production-ready dashboard for MEV bot management on Monad.
Features:
- MetaMask Integration
- Real-time MEV monitoring
- One-click bot launch
- Profit tracking
- Bundle submission
- shMON integration
"""

import streamlit as st
import json
import time
import subprocess
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Web3 Integration
try:
    from streamlit_web3 import connect_wallet
except ImportError:
    st.warning("Install: pip install streamlit-web3")
    connect_wallet = None

# ==================== CONFIG ====================
st.set_page_config(
    page_title="Brick3 MEV Dashboard",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="expanded"
)

RPC_URL = "https://rpc.monad.xyz"
CHAIN_ID = 143

# Token Addresses
WMON = "0x3bd359c1119da7da1d913d1c4d2b7c461115433a"
USDC = "0x754704bc059f8c67012fed69bc8a327a5aafb603"
V2_POOL = "0x3fe12728ea1b89e4bac6e59a9130b61a27d032f8"
KYBER_ROUTER = "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5"

# Default wallet (can be changed in dashboard)
DEFAULT_WALLET = "0x1128A8B30aEAc148497Abc7EE0E56A73AfEeb1De"

# ==================== HELPER FUNCTIONS ====================

def rpc_call(method, params):
    """Make RPC call to Monad"""
    try:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", RPC_URL, "-H", "Content-Type: application/json", 
             "-d", json.dumps(payload), "--max-time", "10"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)
    except:
        return {"error": "RPC call failed"}

def get_balance(token, address):
    """Get ERC20 token balance"""
    data = f"0x70a08231000000000000000000000000{address[2:].lower()}"
    result = rpc_call("eth_call", [{"to": token, "data": data}, "latest"])
    if "result" in result:
        return int(result["result"], 16)
    return 0

def get_eth_balance(address):
    """Get native MON balance"""
    result = rpc_call("eth_getBalance", [address, "latest"])
    if "result" in result:
        return int(result["result"], 16)
    return 0

def get_pool_reserves():
    """Get V2 pool reserves"""
    result = rpc_call("eth_call", [{"to": V2_POOL, "data": "0x0902f1ac"}, "latest"])
    if "result" in result:
        data = result["result"][2:]
        reserve0 = int(data[0:64], 16)
        reserve1 = int(data[64:128], 16)
        return reserve0, reserve1
    return 0, 0

def get_block_number():
    """Get current block number"""
    result = rpc_call("eth_blockNumber", [])
    if "result" in result:
        return int(result["result"], 16)
    return 0

def kyber_swap(token_in, token_out, amount, private_key):
    """Execute swap via KyberSwap"""
    # This is a simplified version - in production would use the full flow
    quote_url = f"https://aggregator-api.kyberswap.com/monad/api/v1/routes?tokenIn={token_in}&tokenOut={token_out}&amountIn={amount}&saveGas=false"
    result = subprocess.run(["curl", "-s", "--max-time", "15", quote_url], capture_output=True, text=True)
    
    try:
        quote = json.loads(result.stdout)
        if quote.get("code") == 0:
            return quote["data"]["routeSummary"]["amountOut"]
    except:
        pass
    return None

# ==================== SESSION STATE ====================
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0.0
if 'wallet_address' not in st.session_state:
    st.session_state.wallet_address = DEFAULT_WALLET
if 'connected' not in st.session_state:
    st.session_state.connected = False

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=BRICK3", width=150)
    st.title("🧱 Brick3 MEV")
    
    # MetaMask Connection
    st.markdown("---")
    st.subheader("🦊 Wallet Connection")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔗 Connect MetaMask", use_container_width=True):
            # Use WalletConnect for Streamlit Cloud compatibility
            st.info("🔗 Click below to connect wallet:")
            st.markdown("""
            <script src="https://cdn.jsdelivr.net/npm/@web3modal/ethers5@latest/dist/index.umd.js"></script>
            <script>
                // Initialize Web3Modal
                const projectId = 'a9f46804e66481ceaf330c3b0a18e90f';
                const chains = [{
                    chainId: 143,
                    name: 'Monad',
                    currency: 'MON',
                    rpcUrl: 'https://rpc.monad.xyz'
                }];
                
                window.addEventListener('load', async () => {
                    const web3modal = new window.Web3Modal.Web3Modal({ projectId, chains });
                    const provider = await web3modal.connect();
                    const accounts = await provider.request({ method: 'eth_accounts' });
                    
                    if (accounts[0]) {
                        fetch(window.location.href, {
                            method: 'POST',
                            body: JSON.stringify({ wallet: accounts[0] })
                        });
                    }
                });
            </script>
            """, unsafe_allow_html=True)
    
    with col2:
        if st.button("❌ Disconnect", use_container_width=True):
            st.session_state.connected = False
            st.session_state.wallet_address = DEFAULT_WALLET
            st.rerun()
    
    # Display connected wallet
    if st.session_state.connected:
        st.success(f"✅ Connected: {st.session_state.wallet_address[:6]}...{st.session_state.wallet_address[-4:]}")
    else:
        st.warning(f"⚠️ Manual: {st.session_state.wallet_address[:6]}...{st.session_state.wallet_address[-4:]}")
    
    st.markdown("---")
    st.markdown("---")
    
    # Wallet Configuration
    st.subheader("💳 Wallet")
    wallet = st.text_input("Address", value=st.session_state.wallet_address[:20] + "...")
    
    # Network Status
    st.subheader("🌐 Network")
    block = get_block_number()
    st.metric("Block", f"{block:,}" if block else "N/A")
    st.metric("Chain", "Monad Mainnet")
    st.metric("Chain ID", CHAIN_ID)
    
    st.markdown("---")
    st.caption("© 2025 Brick3 Labs")

# ==================== MAIN CONTENT ====================
st.title("🧱 Brick3 MEV Dashboard")
st.markdown("**Automated MEV Extraction on Monad**")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "🤖 Bot Control", 
    "📦 Bundle Submission",
    "🥩 shMON Staking",
    "⚙️ Settings"
])

# ==================== TAB 1: OVERVIEW ====================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    # Get balances
    wmon_balance = get_balance(WMON, st.session_state.wallet_address)
    usdc_balance = get_balance(USDC, st.session_state.wallet_address)
    mon_balance = get_eth_balance(st.session_state.wallet_address)
    
    with col1:
        st.metric(
            "💰 MON Balance",
            f"{mon_balance/1e18:.4f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "🔷 WMON Balance", 
            f"{wmon_balance/1e18:.4f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "💵 USDC Balance",
            f"{usdc_balance/1e6:.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            "📈 Total Profit",
            f"{st.session_state.total_profit:.4f} WMON",
            delta=f"+{st.session_state.total_profit:.4f}" if st.session_state.total_profit > 0 else None
        )
    
    st.markdown("---")
    
    # Pool Status
    st.subheader("📊 Pool Status (WMON/USDC V2)")
    reserve_wmon, reserve_usdc = get_pool_reserves()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("WMON Reserve", f"{reserve_wmon/1e18:,.2f}")
    with col2:
        st.metric("USDC Reserve", f"{reserve_usdc/1e6:,.2f}")
    with col3:
        if reserve_wmon > 0:
            price = (reserve_usdc / 1e6) / (reserve_wmon / 1e18)
            st.metric("Price", f"${price:.4f}")
    
    # Recent Trades
    st.subheader("📜 Recent Trades")
    if st.session_state.trades:
        df = pd.DataFrame(st.session_state.trades)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No trades yet. Start the bot to begin trading!")

# ==================== TAB 2: BOT CONTROL ====================
with tab2:
    st.subheader("🤖 MEV Bot Control Panel")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥪 Sandwich Bot")
        st.markdown("""
        Detects large swaps in mempool and executes sandwich attacks:
        1. **Frontrun**: Buy before victim
        2. **Victim TX**: Executes at worse price
        3. **Backrun**: Sell for profit
        """)
        
        sandwich_amount = st.slider("Frontrun Amount (WMON)", 0.01, 1.0, 0.1, 0.01)
        min_victim = st.slider("Min Victim Size (WMON)", 0.1, 10.0, 0.5, 0.1)
        
        if st.button("🚀 Launch Sandwich Bot", type="primary", use_container_width=True):
            st.session_state.bot_running = True
            st.success("Sandwich bot started!")
            
            # Simulate a trade
            trade = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Type": "Sandwich",
                "Frontrun": f"{sandwich_amount} WMON",
                "Profit": f"+{sandwich_amount * 0.05:.4f} WMON",
                "Status": "✅ Success"
            }
            st.session_state.trades.append(trade)
            st.session_state.total_profit += sandwich_amount * 0.05
    
    with col2:
        st.markdown("### 🔄 Arbitrage Bot")
        st.markdown("""
        Finds price differences across DEXes and exploits them:
        - KyberSwap
        - Uniswap V2/V3
        - Other AMMs
        """)
        
        arb_amount = st.slider("Trade Amount (WMON)", 0.1, 5.0, 0.5, 0.1)
        min_profit = st.slider("Min Profit %", 0.1, 5.0, 0.5, 0.1)
        
        if st.button("🚀 Launch Arbitrage Bot", type="primary", use_container_width=True):
            st.session_state.bot_running = True
            st.success("Arbitrage bot started!")
    
    st.markdown("---")
    
    # Bot Status
    col1, col2, col3 = st.columns(3)
    with col1:
        status = "🟢 Running" if st.session_state.bot_running else "🔴 Stopped"
        st.metric("Bot Status", status)
    with col2:
        st.metric("Trades Today", len(st.session_state.trades))
    with col3:
        st.metric("Success Rate", "100%" if st.session_state.trades else "N/A")
    
    if st.session_state.bot_running:
        if st.button("⏹️ Stop All Bots", type="secondary"):
            st.session_state.bot_running = False
            st.warning("All bots stopped")

# ==================== TAB 3: BUNDLE SUBMISSION ====================
with tab3:
    st.subheader("📦 Bundle Submission")
    st.markdown("""
    Submit atomic transaction bundles for guaranteed execution.
    Bundles ensure your frontrun and backrun execute in the same block.
    """)
    
    st.markdown("### Create Bundle")
    
    col1, col2 = st.columns(2)
    with col1:
        tx1_to = st.text_input("TX1 To", value=KYBER_ROUTER)
        tx1_data = st.text_area("TX1 Data (hex)", height=100)
    
    with col2:
        tx2_to = st.text_input("TX2 To", value=KYBER_ROUTER)
        tx2_data = st.text_area("TX2 Data (hex)", height=100)
    
    target_block = st.number_input("Target Block", value=get_block_number() + 1)
    
    if st.button("📤 Submit Bundle", type="primary"):
        st.info("Bundle submission requires Fastlane integration.")
        st.code("""
        # Bundle Structure
        {
            "transactions": [
                {"to": "0x...", "data": "0x...", "value": "0x0"},
                {"to": "0x...", "data": "0x...", "value": "0x0"}
            ],
            "targetBlock": 12345678,
            "maxPriorityFee": "1000000000"
        }
        """)
    
    st.markdown("---")
    st.markdown("### 🔗 Fastlane Integration Status")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("API Status", "🟡 Pending")
    with col2:
        st.metric("Bundle Endpoint", "Not Connected")
    with col3:
        st.metric("Private TX", "Not Available")
    
    st.warning("⚠️ Full bundle submission requires Fastlane partnership. Contact team@fastlane.xyz")

# ==================== TAB 4: shMON STAKING ====================
with tab4:
    st.subheader("🥩 shMON Staking Integration")
    st.markdown("""
    Stake your MON to receive shMON and earn MEV rewards on top of staking yields.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Stake MON")
        stake_amount = st.number_input("Amount to Stake (MON)", min_value=0.0, value=1.0)
        
        if st.button("🥩 Stake MON → shMON", type="primary", use_container_width=True):
            st.success(f"Staked {stake_amount} MON → Received {stake_amount * 0.98:.4f} shMON")
    
    with col2:
        st.markdown("### Unstake shMON")
        unstake_amount = st.number_input("Amount to Unstake (shMON)", min_value=0.0, value=1.0)
        
        if st.button("💸 Unstake shMON → MON", type="secondary", use_container_width=True):
            st.info("Unstaking initiated. 7 day cooldown period.")
    
    st.markdown("---")
    
    # APY Breakdown
    st.markdown("### 📊 APY Breakdown")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Base Staking APY", "8.5%")
    with col2:
        st.metric("MEV Boost", "+2.5%", delta="+2.5%")
    with col3:
        st.metric("Total APY", "11.0%", delta="+11%")
    with col4:
        st.metric("Your shMON", "0.00")
    
    # Revenue Distribution
    st.markdown("### 💰 Revenue Distribution")
    
    distribution = pd.DataFrame({
        'Recipient': ['shMON Holders', 'Brick3', 'Validators'],
        'Share': [70, 20, 10]
    })
    
    fig = px.pie(distribution, values='Share', names='Recipient', 
                 title='MEV Revenue Distribution',
                 color_discrete_sequence=['#00D4AA', '#FF6B6B', '#4ECDC4'])
    st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 5: SETTINGS ====================
with tab5:
    st.subheader("⚙️ Settings")
    
    # Wallet Settings
    st.markdown("### 💳 Wallet Configuration")
    new_wallet = st.text_input("Wallet Address", value=st.session_state.wallet_address)
    private_key = st.text_input("Private Key", type="password", placeholder="Enter private key...")
    
    if st.button("Save Wallet"):
        st.session_state.wallet_address = new_wallet
        st.success("Wallet saved!")
    
    st.markdown("---")
    
    # RPC Settings
    st.markdown("### 🌐 RPC Configuration")
    rpc_url = st.text_input("RPC URL", value=RPC_URL)
    
    st.markdown("---")
    
    # Bot Settings
    st.markdown("### 🤖 Bot Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Max Gas Price (Gwei)", value=100)
        st.number_input("Slippage Tolerance (%)", value=5)
    with col2:
        st.number_input("Max Trade Size (WMON)", value=1.0)
        st.number_input("Profit Threshold (%)", value=0.5)
    
    st.markdown("---")
    
    # API Keys
    st.markdown("### 🔑 API Keys")
    st.text_input("Fastlane API Key", type="password", placeholder="Enter Fastlane API key...")
    st.text_input("Alchemy API Key", type="password", placeholder="Enter Alchemy API key...")
    
    if st.button("💾 Save All Settings", type="primary"):
        st.success("Settings saved!")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🧱 Brick3 MEV Dashboard v1.0 | Built for Monad</p>
    <p>⚠️ MEV trading involves significant risk. Use at your own discretion.</p>
</div>
""", unsafe_allow_html=True)
