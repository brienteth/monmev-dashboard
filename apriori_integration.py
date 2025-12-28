"""
Brick3 + aPriori Integration Module
Validator MEV yield optimization for Monad stakers
Version: 0.1
"""

import requests
from web3 import Web3
import time
import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class Brick3APrioriIntegration:
    """
    Brick3 MEV verilerini aPriori validator'larına bağlar.
    Staker'lar için MEV yield boost hesaplar ve fırsatları relay eder.
    """
    
    def __init__(
        self,
        brick3_api_key: str,
        apriori_validator_address: str,
        brick3_api_url: str = "http://localhost:8000",
        monad_rpc: str = None
    ):
        self.brick3_api = brick3_api_url
        self.api_key = brick3_api_key
        self.validator = apriori_validator_address
        
        # Web3 bağlantısı
        rpc_url = monad_rpc or os.getenv("MONAD_RPC", "https://testnet-rpc.monad.xyz")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
        
        # aPriori contract adresleri (mainnet için güncelle)
        self.apriori_contracts = {
            "staking": os.getenv("APRIORI_STAKING_CONTRACT", "0x0000000000000000000000000000000000000000"),
            "apr_mon": os.getenv("APRIORI_APRMON_CONTRACT", "0x0000000000000000000000000000000000000000"),
            "relay": os.getenv("APRIORI_RELAY_URL", "https://relay.apriori.xyz")
        }
        
        # Session stats
        self.session_stats = {
            "opportunities_processed": 0,
            "total_profit_submitted": 0.0,
            "successful_submissions": 0,
            "failed_submissions": 0,
            "session_start": datetime.now().isoformat()
        }
        
        # Caching
        self._last_fetch_time = 0
        self._cached_opportunities = []
        self._cache_ttl = 5  # seconds
    
    def is_connected(self) -> bool:
        """RPC bağlantı durumu"""
        try:
            return self.w3.is_connected()
        except:
            return False
    
    def get_current_block(self) -> Optional[int]:
        """Mevcut blok numarası"""
        try:
            return self.w3.eth.block_number
        except:
            return None
    
    def fetch_mev_opportunities(
        self,
        min_profit: float = 0.1,
        mev_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Brick3 API'den MEV fırsatlarını çek
        
        Args:
            min_profit: Minimum profit filtresi (MON)
            mev_type: MEV türü filtresi
            limit: Maksimum sonuç sayısı
            
        Returns:
            MEV opportunity listesi
        """
        # Cache kontrolü
        current_time = time.time()
        if current_time - self._last_fetch_time < self._cache_ttl:
            return self._cached_opportunities
        
        try:
            headers = {"api-key": self.api_key}
            params = {
                "min_profit": min_profit,
                "limit": limit
            }
            
            if mev_type:
                params["mev_type"] = mev_type
            
            response = requests.get(
                f"{self.brick3_api}/api/v1/opportunities",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get("opportunities", [])
                
                # Cache güncelle
                self._cached_opportunities = opportunities
                self._last_fetch_time = current_time
                
                return opportunities
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            print("API timeout - using cached data")
            return self._cached_opportunities
        except Exception as e:
            print(f"Fetch error: {e}")
            return []
    
    def get_api_stats(self) -> Optional[Dict]:
        """Brick3 API istatistiklerini al"""
        try:
            headers = {"api-key": self.api_key}
            response = requests.get(
                f"{self.brick3_api}/api/v1/stats",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_total_staked(self) -> float:
        """
        aPriori total staked MON miktarını al
        Production'da contract'tan çekilmeli
        """
        # TODO: Gerçek contract call
        # Örnek: self.w3.eth.call() ile aprMON total supply
        
        # Mock data - production'da contract'tan al
        return 1_000_000.0  # 1M MON
    
    def get_validator_stake(self) -> float:
        """Validator'ın stake miktarını al"""
        # TODO: Contract call
        return 50_000.0  # 50K MON (örnek)
    
    def calculate_validator_boost(
        self,
        opportunities: List[Dict],
        time_window_hours: int = 24
    ) -> Dict:
        """
        Validator için MEV APY boost hesapla
        
        Args:
            opportunities: MEV opportunity listesi
            time_window_hours: Hesaplama için zaman penceresi
            
        Returns:
            APY boost metrikleri
        """
        if not opportunities:
            return {
                "daily_mev_profit": 0.0,
                "annual_boost_pct": 0.0,
                "opportunities_count": 0,
                "avg_profit_per_opp": 0.0,
                "validator_share": 0.0
            }
        
        # Toplam profit
        total_profit = sum(opp.get("estimated_profit", 0) for opp in opportunities)
        
        # Total staked
        total_staked = self.get_total_staked()
        validator_stake = self.get_validator_stake()
        
        # Validator'ın payı (stake oranına göre)
        validator_ratio = validator_stake / total_staked if total_staked > 0 else 0
        validator_mev_share = total_profit * validator_ratio
        
        # Günlük ve yıllık projeksiyon
        # Fırsatlar belirli bir zaman diliminden geliyorsa normalize et
        hours_factor = 24 / time_window_hours
        daily_mev_profit = total_profit * hours_factor
        
        # Annual boost (günlük profit * 365 / total stake)
        annual_mev_yield = (daily_mev_profit * 365) / total_staked if total_staked > 0 else 0
        
        return {
            "daily_mev_profit": round(daily_mev_profit, 4),
            "annual_boost_pct": round(annual_mev_yield * 100, 4),
            "opportunities_count": len(opportunities),
            "avg_profit_per_opp": round(total_profit / len(opportunities), 4),
            "validator_share": round(validator_mev_share, 4),
            "total_staked": total_staked,
            "validator_stake": validator_stake,
            "validator_ratio_pct": round(validator_ratio * 100, 2)
        }
    
    def prioritize_opportunities(
        self,
        opportunities: List[Dict],
        top_n: int = 10
    ) -> List[Dict]:
        """
        En karlı fırsatları önceliklendir
        
        Args:
            opportunities: Tüm fırsatlar
            top_n: Seçilecek fırsat sayısı
            
        Returns:
            Önceliklendirilmiş fırsat listesi
        """
        if not opportunities:
            return []
        
        # Profit/value oranına göre sırala (efficiency)
        def efficiency_score(opp):
            value = opp.get("value_mon", 1)
            profit = opp.get("estimated_profit", 0)
            # Sandwich type bonus
            type_bonus = 1.5 if "Sandwich" in opp.get("mev_type", "") else 1.0
            return (profit / value) * type_bonus if value > 0 else 0
        
        sorted_opps = sorted(opportunities, key=efficiency_score, reverse=True)
        return sorted_opps[:top_n]
    
    def submit_to_relay(self, opportunity: Dict) -> Dict:
        """
        Fırsatı aPriori relay'ine gönder (backrun için)
        
        Args:
            opportunity: Gönderilecek MEV fırsatı
            
        Returns:
            Submission sonucu
        """
        payload = {
            "validator": self.validator,
            "tx_hash": opportunity.get("hash"),
            "estimated_profit": opportunity.get("estimated_profit"),
            "mev_type": opportunity.get("mev_type"),
            "value_mon": opportunity.get("value_mon"),
            "block": opportunity.get("block"),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # TODO: Gerçek aPriori relay endpoint'i
            # response = requests.post(
            #     f"{self.apriori_contracts['relay']}/submit",
            #     json=payload,
            #     timeout=5
            # )
            
            # Mock response - production'da gerçek API call
            print(f"📤 Submitting to relay: {opportunity.get('hash')[:16]}...")
            
            self.session_stats["opportunities_processed"] += 1
            self.session_stats["total_profit_submitted"] += opportunity.get("estimated_profit", 0)
            self.session_stats["successful_submissions"] += 1
            
            return {
                "success": True,
                "message": "Submitted to relay",
                "tx_hash": opportunity.get("hash"),
                "profit": opportunity.get("estimated_profit")
            }
            
        except Exception as e:
            self.session_stats["failed_submissions"] += 1
            return {
                "success": False,
                "error": str(e),
                "tx_hash": opportunity.get("hash")
            }
    
    def get_session_stats(self) -> Dict:
        """Mevcut session istatistikleri"""
        return {
            **self.session_stats,
            "session_duration": str(
                datetime.now() - datetime.fromisoformat(self.session_stats["session_start"])
            ),
            "success_rate": (
                self.session_stats["successful_submissions"] / 
                max(self.session_stats["opportunities_processed"], 1) * 100
            )
        }
    
    def run_monitoring_loop(
        self,
        min_profit: float = 0.1,
        check_interval: int = 10,
        auto_submit: bool = False
    ):
        """
        Ana monitoring loop
        
        Args:
            min_profit: Minimum profit filtresi
            check_interval: Kontrol aralığı (saniye)
            auto_submit: Otomatik relay submission
        """
        print(f"""
        ╔══════════════════════════════════════════════════════════╗
        ║   🧱 Brick3 + aPriori Integration Started                ║
        ║   Validator: {self.validator[:20]}...                    ║
        ║   Min Profit: {min_profit} MON                           ║
        ║   Auto Submit: {auto_submit}                             ║
        ╚══════════════════════════════════════════════════════════╝
        """)
        
        while True:
            try:
                # RPC durumu
                if not self.is_connected():
                    print("⚠️ RPC disconnected, retrying...")
                    time.sleep(check_interval)
                    continue
                
                current_block = self.get_current_block()
                print(f"\n📦 Block: {current_block}")
                
                # Fırsatları çek
                opportunities = self.fetch_mev_opportunities(min_profit=min_profit)
                
                if opportunities:
                    print(f"🔍 Found {len(opportunities)} opportunities")
                    
                    # En iyi fırsatları seç
                    top_opps = self.prioritize_opportunities(opportunities, top_n=5)
                    
                    # APY boost hesapla
                    boost = self.calculate_validator_boost(opportunities)
                    print(f"📈 Estimated APY Boost: +{boost['annual_boost_pct']}%")
                    print(f"💰 Daily MEV Profit: {boost['daily_mev_profit']} MON")
                    
                    # En iyi fırsatları göster
                    print("\n🏆 Top Opportunities:")
                    for i, opp in enumerate(top_opps[:3], 1):
                        print(f"   {i}. {opp['mev_type']} - "
                              f"Profit: {opp['estimated_profit']} MON - "
                              f"Value: {opp['value_mon']} MON")
                    
                    # Auto submit aktifse relay'e gönder
                    if auto_submit and top_opps:
                        best_opp = top_opps[0]
                        result = self.submit_to_relay(best_opp)
                        if result["success"]:
                            print(f"✅ Submitted: {result['tx_hash'][:16]}...")
                        else:
                            print(f"❌ Submit failed: {result.get('error')}")
                else:
                    print("😴 No profitable opportunities found")
                
                # Session stats
                stats = self.get_session_stats()
                print(f"📊 Session: {stats['opportunities_processed']} processed, "
                      f"{stats['total_profit_submitted']:.4f} MON submitted")
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(check_interval * 2)
    
    async def async_monitoring_loop(
        self,
        min_profit: float = 0.1,
        check_interval: int = 10
    ):
        """Async monitoring loop"""
        print(f"🚀 Async monitoring started for validator: {self.validator[:20]}...")
        
        while True:
            try:
                opportunities = self.fetch_mev_opportunities(min_profit=min_profit)
                
                if opportunities:
                    boost = self.calculate_validator_boost(opportunities)
                    yield {
                        "opportunities": opportunities[:10],
                        "boost": boost,
                        "timestamp": datetime.now().isoformat()
                    }
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"Async error: {e}")
                await asyncio.sleep(check_interval * 2)


class MEVYieldCalculator:
    """
    Staker'lar için MEV yield hesaplayıcı
    """
    
    def __init__(self, base_apy: float = 8.0):
        """
        Args:
            base_apy: Temel staking APY (%)
        """
        self.base_apy = base_apy
    
    def calculate_total_yield(
        self,
        stake_amount: float,
        mev_boost_pct: float,
        duration_days: int = 365
    ) -> Dict:
        """
        Toplam yield hesapla
        
        Args:
            stake_amount: Stake edilen MON miktarı
            mev_boost_pct: MEV APY boost yüzdesi
            duration_days: Stake süresi (gün)
            
        Returns:
            Detaylı yield hesaplaması
        """
        total_apy = self.base_apy + mev_boost_pct
        
        # Compound calculation
        daily_rate = total_apy / 365 / 100
        base_daily_rate = self.base_apy / 365 / 100
        
        # Final amounts
        final_with_mev = stake_amount * ((1 + daily_rate) ** duration_days)
        final_base_only = stake_amount * ((1 + base_daily_rate) ** duration_days)
        
        return {
            "stake_amount": stake_amount,
            "duration_days": duration_days,
            "base_apy": self.base_apy,
            "mev_boost_apy": mev_boost_pct,
            "total_apy": round(total_apy, 2),
            "final_amount_with_mev": round(final_with_mev, 4),
            "final_amount_base_only": round(final_base_only, 4),
            "mev_bonus_mon": round(final_with_mev - final_base_only, 4),
            "total_profit_mon": round(final_with_mev - stake_amount, 4)
        }


# ==================== CLI INTERFACE ====================

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Brick3 + aPriori Integration")
    parser.add_argument("--api-key", default=os.getenv("BRICK3_API_KEY", "demo_key_123"),
                       help="Brick3 API key")
    parser.add_argument("--validator", default=os.getenv("APRIORI_VALIDATOR_ADDRESS", "0x0000"),
                       help="Validator address")
    parser.add_argument("--min-profit", type=float, default=0.1,
                       help="Minimum profit filter (MON)")
    parser.add_argument("--interval", type=int, default=10,
                       help="Check interval (seconds)")
    parser.add_argument("--auto-submit", action="store_true",
                       help="Auto-submit to relay")
    parser.add_argument("--api-url", default="http://localhost:8000",
                       help="Brick3 API URL")
    
    args = parser.parse_args()
    
    # Integration başlat
    integration = Brick3APrioriIntegration(
        brick3_api_key=args.api_key,
        apriori_validator_address=args.validator,
        brick3_api_url=args.api_url
    )
    
    # Monitoring başlat
    integration.run_monitoring_loop(
        min_profit=args.min_profit,
        check_interval=args.interval,
        auto_submit=args.auto_submit
    )


if __name__ == "__main__":
    main()
