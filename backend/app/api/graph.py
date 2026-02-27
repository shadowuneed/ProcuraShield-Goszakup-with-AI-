"""
ProcuraShield — API: Граф связей
Построение и запрос графа аффилированных лиц
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import structlog

from app.core.database import get_db
from app.core.security import get_current_user, require_analyst
from app.schemas import GraphResponse, GraphNode, GraphEdge

logger = structlog.get_logger()
router = APIRouter()


@router.get("/connections/{entity_id}", response_model=GraphResponse)
async def get_entity_graph(
    entity_id: UUID,
    depth: int = Query(2, ge=1, le=5),
    entity_type: str = Query("supplier", pattern=r"^(supplier|person|procurement)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """
    Получить граф связей для сущности.
    Рекурсивно обходит связи до указанной глубины.
    """
    nodes = []
    edges = []
    visited = set()

    await _build_graph_recursive(
        db, str(entity_id), entity_type, depth, nodes, edges, visited
    )

    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/communities", response_model=GraphResponse)
async def detect_communities(
    min_size: int = Query(3, ge=2),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """
    Выявление кластеров аффилированных лиц (Louvain algorithm).
    Возвращает граф с пометками сообществ.
    """
    import networkx as nx
    from community import community_louvain

    # Загружаем все связи
    result = await db.execute(text("""
        SELECT source_type, source_id::text, target_type, target_id::text, 
               connection_type, strength
        FROM connections
    """))
    rows = result.fetchall()

    # Строим NetworkX граф
    G = nx.Graph()
    for row in rows:
        source_key = f"{row[0]}:{row[1]}"
        target_key = f"{row[2]}:{row[3]}"
        G.add_edge(source_key, target_key, weight=float(row[5] or 1.0), type=row[4])

    if len(G.nodes()) == 0:
        return GraphResponse(nodes=[], edges=[], communities=[])

    # Louvain community detection
    partition = community_louvain.best_partition(G)

    # Формируем ответ
    nodes = []
    for node_key, community_id in partition.items():
        node_type, node_id = node_key.split(":", 1)
        nodes.append(GraphNode(
            id=node_id,
            label=node_key,
            type=node_type,
            metadata={"community": community_id}
        ))

    edges_out = []
    for u, v, data in G.edges(data=True):
        u_type, u_id = u.split(":", 1)
        v_type, v_id = v.split(":", 1)
        edges_out.append(GraphEdge(
            source=u_id,
            target=v_id,
            type=data.get("type", "unknown"),
            strength=data.get("weight", 1.0)
        ))

    # Группируем сообщества
    communities = {}
    for node_key, community_id in partition.items():
        if community_id not in communities:
            communities[community_id] = []
        communities[community_id].append(node_key)

    community_list = [
        {"id": cid, "members": members, "size": len(members)}
        for cid, members in communities.items()
        if len(members) >= min_size
    ]

    return GraphResponse(nodes=nodes, edges=edges_out, communities=community_list)


@router.get("/supplier/{supplier_id}/affiliations")
async def get_supplier_affiliations(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_analyst),
):
    """Получить все аффилированные связи поставщика"""
    result = await db.execute(text("""
        SELECT c.*, 
               s.name as connected_supplier_name,
               p.full_name as connected_person_name
        FROM connections c
        LEFT JOIN suppliers s ON c.target_id = s.id AND c.target_type = 'supplier'
        LEFT JOIN persons p ON c.target_id = p.id AND c.target_type = 'person'
        WHERE (c.source_id = :sid AND c.source_type = 'supplier')
           OR (c.target_id = :sid AND c.target_type = 'supplier')
    """), {"sid": str(supplier_id)})

    affiliations = []
    for row in result.fetchall():
        affiliations.append({
            "connection_type": row.connection_type,
            "strength": float(row.strength or 1.0),
            "connected_name": row.connected_supplier_name or row.connected_person_name,
            "evidence": row.evidence,
        })

    return {"supplier_id": str(supplier_id), "affiliations": affiliations}


async def _build_graph_recursive(
    db: AsyncSession,
    entity_id: str,
    entity_type: str,
    depth: int,
    nodes: list,
    edges: list,
    visited: set,
):
    """Рекурсивное построение графа связей"""
    if depth <= 0 or entity_id in visited:
        return

    visited.add(entity_id)

    # Добавляем текущий узел
    nodes.append(GraphNode(
        id=entity_id,
        label=f"{entity_type}:{entity_id[:8]}",
        type=entity_type,
    ))

    # Находим исходящие связи
    result = await db.execute(text("""
        SELECT target_type, target_id::text, connection_type, strength
        FROM connections
        WHERE source_id = :eid AND source_type = :etype
        UNION
        SELECT source_type, source_id::text, connection_type, strength
        FROM connections
        WHERE target_id = :eid AND target_type = :etype
    """), {"eid": entity_id, "etype": entity_type})

    for row in result.fetchall():
        target_type, target_id, conn_type, strength = row

        edges.append(GraphEdge(
            source=entity_id,
            target=target_id,
            type=conn_type,
            strength=float(strength or 1.0)
        ))

        await _build_graph_recursive(
            db, target_id, target_type, depth - 1, nodes, edges, visited
        )
