// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title EvidenceVault
 * @notice Неизменяемое хранилище доказательств коррупции.
 * @dev Хранение хешей документов с ролевым доступом и уведомлением регулятора.
 *
 * Функции:
 * - Запись хеша доказательства (файл на IPFS)
 * - Ролевой доступ (аналитик, следователь, регулятор)
 * - Заморозка доказательств для суда
 * - Авто-уведомление регулятора при risk > 80
 */
contract EvidenceVault {

    // === ПЕРЕЧИСЛЕНИЯ ===

    enum EvidenceType {
        DOCUMENT,       // Документ тендера
        ANALYSIS,       // Результат AI-анализа
        SCREENSHOT,     // Скриншот
        COMMUNICATION,  // Переписка
        FINANCIAL,      // Финансовый документ
        WHISTLEBLOWER,  // Обращение информатора
        OTHER
    }

    enum AccessLevel {
        PUBLIC,         // Публичный доступ
        ANALYST,        // Только для аналитиков
        INVESTIGATOR,   // Только для следователей
        REGULATOR,      // Только для регулятора
        COURT           // Замороженные для суда
    }

    // === СТРУКТУРЫ ===

    struct Evidence {
        uint256 evidenceId;
        string procurementId;       // ID закупки
        bytes32 documentHash;       // SHA-256 хеш документа
        string ipfsCid;             // IPFS Content Identifier
        EvidenceType evidenceType;
        AccessLevel accessLevel;
        address submittedBy;
        uint256 timestamp;
        bool frozen;                // Заморожен для суда
        string description;
        uint8 riskScore;            // Связанный риск-скор
    }

    struct AccessGrant {
        address grantee;
        uint256 evidenceId;
        uint256 grantedAt;
        uint256 expiresAt;
    }

    // === СОСТОЯНИЕ ===

    address public owner;
    uint256 public evidenceCount;

    mapping(uint256 => Evidence) public evidences;
    mapping(bytes32 => uint256) public hashToEvidence;
    mapping(string => uint256[]) public procurementEvidences;

    // Роли
    mapping(address => bool) public analysts;
    mapping(address => bool) public investigators;
    mapping(address => bool) public regulators;

    // Гранты доступа
    mapping(uint256 => AccessGrant[]) public accessGrants;

    // Порог автоуведомления регулятора
    uint8 public regulatorAlertThreshold = 80;

    // === СОБЫТИЯ ===

    event EvidenceStored(
        uint256 indexed evidenceId,
        string procurementId,
        bytes32 documentHash,
        string ipfsCid,
        EvidenceType evidenceType,
        uint256 timestamp
    );

    event EvidenceFrozen(
        uint256 indexed evidenceId,
        address frozenBy,
        uint256 timestamp
    );

    event RegulatorAlerted(
        uint256 indexed evidenceId,
        string procurementId,
        uint8 riskScore,
        uint256 timestamp
    );

    event AccessGranted(
        uint256 indexed evidenceId,
        address grantee,
        uint256 expiresAt,
        uint256 timestamp
    );

    // === МОДИФИКАТОРЫ ===

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    modifier onlyAnalystOrAbove() {
        require(
            analysts[msg.sender] ||
            investigators[msg.sender] ||
            regulators[msg.sender] ||
            msg.sender == owner,
            "Insufficient role"
        );
        _;
    }

    modifier onlyInvestigatorOrAbove() {
        require(
            investigators[msg.sender] ||
            regulators[msg.sender] ||
            msg.sender == owner,
            "Insufficient role"
        );
        _;
    }

    // === КОНСТРУКТОР ===

    constructor() {
        owner = msg.sender;
        analysts[msg.sender] = true;
        investigators[msg.sender] = true;
        regulators[msg.sender] = true;
    }

    // === УПРАВЛЕНИЕ РОЛЯМИ ===

    function setAnalyst(address _addr, bool _status) external onlyOwner {
        analysts[_addr] = _status;
    }

    function setInvestigator(address _addr, bool _status) external onlyOwner {
        investigators[_addr] = _status;
    }

    function setRegulator(address _addr, bool _status) external onlyOwner {
        regulators[_addr] = _status;
    }

    // === ОСНОВНЫЕ ФУНКЦИИ ===

    /**
     * @notice Сохранить хеш доказательства
     * @param procurementId ID закупки
     * @param documentHash SHA-256 хеш документа
     * @param ipfsCid IPFS CID для получения документа
     * @param evidenceType Тип доказательства
     * @param accessLevel Уровень доступа
     * @param description Описание
     * @param riskScore Связанный риск-скор (0-100)
     */
    function storeEvidence(
        string calldata procurementId,
        bytes32 documentHash,
        string calldata ipfsCid,
        EvidenceType evidenceType,
        AccessLevel accessLevel,
        string calldata description,
        uint8 riskScore
    ) external onlyAnalystOrAbove returns (uint256) {
        require(riskScore <= 100, "Score must be 0-100");
        require(hashToEvidence[documentHash] == 0, "Evidence already exists");

        evidenceCount++;
        uint256 newId = evidenceCount;

        evidences[newId] = Evidence({
            evidenceId: newId,
            procurementId: procurementId,
            documentHash: documentHash,
            ipfsCid: ipfsCid,
            evidenceType: evidenceType,
            accessLevel: accessLevel,
            submittedBy: msg.sender,
            timestamp: block.timestamp,
            frozen: false,
            description: description,
            riskScore: riskScore
        });

        hashToEvidence[documentHash] = newId;
        procurementEvidences[procurementId].push(newId);

        emit EvidenceStored(
            newId, procurementId, documentHash,
            ipfsCid, evidenceType, block.timestamp
        );

        // Авто-уведомление регулятора при высоком риске
        if (riskScore >= regulatorAlertThreshold) {
            emit RegulatorAlerted(newId, procurementId, riskScore, block.timestamp);
        }

        return newId;
    }

    /**
     * @notice Заморозить доказательство для суда
     */
    function freezeEvidence(uint256 evidenceId) external onlyInvestigatorOrAbove {
        Evidence storage evidence = evidences[evidenceId];
        require(evidence.timestamp > 0, "Evidence not found");
        require(!evidence.frozen, "Already frozen");

        evidence.frozen = true;
        evidence.accessLevel = AccessLevel.COURT;

        emit EvidenceFrozen(evidenceId, msg.sender, block.timestamp);
    }

    /**
     * @notice Предоставить временный доступ к доказательству
     */
    function grantAccess(
        uint256 evidenceId,
        address grantee,
        uint256 duration
    ) external onlyInvestigatorOrAbove {
        Evidence storage evidence = evidences[evidenceId];
        require(evidence.timestamp > 0, "Evidence not found");

        uint256 expiresAt = block.timestamp + duration;

        accessGrants[evidenceId].push(AccessGrant({
            grantee: grantee,
            evidenceId: evidenceId,
            grantedAt: block.timestamp,
            expiresAt: expiresAt
        }));

        emit AccessGranted(evidenceId, grantee, expiresAt, block.timestamp);
    }

    /**
     * @notice Верификация хеша документа
     */
    function verifyDocument(bytes32 documentHash)
        external view
        returns (bool exists, uint256 evidenceId, uint256 timestamp)
    {
        uint256 id = hashToEvidence[documentHash];
        if (id == 0) {
            return (false, 0, 0);
        }
        return (true, id, evidences[id].timestamp);
    }

    /**
     * @notice Получить все доказательства по закупке
     */
    function getEvidencesByProcurement(string calldata procurementId)
        external view
        returns (uint256[] memory)
    {
        return procurementEvidences[procurementId];
    }

    /**
     * @notice Проверить доступ пользователя
     */
    function hasAccess(uint256 evidenceId, address user)
        external view
        returns (bool)
    {
        Evidence storage evidence = evidences[evidenceId];

        // Владелец имеет доступ ко всему
        if (user == owner) return true;

        // Проверка уровня доступа
        if (evidence.accessLevel == AccessLevel.PUBLIC) return true;
        if (evidence.accessLevel == AccessLevel.ANALYST && analysts[user]) return true;
        if (evidence.accessLevel == AccessLevel.INVESTIGATOR && investigators[user]) return true;
        if (evidence.accessLevel == AccessLevel.REGULATOR && regulators[user]) return true;

        // Проверка грантов
        AccessGrant[] storage grants = accessGrants[evidenceId];
        for (uint256 i = 0; i < grants.length; i++) {
            if (grants[i].grantee == user && grants[i].expiresAt > block.timestamp) {
                return true;
            }
        }

        return false;
    }
}
