"""
💰 Brick3 Revenue Distribution System
Calculates and tracks MEV earnings distribution
70% shMON Holders | 20% Brick3 | 10% Validators
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
import hashlib

@dataclass
class RevenueShare:
    """Revenue share for a single distribution"""
    id: str
    timestamp: str
    total_profit_mon: float
    total_profit_usd: float
    
    # Distribution amounts
    shmon_holders_mon: float
    shmon_holders_usd: float
    brick3_mon: float
    brick3_usd: float
    validators_mon: float
    validators_usd: float
    
    # Source info
    source_type: str  # "mev_execution", "bot_profit", "manual"
    source_id: str
    
    # Status
    status: str = "pending"  # pending, distributed, failed
    distribution_tx: Optional[str] = None

@dataclass
class RevenueStats:
    """Aggregated revenue statistics"""
    period: str  # "hourly", "daily", "weekly", "monthly", "all_time"
    start_time: str
    end_time: str
    
    total_revenue_mon: float
    total_revenue_usd: float
    
    shmon_holders_total_mon: float
    shmon_holders_total_usd: float
    brick3_total_mon: float
    brick3_total_usd: float
    validators_total_mon: float
    validators_total_usd: float
    
    distribution_count: int
    avg_distribution_mon: float
    largest_distribution_mon: float
    
    # APY calculation
    estimated_apy_boost: float

class RevenueDistributionSystem:
    """
    Revenue Distribution System
    Manages MEV profit distribution according to:
    - 70% → shMON Holders
    - 20% → Brick3
    - 10% → Validators
    """
    
    DISTRIBUTION_PERCENTAGES = {
        "shmon_holders": 0.70,
        "brick3": 0.20,
        "validators": 0.10
    }
    
    def __init__(self):
        # Price feed (simplified)
        self.mon_price_usd = 1.5
        
        # Storage
        self.distributions: List[RevenueShare] = []
        self.pending_distributions: List[RevenueShare] = []
        
        # Addresses (placeholder - set real addresses)
        self.addresses = {
            "shmon_holders_pool": os.getenv("SHMON_POOL_ADDRESS", "0x..."),
            "brick3_treasury": os.getenv("BRICK3_TREASURY", "0x..."),
            "validator_rewards": os.getenv("VALIDATOR_REWARDS", "0x...")
        }
        
        # Accumulator for batching small profits
        self.accumulator = {
            "total_mon": 0.0,
            "shmon_holders_mon": 0.0,
            "brick3_mon": 0.0,
            "validators_mon": 0.0,
            "sources": []
        }
        
        # Minimum distribution threshold (avoid gas waste)
        self.min_distribution_mon = 10.0
        
        # Statistics
        self.stats = {
            "total_distributed_mon": 0.0,
            "total_distributed_usd": 0.0,
            "distribution_count": 0,
            "last_distribution": None
        }
    
    def calculate_distribution(self, profit_mon: float) -> Dict:
        """
        Calculate revenue distribution for a given profit
        """
        profit_usd = profit_mon * self.mon_price_usd
        
        distribution = {
            "total_profit_mon": round(profit_mon, 6),
            "total_profit_usd": round(profit_usd, 2),
            "breakdown": {}
        }
        
        for recipient, percentage in self.DISTRIBUTION_PERCENTAGES.items():
            amount_mon = profit_mon * percentage
            amount_usd = amount_mon * self.mon_price_usd
            
            distribution["breakdown"][recipient] = {
                "percentage": percentage * 100,
                "amount_mon": round(amount_mon, 6),
                "amount_usd": round(amount_usd, 2)
            }
        
        return distribution
    
    def record_profit(
        self,
        profit_mon: float,
        source_type: str = "mev_execution",
        source_id: str = None
    ) -> RevenueShare:
        """
        Record a profit and calculate distribution
        """
        distribution_id = hashlib.md5(
            f"{datetime.now().isoformat()}{profit_mon}{source_id}".encode()
        ).hexdigest()[:16]
        
        profit_usd = profit_mon * self.mon_price_usd
        
        share = RevenueShare(
            id=distribution_id,
            timestamp=datetime.now().isoformat(),
            total_profit_mon=round(profit_mon, 6),
            total_profit_usd=round(profit_usd, 2),
            shmon_holders_mon=round(profit_mon * 0.70, 6),
            shmon_holders_usd=round(profit_usd * 0.70, 2),
            brick3_mon=round(profit_mon * 0.20, 6),
            brick3_usd=round(profit_usd * 0.20, 2),
            validators_mon=round(profit_mon * 0.10, 6),
            validators_usd=round(profit_usd * 0.10, 2),
            source_type=source_type,
            source_id=source_id or distribution_id,
            status="pending"
        )
        
        # Add to accumulator
        self.accumulator["total_mon"] += profit_mon
        self.accumulator["shmon_holders_mon"] += share.shmon_holders_mon
        self.accumulator["brick3_mon"] += share.brick3_mon
        self.accumulator["validators_mon"] += share.validators_mon
        self.accumulator["sources"].append(source_id)
        
        self.pending_distributions.append(share)
        
        # Check if we should trigger distribution
        if self.accumulator["total_mon"] >= self.min_distribution_mon:
            self._trigger_distribution()
        
        return share
    
    def _trigger_distribution(self):
        """Trigger actual on-chain distribution"""
        if self.accumulator["total_mon"] < self.min_distribution_mon:
            return
        
        # In production: Create and send transactions to distribute funds
        # For now, mark as distributed (simulation)
        
        batch_distribution = RevenueShare(
            id=hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:16],
            timestamp=datetime.now().isoformat(),
            total_profit_mon=self.accumulator["total_mon"],
            total_profit_usd=self.accumulator["total_mon"] * self.mon_price_usd,
            shmon_holders_mon=self.accumulator["shmon_holders_mon"],
            shmon_holders_usd=self.accumulator["shmon_holders_mon"] * self.mon_price_usd,
            brick3_mon=self.accumulator["brick3_mon"],
            brick3_usd=self.accumulator["brick3_mon"] * self.mon_price_usd,
            validators_mon=self.accumulator["validators_mon"],
            validators_usd=self.accumulator["validators_mon"] * self.mon_price_usd,
            source_type="batch",
            source_id=",".join(self.accumulator["sources"][-10:]),  # Last 10 sources
            status="distributed",
            distribution_tx=f"0xdist_{hashlib.md5(str(self.accumulator['total_mon']).encode()).hexdigest()[:12]}"
        )
        
        self.distributions.append(batch_distribution)
        
        # Update stats
        self.stats["total_distributed_mon"] += batch_distribution.total_profit_mon
        self.stats["total_distributed_usd"] += batch_distribution.total_profit_usd
        self.stats["distribution_count"] += 1
        self.stats["last_distribution"] = datetime.now().isoformat()
        
        # Clear pending
        for pending in self.pending_distributions:
            pending.status = "distributed"
            pending.distribution_tx = batch_distribution.distribution_tx
        
        # Reset accumulator
        self.accumulator = {
            "total_mon": 0.0,
            "shmon_holders_mon": 0.0,
            "brick3_mon": 0.0,
            "validators_mon": 0.0,
            "sources": []
        }
    
    def force_distribution(self) -> Optional[RevenueShare]:
        """Force distribution regardless of threshold"""
        if self.accumulator["total_mon"] > 0:
            self._trigger_distribution()
            return self.distributions[-1] if self.distributions else None
        return None
    
    def get_stats(self, period: str = "all_time") -> RevenueStats:
        """Get aggregated statistics for a period"""
        now = datetime.now()
        
        if period == "hourly":
            start_time = now - timedelta(hours=1)
        elif period == "daily":
            start_time = now - timedelta(days=1)
        elif period == "weekly":
            start_time = now - timedelta(weeks=1)
        elif period == "monthly":
            start_time = now - timedelta(days=30)
        else:
            start_time = datetime.min
        
        # Filter distributions in period
        period_distributions = [
            d for d in self.distributions
            if datetime.fromisoformat(d.timestamp) >= start_time
        ]
        
        # Calculate totals
        total_mon = sum(d.total_profit_mon for d in period_distributions)
        shmon_mon = sum(d.shmon_holders_mon for d in period_distributions)
        brick3_mon = sum(d.brick3_mon for d in period_distributions)
        validators_mon = sum(d.validators_mon for d in period_distributions)
        
        # APY calculation
        # Assume $10M TVL in shMON, annualize the period earnings
        tvl_usd = 10_000_000
        if period == "daily":
            annualized_earnings = shmon_mon * self.mon_price_usd * 365
        elif period == "weekly":
            annualized_earnings = shmon_mon * self.mon_price_usd * 52
        elif period == "monthly":
            annualized_earnings = shmon_mon * self.mon_price_usd * 12
        else:
            # All time - assume 30 days of data
            annualized_earnings = shmon_mon * self.mon_price_usd * 12
        
        estimated_apy = (annualized_earnings / tvl_usd) * 100 if tvl_usd > 0 else 0
        
        return RevenueStats(
            period=period,
            start_time=start_time.isoformat(),
            end_time=now.isoformat(),
            total_revenue_mon=round(total_mon, 4),
            total_revenue_usd=round(total_mon * self.mon_price_usd, 2),
            shmon_holders_total_mon=round(shmon_mon, 4),
            shmon_holders_total_usd=round(shmon_mon * self.mon_price_usd, 2),
            brick3_total_mon=round(brick3_mon, 4),
            brick3_total_usd=round(brick3_mon * self.mon_price_usd, 2),
            validators_total_mon=round(validators_mon, 4),
            validators_total_usd=round(validators_mon * self.mon_price_usd, 2),
            distribution_count=len(period_distributions),
            avg_distribution_mon=round(total_mon / len(period_distributions), 4) if period_distributions else 0,
            largest_distribution_mon=max((d.total_profit_mon for d in period_distributions), default=0),
            estimated_apy_boost=round(estimated_apy, 2)
        )
    
    def get_pending_amount(self) -> Dict:
        """Get pending (accumulated but not distributed) amounts"""
        return {
            "pending_total_mon": round(self.accumulator["total_mon"], 6),
            "pending_total_usd": round(self.accumulator["total_mon"] * self.mon_price_usd, 2),
            "pending_breakdown": {
                "shmon_holders": round(self.accumulator["shmon_holders_mon"], 6),
                "brick3": round(self.accumulator["brick3_mon"], 6),
                "validators": round(self.accumulator["validators_mon"], 6)
            },
            "pending_sources_count": len(self.accumulator["sources"]),
            "distribution_threshold_mon": self.min_distribution_mon,
            "ready_for_distribution": self.accumulator["total_mon"] >= self.min_distribution_mon
        }
    
    def get_distribution_history(self, limit: int = 50) -> List[Dict]:
        """Get recent distribution history"""
        return [asdict(d) for d in self.distributions[-limit:]]
    
    def estimate_apy_boost(
        self,
        daily_mev_volume_usd: float,
        tvl_usd: float = 10_000_000
    ) -> Dict:
        """
        Estimate APY boost from MEV earnings
        
        Args:
            daily_mev_volume_usd: Daily MEV capture volume in USD
            tvl_usd: Total Value Locked in shMON
        """
        # shMON holders get 70%
        daily_shmon_earnings = daily_mev_volume_usd * 0.70
        yearly_shmon_earnings = daily_shmon_earnings * 365
        
        apy_boost = (yearly_shmon_earnings / tvl_usd) * 100 if tvl_usd > 0 else 0
        
        return {
            "daily_mev_volume_usd": daily_mev_volume_usd,
            "tvl_usd": tvl_usd,
            "daily_shmon_earnings_usd": round(daily_shmon_earnings, 2),
            "yearly_shmon_earnings_usd": round(yearly_shmon_earnings, 2),
            "estimated_apy_boost_percent": round(apy_boost, 2),
            "note": "APY boost added to base staking rewards"
        }
    
    def get_summary(self) -> Dict:
        """Get complete system summary"""
        all_time = self.get_stats("all_time")
        daily = self.get_stats("daily")
        
        return {
            "distribution_model": {
                "shmon_holders": "70%",
                "brick3": "20%",
                "validators": "10%"
            },
            "all_time_stats": asdict(all_time),
            "daily_stats": asdict(daily),
            "pending": self.get_pending_amount(),
            "system_stats": self.stats,
            "addresses": self.addresses
        }


# Singleton instance
_revenue_system: Optional[RevenueDistributionSystem] = None

def get_revenue_system() -> RevenueDistributionSystem:
    global _revenue_system
    if _revenue_system is None:
        _revenue_system = RevenueDistributionSystem()
    return _revenue_system


if __name__ == "__main__":
    print("💰 Brick3 Revenue Distribution System")
    print("=" * 50)
    
    system = get_revenue_system()
    
    # Simulate some profits
    print("\n📥 Recording profits...")
    system.record_profit(5.0, "mev_execution", "exec_001")
    system.record_profit(8.0, "mev_execution", "exec_002")
    system.record_profit(3.0, "mev_execution", "exec_003")
    
    # Show pending
    pending = system.get_pending_amount()
    print(f"\n⏳ Pending Distribution:")
    print(f"   Total: {pending['pending_total_mon']:.4f} MON (${pending['pending_total_usd']:.2f})")
    print(f"   Ready: {pending['ready_for_distribution']}")
    
    # Force distribution
    print("\n📤 Forcing distribution...")
    dist = system.force_distribution()
    if dist:
        print(f"   Distributed: {dist.total_profit_mon:.4f} MON")
        print(f"   TX: {dist.distribution_tx}")
    
    # Show breakdown
    print("\n📊 Distribution Breakdown:")
    calc = system.calculate_distribution(100)  # 100 MON example
    for recipient, data in calc["breakdown"].items():
        print(f"   {recipient}: {data['percentage']}% = {data['amount_mon']:.2f} MON (${data['amount_usd']:.2f})")
    
    # APY estimate
    print("\n📈 APY Boost Estimate (assuming $10K daily MEV):")
    apy = system.estimate_apy_boost(daily_mev_volume_usd=10000)
    print(f"   Daily shMON Earnings: ${apy['daily_shmon_earnings_usd']:.2f}")
    print(f"   Estimated APY Boost: +{apy['estimated_apy_boost_percent']:.2f}%")
