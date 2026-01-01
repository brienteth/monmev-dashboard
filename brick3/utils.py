# Brick3 Utilities and Helper Functions
from typing import Dict, Any, Optional
from web3 import Web3
import asyncio
from datetime import datetime

def validate_address(address: str) -> bool:
    """Validate Ethereum address format"""
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False

def format_wei_to_mon(wei: int) -> float:
    """Convert wei to MON (18 decimals)"""
    return wei / 1e18

def format_mon_to_wei(mon: float) -> int:
    """Convert MON to wei"""
    return int(mon * 1e18)

def format_gas_gwei(wei: int) -> float:
    """Convert wei to Gwei for gas prices"""
    return wei / 1e9

def calculate_transaction_cost(gas_used: int, gas_price_wei: int) -> int:
    """Calculate total transaction cost in wei"""
    return gas_used * gas_price_wei

def estimate_execution_time(mempool_poll_interval_ms: int, speed_multiplier: int) -> str:
    """
    Estimate execution time for transaction inclusion
    
    Speed multiplier: How much faster than standard RPC
    Mempool poll interval: How frequently we check mempool
    """
    base_time_ms = 1000 / mempool_poll_interval_ms * 100  # Rough estimate
    improved_time_ms = base_time_ms / speed_multiplier
    
    if improved_time_ms < 100:
        return f"{improved_time_ms:.0f}ms"
    elif improved_time_ms < 1000:
        return f"{improved_time_ms/1000:.2f}s"
    else:
        return f"{improved_time_ms/1000:.1f}s"

def calculate_mev_risk_score(gas_price_gwei: float, tx_value_mon: float) -> Dict[str, Any]:
    """
    Calculate MEV risk score for a transaction
    
    Returns:
        - risk_level: "critical", "high", "medium", "low"
        - score: 0-100
        - recommended_protection: bool
    """
    
    risk_score = 0
    
    # Gas price impact (0-40 points)
    if gas_price_gwei > 1000:
        risk_score += 40
    elif gas_price_gwei > 100:
        risk_score += 30
    elif gas_price_gwei > 10:
        risk_score += 20
    else:
        risk_score += 10
    
    # Transaction value impact (0-40 points)
    if tx_value_mon > 1000:
        risk_score += 40
    elif tx_value_mon > 100:
        risk_score += 30
    elif tx_value_mon > 10:
        risk_score += 20
    else:
        risk_score += 10
    
    # Network congestion impact (0-20 points)
    risk_score += 10  # Default: assume moderate congestion
    
    # Determine risk level
    if risk_score >= 80:
        risk_level = "critical"
    elif risk_score >= 60:
        risk_level = "high"
    elif risk_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "risk_level": risk_level,
        "score": risk_score,
        "recommended_protection": risk_score >= 40,
        "estimated_mev_exposure_percent": min(risk_score / 100 * 25, 20)  # Up to 20% MEV
    }

def simulate_mev_protection_savings(
    tx_value_mon: float,
    gas_price_gwei: float,
    gas_used: int = 21000,
    mev_protection_percent: float = 15.0
) -> Dict[str, float]:
    """
    Simulate MEV protection savings for a transaction
    
    Args:
        tx_value_mon: Transaction value in MON
        gas_price_gwei: Gas price in Gwei
        gas_used: Estimated gas used
        mev_protection_percent: MEV protection percentage (default 15% for Turbo)
    
    Returns:
        Dictionary with savings breakdown
    """
    
    # Convert to wei for calculation
    value_wei = tx_value_mon * 1e18
    gas_price_wei = gas_price_gwei * 1e9
    
    # Calculate costs
    normal_gas_cost = gas_used * gas_price_wei
    protected_gas_cost = normal_gas_cost * 0.2  # 80% gas reduction
    gas_savings = normal_gas_cost - protected_gas_cost
    
    # Calculate MEV exposure and savings
    mev_exposure = value_wei * (mev_protection_percent / 100)
    
    # Total savings
    total_savings = gas_savings + mev_exposure
    total_savings_mon = total_savings / 1e18
    
    return {
        "normal_gas_cost_mon": normal_gas_cost / 1e18,
        "protected_gas_cost_mon": protected_gas_cost / 1e18,
        "gas_savings_mon": gas_savings / 1e18,
        "mev_exposure_mon": mev_exposure / 1e18,
        "total_savings_mon": total_savings_mon,
        "total_savings_percent": (total_savings / normal_gas_cost * 100) if normal_gas_cost > 0 else 0
    }

async def async_sleep_ms(milliseconds: int):
    """Sleep for milliseconds in async context"""
    await asyncio.sleep(milliseconds / 1000)

def timestamp_to_readable(timestamp: float) -> str:
    """Convert Unix timestamp to readable format"""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_current_timestamp_ms() -> int:
    """Get current Unix timestamp in milliseconds"""
    return int(datetime.now().timestamp() * 1000)

# Color/emoji utilities for terminal output
class Emoji:
    """Terminal emoji utilities"""
    ROCKET = "🚀"
    SHIELD = "🛡️"
    ZAPPING = "⚡"
    FIRE = "🔥"
    CHART = "📊"
    TIMER = "⏱️"
    CHECK = "✅"
    CROSS = "❌"
    LOCK = "🔒"
    UNLOCK = "🔓"
    GAS = "⛽"
    MONEY = "💰"
    WARNING = "⚠️"
    INFO = "ℹ️"
    GEAR = "⚙️"
    FLASH = "⚡"
    SPEED = "🏃"

def print_header(text: str):
    """Print styled header"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}\n")

def print_metric(label: str, value: Any, emoji: str = ""):
    """Print formatted metric"""
    print(f"{emoji} {label}: {value}")

def print_transaction_summary(tx: Dict) -> None:
    """Print transaction summary"""
    print(f"""
{Emoji.ROCKET} Transaction Summary:
  {Emoji.INFO} ID: {tx.get('id', 'N/A')}
  {Emoji.CHECK} Status: {tx.get('status', 'unknown')}
  {Emoji.MONEY} Value: {tx.get('value', 'N/A')}
  {Emoji.GAS} Gas: {tx.get('gas_limit', 'N/A')}
  {Emoji.SHIELD} MEV Savings: {tx.get('mev_savings', 0)}%
  {Emoji.TIMER} Created: {tx.get('created_at', 'N/A')}
""")
