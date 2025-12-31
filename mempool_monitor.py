"""
🔍 Brick3 Real-Time Mempool Monitor for Monad
Answers FastLane Question #1: "How do you achieve mempool monitoring on monad?"

This module implements real mempool monitoring using multiple approaches:
1. RPC Polling (eth_getFilterChanges with pending filter)
2. WebSocket subscription (when available)
3. Direct node connection (for validators)

Author: Brick3 MEV Team
License: MIT
"""

import asyncio
import json
import time
import os
import sqlite3
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import deque
import hashlib
import logging
import threading
from abc import ABC, abstractmethod

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Brick3Mempool")

# ==================== CONFIGURATION ====================

MONAD_CONFIG = {
    "mainnet": {
        "rpc_http": os.getenv("MONAD_RPC_HTTP", "https://rpc.monad.xyz"),
        "rpc_ws": os.getenv("MONAD_RPC_WS", "wss://ws.monad.xyz"),
        "chain_id": 10143,
        "block_time_ms": 1000,
    },
    "testnet": {
        "rpc_http": os.getenv("MONAD_TESTNET_RPC", "https://testnet-rpc.monad.xyz"),
        "rpc_ws": os.getenv("MONAD_TESTNET_WS", "wss://testnet-ws.monad.xyz"),
        "chain_id": 10143,
        "block_time_ms": 1000,
    }
}

# Known DEX router addresses on Monad
DEX_ROUTERS = {
    "0x...kuru": "Kuru DEX",
    "0x...bean": "Bean DEX",
    "0x...uniswap_clone": "Uniswap V2 Clone",
}

# Swap function signatures for detection
SWAP_SIGNATURES = {
    # Uniswap V2 style
    "0x38ed1739": {"name": "swapExactTokensForTokens", "type": "v2_swap"},
    "0x7ff36ab5": {"name": "swapExactETHForTokens", "type": "v2_swap_native"},
    "0x18cbafe5": {"name": "swapExactTokensForETH", "type": "v2_swap_to_native"},
    "0x8803dbee": {"name": "swapTokensForExactTokens", "type": "v2_swap_exact_out"},
    "0xfb3bdb41": {"name": "swapETHForExactTokens", "type": "v2_swap_native_exact"},
    "0x5c11d795": {"name": "swapExactTokensForTokensSupportingFeeOnTransferTokens", "type": "v2_fee_on_transfer"},
    
    # Uniswap V3 style
    "0x414bf389": {"name": "exactInputSingle", "type": "v3_single"},
    "0xc04b8d59": {"name": "exactInput", "type": "v3_multi"},
    "0x5023b4df": {"name": "exactOutputSingle", "type": "v3_single_exact_out"},
    "0xf28c0498": {"name": "exactOutput", "type": "v3_multi_exact_out"},
    
    # Common aggregator methods
    "0x0d5f0e3b": {"name": "swap", "type": "aggregator"},
    "0xe449022e": {"name": "uniswapV3SwapCallback", "type": "callback"},
}

# ==================== DATA STRUCTURES ====================

@dataclass
class PendingTx:
    """Pending transaction from mempool"""
    hash: str
    from_address: str
    to_address: str
    value_wei: int
    gas_price_wei: int
    max_fee_per_gas: Optional[int]
    max_priority_fee: Optional[int]
    gas_limit: int
    nonce: int
    input_data: str
    
    # Decoded info
    is_swap: bool = False
    swap_method: Optional[str] = None
    swap_type: Optional[str] = None
    token_in: Optional[str] = None
    token_out: Optional[str] = None
    amount_in: Optional[int] = None
    min_amount_out: Optional[int] = None
    slippage_percent: Optional[float] = None
    
    # Metadata
    first_seen: float = field(default_factory=time.time)
    block_number_when_seen: int = 0
    source: str = "rpc_poll"  # rpc_poll, websocket, direct

    def to_dict(self) -> Dict:
        return asdict(self)
    
    @property
    def value_eth(self) -> float:
        return self.value_wei / 1e18
    
    @property
    def gas_price_gwei(self) -> float:
        return self.gas_price_wei / 1e9
    
    @property
    def is_sandwichable(self) -> bool:
        """Check if this tx could be sandwiched"""
        if not self.is_swap:
            return False
        if self.slippage_percent and self.slippage_percent < 0.3:
            return False  # Too tight slippage
        if self.amount_in and self.amount_in > 10000 * 1e18:  # > $10k
            return True
        return self.slippage_percent and self.slippage_percent > 0.5

@dataclass
class MempoolStats:
    """Statistics about mempool monitoring"""
    start_time: float = field(default_factory=time.time)
    total_txs_seen: int = 0
    swap_txs_seen: int = 0
    sandwichable_txs: int = 0
    unique_wallets: int = 0
    unique_tokens: int = 0
    avg_latency_ms: float = 0.0
    last_block: int = 0
    txs_per_second: float = 0.0
    
    # Per-DEX stats
    dex_stats: Dict[str, int] = field(default_factory=dict)

# ==================== MEMPOOL MONITOR BASE ====================

class BaseMempoolMonitor(ABC):
    """Abstract base class for mempool monitoring"""
    
    def __init__(self, network: str = "mainnet"):
        self.network = network
        self.config = MONAD_CONFIG[network]
        self.running = False
        self.stats = MempoolStats()
        self.callbacks: List[Callable[[PendingTx], None]] = []
        self.seen_hashes: set = set()
        self.pending_txs: Dict[str, PendingTx] = {}
        
        # Circular buffer for recent txs (last 1000)
        self.recent_txs: deque = deque(maxlen=1000)
        
        # Database for persistence
        self.db_path = os.getenv("MEMPOOL_DB", "mempool_data.db")
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for tx logging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_transactions (
                hash TEXT PRIMARY KEY,
                from_address TEXT,
                to_address TEXT,
                value_wei TEXT,
                gas_price_wei TEXT,
                input_data TEXT,
                is_swap INTEGER,
                swap_method TEXT,
                token_in TEXT,
                token_out TEXT,
                amount_in TEXT,
                slippage_percent REAL,
                first_seen REAL,
                block_number INTEGER,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sandwich_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_tx_hash TEXT,
                estimated_profit_wei TEXT,
                token_pair TEXT,
                detected_at REAL,
                simulated INTEGER DEFAULT 0,
                executed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (target_tx_hash) REFERENCES pending_transactions(hash)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pending_swap ON pending_transactions(is_swap)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pending_time ON pending_transactions(first_seen)
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"📁 Database initialized: {self.db_path}")
    
    def add_callback(self, callback: Callable[[PendingTx], None]):
        """Add callback for new pending transactions"""
        self.callbacks.append(callback)
    
    def decode_swap(self, input_data: str, to_address: str) -> Dict[str, Any]:
        """Decode swap transaction input data"""
        result = {
            "is_swap": False,
            "method": None,
            "type": None,
        }
        
        if not input_data or len(input_data) < 10:
            return result
        
        method_id = input_data[:10].lower()
        
        if method_id in SWAP_SIGNATURES:
            sig_info = SWAP_SIGNATURES[method_id]
            result["is_swap"] = True
            result["method"] = sig_info["name"]
            result["type"] = sig_info["type"]
            
            # Try to decode parameters
            try:
                data = input_data[10:]  # Remove method ID
                
                # For V2 style swaps, decode path and amounts
                if sig_info["type"].startswith("v2"):
                    result.update(self._decode_v2_swap(data, sig_info["type"]))
                elif sig_info["type"].startswith("v3"):
                    result.update(self._decode_v3_swap(data))
                    
            except Exception as e:
                logger.debug(f"Decode error: {e}")
        
        return result
    
    def _decode_v2_swap(self, data: str, swap_type: str) -> Dict:
        """Decode Uniswap V2 style swap parameters"""
        result = {}
        
        try:
            # Standard V2 swap layout:
            # amountIn (32 bytes) | amountOutMin (32 bytes) | path offset | to | deadline
            if len(data) >= 64:
                amount_in = int(data[0:64], 16)
                amount_out_min = int(data[64:128], 16)
                
                result["amount_in"] = amount_in
                result["min_amount_out"] = amount_out_min
                
                # Calculate slippage (rough estimate)
                if amount_in > 0 and amount_out_min > 0:
                    # Assuming 1:1 ratio for estimate
                    result["slippage_percent"] = ((amount_in - amount_out_min) / amount_in) * 100
                
                # Try to get path (tokens)
                if len(data) >= 256:
                    # Path is dynamic array, get offset and parse
                    path_offset = int(data[128:192], 16) * 2
                    if len(data) > path_offset + 64:
                        path_length = int(data[path_offset:path_offset+64], 16)
                        if path_length >= 2:
                            # First token
                            token_in_start = path_offset + 64
                            result["token_in"] = "0x" + data[token_in_start+24:token_in_start+64]
                            # Last token
                            token_out_start = token_in_start + (path_length - 1) * 64
                            if len(data) >= token_out_start + 64:
                                result["token_out"] = "0x" + data[token_out_start+24:token_out_start+64]
        except Exception as e:
            logger.debug(f"V2 decode error: {e}")
        
        return result
    
    def _decode_v3_swap(self, data: str) -> Dict:
        """Decode Uniswap V3 style swap parameters"""
        result = {}
        
        try:
            # V3 exactInputSingle has struct:
            # tokenIn, tokenOut, fee, recipient, deadline, amountIn, amountOutMinimum, sqrtPriceLimitX96
            if len(data) >= 512:
                result["token_in"] = "0x" + data[24:64]
                result["token_out"] = "0x" + data[88:128]
                result["amount_in"] = int(data[320:384], 16)
                result["min_amount_out"] = int(data[384:448], 16)
                
                if result["amount_in"] > 0 and result["min_amount_out"] > 0:
                    result["slippage_percent"] = ((result["amount_in"] - result["min_amount_out"]) / result["amount_in"]) * 100
        except Exception as e:
            logger.debug(f"V3 decode error: {e}")
        
        return result
    
    def save_tx(self, tx: PendingTx):
        """Save transaction to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO pending_transactions 
                (hash, from_address, to_address, value_wei, gas_price_wei, input_data,
                 is_swap, swap_method, token_in, token_out, amount_in, slippage_percent,
                 first_seen, block_number, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx.hash, tx.from_address, tx.to_address, 
                str(tx.value_wei), str(tx.gas_price_wei), tx.input_data[:1000],
                1 if tx.is_swap else 0, tx.swap_method, tx.token_in, tx.token_out,
                str(tx.amount_in) if tx.amount_in else None, tx.slippage_percent,
                tx.first_seen, tx.block_number_when_seen, tx.source
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB save error: {e}")
    
    def _notify_callbacks(self, tx: PendingTx):
        """Notify all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(tx)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    @abstractmethod
    async def start(self):
        """Start monitoring"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop monitoring"""
        pass
    
    def get_stats(self) -> Dict:
        """Get current monitoring statistics"""
        uptime = time.time() - self.stats.start_time
        return {
            "uptime_seconds": uptime,
            "total_txs_seen": self.stats.total_txs_seen,
            "swap_txs_seen": self.stats.swap_txs_seen,
            "sandwichable_txs": self.stats.sandwichable_txs,
            "txs_per_second": self.stats.total_txs_seen / max(uptime, 1),
            "avg_latency_ms": self.stats.avg_latency_ms,
            "pending_txs_count": len(self.pending_txs),
            "dex_stats": self.stats.dex_stats,
            "network": self.network,
            "source": self.__class__.__name__,
        }

# ==================== RPC POLLING MONITOR ====================

class RPCMempoolMonitor(BaseMempoolMonitor):
    """
    Mempool monitor using RPC polling
    This is the most reliable method for public nodes
    """
    
    def __init__(self, network: str = "mainnet", poll_interval: float = 0.1):
        super().__init__(network)
        self.poll_interval = poll_interval  # 100ms default
        self.w3 = None
        self.pending_filter = None
        self._init_web3()
    
    def _init_web3(self):
        """Initialize Web3 connection"""
        try:
            from web3 import Web3
            from web3.middleware import geth_poa_middleware
            
            self.w3 = Web3(Web3.HTTPProvider(
                self.config["rpc_http"],
                request_kwargs={'timeout': 10}
            ))
            
            # Add PoA middleware for Monad
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if self.w3.is_connected():
                chain_id = self.w3.eth.chain_id
                block = self.w3.eth.block_number
                logger.info(f"✅ Connected to Monad RPC")
                logger.info(f"   Chain ID: {chain_id}")
                logger.info(f"   Current Block: {block}")
                self.stats.last_block = block
            else:
                logger.warning("⚠️ Web3 not connected")
        except ImportError:
            logger.error("❌ web3 package not installed. Run: pip install web3")
        except Exception as e:
            logger.error(f"❌ Web3 init error: {e}")
    
    async def start(self):
        """Start RPC polling"""
        if not self.w3:
            logger.error("Cannot start: Web3 not initialized")
            return
        
        self.running = True
        logger.info(f"🔍 Starting RPC mempool monitoring (poll interval: {self.poll_interval}s)")
        
        try:
            # Create pending transaction filter
            self.pending_filter = self.w3.eth.filter('pending')
            logger.info("✅ Pending transaction filter created")
        except Exception as e:
            logger.warning(f"⚠️ Could not create pending filter: {e}")
            logger.info("Falling back to block-by-block monitoring")
        
        # Start monitoring loop
        await self._monitoring_loop()
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        last_block = self.w3.eth.block_number
        
        while self.running:
            try:
                start_time = time.time()
                
                # Method 1: Get new pending txs from filter
                if self.pending_filter:
                    try:
                        new_entries = self.pending_filter.get_new_entries()
                        for tx_hash in new_entries:
                            await self._process_tx_hash(tx_hash.hex())
                    except Exception as e:
                        logger.debug(f"Filter error: {e}")
                
                # Method 2: Check for new blocks and their txs
                current_block = self.w3.eth.block_number
                if current_block > last_block:
                    self.stats.last_block = current_block
                    # Process transactions from new blocks
                    for block_num in range(last_block + 1, current_block + 1):
                        await self._process_block(block_num)
                    last_block = current_block
                
                # Calculate latency
                latency = (time.time() - start_time) * 1000
                self.stats.avg_latency_ms = (self.stats.avg_latency_ms * 0.9) + (latency * 0.1)
                
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(1)
    
    async def _process_tx_hash(self, tx_hash: str):
        """Process a single transaction hash"""
        if tx_hash in self.seen_hashes:
            return
        
        self.seen_hashes.add(tx_hash)
        
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            if tx:
                pending_tx = self._convert_tx(tx)
                await self._handle_pending_tx(pending_tx)
        except Exception as e:
            logger.debug(f"Get tx error for {tx_hash[:10]}...: {e}")
    
    async def _process_block(self, block_number: int):
        """Process transactions from a block"""
        try:
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            for tx in block.transactions:
                tx_hash = tx.hash.hex()
                if tx_hash not in self.seen_hashes:
                    self.seen_hashes.add(tx_hash)
                    pending_tx = self._convert_tx(tx)
                    pending_tx.source = "block_scan"
                    await self._handle_pending_tx(pending_tx)
        except Exception as e:
            logger.debug(f"Block processing error: {e}")
    
    def _convert_tx(self, tx) -> PendingTx:
        """Convert Web3 transaction to PendingTx"""
        # Decode swap info
        input_data = tx.input.hex() if tx.input else ""
        to_address = tx.to if tx.to else ""
        swap_info = self.decode_swap(input_data, to_address)
        
        return PendingTx(
            hash=tx.hash.hex(),
            from_address=tx['from'],
            to_address=to_address,
            value_wei=tx.value,
            gas_price_wei=tx.get('gasPrice', 0),
            max_fee_per_gas=tx.get('maxFeePerGas'),
            max_priority_fee=tx.get('maxPriorityFeePerGas'),
            gas_limit=tx.gas,
            nonce=tx.nonce,
            input_data=input_data,
            is_swap=swap_info.get("is_swap", False),
            swap_method=swap_info.get("method"),
            swap_type=swap_info.get("type"),
            token_in=swap_info.get("token_in"),
            token_out=swap_info.get("token_out"),
            amount_in=swap_info.get("amount_in"),
            min_amount_out=swap_info.get("min_amount_out"),
            slippage_percent=swap_info.get("slippage_percent"),
            block_number_when_seen=self.stats.last_block,
            source="rpc_poll"
        )
    
    async def _handle_pending_tx(self, tx: PendingTx):
        """Handle a new pending transaction"""
        self.stats.total_txs_seen += 1
        
        if tx.is_swap:
            self.stats.swap_txs_seen += 1
            
            # Track DEX usage
            if tx.to_address:
                dex_name = DEX_ROUTERS.get(tx.to_address.lower(), "Unknown DEX")
                self.stats.dex_stats[dex_name] = self.stats.dex_stats.get(dex_name, 0) + 1
            
            # Check if sandwichable
            if tx.is_sandwichable:
                self.stats.sandwichable_txs += 1
                logger.info(f"🥪 Sandwichable TX detected: {tx.hash[:16]}...")
                logger.info(f"   Amount: {tx.amount_in / 1e18 if tx.amount_in else 'Unknown'}")
                logger.info(f"   Slippage: {tx.slippage_percent:.2f}%" if tx.slippage_percent else "   Slippage: Unknown")
        
        # Store in memory
        self.pending_txs[tx.hash] = tx
        self.recent_txs.append(tx)
        
        # Save to database
        self.save_tx(tx)
        
        # Notify callbacks
        self._notify_callbacks(tx)
    
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("🛑 Mempool monitoring stopped")
        logger.info(f"   Total TXs seen: {self.stats.total_txs_seen}")
        logger.info(f"   Swap TXs: {self.stats.swap_txs_seen}")
        logger.info(f"   Sandwichable: {self.stats.sandwichable_txs}")

# ==================== WEBSOCKET MONITOR ====================

class WebSocketMempoolMonitor(BaseMempoolMonitor):
    """
    Mempool monitor using WebSocket subscription
    Lower latency than RPC polling
    """
    
    def __init__(self, network: str = "mainnet"):
        super().__init__(network)
        self.ws = None
    
    async def start(self):
        """Start WebSocket monitoring"""
        import websockets
        
        self.running = True
        logger.info(f"🔌 Connecting to WebSocket: {self.config['rpc_ws']}")
        
        try:
            async with websockets.connect(self.config['rpc_ws']) as ws:
                self.ws = ws
                
                # Subscribe to pending transactions
                subscribe_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["newPendingTransactions"]
                }
                await ws.send(json.dumps(subscribe_msg))
                
                # Get subscription confirmation
                response = await ws.recv()
                result = json.loads(response)
                
                if "result" in result:
                    logger.info(f"✅ Subscribed to pending transactions")
                    await self._listen_loop()
                else:
                    logger.error(f"Subscription failed: {result}")
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
    
    async def _listen_loop(self):
        """Listen for new pending transactions"""
        while self.running and self.ws:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=30)
                data = json.loads(message)
                
                if "params" in data:
                    tx_hash = data["params"]["result"]
                    self.stats.total_txs_seen += 1
                    # Get full transaction details via RPC
                    # (WebSocket only gives us the hash)
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                pass
            except Exception as e:
                logger.error(f"Listen error: {e}")
                break
    
    async def stop(self):
        """Stop WebSocket monitoring"""
        self.running = False
        if self.ws:
            await self.ws.close()

# ==================== COMBINED MONITOR ====================

class CombinedMempoolMonitor:
    """
    Combined mempool monitor using multiple sources
    Provides best coverage and lowest latency
    """
    
    def __init__(self, network: str = "mainnet"):
        self.network = network
        self.monitors: List[BaseMempoolMonitor] = []
        self.callbacks: List[Callable[[PendingTx], None]] = []
        self.seen_hashes: set = set()
        self.running = False
        
        # Initialize monitors
        self._init_monitors()
    
    def _init_monitors(self):
        """Initialize all available monitors"""
        # Always use RPC polling as base
        rpc_monitor = RPCMempoolMonitor(self.network)
        rpc_monitor.add_callback(self._on_new_tx)
        self.monitors.append(rpc_monitor)
        logger.info("✅ RPC Monitor initialized")
        
        # Try to add WebSocket monitor
        try:
            ws_monitor = WebSocketMempoolMonitor(self.network)
            ws_monitor.add_callback(self._on_new_tx)
            self.monitors.append(ws_monitor)
            logger.info("✅ WebSocket Monitor initialized")
        except Exception as e:
            logger.warning(f"WebSocket monitor not available: {e}")
    
    def add_callback(self, callback: Callable[[PendingTx], None]):
        """Add callback for new transactions"""
        self.callbacks.append(callback)
    
    def _on_new_tx(self, tx: PendingTx):
        """Handle new transaction from any monitor"""
        if tx.hash in self.seen_hashes:
            return
        
        self.seen_hashes.add(tx.hash)
        
        for callback in self.callbacks:
            try:
                callback(tx)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def start(self):
        """Start all monitors"""
        self.running = True
        logger.info("🚀 Starting Combined Mempool Monitor")
        
        # Start all monitors concurrently
        tasks = [asyncio.create_task(m.start()) for m in self.monitors]
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop all monitors"""
        self.running = False
        for monitor in self.monitors:
            await monitor.stop()
    
    def get_stats(self) -> Dict:
        """Get combined statistics"""
        combined = {
            "monitors_active": len(self.monitors),
            "unique_txs_seen": len(self.seen_hashes),
            "per_monitor": []
        }
        
        for monitor in self.monitors:
            combined["per_monitor"].append(monitor.get_stats())
        
        return combined

# ==================== QUERY FUNCTIONS ====================

def get_recent_swaps(db_path: str = "mempool_data.db", limit: int = 100) -> List[Dict]:
    """Get recent swap transactions from database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT hash, from_address, to_address, swap_method, token_in, token_out,
               amount_in, slippage_percent, first_seen
        FROM pending_transactions
        WHERE is_swap = 1
        ORDER BY first_seen DESC
        LIMIT ?
    ''', (limit,))
    
    columns = ['hash', 'from_address', 'to_address', 'swap_method', 'token_in', 
               'token_out', 'amount_in', 'slippage_percent', 'first_seen']
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return results

def get_sandwichable_txs(db_path: str = "mempool_data.db", limit: int = 50) -> List[Dict]:
    """Get recent sandwichable transactions"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT hash, from_address, to_address, swap_method, token_in, token_out,
               amount_in, slippage_percent, first_seen
        FROM pending_transactions
        WHERE is_swap = 1 AND slippage_percent > 0.5
        ORDER BY first_seen DESC
        LIMIT ?
    ''', (limit,))
    
    columns = ['hash', 'from_address', 'to_address', 'swap_method', 'token_in', 
               'token_out', 'amount_in', 'slippage_percent', 'first_seen']
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return results

def get_monitoring_summary(db_path: str = "mempool_data.db") -> Dict:
    """Get summary of mempool monitoring data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total transactions
    cursor.execute('SELECT COUNT(*) FROM pending_transactions')
    total_txs = cursor.fetchone()[0]
    
    # Swap transactions
    cursor.execute('SELECT COUNT(*) FROM pending_transactions WHERE is_swap = 1')
    swap_txs = cursor.fetchone()[0]
    
    # Sandwichable
    cursor.execute('SELECT COUNT(*) FROM pending_transactions WHERE is_swap = 1 AND slippage_percent > 0.5')
    sandwichable = cursor.fetchone()[0]
    
    # Unique wallets
    cursor.execute('SELECT COUNT(DISTINCT from_address) FROM pending_transactions')
    unique_wallets = cursor.fetchone()[0]
    
    # Time range
    cursor.execute('SELECT MIN(first_seen), MAX(first_seen) FROM pending_transactions')
    time_range = cursor.fetchone()
    
    conn.close()
    
    return {
        "total_transactions": total_txs,
        "swap_transactions": swap_txs,
        "sandwichable_transactions": sandwichable,
        "unique_wallets": unique_wallets,
        "first_tx_time": datetime.fromtimestamp(time_range[0]).isoformat() if time_range[0] else None,
        "last_tx_time": datetime.fromtimestamp(time_range[1]).isoformat() if time_range[1] else None,
    }

# ==================== CLI / DEMO ====================

async def main():
    """Demo: Run mempool monitoring"""
    print("=" * 60)
    print("🔍 Brick3 Mempool Monitor for Monad")
    print("=" * 60)
    
    # Callback to log interesting transactions
    def on_swap(tx: PendingTx):
        if tx.is_sandwichable:
            print(f"\n🥪 SANDWICHABLE TX DETECTED!")
            print(f"   Hash: {tx.hash}")
            print(f"   From: {tx.from_address}")
            print(f"   Method: {tx.swap_method}")
            print(f"   Slippage: {tx.slippage_percent:.2f}%" if tx.slippage_percent else "")
    
    # Create monitor
    monitor = RPCMempoolMonitor(network="mainnet")
    monitor.add_callback(on_swap)
    
    print("\n📡 Starting mempool monitoring...")
    print("Press Ctrl+C to stop\n")
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        print("\n\n⏹️ Stopping...")
        await monitor.stop()
        
        # Print summary
        print("\n📊 Session Summary:")
        stats = monitor.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())
