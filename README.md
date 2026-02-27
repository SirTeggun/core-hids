# Host Intrusion Detection System (HIDS)

## 📌 Overview

This project is a modular Host Intrusion Detection System (HIDS) designed for defensive cybersecurity research and educational purposes.

The system implements a rule-based detection pipeline combined with baseline behavior monitoring, alert generation, and persistent logging mechanisms.

> ⚠️ Disclaimer: This software is intended for educational and defensive security research only.

---

## 🧠 Architecture

The system follows a modular detection workflow:

- Log monitoring and acquisition  
- Baseline behavior analysis  
- Rule-based detection logic  
- Alert generation engine  
- Worker execution layer  
- Persistence storage interface  

### Planned Architectural Evolution

- Introduce a `DetectionEngine` abstraction layer  
- Implement modular rule-based detection objects  
- Add severity scoring and escalation management  
- Develop persistence layer abstraction  

---

## 📁 Project Structure

src/
├── detector.py
├── baseline.py
├── alerts.py
├── config.py
├── log_monitor.py
├── logger.py
├── worker.py
├── persistence.py
├── main.py

tests/
logs/

---

## 🚀 Installation

### Clone the repository

```bash
git clone <repository_url>
cd hids-project

---
---
---
---
--
---
---

Create virtual environment