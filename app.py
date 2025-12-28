"""
Brick3 MEV Discovery Dashboard
Monad Mainnet Real-time Mempool Monitoring
Version: 0.1 MVP
"""

import streamlit as st
from web3 import Web3
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import threading
import requests
import json

load_dotenv()

# ==================== CONFIG ====================
RPC_URL = os.getenv("MONAD_RPC", "https://testnet-rpc.monad.xyz")
API_URL = os.getenv("API_URL", "http://localhost:8000")
CHAIN_ID = 10143  # Monad testnet
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/"

# Web3 bağlantısı
try:
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 30}))
except Exception as e:
    w3 = None

# DEX Router adresleri (Monad için güncellenecek)
DEX_ROUTERS = {
    "uniswap_v2": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
    "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "kuru": "0x0000000000000000000000000000000000000000",
}

# Swap fonksiyon signature'ları
SWAP_SIGNATURES = [
    '0x38ed1739',  # swapExactTokensForTokens
    '0x7ff36ab5',  # swapExactETHForTokens
    '0x18cbafe5',  # swapExactTokensForETH
    '0x8803dbee',  # swapTokensForExactTokens
    '0xfb3bdb41',  # swapETHForExactTokens
    '0x4a25d94a',  # swapTokensForExactETH
    '0x5c11d795',  # swapExactTokensForTokensSupportingFeeOnTransferTokens
    '0xb6f9de95',  # swapExactETHForTokensSupportingFeeOnTransferTokens
    '0x791ac947',  # swapExactTokensForETHSupportingFeeOnTransferTokens
    '0xc04b8d59',  # exactInput (V3)
    '0xdb3e2198',  # exactInputSingle (V3)
    '0xf28c0498',  # exactOutput (V3)
    '0x414bf389',  # exactInputSingle (V3)
]

# ==================== SESSION STATE ====================
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False

# ==================== HELPER FUNCTIONS ====================

def sync_from_global():
    """Global değişkenlerden session_state'e senkronize et"""
    global _monitoring_data
    return {
        'opportunities': _monitoring_data['opportunities'].copy(),
        'last_block': _monitoring_data['last_block'],
        'total_profit': _monitoring_data['total_profit'],
        'stats': _monitoring_data['stats'].copy()
    }

def is_swap_transaction(tx):
    """Swap işlemi olup olmadığını kontrol et"""
    try:
        input_data = tx.get('input', '0x')
        if len(input_data) < 10:
            return False
        return any(input_data.startswith(sig) for sig in SWAP_SIGNATURES)
    except:
        return False

def is_large_swap(tx, threshold=5.0):
    """Büyük swap işlemlerini tespit et"""
    try:
        value_eth = float(w3.from_wei(tx.get('value', 0), 'ether'))
        if is_swap_transaction(tx) and value_eth > threshold:
            return True
        return False
    except:
        return False

def estimate_profit(tx):
    """
    Profit tahmini - basit hesaplama
    Production'da daha sofistike hesaplama gerekir:
    - Liquidity pool analizi
    - Price impact hesaplama
    - Gas cost optimization
    """
    try:
        value_eth = float(w3.from_wei(tx.get('value', 0), 'ether'))
        input_data = tx.get('input', '0x')
        
        # Swap işlemleri için profit tahmini
        if is_swap_transaction(tx):
            if value_eth > 100:
                # Çok büyük swap - yüksek slippage potansiyeli
                return round(value_eth * 0.008, 4)
            elif value_eth > 50:
                return round(value_eth * 0.006, 4)
            elif value_eth > 10:
                return round(value_eth * 0.004, 4)
            elif value_eth > 5:
                return round(value_eth * 0.003, 4)
            return 0
        
        # Büyük transferler
        if value_eth > 100:
            return round(value_eth * 0.001, 4)
        elif value_eth > 50:
            return round(value_eth * 0.0005, 4)
        
        return 0
    except:
        return 0

def classify_mev_type(tx):
    """MEV türünü detaylı sınıflandır"""
    try:
        input_data = tx.get('input', '0x')
        value_eth = float(w3.from_wei(tx.get('value', 0), 'ether'))
        to_address = tx.get('to', '')
        
        # Swap işlemi kontrolü
        if is_swap_transaction(tx):
            if value_eth > 10:
                return "🥪 Sandwich Potential"
            return "🔄 Swap"
        
        # Büyük transfer
        if value_eth > 50:
            return "🐋 Large Transfer"
        
        # Contract interaction
        if len(input_data) > 10:
            # Approve işlemi
            if input_data.startswith('0x095ea7b3'):
                return "✅ Token Approve"
            # Transfer
            if input_data.startswith('0xa9059cbb'):
                return "💸 Token Transfer"
            return "🔄 Contract Interaction"
        
        return "💸 Transfer"
    except:
        return "❓ Unknown"

def get_gas_info(tx):
    """Gas bilgilerini çıkar"""
    try:
        gas_price = tx.get('gasPrice', 0)
        max_fee = tx.get('maxFeePerGas', gas_price)
        gas_limit = tx.get('gas', 21000)
        
        gas_price_gwei = float(w3.from_wei(max_fee, 'gwei'))
        max_gas_cost = float(w3.from_wei(max_fee * gas_limit, 'ether'))
        
        return {
            'gas_price_gwei': round(gas_price_gwei, 2),
            'gas_limit': gas_limit,
            'max_gas_cost': round(max_gas_cost, 6)
        }
    except:
        return {'gas_price_gwei': 0, 'gas_limit': 0, 'max_gas_cost': 0}

def fetch_from_api(min_profit=0.01, limit=50):
    """API'den fırsatları çek"""
    try:
        headers = {"api-key": os.getenv("BRICK3_API_KEY", "demo_key_123")}
        params = {"min_profit": min_profit, "limit": limit}
        response = requests.get(
            f"{API_URL}/api/v1/opportunities",
            headers=headers,
            params=params,
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("opportunities", [])
    except:
        pass
    return []

def process_transaction(tx, block_number):
    """Transaction'ı işle ve opportunity oluştur"""
    global _monitoring_data
    
    try:
        value_eth = float(w3.from_wei(tx.value, 'ether'))
        
        # Sadece anlamlı tx'leri işle
        if value_eth < 0.1:
            return None
        
        profit = estimate_profit(tx)
        mev_type = classify_mev_type(tx)
        gas_info = get_gas_info(tx)
        
        # Stats güncelle
        if "Sandwich" in mev_type:
            _monitoring_data['stats']['sandwich'] += 1
        elif "Large" in mev_type:
            _monitoring_data['stats']['large_transfer'] += 1
        elif "Contract" in mev_type:
            _monitoring_data['stats']['contract'] += 1
        else:
            _monitoring_data['stats']['transfer'] += 1
        
        return {
            "hash": tx['hash'].hex(),
            "from": tx['from'],
            "to": tx['to'] if tx['to'] else "Contract Creation",
            "value_mon": round(value_eth, 4),
            "estimated_profit": profit,
            "mev_type": mev_type,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "block": block_number,
            "gas": gas_info,
            "nonce": tx.get('nonce', 0),
            "input_preview": tx.get('input', '0x')[:20] + "..." if len(tx.get('input', '0x')) > 20 else tx.get('input', '0x')
        }
    except Exception as e:
        return None

# Global variables for thread-safe monitoring
_monitoring_data = {
    'opportunities': [],
    'last_block': 0,
    'total_profit': 0.0,
    'stats': {'sandwich': 0, 'large_transfer': 0, 'contract': 0, 'transfer': 0},
    'active': False
}

def monitor_transactions():
    """Background transaction monitoring"""
    global _monitoring_data
    
    last_check_block = _monitoring_data['last_block']
    
    while _monitoring_data['active']:
        try:
            if not w3 or not w3.is_connected():
                time.sleep(5)
                continue
            
            current_block = w3.eth.block_number
            
            if current_block > last_check_block:
                # Son bloğu al
                try:
                    block = w3.eth.get_block(current_block, full_transactions=True)
                except:
                    time.sleep(2)
                    continue
                
                for tx in block.transactions:
                    opp = process_transaction(tx, current_block)
                    
                    if opp and opp['estimated_profit'] > 0:
                        _monitoring_data['opportunities'].insert(0, opp)
                        _monitoring_data['total_profit'] += opp['estimated_profit']
                        
                        # Son 200'ü tut
                        if len(_monitoring_data['opportunities']) > 200:
                            _monitoring_data['opportunities'] = _monitoring_data['opportunities'][:200]
                
                last_check_block = current_block
                _monitoring_data['last_block'] = current_block
                
        except Exception as e:
            print(f"Monitoring error: {e}")
        
        time.sleep(1)  # 1 saniye bekle

# ==================== STREAMLIT UI ====================

# Page config
st.set_page_config(
    page_title="Brick3 MEV Dashboard",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .stMetric {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .opportunity-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 10px;
    }
    .profit-positive {
        color: #00ff88;
        font-weight: bold;
    }
    .sandwich-alert {
        background-color: #ff6b6b20;
        border-left-color: #ff6b6b;
    }
    div[data-testid="stSidebar"] {
        background-color: #0e1117;
    }
    .fastlane-badge {
        background: linear-gradient(90deg, #00d4aa, #00a8cc);
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.8rem;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🧱 Brick3 MEV Discovery</p>', unsafe_allow_html=True)
st.caption("Monad Real-time MEV Monitoring Dashboard | v0.1 MVP | Powered by FastLane")

# Sidebar
with st.sidebar:
    st.image("https://www.fastlane.xyz/assets/ui-assets/images/fl-logo-dark.svg", width=120)
    st.markdown("---")
    
    # ==================== CONTROLS (EN ÜSTTE) ====================
    st.subheader("🎛️ Controls")
    
    if not st.session_state.monitoring_active:
        if st.button("🚀 Start Monitoring", use_container_width=True, type="primary"):
            st.session_state.monitoring_active = True
            _monitoring_data['active'] = True
            thread = threading.Thread(target=monitor_transactions, daemon=True)
            thread.start()
            st.rerun()
    else:
        if st.button("⏸️ Stop Monitoring", use_container_width=True):
            st.session_state.monitoring_active = False
            _monitoring_data['active'] = False
            st.rerun()
        st.success("🟢 Monitoring Active")
    
    # Clear data butonu
    if st.button("🗑️ Clear Data", use_container_width=True):
        _monitoring_data['opportunities'] = []
        _monitoring_data['total_profit'] = 0.0
        _monitoring_data['stats'] = {'sandwich': 0, 'large_transfer': 0, 'contract': 0, 'transfer': 0}
        st.rerun()
    
    st.divider()
    
    # ==================== FILTERS ====================
    st.subheader("🔍 Filters")
    min_profit = st.number_input("Min Profit (MON)", value=0.001, step=0.001, format="%.3f")
    min_value = st.number_input("Min Value (MON)", value=0.1, step=0.1, format="%.1f")
    mev_type_filter = st.selectbox(
        "MEV Type",
        ["All", "🥪 Sandwich Potential", "🐋 Large Transfer", "🔄 Contract Interaction", "💸 Transfer", "🔄 Swap"]
    )
    
    st.divider()
    
    # ==================== FASTLANE INTEGRATION ====================
    st.subheader("⚡ FastLane MEV Protection")
    
    fastlane_enabled = st.toggle("Enable FastLane", value=False)
    if fastlane_enabled:
        st.success("✅ FastLane Active")
        st.caption("MEV Protection via Atlas Protocol")
        
        refund_percent = st.slider("Refund %", 0, 90, 10)
        st.caption(f"MEV rebate: {refund_percent}%")
    else:
        st.info("Enable for MEV Protection")
    
    st.markdown("""
    <a href="https://shmonad.xyz/" target="_blank" style="text-decoration:none;">
        <div style="background:linear-gradient(90deg,#00d4aa,#00a8cc);padding:8px;border-radius:5px;text-align:center;color:white;font-weight:bold;">
            🔗 Stake shMONAD
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # ==================== SETTINGS (EN ALTTA) ====================
    st.subheader("⚙️ Settings")
    
    # RPC Status
    st.markdown("**🔗 Connection**")
    if w3 and w3.is_connected():
        st.success("✅ Monad RPC Connected")
        try:
            latest_block = w3.eth.block_number
            st.info(f"Block: #{latest_block:,}")
        except:
            st.warning("⚠️ Block fetch failed")
    else:
        st.error("❌ RPC Disconnected")
    
    st.caption(f"RPC: {RPC_URL[:30]}...")
    st.caption(f"Chain ID: {CHAIN_ID}")

# Senkronize et
data = sync_from_global()

# Main content
# Metrics row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "🔍 Opportunities",
        len(data['opportunities']),
        delta=f"+{len([o for o in data['opportunities'] if o['timestamp'] > (datetime.now().strftime('%H:%M'))][:10])}" if data['opportunities'] else None
    )

with col2:
    st.metric(
        "💰 Total Profit Found",
        f"{data['total_profit']:.4f} MON"
    )

with col3:
    st.metric(
        "🥪 Sandwich",
        data['stats']['sandwich']
    )

with col4:
    st.metric(
        "🐋 Large Transfers",
        data['stats']['large_transfer']
    )

with col5:
    st.metric(
        "📦 Last Block",
        f"#{data['last_block']:,}" if data['last_block'] > 0 else "N/A"
    )

st.divider()

# Filter opportunities
filtered_opps = [
    opp for opp in data['opportunities']
    if opp["estimated_profit"] >= min_profit
    and opp["value_mon"] >= min_value
    and (mev_type_filter == "All" or opp["mev_type"] == mev_type_filter)
]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Live Feed", "📈 Analytics", "⚡ FastLane", "🔧 API Status"])

with tab1:
    st.subheader(f"Live Opportunities ({len(filtered_opps)} found)")
    
    if filtered_opps:
        for i, opp in enumerate(filtered_opps[:50]):  # İlk 50'yi göster
            # Sandwich alert için özel stil
            card_class = "sandwich-alert" if "Sandwich" in opp['mev_type'] else ""
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
                with col1:
                    tx_link = f"{EXPLORER_URL}{opp['hash']}"
                    st.markdown(f"**[{opp['hash'][:12]}...{opp['hash'][-8:]}]({tx_link})**")
                    st.caption(f"Block #{opp['block']:,} • {opp['timestamp']}")
                
                with col2:
                    st.metric("Value", f"{opp['value_mon']:.4f} MON")
                
                with col3:
                    profit_pct = (opp['estimated_profit'] / opp['value_mon'] * 100) if opp['value_mon'] > 0 else 0
                    st.metric(
                        "Est. Profit",
                        f"{opp['estimated_profit']:.4f} MON",
                        delta=f"{profit_pct:.2f}%"
                    )
                
                with col4:
                    if "Sandwich" in opp['mev_type']:
                        st.error(opp['mev_type'])
                    elif "Large" in opp['mev_type']:
                        st.warning(opp['mev_type'])
                    else:
                        st.info(opp['mev_type'])
                
                with col5:
                    st.caption(f"⛽ {opp['gas']['gas_price_gwei']} Gwei")
                
                # Expanded details
                with st.expander("Details"):
                    dcol1, dcol2 = st.columns(2)
                    with dcol1:
                        st.code(f"From: {opp['from']}", language=None)
                        st.code(f"To: {opp['to']}", language=None)
                    with dcol2:
                        st.code(f"Nonce: {opp['nonce']}", language=None)
                        st.code(f"Input: {opp['input_preview']}", language=None)
                
                st.divider()
    else:
        if st.session_state.monitoring_active:
            st.info("🔍 Monitoring active... waiting for profitable opportunities")
            
            # Loading animation
            with st.spinner("Scanning blockchain..."):
                time.sleep(0.5)
        else:
            st.warning("⚠️ Monitoring stopped. Click 'Start Monitoring' in sidebar to begin.")

with tab2:
    st.subheader("📈 Analytics Dashboard")
    
    if data['opportunities']:
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # MEV Type distribution
            st.markdown("**MEV Type Distribution**")
            type_counts = {}
            for opp in data['opportunities']:
                t = opp['mev_type']
                type_counts[t] = type_counts.get(t, 0) + 1
            
            if type_counts:
                import pandas as pd
                df = pd.DataFrame(list(type_counts.items()), columns=['Type', 'Count'])
                st.bar_chart(df.set_index('Type'))
        
        with col2:
            # Profit distribution
            st.markdown("**Profit Over Time**")
            profits = [opp['estimated_profit'] for opp in data['opportunities'][:50]]
            if profits:
                import pandas as pd
                df = pd.DataFrame({'Profit (MON)': profits})
                st.line_chart(df)
        
        # Summary stats
        st.markdown("---")
        st.markdown("**Summary Statistics**")
        
        total_value = sum(opp['value_mon'] for opp in data['opportunities'])
        avg_profit = data['total_profit'] / len(data['opportunities']) if data['opportunities'] else 0
        
        scol1, scol2, scol3, scol4 = st.columns(4)
        scol1.metric("Total Value Monitored", f"{total_value:.2f} MON")
        scol2.metric("Average Profit", f"{avg_profit:.4f} MON")
        scol3.metric("Best Opportunity", f"{max(opp['estimated_profit'] for opp in data['opportunities']):.4f} MON" if data['opportunities'] else "N/A")
        scol4.metric("Transactions Analyzed", len(data['opportunities']))
    else:
        st.info("No data yet. Start monitoring to see analytics.")

with tab3:
    st.subheader("⚡ FastLane MEV Protection")
    
    st.markdown("""
    **FastLane** provides smart contract-based MEV protection powered by **Atlas Protocol**.
    Protect your swaps from sandwich attacks and capture MEV value for users.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🛡️ MEV Protection Calculator")
        
        calc_swap_value = st.number_input("Swap Value (MON)", value=100.0, min_value=0.1, step=10.0, key="fl_calc")
        calc_refund = st.slider("Protocol Refund %", 0, 90, 10, key="fl_refund")
        
        if calc_swap_value > 0:
            is_large = calc_swap_value > 10
            mev_rate = 0.008 if is_large else 0.003
            total_mev = calc_swap_value * mev_rate
            user_savings = total_mev * (1 - calc_refund / 100)
            protocol_rev = total_mev * (calc_refund / 100)
            
            st.markdown("---")
            mcol1, mcol2, mcol3 = st.columns(3)
            mcol1.metric("Estimated MEV", f"{total_mev:.4f} MON")
            mcol2.metric("User Savings", f"{user_savings:.4f} MON", delta=f"+{(user_savings/calc_swap_value*100):.2f}%")
            mcol3.metric("Protocol Revenue", f"{protocol_rev:.4f} MON")
            
            if total_mev > 0.01:
                st.success("✅ MEV Protection recommended for this swap!")
            else:
                st.info("ℹ️ MEV protection optional for small swaps")
    
    with col2:
        st.markdown("### 📋 Atlas Protocol Info")
        
        st.markdown("""
        **Features:**
        - 🔒 Smart contract-based protection
        - 💰 Better pricing via output token bidding
        - 📈 Revenue generation for dApps
        - 🌐 Multi-chain support
        """)
        
        st.code("""
Atlas Router: 0xbB010Cb7e71D44d7323aE1C267B333A48D05907C
Chain ID: 0x279f (Monad Testnet)
Auctioneer: auctioneer-fra.fastlane-labs.xyz
        """)
        
        st.markdown("### 🔗 Quick Links")
        link_col1, link_col2 = st.columns(2)
        with link_col1:
            st.link_button("📚 Documentation", "https://dev.shmonad.xyz/products/mev-protection", use_container_width=True)
            st.link_button("🏦 Stake shMONAD", "https://shmonad.xyz/", use_container_width=True)
        with link_col2:
            st.link_button("💬 Discord", "https://discord.fastlane.xyz/", use_container_width=True)
            st.link_button("🐦 Twitter", "https://x.com/0xFastLane", use_container_width=True)
    
    st.divider()
    
    # shMONAD Staking Section
    st.markdown("### 🏦 shMONAD Liquid Staking")
    
    shcol1, shcol2, shcol3 = st.columns(3)
    
    with shcol1:
        st.metric("Base Staking APY", "~8.0%")
    with shcol2:
        st.metric("MEV Boost APY", "~0.5%")
    with shcol3:
        st.metric("Total Est. APY", "~8.5%", delta="+MEV")
    
    st.markdown("""
    **Yield Channels:**
    - Staking rewards • MEV capture • Paymaster fees • Task Manager • FastLane RPC
    """)
    
    st.link_button("🚀 Stake Now at shmonad.xyz", "https://shmonad.xyz/", use_container_width=True, type="primary")

with tab4:
    st.subheader("🔧 API & System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Backend API**")
        try:
            response = requests.get(f"{API_URL}/", timeout=3)
            if response.status_code == 200:
                st.success("✅ API Connected")
                st.json(response.json())
            else:
                st.warning(f"⚠️ API returned {response.status_code}")
        except:
            st.error("❌ API Not Available")
            st.caption("Start the API with: `python api.py`")
    
    with col2:
        st.markdown("**Configuration**")
        st.code(f"""
RPC URL: {RPC_URL}
Chain ID: {CHAIN_ID}
Explorer: {EXPLORER_URL}
API URL: {API_URL}
        """)
        
        st.markdown("**Session Info**")
        st.code(f"""
Monitoring: {'Active' if st.session_state.monitoring_active else 'Stopped'}
Last Block: {data['last_block']}
Opportunities: {len(data['opportunities'])}
Total Profit: {data['total_profit']:.4f} MON
        """)

# Footer
st.divider()
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.caption("""
    **⚠️ Disclaimer:** Bu MVP read-only discovery dashboard'dur. Transaction execution özelliği yoktur.
    Production kullanımı için paid RPC ve güvenlik audit'i önerilir.
    """)
with col2:
    st.caption("[🌐 brick3.fun](https://www.brick3.fun/)")
with col3:
    st.caption("[📚 Documentation](https://github.com/)")

# Auto-refresh
if st.session_state.monitoring_active:
    time.sleep(3)
    st.rerun()
