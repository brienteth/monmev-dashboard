# Real-time mempool monitoring and data streaming
import asyncio
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
import aiohttp

@dataclass
class MempoolTransaction:
    """Represents a transaction in the mempool"""
    hash: str
    from_address: str
    to_address: Optional[str]
    value: str
    gas_price: str
    gas_limit: int
    nonce: int
    timestamp: float
    mev_risk: str  # "high", "medium", "low"
    profit_opportunity: Optional[float]

class MempoolMonitor:
    """Real-time mempool monitoring with 100ms polling for 6x speed"""
    
    def __init__(self, rpc_endpoint: str = "https://rpc.monad.xyz", 
                 poll_interval_ms: int = 100):
        self.rpc_endpoint = rpc_endpoint
        self.poll_interval = poll_interval_ms / 1000.0  # Convert to seconds
        self.pending_transactions: Dict[str, MempoolTransaction] = {}
        self.callbacks: List[Callable] = []
        self.is_running = False
        
    async def start_streaming(self, callback: Optional[Callable] = None):
        """Start real-time mempool monitoring"""
        if callback:
            self.callbacks.append(callback)
        
        self.is_running = True
        print(f"🚀 Brick3 Mempool Monitor started (polling every {self.poll_interval_ms}ms)")
        
        while self.is_running:
            try:
                await self._poll_mempool()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                print(f"❌ Mempool polling error: {e}")
                await asyncio.sleep(1)
    
    async def _poll_mempool(self):
        """Poll mempool for pending transactions"""
        try:
            async with aiohttp.ClientSession() as session:
                # eth_pendingTransactions is a custom Monad RPC method
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_pendingTransactions",
                    "params": []
                }
                
                async with session.post(self.rpc_endpoint, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        await self._process_mempool_data(data.get("result", []))
        except Exception as e:
            print(f"Mempool polling failed: {e}")
    
    async def _process_mempool_data(self, transactions: List[Dict]):
        """Process mempool transactions and trigger callbacks"""
        for tx in transactions:
            tx_hash = tx.get("hash", "")
            
            if tx_hash not in self.pending_transactions:
                # New transaction detected
                mempool_tx = MempoolTransaction(
                    hash=tx_hash,
                    from_address=tx.get("from", ""),
                    to_address=tx.get("to"),
                    value=tx.get("value", "0"),
                    gas_price=tx.get("gasPrice", "0"),
                    gas_limit=int(tx.get("gas", 21000), 0),
                    nonce=int(tx.get("nonce", 0), 0),
                    timestamp=datetime.now().timestamp(),
                    mev_risk=self._calculate_mev_risk(tx),
                    profit_opportunity=self._calculate_profit(tx)
                )
                
                self.pending_transactions[tx_hash] = mempool_tx
                
                # Trigger callbacks
                for callback in self.callbacks:
                    await callback(mempool_tx)
    
    def _calculate_mev_risk(self, tx: Dict) -> str:
        """Estimate MEV risk for transaction"""
        gas_price = int(tx.get("gasPrice", "0"), 0)
        
        if gas_price > 1000e9:  # > 1000 Gwei
            return "high"
        elif gas_price > 100e9:  # > 100 Gwei
            return "medium"
        else:
            return "low"
    
    def _calculate_profit(self, tx: Dict) -> Optional[float]:
        """Calculate potential profit opportunity"""
        value = int(tx.get("value", "0"), 0)
        gas_price = int(tx.get("gasPrice", "0"), 0)
        
        if value > 1e18:  # > 1 MON
            return float(value) * (gas_price / 1e9) / 1e18
        return None
    
    async def stop(self):
        """Stop mempool monitoring"""
        self.is_running = False
        print("⏹️ Mempool Monitor stopped")
    
    def get_pending_transactions(self) -> List[MempoolTransaction]:
        """Get all pending transactions"""
        return list(self.pending_transactions.values())
    
    def clear_old_transactions(self, max_age_seconds: float = 300):
        """Remove transactions older than max_age"""
        current_time = datetime.now().timestamp()
        self.pending_transactions = {
            hash: tx for hash, tx in self.pending_transactions.items()
            if current_time - tx.timestamp < max_age_seconds
        }

class MempoolData:
    """Aggregated mempool data for agents"""
    
    def __init__(self, monitor: MempoolMonitor):
        self.monitor = monitor
    
    @property
    def pending_count(self) -> int:
        """Total pending transactions"""
        return len(self.monitor.pending_transactions)
    
    @property
    def high_risk_transactions(self) -> List[MempoolTransaction]:
        """High MEV-risk transactions"""
        return [tx for tx in self.monitor.get_pending_transactions() 
                if tx.mev_risk == "high"]
    
    @property
    def opportunities(self) -> List[MempoolTransaction]:
        """Profitable opportunity transactions"""
        return [tx for tx in self.monitor.get_pending_transactions() 
                if tx.profit_opportunity and tx.profit_opportunity > 0.1]
    
    def get_by_from_address(self, address: str) -> List[MempoolTransaction]:
        """Get transactions from specific address"""
        return [tx for tx in self.monitor.get_pending_transactions() 
                if tx.from_address.lower() == address.lower()]
    
    def get_by_to_address(self, address: str) -> List[MempoolTransaction]:
        """Get transactions to specific address"""
        return [tx for tx in self.monitor.get_pending_transactions() 
                if tx.to_address and tx.to_address.lower() == address.lower()]
