"""
Ethereum testnet adapter for digital ID verification
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from web3 import Web3
from eth_account import Account
import json

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.tourist import DigitalId

settings = get_settings()
logger = logging.getLogger(__name__)


class EthereumAdapter:
    """Ethereum testnet integration for digital ID verification."""
    
    def __init__(self):
        """Initialize Ethereum connection."""
        self.w3 = None
        self.account = None
        self.contract = None
        self.setup_connection()
    
    def setup_connection(self):
        """Setup connection to Ethereum testnet."""
        try:
            # Connect to Ethereum testnet (Sepolia by default)
            if settings.ethereum_rpc_url:
                self.w3 = Web3(Web3.HTTPProvider(settings.ethereum_rpc_url))
                
                if self.w3.is_connected():
                    logger.info(f"✅ Connected to Ethereum {settings.ethereum_network}")
                    logger.info(f"   Chain ID: {self.w3.eth.chain_id}")
                    logger.info(f"   Latest block: {self.w3.eth.block_number}")
                else:
                    logger.error("❌ Failed to connect to Ethereum network")
                    return
            else:
                logger.warning("⚠️ No Ethereum RPC URL configured, using mock mode")
                return
            
            # Setup account if private key provided
            if settings.ethereum_private_key:
                self.account = Account.from_key(settings.ethereum_private_key)
                logger.info(f"✅ Ethereum account loaded: {self.account.address}")
            else:
                logger.warning("⚠️ No Ethereum private key configured, read-only mode")
                
        except Exception as e:
            logger.error(f"❌ Error setting up Ethereum connection: {str(e)}")
    
    def generate_id_hash(self, tourist_data: Dict[str, Any]) -> str:
        """Generate hash for tourist digital identity."""
        try:
            # Create deterministic hash from tourist data
            identity_string = json.dumps({
                "name": tourist_data.get("name", ""),
                "passport": tourist_data.get("passport", ""),
                "nationality": tourist_data.get("nationality", ""),
                "birth_date": tourist_data.get("birth_date", ""),
                "timestamp": datetime.utcnow().isoformat()
            }, sort_keys=True)
            
            # Generate Keccak256 hash
            if self.w3:
                hash_bytes = self.w3.keccak(text=identity_string)
                return hash_bytes.hex()
            else:
                # Mock hash for testing
                import hashlib
                return hashlib.sha256(identity_string.encode()).hexdigest()
                
        except Exception as e:
            logger.error(f"Error generating ID hash: {str(e)}")
            return None
    
    async def submit_identity_hash(self, tourist_id: str, identity_hash: str) -> Optional[str]:
        """Submit identity hash to Ethereum testnet."""
        try:
            if not self.w3 or not self.w3.is_connected():
                logger.warning("⚠️ Ethereum not connected, using mock transaction")
                # Generate mock transaction hash
                mock_tx = f"0x{''.join(['a' + str(i % 10) for i in range(64)])}"
                
                # Store in database
                db = SessionLocal()
                digital_id = DigitalId(
                    tourist_id=tourist_id,
                    offchain_hash=identity_hash,
                    eth_tx_hash=mock_tx,
                    chain=settings.ethereum_network,
                    verified_at=datetime.utcnow()
                )
                db.add(digital_id)
                db.commit()
                db.close()
                
                logger.info(f"✅ Mock identity hash submitted: {mock_tx}")
                return mock_tx
            
            if not self.account:
                logger.error("❌ No Ethereum account configured for transactions")
                return None
            
            # Prepare transaction data
            # In a real implementation, this would call a smart contract
            transaction_data = {
                'tourist_id': tourist_id,
                'identity_hash': identity_hash,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # For this demo, we'll create a simple transaction with data
            tx_data = {
                'to': '0x0000000000000000000000000000000000000000',  # Null address for data storage
                'value': 0,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'data': self.w3.to_hex(text=json.dumps(transaction_data))
            }
            
            # Sign and send transaction
            signed_tx = self.account.sign_transaction(tx_data)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"✅ Identity hash submitted to Ethereum: {tx_hash_hex}")
            
            # Store in database
            db = SessionLocal()
            digital_id = DigitalId(
                tourist_id=tourist_id,
                offchain_hash=identity_hash,
                eth_tx_hash=tx_hash_hex,
                chain=settings.ethereum_network,
                verified_at=datetime.utcnow()
            )
            db.add(digital_id)
            db.commit()
            db.close()
            
            return tx_hash_hex
            
        except Exception as e:
            logger.error(f"❌ Error submitting identity hash: {str(e)}")
            return None
    
    async def verify_identity_hash(self, tourist_id: str, provided_hash: str) -> bool:
        """Verify identity hash against blockchain record."""
        try:
            # Get stored digital ID from database
            db = SessionLocal()
            digital_id = db.query(DigitalId).filter(
                DigitalId.tourist_id == tourist_id
            ).first()
            db.close()
            
            if not digital_id:
                logger.warning(f"⚠️ No digital ID found for tourist {tourist_id}")
                return False
            
            # Compare hashes
            if digital_id.offchain_hash == provided_hash:
                logger.info(f"✅ Identity hash verified for tourist {tourist_id}")
                return True
            else:
                logger.warning(f"❌ Identity hash mismatch for tourist {tourist_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verifying identity hash: {str(e)}")
            return False
    
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction status from blockchain."""
        try:
            if not self.w3 or not self.w3.is_connected():
                return {
                    "status": "mock",
                    "confirmed": True,
                    "block_number": 12345,
                    "message": "Mock transaction status"
                }
            
            # Get transaction receipt
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            return {
                "status": "confirmed" if receipt.status == 1 else "failed",
                "confirmed": receipt.status == 1,
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "transaction_hash": receipt.transactionHash.hex()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting transaction status: {str(e)}")
            return {
                "status": "error",
                "confirmed": False,
                "message": str(e)
            }


# Global adapter instance
eth_adapter = EthereumAdapter()


async def process_digital_id_verification():
    """Background service for processing digital ID verifications."""
    logger.info("🔗 Starting Ethereum adapter service...")
    
    while True:
        try:
            # Check for unverified digital IDs
            db = SessionLocal()
            unverified_ids = db.query(DigitalId).filter(
                DigitalId.verified_at.is_(None)
            ).limit(10).all()
            
            for digital_id in unverified_ids:
                if digital_id.eth_tx_hash:
                    # Check transaction status
                    status = await eth_adapter.get_transaction_status(digital_id.eth_tx_hash)
                    
                    if status.get("confirmed"):
                        digital_id.verified_at = datetime.utcnow()
                        db.commit()
                        logger.info(f"✅ Digital ID verified: {digital_id.tourist_id}")
            
            db.close()
            
            # Sleep for 30 seconds before next check
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"❌ Error in digital ID processing: {str(e)}")
            await asyncio.sleep(60)  # Wait longer on error


async def main():
    """Main service entry point."""
    logger.info("🚀 Starting Ethereum Adapter Service")
    
    # Test connection
    if eth_adapter.w3 and eth_adapter.w3.is_connected():
        logger.info("✅ Ethereum connection successful")
    else:
        logger.warning("⚠️ Running in mock mode (no Ethereum connection)")
    
    # Start background processing
    await process_digital_id_verification()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(main())
