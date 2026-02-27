"""
ProcuraShield — Граф-анализ связей (Graph Neural Network)
Построение и анализ графа аффилированных лиц.

Узлы: поставщики, заказчики, физлица, адреса
Рёбра: участие, победы, аффилированность, общие адреса
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import structlog

logger = structlog.get_logger()


class GraphAnalyzer:
    """
    Построение и анализ графа связей между участниками госзакупок.
    Использует NetworkX для анализа и Louvain для community detection.
    """

    def __init__(self):
        import networkx as nx
        self.G = nx.Graph()
        self._node_data: Dict[str, Dict] = {}

    def build_graph(
        self,
        suppliers: List[Dict[str, Any]],
        procurements: List[Dict[str, Any]],
        persons: List[Dict[str, Any]],
        bids: List[Dict[str, Any]],
    ) -> None:
        """
        Построение графа из данных.
        """
        import networkx as nx

        self.G = nx.Graph()

        # Добавляем поставщиков как узлы
        for supplier in suppliers:
            node_id = f"supplier:{supplier['inn']}"
            self.G.add_node(node_id, type="supplier", **supplier)
            self._node_data[node_id] = supplier

        # Добавляем физлиц
        for person in persons:
            node_id = f"person:{person.get('inn', person.get('id', ''))}"
            self.G.add_node(node_id, type="person", **person)
            self._node_data[node_id] = person

        # Добавляем заказчиков
        customer_inns = set()
        for proc in procurements:
            inn = proc.get("customer_inn", "")
            if inn and inn not in customer_inns:
                customer_inns.add(inn)
                node_id = f"customer:{inn}"
                self.G.add_node(node_id, type="customer", name=proc.get("customer_name", ""))

        # Строим рёбра
        self._build_edges(suppliers, procurements, persons, bids)

        logger.info(
            "Граф построен",
            nodes=self.G.number_of_nodes(),
            edges=self.G.number_of_edges()
        )

    def _build_edges(
        self,
        suppliers: List[Dict[str, Any]],
        procurements: List[Dict[str, Any]],
        persons: List[Dict[str, Any]],
        bids: List[Dict[str, Any]],
    ) -> None:
        """Построение рёбер графа"""

        # 1. Связи поставщик → директор/учредитель
        for supplier in suppliers:
            s_node = f"supplier:{supplier['inn']}"

            # CEO
            ceo_inn = supplier.get("ceo_inn")
            if ceo_inn:
                p_node = f"person:{ceo_inn}"
                self.G.add_edge(s_node, p_node, type="ceo_of", weight=0.9)

            # Учредители
            founders = supplier.get("founder_names", []) or []
            for founder in founders:
                if isinstance(founder, dict) and founder.get("inn"):
                    f_node = f"person:{founder['inn']}"
                    self.G.add_edge(s_node, f_node, type="founder_of", weight=0.8)

        # 2. Общие адреса
        address_map = defaultdict(list)
        for supplier in suppliers:
            addr = supplier.get("legal_address", "")
            if addr and len(addr) > 10:
                # Нормализуем адрес (упрощённо)
                normalized = addr.lower().strip().replace(" ", "")
                address_map[normalized].append(supplier["inn"])

        for addr, inns in address_map.items():
            if len(inns) > 1:
                for i, inn1 in enumerate(inns):
                    for inn2 in inns[i + 1:]:
                        self.G.add_edge(
                            f"supplier:{inn1}",
                            f"supplier:{inn2}",
                            type="same_address",
                            weight=0.7
                        )

        # 3. Участие в тендерах
        for bid in bids:
            s_inn = bid.get("supplier_inn", "")
            c_inn = bid.get("customer_inn", "")
            if s_inn and c_inn:
                edge_type = "won" if bid.get("is_winner") else "bid_in"
                weight = 0.6 if bid.get("is_winner") else 0.3
                s_node = f"supplier:{s_inn}"
                c_node = f"customer:{c_inn}"
                if self.G.has_edge(s_node, c_node):
                    # Увеличиваем вес при повторных взаимодействиях
                    self.G[s_node][c_node]["weight"] = min(
                        1.0,
                        self.G[s_node][c_node]["weight"] + 0.1
                    )
                else:
                    self.G.add_edge(s_node, c_node, type=edge_type, weight=weight)

        # 4. Общие телефоны
        phone_map = defaultdict(list)
        for supplier in suppliers:
            phone = supplier.get("phone", "")
            if phone and len(phone) >= 10:
                normalized = phone.replace(" ", "").replace("-", "").replace("+", "")
                phone_map[normalized].append(supplier["inn"])

        for phone, inns in phone_map.items():
            if len(inns) > 1:
                for i, inn1 in enumerate(inns):
                    for inn2 in inns[i + 1:]:
                        self.G.add_edge(
                            f"supplier:{inn1}",
                            f"supplier:{inn2}",
                            type="same_phone",
                            weight=0.8
                        )

    def detect_communities(self, min_size: int = 3) -> List[Dict[str, Any]]:
        """
        Выявление сообществ (кластеров аффилированных лиц)
        с помощью алгоритма Louvain.
        """
        from community import community_louvain

        if self.G.number_of_nodes() < 3:
            return []

        partition = community_louvain.best_partition(self.G)

        # Группируем по сообществам
        communities = defaultdict(list)
        for node, comm_id in partition.items():
            communities[comm_id].append(node)

        # Фильтруем маленькие сообщества
        result = []
        for comm_id, members in communities.items():
            if len(members) >= min_size:
                # Анализируем состав сообщества
                suppliers_in = [m for m in members if m.startswith("supplier:")]
                persons_in = [m for m in members if m.startswith("person:")]

                # Вычисляем «подозрительность» сообщества
                suspicion = self._calculate_community_suspicion(members)

                result.append({
                    "community_id": comm_id,
                    "size": len(members),
                    "members": members,
                    "supplier_count": len(suppliers_in),
                    "person_count": len(persons_in),
                    "suspicion_score": suspicion,
                    "internal_edges": self._count_internal_edges(members),
                })

        return sorted(result, key=lambda c: c["suspicion_score"], reverse=True)

    def find_family_contracts(self) -> List[Dict[str, Any]]:
        """
        Выявление «семейных подрядов».
        Ищем поставщиков, которые поделяют общих директоров/учредителей
        и побеждают у одних и тех же заказчиков.
        """
        import networkx as nx

        family_groups = []

        # Ищем поставщиков, связанных через физлиц
        supplier_nodes = [n for n in self.G.nodes() if n.startswith("supplier:")]

        for i, s1 in enumerate(supplier_nodes):
            for s2 in supplier_nodes[i + 1:]:
                # Есть ли общие «соседи» типа person?
                s1_persons = {
                    n for n in self.G.neighbors(s1)
                    if n.startswith("person:")
                }
                s2_persons = {
                    n for n in self.G.neighbors(s2)
                    if n.startswith("person:")
                }

                common_persons = s1_persons & s2_persons
                if common_persons:
                    # Есть общие физлица — проверяем, побеждали ли оба
                    s1_customers = {
                        n for n in self.G.neighbors(s1)
                        if n.startswith("customer:")
                    }
                    s2_customers = {
                        n for n in self.G.neighbors(s2)
                        if n.startswith("customer:")
                    }
                    common_customers = s1_customers & s2_customers

                    if common_customers:
                        family_groups.append({
                            "supplier_1": s1,
                            "supplier_2": s2,
                            "common_persons": list(common_persons),
                            "common_customers": list(common_customers),
                            "risk": "HIGH" if len(common_persons) >= 2 else "MEDIUM",
                        })

        return family_groups

    def get_risk_subgraph(self, entity_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Получить подграф вокруг сущности до заданной глубины.
        Для визуализации в D3.js/Cytoscape.
        """
        import networkx as nx

        if entity_id not in self.G:
            return {"nodes": [], "edges": []}

        # BFS до нужной глубины
        subgraph_nodes = {entity_id}
        frontier = {entity_id}

        for _ in range(depth):
            new_frontier = set()
            for node in frontier:
                for neighbor in self.G.neighbors(node):
                    if neighbor not in subgraph_nodes:
                        new_frontier.add(neighbor)
                        subgraph_nodes.add(neighbor)
            frontier = new_frontier

        # Формируем данные для визуализации
        nodes = []
        for node in subgraph_nodes:
            node_type, node_id = node.split(":", 1)
            data = self._node_data.get(node, {})
            nodes.append({
                "id": node,
                "label": data.get("name", node_id[:12]),
                "type": node_type,
                "risk_score": data.get("risk_score"),
            })

        edges = []
        subgraph = self.G.subgraph(subgraph_nodes)
        for u, v, data in subgraph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "type": data.get("type", "unknown"),
                "weight": data.get("weight", 1.0),
            })

        return {"nodes": nodes, "edges": edges}

    def _calculate_community_suspicion(self, members: List[str]) -> float:
        """Расчёт «подозрительности» сообщества"""
        score = 0.0

        suppliers = [m for m in members if m.startswith("supplier:")]
        persons = [m for m in members if m.startswith("person:")]

        # Много поставщиков, связанных через мало физлиц
        if len(suppliers) >= 3 and len(persons) <= 2:
            score += 40.0

        # Проверяем плотность связей
        internal_edges = self._count_internal_edges(members)
        max_edges = len(members) * (len(members) - 1) / 2
        density = internal_edges / max(max_edges, 1)

        if density > 0.6:
            score += 30.0

        # Проверяем типы связей
        for m1 in members:
            for m2 in members:
                if m1 < m2 and self.G.has_edge(m1, m2):
                    edge_type = self.G[m1][m2].get("type", "")
                    if edge_type == "same_address":
                        score += 10.0
                    elif edge_type == "same_phone":
                        score += 15.0

        return min(100.0, score)

    def _count_internal_edges(self, members: List[str]) -> int:
        """Количество рёбер внутри группы"""
        count = 0
        member_set = set(members)
        for m in members:
            if m in self.G:
                for neighbor in self.G.neighbors(m):
                    if neighbor in member_set:
                        count += 1
        return count // 2  # Каждое ребро считается дважды
