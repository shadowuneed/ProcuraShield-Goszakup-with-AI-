"""
Web3.py интеграционный слой для смарт-контрактов ProcuraShield.
Обеспечивает взаимодействие Python-бэкенда с Ethereum (Ganache).
"""
import json
import hashlib
from typing import Optional
from pathlib import Path

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from app.core.config import settings


class BlockchainService:
    """Сервис для взаимодействия с блокчейном."""

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
        # Поддержка PoA-сетей (Ganache)
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        self.account = self.w3.eth.accounts[0] if self.w3.eth.accounts else None

        # ABI и адреса контрактов (загружаются после деплоя)
        self._contracts = {}
        self._load_contracts()

    def _load_contracts(self):
        """Загрузка ABI и адресов контрактов из файлов деплоя."""
        deploy_dir = Path(__file__).parent.parent.parent / "contracts" / "deployed"
        if not deploy_dir.exists():
            return

        for contract_file in deploy_dir.glob("*.json"):
            with open(contract_file, "r") as f:
                data = json.load(f)
                name = contract_file.stem
                self._contracts[name] = self.w3.eth.contract(
                    address=Web3.to_checksum_address(data["address"]),
                    abi=data["abi"]
                )

    @property
    def is_connected(self) -> bool:
        """Проверка подключения к блокчейну."""
        return self.w3.is_connected()

    # === ProcurementRegistry ===

    def register_procurement(
        self,
        procurement_id: str,
        title: str,
        organization: str,
        amount: int,
        document_hash: str
    ) -> Optional[str]:
        """
        Регистрация закупки в блокчейне.
        Возвращает хеш транзакции.
        """
        contract = self._contracts.get("ProcurementRegistry")
        if not contract:
            return None

        doc_hash_bytes = bytes.fromhex(document_hash) if len(document_hash) == 64 else \
            hashlib.sha256(document_hash.encode()).digest()

        tx = contract.functions.registerProcurement(
            procurement_id,
            title,
            organization,
            amount,
            doc_hash_bytes
        ).transact({"from": self.account})

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        return receipt.transactionHash.hex()

    def verify_document(self, document_hash: str) -> dict:
        """
        Верификация документа по хешу.
        Возвращает информацию о записи в блокчейне.
        """
        contract = self._contracts.get("ProcurementRegistry")
        if not contract:
            return {"verified": False, "reason": "Contract not deployed"}

        doc_hash_bytes = bytes.fromhex(document_hash) if len(document_hash) == 64 else \
            hashlib.sha256(document_hash.encode()).digest()

        try:
            result = contract.functions.verifyDocument(doc_hash_bytes).call()
            return {
                "verified": result[0],
                "procurement_id": result[1] if result[0] else None,
                "timestamp": result[2] if result[0] else None
            }
        except Exception as e:
            return {"verified": False, "reason": str(e)}

    # === RiskOracle ===

    def submit_risk_score(
        self,
        procurement_id: str,
        ai_score: int,
        risk_level: str,
        analysis_hash: str
    ) -> Optional[str]:
        """
        Запись результата AI-анализа риска в блокчейн.
        """
        contract = self._contracts.get("RiskOracle")
        if not contract:
            return None

        hash_bytes = bytes.fromhex(analysis_hash) if len(analysis_hash) == 64 else \
            hashlib.sha256(analysis_hash.encode()).digest()

        tx = contract.functions.submitRiskScore(
            procurement_id,
            ai_score,
            risk_level,
            hash_bytes
        ).transact({"from": self.account})

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        return receipt.transactionHash.hex()

    def get_risk_record(self, procurement_id: str) -> Optional[dict]:
        """Получение записи о риске из блокчейна."""
        contract = self._contracts.get("RiskOracle")
        if not contract:
            return None

        try:
            record = contract.functions.getRiskRecord(procurement_id).call()
            return {
                "procurement_id": record[0],
                "ai_score": record[1],
                "final_score": record[2],
                "risk_level": record[3],
                "analysis_hash": record[4].hex(),
                "submitted_by": record[5],
                "timestamp": record[6],
                "validator_votes": record[7],
                "disputed": record[8],
                "finalized": record[9]
            }
        except Exception:
            return None

    # === EvidenceVault ===

    def store_evidence(
        self,
        procurement_id: str,
        document_hash: str,
        ipfs_cid: str,
        evidence_type: int,
        access_level: int,
        description: str,
        risk_score: int
    ) -> Optional[dict]:
        """
        Сохранение хеша доказательства в блокчейн.
        """
        contract = self._contracts.get("EvidenceVault")
        if not contract:
            return None

        doc_hash_bytes = bytes.fromhex(document_hash) if len(document_hash) == 64 else \
            hashlib.sha256(document_hash.encode()).digest()

        tx = contract.functions.storeEvidence(
            procurement_id,
            doc_hash_bytes,
            ipfs_cid,
            evidence_type,
            access_level,
            description,
            risk_score
        ).transact({"from": self.account})

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)

        # Извлекаем evidenceId из логов
        logs = contract.events.EvidenceStored().process_receipt(receipt)
        evidence_id = logs[0]["args"]["evidenceId"] if logs else None

        return {
            "tx_hash": receipt.transactionHash.hex(),
            "evidence_id": evidence_id
        }

    def verify_evidence(self, document_hash: str) -> dict:
        """Верификация доказательства по хешу."""
        contract = self._contracts.get("EvidenceVault")
        if not contract:
            return {"exists": False}

        doc_hash_bytes = bytes.fromhex(document_hash) if len(document_hash) == 64 else \
            hashlib.sha256(document_hash.encode()).digest()

        try:
            result = contract.functions.verifyDocument(doc_hash_bytes).call()
            return {
                "exists": result[0],
                "evidence_id": result[1] if result[0] else None,
                "timestamp": result[2] if result[0] else None
            }
        except Exception:
            return {"exists": False}

    # === AntiMoneyLaundering ===

    def record_payment(
        self,
        from_entity: str,
        to_entity: str,
        amount: int,
        procurement_id: str,
        document_hash: str
    ) -> Optional[dict]:
        """
        Записать платёж в AML-контракт.
        """
        contract = self._contracts.get("AntiMoneyLaundering")
        if not contract:
            return None

        doc_hash_bytes = bytes.fromhex(document_hash) if len(document_hash) == 64 else \
            hashlib.sha256(document_hash.encode()).digest()

        tx = contract.functions.recordPayment(
            from_entity,
            to_entity,
            amount,
            procurement_id,
            doc_hash_bytes
        ).transact({"from": self.account})

        receipt = self.w3.eth.wait_for_transaction_receipt(tx)

        # Проверяем наличие AML-алертов
        alert_logs = contract.events.AMLAlertRaised().process_receipt(receipt)
        blocked_logs = contract.events.PaymentBlocked().process_receipt(receipt)

        return {
            "tx_hash": receipt.transactionHash.hex(),
            "blocked": len(blocked_logs) > 0,
            "alerts": [
                {
                    "alert_id": log["args"]["alertId"],
                    "alert_type": log["args"]["alertType"],
                }
                for log in alert_logs
            ]
        }

    # === IPFS ===

    def upload_to_ipfs(self, file_content: bytes) -> Optional[str]:
        """
        Загрузка файла в IPFS.
        Возвращает CID.
        """
        import requests

        try:
            response = requests.post(
                f"{settings.IPFS_API_URL}/api/v0/add",
                files={"file": file_content},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["Hash"]
        except Exception:
            pass
        return None

    def get_from_ipfs(self, cid: str) -> Optional[bytes]:
        """Получение файла из IPFS по CID."""
        import requests

        try:
            response = requests.post(
                f"{settings.IPFS_API_URL}/api/v0/cat?arg={cid}",
                timeout=30
            )
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None

    # === УТИЛИТЫ ===

    @staticmethod
    def compute_hash(data: bytes) -> str:
        """Вычислить SHA-256 хеш."""
        return hashlib.sha256(data).hexdigest()

    def get_transaction_history(self, procurement_id: str) -> list:
        """
        Получить историю всех транзакций по закупке.
        """
        history = []

        # ProcurementRegistry
        contract = self._contracts.get("ProcurementRegistry")
        if contract:
            try:
                versions = contract.functions.getVersionHistory(procurement_id).call()
                for v in versions:
                    history.append({
                        "contract": "ProcurementRegistry",
                        "action": "registration/update",
                        "timestamp": v[5],  # timestamp из структуры
                        "data": {"title": v[1], "amount": v[3]}
                    })
            except Exception:
                pass

        # RiskOracle
        contract = self._contracts.get("RiskOracle")
        if contract:
            try:
                record = contract.functions.getRiskRecord(procurement_id).call()
                if record[6] > 0:  # timestamp > 0
                    history.append({
                        "contract": "RiskOracle",
                        "action": "risk_assessment",
                        "timestamp": record[6],
                        "data": {
                            "ai_score": record[1],
                            "final_score": record[2],
                            "risk_level": record[3]
                        }
                    })
            except Exception:
                pass

        # EvidenceVault
        contract = self._contracts.get("EvidenceVault")
        if contract:
            try:
                evidence_ids = contract.functions.getEvidencesByProcurement(
                    procurement_id
                ).call()
                for eid in evidence_ids:
                    ev = contract.functions.evidences(eid).call()
                    history.append({
                        "contract": "EvidenceVault",
                        "action": "evidence_stored",
                        "timestamp": ev[7],
                        "data": {
                            "evidence_id": eid,
                            "type": ev[4],
                            "ipfs_cid": ev[3]
                        }
                    })
            except Exception:
                pass

        # Сортировка по времени
        history.sort(key=lambda x: x["timestamp"])
        return history


# Singleton
blockchain_service = BlockchainService()
