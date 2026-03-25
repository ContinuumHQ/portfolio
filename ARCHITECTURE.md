Architecture Overview
Dieses Dokument beschreibt die architektonischen Entscheidungen hinter den drei Portfolio-Projekten. Ziel ist eine strikte Trennung von Belangen (Separation of Concerns) und eine hohe Portabilität durch Containerisierung.
---
Kernprinzipien
Alle Projekte folgen einem einheitlichen Architektur-Muster, um Wartbarkeit und Testbarkeit zu garantieren:

* Orchestrierung vs. Domänenlogik: Die main.py fungiert rein als Orchestrator. Sie kennt den Ablauf, aber nicht die mathematischen oder technischen Details der Umsetzung.
* Stateless Execution: Wo immer möglich, sind die Rechenschritte zustandslos. Daten fließen durch eine Pipeline, anstatt globale Zustände zu verändern.
* Dependency Inversion (Light): High-Level-Entscheidungen (wie Pfade oder Parameter) werden über das CLI (argparse) injiziert, anstatt sie tief im Code zu verankern.
* Resilience: Implementierung von Graceful Shutdowns und robustem Error-Handling, um in Produktionsumgebungen (Docker) stabil zu laufen.
  
---

Die drei Säulen

1. Predictive Maintenance (Data Engineering & AI)
    * Architektur: Lineare Datenpipeline.
    * Entscheidung: Trennung von Datengenerierung, Processing und Scoring. Der Verzicht auf komplexe ML-Frameworks zugunsten von statistischen Methoden (Z-Score/IQR) demonstriert ein tiefes Verständnis der zugrunde liegenden Mathematik.

2. Network Monitor (System Integration)
    * Architektur: Event-Loop / Task-basierte Überwachung.
    * Entscheidung: Entkopplung von Monitoring-Logik und Reporting. Der Einsatz von YAML für die Konfiguration spiegelt Industriestandards (Ansible/K8s) wider. Ein besonderer Fokus liegt auf der Signalverarbeitung (KeyboardInterrupt) für sauberes Container-Handling.

3. Sales Dashboard (Data Processing)
    * Architektur: Relationales Datenmodell (Star-Schema Ansatz).
    * Entscheidung: Persistenzschicht (SQLite) ist klar von der Logik getrennt. Die Pipeline ist idempotent ausgelegt – ein Re-Run zerstört keine bestehenden Daten, sondern validiert den Ist-Zustand.
      
---

Deployment-Strategie
Durch die Docker-First-Strategie wird die Infrastruktur als Code (IaC) behandelt. Die docker-compose.yaml stellt sicher, dass die Projekte unabhängig vom Host-System (OS, Python-Version) sofort und reproduzierbar lauffähig sind.

---
