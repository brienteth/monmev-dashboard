# Brick3 Configuration
from enum import Enum
from typing import Dict, Optional

class NetworkType(Enum):
    """Supported blockchain networks"""
    MONAD_MAINNET = "monad_mainnet"
    MONAD_TESTNET = "monad_testnet"

class GatewayType(Enum):
    """Brick3 Gateway tiers"""
    TURBO = "turbo"      # 6x speed, 15% MEV savings, real-time mempool
    FLASH = "flash"      # 4x speed, 10% MEV savings
    FLOW = "flow"        # 2x speed, 5% MEV savings

class TurboConfig:
    """Configuration for Turbo™ gateway (6x speed, 15% MEV savings)"""
    
    # Network
    CHAIN_ID = 143
    NETWORK_NAME = "Monad"
    RPC_ENDPOINT = "https://rpc.monad.xyz"
    
    # Speed optimizations
    MEMPOOL_POLL_INTERVAL_MS = 100  # 100ms mempool polling for 6x speed
    USE_HTTP3_QUIC = True           # HTTP3/QUIC for faster RPC calls
    BATCH_RPC_SIZE = 50             # Batch RPC calls
    PARALLEL_STREAMS = 4            # 4 parallel streams per connection
    
    # MEV Protection
    FASTLANE_ENABLED = True
    MEV_SAVINGS_PERCENT = 15        # 15% per-trade savings
    SANDWICH_PROTECTION = True
    SLIPPAGE_MONITOR = True
    
    # Real-time data
    MEMPOOL_STREAMING = True
    TRANSACTION_ORDERING = "time_priority"  # Priority-ordered mempool
    DATA_FRESHNESS_MS = 50                  # 50ms data freshness
    
    # Gas optimization
    GAS_OPTIMIZATION = True
    GAS_SAVINGS_PERCENT = 80        # 80% gas reduction through bundling
    SMART_BUNDLING = True
    
    # Infrastructure
    ATLAS_ROUTER = "0xbB010Cb7e71D44d7323aE1C267B333A48D05907C"
    SOLVER_ADDRESSES = {
        "sandwich": "0x64D3607B0E17315019E76C8f98303087Fd59b391",
        "arbitrage": "0x3f7ddef08188A1c50754b5b4E92A37e938c20226",
        "liquidation": "0x48ed7310B00116b08567a59B1cbc072C8e810E3D"
    }
    OPERATIONS_RELAY = "wss://relay-fra.fastlane-labs.xyz/ws/solver"
    
    @classmethod
    def to_dict(cls) -> Dict:
        """Convert config to dictionary"""
        return {
            "chain_id": cls.CHAIN_ID,
            "network": cls.NETWORK_NAME,
            "speed_multiplier": 6,
            "mempool_poll_ms": cls.MEMPOOL_POLL_INTERVAL_MS,
            "mev_savings_percent": cls.MEV_SAVINGS_PERCENT,
            "gas_savings_percent": cls.GAS_SAVINGS_PERCENT,
            "features": {
                "http3_quic": cls.USE_HTTP3_QUIC,
                "fastlane_mev_protection": cls.FASTLANE_ENABLED,
                "mempool_streaming": cls.MEMPOOL_STREAMING,
                "smart_bundling": cls.SMART_BUNDLING
            }
        }

class FlashConfig:
    """Configuration for Flash™ gateway (4x speed, 10% MEV savings)"""
    CHAIN_ID = 143
    NETWORK_NAME = "Monad"
    RPC_ENDPOINT = "https://rpc.monad.xyz"
    MEMPOOL_POLL_INTERVAL_MS = 250
    MEV_SAVINGS_PERCENT = 10
    GAS_SAVINGS_PERCENT = 50
    SPEED_MULTIPLIER = 4
    FASTLANE_ENABLED = True
    USE_HTTP3_QUIC = True
    ATLAS_ROUTER = "0xbB010Cb7e71D44d7323aE1C267B333A48D05907C"
    OPERATIONS_RELAY = "wss://relay-fra.fastlane-labs.xyz/ws/solver"

class FlowConfig:
    """Configuration for Flow™ gateway (2x speed, 5% MEV savings)"""
    CHAIN_ID = 143
    NETWORK_NAME = "Monad"
    RPC_ENDPOINT = "https://rpc.monad.xyz"
    MEMPOOL_POLL_INTERVAL_MS = 500
    MEV_SAVINGS_PERCENT = 5
    GAS_SAVINGS_PERCENT = 20
    SPEED_MULTIPLIER = 2
    FASTLANE_ENABLED = True
    USE_HTTP3_QUIC = True
    ATLAS_ROUTER = "0xbB010Cb7e71D44d7323aE1C267B333A48D05907C"
    OPERATIONS_RELAY = "wss://relay-fra.fastlane-labs.xyz/ws/solver"
