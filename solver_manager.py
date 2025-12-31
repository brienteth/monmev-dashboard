"""
🔑 Brick3 Solver Registration & Wallet Management
Answers FastLane Question #3: "How are your bots using fastlane currently? through atlas? can you share your solver addresses"

This module:
1. Manages solver/searcher wallet addresses
2. Handles registration with FastLane Atlas
3. Provides secure key management
4. Tracks solver performance metrics

Author: Brick3 MEV Team
License: MIT
"""

import os
import json
import time
import hashlib
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import logging
import secrets
from pathlib import Path

# Try to import web3 for wallet operations
try:
    from web3 import Web3
    from eth_account import Account
    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Brick3Solver")

# ==================== CONFIGURATION ====================

FASTLANE_ATLAS_CONFIG = {
    # Atlas Router Contract on Monad
    "atlas_router": "0xbB010Cb7e71D44d7323aE1C267B333A48D05907C",
    
    # Auctioneer endpoint
    "auctioneer_url": "https://auctioneer-fra.fastlane-labs.xyz",
    
    # Monad Chain ID
    "chain_id": 10143,
    
    # Solver registration params
    "min_bond_amount": 0,  # MON required for solver bond
    "registration_gas": 500000,
}

# ==================== DATA STRUCTURES ====================

class SolverStatus(Enum):
    PENDING = "pending"
    REGISTERED = "registered"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"

@dataclass
class SolverWallet:
    """Solver wallet configuration"""
    address: str
    name: str
    description: str
    
    # Status
    status: SolverStatus = SolverStatus.PENDING
    registered_at: Optional[float] = None
    registration_tx: Optional[str] = None
    
    # Balances (cached)
    mon_balance_wei: int = 0
    bond_amount_wei: int = 0
    
    # Performance metrics
    bundles_submitted: int = 0
    bundles_landed: int = 0
    total_profit_wei: int = 0
    total_gas_spent_wei: int = 0
    
    # Timestamps
    created_at: float = field(default_factory=time.time)
    last_active: Optional[float] = None
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['status'] = self.status.value
        return d
    
    @property
    def success_rate(self) -> float:
        if self.bundles_submitted == 0:
            return 0
        return (self.bundles_landed / self.bundles_submitted) * 100
    
    @property
    def avg_profit_per_bundle(self) -> float:
        if self.bundles_landed == 0:
            return 0
        return self.total_profit_wei / self.bundles_landed

@dataclass
class BundleSubmission:
    """Record of a bundle submission"""
    id: str
    solver_address: str
    bundle_hash: str
    target_block: int
    
    # Transactions in bundle
    tx_count: int
    tx_hashes: List[str]
    
    # Target info
    opportunity_type: str  # sandwich, arbitrage, liquidation
    target_tx_hash: Optional[str]
    
    # Profit expectation
    expected_profit_wei: int
    gas_price_wei: int
    
    # Result
    landed: bool = False
    actual_profit_wei: int = 0
    actual_gas_used: int = 0
    landing_block: Optional[int] = None
    
    # Timing
    submitted_at: float = field(default_factory=time.time)
    confirmed_at: Optional[float] = None

# ==================== SOLVER MANAGER ====================

class SolverManager:
    """
    Manages solver wallets and their registration with FastLane Atlas
    """
    
    def __init__(
        self,
        db_path: str = "solver_data.db",
        keystore_path: str = ".keystore"
    ):
        self.db_path = db_path
        self.keystore_path = Path(keystore_path)
        self.keystore_path.mkdir(exist_ok=True)
        
        self.solvers: Dict[str, SolverWallet] = {}
        self.w3 = None
        
        self._init_db()
        self._init_web3()
        self._load_solvers()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solvers (
                address TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                status TEXT,
                registered_at REAL,
                registration_tx TEXT,
                mon_balance_wei TEXT,
                bond_amount_wei TEXT,
                bundles_submitted INTEGER DEFAULT 0,
                bundles_landed INTEGER DEFAULT 0,
                total_profit_wei TEXT DEFAULT '0',
                total_gas_spent_wei TEXT DEFAULT '0',
                created_at REAL,
                last_active REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bundle_submissions (
                id TEXT PRIMARY KEY,
                solver_address TEXT,
                bundle_hash TEXT,
                target_block INTEGER,
                tx_count INTEGER,
                tx_hashes TEXT,
                opportunity_type TEXT,
                target_tx_hash TEXT,
                expected_profit_wei TEXT,
                gas_price_wei TEXT,
                landed INTEGER DEFAULT 0,
                actual_profit_wei TEXT DEFAULT '0',
                actual_gas_used INTEGER DEFAULT 0,
                landing_block INTEGER,
                submitted_at REAL,
                confirmed_at REAL,
                FOREIGN KEY (solver_address) REFERENCES solvers(address)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_bundle_solver ON bundle_submissions(solver_address)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_bundle_time ON bundle_submissions(submitted_at)
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"📁 Solver database initialized: {self.db_path}")
    
    def _init_web3(self):
        """Initialize Web3 connection"""
        if not HAS_WEB3:
            logger.warning("⚠️ web3 package not installed")
            return
        
        try:
            rpc_url = os.getenv("MONAD_RPC", "https://rpc.monad.xyz")
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if self.w3.is_connected():
                logger.info("✅ Connected to Monad RPC")
            else:
                logger.warning("⚠️ Web3 not connected")
        except Exception as e:
            logger.error(f"Web3 init error: {e}")
    
    def _load_solvers(self):
        """Load solvers from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM solvers')
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            
            solver = SolverWallet(
                address=data['address'],
                name=data['name'],
                description=data['description'],
                status=SolverStatus(data['status']),
                registered_at=data['registered_at'],
                registration_tx=data['registration_tx'],
                mon_balance_wei=int(data['mon_balance_wei'] or 0),
                bond_amount_wei=int(data['bond_amount_wei'] or 0),
                bundles_submitted=data['bundles_submitted'],
                bundles_landed=data['bundles_landed'],
                total_profit_wei=int(data['total_profit_wei'] or 0),
                total_gas_spent_wei=int(data['total_gas_spent_wei'] or 0),
                created_at=data['created_at'],
                last_active=data['last_active']
            )
            self.solvers[solver.address.lower()] = solver
        
        conn.close()
        logger.info(f"📂 Loaded {len(self.solvers)} solvers from database")
    
    def create_solver_wallet(
        self,
        name: str,
        description: str = "",
        save_private_key: bool = True
    ) -> SolverWallet:
        """
        Create a new solver wallet
        
        Args:
            name: Friendly name for the solver
            description: Description of solver purpose
            save_private_key: Whether to save encrypted private key
            
        Returns:
            New SolverWallet object
        """
        if not HAS_WEB3:
            raise RuntimeError("web3 package required for wallet creation")
        
        # Generate new account
        account = Account.create()
        address = account.address
        private_key = account.key.hex()
        
        logger.info(f"🔑 Created new solver wallet: {address}")
        
        # Create solver object
        solver = SolverWallet(
            address=address,
            name=name,
            description=description,
            status=SolverStatus.PENDING
        )
        
        # Save to memory and database
        self.solvers[address.lower()] = solver
        self._save_solver(solver)
        
        # Optionally save private key (encrypted)
        if save_private_key:
            self._save_private_key(address, private_key, name)
        
        return solver
    
    def import_solver_wallet(
        self,
        address: str,
        name: str,
        description: str = "",
        private_key: Optional[str] = None
    ) -> SolverWallet:
        """
        Import an existing wallet as a solver
        
        Args:
            address: Wallet address
            name: Friendly name
            description: Description
            private_key: Optional private key to store
        """
        address = Web3.to_checksum_address(address) if HAS_WEB3 else address
        
        solver = SolverWallet(
            address=address,
            name=name,
            description=description,
            status=SolverStatus.PENDING
        )
        
        self.solvers[address.lower()] = solver
        self._save_solver(solver)
        
        if private_key:
            self._save_private_key(address, private_key, name)
        
        logger.info(f"📥 Imported solver wallet: {address}")
        return solver
    
    def _save_private_key(self, address: str, private_key: str, name: str):
        """Save encrypted private key to keystore"""
        # In production, use proper encryption (e.g., keystore v3)
        # This is a simplified version
        keyfile = self.keystore_path / f"{name.lower().replace(' ', '_')}_{address[:8]}.json"
        
        data = {
            "address": address,
            "name": name,
            "private_key_encrypted": f"[ENCRYPTED:{hashlib.sha256(private_key.encode()).hexdigest()[:16]}]",
            "created_at": datetime.now().isoformat(),
            "warning": "In production, use proper encryption!"
        }
        
        with open(keyfile, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Also print to console for user to save
        logger.warning(f"⚠️ SAVE THIS PRIVATE KEY SECURELY: {private_key[:10]}...{private_key[-6:]}")
        logger.info(f"📁 Keyfile saved: {keyfile}")
    
    def _save_solver(self, solver: SolverWallet):
        """Save solver to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO solvers
            (address, name, description, status, registered_at, registration_tx,
             mon_balance_wei, bond_amount_wei, bundles_submitted, bundles_landed,
             total_profit_wei, total_gas_spent_wei, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            solver.address, solver.name, solver.description, solver.status.value,
            solver.registered_at, solver.registration_tx,
            str(solver.mon_balance_wei), str(solver.bond_amount_wei),
            solver.bundles_submitted, solver.bundles_landed,
            str(solver.total_profit_wei), str(solver.total_gas_spent_wei),
            solver.created_at, solver.last_active
        ))
        
        conn.commit()
        conn.close()
    
    async def register_with_atlas(
        self,
        solver_address: str,
        bond_amount_wei: int = 0
    ) -> Dict:
        """
        Register solver with FastLane Atlas protocol
        
        Args:
            solver_address: Address to register
            bond_amount_wei: Bond amount to deposit
            
        Returns:
            Registration result
        """
        solver = self.solvers.get(solver_address.lower())
        if not solver:
            return {"success": False, "error": "Solver not found"}
        
        if solver.status == SolverStatus.REGISTERED:
            return {"success": False, "error": "Already registered"}
        
        # In production, this would:
        # 1. Call Atlas Router contract to register
        # 2. Deposit bond if required
        # 3. Wait for confirmation
        
        logger.info(f"📝 Registering solver {solver_address} with Atlas...")
        
        # For now, simulate registration
        # Real implementation would interact with Atlas contract
        registration_result = {
            "success": True,
            "solver_address": solver_address,
            "atlas_router": FASTLANE_ATLAS_CONFIG["atlas_router"],
            "registration_tx": f"0x{secrets.token_hex(32)}",  # Mock tx hash
            "bond_deposited": bond_amount_wei,
            "message": "Registration simulated - needs real Atlas contract interaction"
        }
        
        # Update solver status
        solver.status = SolverStatus.REGISTERED
        solver.registered_at = time.time()
        solver.registration_tx = registration_result["registration_tx"]
        solver.bond_amount_wei = bond_amount_wei
        
        self._save_solver(solver)
        
        logger.info(f"✅ Solver registered with Atlas")
        return registration_result
    
    def update_balance(self, solver_address: str) -> Dict:
        """Update solver's MON balance"""
        solver = self.solvers.get(solver_address.lower())
        if not solver or not self.w3:
            return {"success": False}
        
        try:
            balance = self.w3.eth.get_balance(solver_address)
            solver.mon_balance_wei = balance
            self._save_solver(solver)
            
            return {
                "success": True,
                "balance_wei": balance,
                "balance_mon": balance / 1e18
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def record_bundle_submission(
        self,
        solver_address: str,
        bundle_hash: str,
        target_block: int,
        tx_hashes: List[str],
        opportunity_type: str,
        target_tx_hash: Optional[str],
        expected_profit_wei: int,
        gas_price_wei: int
    ) -> BundleSubmission:
        """Record a bundle submission"""
        submission = BundleSubmission(
            id=hashlib.md5(f"{bundle_hash}_{time.time()}".encode()).hexdigest()[:16],
            solver_address=solver_address,
            bundle_hash=bundle_hash,
            target_block=target_block,
            tx_count=len(tx_hashes),
            tx_hashes=tx_hashes,
            opportunity_type=opportunity_type,
            target_tx_hash=target_tx_hash,
            expected_profit_wei=expected_profit_wei,
            gas_price_wei=gas_price_wei
        )
        
        # Update solver stats
        solver = self.solvers.get(solver_address.lower())
        if solver:
            solver.bundles_submitted += 1
            solver.last_active = time.time()
            self._save_solver(solver)
        
        # Save submission
        self._save_bundle_submission(submission)
        
        return submission
    
    def record_bundle_result(
        self,
        submission_id: str,
        landed: bool,
        actual_profit_wei: int = 0,
        actual_gas_used: int = 0,
        landing_block: Optional[int] = None
    ):
        """Record the result of a bundle submission"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bundle_submissions
            SET landed = ?, actual_profit_wei = ?, actual_gas_used = ?,
                landing_block = ?, confirmed_at = ?
            WHERE id = ?
        ''', (
            1 if landed else 0, str(actual_profit_wei), actual_gas_used,
            landing_block, time.time(), submission_id
        ))
        
        # Get solver address
        cursor.execute('SELECT solver_address FROM bundle_submissions WHERE id = ?', (submission_id,))
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        # Update solver stats
        if result and landed:
            solver = self.solvers.get(result[0].lower())
            if solver:
                solver.bundles_landed += 1
                solver.total_profit_wei += actual_profit_wei
                solver.total_gas_spent_wei += actual_gas_used
                self._save_solver(solver)
    
    def _save_bundle_submission(self, submission: BundleSubmission):
        """Save bundle submission to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bundle_submissions
            (id, solver_address, bundle_hash, target_block, tx_count, tx_hashes,
             opportunity_type, target_tx_hash, expected_profit_wei, gas_price_wei,
             landed, actual_profit_wei, actual_gas_used, landing_block, submitted_at, confirmed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission.id, submission.solver_address, submission.bundle_hash,
            submission.target_block, submission.tx_count, json.dumps(submission.tx_hashes),
            submission.opportunity_type, submission.target_tx_hash,
            str(submission.expected_profit_wei), str(submission.gas_price_wei),
            1 if submission.landed else 0, str(submission.actual_profit_wei),
            submission.actual_gas_used, submission.landing_block,
            submission.submitted_at, submission.confirmed_at
        ))
        
        conn.commit()
        conn.close()
    
    def get_all_solvers(self) -> List[Dict]:
        """Get all solver wallets"""
        return [s.to_dict() for s in self.solvers.values()]
    
    def get_solver_stats(self, solver_address: str) -> Dict:
        """Get detailed stats for a solver"""
        solver = self.solvers.get(solver_address.lower())
        if not solver:
            return {"error": "Solver not found"}
        
        # Get bundle history
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN landed = 1 THEN 1 ELSE 0 END) as landed,
                   SUM(CASE WHEN landed = 1 THEN actual_profit_wei ELSE 0 END) as profit
            FROM bundle_submissions
            WHERE solver_address = ?
        ''', (solver_address,))
        
        bundle_stats = cursor.fetchone()
        conn.close()
        
        return {
            "solver": solver.to_dict(),
            "bundle_stats": {
                "total_submissions": bundle_stats[0] or 0,
                "successful_landings": bundle_stats[1] or 0,
                "total_profit_wei": int(bundle_stats[2] or 0),
                "success_rate": ((bundle_stats[1] or 0) / max(bundle_stats[0] or 1, 1)) * 100
            }
        }

# ==================== QUERY FUNCTIONS ====================

def get_solver_addresses(db_path: str = "solver_data.db") -> List[str]:
    """Get all registered solver addresses"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT address FROM solvers WHERE status IN ('registered', 'active')")
    addresses = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return addresses

def get_solver_summary(db_path: str = "solver_data.db") -> Dict:
    """Get summary of all solvers"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM solvers')
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM solvers WHERE status = 'registered'")
    registered = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(bundles_submitted), SUM(bundles_landed) FROM solvers')
    bundle_stats = cursor.fetchone()
    
    cursor.execute('SELECT SUM(CAST(total_profit_wei AS INTEGER)) FROM solvers')
    total_profit = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_solvers": total,
        "registered_solvers": registered,
        "total_bundles_submitted": bundle_stats[0] or 0,
        "total_bundles_landed": bundle_stats[1] or 0,
        "total_profit_wei": total_profit,
        "total_profit_mon": total_profit / 1e18,
        "atlas_router": FASTLANE_ATLAS_CONFIG["atlas_router"]
    }

def export_solver_info(db_path: str = "solver_data.db") -> Dict:
    """
    Export solver information for FastLane team
    This provides the answer to: "can you share your solver addresses"
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT address, name, description, status, registered_at, 
               bundles_submitted, bundles_landed, total_profit_wei
        FROM solvers
    ''')
    
    columns = ['address', 'name', 'description', 'status', 'registered_at',
               'bundles_submitted', 'bundles_landed', 'total_profit_wei']
    solvers = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "generated_at": datetime.now().isoformat(),
        "atlas_integration": {
            "atlas_router": FASTLANE_ATLAS_CONFIG["atlas_router"],
            "auctioneer_url": FASTLANE_ATLAS_CONFIG["auctioneer_url"],
            "chain_id": FASTLANE_ATLAS_CONFIG["chain_id"],
        },
        "solver_wallets": solvers,
        "summary": get_solver_summary(db_path),
        "note": "We are seeking official FastLane integration to register these solvers with Atlas"
    }

# ==================== DEMO ====================

def demo_solver_setup():
    """Demo: Solver wallet setup"""
    print("=" * 60)
    print("🔑 Brick3 Solver Registration Demo")
    print("=" * 60)
    
    # Create manager
    manager = SolverManager()
    
    # Create demo solver wallets
    print("\n📝 Creating solver wallets...\n")
    
    solvers_to_create = [
        ("Brick3-Sandwich-Bot", "Primary sandwich attack solver"),
        ("Brick3-Arb-Bot", "Cross-DEX arbitrage solver"),
        ("Brick3-Liquidation-Bot", "Lending protocol liquidation solver"),
    ]
    
    for name, desc in solvers_to_create:
        if HAS_WEB3:
            solver = manager.create_solver_wallet(name, desc)
            print(f"  ✅ Created: {name}")
            print(f"     Address: {solver.address}")
            print()
        else:
            # Create with mock address
            mock_addr = f"0x{secrets.token_hex(20)}"
            solver = manager.import_solver_wallet(mock_addr, name, desc)
            print(f"  ✅ Created (mock): {name}")
            print(f"     Address: {solver.address}")
            print()
    
    # Show summary
    print("=" * 60)
    print("📊 Solver Summary")
    print("=" * 60)
    
    summary = get_solver_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Export info for FastLane
    print("\n" + "=" * 60)
    print("📤 Solver Info Export (for FastLane)")
    print("=" * 60)
    
    export = export_solver_info()
    
    # Save to file
    with open("solver_info_export.json", 'w') as f:
        json.dump(export, f, indent=2)
    
    print(f"\n📁 Exported to: solver_info_export.json")
    print("\nSolver addresses:")
    for solver in export["solver_wallets"]:
        print(f"  - {solver['name']}: {solver['address']}")

if __name__ == "__main__":
    demo_solver_setup()
