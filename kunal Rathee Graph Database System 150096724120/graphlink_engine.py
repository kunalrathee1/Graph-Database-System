"""
GraphLink Distributed Graph Database System
============================================
A Python-based prototype implementing core concepts of a distributed graph
database, including:
  - Index-Free Adjacency (IFA) storage model
  - Secondary property indexing (O(1) lookups)
  - BFS-based multi-hop relationship traversal
  - Dijkstra's shortest path algorithm
  - Fraud detection pattern matching
  - Recommendation engine traversal
  - Partition-aware distributed node store simulation

Author  : Kunal Rathee
Subject : System Design – Final Examination
Topic   : GraphLink – Distributed Graph Database System
"""

import heapq
import hashlib
import random
import time
from collections import deque, defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple


# ===========================================================================
# SECTION 1: CORE DATA STRUCTURES
# ===========================================================================

class Node:
    """Represents a graph node (vertex) with labels and property map."""

    def __init__(self, node_id: str, labels: List[str], properties: Dict[str, Any]):
        self.node_id   = node_id
        self.labels    = set(labels)
        self.properties = properties
        self.created_at = time.time()

    def __repr__(self):
        return f"Node(id={self.node_id!r}, labels={self.labels}, props={self.properties})"


class Edge:
    """Represents a directed relationship (edge) between two nodes."""

    def __init__(self, src_id: str, target_id: str, rel_type: str,
                 properties: Dict[str, Any]):
        self.src_id     = src_id
        self.target_id  = target_id
        self.rel_type   = rel_type
        self.properties = properties
        self.edge_id    = hashlib.md5(
            f"{src_id}-{rel_type}-{target_id}".encode()
        ).hexdigest()[:12]
        self.created_at = time.time()

    def __repr__(self):
        return (f"Edge({self.src_id!r} --[{self.rel_type}]--> "
                f"{self.target_id!r}, props={self.properties})")


# ===========================================================================
# SECTION 2: GRAPH STORAGE ENGINE  (Index-Free Adjacency Model)
# ===========================================================================

class GraphStorageEngine:
    """
    Core in-memory graph storage engine.

    Uses Index-Free Adjacency (IFA): each node holds direct references
    (pointers) to its neighbouring edge records, eliminating costly
    global index scans during traversal – mirroring how Neo4j stores
    data on disk.

    Data layout
    -----------
    nodes           : node_id → Node object
    adjacency_list  : node_id → [(target_id, rel_type, edge_props), ...]
    secondary_index : prop_name → {prop_value → set(node_ids)}
    label_index     : label → set(node_ids)
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.adjacency_list: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = {}
        self.secondary_index: Dict[str, Dict[Any, Set[str]]] = {}
        self.label_index: Dict[str, Set[str]] = defaultdict(set)
        self.edge_count: int = 0

    # ------------------------------------------------------------------
    # Node Operations
    # ------------------------------------------------------------------

    def create_node(self, node_id: str, labels: List[str],
                    properties: Dict[str, Any]) -> bool:
        """
        Creates a node and updates secondary/label indices.
        Time Complexity: O(p) where p = number of properties.
        """
        if node_id in self.nodes:
            print(f"[WARN] Node '{node_id}' already exists – skipping.")
            return False

        node = Node(node_id, labels, properties)
        self.nodes[node_id] = node
        self.adjacency_list[node_id] = []

        # Update label index
        for label in labels:
            self.label_index[label].add(node_id)

        # Update secondary property index
        for prop_name, prop_val in properties.items():
            if prop_name not in self.secondary_index:
                self.secondary_index[prop_name] = {}
            self.secondary_index[prop_name].setdefault(prop_val, set()).add(node_id)

        return True

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    # ------------------------------------------------------------------
    # Edge Operations
    # ------------------------------------------------------------------

    def create_edge(self, src_id: str, target_id: str, rel_type: str,
                    properties: Dict[str, Any]) -> bool:
        """
        Creates a directed edge between two existing nodes.
        Enforces referential integrity before insertion.
        Time Complexity: O(1) amortised.
        """
        if src_id not in self.nodes:
            print(f"[ERROR] Source node '{src_id}' not found – referential integrity violation.")
            return False
        if target_id not in self.nodes:
            print(f"[ERROR] Target node '{target_id}' not found – referential integrity violation.")
            return False

        self.adjacency_list[src_id].append((target_id, rel_type, properties))
        self.edge_count += 1
        return True

    def get_neighbors(self, node_id: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Returns all outgoing neighbours of a node via Index-Free Adjacency.
        Direct memory reference – no index scan needed.
        Time Complexity: O(degree(node)).
        """
        return self.adjacency_list.get(node_id, [])

    # ------------------------------------------------------------------
    # Index-Based Lookups
    # ------------------------------------------------------------------

    def find_nodes_by_property(self, prop_name: str,
                                prop_value: Any) -> List[str]:
        """O(1) property-value lookup via secondary index."""
        return list(
            self.secondary_index.get(prop_name, {}).get(prop_value, set())
        )

    def find_nodes_by_label(self, label: str) -> List[str]:
        """O(1) label lookup via label index."""
        return list(self.label_index.get(label, set()))

    # ------------------------------------------------------------------
    # Graph Statistics
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, int]:
        return {
            "total_nodes": len(self.nodes),
            "total_edges": self.edge_count,
            "labels":      len(self.label_index),
            "index_keys":  len(self.secondary_index),
        }


# ===========================================================================
# SECTION 3: TRAVERSAL PROCESSOR
# ===========================================================================

class TraversalProcessor:
    """
    Implements multiple graph traversal strategies on top of a
    GraphStorageEngine instance.

    Algorithms
    ----------
    bfs_traversal         – Breadth-First Search (level-order exploration)
    dfs_traversal         – Depth-First Search (deep-path exploration)
    shortest_path_dijkstra – Weighted shortest path (Dijkstra's algorithm)
    multi_hop_friends      – Social network k-hop neighbourhood
    detect_fraud_ring      – Cyclic relationship detector for fraud rings
    """

    def __init__(self, engine: GraphStorageEngine):
        self.engine = engine

    # ------------------------------------------------------------------
    # BFS Traversal
    # ------------------------------------------------------------------

    def bfs_traversal(self, start_id: str,
                      max_depth: int = 3) -> Dict[int, List[str]]:
        """
        Breadth-First Search exploring nodes level by level.

        Returns a dict mapping depth → list of node_ids discovered at
        that depth. Used for neighbour discovery, social graph expansion,
        and recommendation pre-computations.

        Time Complexity : O(V + E)
        Space Complexity: O(V)
        """
        if start_id not in self.engine.nodes:
            return {}

        visited  : Set[str] = {start_id}
        queue    : deque    = deque([(start_id, 0)])
        result   : Dict[int, List[str]] = defaultdict(list)
        result[0].append(start_id)

        while queue:
            node_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for target_id, _, _ in self.engine.get_neighbors(node_id):
                if target_id not in visited:
                    visited.add(target_id)
                    queue.append((target_id, depth + 1))
                    result[depth + 1].append(target_id)

        return dict(result)

    # ------------------------------------------------------------------
    # DFS Traversal
    # ------------------------------------------------------------------

    def dfs_traversal(self, start_id: str,
                      max_depth: int = 5) -> List[str]:
        """
        Depth-First Search returning all reachable nodes.

        Used for dependency resolution, cycle detection preparation,
        and deep-path pattern matching.

        Time Complexity : O(V + E)
        Space Complexity: O(V)
        """
        if start_id not in self.engine.nodes:
            return []

        visited  : Set[str]  = set()
        result   : List[str] = []
        stack    : List[Tuple[str, int]] = [(start_id, 0)]

        while stack:
            node_id, depth = stack.pop()
            if node_id in visited or depth > max_depth:
                continue
            visited.add(node_id)
            result.append(node_id)

            for target_id, _, _ in self.engine.get_neighbors(node_id):
                if target_id not in visited:
                    stack.append((target_id, depth + 1))

        return result

    # ------------------------------------------------------------------
    # Dijkstra's Weighted Shortest Path
    # ------------------------------------------------------------------

    def shortest_path_dijkstra(
            self,
            start_id: str,
            end_id: str,
            weight_property: str = "weight"
    ) -> Optional[Tuple[float, List[str]]]:
        """
        Computes the minimum-weight path between two nodes using
        Dijkstra's algorithm with a min-heap priority queue.

        This mirrors the PathFinder component inside a production graph
        database query engine (e.g., Neo4j's shortestPath() procedure).

        Parameters
        ----------
        start_id        : origin node identifier
        end_id          : destination node identifier
        weight_property : edge property key to use as traversal cost

        Returns
        -------
        (total_cost, path_list) on success, None if unreachable.

        Time Complexity : O((V + E) log V)
        Space Complexity: O(V)
        """
        if start_id not in self.engine.nodes or end_id not in self.engine.nodes:
            print("[ERROR] One or both nodes do not exist in the graph.")
            return None

        # (cumulative_cost, node_id, path_so_far)
        pq      : List[Tuple[float, str, List[str]]] = [(0.0, start_id, [start_id])]
        visited : Set[str] = set()

        while pq:
            cost, current, path = heapq.heappop(pq)

            if current == end_id:
                return cost, path

            if current in visited:
                continue
            visited.add(current)

            for target_id, _, edge_props in self.engine.get_neighbors(current):
                if target_id not in visited:
                    edge_weight = float(edge_props.get(weight_property, 1.0))
                    heapq.heappush(pq, (cost + edge_weight,
                                        target_id,
                                        path + [target_id]))

        return None  # Destination unreachable

    # ------------------------------------------------------------------
    # K-Hop Social Network Expansion
    # ------------------------------------------------------------------

    def multi_hop_friends(self, user_id: str,
                          hops: int = 2) -> Dict[str, int]:
        """
        Returns all nodes reachable within `hops` relationship steps,
        mapped to their minimum hop distance from the source.

        Typical use: "Friends of Friends" recommendation in social graphs.
        """
        distances: Dict[str, int] = {user_id: 0}
        queue    = deque([(user_id, 0)])

        while queue:
            node_id, depth = queue.popleft()
            if depth >= hops:
                continue

            for target_id, _, _ in self.engine.get_neighbors(node_id):
                if target_id not in distances:
                    distances[target_id] = depth + 1
                    queue.append((target_id, depth + 1))

        # Exclude the source itself
        distances.pop(user_id, None)
        return distances

    # ------------------------------------------------------------------
    # Fraud Ring Detection (Cycle Detector)
    # ------------------------------------------------------------------

    def detect_fraud_ring(self, start_id: str,
                          max_depth: int = 6) -> Optional[List[str]]:
        """
        Detects cyclic paths originating and terminating at `start_id`
        within `max_depth` hops – a hallmark of coordinated fraud rings.

        Uses DFS with path tracking instead of a simple visited set,
        allowing revisit of start node.

        Returns the cycle path if found, else None.
        """
        def dfs_cycle(node_id: str, path: List[str],
                      depth: int) -> Optional[List[str]]:
            if depth > max_depth:
                return None

            for target_id, rel_type, _ in self.engine.get_neighbors(node_id):
                # Found a cycle back to origin
                if target_id == start_id and len(path) > 1:
                    return path + [start_id]

                # Only allow revisit of non-origin nodes not already in path
                if target_id not in path:
                    result = dfs_cycle(target_id, path + [target_id], depth + 1)
                    if result:
                        return result
            return None

        if start_id not in self.engine.nodes:
            return None

        return dfs_cycle(start_id, [start_id], 0)


# ===========================================================================
# SECTION 4: QUERY OPTIMIZER (Cost-Based)
# ===========================================================================

class QueryOptimizer:
    """
    Simulates a rule-based / cost-based query optimizer that selects
    the most efficient traversal strategy given the query type and
    available index information.
    """

    def __init__(self, engine: GraphStorageEngine):
        self.engine = engine

    def optimize(self, query_type: str, params: Dict[str, Any]) -> str:
        """
        Returns the recommended execution strategy for a given query.

        Query Types
        -----------
        "property_lookup"  → Use Secondary Index (O(1))
        "label_scan"       → Use Label Index (O(1))
        "shortest_path"    → Use Dijkstra with IFA traversal
        "neighborhood"     → Use BFS limited to depth
        "fraud_detection"  → Use cycle-detecting DFS
        """
        strategies = {
            "property_lookup": (
                "→ PLAN: Secondary Index Scan → O(1) hash lookup on "
                f"property '{params.get('prop', '?')}'"
            ),
            "label_scan": (
                "→ PLAN: Label Index Scan → O(1) set retrieval for "
                f"label '{params.get('label', '?')}'"
            ),
            "shortest_path": (
                "→ PLAN: Dijkstra Shortest Path → IFA neighbour iteration "
                "with min-heap priority queue → O((V+E) log V)"
            ),
            "neighborhood": (
                f"→ PLAN: BFS Traversal → capped at depth "
                f"{params.get('depth', 2)} → O(V + E) worst-case"
            ),
            "fraud_detection": (
                "→ PLAN: Cycle-Detecting DFS → path-tracking stack → "
                f"max depth {params.get('max_depth', 6)}"
            ),
        }
        plan = strategies.get(query_type, "→ PLAN: Full Graph Scan (no index available)")
        print(f"[QueryOptimizer] Query='{query_type}' | {plan}")
        return plan


# ===========================================================================
# SECTION 5: DISTRIBUTED PARTITION MANAGER (Simulation)
# ===========================================================================

class PartitionManager:
    """
    Simulates consistent-hash-based graph partitioning across multiple
    virtual shards.  In a real deployment (e.g., Amazon Neptune, JanusGraph),
    this layer maps node IDs to physical cluster nodes.

    Strategy: Vertex-cut partitioning – each node is assigned to exactly
    one shard; edges crossing shards are handled via ghost/mirror nodes.
    """

    def __init__(self, num_partitions: int = 4):
        self.num_partitions = num_partitions
        self.partition_map  : Dict[str, int] = {}

    def assign_partition(self, node_id: str) -> int:
        """Consistent-hash partition assignment."""
        shard = int(hashlib.md5(node_id.encode()).hexdigest(), 16) % self.num_partitions
        self.partition_map[node_id] = shard
        return shard

    def get_partition(self, node_id: str) -> int:
        if node_id not in self.partition_map:
            return self.assign_partition(node_id)
        return self.partition_map[node_id]

    def partition_stats(self) -> Dict[int, int]:
        """Returns the node count per shard for load analysis."""
        counts: Dict[int, int] = defaultdict(int)
        for shard in self.partition_map.values():
            counts[shard] += 1
        return dict(counts)


# ===========================================================================
# SECTION 6: REPLICATION MANAGER (Leader–Follower Simulation)
# ===========================================================================

class ReplicationManager:
    """
    Simulates a leader–follower replication model.
    Write operations go to the leader; reads can be served by followers
    with eventual consistency guarantees.
    """

    def __init__(self, num_followers: int = 2):
        self.leader_log   : List[Dict[str, Any]] = []
        self.followers     = [[] for _ in range(num_followers)]
        self.repl_lag_ms   = 0.0   # simulated replication lag in ms

    def write_to_leader(self, operation: Dict[str, Any]) -> bool:
        """Appends an operation record to the leader's write-ahead log."""
        operation["timestamp"] = time.time()
        self.leader_log.append(operation)
        return True

    def replicate_to_followers(self) -> None:
        """Propagates the leader log to all followers (async simulation)."""
        simulated_lag = random.uniform(1, 15)   # 1–15 ms network lag
        self.repl_lag_ms = simulated_lag
        for follower in self.followers:
            follower.clear()
            follower.extend(self.leader_log)
        print(f"[Replication] Synced {len(self.leader_log)} log entries "
              f"to {len(self.followers)} follower(s) "
              f"(simulated lag: {simulated_lag:.2f} ms)")

    def is_consistent(self) -> bool:
        """Checks if all followers are in sync with the leader."""
        return all(f == self.leader_log for f in self.followers)


# ===========================================================================
# SECTION 7: DEMO / TEST DRIVER
# ===========================================================================

def print_section(title: str) -> None:
    width = 65
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def run_demo():
    """
    End-to-end demonstration of GraphLink capabilities covering:
      1. Node & edge creation with IFA storage
      2. Secondary index property lookups
      3. Label-based index lookups
      4. Dijkstra shortest-path traversal
      5. BFS neighbourhood expansion
      6. DFS full-graph reachability
      7. Fraud ring cycle detection
      8. Query optimizer plan selection
      9. Distributed partition assignment
     10. Leader–follower replication simulation
    """

    # ── ENGINE INITIALISATION ─────────────────────────────────────────
    print_section("GraphLink Engine — Initialising")
    engine      = GraphStorageEngine()
    traversal   = TraversalProcessor(engine)
    optimizer   = QueryOptimizer(engine)
    partitioner = PartitionManager(num_partitions=4)
    replication = ReplicationManager(num_followers=2)
    print("  All subsystems online.\n")

    # ── SCENARIO: E-COMMERCE FRAUD DETECTION GRAPH ───────────────────
    print_section("1. Seeding Graph Nodes")

    nodes_data = [
        ("u_alice",   ["User"],    {"name": "Alice",   "risk_score": 10,  "region": "US"}),
        ("u_bob",     ["User"],    {"name": "Bob",     "risk_score": 85,  "region": "EU"}),
        ("u_charlie", ["User"],    {"name": "Charlie", "risk_score": 92,  "region": "EU"}),
        ("u_diana",   ["User"],    {"name": "Diana",   "risk_score": 15,  "region": "US"}),
        ("u_eve",     ["User"],    {"name": "Eve",     "risk_score": 78,  "region": "AS"}),
        ("dev_1",     ["Device"],  {"mac": "AA:BB:CC", "type": "Mobile"}),
        ("dev_2",     ["Device"],  {"mac": "DD:EE:FF", "type": "Laptop"}),
        ("ip_100",    ["IPAddr"],  {"address": "203.0.113.10", "country": "RU"}),
        ("ip_101",    ["IPAddr"],  {"address": "198.51.100.5", "country": "US"}),
        ("txn_500",   ["Txn"],     {"amount": 4999,   "currency": "USD", "status": "flagged"}),
        ("txn_501",   ["Txn"],     {"amount": 12000,  "currency": "EUR", "status": "flagged"}),
    ]

    for node_id, labels, props in nodes_data:
        created = engine.create_node(node_id, labels, props)
        status  = "✓" if created else "✗ (duplicate)"
        print(f"  [{status}] Node '{node_id}' ({', '.join(labels)})")
        # Log to replication manager
        replication.write_to_leader({"op": "CREATE_NODE", "id": node_id})
        # Assign to partition shard
        shard = partitioner.assign_partition(node_id)
        print(f"       → Assigned to Shard #{shard}")

    # ── EDGES / RELATIONSHIPS ─────────────────────────────────────────
    print_section("2. Creating Relationships (Edges)")

    edges_data = [
        ("u_alice",   "dev_1",     "USED_DEVICE",     {"weight": 1.0}),
        ("u_bob",     "dev_1",     "USED_DEVICE",     {"weight": 1.0}),
        ("u_bob",     "ip_100",    "CONNECTED_FROM",  {"weight": 2.5}),
        ("u_charlie", "ip_100",    "CONNECTED_FROM",  {"weight": 2.5}),
        ("u_alice",   "u_diana",   "TRANSFERRED_TO",  {"weight": 3.0, "amount": 500}),
        ("u_bob",     "u_charlie", "TRANSFERRED_TO",  {"weight": 1.5, "amount": 4999}),
        ("u_charlie", "txn_500",   "INITIATED",       {"weight": 1.0}),
        ("u_charlie", "u_bob",     "COLLUDED_WITH",   {"weight": 0.5}),  # creates ring
        ("u_eve",     "dev_2",     "USED_DEVICE",     {"weight": 1.0}),
        ("u_eve",     "txn_501",   "INITIATED",       {"weight": 1.0}),
        ("u_alice",   "ip_101",    "CONNECTED_FROM",  {"weight": 1.0}),
        ("dev_1",     "ip_100",    "ASSOCIATED_IP",   {"weight": 1.5}),
    ]

    for src, tgt, rel, props in edges_data:
        ok = engine.create_edge(src, tgt, rel, props)
        print(f"  [{'✓' if ok else '✗'}] ({src}) --[{rel}]--> ({tgt})")
        replication.write_to_leader({"op": "CREATE_EDGE", "src": src, "tgt": tgt})

    print(f"\n  Graph Stats: {engine.stats()}")

    # ── SECONDARY INDEX LOOKUP ────────────────────────────────────────
    print_section("3. Secondary Index Lookups (O(1))")

    optimizer.optimize("property_lookup", {"prop": "risk_score"})
    high_risk = engine.find_nodes_by_property("risk_score", 85)
    print(f"  Nodes with risk_score=85  : {high_risk}")

    optimizer.optimize("label_scan", {"label": "Device"})
    devices = engine.find_nodes_by_label("Device")
    print(f"  All nodes with label=Device: {devices}")

    flagged_txns = engine.find_nodes_by_property("status", "flagged")
    print(f"  Flagged transactions       : {flagged_txns}")

    # ── DIJKSTRA SHORTEST PATH ────────────────────────────────────────
    print_section("4. Dijkstra Shortest Path — Alice → Charlie")

    optimizer.optimize("shortest_path", {})
    result = traversal.shortest_path_dijkstra("u_alice", "u_charlie",
                                              weight_property="weight")
    if result:
        cost, path = result
        print(f"  Path  : {' → '.join(path)}")
        print(f"  Cost  : {cost:.2f} (sum of edge weights)")
    else:
        print("  [INFO] No path found.")

    # ── BFS NEIGHBOURHOOD ─────────────────────────────────────────────
    print_section("5. BFS Neighbourhood — Alice (depth=2)")

    optimizer.optimize("neighborhood", {"depth": 2})
    bfs_result = traversal.bfs_traversal("u_alice", max_depth=2)
    for depth, nodes in bfs_result.items():
        print(f"  Depth {depth}: {nodes}")

    # ── DFS FULL REACHABILITY ─────────────────────────────────────────
    print_section("6. DFS Full Reachability from 'u_bob'")

    dfs_result = traversal.dfs_traversal("u_bob", max_depth=4)
    print(f"  Reachable nodes: {dfs_result}")

    # ── K-HOP FRIENDS (Social Graph) ─────────────────────────────────
    print_section("7. K-Hop Friend Discovery — Alice (2 hops)")

    friends = traversal.multi_hop_friends("u_alice", hops=2)
    for node, dist in friends.items():
        label = engine.get_node(node)
        print(f"  {node:12s}  (hop distance = {dist})  "
              f"labels = {label.labels if label else 'N/A'}")

    # ── FRAUD RING DETECTION ──────────────────────────────────────────
    print_section("8. Fraud Ring Detection — Starting at 'u_bob'")

    optimizer.optimize("fraud_detection", {"max_depth": 6})
    ring = traversal.detect_fraud_ring("u_bob", max_depth=6)
    if ring:
        print(f"  ⚠  FRAUD RING DETECTED: {' → '.join(ring)}")
    else:
        print("  No fraud ring detected from 'u_bob'.")

    # ── PARTITION STATS ───────────────────────────────────────────────
    print_section("9. Distributed Partition Assignment Summary")

    stats = partitioner.partition_stats()
    for shard_id, count in sorted(stats.items()):
        bar = "█" * count
        print(f"  Shard #{shard_id}  {bar}  ({count} nodes)")

    # ── REPLICATION ───────────────────────────────────────────────────
    print_section("10. Leader–Follower Replication")

    replication.replicate_to_followers()
    print(f"  Write-Ahead Log entries : {len(replication.leader_log)}")
    print(f"  All followers in sync   : {replication.is_consistent()}")
    print(f"  Simulated lag           : {replication.repl_lag_ms:.2f} ms")

    print_section("GraphLink Demo Complete ✓")


# ===========================================================================
# ENTRYPOINT
# ===========================================================================

if __name__ == "__main__":
    run_demo()
