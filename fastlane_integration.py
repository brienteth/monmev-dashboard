"""
FastLane MEV Protection Integration
Atlas Protocol powered MEV protection for Monad
https://www.fastlane.xyz/
"""

import requests
import json
from typing import Dict, Optional, Any
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

# FastLane Atlas Configuration
FASTLANE_CONFIG = {
    "atlas_router": "0xbB010Cb7e71D44d7323aE1C267B333A48D05907C",
    "auctioneer_url": "https://auctioneer-fra.fastlane-labs.xyz",
    "monad_testnet_chain_id": "0x279f",  # 10143 in hex
    "docs_url": "https://dev.shmonad.xyz/products/mev-protection",
    "shmonad_stake_url": "https://shmonad.xyz/",
    "rpc_policy_url": "https://shmonad.xyz/commit?policy=rpc"
}


class FastLaneClient:
    """
    FastLane MEV Protection Client
    Integrates with Atlas Protocol for MEV protection on Monad
    """
    
    def __init__(
        self,
        refund_recipient: str = None,
        refund_percent: int = 10,
        auctioneer_url: str = None
    ):
        """
        Initialize FastLane client
        
        Args:
            refund_recipient: Address to receive MEV refunds (your protocol address)
            refund_percent: Percentage of MEV to refund (0-90)
            auctioneer_url: FastLane auctioneer endpoint
        """
        self.refund_recipient = refund_recipient or os.getenv(
            "FASTLANE_REFUND_RECIPIENT", 
            "0x0000000000000000000000000000000000000000"
        )
        self.refund_percent = min(max(refund_percent, 0), 90)
        self.auctioneer_url = auctioneer_url or FASTLANE_CONFIG["auctioneer_url"]
        self.atlas_router = FASTLANE_CONFIG["atlas_router"]
        self.chain_id = FASTLANE_CONFIG["monad_testnet_chain_id"]
        
        # Session stats
        self.stats = {
            "requests_sent": 0,
            "successful_protections": 0,
            "total_mev_captured": 0.0,
            "failed_requests": 0
        }
    
    def create_protected_swap(
        self,
        from_address: str,
        to_address: str,
        value: str,
        data: str,
        token_in: str,
        token_out: str,
        amount_in: str,
        amount_out_min: str,
        max_fee_per_gas: str,
        bid_token_is_output: bool = True
    ) -> Dict[str, Any]:
        """
        Create MEV-protected swap transaction via FastLane
        
        Args:
            from_address: User's address
            to_address: DEX router address
            value: Transaction value (hex)
            data: Transaction calldata (hex)
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount (hex)
            amount_out_min: Minimum output amount (hex)
            max_fee_per_gas: Max gas fee (hex)
            bid_token_is_output: Use output token for bidding
            
        Returns:
            Atlas-wrapped transaction ready for signing
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "atlas_sendUnsignedTransaction",
            "params": [{
                "transaction": {
                    "chainId": self.chain_id,
                    "from": from_address,
                    "to": to_address,
                    "value": value,
                    "data": data,
                    "maxFeePerGas": max_fee_per_gas
                },
                "refundRecipient": self.refund_recipient,
                "refundPercent": hex(self.refund_percent),
                "bidTokenIsOutputToken": bid_token_is_output,
                "tokenIn": token_in,
                "tokenOut": token_out,
                "amountIn": amount_in,
                "amountOutMin": amount_out_min
            }],
            "id": 1
        }
        
        try:
            self.stats["requests_sent"] += 1
            
            response = requests.post(
                self.auctioneer_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    self.stats["successful_protections"] += 1
                    return {
                        "success": True,
                        "protected_tx": result["result"],
                        "atlas_router": self.atlas_router
                    }
                elif "error" in result:
                    self.stats["failed_requests"] += 1
                    return {
                        "success": False,
                        "error": result["error"]
                    }
            
            self.stats["failed_requests"] += 1
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
        except requests.exceptions.Timeout:
            self.stats["failed_requests"] += 1
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            self.stats["failed_requests"] += 1
            return {"success": False, "error": str(e)}
    
    def estimate_mev_savings(
        self,
        swap_value_mon: float,
        is_large_swap: bool = False
    ) -> Dict[str, float]:
        """
        Estimate potential MEV savings from protection
        
        Args:
            swap_value_mon: Swap value in MON
            is_large_swap: Whether this is a large swap (>10 MON)
            
        Returns:
            Estimated MEV savings breakdown
        """
        # Typical MEV extraction rates
        if is_large_swap:
            estimated_mev_rate = 0.008  # 0.8% for large swaps
        else:
            estimated_mev_rate = 0.003  # 0.3% for normal swaps
        
        total_mev = swap_value_mon * estimated_mev_rate
        user_refund = total_mev * (1 - self.refund_percent / 100)
        protocol_refund = total_mev * (self.refund_percent / 100)
        
        return {
            "estimated_total_mev": round(total_mev, 6),
            "user_savings": round(user_refund, 6),
            "protocol_revenue": round(protocol_refund, 6),
            "refund_percent": self.refund_percent,
            "swap_value": swap_value_mon
        }
    
    def get_stats(self) -> Dict:
        """Get client statistics"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_protections"] / 
                max(self.stats["requests_sent"], 1) * 100
            )
        }
    
    @staticmethod
    def get_atlas_info() -> Dict:
        """Get Atlas Protocol information"""
        return {
            "name": "FastLane MEV Protection",
            "protocol": "Atlas",
            "features": [
                "Smart contract-based MEV protection",
                "Better pricing via output token bidding",
                "Revenue generation for dApps",
                "Multi-chain support"
            ],
            "contracts": {
                "atlas_router": FASTLANE_CONFIG["atlas_router"],
                "chain_id": FASTLANE_CONFIG["monad_testnet_chain_id"]
            },
            "links": {
                "docs": FASTLANE_CONFIG["docs_url"],
                "stake": FASTLANE_CONFIG["shmonad_stake_url"],
                "rpc_policy": FASTLANE_CONFIG["rpc_policy_url"]
            }
        }


class FastLaneSolver:
    """
    FastLane Solver Integration
    For protocols wanting to participate as solvers in the MEV auction
    """
    
    def __init__(self, solver_address: str, private_key: str = None):
        self.solver_address = solver_address
        self.private_key = private_key
        self.w3 = Web3(Web3.HTTPProvider(
            os.getenv("MONAD_RPC", "https://testnet-rpc.monad.xyz")
        ))
    
    def calculate_bid(
        self,
        opportunity: Dict,
        gas_price_gwei: float
    ) -> Dict:
        """
        Calculate optimal bid for an MEV opportunity
        
        Args:
            opportunity: MEV opportunity details
            gas_price_gwei: Current gas price
            
        Returns:
            Bid calculation
        """
        estimated_profit = opportunity.get("estimated_profit", 0)
        value_mon = opportunity.get("value_mon", 0)
        
        # Conservative bid: 70% of estimated profit
        bid_amount = estimated_profit * 0.7
        
        # Gas cost estimation
        gas_limit = 300000  # Typical swap + backrun
        gas_cost_mon = (gas_price_gwei * gas_limit) / 1e9
        
        net_profit = bid_amount - gas_cost_mon
        
        return {
            "opportunity_hash": opportunity.get("hash"),
            "estimated_profit": estimated_profit,
            "bid_amount": round(bid_amount, 6),
            "gas_cost": round(gas_cost_mon, 6),
            "net_profit": round(net_profit, 6),
            "profitable": net_profit > 0,
            "bid_percent_of_mev": round(bid_amount / max(estimated_profit, 0.0001) * 100, 2)
        }
    
    def submit_solver_bid(self, bid: Dict) -> Dict:
        """Submit a bid to the FastLane auction"""
        # TODO: Implement actual solver bid submission
        # This requires solver registration with FastLane
        return {
            "success": False,
            "message": "Solver bid submission requires FastLane solver registration",
            "registration_url": "https://discord.fastlane.xyz/"
        }


class ShMonadIntegration:
    """
    shMONAD Liquid Staking Integration
    Stake MON and earn yield from staking + MEV
    """
    
    SHMONAD_URL = "https://shmonad.xyz/"
    
    @staticmethod
    def get_staking_info() -> Dict:
        """Get shMONAD staking information"""
        return {
            "name": "shMONAD",
            "description": "Liquid Staking Token for Monad",
            "features": [
                "Staking rewards",
                "MEV yield sharing",
                "Gas payment support",
                "Restaking enabled"
            ],
            "yield_channels": [
                "Staking",
                "Paymaster fees",
                "Clearing House",
                "Task Manager",
                "FastLane RPC",
                "Atlas Protocol MEV"
            ],
            "stake_url": "https://shmonad.xyz/",
            "docs_url": "https://dev.shmonad.xyz/products/shmonad/overview"
        }
    
    @staticmethod
    def estimate_total_apy(
        base_staking_apy: float = 8.0,
        mev_boost_apy: float = 0.5
    ) -> Dict:
        """
        Estimate total APY from shMONAD staking
        
        Args:
            base_staking_apy: Base staking APY (%)
            mev_boost_apy: Additional MEV yield (%)
            
        Returns:
            APY breakdown
        """
        return {
            "base_staking_apy": base_staking_apy,
            "mev_boost_apy": mev_boost_apy,
            "total_apy": base_staking_apy + mev_boost_apy,
            "note": "Actual APY varies based on network activity and MEV opportunities"
        }


# Convenience functions
def create_fastlane_client(refund_percent: int = 10) -> FastLaneClient:
    """Create a FastLane client with default settings"""
    return FastLaneClient(refund_percent=refund_percent)


def get_mev_protection_quote(swap_value: float) -> Dict:
    """Quick quote for MEV protection savings"""
    client = FastLaneClient()
    return client.estimate_mev_savings(swap_value, is_large_swap=swap_value > 10)


# CLI
if __name__ == "__main__":
    print("🚀 FastLane MEV Protection Integration")
    print("=" * 50)
    
    # Show Atlas info
    info = FastLaneClient.get_atlas_info()
    print(f"\n📋 {info['name']}")
    print(f"Protocol: {info['protocol']}")
    print("\nFeatures:")
    for feature in info["features"]:
        print(f"  • {feature}")
    
    print(f"\n🔗 Atlas Router: {info['contracts']['atlas_router']}")
    
    # Example MEV savings estimate
    print("\n💰 MEV Savings Estimate (100 MON swap):")
    estimate = get_mev_protection_quote(100)
    print(f"  Total MEV: {estimate['estimated_total_mev']} MON")
    print(f"  User Savings: {estimate['user_savings']} MON")
    print(f"  Protocol Revenue: {estimate['protocol_revenue']} MON")
    
    # shMONAD info
    print("\n🏦 shMONAD Staking:")
    shmonad = ShMonadIntegration.get_staking_info()
    print(f"  Stake URL: {shmonad['stake_url']}")
    apy = ShMonadIntegration.estimate_total_apy()
    print(f"  Estimated APY: {apy['total_apy']}%")
