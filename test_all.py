#!/usr/bin/env python3
"""
🧪 Brick3 MEV API - Tam Test Script
Tüm bot, simülasyon ve revenue endpointlerini test eder.
"""

import subprocess
import time
import requests
import json
import sys

def main():
    # Start API in background
    print("⏳ API başlatılıyor...")
    proc = subprocess.Popen(
        ['python', 'monmev_api.py'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    time.sleep(6)
    
    print()
    print("╔" + "═"*60 + "╗")
    print("║          🧪 BRICK3 MEV API - TAM TEST                     ║")
    print("╚" + "═"*60 + "╝")
    print()
    
    headers = {'X-API-Key': 'brick3_unlimited_master'}
    base = 'http://localhost:8000'
    
    tests = [
        ('1️⃣  HEALTH CHECK', 'GET', '/health'),
        ('2️⃣  BOT STATUS', 'GET', '/api/v1/bots/status'),
        ('3️⃣  SANDWICH BOT BAŞLAT', 'POST', '/api/v1/bots/start/sandwich'),
        ('4️⃣  ARBITRAGE BOT BAŞLAT', 'POST', '/api/v1/bots/start/arbitrage'),
        ('5️⃣  BOT DURUMLARI', 'GET', '/api/v1/bots/status'),
        ('6️⃣  SANDWICH SİMÜLASYON', 'POST', '/api/v1/simulate/sandwich?victim_value_mon=100'),
        ('7️⃣  ARBITRAGE SİMÜLASYON', 'POST', '/api/v1/simulate/arbitrage?amount_in_mon=50&hops=3'),
        ('8️⃣  REVENUE ÖZET', 'GET', '/api/v1/revenue/summary'),
        ('9️⃣  APY TAHMİNİ', 'GET', '/api/v1/revenue/estimate-apy?daily_mev_volume_usd=5000&tvl_usd=1000000'),
        ('🔟 DAĞITIM HESAPLA', 'POST', '/api/v1/revenue/calculate?profit_mon=100'),
        ('1️⃣1️⃣ BOTLARI DURDUR', 'POST', '/api/v1/bots/stop-all'),
    ]
    
    success_count = 0
    fail_count = 0
    
    for name, method, endpoint in tests:
        print(f'{name}')
        print('=' * 50)
        try:
            if method == 'GET':
                r = requests.get(base + endpoint, headers=headers, timeout=5)
            else:
                r = requests.post(base + endpoint, headers=headers, timeout=5)
            
            result = r.json()
            
            # Pretty print (truncated)
            output = json.dumps(result, indent=2, ensure_ascii=False)
            if len(output) > 500:
                print(output[:500] + "\n... (truncated)")
            else:
                print(output)
            
            if result.get('success', True):
                print('✅ SUCCESS')
                success_count += 1
            else:
                print('❌ FAILED')
                fail_count += 1
        except Exception as e:
            print(f'❌ ERROR: {e}')
            fail_count += 1
        print()
    
    # Stop API
    proc.terminate()
    proc.wait()
    
    print()
    print("╔" + "═"*60 + "╗")
    print(f"║     ✅ TEST SONUÇLARI: {success_count} başarılı, {fail_count} başarısız       ║")
    print("╚" + "═"*60 + "╝")
    
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
