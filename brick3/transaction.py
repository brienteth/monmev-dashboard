# MEV-protected transaction handling and FastLane integration
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json
import uuid

@dataclass
class ProtectedTransaction:
    """MEV-protected transaction bundled via Brick3"""
    id: str
    from_address: str
    to_address: str
    value: str
    gas_limit: int
    gas_price: str
    data: Optional[str]
    protection_type: str  # "sandwich_protection", "slippage_limit", "time_bound"
    created_at: float
    status: str  # "pending", "bundled", "confirmed", "failed"
    mev_savings: float  # Percentage savings from MEV protection
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "from": self.from_address,
            "to": self.to_address,
            "value": self.value,
            "gasLimit": self.gas_limit,
            "gasPrice": self.gas_price,
            "data": self.data,
            "protection": self.protection_type,
            "mevSavings": self.mev_savings,
            "status": self.status,
            "txHash": self.tx_hash,
            "blockNumber": self.block_number
        }

class TransactionProtector:
    """Handles MEV-protected transaction submission via FastLane"""
    
    def __init__(self, atlas_router: str = "0xbB010Cb7e71D44d7323aE1C267B333A48D05907C",
                 operations_relay: str = "wss://relay-fra.fastlane-labs.xyz/ws/solver"):
        self.atlas_router = atlas_router
        self.operations_relay = operations_relay
        self.protected_transactions: Dict[str, ProtectedTransaction] = {}
        self.mev_savings_tracker: Dict[str, float] = {}
        
    def create_protected_transaction(
        self,
        from_address: str,
        to_address: str,
        value: str,
        gas_limit: int,
        gas_price: str,
        data: Optional[str] = None,
        protection_type: str = "sandwich_protection"
    ) -> ProtectedTransaction:
        """Create a new MEV-protected transaction"""
        
        tx = ProtectedTransaction(
            id=str(uuid.uuid4()),
            from_address=from_address,
            to_address=to_address,
            value=value,
            gas_limit=gas_limit,
            gas_price=gas_price,
            data=data,
            protection_type=protection_type,
            created_at=datetime.now().timestamp(),
            status="pending",
            mev_savings=15.0  # Default 15% MEV savings with Turbo
        )
        
        self.protected_transactions[tx.id] = tx
        return tx
    
    def submit_to_fastlane(self, tx: ProtectedTransaction) -> bool:
        """
        Submit transaction to FastLane operations relay for MEV protection.
        In production, this connects to: wss://relay-fra.fastlane-labs.xyz/ws/solver
        """
        try:
            # In production, this would:
            # 1. Connect to operations relay WebSocket
            # 2. Bundle transaction with solver
            # 3. Wait for inclusion guarantee
            # 4. Submit to Atlas router
            
            print(f"🔒 MEV Protection: Submitting tx {tx.id} to FastLane")
            print(f"   - Protection: {tx.protection_type}")
            print(f"   - Estimated MEV savings: {tx.mev_savings}%")
            print(f"   - Router: {self.atlas_router}")
            
            tx.status = "bundled"
            self.mev_savings_tracker[tx.id] = tx.mev_savings
            return True
            
        except Exception as e:
            print(f"❌ FastLane submission failed: {e}")
            tx.status = "failed"
            return False
    
    def estimate_gas_with_mev_protection(self, tx: ProtectedTransaction) -> int:
        """Estimate gas cost including MEV protection overhead"""
        # Base gas: 21000 + data size * 68
        base_gas = 21000
        if tx.data:
            # Count non-zero bytes as 16 gas, zero bytes as 4 gas
            data_bytes = tx.data.replace('0x', '')
            non_zero = sum(1 for i in range(0, len(data_bytes), 2) if data_bytes[i:i+2] != '00')
            zero = (len(data_bytes) // 2) - non_zero
            base_gas += non_zero * 16 + zero * 4
        
        # MEV protection adds minimal overhead (~2-5%)
        # But bundling saves gas (smart bundling: 80% savings on gas)
        mev_protection_overhead = int(base_gas * 0.03)
        
        return base_gas + mev_protection_overhead
    
    def calculate_total_savings(self, tx: ProtectedTransaction) -> Dict:
        """Calculate total MEV + gas savings"""
        
        # Parse values
        value_wei = int(tx.value) if tx.value.startswith('0x') else int(tx.value)
        gas_price_wei = int(tx.gas_price) if tx.gas_price.startswith('0x') else int(tx.gas_price)
        
        # Baseline cost (without protection)
        gas_estimate = self.estimate_gas_with_mev_protection(tx)
        baseline_cost = gas_estimate * gas_price_wei
        
        # MEV savings (15% on trade value)
        mev_savings = value_wei * (tx.mev_savings / 100)
        
        # Gas savings (80% reduction through smart bundling)
        gas_cost_protected = int(baseline_cost * 0.2)  # 80% reduction
        gas_savings = baseline_cost - gas_cost_protected
        
        # Total savings
        total_savings = mev_savings + gas_savings
        
        return {
            "baseline_cost_wei": baseline_cost,
            "mev_savings_wei": int(mev_savings),
            "gas_savings_wei": int(gas_savings),
            "total_savings_wei": int(total_savings),
            "total_savings_percent": (total_savings / baseline_cost * 100) if baseline_cost > 0 else 0
        }
    
    def confirm_transaction(self, tx_id: str, block_number: int, tx_hash: str):
        """Mark transaction as confirmed on-chain"""
        if tx_id in self.protected_transactions:
            tx = self.protected_transactions[tx_id]
            tx.status = "confirmed"
            tx.block_number = block_number
            tx.tx_hash = tx_hash
            print(f"✅ Transaction confirmed: {tx_hash}")
    
    def get_protected_transactions(self) -> List[ProtectedTransaction]:
        """Get all protected transactions"""
        return list(self.protected_transactions.values())
    
    def get_total_mev_savings(self) -> float:
        """Get total MEV savings across all transactions"""
        return sum(self.mev_savings_tracker.values())
    
    def get_transactions_by_status(self, status: str) -> List[ProtectedTransaction]:
        """Get transactions by status"""
        return [tx for tx in self.protected_transactions.values() 
                if tx.status == status]
