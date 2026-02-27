// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AntiMoneyLaundering
 * @notice AML-мониторинг платёжных цепочек в госзакупках.
 * @dev Отслеживание подозрительных транзакций, блокировка, KYC/AML.
 *
 * Функции:
 * - Регистрация и отслеживание платёжных цепочек
 * - Блокировка подозрительных транзакций
 * - KYC-статус участников
 * - FATF Travel Rule compliance
 * - Мониторинг дробления платежей
 */
contract AntiMoneyLaundering {

    // === ПЕРЕЧИСЛЕНИЯ ===

    enum KYCStatus {
        NOT_VERIFIED,   // Не проверен
        PENDING,        // На проверке
        VERIFIED,       // Проверен
        REJECTED,       // Отклонён
        SANCTIONED      // В санкционном списке
    }

    enum TransactionStatus {
        NORMAL,         // Нормальная транзакция
        FLAGGED,        // Помечена для проверки
        BLOCKED,        // Заблокирована
        CLEARED         // Проверена и очищена
    }

    enum AlertType {
        SPLITTING,              // Дробление платежей
        ROUND_AMOUNT,           // Круглые суммы
        RAPID_SUCCESSION,       // Быстрые последовательные платежи
        SHELL_COMPANY,          // Фирма-однодневка
        SANCTIONS_HIT,          // Совпадение с санкционным списком
        THRESHOLD_EVASION,      // Уклонение от порога
        UNUSUAL_PATTERN         // Необычный паттерн
    }

    // === СТРУКТУРЫ ===

    struct Entity {
        string entityId;        // ИНН / BIN
        string name;
        KYCStatus kycStatus;
        uint256 registeredAt;
        uint256 totalTransactions;
        uint256 totalVolume;
        bool isPEP;             // Politically Exposed Person
        bool isSanctioned;      // В санкционном списке
        uint256 riskScore;      // 0-100
    }

    struct PaymentRecord {
        uint256 paymentId;
        string fromEntity;      // ИНН отправителя
        string toEntity;        // ИНН получателя
        uint256 amount;         // Сумма в тиын/копейках
        string procurementId;   // ID закупки
        TransactionStatus status;
        uint256 timestamp;
        bytes32 documentHash;   // Хеш платёжного поручения
    }

    struct AMLAlert {
        uint256 alertId;
        uint256 paymentId;
        AlertType alertType;
        string description;
        uint256 timestamp;
        bool resolved;
    }

    struct TravelRuleData {
        string originatorName;
        string originatorAccount;
        string originatorAddress;
        string beneficiaryName;
        string beneficiaryAccount;
        string beneficiaryAddress;
    }

    // === СОСТОЯНИЕ ===

    address public owner;
    address public complianceOfficer;

    uint256 public paymentCount;
    uint256 public alertCount;

    // Порог для автоматической проверки (в тиын/копейках)
    uint256 public reportingThreshold = 3_000_000_00; // 3 млн тенге/рубли

    // Временное окно для обнаружения дробления (в секундах)
    uint256 public splittingWindow = 86400; // 24 часа

    // Порог количества транзакций для подозрения в дроблении
    uint256 public splittingCountThreshold = 5;

    mapping(string => Entity) public entities;
    mapping(uint256 => PaymentRecord) public payments;
    mapping(uint256 => AMLAlert) public alerts;
    mapping(uint256 => TravelRuleData) public travelRuleRecords;

    // Платежи по отправителю
    mapping(string => uint256[]) public entityPayments;

    // Санкционный список
    mapping(string => bool) public sanctionsList;

    // Оператор — может записывать транзакции
    mapping(address => bool) public operators;

    // === СОБЫТИЯ ===

    event PaymentRecorded(
        uint256 indexed paymentId,
        string fromEntity,
        string toEntity,
        uint256 amount,
        uint256 timestamp
    );

    event PaymentBlocked(
        uint256 indexed paymentId,
        string reason,
        uint256 timestamp
    );

    event AMLAlertRaised(
        uint256 indexed alertId,
        uint256 paymentId,
        AlertType alertType,
        uint256 timestamp
    );

    event EntityKYCUpdated(
        string indexed entityId,
        KYCStatus status,
        uint256 timestamp
    );

    event SanctionsListUpdated(
        string indexed entityId,
        bool sanctioned,
        uint256 timestamp
    );

    // === МОДИФИКАТОРЫ ===

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    modifier onlyCompliance() {
        require(
            msg.sender == complianceOfficer || msg.sender == owner,
            "Only compliance officer"
        );
        _;
    }

    modifier onlyOperator() {
        require(
            operators[msg.sender] || msg.sender == owner,
            "Only operator"
        );
        _;
    }

    // === КОНСТРУКТОР ===

    constructor(address _complianceOfficer) {
        owner = msg.sender;
        complianceOfficer = _complianceOfficer;
        operators[msg.sender] = true;
    }

    // === УПРАВЛЕНИЕ ===

    function setOperator(address _addr, bool _status) external onlyOwner {
        operators[_addr] = _status;
    }

    function setComplianceOfficer(address _addr) external onlyOwner {
        complianceOfficer = _addr;
    }

    function setReportingThreshold(uint256 _threshold) external onlyCompliance {
        reportingThreshold = _threshold;
    }

    // === KYC/AML ===

    /**
     * @notice Регистрация участника закупок
     */
    function registerEntity(
        string calldata entityId,
        string calldata name,
        bool isPEP
    ) external onlyOperator {
        entities[entityId] = Entity({
            entityId: entityId,
            name: name,
            kycStatus: KYCStatus.PENDING,
            registeredAt: block.timestamp,
            totalTransactions: 0,
            totalVolume: 0,
            isPEP: isPEP,
            isSanctioned: false,
            riskScore: isPEP ? 50 : 0
        });
    }

    /**
     * @notice Обновить KYC-статус
     */
    function updateKYCStatus(
        string calldata entityId,
        KYCStatus status
    ) external onlyCompliance {
        Entity storage entity = entities[entityId];
        require(entity.registeredAt > 0, "Entity not found");
        entity.kycStatus = status;

        if (status == KYCStatus.SANCTIONED) {
            entity.isSanctioned = true;
            sanctionsList[entityId] = true;
        }

        emit EntityKYCUpdated(entityId, status, block.timestamp);
    }

    /**
     * @notice Обновить санкционный список
     */
    function updateSanctionsList(
        string calldata entityId,
        bool sanctioned
    ) external onlyCompliance {
        sanctionsList[entityId] = sanctioned;

        Entity storage entity = entities[entityId];
        if (entity.registeredAt > 0) {
            entity.isSanctioned = sanctioned;
            if (sanctioned) {
                entity.kycStatus = KYCStatus.SANCTIONED;
                entity.riskScore = 100;
            }
        }

        emit SanctionsListUpdated(entityId, sanctioned, block.timestamp);
    }

    // === МОНИТОРИНГ ПЛАТЕЖЕЙ ===

    /**
     * @notice Записать платёж и проверить на AML
     */
    function recordPayment(
        string calldata fromEntity,
        string calldata toEntity,
        uint256 amount,
        string calldata procurementId,
        bytes32 documentHash
    ) external onlyOperator returns (uint256) {
        paymentCount++;
        uint256 newId = paymentCount;

        TransactionStatus initialStatus = TransactionStatus.NORMAL;

        // Проверка санкционного списка
        if (sanctionsList[fromEntity] || sanctionsList[toEntity]) {
            initialStatus = TransactionStatus.BLOCKED;
            _raiseAlert(newId, AlertType.SANCTIONS_HIT, "Entity in sanctions list");
            emit PaymentBlocked(newId, "Sanctions list match", block.timestamp);
        }

        // Проверка KYC
        Entity storage fromEnt = entities[fromEntity];
        Entity storage toEnt = entities[toEntity];

        if (fromEnt.registeredAt > 0 &&
            fromEnt.kycStatus != KYCStatus.VERIFIED &&
            initialStatus == TransactionStatus.NORMAL) {
            initialStatus = TransactionStatus.FLAGGED;
        }

        payments[newId] = PaymentRecord({
            paymentId: newId,
            fromEntity: fromEntity,
            toEntity: toEntity,
            amount: amount,
            procurementId: procurementId,
            status: initialStatus,
            timestamp: block.timestamp,
            documentHash: documentHash
        });

        entityPayments[fromEntity].push(newId);

        // Обновить статистику
        if (fromEnt.registeredAt > 0) {
            fromEnt.totalTransactions++;
            fromEnt.totalVolume += amount;
        }
        if (toEnt.registeredAt > 0) {
            toEnt.totalTransactions++;
            toEnt.totalVolume += amount;
        }

        emit PaymentRecorded(newId, fromEntity, toEntity, amount, block.timestamp);

        // Запуск AML-проверок
        _checkThreshold(newId, amount);
        _checkSplitting(fromEntity, amount);
        _checkRoundAmount(newId, amount);

        return newId;
    }

    /**
     * @notice Добавить FATF Travel Rule данные
     */
    function addTravelRuleData(
        uint256 paymentId,
        TravelRuleData calldata data
    ) external onlyOperator {
        require(payments[paymentId].timestamp > 0, "Payment not found");
        travelRuleRecords[paymentId] = data;
    }

    // === AML-ПРОВЕРКИ ===

    /**
     * @dev Проверка превышения порога
     */
    function _checkThreshold(uint256 paymentId, uint256 amount) internal {
        if (amount >= reportingThreshold) {
            _raiseAlert(
                paymentId,
                AlertType.THRESHOLD_EVASION,
                "Amount exceeds reporting threshold"
            );
        }
    }

    /**
     * @dev Обнаружение дробления платежей
     */
    function _checkSplitting(string memory fromEntity, uint256 amount) internal {
        uint256[] storage payIds = entityPayments[fromEntity];
        if (payIds.length < splittingCountThreshold) return;

        uint256 recentCount = 0;
        uint256 recentTotal = 0;

        for (uint256 i = payIds.length; i > 0 && i > payIds.length - 10; i--) {
            PaymentRecord storage p = payments[payIds[i - 1]];
            if (block.timestamp - p.timestamp <= splittingWindow) {
                recentCount++;
                recentTotal += p.amount;
            }
        }

        // Подозрение в дроблении: много мелких платежей, сумма >= порога
        if (recentCount >= splittingCountThreshold && recentTotal >= reportingThreshold) {
            _raiseAlert(
                payIds[payIds.length - 1],
                AlertType.SPLITTING,
                "Suspected payment splitting detected"
            );
        }
    }

    /**
     * @dev Обнаружение круглых сумм
     */
    function _checkRoundAmount(uint256 paymentId, uint256 amount) internal {
        // Проверка на круглые суммы (кратные 100 000)
        if (amount > 100_000_00 && amount % 100_000_00 == 0) {
            _raiseAlert(
                paymentId,
                AlertType.ROUND_AMOUNT,
                "Suspiciously round amount"
            );
        }
    }

    /**
     * @dev Создать AML-алерт
     */
    function _raiseAlert(
        uint256 paymentId,
        AlertType alertType,
        string memory description
    ) internal {
        alertCount++;
        alerts[alertCount] = AMLAlert({
            alertId: alertCount,
            paymentId: paymentId,
            alertType: alertType,
            description: description,
            timestamp: block.timestamp,
            resolved: false
        });

        emit AMLAlertRaised(alertCount, paymentId, alertType, block.timestamp);
    }

    // === БЛОКИРОВКА / РАЗБЛОКИРОВКА ===

    /**
     * @notice Заблокировать транзакцию
     */
    function blockPayment(uint256 paymentId, string calldata reason)
        external onlyCompliance
    {
        PaymentRecord storage payment = payments[paymentId];
        require(payment.timestamp > 0, "Payment not found");
        payment.status = TransactionStatus.BLOCKED;
        emit PaymentBlocked(paymentId, reason, block.timestamp);
    }

    /**
     * @notice Очистить транзакцию после проверки
     */
    function clearPayment(uint256 paymentId) external onlyCompliance {
        PaymentRecord storage payment = payments[paymentId];
        require(payment.timestamp > 0, "Payment not found");
        payment.status = TransactionStatus.CLEARED;
    }

    /**
     * @notice Разрешить алерт
     */
    function resolveAlert(uint256 alertId) external onlyCompliance {
        AMLAlert storage alert = alerts[alertId];
        require(alert.timestamp > 0, "Alert not found");
        alert.resolved = true;
    }

    // === ЗАПРОСЫ ===

    function getEntityPayments(string calldata entityId)
        external view
        returns (uint256[] memory)
    {
        return entityPayments[entityId];
    }

    function getPayment(uint256 paymentId)
        external view
        returns (PaymentRecord memory)
    {
        return payments[paymentId];
    }
}
