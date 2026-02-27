// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title RiskOracle
 * @notice Запись результатов AI-анализа в блокчейн.
 * @dev Oracle для хранения риск-скоров с механизмом голосования.
 *
 * Функции:
 * - Запись AI risk score
 * - Голосование валидаторов за финальный скор
 * - Механизм оспаривания
 */
contract RiskOracle {

    // === СТРУКТУРЫ ===

    struct RiskRecord {
        string procurementId;       // ID закупки
        uint8 aiScore;              // AI Risk Score (0-100)
        uint8 finalScore;           // Финальный скор после голосования
        string riskLevel;           // "green", "yellow", "orange", "red"
        bytes32 analysisHash;       // Хеш полного отчёта анализа
        address submittedBy;        // Кто отправил результат
        uint256 timestamp;
        uint256 validatorVotes;     // Количество голосов
        bool disputed;              // Оспорен ли результат
        bool finalized;             // Финализирован
    }

    struct Vote {
        address validator;
        uint8 score;
        string comment;
        uint256 timestamp;
    }

    struct Dispute {
        address disputedBy;
        string reason;
        uint256 timestamp;
        bool resolved;
        string resolution;
    }

    // === СОСТОЯНИЕ ===

    address public owner;
    mapping(address => bool) public validators;
    uint256 public validatorCount;

    mapping(string => RiskRecord) public riskRecords;
    mapping(string => Vote[]) public votes;
    mapping(string => Dispute[]) public disputes;

    uint256 public minVotesForFinalization = 3;

    // === СОБЫТИЯ ===

    event RiskScoreSubmitted(
        string indexed procurementId,
        uint8 aiScore,
        string riskLevel,
        uint256 timestamp
    );

    event ValidatorVoted(
        string indexed procurementId,
        address validator,
        uint8 score,
        uint256 timestamp
    );

    event RiskFinalized(
        string indexed procurementId,
        uint8 finalScore,
        uint256 timestamp
    );

    event DisputeRaised(
        string indexed procurementId,
        address disputedBy,
        string reason,
        uint256 timestamp
    );

    // === МОДИФИКАТОРЫ ===

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    modifier onlyValidator() {
        require(validators[msg.sender], "Not a validator");
        _;
    }

    // === КОНСТРУКТОР ===

    constructor() {
        owner = msg.sender;
        validators[msg.sender] = true;
        validatorCount = 1;
    }

    // === УПРАВЛЕНИЕ ВАЛИДАТОРАМИ ===

    function addValidator(address _validator) external onlyOwner {
        require(!validators[_validator], "Already a validator");
        validators[_validator] = true;
        validatorCount++;
    }

    function removeValidator(address _validator) external onlyOwner {
        require(validators[_validator], "Not a validator");
        require(_validator != owner, "Cannot remove owner");
        validators[_validator] = false;
        validatorCount--;
    }

    // === ОСНОВНЫЕ ФУНКЦИИ ===

    /**
     * @notice Отправить результат AI-анализа
     */
    function submitRiskScore(
        string calldata procurementId,
        uint8 aiScore,
        string calldata riskLevel,
        bytes32 analysisHash
    ) external onlyValidator {
        require(aiScore <= 100, "Score must be 0-100");

        riskRecords[procurementId] = RiskRecord({
            procurementId: procurementId,
            aiScore: aiScore,
            finalScore: aiScore,
            riskLevel: riskLevel,
            analysisHash: analysisHash,
            submittedBy: msg.sender,
            timestamp: block.timestamp,
            validatorVotes: 0,
            disputed: false,
            finalized: false
        });

        emit RiskScoreSubmitted(procurementId, aiScore, riskLevel, block.timestamp);
    }

    /**
     * @notice Голосование валидатора за скор
     */
    function vote(
        string calldata procurementId,
        uint8 score,
        string calldata comment
    ) external onlyValidator {
        require(score <= 100, "Score must be 0-100");
        RiskRecord storage record = riskRecords[procurementId];
        require(record.timestamp > 0, "Record not found");
        require(!record.finalized, "Already finalized");

        // Проверяем, не голосовал ли уже
        Vote[] storage voteList = votes[procurementId];
        for (uint256 i = 0; i < voteList.length; i++) {
            require(voteList[i].validator != msg.sender, "Already voted");
        }

        voteList.push(Vote({
            validator: msg.sender,
            score: score,
            comment: comment,
            timestamp: block.timestamp
        }));

        record.validatorVotes++;

        emit ValidatorVoted(procurementId, msg.sender, score, block.timestamp);

        // Автоматическая финализация при достаточном количестве голосов
        if (record.validatorVotes >= minVotesForFinalization) {
            _finalize(procurementId);
        }
    }

    /**
     * @notice Оспорить результат анализа
     */
    function raiseDispute(
        string calldata procurementId,
        string calldata reason
    ) external {
        RiskRecord storage record = riskRecords[procurementId];
        require(record.timestamp > 0, "Record not found");

        record.disputed = true;
        record.finalized = false;

        disputes[procurementId].push(Dispute({
            disputedBy: msg.sender,
            reason: reason,
            timestamp: block.timestamp,
            resolved: false,
            resolution: ""
        }));

        emit DisputeRaised(procurementId, msg.sender, reason, block.timestamp);
    }

    // === ВНУТРЕННИЕ ===

    function _finalize(string memory procurementId) internal {
        Vote[] storage voteList = votes[procurementId];
        RiskRecord storage record = riskRecords[procurementId];

        // Средневзвешенный скор (AI + голоса валидаторов)
        uint256 totalScore = uint256(record.aiScore); // AI вес = 1
        uint256 weightCount = 1;

        for (uint256 i = 0; i < voteList.length; i++) {
            totalScore += uint256(voteList[i].score);
            weightCount++;
        }

        record.finalScore = uint8(totalScore / weightCount);
        record.finalized = true;

        emit RiskFinalized(procurementId, record.finalScore, block.timestamp);
    }

    /**
     * @notice Получить запись о риске
     */
    function getRiskRecord(string calldata procurementId)
        external view
        returns (RiskRecord memory)
    {
        return riskRecords[procurementId];
    }

    /**
     * @notice Получить голоса по тендеру
     */
    function getVotes(string calldata procurementId)
        external view
        returns (Vote[] memory)
    {
        return votes[procurementId];
    }
}
