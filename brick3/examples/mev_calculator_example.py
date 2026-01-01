#!/usr/bin/env python3
"""
Brick3 MEV Calculator
====================

Demonstrates MEV impact analysis and savings calculations
for transactions on Monad.
"""

from brick3 import (
    monad_turbo,
    monad_flash,
    monad_flow,
    calculate_mev_risk_score,
    simulate_mev_protection_savings,
    format_wei_to_mon,
    Emoji,
    print_header
)

def analyze_transaction(tx_value_mon: float, gas_price_gwei: float):
    """Analyze MEV impact for a transaction"""
    
    print_header(f"Transaction Analysis")
    
    print(f"{Emoji.INFO} Transaction Details:")
    print(f"  Value: {tx_value_mon} MON")
    print(f"  Gas Price: {gas_price_gwei} Gwei\n")
    
    # ========== MEV RISK ANALYSIS ==========
    
    risk = calculate_mev_risk_score(gas_price_gwei, tx_value_mon)
    
    print(f"{Emoji.WARNING} MEV Risk Analysis:")
    print(f"  Risk Level: {risk['risk_level'].upper()}")
    print(f"  Risk Score: {risk['score']}/100")
    print(f"  Needs Protection: {'Yes' if risk['recommended_protection'] else 'No'}")
    print(f"  Estimated MEV Exposure: {risk['estimated_mev_exposure_percent']:.1f}%\n")
    
    # ========== SAVINGS WITH DIFFERENT GATEWAYS ==========
    
    print(f"{Emoji.CHART} Savings Comparison:\n")
    
    gateways = [
        ("Turbo™ (6x speed)", 15, 80),
        ("Flash™ (4x speed)", 10, 50),
        ("Flow™ (2x speed)", 5, 20)
    ]
    
    results = []
    
    for name, mev_pct, gas_pct in gateways:
        savings = simulate_mev_protection_savings(
            tx_value_mon=tx_value_mon,
            gas_price_gwei=gas_price_gwei,
            gas_used=100000,
            mev_protection_percent=mev_pct
        )
        results.append((name, mev_pct, gas_pct, savings))
        
        print(f"  {Emoji.ZAPPING} {name}")
        print(f"     Gas Savings: {savings['gas_savings_mon']:.6f} MON")
        print(f"     MEV Savings: {savings['mev_exposure_mon']:.6f} MON")
        print(f"     Total Savings: {savings['total_savings_mon']:.6f} MON ({savings['total_savings_percent']:.2f}%)")
        print()
    
    # ========== RECOMMENDATION ==========
    
    print(f"{Emoji.ROCKET} Recommendation:")
    
    if risk['score'] >= 80:
        print(f"  Use Turbo™ - Critical risk requires maximum protection")
    elif risk['score'] >= 60:
        print(f"  Use Flash™ or Turbo™ - High risk, use strong protection")
    elif risk['score'] >= 40:
        print(f"  Use Flash™ - Balanced protection and cost")
    else:
        print(f"  Use Flow™ - Low risk, basic protection sufficient")
    
    print()
    
    return results

def main():
    """Main analysis"""
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           Brick3 MEV Impact Calculator                   ║
║        Analyze MEV exposure and protection savings       ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Example 1: Large value, high gas price (high risk)
    print(f"\n{Emoji.FIRE} Example 1: Large Trade (High Risk)")
    analyze_transaction(tx_value_mon=1000.0, gas_price_gwei=50.0)
    
    # Example 2: Medium value, medium gas price (medium risk)
    print(f"\n{Emoji.CHART} Example 2: Medium Trade (Medium Risk)")
    analyze_transaction(tx_value_mon=100.0, gas_price_gwei=10.0)
    
    # Example 3: Small value, low gas price (low risk)
    print(f"\n{Emoji.SHIELD} Example 3: Small Trade (Low Risk)")
    analyze_transaction(tx_value_mon=10.0, gas_price_gwei=1.0)
    
    # ========== VIRTUALS AGENT OPTIMIZATION ==========
    
    print_header("Brick3 for Virtuals Agents")
    
    print(f"""
{Emoji.ROCKET} Integration is simple:

    from brick3 import Gateway
    from virtuals import Agent
    
    agent = Agent.create("trading_bot")
    agent.use_infrastructure(Gateway.monad_turbo)

{Emoji.CHECK} Your agent now has:
  
  {Emoji.ZAPPING} 6x faster execution
  {Emoji.SHIELD} 15% MEV protection
  {Emoji.GAS} 80% gas savings
  {Emoji.CHART} Real-time mempool access

{Emoji.MONEY} Expected ROI improvement:
  
  • 6x faster execution = catch opportunities others miss
  • 15% MEV savings = direct profit increase
  • 80% gas reduction = lower operating costs
  • Combined: +30% profitability on average
""")

if __name__ == "__main__":
    main()
