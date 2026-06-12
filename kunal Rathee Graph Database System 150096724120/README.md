# GraphLink — Distributed Graph Database System

> **System Design Final Examination | Topic: Graph Database System Design**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Project Overview

**GraphLink** is a distributed graph database platform prototype inspired by real-world systems like **Neo4j** and **Amazon Neptune**. It is designed to manage highly connected data efficiently for enterprise use cases such as:

| Use Case              | Description                                          |
|-----------------------|------------------------------------------------------|
| Social Networks       | Friend-of-friend queries, community detection        |
| Fraud Detection       | Fraud ring identification via cyclic path detection  |
| Recommendation Engines| K-hop neighbourhood traversal for collaborative filtering |
| Knowledge Graphs      | Entity–relationship modelling at scale               |
| Supply Chain Analysis | Multi-hop dependency and bottleneck analysis         |

This prototype demonstrates the core architectural patterns of a production-grade distributed graph database system, implemented purely in Python with **zero external dependencies**.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     CLIENT APPLICATIONS                       │
└─────────────────────────────┬────────────────────────────────┘
                              │ Graph Query (Cypher / API)
┌─────────────────────────────▼────────────────────────────────┐
│                     QUERY OPTIMIZER                           │
│     (Cost-Based Plan Selection – Index vs. Full Scan)         │
└────────┬────────────────────┬──────────────────────┬─────────┘
         │                    │                      │
┌────────▼──────┐  ┌──────────▼──────┐  ┌───────────▼───────┐
│  Traversal    │  │  Storage Engine  │  │  Index Manager     │
│  Processor    │  │  (IFA Model)     │  │  (2° Index +       │
│  BFS/DFS/     │  │  Nodes + Edges   │  │   Label Index)     │
│  Dijkstra     │  │  Adjacency Lists │  │                    │
└───────────────┘  └──────────────────┘  └───────────────────┘
         │                    │
┌────────▼────────────────────▼────────────────────────────────┐
│                  PARTITION MANAGER                             │
│        (Consistent Hash → 4 virtual shards)                   │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                  REPLICATION MANAGER                           │
│          Leader ──WAL──► Follower 1, Follower 2               │
└──────────────────────────────────────────────────────────────┘
```

---

## Features

- **Index-Free Adjacency (IFA)** — Direct pointer-based neighbour resolution; no global index scans during traversal
- **Secondary Property Index** — O(1) property-value lookups via hash maps
- **Label Index** — O(1) node retrieval by entity type
- **Dijkstra Shortest Path** — Weighted path computation with a min-heap priority queue
- **BFS Traversal** — Level-order graph exploration for neighbourhood queries
- **DFS Traversal** — Deep-path reachability analysis
- **K-Hop Friend Discovery** — Social network multi-hop expansion
- **Fraud Ring Detection** — Cycle-detecting DFS for coordinated fraud identification
- **Cost-Based Query Optimizer** — Rule-based execution plan selection
- **Consistent-Hash Partitioning** — Simulated 4-shard vertex-cut partitioning
- **Leader–Follower Replication** — Write-ahead log with async follower sync simulation

---

## File Structure

```
GraphLink_Submission/
├── graphlink_engine.py        ← Complete Python source code (all modules)
├── README.md                  ← This file
├── system_architecture.png    ← High-level architecture diagram
└── GraphLink_Documentation.md ← Full project documentation (PDF-ready)
```

---

## Dependencies

This project requires **only the Python Standard Library**. No pip installs needed.

| Module        | Usage                                    |
|---------------|------------------------------------------|
| `heapq`       | Min-heap priority queue for Dijkstra     |
| `hashlib`     | MD5 consistent hashing for partitioning  |
| `collections` | `deque` for BFS, `defaultdict` for indices |
| `typing`      | Type annotations                         |
| `random`      | Simulated replication lag                |
| `time`        | Timestamps on nodes and edges            |

**Python Version:** 3.9 or higher

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/graphlink-db.git
cd graphlink-db
```

### 2. Verify Python Version

```bash
python3 --version
# Expected: Python 3.9.x or higher
```

### 3. No Installation Required

There are no third-party dependencies. The project runs directly with the standard library.

---

## Execution Steps

### Run the Full Demo

```bash
python3 graphlink_engine.py
```

### Expected Output Sections

```
══════════════════════════════════════════════════════════════
  GraphLink Engine — Initialising
══════════════════════════════════════════════════════════════
  All subsystems online.

══════════════════════════════════════════════════════════════
  1. Seeding Graph Nodes
══════════════════════════════════════════════════════════════
  [✓] Node 'u_alice'   (User)    → Assigned to Shard #2
  ...
══════════════════════════════════════════════════════════════
  4. Dijkstra Shortest Path — Alice → Charlie
══════════════════════════════════════════════════════════════
  Path  : u_alice → dev_1 → ip_100 → u_charlie
  Cost  : 5.00

══════════════════════════════════════════════════════════════
  8. Fraud Ring Detection — Starting at 'u_bob'
══════════════════════════════════════════════════════════════
  ⚠  FRAUD RING DETECTED: u_bob → u_charlie → u_bob
...
```

---

## Module Descriptions

| Class / Module          | Responsibility                                                   |
|-------------------------|------------------------------------------------------------------|
| `Node`                  | Graph vertex data model (labels + properties)                    |
| `Edge`                  | Directed relationship model with MD5 edge ID                     |
| `GraphStorageEngine`    | Core IFA storage with adjacency lists and dual index system      |
| `TraversalProcessor`    | BFS, DFS, Dijkstra, K-hop expansion, fraud ring detection        |
| `QueryOptimizer`        | Cost-based query plan selection (rule-based simulation)          |
| `PartitionManager`      | Consistent-hash sharding across 4 virtual partitions             |
| `ReplicationManager`    | Leader–follower WAL replication with simulated network lag       |

---

## Key Design Decisions

| Decision                     | Rationale                                                            |
|------------------------------|----------------------------------------------------------------------|
| Index-Free Adjacency         | O(degree) traversal vs O(log N) in B-tree; eliminates global scans  |
| Vertex-Cut Partitioning      | Distributes high-degree nodes; minimises cross-partition edge cuts   |
| Dijkstra over Bellman-Ford   | Non-negative edge weights; O((V+E)logV) vs O(VE) for Bellman-Ford  |
| Write-Ahead Log Replication  | Durable replication with replay capability for crash recovery        |
| Secondary Index (Hash Map)   | O(1) average-case property lookups; faster than B-tree for equality  |

---

## Future Scope

- Integration with **Apache Cassandra** as a persistent backend storage layer
- Implementation of the **Raft consensus protocol** for leader election
- Native **Cypher query language** parser and executor
- **GraphQL API** layer exposed over FastAPI
- Support for **ACID transactions** using Multi-Version Concurrency Control (MVCC)
- **GPU-accelerated** graph analytics using cuGraph

---

## GitHub Repository

> **Repository:** https://github.com/kunalrathee1/Graph-Database-System.git

---

## Author

| Field         | Details                              |
|---------------|--------------------------------------|
| **Name**      | Kunal Rathee                         |
| **Subject**   | System Design                        |
| **Topic**     | GraphLink – Distributed Graph DB     |
| **Exam Type** | Final Examination                    |

---

