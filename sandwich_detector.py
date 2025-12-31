"""
🥪 Brick3 Sandwich Detector & Simulator
Answers FastLane Question #2: "Do you have some example transactions of sandwich?"

This module:
1. Detects sandwich opportunities from pending transactions
2. Simulates sandwich attacks without execution
3. Logs all opportunities with detailed metrics
4. Provides example transaction data for analysis

Author: Brick3 MEV Team
License: MIT
"""

import asyncio
import json
import time
import os
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from decimal import Decimal
import hashlib
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Brick3Sandwich")

# ==================== CONFIGURATION ====================

# Sandwich simulation parameters
SANDWICH_CONFIG = {
    "min_victim_value_usd": 100,       # Minimum $100 trade
    "max_victim_value_usd": 100000,    # Maximum $100k trade
    "min_slippage_percent": 0.3,       # Minimum 0.3% slippage
    "max_frontrun_percent": 0.1,       # Don't frontrun more than 10% of pool
    "gas_price_multiplier": 1.1,       # 10% higher gas for frontrun
    "base_gas_frontrun": 150000,       # Gas for frontrun tx
    "base_gas_backrun": 150000,        # Gas for backrun tx
    "profitability_threshold": 0.001,  # 0.1% minimum profit
}

# Token prices (mock - in production, fetch from oracle)
TOKEN_PRICES = {
    "0x0000000000000000000000000000000000000000": 3500,  # MON (native)
    "0x...usdc": 1.0,
    "0x...usdt": 1.0,
    "0x...weth": 3500,
    "0x...wmon": 3500,
}

# ==================== DATA STRUCTURES ====================

@dataclass
class PoolState:
    """DEX pool state"""
    address: str
    token0: str
    token1: str
    reserve0: int
    reserve1: int
    fee_bps: int = 30  # 0.30% default
    
    @property
    def price_0_in_1(self) -> float:
        """Price of token0 in terms of token1"""
        if self.reserve0 == 0:
            return 0
        return self.reserve1 / self.reserve0
    
    @property
    def price_1_in_0(self) -> float:
        """Price of token1 in terms of token0"""
        if self.reserve1 == 0:
            return 0
        return self.reserve0 / self.reserve1
    
    def get_amount_out(self, amount_in: int, token_in: str) -> int:
        """Calculate output amount using constant product formula"""
        if token_in == self.token0:
            reserve_in, reserve_out = self.reserve0, self.reserve1
        else:
            reserve_in, reserve_out = self.reserve1, self.reserve0
        
        # Apply fee
        amount_in_with_fee = amount_in * (10000 - self.fee_bps)
        numerator = amount_in_with_fee * reserve_out
        denominator = (reserve_in * 10000) + amount_in_with_fee
        
        return numerator // denominator
    
    def simulate_swap(self, amount_in: int, token_in: str) -> Tuple[int, 'PoolState']:
        """Simulate a swap and return new pool state"""
        amount_out = self.get_amount_out(amount_in, token_in)
        
        if token_in == self.token0:
            new_reserve0 = self.reserve0 + amount_in
            new_reserve1 = self.reserve1 - amount_out
        else:
            new_reserve0 = self.reserve0 - amount_out
            new_reserve1 = self.reserve1 + amount_in
        
        new_state = PoolState(
            address=self.address,
            token0=self.token0,
            token1=self.token1,
            reserve0=new_reserve0,
            reserve1=new_reserve1,
            fee_bps=self.fee_bps
        )
        
        return amount_out, new_state

@dataclass
class SandwichOpportunity:
    """Detected sandwich opportunity"""
    id: str
    target_tx_hash: str
    target_from: str
    target_to: str
    target_method: str
    
    # Token info
    token_in: str
    token_out: str
    pool_address: str
    
    # Target trade details
    target_amount_in: int
    target_min_amount_out: int
    target_slippage: float
    target_value_usd: float
    
    # Sandwich simulation results
    frontrun_amount: int
    frontrun_cost_wei: int
    backrun_amount_out: int
    
    # Profit analysis
    gross_profit_wei: int
    gas_cost_wei: int
    net_profit_wei: int
    net_profit_usd: float
    roi_percent: float
    
    # Risk metrics
    confidence: float
    price_impact_percent: float
    
    # Timing
    detected_at: float = field(default_factory=time.time)
    block_number: int = 0
    
    # Status
    simulated: bool = True
    executed: bool = False
    execution_result: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class SandwichSimulation:
    """Full sandwich simulation result"""
    opportunity: SandwichOpportunity
    
    # Detailed simulation steps
    initial_pool_state: PoolState
    after_frontrun_state: PoolState
    after_victim_state: PoolState
    after_backrun_state: PoolState
    
    # Transaction details
    frontrun_tx: Dict
    victim_tx: Dict
    backrun_tx: Dict
    
    # Timing analysis
    simulation_time_ms: float
    estimated_execution_time_ms: float

# ==================== SANDWICH DETECTOR ====================

class SandwichDetector:
    """
    Detects and simulates sandwich attack opportunities
    """
    
    def __init__(self, db_path: str = "sandwich_data.db"):
        self.db_path = db_path
        self.stats = {
            "total_analyzed": 0,
            "opportunities_found": 0,
            "profitable_opportunities": 0,
            "total_potential_profit_usd": 0.0,
            "simulations_run": 0,
        }
        self._init_db()
    
    def _init_db(self):
        """Initialize database for sandwich opportunities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sandwich_opportunities (
                id TEXT PRIMARY KEY,
                target_tx_hash TEXT,
                target_from TEXT,
                target_method TEXT,
                token_in TEXT,
                token_out TEXT,
                pool_address TEXT,
                target_amount_in TEXT,
                target_slippage REAL,
                target_value_usd REAL,
                frontrun_amount TEXT,
                net_profit_wei TEXT,
                net_profit_usd REAL,
                roi_percent REAL,
                confidence REAL,
                price_impact_percent REAL,
                detected_at REAL,
                block_number INTEGER,
                simulated INTEGER,
                executed INTEGER,
                execution_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id TEXT,
                simulation_data TEXT,
                frontrun_tx TEXT,
                victim_tx TEXT,
                backrun_tx TEXT,
                simulation_time_ms REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES sandwich_opportunities(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_opp_profit ON sandwich_opportunities(net_profit_usd)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_opp_time ON sandwich_opportunities(detected_at)
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"📁 Sandwich database initialized: {self.db_path}")
    
    def analyze_pending_tx(
        self,
        tx_hash: str,
        from_address: str,
        to_address: str,
        method: str,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        slippage_percent: float,
        pool_state: PoolState,
        gas_price_wei: int,
        block_number: int
    ) -> Optional[SandwichOpportunity]:
        """
        Analyze a pending transaction for sandwich opportunity
        """
        self.stats["total_analyzed"] += 1
        
        # Calculate target value in USD
        token_price = TOKEN_PRICES.get(token_in.lower(), 0)
        target_value_usd = (amount_in / 1e18) * token_price
        
        # Check basic eligibility
        if target_value_usd < SANDWICH_CONFIG["min_victim_value_usd"]:
            logger.debug(f"TX {tx_hash[:10]}... too small: ${target_value_usd:.2f}")
            return None
        
        if target_value_usd > SANDWICH_CONFIG["max_victim_value_usd"]:
            logger.debug(f"TX {tx_hash[:10]}... too large: ${target_value_usd:.2f}")
            return None
        
        if slippage_percent < SANDWICH_CONFIG["min_slippage_percent"]:
            logger.debug(f"TX {tx_hash[:10]}... slippage too low: {slippage_percent:.2f}%")
            return None
        
        # Simulate sandwich attack
        simulation = self._simulate_sandwich(
            pool_state=pool_state,
            target_amount_in=amount_in,
            target_min_out=min_amount_out,
            target_slippage=slippage_percent,
            token_in=token_in,
            gas_price_wei=gas_price_wei
        )
        
        if not simulation:
            return None
        
        # Calculate profitability
        net_profit_usd = (simulation["net_profit_wei"] / 1e18) * token_price
        roi = (simulation["net_profit_wei"] / max(simulation["frontrun_cost"], 1)) * 100
        
        # Create opportunity object
        opportunity = SandwichOpportunity(
            id=hashlib.md5(f"{tx_hash}_{time.time()}".encode()).hexdigest()[:16],
            target_tx_hash=tx_hash,
            target_from=from_address,
            target_to=to_address,
            target_method=method,
            token_in=token_in,
            token_out=token_out,
            pool_address=pool_state.address,
            target_amount_in=amount_in,
            target_min_amount_out=min_amount_out,
            target_slippage=slippage_percent,
            target_value_usd=target_value_usd,
            frontrun_amount=simulation["frontrun_amount"],
            frontrun_cost_wei=simulation["frontrun_cost"],
            backrun_amount_out=simulation["backrun_amount_out"],
            gross_profit_wei=simulation["gross_profit_wei"],
            gas_cost_wei=simulation["gas_cost_wei"],
            net_profit_wei=simulation["net_profit_wei"],
            net_profit_usd=net_profit_usd,
            roi_percent=roi,
            confidence=simulation["confidence"],
            price_impact_percent=simulation["price_impact"],
            block_number=block_number
        )
        
        # Save to database
        self._save_opportunity(opportunity)
        
        # Update stats
        self.stats["opportunities_found"] += 1
        if opportunity.net_profit_wei > 0:
            self.stats["profitable_opportunities"] += 1
            self.stats["total_potential_profit_usd"] += net_profit_usd
        
        logger.info(f"🥪 Sandwich opportunity found!")
        logger.info(f"   Target: {tx_hash[:16]}...")
        logger.info(f"   Value: ${target_value_usd:.2f}")
        logger.info(f"   Profit: ${net_profit_usd:.4f} ({roi:.2f}% ROI)")
        
        return opportunity
    
    def _simulate_sandwich(
        self,
        pool_state: PoolState,
        target_amount_in: int,
        target_min_out: int,
        target_slippage: float,
        token_in: str,
        gas_price_wei: int
    ) -> Optional[Dict]:
        """
        Simulate sandwich attack
        Returns simulation results or None if not profitable
        """
        self.stats["simulations_run"] += 1
        
        # Calculate optimal frontrun amount
        # Start with a fraction of target trade
        frontrun_percent = min(target_slippage * 0.5, SANDWICH_CONFIG["max_frontrun_percent"])
        frontrun_amount = int(target_amount_in * frontrun_percent)
        
        # Simulate frontrun
        frontrun_out, state_after_frontrun = pool_state.simulate_swap(frontrun_amount, token_in)
        
        # Calculate price impact from frontrun
        initial_price = pool_state.price_0_in_1 if token_in == pool_state.token0 else pool_state.price_1_in_0
        after_frontrun_price = state_after_frontrun.price_0_in_1 if token_in == pool_state.token0 else state_after_frontrun.price_1_in_0
        frontrun_impact = abs(after_frontrun_price - initial_price) / initial_price * 100
        
        # Simulate victim trade on impacted pool
        victim_out, state_after_victim = state_after_frontrun.simulate_swap(target_amount_in, token_in)
        
        # Check if victim still gets minimum output
        if victim_out < target_min_out:
            logger.debug("Sandwich would cause victim to get less than min output")
            return None
        
        # Simulate backrun (sell what we bought)
        # We need to swap back the output token
        output_token = pool_state.token1 if token_in == pool_state.token0 else pool_state.token0
        backrun_out, state_after_backrun = state_after_victim.simulate_swap(frontrun_out, output_token)
        
        # Calculate profit
        gross_profit = backrun_out - frontrun_amount  # We get back more than we put in
        
        # Calculate gas costs
        gas_cost = (
            SANDWICH_CONFIG["base_gas_frontrun"] * gas_price_wei * SANDWICH_CONFIG["gas_price_multiplier"] +
            SANDWICH_CONFIG["base_gas_backrun"] * gas_price_wei
        )
        gas_cost = int(gas_cost)
        
        net_profit = gross_profit - gas_cost
        
        # Calculate confidence based on various factors
        confidence = self._calculate_confidence(
            target_slippage=target_slippage,
            price_impact=frontrun_impact,
            profit_margin=(net_profit / max(frontrun_amount, 1)) * 100
        )
        
        return {
            "frontrun_amount": frontrun_amount,
            "frontrun_cost": frontrun_amount,
            "frontrun_out": frontrun_out,
            "backrun_amount_out": backrun_out,
            "gross_profit_wei": gross_profit,
            "gas_cost_wei": gas_cost,
            "net_profit_wei": net_profit,
            "price_impact": frontrun_impact,
            "confidence": confidence,
        }
    
    def _calculate_confidence(
        self,
        target_slippage: float,
        price_impact: float,
        profit_margin: float
    ) -> float:
        """Calculate confidence score for opportunity"""
        score = 0.0
        
        # Higher slippage = easier to sandwich
        if target_slippage > 2.0:
            score += 0.3
        elif target_slippage > 1.0:
            score += 0.2
        elif target_slippage > 0.5:
            score += 0.1
        
        # Reasonable price impact
        if 0.1 < price_impact < 1.0:
            score += 0.3
        elif price_impact <= 0.1:
            score += 0.2
        
        # Profitable margin
        if profit_margin > 1.0:
            score += 0.4
        elif profit_margin > 0.5:
            score += 0.3
        elif profit_margin > 0.1:
            score += 0.2
        
        return min(score, 1.0)
    
    def _save_opportunity(self, opp: SandwichOpportunity):
        """Save opportunity to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sandwich_opportunities 
                (id, target_tx_hash, target_from, target_method, token_in, token_out,
                 pool_address, target_amount_in, target_slippage, target_value_usd,
                 frontrun_amount, net_profit_wei, net_profit_usd, roi_percent,
                 confidence, price_impact_percent, detected_at, block_number,
                 simulated, executed, execution_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opp.id, opp.target_tx_hash, opp.target_from, opp.target_method,
                opp.token_in, opp.token_out, opp.pool_address,
                str(opp.target_amount_in), opp.target_slippage, opp.target_value_usd,
                str(opp.frontrun_amount), str(opp.net_profit_wei), opp.net_profit_usd,
                opp.roi_percent, opp.confidence, opp.price_impact_percent,
                opp.detected_at, opp.block_number, 1, 0, None
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB save error: {e}")
    
    def run_full_simulation(
        self,
        opportunity: SandwichOpportunity,
        pool_state: PoolState,
        gas_price_wei: int
    ) -> SandwichSimulation:
        """
        Run detailed simulation with all transaction details
        """
        start_time = time.time()
        
        # Frontrun simulation
        frontrun_out, state_after_frontrun = pool_state.simulate_swap(
            opportunity.frontrun_amount,
            opportunity.token_in
        )
        
        # Victim trade
        victim_out, state_after_victim = state_after_frontrun.simulate_swap(
            opportunity.target_amount_in,
            opportunity.token_in
        )
        
        # Backrun
        output_token = pool_state.token1 if opportunity.token_in == pool_state.token0 else pool_state.token0
        backrun_out, state_after_backrun = state_after_victim.simulate_swap(
            frontrun_out,
            output_token
        )
        
        simulation_time = (time.time() - start_time) * 1000
        
        # Create transaction objects
        frontrun_tx = {
            "type": "frontrun",
            "to": opportunity.pool_address,
            "value": opportunity.frontrun_amount,
            "gas_limit": SANDWICH_CONFIG["base_gas_frontrun"],
            "gas_price": int(gas_price_wei * SANDWICH_CONFIG["gas_price_multiplier"]),
            "data": f"0x...swap({opportunity.token_in}, {opportunity.frontrun_amount})"
        }
        
        victim_tx = {
            "type": "victim",
            "hash": opportunity.target_tx_hash,
            "from": opportunity.target_from,
            "amount_in": opportunity.target_amount_in,
            "expected_out": victim_out
        }
        
        backrun_tx = {
            "type": "backrun",
            "to": opportunity.pool_address,
            "value": frontrun_out,
            "gas_limit": SANDWICH_CONFIG["base_gas_backrun"],
            "gas_price": gas_price_wei,
            "data": f"0x...swap({output_token}, {frontrun_out})"
        }
        
        simulation = SandwichSimulation(
            opportunity=opportunity,
            initial_pool_state=pool_state,
            after_frontrun_state=state_after_frontrun,
            after_victim_state=state_after_victim,
            after_backrun_state=state_after_backrun,
            frontrun_tx=frontrun_tx,
            victim_tx=victim_tx,
            backrun_tx=backrun_tx,
            simulation_time_ms=simulation_time,
            estimated_execution_time_ms=100  # 100ms for bundle submission
        )
        
        # Log simulation
        self._save_simulation_log(simulation)
        
        return simulation
    
    def _save_simulation_log(self, sim: SandwichSimulation):
        """Save simulation log to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO simulation_logs 
                (opportunity_id, simulation_data, frontrun_tx, victim_tx, backrun_tx, simulation_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                sim.opportunity.id,
                json.dumps(asdict(sim.opportunity)),
                json.dumps(sim.frontrun_tx),
                json.dumps(sim.victim_tx),
                json.dumps(sim.backrun_tx),
                sim.simulation_time_ms
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Simulation log save error: {e}")

# ==================== QUERY FUNCTIONS ====================

def get_sandwich_opportunities(
    db_path: str = "sandwich_data.db",
    limit: int = 100,
    min_profit_usd: float = 0
) -> List[Dict]:
    """Get sandwich opportunities from database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, target_tx_hash, target_from, target_method, token_in, token_out,
               target_value_usd, net_profit_usd, roi_percent, confidence, detected_at
        FROM sandwich_opportunities
        WHERE net_profit_usd >= ?
        ORDER BY detected_at DESC
        LIMIT ?
    ''', (min_profit_usd, limit))
    
    columns = ['id', 'target_tx_hash', 'target_from', 'target_method', 'token_in', 
               'token_out', 'target_value_usd', 'net_profit_usd', 'roi_percent', 
               'confidence', 'detected_at']
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return results

def get_simulation_logs(
    db_path: str = "sandwich_data.db",
    opportunity_id: str = None,
    limit: int = 50
) -> List[Dict]:
    """Get simulation logs from database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if opportunity_id:
        cursor.execute('''
            SELECT * FROM simulation_logs
            WHERE opportunity_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (opportunity_id, limit))
    else:
        cursor.execute('''
            SELECT * FROM simulation_logs
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
    
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return results

def get_sandwich_summary(db_path: str = "sandwich_data.db") -> Dict:
    """Get summary of sandwich opportunities"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total opportunities
    cursor.execute('SELECT COUNT(*) FROM sandwich_opportunities')
    total = cursor.fetchone()[0]
    
    # Profitable opportunities
    cursor.execute('SELECT COUNT(*) FROM sandwich_opportunities WHERE net_profit_usd > 0')
    profitable = cursor.fetchone()[0]
    
    # Total potential profit
    cursor.execute('SELECT SUM(net_profit_usd) FROM sandwich_opportunities WHERE net_profit_usd > 0')
    total_profit = cursor.fetchone()[0] or 0
    
    # Average ROI
    cursor.execute('SELECT AVG(roi_percent) FROM sandwich_opportunities WHERE net_profit_usd > 0')
    avg_roi = cursor.fetchone()[0] or 0
    
    # Simulation count
    cursor.execute('SELECT COUNT(*) FROM simulation_logs')
    simulations = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_opportunities": total,
        "profitable_opportunities": profitable,
        "total_potential_profit_usd": total_profit,
        "average_roi_percent": avg_roi,
        "total_simulations": simulations,
        "profitability_rate": (profitable / max(total, 1)) * 100
    }

def export_example_sandwiches(
    db_path: str = "sandwich_data.db",
    output_file: str = "sandwich_examples.json"
) -> str:
    """Export example sandwich data for FastLane team"""
    opportunities = get_sandwich_opportunities(db_path, limit=10, min_profit_usd=0.01)
    
    examples = []
    for opp in opportunities:
        # Get simulation log
        logs = get_simulation_logs(db_path, opportunity_id=opp['id'], limit=1)
        
        example = {
            "opportunity": opp,
            "simulation": logs[0] if logs else None,
            "explanation": {
                "strategy": "Classic sandwich attack simulation",
                "frontrun": "Buy token before victim to raise price",
                "victim_trade": "Victim buys at inflated price",
                "backrun": "Sell token after victim at higher price",
                "profit_source": "Price difference between frontrun and backrun"
            }
        }
        examples.append(example)
    
    with open(output_file, 'w') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "disclaimer": "These are SIMULATED examples, not executed transactions",
            "summary": get_sandwich_summary(db_path),
            "examples": examples
        }, f, indent=2)
    
    return output_file

# ==================== DEMO ====================

def demo_sandwich_detection():
    """Demo: Sandwich detection and simulation"""
    print("=" * 60)
    print("🥪 Brick3 Sandwich Detector Demo")
    print("=" * 60)
    
    # Create detector
    detector = SandwichDetector()
    
    # Create mock pool state
    pool = PoolState(
        address="0x...pool_mon_usdc",
        token0="0x...wmon",
        token1="0x...usdc",
        reserve0=int(1000000 * 1e18),  # 1M MON
        reserve1=int(3500000 * 1e6),   # 3.5M USDC
        fee_bps=30
    )
    
    # Simulate some pending transactions
    test_txs = [
        {
            "hash": "0xabc123...",
            "from": "0xvictim1...",
            "method": "swapExactTokensForTokens",
            "amount_in": int(10000 * 1e18),  # 10k MON
            "min_out": int(33000 * 1e6),     # 33k USDC (5.7% slippage)
            "slippage": 5.7,
            "gas_price": int(50 * 1e9)       # 50 gwei
        },
        {
            "hash": "0xdef456...",
            "from": "0xvictim2...",
            "method": "swapExactTokensForTokens",
            "amount_in": int(5000 * 1e18),   # 5k MON
            "min_out": int(16500 * 1e6),     # 16.5k USDC (2.8% slippage)
            "slippage": 2.8,
            "gas_price": int(40 * 1e9)
        },
        {
            "hash": "0xghi789...",
            "from": "0xvictim3...",
            "method": "swapExactTokensForTokens",
            "amount_in": int(500 * 1e18),    # 500 MON
            "min_out": int(1730 * 1e6),      # 1.73k USDC (1% slippage)
            "slippage": 1.0,
            "gas_price": int(35 * 1e9)
        }
    ]
    
    print(f"\n📊 Analyzing {len(test_txs)} pending transactions...\n")
    
    for tx in test_txs:
        print(f"Analyzing TX: {tx['hash']}")
        print(f"  Amount: {tx['amount_in'] / 1e18:.2f} MON")
        print(f"  Slippage: {tx['slippage']:.2f}%")
        
        opportunity = detector.analyze_pending_tx(
            tx_hash=tx["hash"],
            from_address=tx["from"],
            to_address=pool.address,
            method=tx["method"],
            token_in=pool.token0,
            token_out=pool.token1,
            amount_in=tx["amount_in"],
            min_amount_out=tx["min_out"],
            slippage_percent=tx["slippage"],
            pool_state=pool,
            gas_price_wei=tx["gas_price"],
            block_number=1000000
        )
        
        if opportunity:
            print(f"  ✅ Opportunity found! Potential profit: ${opportunity.net_profit_usd:.4f}")
            
            # Run full simulation
            sim = detector.run_full_simulation(opportunity, pool, tx["gas_price"])
            print(f"  📝 Full simulation logged (took {sim.simulation_time_ms:.2f}ms)")
        else:
            print(f"  ❌ No profitable opportunity")
        
        print()
    
    # Print summary
    print("=" * 60)
    print("📊 Detection Summary")
    print("=" * 60)
    summary = get_sandwich_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Export examples
    export_file = export_example_sandwiches()
    print(f"\n📁 Examples exported to: {export_file}")

if __name__ == "__main__":
    demo_sandwich_detection()
