# 🚆 RailTwin: Self-Healing Railway Digital Twin

> A graph-powered digital twin that monitors railway health, predicts network risk, and autonomously reroutes train services during disruptions.

![Status](https://img.shields.io/badge/status-prototype-success)
![Python](https://img.shields.io/badge/backend-Python-blue)
![React](https://img.shields.io/badge/frontend-React-61DAFB)
![FastAPI](https://img.shields.io/badge/API-FastAPI-green)

---

## 📖 Overview

Railway networks are complex interconnected systems where a single disruption can propagate across multiple corridors, causing delays, congestion, and operational failures.

RailTwin models the railway network as a dynamic graph and continuously evaluates:

* Station stress
* Network health
* Infrastructure criticality
* Failure propagation
* Train routing efficiency

When a disruption occurs, the system automatically computes alternative routes and restores network functionality with minimal operator intervention.

---

## 🎯 Problem Statement

Traditional railway monitoring systems are primarily reactive.

They answer:

> "What has already failed?"

RailTwin aims to answer:

> "What is likely to fail, what will be affected, and how can we recover automatically?"

---

## ✨ Key Features

### 🚉 Railway Digital Twin

Real-time virtual representation of:

* Stations
* Tracks
* Train services
* Network state

---

### 📊 Stress Monitoring

Each station continuously evaluates utilization:

Stress = Load / Capacity

High stress stations are highlighted within the network.

---

### 🌐 Graph-Based Railway Model

The railway system is represented as:

* Nodes → Stations
* Edges → Railway Corridors
* Agents → Trains

This enables powerful graph-theoretic analysis and optimization.

---

### ⚠️ Failure Simulation

Simulate:

* Track failures
* Corridor disruptions
* Congestion events

Observe their impact across the network.

---

### 🔄 Self-Healing Routing

When a track fails:

1. Failure is detected
2. A healthy operational graph is generated
3. Alternative routes are computed
4. Active trains are rerouted automatically

No manual intervention required.

---

### 📈 Cascading Stress Propagation

Failures rarely remain local.

RailTwin models how congestion propagates through neighboring stations and corridors.

This helps identify emerging bottlenecks before network-wide degradation occurs.

---

### 🎯 Critical Station Detection

Using graph centrality metrics, RailTwin identifies stations whose failure would cause maximum disruption.

These stations receive higher operational priority.

---

### 🤖 Risk Prediction Engine

Risk scores are calculated using:

Risk =
0.5 × Stress
+
0.3 × Criticality
+
0.2 × Load Ratio

This enables proactive monitoring and decision making.

---

## 🧮 Mathematical Foundation

RailTwin is built upon concepts from:

### Graph Theory

* Shortest Paths
* Network Connectivity
* Graph Traversal

### Network Science

* Failure Propagation
* Cascading Effects
* Resilience Analysis

### Optimization

* Dynamic Routing
* Load Balancing
* Recovery Planning

### Centrality Analysis

* Betweenness Centrality
* Critical Infrastructure Detection

---

## 🏗️ System Architecture

Frontend (React Dashboard)

↓

FastAPI API Layer

↓

Simulation Engine

↓

Graph Analytics Layer

↓

Railway Network Model (NetworkX)

---

## 🖥️ Dashboard Features

The dashboard provides:

* Live railway map
* Network health score
* Stress visualization
* Active train tracking
* Failure monitoring
* Station telemetry
* Criticality analysis
* AI recovery insights

---

## 🚀 Getting Started

### Backend

```bash
uvicorn api:app --reload
```

Backend API:

```text
http://localhost:8001
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## 🔌 API Endpoints

### Get Current State

```http
GET /state
```

Returns:

* Stations
* Tracks
* Trains
* Stress Metrics
* Criticality Data

---

### Advance Simulation

```http
POST /tick
```

Advances simulation time.

---

### Fail Track

```http
POST /fail-track
```

Request:

```json
{
  "source": "Pune",
  "target": "Nashik"
}
```

---

### Repair Track

```http
POST /repair-track
```

Request:

```json
{
  "source": "Pune",
  "target": "Nashik"
}
```

---

## 🔮 Future Work

* Graph Neural Networks for failure prediction
* Reinforcement Learning based train scheduling
* Real-world railway telemetry integration
* Multi-agent autonomous dispatching
* National-scale railway digital twin
* Predictive maintenance engine

---

## 🏆 Hackathon Vision

RailTwin transforms railway operations from reactive monitoring to autonomous resilience.

Instead of simply detecting failures, the system continuously evaluates network health, predicts risk, and orchestrates recovery actions in real time.

> One failed corridor should not stop an entire railway network.

---
## Screenshots
<img width="2876" height="1522" alt="rt3" src="https://github.com/user-attachments/assets/31686416-023a-4cb1-a58f-eb912b70b5a2" />
<img width="2880" height="1564" alt="rt1" src="https://github.com/user-attachments/assets/2b2ec725-5a62-4888-b650-7f95d01431c9" />
<img width="2880" height="1552" alt="rt2" src="https://github.com/user-attachments/assets/887f865f-8209-482f-a380-74ff23a84c34" />

