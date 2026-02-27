# CORE-HIDS

## Overview

CORE-HIDS is a Host-Based Intrusion Detection System designed to monitor system activities, analyze behavioral patterns, and detect anomalous behaviors using a modular detection pipeline.

The project is written in Python and follows a separation-of-concerns architecture to ensure maintainability, extensibility, and research-oriented development.

---

## Project Structure


src/
├── alerts.py # Alert generation and management
├── baseline.py # Behavioral baseline profiling
├── config.py # System configuration parameters
├── detector.py # Core detection logic (legacy entry / bridge to DetectionEngine)
├── log_monitor.py # System log monitoring module
├── logger.py # Internal logging framework
├── main.py # Application entry point
├── persistence.py # Event storage and history backend
├── worker.py # Concurrent processing layer
└── init.py


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
cd CORE-HIDS
pip install -r requirements.txt
Usage

Run the HIDS system using:

python src/main.py
Configuration

System parameters can be customized inside:

src/config.py

Adjust settings according to monitoring and detection requirements.

Roadmap

✅ Modular detection pipeline

🔧 DetectionEngine refactor

🔧 Rule abstraction layer

🔧 Severity & escalation engine

🔧 Persistence layer enhancement

🔧 Performance optimization for real-time monitoring

Contributing

Fork the repository

Create a feature branch

Implement and test your changes

Submit a Pull Request with detailed explanation

License

Specify the project license inside the LICENSE file.

Security Notice

CORE-HIDS is a security research project. Avoid exposing sensitive monitoring components without proper hardening and access control.