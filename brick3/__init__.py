# Brick3 - MEV Infrastructure for Virtuals Agents
# Simple 1-line integration for blazing-fast, MEV-protected trading

from .gateway import Gateway, GatewayFactory
from .config import GatewayType, TurboConfig, FlashConfig, FlowConfig
from .mempool import MempoolMonitor, MempoolData, MempoolTransaction
from .transaction import TransactionProtector, ProtectedTransaction
from .utils import (
    validate_address,
    format_wei_to_mon,
    format_mon_to_wei,
    format_gas_gwei,
    calculate_mev_risk_score,
    simulate_mev_protection_savings,
    Emoji,
    print_header
)

__version__ = "1.0.0"
__author__ = "Brick3 Team"
__description__ = "Ultra-fast MEV infrastructure for Virtuals Agents on Monad"

# ========== MAIN API ==========
# Users interact through these exports

# Easy access to gateways
monad_turbo = GatewayFactory.turbo()
monad_flash = GatewayFactory.flash()
monad_flow = GatewayFactory.flow()

# ========== IMPORTS NEEDED BY USERS ==========
__all__ = [
    # Main API
    "Gateway",
    "monad_turbo",
    "monad_flash", 
    "monad_flow",
    "GatewayFactory",
    
    # Configuration
    "GatewayType",
    "TurboConfig",
    "FlashConfig",
    "FlowConfig",
    
    # Mempool
    "MempoolMonitor",
    "MempoolData",
    "MempoolTransaction",
    
    # Transactions
    "TransactionProtector",
    "ProtectedTransaction",
    
    # Utilities
    "validate_address",
    "format_wei_to_mon",
    "format_mon_to_wei",
    "format_gas_gwei",
    "calculate_mev_risk_score",
    "simulate_mev_protection_savings",
    "Emoji",
    "print_header"
]

# Print banner on import
def _print_banner():
    """Print Brick3 banner"""
    try:
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🧱 Brick3 v{__version__} - MEV Infrastructure       ║
║        Ultra-fast execution for Virtuals Agents          ║
║                                                           ║
║  ⚡ 6x Speed     🛡️  15% MEV Savings     ⛽ 80% Gas Cuts   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    except:
        pass

# Print banner on import
_print_banner()
