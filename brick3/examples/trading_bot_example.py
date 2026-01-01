#!/usr/bin/env python3
"""
Brick3 + Virtuals: Simple Trading Bot Example
==============================================

Demonstrates a complete trading bot using Brick3 for:
- Ultra-fast execution (6x speed)
- MEV protection (15% savings)
- Real-time mempool monitoring
- Automatic opportunity detection

This is production-ready code for Virtuals agents.
"""

import asyncio
from brick3 import (
    monad_turbo,
    calculate_mev_risk_score,
    simulate_mev_protection_savings,
    Emoji
)

class SimpleArbitrageBot:
    """
    Simple arbitrage bot using Brick3
    
    Monitors mempool for profitable opportunities and executes
    MEV-protected swaps through FastLane infrastructure.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.gateway = monad_turbo
        self.total_trades = 0
        self.total_savings = 0.0
        self.opportunities_found = 0
    
    async def start(self):
        """Start the trading bot"""
        print(f"\n{'='*60}")
        print(f" 🤖 {self.name} Trading Bot")
        print(f"{'='*60}\n")
        
        # Initialize Brick3
        await self.gateway.initialize()
        
        print(f"{Emoji.ROCKET} Bot started!")
        print(f"{Emoji.CHART} Monitoring mempool for opportunities...\n")
        
        # Start mempool monitoring with callback
        await self.gateway.subscribe_to_mempool(self.on_new_transaction)
    
    async def on_new_transaction(self, tx):
        """Handle new mempool transaction"""
        
        # Analyze transaction
        risk_score = calculate_mev_risk_score(
            gas_price_gwei=float(tx.gas_price) / 1e9,
            tx_value_mon=float(tx.value) / 1e18
        )
        
        # Check if worth trading
        if risk_score['recommended_protection'] and tx.profit_opportunity:
            self.opportunities_found += 1
            
            print(f"\n{Emoji.FIRE} Opportunity Detected!")
            print(f"  Tx: {tx.hash[:16]}...")
            print(f"  Risk: {risk_score['risk_level']} (score: {risk_score['score']})")
            print(f"  Potential profit: {tx.profit_opportunity:.6f} MON")
            
            # Execute trade with MEV protection
            await self.execute_trade(tx)
    
    async def execute_trade(self, mempool_tx):
        """Execute trade with MEV protection"""
        
        self.total_trades += 1
        
        print(f"\n  {Emoji.ZAPPING} Executing MEV-protected trade...")
        
        # Submit protected transaction
        tx = self.gateway.submit_protected_transaction(
            to_address=mempool_tx.to_address or "0x0000000000000000000000000000000000000000",
            value=mempool_tx.value,
            gas_limit=200000,
            gas_price=mempool_tx.gas_price
        )
        
        # Calculate savings
        savings = self.gateway.estimate_transaction_savings(tx)
        
        mev_saved = savings['mev_savings_wei'] / 1e18
        gas_saved = savings['gas_savings_wei'] / 1e18
        total_saved = (savings['mev_savings_wei'] + savings['gas_savings_wei']) / 1e18
        
        self.total_savings += total_saved
        
        print(f"  {Emoji.LOCK} Protected with MEV bundle")
        print(f"  {Emoji.MONEY} MEV savings: {mev_saved:.6f} MON")
        print(f"  {Emoji.GAS} Gas savings: {gas_saved:.6f} MON")
        print(f"  {Emoji.CHART} Total savings: {total_saved:.6f} MON")
        print(f"  {Emoji.CHECK} Trade #{self.total_trades} submitted\n")
    
    def print_stats(self):
        """Print bot statistics"""
        print(f"\n{'='*60}")
        print(f" 📊 Bot Statistics")
        print(f"{'='*60}")
        print(f"  {Emoji.CHART} Total trades: {self.total_trades}")
        print(f"  {Emoji.FIRE} Opportunities found: {self.opportunities_found}")
        print(f"  {Emoji.MONEY} Total savings: {self.total_savings:.6f} MON")
        if self.total_trades > 0:
            print(f"  {Emoji.CHART} Avg savings per trade: {self.total_savings / self.total_trades:.6f} MON")
        print(f"{'='*60}\n")

async def main():
    """Run the trading bot"""
    
    # Create bot
    bot = SimpleArbitrageBot("Brick3 Arbitrage Bot")
    
    # Start bot
    try:
        await bot.start()
        
        # Run for demonstration
        await asyncio.sleep(5)
        
        # Print stats
        bot.print_stats()
        
    except KeyboardInterrupt:
        print(f"\n{Emoji.CHECK} Bot stopped")
        bot.print_stats()

if __name__ == "__main__":
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║     Brick3 + Virtuals: Arbitrage Bot Example             ║
║     Ultra-fast MEV-protected trading on Monad            ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    asyncio.run(main())
