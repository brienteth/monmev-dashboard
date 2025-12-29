"""
🏗️ Brick3 MEV Infrastructure Configuration
OpaMev Altyapısı ile Tam Entegrasyon

Bu modül MonMev/Brick3'i OpaMev'in gelişmiş altyapısına bağlar:
- QUIC Gateway (HTTP/3, ultra-low latency)
- Redis Cache (session, rate limiting, metrics)
- PostgreSQL (persistent storage)
- DAG Mempool (transaction ordering)
- Monad RPC Proxy (local caching)
"""

import os
import redis
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
import json

# ==================== INFRASTRUCTURE CONFIG ====================

class InfrastructureConfig:
    """OpaMev altyapı konfigürasyonu"""
    
    # Local Services (OpaMev Docker Stack)
    QUIC_GATEWAY = os.getenv("QUIC_GATEWAY", "http://localhost:4242")
    DAG_MEMPOOL = os.getenv("DAG_MEMPOOL", "http://localhost:9000")
    H3DAC_RELAY = os.getenv("H3DAC_RELAY", "http://localhost:5001")
    OPACUS_GATEWAY = os.getenv("OPACUS_GATEWAY", "http://localhost:8080")
    
    # Monad RPC (via local proxy for caching)
    MONAD_RPC_LOCAL = os.getenv("MONAD_RPC_LOCAL", "http://localhost:8545")
    MONAD_RPC_REMOTE = os.getenv("MONAD_RPC_REMOTE", "https://rpc.monad.xyz")
    
    # Redis Cache
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # PostgreSQL
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "opamev")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    # Feature Flags
    USE_QUIC = os.getenv("USE_QUIC", "true").lower() == "true"
    USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"
    USE_DAG_MEMPOOL = os.getenv("USE_DAG_MEMPOOL", "true").lower() == "true"
    USE_LOCAL_RPC = os.getenv("USE_LOCAL_RPC", "true").lower() == "true"


# ==================== REDIS CACHE MANAGER ====================

class RedisCache:
    """Redis cache manager for MEV operations"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=InfrastructureConfig.REDIS_HOST,
                    port=InfrastructureConfig.REDIS_PORT,
                    db=InfrastructureConfig.REDIS_DB,
                    decode_responses=True
                )
                self._client.ping()
                print(f"✅ Redis connected: {InfrastructureConfig.REDIS_HOST}:{InfrastructureConfig.REDIS_PORT}")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
                self._client = None
    
    @property
    def connected(self) -> bool:
        try:
            return self._client is not None and self._client.ping()
        except:
            return False
    
    def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Set a cached value with TTL"""
        if not self._client:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self._client.setex(f"brick3:{key}", ttl, value)
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value"""
        if not self._client:
            return None
        try:
            value = self._client.get(f"brick3:{key}")
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except:
            return None
    
    def incr(self, key: str, ttl: int = 3600) -> int:
        """Increment a counter (for rate limiting, metrics)"""
        if not self._client:
            return 0
        try:
            pipe = self._client.pipeline()
            pipe.incr(f"brick3:counter:{key}")
            pipe.expire(f"brick3:counter:{key}", ttl)
            result = pipe.execute()
            return result[0]
        except:
            return 0
    
    def add_to_stream(self, stream: str, data: Dict) -> bool:
        """Add to Redis stream for real-time data"""
        if not self._client:
            return False
        try:
            self._client.xadd(
                f"brick3:stream:{stream}",
                data,
                maxlen=1000  # Keep last 1000 entries
            )
            return True
        except:
            return False
    
    def get_stream(self, stream: str, count: int = 100) -> list:
        """Get recent stream entries"""
        if not self._client:
            return []
        try:
            entries = self._client.xrevrange(
                f"brick3:stream:{stream}",
                count=count
            )
            return entries
        except:
            return []


# ==================== QUIC GATEWAY CLIENT ====================

class QUICGateway:
    """QUIC/HTTP3 Gateway for ultra-low latency operations"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.gateway_url = InfrastructureConfig.QUIC_GATEWAY
        self.enabled = InfrastructureConfig.USE_QUIC
        self._session = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            )
        return self._session
    
    async def health_check(self) -> Dict[str, Any]:
        """Check QUIC gateway health"""
        if not self.enabled:
            return {"status": "disabled", "reason": "QUIC disabled in config"}
        
        try:
            session = await self.get_session()
            async with session.get(f"{self.gateway_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "status": "ok",
                        "gateway": "quic",
                        "uptime": data.get("uptime", 0),
                        "latency_ms": data.get("latency", 0)
                    }
        except Exception as e:
            return {"status": "error", "error": str(e)}
        
        return {"status": "unknown"}
    
    async def submit_bundle(self, bundle: Dict) -> Dict[str, Any]:
        """Submit MEV bundle via QUIC gateway"""
        if not self.enabled:
            return {"success": False, "error": "QUIC disabled"}
        
        try:
            session = await self.get_session()
            async with session.post(
                f"{self.gateway_url}/bundle",
                json=bundle,
                headers={"Content-Type": "application/json"}
            ) as resp:
                return await resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_mempool(self) -> Dict[str, Any]:
        """Get pending transactions from DAG mempool"""
        try:
            session = await self.get_session()
            async with session.get(f"{InfrastructureConfig.DAG_MEMPOOL}/pending") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            return {"error": str(e)}
        return {}


# ==================== LOCAL RPC CLIENT ====================

class LocalRPCClient:
    """Local Monad RPC client with caching"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.local_url = InfrastructureConfig.MONAD_RPC_LOCAL
        self.remote_url = InfrastructureConfig.MONAD_RPC_REMOTE
        self.use_local = InfrastructureConfig.USE_LOCAL_RPC
        self._session = None
        self._cache = RedisCache()
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self._session
    
    def _get_rpc_url(self) -> str:
        return self.local_url if self.use_local else self.remote_url
    
    async def call(self, method: str, params: list = None, cache_ttl: int = 0) -> Dict:
        """Make RPC call with optional caching"""
        if params is None:
            params = []
        
        # Check cache first
        if cache_ttl > 0:
            cache_key = f"rpc:{method}:{hash(str(params))}"
            cached = self._cache.get(cache_key)
            if cached:
                return {"result": cached, "cached": True}
        
        # Make RPC call
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        try:
            session = await self.get_session()
            async with session.post(
                self._get_rpc_url(),
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                data = await resp.json()
                
                # Cache successful results
                if cache_ttl > 0 and "result" in data:
                    self._cache.set(cache_key, data["result"], cache_ttl)
                
                return data
        except Exception as e:
            # Fallback to remote if local fails
            if self.use_local:
                try:
                    async with session.post(
                        self.remote_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as resp:
                        return await resp.json()
                except:
                    pass
            return {"error": str(e)}
    
    async def get_block_number(self) -> int:
        """Get current block number"""
        result = await self.call("eth_blockNumber", cache_ttl=2)
        if "result" in result:
            return int(result["result"], 16)
        return 0
    
    async def get_gas_price(self) -> int:
        """Get current gas price"""
        result = await self.call("eth_gasPrice", cache_ttl=5)
        if "result" in result:
            return int(result["result"], 16)
        return 0
    
    async def health_check(self) -> Dict:
        """Check RPC health"""
        try:
            session = await self.get_session()
            
            # Check local health endpoint
            async with session.get(f"{self.local_url}/health") as resp:
                if resp.status == 200:
                    return await resp.json()
        except:
            pass
        
        # Fallback to block number check
        block = await self.get_block_number()
        return {
            "status": "ok" if block > 0 else "error",
            "block": block,
            "rpc": self._get_rpc_url()
        }


# ==================== METRICS COLLECTOR ====================

class MetricsCollector:
    """Collect and store MEV metrics"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._cache = RedisCache()
        self._metrics = {
            "api_calls": 0,
            "mev_opportunities": 0,
            "bundles_submitted": 0,
            "successful_executions": 0,
            "total_profit_usd": 0.0
        }
    
    def record_api_call(self, endpoint: str, latency_ms: float):
        """Record API call metric"""
        self._cache.incr(f"metrics:api_calls:{endpoint}")
        self._cache.add_to_stream("api_calls", {
            "endpoint": endpoint,
            "latency_ms": str(latency_ms),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def record_mev_opportunity(self, opp_type: str, profit_usd: float):
        """Record MEV opportunity detection"""
        self._cache.incr(f"metrics:mev:{opp_type}")
        self._cache.add_to_stream("mev_opportunities", {
            "type": opp_type,
            "profit_usd": str(profit_usd),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def record_bundle_submission(self, success: bool, latency_ms: float):
        """Record bundle submission"""
        status = "success" if success else "failed"
        self._cache.incr(f"metrics:bundles:{status}")
        self._cache.add_to_stream("bundles", {
            "success": str(success),
            "latency_ms": str(latency_ms),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        return {
            "api_calls_1h": self._cache.get("metrics:api_calls:total") or 0,
            "mev_detected_1h": self._cache.get("metrics:mev:total") or 0,
            "bundles_submitted_1h": self._cache.get("metrics:bundles:total") or 0,
            "success_rate": self._calculate_success_rate(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_success_rate(self) -> float:
        success = int(self._cache.get("metrics:bundles:success") or 0)
        failed = int(self._cache.get("metrics:bundles:failed") or 0)
        total = success + failed
        return (success / total * 100) if total > 0 else 0.0


# ==================== INFRASTRUCTURE STATUS ====================

async def check_infrastructure_status() -> Dict[str, Any]:
    """Check all infrastructure components"""
    
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall": "unknown",
        "services": {}
    }
    
    # Redis
    cache = RedisCache()
    status["services"]["redis"] = {
        "status": "ok" if cache.connected else "error",
        "host": f"{InfrastructureConfig.REDIS_HOST}:{InfrastructureConfig.REDIS_PORT}"
    }
    
    # QUIC Gateway
    quic = QUICGateway()
    quic_status = await quic.health_check()
    status["services"]["quic_gateway"] = quic_status
    
    # Local RPC
    rpc = LocalRPCClient()
    rpc_status = await rpc.health_check()
    status["services"]["monad_rpc"] = rpc_status
    
    # DAG Mempool
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{InfrastructureConfig.DAG_MEMPOOL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status["services"]["dag_mempool"] = {
                        "status": "ok",
                        "uptime": data.get("uptime", 0)
                    }
                else:
                    status["services"]["dag_mempool"] = {"status": "error"}
    except Exception as e:
        status["services"]["dag_mempool"] = {"status": "error", "error": str(e)}
    
    # Calculate overall status
    all_ok = all(
        s.get("status") == "ok" 
        for s in status["services"].values()
    )
    status["overall"] = "ok" if all_ok else "degraded"
    
    return status


# ==================== SINGLETON GETTERS ====================

def get_redis_cache() -> RedisCache:
    """Get Redis cache singleton"""
    return RedisCache()

def get_quic_gateway() -> QUICGateway:
    """Get QUIC gateway singleton"""
    return QUICGateway()

def get_rpc_client() -> LocalRPCClient:
    """Get RPC client singleton"""
    return LocalRPCClient()

def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector singleton"""
    return MetricsCollector()


# ==================== QUICK TEST ====================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("🔧 Infrastructure Test")
        print("=" * 50)
        
        # Test Redis
        cache = get_redis_cache()
        print(f"Redis: {'✅ Connected' if cache.connected else '❌ Disconnected'}")
        
        # Test QUIC
        quic = get_quic_gateway()
        quic_status = await quic.health_check()
        print(f"QUIC Gateway: {quic_status.get('status', 'unknown')}")
        
        # Test RPC
        rpc = get_rpc_client()
        block = await rpc.get_block_number()
        print(f"Monad RPC: Block #{block}")
        
        # Full status
        print("\n📊 Full Infrastructure Status:")
        status = await check_infrastructure_status()
        print(json.dumps(status, indent=2))
    
    asyncio.run(test())
