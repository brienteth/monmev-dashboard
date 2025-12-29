"""
📊 Brick3 Transaction Simulator
Accurate profit calculation for MEV opportunities
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
import json
import os

# Lazy import for web3
Web3 = None
def get_web3_module():
    global Web3
    if Web3 is None:
        try:
            from web3 import Web3 as W3
            Web3 = W3
        except ImportError:
            # Fallback - create mock
            class MockWeb3:
                @staticmethod
                def to_wei(amount, unit):
                    if unit == 'ether':
                        return int(amount * 10**18)
                    elif unit == 'gwei':
                        return int(amount * 10**9)
                    return int(amount)
                @staticmethod
                def from_wei(amount, unit):
                    if unit == 'ether':
                        return amount / 10**18
                    elif unit == 'gwei':
                        return amount / 10**9
                    return amount
            Web3 = MockWeb3
    return Web3

@dataclass
class SimulationResult:
    """Result of a transaction simulation"""
    success: bool
    gross_profit_mon: float
    gas_cost_mon: float
    net_profit_mon: float
    net_profit_usd: float
    price_impact_percent: float
    slippage_percent: float
    confidence: float
    execution_path: List[str]
    warnings: List[str]
    details: Dict

class TransactionSimulator:
    """
    Simulates MEV transactions to calculate accurate profits
    """
    
    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url or os.getenv("MONAD_RPC", "https://rpc.monad.xyz")
        W3 = get_web3_module()
        try:
            self.w3 = W3(W3.HTTPProvider(self.rpc_url, request_kwargs={'timeout': 30}))
        except:
            self.w3 = None
        
        # Price oracle (simplified - use Chainlink in production)
        self.prices = {
            "MON": 1.5,
            "WMON": 1.5,
            "USDC": 1.0,
            "USDT": 1.0,
            "ETH": 3500,
            "WETH": 3500
        }
        
        # Gas estimates by operation type
        self.gas_estimates = {
            "simple_transfer": 21000,
            "erc20_transfer": 65000,
            "swap_v2": 150000,
            "swap_v3": 180000,
            "sandwich_frontrun": 150000,
            "sandwich_backrun": 150000,
            "arbitrage_2_hop": 300000,
            "arbitrage_3_hop": 450000,
            "liquidation": 350000,
            "flash_loan": 200000
        }
        
        # DEX fee rates
        self.dex_fees = {
            "uniswap_v2": 0.003,  # 0.3%
            "uniswap_v3_low": 0.0005,  # 0.05%
            "uniswap_v3_medium": 0.003,  # 0.3%
            "uniswap_v3_high": 0.01,  # 1%
            "kuru": 0.003,
            "default": 0.003
        }
    
    def simulate_sandwich(
        self,
        victim_tx: Dict,
        frontrun_amount_mon: float,
        target_pool: str = None
    ) -> SimulationResult:
        """
        Simulate a sandwich attack
        
        Args:
            victim_tx: The victim's swap transaction
            frontrun_amount_mon: Amount to use in frontrun
            target_pool: Target liquidity pool address
        """
        warnings = []
        
        try:
            # Extract victim swap details
            victim_value = victim_tx.get('value', 0)
            victim_value_mon = float(self.w3.from_wei(victim_value, 'ether'))
            gas_price = victim_tx.get('gasPrice', 0)
            gas_price_gwei = gas_price / 1e9 if gas_price else 50
            
            # Validate
            if victim_value_mon < 10:
                return SimulationResult(
                    success=False,
                    gross_profit_mon=0,
                    gas_cost_mon=0,
                    net_profit_mon=0,
                    net_profit_usd=0,
                    price_impact_percent=0,
                    slippage_percent=0,
                    confidence=0,
                    execution_path=[],
                    warnings=["Victim swap too small"],
                    details={}
                )
            
            # Calculate price impact from frontrun
            # Simplified AMM model: price_impact = amount / (2 * liquidity)
            estimated_liquidity = victim_value_mon * 100  # Assume pool is 100x victim size
            
            frontrun_impact = frontrun_amount_mon / (2 * estimated_liquidity) * 100
            victim_impact = victim_value_mon / (2 * estimated_liquidity) * 100
            
            # Profit from sandwich = victim_impact * frontrun_amount (simplified)
            gross_profit_mon = (victim_impact / 100) * frontrun_amount_mon
            
            # More realistic: profit depends on slippage tolerance
            # Assume 0.5% average slippage tolerance
            max_extractable = victim_value_mon * 0.005
            gross_profit_mon = min(gross_profit_mon, max_extractable)
            
            # Gas costs (frontrun + backrun)
            frontrun_gas = self.gas_estimates["sandwich_frontrun"]
            backrun_gas = self.gas_estimates["sandwich_backrun"]
            total_gas = frontrun_gas + backrun_gas
            gas_cost_mon = (gas_price_gwei * total_gas) / 1e9
            
            # DEX fees
            dex_fee = self.dex_fees["default"]
            fee_cost_mon = frontrun_amount_mon * dex_fee * 2  # Buy and sell
            
            # Net profit
            net_profit_mon = gross_profit_mon - gas_cost_mon - fee_cost_mon
            net_profit_usd = net_profit_mon * self.prices["MON"]
            
            # Confidence based on profit margin
            if net_profit_mon > 0:
                profit_margin = net_profit_mon / gross_profit_mon if gross_profit_mon > 0 else 0
                confidence = min(0.9, 0.5 + profit_margin * 0.4)
            else:
                confidence = 0.1
            
            # Warnings
            if frontrun_impact > 1:
                warnings.append(f"High frontrun impact: {frontrun_impact:.2f}%")
            if gas_cost_mon > gross_profit_mon * 0.5:
                warnings.append("High gas cost relative to profit")
            if confidence < 0.5:
                warnings.append("Low confidence execution")
            
            return SimulationResult(
                success=net_profit_mon > 0,
                gross_profit_mon=round(gross_profit_mon, 6),
                gas_cost_mon=round(gas_cost_mon, 6),
                net_profit_mon=round(net_profit_mon, 6),
                net_profit_usd=round(net_profit_usd, 2),
                price_impact_percent=round(frontrun_impact, 4),
                slippage_percent=round(victim_impact, 4),
                confidence=round(confidence, 2),
                execution_path=[
                    f"1. Frontrun: Buy {frontrun_amount_mon:.2f} MON",
                    f"2. Victim swap: {victim_value_mon:.2f} MON",
                    f"3. Backrun: Sell {frontrun_amount_mon:.2f} MON"
                ],
                warnings=warnings,
                details={
                    "victim_value_mon": victim_value_mon,
                    "frontrun_amount_mon": frontrun_amount_mon,
                    "estimated_liquidity": estimated_liquidity,
                    "frontrun_gas": frontrun_gas,
                    "backrun_gas": backrun_gas,
                    "gas_price_gwei": gas_price_gwei,
                    "dex_fee_percent": dex_fee * 100
                }
            )
            
        except Exception as e:
            return SimulationResult(
                success=False,
                gross_profit_mon=0,
                gas_cost_mon=0,
                net_profit_mon=0,
                net_profit_usd=0,
                price_impact_percent=0,
                slippage_percent=0,
                confidence=0,
                execution_path=[],
                warnings=[f"Simulation error: {str(e)}"],
                details={}
            )
    
    def simulate_arbitrage(
        self,
        token_path: List[str],
        amount_in_mon: float,
        dex_path: List[str] = None
    ) -> SimulationResult:
        """
        Simulate an arbitrage trade
        
        Args:
            token_path: List of token addresses in the path
            amount_in_mon: Starting amount in MON
            dex_path: List of DEXes to use (optional)
        """
        warnings = []
        
        try:
            hops = len(token_path) - 1
            
            if hops < 2:
                return SimulationResult(
                    success=False,
                    gross_profit_mon=0,
                    gas_cost_mon=0,
                    net_profit_mon=0,
                    net_profit_usd=0,
                    price_impact_percent=0,
                    slippage_percent=0,
                    confidence=0,
                    execution_path=[],
                    warnings=["Arbitrage requires at least 2 hops"],
                    details={}
                )
            
            # Simulate each hop with price impact
            current_amount = amount_in_mon
            total_fees = 0
            execution_path = []
            
            for i in range(hops):
                dex = dex_path[i] if dex_path and i < len(dex_path) else "default"
                fee_rate = self.dex_fees.get(dex, 0.003)
                
                # Price impact (simplified)
                impact = current_amount * 0.001  # 0.1% per hop
                current_amount = current_amount * (1 - fee_rate) * (1 - impact / 100)
                total_fees += current_amount * fee_rate
                
                execution_path.append(
                    f"{i+1}. Swap {token_path[i][:8]}... → {token_path[i+1][:8]}... on {dex}"
                )
            
            gross_profit_mon = current_amount - amount_in_mon
            
            # Gas costs
            gas_type = f"arbitrage_{hops}_hop" if hops <= 3 else "arbitrage_3_hop"
            gas_estimate = self.gas_estimates.get(gas_type, 300000)
            gas_price_gwei = 50  # Default
            gas_cost_mon = (gas_price_gwei * gas_estimate) / 1e9
            
            net_profit_mon = gross_profit_mon - gas_cost_mon
            net_profit_usd = net_profit_mon * self.prices["MON"]
            
            # Confidence
            confidence = 0.7 if net_profit_mon > 0 else 0.2
            if hops > 3:
                confidence -= 0.1
                warnings.append("Complex arbitrage path may fail")
            
            return SimulationResult(
                success=net_profit_mon > 0,
                gross_profit_mon=round(gross_profit_mon, 6),
                gas_cost_mon=round(gas_cost_mon, 6),
                net_profit_mon=round(net_profit_mon, 6),
                net_profit_usd=round(net_profit_usd, 2),
                price_impact_percent=round(impact, 4),
                slippage_percent=round(total_fees / amount_in_mon * 100, 4),
                confidence=round(confidence, 2),
                execution_path=execution_path,
                warnings=warnings,
                details={
                    "hops": hops,
                    "amount_in_mon": amount_in_mon,
                    "amount_out_mon": current_amount,
                    "total_fees_mon": total_fees,
                    "gas_estimate": gas_estimate
                }
            )
            
        except Exception as e:
            return SimulationResult(
                success=False,
                gross_profit_mon=0,
                gas_cost_mon=0,
                net_profit_mon=0,
                net_profit_usd=0,
                price_impact_percent=0,
                slippage_percent=0,
                confidence=0,
                execution_path=[],
                warnings=[f"Simulation error: {str(e)}"],
                details={}
            )
    
    def simulate_backrun(
        self,
        target_tx: Dict,
        backrun_amount_mon: float
    ) -> SimulationResult:
        """
        Simulate a backrun trade
        """
        warnings = []
        
        try:
            target_value = target_tx.get('value', 0)
            target_value_mon = float(self.w3.from_wei(target_value, 'ether'))
            gas_price = target_tx.get('gasPrice', 0)
            gas_price_gwei = gas_price / 1e9 if gas_price else 50
            
            # Backrun captures price recovery after large swap
            # Typical recovery: 0.1-0.3% of target swap
            recovery_rate = 0.002  # 0.2%
            gross_profit_mon = target_value_mon * recovery_rate
            
            # Cap at our backrun amount potential
            max_profit = backrun_amount_mon * 0.01  # 1% max
            gross_profit_mon = min(gross_profit_mon, max_profit)
            
            # Gas cost
            gas_estimate = self.gas_estimates["swap_v2"]
            gas_cost_mon = (gas_price_gwei * gas_estimate) / 1e9
            
            # Fees
            fee_cost = backrun_amount_mon * self.dex_fees["default"]
            
            net_profit_mon = gross_profit_mon - gas_cost_mon - fee_cost
            net_profit_usd = net_profit_mon * self.prices["MON"]
            
            confidence = 0.65 if net_profit_mon > 0 else 0.2
            
            return SimulationResult(
                success=net_profit_mon > 0,
                gross_profit_mon=round(gross_profit_mon, 6),
                gas_cost_mon=round(gas_cost_mon, 6),
                net_profit_mon=round(net_profit_mon, 6),
                net_profit_usd=round(net_profit_usd, 2),
                price_impact_percent=round(recovery_rate * 100, 4),
                slippage_percent=0,
                confidence=round(confidence, 2),
                execution_path=[
                    f"1. Wait for target tx: {target_value_mon:.2f} MON",
                    f"2. Backrun swap: {backrun_amount_mon:.2f} MON",
                    f"3. Capture price recovery"
                ],
                warnings=warnings,
                details={
                    "target_value_mon": target_value_mon,
                    "backrun_amount_mon": backrun_amount_mon,
                    "recovery_rate": recovery_rate
                }
            )
            
        except Exception as e:
            return SimulationResult(
                success=False,
                gross_profit_mon=0,
                gas_cost_mon=0,
                net_profit_mon=0,
                net_profit_usd=0,
                price_impact_percent=0,
                slippage_percent=0,
                confidence=0,
                execution_path=[],
                warnings=[f"Simulation error: {str(e)}"],
                details={}
            )
    
    def estimate_gas_cost(
        self,
        operation: str,
        gas_price_gwei: float = 50
    ) -> Dict:
        """Estimate gas cost for an operation"""
        gas_estimate = self.gas_estimates.get(operation, 150000)
        gas_cost_mon = (gas_price_gwei * gas_estimate) / 1e9
        gas_cost_usd = gas_cost_mon * self.prices["MON"]
        
        return {
            "operation": operation,
            "gas_estimate": gas_estimate,
            "gas_price_gwei": gas_price_gwei,
            "gas_cost_mon": round(gas_cost_mon, 6),
            "gas_cost_usd": round(gas_cost_usd, 4)
        }
    
    def calculate_optimal_frontrun_amount(
        self,
        victim_value_mon: float,
        available_capital_mon: float,
        gas_price_gwei: float = 50
    ) -> Dict:
        """Calculate optimal frontrun amount for maximum profit"""
        
        # Binary search for optimal amount
        best_profit = 0
        best_amount = 0
        
        for percent in range(5, 105, 5):  # 5% to 100% of victim value
            test_amount = min(victim_value_mon * (percent / 100), available_capital_mon)
            
            # Simplified profit calculation
            estimated_liquidity = victim_value_mon * 100
            victim_impact = victim_value_mon / (2 * estimated_liquidity)
            gross_profit = victim_impact * test_amount
            
            # Costs
            gas_cost = (gas_price_gwei * 300000) / 1e9
            fee_cost = test_amount * 0.003 * 2
            
            net_profit = gross_profit - gas_cost - fee_cost
            
            if net_profit > best_profit:
                best_profit = net_profit
                best_amount = test_amount
        
        return {
            "optimal_amount_mon": round(best_amount, 4),
            "optimal_percent_of_victim": round(best_amount / victim_value_mon * 100, 2) if victim_value_mon > 0 else 0,
            "estimated_net_profit_mon": round(best_profit, 6),
            "estimated_net_profit_usd": round(best_profit * self.prices["MON"], 2)
        }


# Singleton
_simulator: Optional[TransactionSimulator] = None

def get_simulator() -> TransactionSimulator:
    global _simulator
    if _simulator is None:
        _simulator = TransactionSimulator()
    return _simulator


if __name__ == "__main__":
    print("📊 Brick3 Transaction Simulator")
    print("=" * 50)
    
    sim = get_simulator()
    W3 = get_web3_module()
    
    # Test sandwich simulation
    print("\n🥪 Sandwich Simulation (100 MON victim):")
    result = sim.simulate_sandwich(
        victim_tx={"value": W3.to_wei(100, 'ether') if W3 else 100*10**18, "gasPrice": 50 * 10**9},
        frontrun_amount_mon=50
    )
    print(f"  Success: {result.success}")
    print(f"  Net Profit: {result.net_profit_mon:.4f} MON (${result.net_profit_usd:.2f})")
    print(f"  Confidence: {result.confidence:.0%}")
    
    # Test arbitrage simulation
    print("\n🔄 Arbitrage Simulation (3-hop, 100 MON):")
    result = sim.simulate_arbitrage(
        token_path=["0xMON", "0xUSDC", "0xWETH", "0xMON"],
        amount_in_mon=100
    )
    print(f"  Success: {result.success}")
    print(f"  Net Profit: {result.net_profit_mon:.4f} MON (${result.net_profit_usd:.2f})")
    
    # Optimal frontrun calculation
    print("\n💡 Optimal Frontrun Amount:")
    optimal = sim.calculate_optimal_frontrun_amount(
        victim_value_mon=500,
        available_capital_mon=1000
    )
    print(f"  Optimal Amount: {optimal['optimal_amount_mon']:.2f} MON")
    print(f"  Expected Profit: ${optimal['estimated_net_profit_usd']:.2f}")
