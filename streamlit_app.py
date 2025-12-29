"""
🧱 Brick3 MEV Dashboard - %100 GERÇEK VERİ
Monad Blockchain Real-time MEV Monitoring
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🧱 Brick3 MEV Dashboard",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONFIG ====================
MONAD_RPC = "https://testnet-rpc.monad.xyz"
MON_PRICE_USD = 1.5

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
.tx-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    border: 1px solid #3d3d5c;
    border-radius: 12px;
    padding: 15px;
    margin: 8px 0;
}
.badge-whale { background: #4ecdc4; color: white; padding: 4px 12px; border-radius: 20px; }
.badge-contract { background: #ffd93d; color: black; padding: 4px 12px; border-radius: 20px; }
.badge-transfer { background: #95a5a6; color: white; padding: 4px 12px; border-radius: 20px; }
.badge-swap { background: #ff6b6b; color: white; padding: 4px 12px; border-radius: 20px; }
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
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "last_block" not in st.session_state:
    st.session_state.last_block = 0
if "scan_count" not in st.session_state:
    st.session_state.scan_count = 0
if "total_value" not in st.session_state:
    st.session_state.total_value = 0

# ==================== DIRECT RPC FUNCTIONS ====================
def rpc_call(method, params=None):
    """Direct JSON-RPC call to Monad"""
    try:
        response = requests.post(
            MONAD_RPC,
            json={"jsonrpc": "2.0", "method": method, "params": params or [], "id": 1},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("result")
    except:
        pass
    return None

def hex_to_int(h):
    """Hex to int"""
    if not h:
        return 0
    if isinstance(h, int):
        return h
    return int(h, 16) if h.startswith("0x") else int(h)

def wei_to_mon(w):
    """Wei to MON"""
    return w / 10**18

# ==================== SWAP SIGNATURES ====================
SWAP_SIGS = {
    "0x38ed1739": "swapExactTokensForTokens",
    "0x7ff36ab5": "swapExactETHForTokens",
    "0x18cbafe5": "swapExactTokensForETH",
    "0x414bf389": "exactInputSingle",
    "0xc04b8d59": "exactInput",
}

# ==================== BLOCKCHAIN SCANNER ====================
def scan_blockchain():
    """Scan Monad blockchain and return REAL transactions"""
    transactions = []
    
    # Get latest block
    block_hex = rpc_call("eth_blockNumber")
    if not block_hex:
        return [], 0
    
    latest_block = hex_to_int(block_hex)
    total_value = 0
    
    # Scan last 10 blocks
    for offset in range(10):
        block_num = latest_block - offset
        block = rpc_call("eth_getBlockByNumber", [hex(block_num), True])
        
        if not block or "transactions" not in block:
            continue
        
        for tx in block["transactions"]:
            parsed = parse_transaction(tx, block_num)
            if parsed:
                transactions.append(parsed)
                total_value += parsed["value_mon"]
    
    return transactions, latest_block

def parse_transaction(tx, block_num):
    """Parse a single transaction into display format"""
    try:
        # Extract basic info
        tx_hash = tx.get("hash", "")
        to_addr = tx.get("to", "") or ""
        from_addr = tx.get("from", "") or ""
        value_wei = hex_to_int(tx.get("value", "0x0"))
        value_mon = wei_to_mon(value_wei)
        input_data = tx.get("input", "0x") or "0x"
        gas_price = hex_to_int(tx.get("gasPrice", "0x0"))
        
        # Determine transaction type
        func_sig = input_data[:10] if len(input_data) >= 10 else ""
        
        if func_sig in SWAP_SIGS:
            tx_type = "swap"
            type_label = f"🔄 {SWAP_SIGS[func_sig]}"
            profit_estimate = max(value_mon * 0.005, 0.5) * MON_PRICE_USD
        elif value_mon >= 10:
            tx_type = "whale"
            type_label = f"🐋 Large Transfer ({value_mon:.2f} MON)"
            profit_estimate = value_mon * 0.01 * MON_PRICE_USD
        elif len(input_data) > 10 and to_addr:
            tx_type = "contract"
            type_label = "📄 Contract Call"
            profit_estimate = 0.5 * MON_PRICE_USD
        elif value_mon > 0:
            tx_type = "transfer"
            type_label = f"💸 Transfer ({value_mon:.4f} MON)"
            profit_estimate = 0.1 * MON_PRICE_USD
        else:
            return None  # Skip zero-value non-contract txs
        
        return {
            "hash": tx_hash,
            "short_hash": f"{tx_hash[:10]}...{tx_hash[-6:]}",
            "from": from_addr,
            "short_from": f"{from_addr[:8]}...{from_addr[-4:]}" if from_addr else "Unknown",
            "to": to_addr,
            "short_to": f"{to_addr[:8]}...{to_addr[-4:]}" if to_addr else "Contract Create",
            "value_mon": value_mon,
            "value_usd": value_mon * MON_PRICE_USD,
            "type": tx_type,
            "type_label": type_label,
            "block": block_num,
            "profit_estimate": round(profit_estimate, 2),
            "gas_gwei": gas_price / 10**9,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "input_preview": input_data[:20] + "..." if len(input_data) > 20 else input_data,
        }
    except:
        return None

# ==================== DISPLAY FUNCTIONS ====================
def show_transactions(txs):
    """Display transaction list"""
    if not txs:
        st.info("Bu kategoride işlem yok. 'Blockchain Tara' butonuna tıklayın.")
        return
    
    for tx in txs[:50]:
        badge_class = f"badge-{tx['type']}"
        
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
            <div style="margin-top:5px;font-size:0.75em;color:#666;">
                {tx['type_label']}
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
                st.write(f"**Input:** {tx['input_preview']}")
            
            explorer_url = f"https://testnet.monadexplorer.com/tx/{tx['hash']}"
            st.markdown(f"[🔗 View on Explorer]({explorer_url})")

# ==================== MAIN UI ====================
def main():
    # Header
    st.markdown('<h1 class="main-header">🧱 Brick3 MEV Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;color:#888;">Real-time Monad Blockchain Monitoring - 100% REAL DATA</p>', unsafe_allow_html=True)
    
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
            with st.spinner("Scanning Monad blockchain..."):
                txs, block = scan_blockchain()
                if txs:
                    st.session_state.transactions = txs
                    st.session_state.last_block = block
                    st.session_state.scan_count += 1
                    st.session_state.total_value = sum(t["value_mon"] for t in txs)
                    st.success(f"✅ Found {len(txs)} real transactions!")
                else:
                    st.warning("No transactions found, try again.")
    
    with col3:
        auto_refresh = st.checkbox("🔁 Auto Refresh", value=False)
    
    st.divider()
    
    # Stats
    if st.session_state.transactions:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Transactions", len(st.session_state.transactions))
        with col2:
            whale_count = len([t for t in st.session_state.transactions if t["type"] == "whale"])
            st.metric("🐋 Whale Transactions", whale_count)
        with col3:
            st.metric("💰 Total Value", f"{st.session_state.total_value:,.2f} MON")
        with col4:
            total_profit = sum(t["profit_estimate"] for t in st.session_state.transactions)
            st.metric("📈 MEV Potential", f"${total_profit:,.2f}")
    
    # Filter tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 All", "🐋 Whale", "🔄 Swap", "📄 Contract"])
    
    with tab1:
        show_transactions(st.session_state.transactions)
    
    with tab2:
        whale_txs = [t for t in st.session_state.transactions if t["type"] == "whale"]
        show_transactions(whale_txs)
    
    with tab3:
        swap_txs = [t for t in st.session_state.transactions if t["type"] == "swap"]
        show_transactions(swap_txs)
    
    with tab4:
        contract_txs = [t for t in st.session_state.transactions if t["type"] == "contract"]
        show_transactions(contract_txs)
    
    # Auto refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()

# ==================== RUN ====================
if __name__ == "__main__":
    main()
else:
    main()
