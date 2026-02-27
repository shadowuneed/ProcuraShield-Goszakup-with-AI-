// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ProcurementRegistry
 * @notice Реестр государственных закупок в блокчейне.
 * @dev Регистрирует хеши тендерной документации и отслеживает изменения.
 *
 * Функции:
 * - Регистрация тендера с хешем документации
 * - Версионирование изменений
 * - Временные метки всех событий
 * - Публичная верификация подлинности
 */
contract ProcurementRegistry {

    // === СТРУКТУРЫ ===

    struct Procurement {
        bytes32 documentHash;      // SHA-256 хеш документации
        string ipfsCid;            // IPFS CID оригинала
        address registeredBy;      // Кто зарегистрировал
        uint256 timestamp;         // Время регистрации
        uint256 versionCount;      // Количество версий
        bool exists;               // Существует ли запись
    }

    struct Version {
        bytes32 documentHash;      // Хеш версии
        string ipfsCid;            // IPFS CID версии
        string changeDescription;  // Описание изменений
        address changedBy;         // Кто внёс изменения
        uint256 timestamp;         // Время изменения
    }

    // === СОСТОЯНИЕ ===

    address public owner;
    mapping(string => Procurement) public procurements;  // externalId => Procurement
    mapping(string => Version[]) public versions;         // externalId => Version[]
    mapping(bytes32 => string) public hashToId;           // documentHash => externalId

    uint256 public totalRegistered;

    // === СОБЫТИЯ ===

    event ProcurementRegistered(
        string indexed externalId,
        bytes32 documentHash,
        string ipfsCid,
        address registeredBy,
        uint256 timestamp
    );

    event ProcurementUpdated(
        string indexed externalId,
        bytes32 newHash,
        string changeDescription,
        uint256 versionNumber,
        uint256 timestamp
    );

    // === МОДИФИКАТОРЫ ===

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this");
        _;
    }

    // === КОНСТРУКТОР ===

    constructor() {
        owner = msg.sender;
    }

    // === ФУНКЦИИ ===

    /**
     * @notice Регистрация нового тендера
     * @param externalId Внешний ID тендера (из ЕИС)
     * @param documentHash SHA-256 хеш документации
     * @param ipfsCid IPFS CID документа
     */
    function registerProcurement(
        string calldata externalId,
        bytes32 documentHash,
        string calldata ipfsCid
    ) external {
        require(!procurements[externalId].exists, "Procurement already registered");
        require(documentHash != bytes32(0), "Invalid document hash");

        procurements[externalId] = Procurement({
            documentHash: documentHash,
            ipfsCid: ipfsCid,
            registeredBy: msg.sender,
            timestamp: block.timestamp,
            versionCount: 1,
            exists: true
        });

        hashToId[documentHash] = externalId;
        totalRegistered++;

        // Сохраняем первую версию
        versions[externalId].push(Version({
            documentHash: documentHash,
            ipfsCid: ipfsCid,
            changeDescription: "Initial registration",
            changedBy: msg.sender,
            timestamp: block.timestamp
        }));

        emit ProcurementRegistered(
            externalId,
            documentHash,
            ipfsCid,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * @notice Обновление документации тендера (версионирование)
     * @param externalId ID тендера
     * @param newHash Новый хеш документации
     * @param newIpfsCid Новый IPFS CID
     * @param changeDescription Описание изменений
     */
    function updateProcurement(
        string calldata externalId,
        bytes32 newHash,
        string calldata newIpfsCid,
        string calldata changeDescription
    ) external {
        require(procurements[externalId].exists, "Procurement not found");

        Procurement storage proc = procurements[externalId];
        proc.documentHash = newHash;
        proc.ipfsCid = newIpfsCid;
        proc.versionCount++;

        hashToId[newHash] = externalId;

        versions[externalId].push(Version({
            documentHash: newHash,
            ipfsCid: newIpfsCid,
            changeDescription: changeDescription,
            changedBy: msg.sender,
            timestamp: block.timestamp
        }));

        emit ProcurementUpdated(
            externalId,
            newHash,
            changeDescription,
            proc.versionCount,
            block.timestamp
        );
    }

    /**
     * @notice Верификация документа по хешу
     * @param documentHash Хеш для проверки
     * @return exists Найден ли документ
     * @return externalId ID тендера
     * @return timestamp Время регистрации
     */
    function verifyDocument(bytes32 documentHash) 
        external view 
        returns (bool exists, string memory externalId, uint256 timestamp) 
    {
        externalId = hashToId[documentHash];
        if (bytes(externalId).length > 0 && procurements[externalId].exists) {
            return (true, externalId, procurements[externalId].timestamp);
        }
        return (false, "", 0);
    }

    /**
     * @notice Получить историю версий документа
     * @param externalId ID тендера
     * @return Version[] Массив версий
     */
    function getVersionHistory(string calldata externalId)
        external view
        returns (Version[] memory)
    {
        return versions[externalId];
    }

    /**
     * @notice Получить количество версий
     */
    function getVersionCount(string calldata externalId)
        external view
        returns (uint256)
    {
        return versions[externalId].length;
    }
}
