import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.blockchain.near_client import near_rpc_client
from app.core.config import settings
from app.core.logging import logger
from app.db.database import db
from app.events.publisher import event_publisher


class BlockchainMonitor:
    """
    Dedicated background monitoring service for NEAR Protocol Testnet activity.
    Coordinates:
    - Periodic node status and block synchronization tracking
    - Verification of executing and unconfirmed on-chain transactions via JSON-RPC
    - Smart contract vault escrow status updates
    - RPC connection state transitions (connection_lost / connection_restored)
    - Checkpoint persistence and crash recovery
    - Emits standardized blockchain.* events to the real-time event pipeline
    """

    def __init__(self, poll_interval_seconds: float = 6.0):
        self.poll_interval = poll_interval_seconds
        self.network_id = getattr(settings, "NEAR_NETWORK_ID", "testnet")
        self.contract_id = getattr(settings, "NEAR_VAULT_CONTRACT_ID", "payguard-vault.testnet")
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self.last_sync_time: Optional[str] = None
        self.last_block_height: int = 0
        self.last_block_hash: str = ""
        self.rpc_status: str = "INITIALIZING"
        self._consecutive_rpc_failures: int = 0

    async def start(self) -> None:
        """Starts the background NEAR event monitoring loop."""
        if self._running:
            return
        self._running = True
        # Load last checkpoint from SQLite
        checkpoint = db.get_blockchain_checkpoint("near_testnet")
        if checkpoint:
            self.last_block_height = checkpoint.get("last_block_height", 0)
            self.last_block_hash = checkpoint.get("last_block_hash", "")
            self.last_sync_time = checkpoint.get("updated_at")
            logger.info(f"[BlockchainMonitor] Restored checkpoint at block height {self.last_block_height}")

        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("[BlockchainMonitor] Background blockchain monitoring service started.")

    async def stop(self) -> None:
        """Stops the background monitoring loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[BlockchainMonitor] Background blockchain monitoring service stopped.")

    async def poll_once(self) -> Dict[str, Any]:
        """Performs a single round of blockchain synchronization and health checks."""
        prev_status = self.rpc_status
        now_ts = datetime.now(timezone.utc).isoformat()

        try:
            node_status = await near_rpc_client.get_node_status()
            current_rpc_status = node_status.get("status", "ONLINE")

            # Detect and broadcast state transitions
            if "ONLINE" in current_rpc_status:
                self.rpc_status = "ONLINE"
                self._consecutive_rpc_failures = 0
                if prev_status in ["OFFLINE", "DEGRADED (OFFLINE FALLBACK)"]:
                    await event_publisher.publish(
                        event_type="blockchain.connection_restored",
                        payload={
                            "rpc_url": near_rpc_client.rpc_url,
                            "network": self.network_id,
                            "restored_at": now_ts,
                        },
                        source="near_blockchain",
                        severity="SUCCESS",
                    )
            else:
                self.rpc_status = current_rpc_status
                self._consecutive_rpc_failures += 1
                if prev_status == "ONLINE" and self._consecutive_rpc_failures >= 2:
                    await event_publisher.publish(
                        event_type="blockchain.connection_lost",
                        payload={
                            "rpc_url": near_rpc_client.rpc_url,
                            "network": self.network_id,
                            "lost_at": now_ts,
                            "error": node_status.get("error", "Node unreachable"),
                        },
                        source="near_blockchain",
                        severity="CRITICAL",
                    )

            # Update checkpoint if new height observed
            latest_height = node_status.get("latest_block_height", 0)
            latest_hash = node_status.get("latest_block_hash", "")

            if latest_height and latest_height > self.last_block_height:
                self.last_block_height = latest_height
                self.last_block_hash = latest_hash
                self.last_sync_time = now_ts
                db.save_blockchain_checkpoint("near_testnet", latest_height, latest_hash)

            # Reconcile any unconfirmed executing transactions in the local database
            await self._reconcile_pending_transactions()

            return {
                "rpc_status": self.rpc_status,
                "latest_block_height": self.last_block_height,
                "latest_block_hash": self.last_block_hash,
                "last_sync_time": self.last_sync_time,
            }
        except Exception as e:
            logger.debug(f"[BlockchainMonitor] Poll error: {e}")
            self.rpc_status = "DEGRADED"
            return {"error": str(e), "rpc_status": self.rpc_status}

    async def _reconcile_pending_transactions(self) -> None:
        """Checks pending or executing transactions against NEAR JSON-RPC."""
        pending_txs = db.list_transactions(limit=10)
        for tx in pending_txs:
            if tx.get("status") == "EXECUTING" and tx.get("tx_hash"):
                tx_hash = tx["tx_hash"]
                sender = tx.get("sender", "agent-executor.testnet")
                res = await near_rpc_client.verify_transaction(tx_hash, sender)
                if res.get("verified"):
                    tx["status"] = "CONFIRMED"
                    if res.get("block_hash"):
                        tx["block_hash"] = res["block_hash"]
                    db.save_transaction(tx)
                    await event_publisher.publish(
                        event_type="blockchain.transaction_confirmed",
                        transaction_id=tx["transaction_id"],
                        payload={
                            "transaction_id": tx["transaction_id"],
                            "tx_hash": tx_hash,
                            "block_hash": tx.get("block_hash"),
                            "explorer_url": tx.get("explorer_url"),
                            "amount": tx.get("amount"),
                        },
                        source="near_blockchain",
                        severity="SUCCESS",
                    )
                elif res.get("status") == "FAILED":
                    tx["status"] = "FAILED"
                    db.save_transaction(tx)
                    await event_publisher.publish(
                        event_type="blockchain.transaction_failed",
                        transaction_id=tx["transaction_id"],
                        payload={
                            "transaction_id": tx["transaction_id"],
                            "tx_hash": tx_hash,
                            "error": res.get("error", "Transaction reverted on NEAR Testnet"),
                        },
                        source="near_blockchain",
                        severity="CRITICAL",
                    )

    async def _monitor_loop(self) -> None:
        """Internal continuous polling loop."""
        while self._running:
            try:
                await self.poll_once()
            except Exception as e:
                logger.warning(f"[BlockchainMonitor] Unexpected loop error: {e}")
            await asyncio.sleep(self.poll_interval)

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry of the monitor."""
        return {
            "service": "BlockchainMonitor",
            "is_running": self._running,
            "network": self.network_id,
            "contract_id": self.contract_id,
            "rpc_url": near_rpc_client.rpc_url,
            "rpc_status": self.rpc_status,
            "last_block_height": self.last_block_height,
            "last_block_hash": self.last_block_hash,
            "last_sync_time": self.last_sync_time,
            "poll_interval_seconds": self.poll_interval,
        }


blockchain_monitor = BlockchainMonitor()

