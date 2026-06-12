# GraphLink — Distributed Graph Database System
## Project Documentation

**Subject:** System Design — Final Examination  
**Topic:** Case Study: Designing a Graph Database System  
**Student:** Kunal Rathee  
**Date:** June 2026  

---

# Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Proposed Solution](#2-proposed-solution)
3. [Requirements Analysis (Q1)](#3-requirements-analysis-q1)
4. [System Architecture Design (Q2)](#4-system-architecture-design-q2)
5. [Graph Query and Traversal Workflow (Q3)](#5-graph-query-and-traversal-workflow-q3)
6. [Database Design (Q4)](#6-database-design-q4)
7. [Algorithm and Implementation (Q5)](#7-algorithm-and-implementation-q5)
8. [Scalability and Fault Tolerance (Q6)](#8-scalability-and-fault-tolerance-q6)
9. [Technology Stack](#9-technology-stack)
10. [Module Description](#10-module-description)
11. [Implementation Screenshots](#11-implementation-screenshots)
12. [Future Scope](#12-future-scope)

---

# 1. Problem Statement

## Context

GraphLink is a distributed graph database platform similar to systems used by **Neo4j** and **Amazon Neptune**, designed to manage highly connected data efficiently for enterprise-scale applications.

Modern data increasingly exists in the form of relationships — social connections, financial transactions, supply chain dependencies, and knowledge associations. Traditional relational databases model this data in rigid, tabular schemas requiring expensive multi-table JOIN operations that grow prohibitively slow as graph size increases. Graph databases store and query relationships as first-class citizens.

## The Core Challenge

GraphLink must support millions of nodes and edges being created, updated, and queried in **real time** by distributed enterprise applications. The system faces the following specific challenges:

| Challenge                      | Description                                                                      |
|--------------------------------|----------------------------------------------------------------------------------|
| **Relationship Traversal**     | Efficient multi-hop traversal across billions of connected entities              |
| **Distributed Storage**        | Partitioning graph structure across multiple servers without losing edge locality |
| **Consistency**                | Maintaining relationship integrity during concurrent writes                       |
| **Low-Latency Queries**        | Sub-millisecond responses for complex pattern matching queries                   |
| **Horizontal Scalability**     | Scaling graph operations without sacrificing traversal performance                |
| **Fault Tolerance**            | Surviving node outages, partition failures, and replication lags                 |

## Real-World Analogies

| Platform           | Use Case                                      |
|--------------------|-----------------------------------------------|
| **Neo4j**          | Social graph, fraud ring detection            |
| **Amazon Neptune** | Knowledge graphs, recommendation systems       |
| **JanusGraph**     | Large-scale distributed graph storage          |
| **TigerGraph**     | Real-time deep-link analytics                  |

---

# 2. Proposed Solution

## Solution Philosophy

GraphLink is designed around three fundamental principles:

1. **Data Locality** — Store nodes and their adjacent edges together to minimise disk seeks and network hops during traversal
2. **Index-Selective Query Execution** — Use specialised graph indices (label index, property index) to avoid full graph scans
3. **Partition-Aware Distribution** — Use consistent hashing to distribute graph partitions while preserving traversal locality

## High-Level Solution Components

| Component                 | Solution Approach                                              |
|---------------------------|----------------------------------------------------------------|
| Storage Model             | Index-Free Adjacency (IFA) — direct pointer chaining          |
| Traversal Engine          | BFS, DFS, Dijkstra with IFA-native neighbour iteration        |
| Indexing                  | Property hash index + Label set index                         |
| Query Optimization        | Cost-based rule selection; index-first execution plans        |
| Distribution              | Vertex-cut consistent hashing across N shards                 |
| Replication               | Leader–Follower with Write-Ahead Logging (WAL)                |
| Fault Tolerance           | Automatic failover, heartbeat monitoring, WAL replay          |

---

# 3. Requirements Analysis (Q1)

## 3.1 Functional Requirements

Functional requirements define **what** the system must do — the capabilities it must provide to users and applications.

### FR-01: Graph Data Management

- The system must allow creation, read, update, and deletion (CRUD) of **nodes** (vertices) with labels and property maps
- The system must allow creation, read, update, and deletion of **edges** (relationships) with a relationship type and property map
- Every edge must reference two existing node IDs — referential integrity must be enforced

### FR-02: Graph Query Execution

- The system must support **shortest path queries** between any two nodes
- The system must support **neighbourhood expansion** queries to a configurable depth
- The system must support **property-value lookups** to retrieve nodes by attribute
- The system must support **label-based filtering** to retrieve all nodes of a specific entity type
- The system must support **pattern matching** queries (e.g., find all nodes connected by a specific relationship type)

### FR-03: Graph Traversal

- The system must implement **Breadth-First Search (BFS)** for level-order exploration
- The system must implement **Depth-First Search (DFS)** for deep path traversal
- The system must implement **Dijkstra's algorithm** for weighted shortest path computation
- The system must support **cycle detection** for fraud ring identification

### FR-04: Index Support

- The system must maintain a **secondary property index** for O(1) property-value lookups
- The system must maintain a **label index** for O(1) entity-type-based retrieval
- The system must provide a **traversal index** using Index-Free Adjacency pointers

### FR-05: Distributed Operations

- The system must partition graph data across multiple server nodes using consistent hashing
- The system must replicate data from a leader node to follower nodes via Write-Ahead Logging
- The system must support read scaling via follower nodes for eventually consistent reads

### FR-06: Monitoring and Observability

- The system must expose graph statistics (node count, edge count, partition distribution)
- The system must provide query execution plans through the query optimizer
- The system must log replication operations and lag metrics

---

## 3.2 Non-Functional Requirements

Non-functional requirements define **how well** the system performs its functions.

### NFR-01: Performance

| Metric                        | Target                                  |
|-------------------------------|----------------------------------------- |
| Node/Edge creation latency    | < 5 ms (single shard)                   |
| Property lookup latency       | < 1 ms (secondary index, O(1))          |
| Shortest path (1M nodes)      | < 100 ms (Dijkstra with IFA)            |
| Read throughput               | > 100,000 queries/second (read replicas)|
| Write throughput              | > 10,000 writes/second (sharded writes) |

### NFR-02: Scalability

- The system must scale **horizontally** by adding new shard nodes without downtime
- Graph partitions must be **rebalanced** using consistent hashing with minimal data movement (< 1/N nodes moved when adding the Nth shard)
- The system must support **billions of nodes and trillions of edges** through distributed partitioning

### NFR-03: Availability

- The system must achieve **99.99% uptime** (< 52 minutes downtime/year)
- A quorum of (N/2 + 1) replicas must be available to serve write operations
- Read operations must remain available even during a leader failover (served by followers)

### NFR-04: Consistency

- Write operations are **strongly consistent** on the leader
- Read operations on followers offer **eventual consistency** with bounded lag (< 50 ms under normal load)
- The system must support **configurable consistency levels**: STRONG, EVENTUAL, BOUNDED_STALENESS

### NFR-05: Fault Tolerance

- The system must survive the failure of any single shard or replica node within 30 seconds of automatic failover
- No data should be lost for committed write operations (durable WAL)
- The system must handle **network partitions** using the CAP theorem trade-off: prioritise Availability + Partition Tolerance (AP) for read-heavy workloads

### NFR-06: Maintainability

- All modules must be independently deployable and testable
- The system must provide comprehensive logging for debugging and auditing
- Query execution plans must be human-readable for DBA inspection

---

## 3.3 Why These Three Properties Are Critical

### Relationship Traversal Efficiency

In a graph database, traversal is the core operation. Unlike relational databases where JOIN costs grow as O(N × M) with table sizes, graph databases with **Index-Free Adjacency** keep traversal cost at O(degree) — constant with respect to overall graph size. A social network with 1 billion users should return a user's friends equally fast regardless of total graph size. This is called the **graph locality principle**.

### Scalability

Enterprise applications generate graph data continuously. A fraud detection system may add 10,000 new edges per second as transactions occur. The system must scale **without downtime**, allowing new partitions to be added using consistent hashing. Without horizontal scalability, the system becomes the bottleneck for business operations.

### Consistency

In a graph database, relationships between entities must remain coherent. If an edge points to a node that has been deleted, queries will produce incorrect results (dangling pointer problem). Maintaining **referential integrity** across distributed partitions — especially under concurrent writes — requires careful coordination through WAL replication and atomic write operations.

---

# 4. System Architecture Design (Q2)

## 4.1 High-Level Architecture Overview

The GraphLink system is organised into six distinct logical layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                     │
│   Enterprise Apps │ Fraud Systems │ Recommendation Engines │ Analytics   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ Graph Query API (REST / Cypher / gRPC)
┌──────────────────────────────────▼──────────────────────────────────────┐
│                       QUERY PROCESSING LAYER                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌───────────────────┐ │
│  │  Query Parser    │    │  Query Optimizer  │    │  Execution Engine │ │
│  │  (Cypher/API)    │───►│  (Cost-Based)     │───►│  (Plan Executor)  │ │
│  └──────────────────┘    └──────────────────┘    └───────────────────┘ │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                       TRAVERSAL ENGINE LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │ BFS Engine  │  │ DFS Engine  │  │ Dijkstra Finder│  │  Cycle     │ │
│  │ (Neighbour) │  │ (Deep Path) │  │ (Shortest Path)│  │  Detector  │ │
│  └─────────────┘  └─────────────┘  └────────────────┘  └────────────┘ │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                         STORAGE ENGINE LAYER                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Index-Free Adjacency Store                                       │  │
│  │  node_id → { labels, properties, [edge_ptr_1, edge_ptr_2, ...] } │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────┐  ┌───────────────────────────────────────┐│
│  │  Secondary Property Index│  │  Label Index                          ││
│  │  prop_name → {val → IDs} │  │  label → set(node_ids)               ││
│  └─────────────────────────┘  └───────────────────────────────────────┘│
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                     DISTRIBUTION & REPLICATION LAYER                     │
│  ┌───────────────────────────────────────────────────────┐             │
│  │           Partition Manager (Consistent Hash)          │             │
│  │   Shard 0  │  Shard 1  │  Shard 2  │  Shard 3         │             │
│  └───────────────────────────────────────────────────────┘             │
│  ┌───────────────────────────────────────────────────────┐             │
│  │           Replication Manager (Leader–Follower)        │             │
│  │   Leader → WAL → [Follower 1, Follower 2, ...]        │             │
│  └───────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

## 4.2 Component Interactions

| Source Component      | Target Component        | Interaction                                           |
|-----------------------|-------------------------|-------------------------------------------------------|
| Client Application    | Query Parser            | Sends Cypher/API query string                         |
| Query Parser          | Query Optimizer         | Passes parsed AST for plan selection                  |
| Query Optimizer       | Execution Engine        | Provides optimal execution plan                       |
| Execution Engine      | Traversal Engine        | Dispatches to BFS/DFS/Dijkstra based on query type    |
| Traversal Engine      | Storage Engine          | Calls `get_neighbors()` via IFA pointer dereferencing |
| Execution Engine      | Index Manager           | Calls secondary/label index for predicate pushdowns   |
| Storage Engine        | Partition Manager       | Routes reads/writes to correct shard                 |
| Storage Engine        | Replication Manager     | Logs writes to WAL; replicates to followers           |

## 4.3 Component Descriptions

### Query Parser
Interprets incoming query strings (Cypher-like syntax or REST API calls) and produces an Abstract Syntax Tree (AST). Validates query syntax and extracts operation type, target nodes, predicates, and traversal constraints.

### Query Optimizer (Cost-Based)
Analyses the AST and selects the most efficient execution plan using rules:
- If query has an indexed property predicate → use Secondary Index first
- If query involves traversal → select algorithm based on edge weights and depth
- If no index exists → fall back to full graph scan (avoided in production)

### Traversal Processor
Implements the core traversal algorithms (BFS, DFS, Dijkstra) directly on top of the adjacency list. By using Index-Free Adjacency pointers, each hop in traversal is O(1) — just dereferencing a pointer to the neighbour's edge list. No global index lookup is required per hop.

### Graph Storage Engine
The central component. Maintains the IFA store (nodes with embedded adjacency lists), the secondary property index (hash map), and the label index (set map). Acts as the primary data authority for a given shard.

### Partition Manager
Uses MD5-based consistent hashing to assign node IDs to shards. When nodes are added or removed from the cluster, only K/N keys need to be remapped (where K = total keys, N = number of shards).

### Replication Manager
Implements a Write-Ahead Log. All mutations (node/edge creates, updates, deletes) are first written to the leader's WAL, then asynchronously propagated to follower replicas. In the event of leader failure, a follower with the most up-to-date WAL is promoted via leader election (Raft protocol in production).

---

# 5. Graph Query and Traversal Workflow (Q3)

## 5.1 How Graph Data Is Stored

GraphLink uses the **Index-Free Adjacency (IFA)** storage model. In this model, each node is a self-contained record that includes:

```
Node Record {
    node_id       : "u_alice"
    labels        : {"User"}
    properties    : {"name": "Alice", "risk_score": 10}
    adjacency_list: [
        ("u_diana",   "TRANSFERRED_TO", {"weight": 3.0, "amount": 500}),
        ("ip_101",    "CONNECTED_FROM", {"weight": 1.0}),
        ("dev_1",     "USED_DEVICE",    {"weight": 1.0})
    ]
}
```

This is in contrast to relational databases, which store relationships in a separate JOIN table that must be scanned globally. With IFA, traversal from a node directly follows the embedded pointers — analogous to following linked list pointers in memory.

## 5.2 How Nodes Are Indexed

GraphLink maintains **three levels of indexing**:

### Level 1 — IFA (Traversal Index)

Each node's adjacency list IS the traversal index. Accessing all neighbours of any node requires a single memory dereference — no global scan necessary.

```
adjacency_list["u_alice"] → [(u_diana, TRANSFERRED_TO, ...), (ip_101, ...), (dev_1, ...)]
```

### Level 2 — Secondary Property Index

A hash-map based index for fast property-value lookups:

```
secondary_index["risk_score"][85] → {"u_bob"}
secondary_index["name"]["Alice"]  → {"u_alice"}
secondary_index["status"]["flagged"] → {"txn_500", "txn_501"}
```

Time Complexity: O(1) average case for both read and write.

### Level 3 — Label Index

A set-based index for entity-type filtering:

```
label_index["User"]   → {"u_alice", "u_bob", "u_charlie", "u_diana", "u_eve"}
label_index["Device"] → {"dev_1", "dev_2"}
label_index["Txn"]    → {"txn_500", "txn_501"}
```

## 5.3 How Queries Are Executed

### Step-by-Step Query Execution Flow

```
1. CLIENT sends query: "Find shortest path from u_alice to u_charlie"
         │
2. QUERY PARSER extracts: operation=shortest_path, src=u_alice, tgt=u_charlie
         │
3. QUERY OPTIMIZER selects plan:
   → "Dijkstra with IFA traversal + min-heap priority queue"
         │
4. EXECUTION ENGINE initialises priority queue:
   pq = [(0.0, "u_alice", ["u_alice"])]
         │
5. TRAVERSAL PROCESSOR pops (0.0, u_alice, [u_alice]):
   → get_neighbors("u_alice") = [(dev_1, USED_DEVICE, {w:1}),
                                  (ip_101, CONNECTED_FROM, {w:1}),
                                  (u_diana, TRANSFERRED_TO, {w:3})]
   → Push (1.0, dev_1, [u_alice, dev_1])
   → Push (1.0, ip_101, [u_alice, ip_101])
   → Push (3.0, u_diana, [u_alice, u_diana])
         │
6. TRAVERSAL continues popping minimum-cost nodes until u_charlie is reached:
   → Final path: u_alice → dev_1 → ip_100 → u_charlie (cost = 5.0)
         │
7. RESULT returned to client
```

## 5.4 Distributed Traversal across Partitions

In a distributed deployment, nodes may reside on different shards. The Partition Manager intercepts each `get_neighbors()` call:

1. For each neighbour in the adjacency list, determine the shard it belongs to
2. If the neighbour is **local** (same shard), resolve directly from local memory
3. If the neighbour is **remote** (different shard), issue a **ghost node lookup** — fetch the node's adjacency list from the responsible shard via RPC
4. Cache the remote node's adjacency list locally for the duration of the query (traversal cache)

This keeps cross-shard hops to a minimum by co-locating heavily connected subgraphs on the same shard through the vertex-cut partitioning strategy.

---

# 6. Database Design (Q4)

## 6.1 Graph Data Model

GraphLink uses a **Labeled Property Graph (LPG)** model — the same model used by Neo4j. In this model:

- **Nodes** represent entities (User, Device, Transaction, IPAddress)
- **Edges** represent directed relationships between entities
- Both nodes and edges carry an arbitrary **property map** (key-value attributes)
- Nodes can have one or more **labels** (entity types)

## 6.2 Node Schema Design

### User Node
```
Node {
  node_id      : STRING   (Primary Key, e.g., "u_alice")
  labels       : SET      ["User"]
  name         : STRING
  risk_score   : INTEGER  (0–100; >75 = high risk)
  region       : STRING   (ISO 3166)
  created_at   : TIMESTAMP
}
```

### Device Node
```
Node {
  node_id      : STRING   (e.g., "dev_1")
  labels       : SET      ["Device"]
  mac_address  : STRING   (XX:XX:XX:XX:XX:XX)
  device_type  : STRING   (Mobile | Laptop | Server)
  created_at   : TIMESTAMP
}
```

### Transaction Node
```
Node {
  node_id      : STRING   (e.g., "txn_500")
  labels       : SET      ["Transaction"]
  amount       : FLOAT
  currency     : STRING   (ISO 4217)
  status       : STRING   (pending | completed | flagged | reversed)
  created_at   : TIMESTAMP
}
```

### IP Address Node
```
Node {
  node_id      : STRING   (e.g., "ip_100")
  labels       : SET      ["IPAddress"]
  ip_address   : STRING
  country      : STRING   (ISO 3166)
  is_proxy     : BOOLEAN
  created_at   : TIMESTAMP
}
```

## 6.3 Edge Schema Design (Relationship Types)

| Relationship Type   | Source Label | Target Label | Key Properties                      |
|---------------------|--------------|--------------|-------------------------------------|
| `TRANSFERRED_TO`    | User         | User         | amount (FLOAT), currency, timestamp |
| `USED_DEVICE`       | User         | Device       | weight (FLOAT), last_seen           |
| `CONNECTED_FROM`    | User/Device  | IPAddress    | weight (FLOAT), session_count       |
| `INITIATED`         | User         | Transaction  | weight (FLOAT), channel             |
| `COLLUDED_WITH`     | User         | User         | confidence (FLOAT), evidence_type   |
| `ASSOCIATED_IP`     | Device       | IPAddress    | weight (FLOAT), association_strength|

## 6.4 Index Design

| Index Name              | Type              | Key                        | Time Complexity |
|-------------------------|-------------------|----------------------------|-----------------|
| IFA Traversal Index     | Embedded List     | node_id → [edge_records]   | O(degree)       |
| Secondary Property Index| Hash Map          | prop_name → val → node_ids | O(1) avg        |
| Label Index             | Hash Set Map      | label → set(node_ids)      | O(1) avg        |
| Edge Type Index         | Hash Map          | rel_type → set(edge_ids)   | O(1) avg        |

## 6.5 Traversal Index (IFA vs B-Tree Comparison)

| Criteria              | Index-Free Adjacency (IFA)      | B-Tree Relationship Index       |
|-----------------------|---------------------------------|---------------------------------|
| Hop Cost              | O(1) per hop                    | O(log N) per hop                |
| 10-hop traversal cost | O(10 × avg_degree)              | O(10 × log N) — grows with N   |
| Storage overhead      | Embedded in node record         | Separate index structure        |
| Insert cost           | O(1) amortised                  | O(log N)                        |
| Used by               | Neo4j, GraphLink                | Traditional RDBMS               |

## 6.6 Metadata Store

GraphLink maintains a separate **metadata store** (equivalent to a system catalog) containing:

```
Metadata {
  schema_version     : INTEGER
  total_nodes        : INTEGER
  total_edges        : INTEGER
  partition_map      : {node_id → shard_id}
  replication_lag_ms : FLOAT
  leader_id          : STRING
  follower_ids       : LIST[STRING]
  index_registry     : {index_name → {type, key_space, cardinality}}
}
```

---

# 7. Algorithm and Implementation (Q5)

## 7.1 Overview of Implemented Algorithms

The Python prototype implements five core algorithms:

| Algorithm                 | Purpose                           | Complexity      |
|---------------------------|-----------------------------------|-----------------|
| BFS (Breadth-First Search) | Level-order graph exploration    | O(V + E)        |
| DFS (Depth-First Search)   | Deep path reachability           | O(V + E)        |
| Dijkstra's Algorithm       | Weighted shortest path           | O((V+E) log V)  |
| K-Hop Expansion            | Social network neighbour finding | O(V + E)        |
| Cycle-Detecting DFS        | Fraud ring identification        | O(V + E)        |

## 7.2 Dijkstra's Shortest Path — Detailed Explanation

Dijkstra's algorithm finds the minimum-cost path between two nodes in a graph with non-negative edge weights. It uses a **min-heap priority queue** to always expand the lowest-cost frontier node next.

### Algorithm Pseudocode

```
DIJKSTRA(graph, start, end, weight_prop):
  pq ← priority_queue containing (cost=0, node=start, path=[start])
  visited ← empty set

  WHILE pq is not empty:
    (cost, current, path) ← pq.pop_minimum()

    IF current == end:
      RETURN (cost, path)          ← FOUND shortest path

    IF current IN visited:
      CONTINUE                     ← already finalized; skip

    visited.add(current)

    FOR each (neighbour, rel_type, props) IN current.neighbours:
      IF neighbour NOT IN visited:
        edge_cost ← props.get(weight_prop, 1.0)
        pq.push((cost + edge_cost, neighbour, path + [neighbour]))

  RETURN None                      ← destination unreachable
```

### Python Implementation

```python
def shortest_path_dijkstra(
        self, start_id: str, end_id: str,
        weight_property: str = "weight"
) -> Optional[Tuple[float, List[str]]]:
    
    if start_id not in self.engine.nodes or end_id not in self.engine.nodes:
        return None

    # Min-heap: (cumulative_cost, node_id, path_list)
    pq: List[Tuple[float, str, List[str]]] = [(0.0, start_id, [start_id])]
    visited: Set[str] = set()

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

    return None
```

### Worked Example

**Graph:**
```
u_alice ──1.0──► dev_1 ──1.5──► ip_100 ──2.5──► u_charlie    (total: 5.0)
u_alice ──3.0──► u_diana                                       (dead end)
u_alice ──7.5──► u_charlie                                     (direct: 7.5)
```

**Priority Queue Trace:**

| Step | Queue Top          | Visited      | Action                          |
|------|--------------------|--------------|----------------------------------|
| 1    | (0.0, u_alice)     | {}           | Pop alice, push dev_1 (1.0), ip_101 (1.0), u_diana (3.0) |
| 2    | (1.0, dev_1)       | {alice}      | Pop dev_1, push ip_100 (2.5)    |
| 3    | (1.0, ip_101)      | {alice,dev_1}| Pop ip_101, no new neighbours    |
| 4    | (2.5, ip_100)      | {...}        | Pop ip_100, push u_charlie (5.0) |
| 5    | (3.0, u_diana)     | {...}        | Pop u_diana, no exit             |
| 6    | (5.0, u_charlie)   | {...}        | **Target reached → return 5.0**  |

**Result:** Path = `u_alice → dev_1 → ip_100 → u_charlie`, Cost = **5.0**

Note: The direct path (alice → u_charlie at cost 7.5) is correctly avoided.

## 7.3 BFS Traversal — Fraud Graph Neighbourhood

```python
def bfs_traversal(self, start_id: str, max_depth: int = 3):
    visited = {start_id}
    queue   = deque([(start_id, 0)])
    result  = defaultdict(list)
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
```

**Use Case:** In a social graph, BFS from a user node returns all contacts at depth 1 (direct friends), depth 2 (friends of friends), and depth 3 (extended network) — the foundation of LinkedIn's degree-of-connection feature.

## 7.4 Fraud Ring Detection — Cycle Detector

```python
def detect_fraud_ring(self, start_id: str, max_depth: int = 6):
    def dfs_cycle(node_id, path, depth):
        if depth > max_depth:
            return None
        for target_id, _, _ in self.engine.get_neighbors(node_id):
            if target_id == start_id and len(path) > 1:
                return path + [start_id]   # cycle found
            if target_id not in path:
                result = dfs_cycle(target_id, path + [target_id], depth + 1)
                if result:
                    return result
        return None

    return dfs_cycle(start_id, [start_id], 0)
```

**Use Case:** Financial fraud often manifests as circular money movement — Account A → Account B → Account C → Account A. This cyclic DFS detects exactly such patterns, which are used by banks to flag coordinated fraud rings.

---

# 8. Scalability and Fault Tolerance (Q6)

## 8.1 Achieving Billion-Scale Graph Storage

### Strategy 1: Vertical Partitioning (Sharding)

GraphLink uses **vertex-cut consistent hashing** to distribute nodes across N shards. When a node is created:

```python
shard_id = int(MD5(node_id), 16) % num_shards
```

**Advantages of consistent hashing:**
- Adding a new shard only remaps K/N existing keys (not all K keys)
- Node redistributions are predictable and bounded
- No central lookup table required — any client can calculate the shard directly

| Query Type             | Routing Logic                                        |
|------------------------|------------------------------------------------------|
| Node creation          | Hash node_id → assign to shard                       |
| Property lookup        | Secondary index maintained separately per shard      |
| Single-node read       | Hash node_id → route to owning shard                 |
| Cross-shard traversal  | Ghost nodes + RPC calls to remote shards             |

### Strategy 2: Read Scaling via Follower Replicas

Write operations go exclusively to the leader. Read operations (traversal, lookups) can be distributed across follower replicas:

```
Write Load  → Leader node (strong consistency)
Read Load   → Round-robin across Follower 1, Follower 2, ... Follower N
```

For a system with 1 leader and 3 followers, this provides **4× read throughput** scalability.

### Strategy 3: Traversal Caching

Frequently accessed subgraphs are cached in memory (LRU cache) on each traversal node. Cache hits avoid repeated IFA pointer resolutions for hot nodes (e.g., widely-connected celebrity nodes in social graphs).

### Strategy 4: Graph Analytics Offloading

Heavy batch analytics (PageRank, community detection, centrality) are offloaded to a separate **Analytics Pipeline** using Apache Spark GraphX or Pregel-based processing, keeping the OLTP graph engine responsive for real-time queries.

## 8.2 Fault Tolerance Mechanisms

### Mechanism 1: Write-Ahead Logging (WAL)

Every mutation is first written durably to the WAL before being applied to the in-memory store:

```
WRITE FLOW:
  1. Client sends write operation
  2. WAL entry appended to leader's durable log
  3. ACK sent to client (write is now durable)
  4. Operation applied to leader's in-memory store
  5. WAL entry asynchronously replicated to followers
```

If the leader crashes after step 3, the WAL can be replayed on recovery. No committed data is lost.

### Mechanism 2: Leader Election (Raft Protocol)

In production, GraphLink uses the **Raft consensus algorithm** for leader election:

1. Followers detect leader failure via heartbeat timeout (typically 150–300 ms)
2. A follower initiates an election, requesting votes from other nodes
3. The candidate with the most up-to-date WAL log wins the election
4. The new leader begins serving writes; followers update their remote pointer

**Failover time:** < 500 ms under normal network conditions

### Mechanism 3: Partition Outage Handling

When a graph partition (shard) becomes unavailable:

1. The Partition Manager marks the shard as **UNAVAILABLE**
2. Incoming queries that would route to the failed shard are held in a **retry queue**
3. If a replica of the shard is available, reads are re-routed to the replica
4. Write operations targeting the failed shard are buffered in the client-side WAL
5. When the shard recovers, buffered writes are replayed

### Mechanism 4: Traversal Timeout and Circuit Breaker

Long-running traversal queries on deeply connected graphs can cause resource exhaustion. GraphLink implements:

- **Max Depth Limits** — configurable per query (default: 6 hops for fraud detection, 3 for social graph)
- **Traversal Timeout** — queries exceeding the time limit are terminated and a partial result is returned
- **Circuit Breaker Pattern** — if a downstream shard returns errors for >50% of requests in a 10-second window, circuit opens and immediately returns error to clients, preventing cascading failures

### Mechanism 5: Replication Lag Monitoring

GraphLink continuously monitors follower lag. If a follower falls behind by more than the configured `max_lag_ms` threshold:

1. The follower is marked as **DEGRADED**
2. Client read requests are not routed to the degraded follower
3. The follower begins a **snapshot catch-up** from the leader's current state
4. Once lag drops below threshold, the follower is reactivated

## 8.3 CAP Theorem Trade-offs

GraphLink is an **AP system** by design:

| Property         | Choice    | Justification                                              |
|------------------|-----------|------------------------------------------------------------|
| Consistency      | Eventual  | Followers may serve slightly stale reads during lag        |
| Availability     | High      | System remains available even during network partitions     |
| Partition Tolerance | Required | Distributed system must handle network splits             |

For critical write-heavy workloads (financial fraud prevention), GraphLink provides a **STRONG** consistency mode that forces all reads through the leader — trading availability for consistency.

## 8.4 Scalability Benchmark Targets

| Scale                  | Target Latency | Target Throughput      |
|------------------------|---------------|------------------------|
| 1M nodes               | < 10 ms (BFS, depth=3) | 50,000 queries/s   |
| 100M nodes, 4 shards   | < 50 ms (Dijkstra) | 200,000 reads/s    |
| 1B nodes, 16 shards    | < 100 ms (6-hop DFS) | 500,000 reads/s   |
| 10B nodes, 64 shards   | < 200 ms (cross-shard) | 1M reads/s       |

---

# 9. Technology Stack

| Layer                   | Technology Choice          | Justification                                         |
|-------------------------|----------------------------|-------------------------------------------------------|
| **Core Language**       | Python 3.9+                | Readable prototype; production would use Java/C++     |
| **Graph Data Model**    | Labeled Property Graph     | Flexible, supports Neo4j Cypher queries               |
| **Traversal Algorithms**| Custom (heapq, deque)      | Zero-dependency; demonstrates algorithmic knowledge   |
| **Primary Storage**     | Index-Free Adjacency       | O(1) per-hop traversal; Neo4j-native model            |
| **Secondary Index**     | Python dict (hash map)     | O(1) average lookup; maps to Redis in production      |
| **Partitioning**        | MD5 Consistent Hashing     | Uniform distribution; minimal redistribution overhead |
| **Replication**         | WAL Leader–Follower model  | Durable writes; maps to Raft/Paxos in production      |
| **Production DB**       | Apache Cassandra (backend) | Wide-column store for raw graph data persistence      |
| **Analytics**           | Apache Spark GraphX        | Distributed graph analytics for batch workloads       |
| **API Layer**           | FastAPI + gRPC             | High-performance query serving                        |
| **Monitoring**          | Prometheus + Grafana       | Real-time latency, throughput, and lag dashboards     |
| **Container**           | Docker + Kubernetes        | Horizontal scaling and orchestration                  |

---

# 10. Module Description

## graphlink_engine.py — Module Breakdown

### Class: `Node`
- Represents a graph vertex
- Attributes: `node_id`, `labels` (set), `properties` (dict), `created_at`
- Used by: `GraphStorageEngine` for node creation and storage

### Class: `Edge`
- Represents a directed relationship between two `Node` instances
- Attributes: `src_id`, `target_id`, `rel_type`, `properties`, `edge_id` (MD5 hash), `created_at`
- Used by: `GraphStorageEngine` for edge storage and replication logging

### Class: `GraphStorageEngine`
- Core IFA storage engine
- Key methods:
  - `create_node()` — Creates node, updates label and secondary indices
  - `create_edge()` — Creates directed edge with referential integrity check
  - `get_neighbors()` — O(1) IFA adjacency list dereference
  - `find_nodes_by_property()` — O(1) secondary index lookup
  - `find_nodes_by_label()` — O(1) label index lookup
  - `stats()` — Returns total node/edge/index counts

### Class: `TraversalProcessor`
- Operates on a `GraphStorageEngine` instance
- Key methods:
  - `bfs_traversal()` — BFS with configurable max depth
  - `dfs_traversal()` — Iterative DFS with max depth cap
  - `shortest_path_dijkstra()` — Weighted shortest path (Dijkstra)
  - `multi_hop_friends()` — K-hop social graph expansion
  - `detect_fraud_ring()` — Recursive cycle-detecting DFS

### Class: `QueryOptimizer`
- Prints the recommended execution plan for a given query type
- Query types: `property_lookup`, `label_scan`, `shortest_path`, `neighborhood`, `fraud_detection`

### Class: `PartitionManager`
- Simulates consistent-hash based node-to-shard assignment
- Key methods:
  - `assign_partition()` — MD5 hash → shard ID
  - `get_partition()` — Returns assigned shard for a node
  - `partition_stats()` — Returns per-shard node count distribution

### Class: `ReplicationManager`
- Simulates WAL-based leader–follower replication
- Key methods:
  - `write_to_leader()` — Appends operation to leader WAL with timestamp
  - `replicate_to_followers()` — Propagates WAL to all followers with simulated lag
  - `is_consistent()` — Checks if all followers match the leader log

---

# 11. Implementation Screenshots

## Console Output — Program Execution

The following output is produced when running `python3 graphlink_engine.py`:

```
═══════════════════════════════════════════════════════════════════
  GraphLink Engine — Initialising
═══════════════════════════════════════════════════════════════════
  All subsystems online.

═══════════════════════════════════════════════════════════════════
  1. Seeding Graph Nodes
═══════════════════════════════════════════════════════════════════
  [✓] Node 'u_alice'   (User)    → Assigned to Shard #2
  [✓] Node 'u_bob'     (User)    → Assigned to Shard #0
  [✓] Node 'u_charlie' (User)    → Assigned to Shard #1
  [✓] Node 'dev_1'     (Device)  → Assigned to Shard #3
  ...

═══════════════════════════════════════════════════════════════════
  3. Secondary Index Lookups (O(1))
═══════════════════════════════════════════════════════════════════
[QueryOptimizer] Query='property_lookup' → PLAN: Secondary Index Scan
Nodes with risk_score=85  : ['u_bob']
All nodes with label=Device: ['dev_1', 'dev_2']
Flagged transactions       : ['txn_500', 'txn_501']

═══════════════════════════════════════════════════════════════════
  4. Dijkstra Shortest Path — Alice → Charlie
═══════════════════════════════════════════════════════════════════
[QueryOptimizer] Query='shortest_path' → PLAN: Dijkstra + IFA
  Path  : u_alice → dev_1 → ip_100 → u_charlie
  Cost  : 5.00

═══════════════════════════════════════════════════════════════════
  8. Fraud Ring Detection — Starting at 'u_bob'
═══════════════════════════════════════════════════════════════════
  ⚠  FRAUD RING DETECTED: u_bob → u_charlie → u_bob

═══════════════════════════════════════════════════════════════════
  9. Distributed Partition Assignment Summary
═══════════════════════════════════════════════════════════════════
  Shard #0  ███  (3 nodes)
  Shard #1  ██   (2 nodes)
  Shard #2  ████ (4 nodes)
  Shard #3  ██   (2 nodes)

═══════════════════════════════════════════════════════════════════
  10. Leader–Follower Replication
═══════════════════════════════════════════════════════════════════
[Replication] Synced 23 log entries to 2 follower(s) (lag: 8.34 ms)
  Write-Ahead Log entries : 23
  All followers in sync   : True
  Simulated lag           : 8.34 ms

═══════════════════════════════════════════════════════════════════
  GraphLink Demo Complete ✓
═══════════════════════════════════════════════════════════════════
```

---

# 12. Future Scope

## Short-Term Enhancements (3–6 months)

| Enhancement                       | Description                                                  |
|-----------------------------------|--------------------------------------------------------------|
| **Native Cypher Language Parser** | Full lexer + parser for Neo4j-compatible Cypher query syntax |
| **Persistent Storage Backend**    | RocksDB / Apache Cassandra integration for durability        |
| **GraphQL API Layer**             | FastAPI + Strawberry GraphQL for web client access           |
| **ACID Transaction Support**      | MVCC (Multi-Version Concurrency Control) for graph mutations |
| **Bi-directional Edge Support**   | Undirected relationship model for social graph use cases     |

## Long-Term Enhancements (6–18 months)

| Enhancement                       | Description                                                  |
|-----------------------------------|--------------------------------------------------------------|
| **Raft Consensus Protocol**       | Production leader election replacing simulated WAL failover  |
| **GPU-Accelerated Analytics**     | cuGraph (NVIDIA RAPIDS) for GPU-parallel PageRank, BFS      |
| **Multi-Model Support**           | Hybrid graph-document store (graph + JSON document storage)  |
| **Automated Shard Rebalancing**   | Dynamic partition rebalancing based on shard load metrics    |
| **Graph Neural Network Integration** | GNN inference directly on stored graph topology           |
| **Zero-Copy Memory Mapping**      | Memory-mapped file storage for graphs larger than RAM        |
| **Time-Versioned Graph**          | Temporal graph model tracking relationship changes over time |

---

*© 2026 Kunal Rathee — GraphLink Distributed Graph Database System*  
*System Design Final Examination Submission*
