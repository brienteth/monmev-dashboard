# Virtuals Agent Integration - Middleware for use_infrastructure()
# Seamlessly extends Virtuals Agent with Brick3 capabilities

from typing import Optional, Callable, Dict, Any
from brick3.gateway import Gateway
from brick3.config import GatewayType

class VirtualsAgentAdapter:
    """
    Adapter for Virtuals Agent to use Brick3 infrastructure
    
    This allows:
        agent.use_infrastructure(Gateway.monad_turbo)
    
    And automatically enhances the agent with:
    - 6x faster execution
    - MEV protection
    - Real-time mempool data
    - Smart bundling for 80% gas savings
    """
    
    def __init__(self, agent):
        self.agent = agent
        self.gateway: Optional[Gateway] = None
        self.is_enhanced = False
    
    def attach_gateway(self, gateway: Gateway):
        """
        Attach a Brick3 gateway to the agent
        
        Usage:
            adapter = VirtualsAgentAdapter(agent)
            adapter.attach_gateway(Gateway.monad_turbo)
        """
        self.gateway = gateway
        print(f"✅ Attached {gateway.gateway_type.value.upper()} gateway to agent")
        print(f"   📊 Speed: {gateway.speed_multiplier}x faster")
        print(f"   🛡️  MEV: {gateway.mev_savings}% savings")
        print(f"   ⛽ Gas: {gateway.gas_savings}% reduction")
        
        # Enhance agent with Brick3 methods
        self._enhance_agent()
        self.is_enhanced = True
    
    def _enhance_agent(self):
        """Add Brick3 methods to agent"""
        if not self.gateway:
            return
        
        # Add mempool data access
        self.agent.mempool = self.gateway.mempool_data
        self.agent.pending_transactions = self.gateway.pending_transactions
        self.agent.opportunities = self.gateway.opportunities
        
        # Add transaction submission
        self.agent.submit_protected_transaction = self._create_submit_wrapper()
        
        # Add metrics
        self.agent.get_brick3_metrics = self.gateway.get_metrics
        
        # Add mempool subscription
        self.agent.subscribe_to_mempool = self._create_subscribe_wrapper()
    
    def _create_submit_wrapper(self) -> Callable:
        """Create wrapped transaction submission method"""
        async def submit(
            to_address: str,
            value: str,
            gas_limit: int = 21000,
            gas_price: str = "1000000000",
            data: Optional[str] = None
        ):
            """
            Submit MEV-protected transaction via Brick3
            
            Usage:
                tx = await agent.submit_protected_transaction(
                    to_address="0x...",
                    value="1000000000000000000"
                )
            """
            tx = self.gateway.submit_protected_transaction(
                to_address=to_address,
                value=value,
                gas_limit=gas_limit,
                gas_price=gas_price,
                data=data
            )
            
            # Enhanced logging
            savings = self.gateway.estimate_transaction_savings(tx)
            print(f"📤 Transaction submitted with MEV protection:")
            print(f"   💾 MEV Savings: {savings['mev_savings_wei'] / 1e18:.4f} MON")
            print(f"   ⛽ Gas Savings: {savings['gas_savings_wei'] / 1e18:.4f} MON")
            print(f"   💰 Total Savings: {savings['total_savings_wei'] / 1e18:.4f} MON ({savings['total_savings_percent']:.1f}%)")
            
            return tx
        
        return submit
    
    def _create_subscribe_wrapper(self) -> Callable:
        """Create wrapped mempool subscription"""
        async def subscribe(callback: Callable):
            """
            Subscribe to real-time mempool updates
            
            Usage:
                async def on_opportunity(tx):
                    print(f"Opportunity: {tx.hash}")
                
                await agent.subscribe_to_mempool(on_opportunity)
            """
            await self.gateway.subscribe_to_mempool(callback)
        
        return subscribe

# ========== MONKEY-PATCH VIRTUALS AGENT ==========
# This allows: agent.use_infrastructure(Gateway.monad_turbo)

def patch_virtuals_agent():
    """
    Patch Virtuals Agent class to support use_infrastructure()
    
    Call this once at startup:
        from brick3.virtuals_integration import patch_virtuals_agent
        patch_virtuals_agent()
    """
    try:
        from virtuals import Agent
        
        # Store original __init__
        original_init = Agent.__init__
        
        def enhanced_init(self, *args, **kwargs):
            """Enhanced Agent init with Brick3 support"""
            original_init(self, *args, **kwargs)
            self._brick3_adapter = None
        
        def use_infrastructure(self, gateway: Gateway):
            """
            Use Brick3 infrastructure for fast execution and MEV protection
            
            Usage:
                agent = Agent.create("trading_bot")
                agent.use_infrastructure(Gateway.monad_turbo)
                
                # Now agent has:
                # - 6x faster execution
                # - MEV protection (15% savings)
                # - Real-time mempool data
                # - 80% gas savings
            """
            if self._brick3_adapter is None:
                self._brick3_adapter = VirtualsAgentAdapter(self)
            
            self._brick3_adapter.attach_gateway(gateway)
            return self
        
        # Apply patches
        Agent.__init__ = enhanced_init
        Agent.use_infrastructure = use_infrastructure
        
        print("✅ Virtuals Agent patched with Brick3 support")
        
    except ImportError:
        print("⚠️  Virtuals library not found. Install with: pip install virtuals")
    except Exception as e:
        print(f"❌ Failed to patch Virtuals Agent: {e}")

# Alternative: Wrapper class (if monkey-patching not preferred)
class VirtualsAgentWithBrick3:
    """
    Wrapper for Virtuals Agent with Brick3 infrastructure
    
    Usage:
        agent = VirtualsAgentWithBrick3.create("trading_bot")
        agent.use_infrastructure(Gateway.monad_turbo)
    """
    
    def __init__(self, agent):
        self.agent = agent
        self._adapter = VirtualsAgentAdapter(agent)
    
    def use_infrastructure(self, gateway: Gateway):
        """Attach Brick3 gateway"""
        self._adapter.attach_gateway(gateway)
        return self.agent
    
    def __getattr__(self, name):
        """Delegate to wrapped agent"""
        return getattr(self.agent, name)
    
    @classmethod
    def create(cls, name: str, **kwargs):
        """Create new Virtuals agent with Brick3"""
        try:
            from virtuals import Agent
            agent = Agent.create(name, **kwargs)
            return cls(agent)
        except Exception as e:
            print(f"❌ Failed to create agent: {e}")
            return None
