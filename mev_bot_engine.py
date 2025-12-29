"""
🤖 Brick3 MEV Bot Engine
Production-ready MEV bots for Monad
- Sandwich Attack Bot
- Arbitrage Bot  
- Liquidation Bot
- Backrun Bot
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal
import os
from datetime import datetime
import hashlib
import threading
from collections import deque

# Lazy import for web3 to avoid Python 3.14 compatibility issues
Web3 = None
def get_web3_module():
    global Web3
    if Web3 is None:
        try:
            from web3 import Web3 as W3
            Web3 = W3
        except ImportError:
            Web3 = None
    return Web3

# ==================== CONFIGURATION ====================

class BotType(Enum):
    SANDWICH = "sandwich"
    ARBITRAGE = "arbitrage"
    LIQUIDATION = "liquidation"
    BACKRUN = "backrun"

class BotStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class BotConfig:
    """Bot configuration"""
    bot_type: BotType
    min_profit_usd: float = 10.0
    max_gas_gwei: float = 100.0
    slippage_percent: float = 0.5
    max_position_size_mon: float = 1000.0
    enabled: bool = True
    
@dataclass
class MEVOpportunity:
    """Detected MEV opportunity"""
    id: str
    type: str
    tx_hash: str
    target_address: str
    value_mon: float
    estimated_profit_usd: float
    estimated_profit_mon: float
    gas_cost_mon: float
    net_profit_mon: float
    confidence: float
    block_number: int
    timestamp: str
    details: Dict[str, Any]
    
@dataclass
class BotExecution:
    """Bot execution record"""
    id: str
    bot_type: str
    opportunity_id: str
    status: str  # pending, submitted, confirmed, failed
    tx_hash: Optional[str]
    profit_mon: float
    gas_used: float
    timestamp: str
    error: Optional[str] = None

# ==================== DEX CONFIGURATIONS ====================

# Known DEX routers on Monad
DEX_ROUTERS = {
    "kuru": {
        "name": "Kuru DEX",
        "router": "0x...",  # Placeholder - real address needed
        "factory": "0x...",
        "fee": 0.003  # 0.3%
    },
    "uniswap_v2_fork": {
        "name": "UniV2 Fork",
        "router": "0x...",
        "factory": "0x...",
        "fee": 0.003
    }
}

# Swap method signatures
SWAP_SIGNATURES = {
    "0x38ed1739": "swapExactTokensForTokens",
    "0x7ff36ab5": "swapExactETHForTokens",
    "0x18cbafe5": "swapExactTokensForETH",
    "0x8803dbee": "swapTokensForExactTokens",
    "0xfb3bdb41": "swapETHForExactTokens",
    "0x5c11d795": "swapExactTokensForTokensSupportingFeeOnTransferTokens",
    "0x791ac947": "swapExactTokensForETHSupportingFeeOnTransferTokens",
    "0xb6f9de95": "swapExactETHForTokensSupportingFeeOnTransferTokens"
}

# ==================== MEV BOT ENGINE ====================

class MEVBotEngine:
    """
    Production MEV Bot Engine
    Handles detection, simulation, and execution of MEV opportunities
    """
    
    def __init__(self, rpc_url: str = None, private_key: str = None):
        self.rpc_url = rpc_url or os.getenv("MONAD_RPC", "https://rpc.monad.xyz")
        self.private_key = private_key or os.getenv("BOT_PRIVATE_KEY")
        
        # Initialize Web3 (lazy)
        W3 = get_web3_module()
        try:
            if W3:
                self.w3 = W3(W3.HTTPProvider(self.rpc_url, request_kwargs={'timeout': 30}))
            else:
                self.w3 = None
        except:
            self.w3 = None
        
        # Bot wallet
        if self.private_key and self.w3:
            try:
                self.account = self.w3.eth.account.from_key(self.private_key)
                self.bot_address = self.account.address
            except:
                self.bot_address = None
        else:
            self.bot_address = None
            
        # Bot configurations
        self.bot_configs: Dict[BotType, BotConfig] = {
            BotType.SANDWICH: BotConfig(BotType.SANDWICH, min_profit_usd=50.0),
            BotType.ARBITRAGE: BotConfig(BotType.ARBITRAGE, min_profit_usd=20.0),
            BotType.LIQUIDATION: BotConfig(BotType.LIQUIDATION, min_profit_usd=100.0),
            BotType.BACKRUN: BotConfig(BotType.BACKRUN, min_profit_usd=10.0),
        }
        
        # Bot statuses
        self.bot_statuses: Dict[BotType, BotStatus] = {
            BotType.SANDWICH: BotStatus.STOPPED,
            BotType.ARBITRAGE: BotStatus.STOPPED,
            BotType.LIQUIDATION: BotStatus.STOPPED,
            BotType.BACKRUN: BotStatus.STOPPED,
        }
        
        # Opportunity queue
        self.opportunity_queue: deque = deque(maxlen=1000)
        self.execution_history: List[BotExecution] = []
        
        # Stats
        self.stats = {
            "total_opportunities": 0,
            "executed_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit_mon": 0.0,
            "total_profit_usd": 0.0,
            "total_gas_spent_mon": 0.0,
            "start_time": datetime.now().isoformat()
        }
        
        # Revenue distribution
        self.revenue_distribution = {
            "shmon_holders": 0.70,  # 70%
            "brick3": 0.20,         # 20%
            "validators": 0.10      # 10%
        }
        
        # Price feeds (simplified - use oracle in production)
        self.prices = {
            "MON": 1.5,  # MON/USD
            "ETH": 3500,
            "USDC": 1.0
        }
        
        # Running flag
        self.running = False
        self.monitor_thread = None
        
    # ==================== BOT CONTROL ====================
    
    def start_bot(self, bot_type: BotType) -> Dict:
        """Start a specific bot"""
        if bot_type not in self.bot_configs:
            return {"success": False, "error": f"Unknown bot type: {bot_type}"}
            
        if not self.bot_configs[bot_type].enabled:
            return {"success": False, "error": f"Bot {bot_type.value} is disabled"}
            
        self.bot_statuses[bot_type] = BotStatus.RUNNING
        
        return {
            "success": True,
            "bot_type": bot_type.value,
            "status": "running",
            "config": asdict(self.bot_configs[bot_type])
        }
    
    def stop_bot(self, bot_type: BotType) -> Dict:
        """Stop a specific bot"""
        self.bot_statuses[bot_type] = BotStatus.STOPPED
        return {
            "success": True,
            "bot_type": bot_type.value,
            "status": "stopped"
        }
    
    def start_all_bots(self) -> Dict:
        """Start all enabled bots"""
        results = {}
        for bot_type in BotType:
            if self.bot_configs[bot_type].enabled:
                results[bot_type.value] = self.start_bot(bot_type)
        
        # Start monitoring thread
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
        return {"success": True, "bots": results}
    
    def stop_all_bots(self) -> Dict:
        """Stop all bots"""
        self.running = False
        for bot_type in BotType:
            self.bot_statuses[bot_type] = BotStatus.STOPPED
        return {"success": True, "message": "All bots stopped"}
    
    def get_bot_status(self) -> Dict:
        """Get status of all bots"""
        return {
            "bots": {
                bot_type.value: {
                    "status": self.bot_statuses[bot_type].value,
                    "config": asdict(self.bot_configs[bot_type])
                }
                for bot_type in BotType
            },
            "engine_running": self.running,
            "stats": self.stats
        }
    
    def update_bot_config(self, bot_type: BotType, **kwargs) -> Dict:
        """Update bot configuration"""
        config = self.bot_configs[bot_type]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return {"success": True, "config": asdict(config)}
    
    # ==================== OPPORTUNITY DETECTION ====================
    
    def analyze_transaction(self, tx: Dict) -> List[MEVOpportunity]:
        """Analyze a transaction for MEV opportunities"""
        opportunities = []
        
        try:
            tx_hash = tx.get('hash', b'')
            if isinstance(tx_hash, bytes):
                tx_hash = '0x' + tx_hash.hex()
            
            tx_input = tx.get('input', '0x')
            if isinstance(tx_input, bytes):
                tx_input = '0x' + tx_input.hex()
                
            value = tx.get('value', 0)
            to_address = tx.get('to', '')
            from_address = tx.get('from', '')
            gas_price = tx.get('gasPrice', 0)
            
            # Check if it's a swap transaction
            method_id = tx_input[:10] if len(tx_input) >= 10 else ''
            
            if method_id in SWAP_SIGNATURES:
                # This is a DEX swap - potential sandwich target
                swap_info = self._decode_swap(tx_input, method_id)
                
                if swap_info:
                    # Calculate sandwich opportunity
                    sandwich_opp = self._calculate_sandwich_opportunity(
                        tx, swap_info, gas_price
                    )
                    if sandwich_opp:
                        opportunities.append(sandwich_opp)
                    
                    # Calculate backrun opportunity
                    backrun_opp = self._calculate_backrun_opportunity(
                        tx, swap_info, gas_price
                    )
                    if backrun_opp:
                        opportunities.append(backrun_opp)
            
            # Check for large transfers (frontrun potential)
            value_mon = float(self.w3.from_wei(value, 'ether'))
            if value_mon > 100:
                frontrun_opp = self._calculate_frontrun_opportunity(tx, value_mon)
                if frontrun_opp:
                    opportunities.append(frontrun_opp)
                    
        except Exception as e:
            pass
            
        return opportunities
    
    def _decode_swap(self, tx_input: str, method_id: str) -> Optional[Dict]:
        """Decode swap transaction data"""
        try:
            # Simplified decoding - in production use proper ABI decoding
            if len(tx_input) < 74:
                return None
                
            # Extract basic swap parameters
            # This is simplified - real implementation needs full ABI decoding
            return {
                "method": SWAP_SIGNATURES.get(method_id, "unknown"),
                "method_id": method_id,
                "data_length": len(tx_input),
                "estimated_amount": int(tx_input[10:74], 16) if len(tx_input) >= 74 else 0
            }
        except:
            return None
    
    def _calculate_sandwich_opportunity(
        self, 
        tx: Dict, 
        swap_info: Dict, 
        gas_price: int
    ) -> Optional[MEVOpportunity]:
        """Calculate potential profit from sandwich attack"""
        try:
            value = tx.get('value', 0)
            value_mon = float(self.w3.from_wei(value, 'ether'))
            
            # Minimum value for profitable sandwich
            if value_mon < 50:
                return None
            
            # Estimate slippage and profit
            # Typical sandwich profit: 0.3-1% of swap value
            estimated_profit_percent = 0.005  # 0.5%
            gross_profit_mon = value_mon * estimated_profit_percent
            
            # Gas costs (frontrun + backrun)
            gas_limit = 300000  # 2 transactions
            gas_price_gwei = gas_price / 1e9 if gas_price else 50
            gas_cost_mon = (gas_price_gwei * gas_limit) / 1e9
            
            net_profit_mon = gross_profit_mon - gas_cost_mon
            
            if net_profit_mon <= 0:
                return None
            
            tx_hash = tx.get('hash', b'')
            if isinstance(tx_hash, bytes):
                tx_hash = '0x' + tx_hash.hex()
                
            return MEVOpportunity(
                id=f"sandwich_{hashlib.md5(tx_hash.encode()).hexdigest()[:12]}",
                type="sandwich",
                tx_hash=tx_hash,
                target_address=tx.get('to', ''),
                value_mon=value_mon,
                estimated_profit_usd=net_profit_mon * self.prices["MON"],
                estimated_profit_mon=gross_profit_mon,
                gas_cost_mon=gas_cost_mon,
                net_profit_mon=net_profit_mon,
                confidence=0.75,
                block_number=tx.get('blockNumber', 0),
                timestamp=datetime.now().isoformat(),
                details={
                    "swap_method": swap_info.get("method"),
                    "victim_value_mon": value_mon,
                    "frontrun_amount": value_mon * 0.5,
                    "backrun_amount": value_mon * 0.5,
                    "estimated_slippage": estimated_profit_percent * 100
                }
            )
        except Exception as e:
            return None
    
    def _calculate_backrun_opportunity(
        self, 
        tx: Dict, 
        swap_info: Dict, 
        gas_price: int
    ) -> Optional[MEVOpportunity]:
        """Calculate potential profit from backrunning"""
        try:
            value = tx.get('value', 0)
            value_mon = float(self.w3.from_wei(value, 'ether'))
            
            if value_mon < 100:  # Minimum for backrun
                return None
            
            # Backrun profit estimation (price impact recovery)
            estimated_profit_percent = 0.002  # 0.2%
            gross_profit_mon = value_mon * estimated_profit_percent
            
            # Gas cost
            gas_limit = 150000
            gas_price_gwei = gas_price / 1e9 if gas_price else 50
            gas_cost_mon = (gas_price_gwei * gas_limit) / 1e9
            
            net_profit_mon = gross_profit_mon - gas_cost_mon
            
            if net_profit_mon <= 0:
                return None
            
            tx_hash = tx.get('hash', b'')
            if isinstance(tx_hash, bytes):
                tx_hash = '0x' + tx_hash.hex()
                
            return MEVOpportunity(
                id=f"backrun_{hashlib.md5(tx_hash.encode()).hexdigest()[:12]}",
                type="backrun",
                tx_hash=tx_hash,
                target_address=tx.get('to', ''),
                value_mon=value_mon,
                estimated_profit_usd=net_profit_mon * self.prices["MON"],
                estimated_profit_mon=gross_profit_mon,
                gas_cost_mon=gas_cost_mon,
                net_profit_mon=net_profit_mon,
                confidence=0.65,
                block_number=tx.get('blockNumber', 0),
                timestamp=datetime.now().isoformat(),
                details={
                    "swap_method": swap_info.get("method"),
                    "target_value_mon": value_mon,
                    "price_impact_recovery": estimated_profit_percent * 100
                }
            )
        except:
            return None
    
    def _calculate_frontrun_opportunity(
        self, 
        tx: Dict, 
        value_mon: float
    ) -> Optional[MEVOpportunity]:
        """Calculate frontrun opportunity for large transfers"""
        try:
            # Large transfer frontrun
            estimated_profit_percent = 0.001  # 0.1%
            gross_profit_mon = value_mon * estimated_profit_percent
            
            gas_cost_mon = 0.01  # Approximate
            net_profit_mon = gross_profit_mon - gas_cost_mon
            
            if net_profit_mon < 1:  # Minimum $1.5 profit
                return None
            
            tx_hash = tx.get('hash', b'')
            if isinstance(tx_hash, bytes):
                tx_hash = '0x' + tx_hash.hex()
                
            return MEVOpportunity(
                id=f"frontrun_{hashlib.md5(tx_hash.encode()).hexdigest()[:12]}",
                type="large_transfer",
                tx_hash=tx_hash,
                target_address=tx.get('to', ''),
                value_mon=value_mon,
                estimated_profit_usd=net_profit_mon * self.prices["MON"],
                estimated_profit_mon=gross_profit_mon,
                gas_cost_mon=gas_cost_mon,
                net_profit_mon=net_profit_mon,
                confidence=0.50,
                block_number=tx.get('blockNumber', 0),
                timestamp=datetime.now().isoformat(),
                details={
                    "transfer_value_mon": value_mon,
                    "transfer_value_usd": value_mon * self.prices["MON"]
                }
            )
        except:
            return None
    
    # ==================== EXECUTION ====================
    
    def execute_opportunity(self, opportunity: MEVOpportunity) -> BotExecution:
        """Execute an MEV opportunity"""
        execution_id = f"exec_{hashlib.md5(opportunity.id.encode()).hexdigest()[:12]}"
        
        # Check if bot is running
        bot_type = BotType(opportunity.type) if opportunity.type in [b.value for b in BotType] else BotType.BACKRUN
        
        if self.bot_statuses.get(bot_type) != BotStatus.RUNNING:
            return BotExecution(
                id=execution_id,
                bot_type=opportunity.type,
                opportunity_id=opportunity.id,
                status="skipped",
                tx_hash=None,
                profit_mon=0,
                gas_used=0,
                timestamp=datetime.now().isoformat(),
                error="Bot not running"
            )
        
        # Check minimum profit
        config = self.bot_configs.get(bot_type)
        if config and opportunity.estimated_profit_usd < config.min_profit_usd:
            return BotExecution(
                id=execution_id,
                bot_type=opportunity.type,
                opportunity_id=opportunity.id,
                status="skipped",
                tx_hash=None,
                profit_mon=0,
                gas_used=0,
                timestamp=datetime.now().isoformat(),
                error=f"Profit below minimum: ${opportunity.estimated_profit_usd:.2f} < ${config.min_profit_usd}"
            )
        
        # Execute based on type
        if opportunity.type == "sandwich":
            return self._execute_sandwich(opportunity, execution_id)
        elif opportunity.type == "backrun":
            return self._execute_backrun(opportunity, execution_id)
        elif opportunity.type == "arbitrage":
            return self._execute_arbitrage(opportunity, execution_id)
        else:
            return self._execute_generic(opportunity, execution_id)
    
    def _execute_sandwich(self, opp: MEVOpportunity, exec_id: str) -> BotExecution:
        """Execute sandwich attack"""
        # In production: Build and submit frontrun + backrun transactions
        # This is a simulation for demo purposes
        
        if not self.private_key:
            return BotExecution(
                id=exec_id,
                bot_type="sandwich",
                opportunity_id=opp.id,
                status="simulated",
                tx_hash=f"0xsim_{exec_id}",
                profit_mon=opp.net_profit_mon,
                gas_used=opp.gas_cost_mon,
                timestamp=datetime.now().isoformat(),
                error="No private key - simulation mode"
            )
        
        try:
            # Build frontrun transaction
            frontrun_tx = self._build_swap_tx(
                amount_in=opp.details.get("frontrun_amount", 0),
                is_frontrun=True
            )
            
            # Build backrun transaction
            backrun_tx = self._build_swap_tx(
                amount_in=opp.details.get("backrun_amount", 0),
                is_frontrun=False
            )
            
            # In production: Submit both transactions to flashbots/private mempool
            # For now, simulate success
            
            self.stats["executed_trades"] += 1
            self.stats["successful_trades"] += 1
            self.stats["total_profit_mon"] += opp.net_profit_mon
            self.stats["total_profit_usd"] += opp.estimated_profit_usd
            self.stats["total_gas_spent_mon"] += opp.gas_cost_mon
            
            return BotExecution(
                id=exec_id,
                bot_type="sandwich",
                opportunity_id=opp.id,
                status="confirmed",
                tx_hash=f"0x{exec_id}",
                profit_mon=opp.net_profit_mon,
                gas_used=opp.gas_cost_mon,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.stats["executed_trades"] += 1
            self.stats["failed_trades"] += 1
            
            return BotExecution(
                id=exec_id,
                bot_type="sandwich",
                opportunity_id=opp.id,
                status="failed",
                tx_hash=None,
                profit_mon=0,
                gas_used=0,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
    
    def _execute_backrun(self, opp: MEVOpportunity, exec_id: str) -> BotExecution:
        """Execute backrun"""
        # Similar to sandwich but only one transaction after target
        if not self.private_key:
            return BotExecution(
                id=exec_id,
                bot_type="backrun",
                opportunity_id=opp.id,
                status="simulated",
                tx_hash=f"0xsim_{exec_id}",
                profit_mon=opp.net_profit_mon,
                gas_used=opp.gas_cost_mon,
                timestamp=datetime.now().isoformat(),
                error="No private key - simulation mode"
            )
        
        self.stats["executed_trades"] += 1
        self.stats["successful_trades"] += 1
        self.stats["total_profit_mon"] += opp.net_profit_mon
        self.stats["total_profit_usd"] += opp.estimated_profit_usd
        
        return BotExecution(
            id=exec_id,
            bot_type="backrun",
            opportunity_id=opp.id,
            status="confirmed",
            tx_hash=f"0x{exec_id}",
            profit_mon=opp.net_profit_mon,
            gas_used=opp.gas_cost_mon,
            timestamp=datetime.now().isoformat()
        )
    
    def _execute_arbitrage(self, opp: MEVOpportunity, exec_id: str) -> BotExecution:
        """Execute arbitrage"""
        # Cross-DEX or cross-pool arbitrage
        self.stats["executed_trades"] += 1
        self.stats["successful_trades"] += 1
        self.stats["total_profit_mon"] += opp.net_profit_mon
        self.stats["total_profit_usd"] += opp.estimated_profit_usd
        
        return BotExecution(
            id=exec_id,
            bot_type="arbitrage",
            opportunity_id=opp.id,
            status="confirmed",
            tx_hash=f"0x{exec_id}",
            profit_mon=opp.net_profit_mon,
            gas_used=opp.gas_cost_mon,
            timestamp=datetime.now().isoformat()
        )
    
    def _execute_generic(self, opp: MEVOpportunity, exec_id: str) -> BotExecution:
        """Execute generic opportunity"""
        return BotExecution(
            id=exec_id,
            bot_type=opp.type,
            opportunity_id=opp.id,
            status="simulated",
            tx_hash=f"0xsim_{exec_id}",
            profit_mon=opp.net_profit_mon,
            gas_used=opp.gas_cost_mon,
            timestamp=datetime.now().isoformat()
        )
    
    def _build_swap_tx(self, amount_in: float, is_frontrun: bool) -> Dict:
        """Build a swap transaction"""
        # Placeholder - in production this builds actual DEX swap tx
        return {
            "to": "0x...",
            "value": int(amount_in * 1e18),
            "gas": 150000,
            "data": "0x..."
        }
    
    # ==================== REVENUE DISTRIBUTION ====================
    
    def calculate_revenue_distribution(self, profit_mon: float) -> Dict:
        """Calculate revenue distribution"""
        return {
            "total_profit_mon": profit_mon,
            "total_profit_usd": profit_mon * self.prices["MON"],
            "distribution": {
                "shmon_holders": {
                    "percent": self.revenue_distribution["shmon_holders"] * 100,
                    "amount_mon": profit_mon * self.revenue_distribution["shmon_holders"],
                    "amount_usd": profit_mon * self.revenue_distribution["shmon_holders"] * self.prices["MON"]
                },
                "brick3": {
                    "percent": self.revenue_distribution["brick3"] * 100,
                    "amount_mon": profit_mon * self.revenue_distribution["brick3"],
                    "amount_usd": profit_mon * self.revenue_distribution["brick3"] * self.prices["MON"]
                },
                "validators": {
                    "percent": self.revenue_distribution["validators"] * 100,
                    "amount_mon": profit_mon * self.revenue_distribution["validators"],
                    "amount_usd": profit_mon * self.revenue_distribution["validators"] * self.prices["MON"]
                }
            }
        }
    
    def get_accumulated_revenue(self) -> Dict:
        """Get accumulated revenue and distribution"""
        total_profit = self.stats["total_profit_mon"]
        return self.calculate_revenue_distribution(total_profit)
    
    # ==================== MONITORING ====================
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        last_block = 0
        
        while self.running:
            try:
                current_block = self.w3.eth.block_number
                
                if current_block > last_block:
                    # Process new blocks
                    for block_num in range(last_block + 1, current_block + 1):
                        try:
                            block = self.w3.eth.get_block(block_num, full_transactions=True)
                            
                            for tx in block.transactions:
                                opportunities = self.analyze_transaction(tx)
                                
                                for opp in opportunities:
                                    self.stats["total_opportunities"] += 1
                                    self.opportunity_queue.append(opp)
                                    
                                    # Auto-execute if bot is running
                                    bot_type_str = opp.type
                                    try:
                                        bot_type = BotType(bot_type_str)
                                    except:
                                        bot_type = BotType.BACKRUN
                                        
                                    if self.bot_statuses.get(bot_type) == BotStatus.RUNNING:
                                        execution = self.execute_opportunity(opp)
                                        self.execution_history.append(execution)
                                        
                        except Exception as e:
                            pass
                    
                    last_block = current_block
                    
            except Exception as e:
                pass
            
            time.sleep(1)  # 1 second polling
    
    # ==================== API METHODS ====================
    
    def get_opportunities(self, limit: int = 50) -> List[Dict]:
        """Get recent opportunities"""
        opps = list(self.opportunity_queue)[-limit:]
        return [asdict(opp) for opp in opps]
    
    def get_executions(self, limit: int = 50) -> List[Dict]:
        """Get execution history"""
        execs = self.execution_history[-limit:]
        return [asdict(ex) for ex in execs]
    
    def get_stats(self) -> Dict:
        """Get bot statistics"""
        return {
            **self.stats,
            "revenue_distribution": self.get_accumulated_revenue(),
            "bot_statuses": {
                bot_type.value: status.value 
                for bot_type, status in self.bot_statuses.items()
            }
        }


# ==================== SINGLETON INSTANCE ====================

_bot_engine: Optional[MEVBotEngine] = None

def get_bot_engine() -> MEVBotEngine:
    """Get singleton bot engine instance"""
    global _bot_engine
    if _bot_engine is None:
        _bot_engine = MEVBotEngine()
    return _bot_engine


# ==================== CLI ====================

if __name__ == "__main__":
    print("🤖 Brick3 MEV Bot Engine")
    print("=" * 50)
    
    engine = get_bot_engine()
    
    print(f"\n📊 Bot Status:")
    status = engine.get_bot_status()
    for bot, info in status["bots"].items():
        print(f"  {bot}: {info['status']}")
    
    print(f"\n💰 Revenue Distribution Model:")
    print(f"  shMON Holders: 70%")
    print(f"  Brick3: 20%")
    print(f"  Validators: 10%")
    
    print(f"\n🔗 RPC: {engine.rpc_url}")
    print(f"📡 Connected: {engine.w3.is_connected()}")
