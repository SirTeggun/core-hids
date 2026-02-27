# CORE-HIDS

## Overview

CORE-HIDS is an advanced research-oriented Host-Based Intrusion Detection framework designed to explore modern approaches to system-level security monitoring and behavioral anomaly detection.

The project focuses on constructing a flexible detection environment capable of analyzing host activity through a modular and extensible processing pipeline. Rather than implementing a rigid detection strategy, CORE-HIDS is architected as an experimental security platform where detection logic, profiling mechanisms, and response policies can evolve independently.

The system is developed in Python following a strict separation-of-concerns design philosophy, enabling long-term maintainability and supporting progressive enhancement of detection capabilities. The architecture is optimized for extensibility, allowing future integration of rule-based detection engines, statistical anomaly models, and severity-driven escalation workflows.

CORE-HIDS is intended to function both as a practical monitoring solution and as a security research framework for studying host-based threat detection methodologies, behavioral baseline modeling, and automated security response orchestration.

The long-term objective of the project is to evolve into a high-performance detection platform capable of supporting modular intelligence layers for advanced host security analytics.
---

## Project Structure

```bash
src/
├── __init__.py
├── main.py
├── config.py
├── logger.py
├── detector.py
├── log_monitor.py
├── baseline.py
├── alerts.py
├── persistence.py
├── worker.py
```

---

## Architecture

CORE-HIDS is built around a modular detection pipeline designed for future scalability.

### Detection Workflow

1. Event acquisition through `log_monitor`
2. Behavioral or rule-based analysis
3. Alert generation via `alerts` module
4. Logging and persistence handling
5. Asynchronous processing through worker threads or tasks

### Planned Evolution

The project roadmap includes:

- Refactoring detection logic into a `DetectionEngine` class
- Implementing modular rule objects for detection strategies
- Adding severity scoring and escalation management
- Building a robust persistence backend
- Optimizing real-time analysis performance

---

## Core Modules

### detector.py

Contains the main detection logic and serves as the bridge toward the future detection engine implementation.

### log_monitor.py

Responsible for system event collection and monitoring.

### baseline.py

Implements behavioral baseline profiling to support anomaly detection approaches.

### alerts.py

Handles security alert generation and notification workflows.

### persistence.py

Provides storage capabilities for detected events and historical analysis data.

### worker.py

Supports concurrent event processing and pipeline execution.

---

## Installation

```bash
git clone https://github.com/yourusername/CORE-HIDS.git
```
```bash
cd CORE-HIDS
```
```bash
pip install -r requirements.txt
```

---

## Usage

Run the HIDS system using:

```bash
python src/main.py
```

---

## Configuration

System parameters can be customized inside:

```bash
src/config.py
```

## Roadmap

🔧 Modular detection pipeline

🔧 DetectionEngine refactor

🔧 Rule abstraction layer

🔧 Severity & escalation engine

🔧 Persistence layer enhancement

🔧 Performance optimization for real-time monitoring

## Contributing

1. Fork the repository

2. Create a feature branch

3. Implement and test your changes

4. Submit a Pull Request with detailed explanation

## License

Specify the project license inside the LICENSE file.

## Security Notice

CORE-HIDS is a security research project. Avoid exposing sensitive monitoring components without proper hardening and access control.