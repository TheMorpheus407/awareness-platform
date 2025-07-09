# Lastenheft: Cybersecurity Awareness Plattform
**Version 1.0 | Stand: Januar 2025**

## 1. Einleitung und Zielsetzung

### 1.1 Projektziel
Entwicklung einer vollautomatisierten Online-Plattform für Cybersecurity Awareness Schulungen, die alle regulatorischen Anforderungen im DACH-Raum erfüllt und Unternehmen eine "hands-off" Lösung bietet.

### 1.2 Produktvision
Eine Plattform, die es Unternehmen ermöglicht, ihre Mitarbeiter kontinuierlich und automatisiert in Cybersecurity zu schulen, dabei alle Compliance-Anforderungen zu erfüllen und messbare Verbesserungen der Sicherheitskultur zu erreichen.

### 1.3 Technische Rahmenbedingungen
- **Frontend**: React (Single Page Application)
- **Backend**: Python REST API (Flask/FastAPI)
- **Datenbank**: PostgreSQL
- **Video-Hosting**: YouTube (unlisted videos)
- **Hosting**: Deutsche Cloud-Provider (DSGVO-konform)

## 2. Funktionale Anforderungen

### 2.1 Benutzerverwaltung

#### 2.1.1 Registrierung und Onboarding
- **Unternehmensregistrierung**
  - Self-Service Registrierungsformular
  - Validierung der Unternehmensdaten (Handelsregister-API)
  - Automatische Compliance-Profil-Erstellung basierend auf Branche/Größe
  - Setup-Wizard für Ersteinrichtung (max. 15 Minuten)

- **Benutzerverwaltung**
  - CSV-Import für Massenanlage
  - Automatische Benutzererstellung via API
  - Rollenbasierte Zugriffssteuerung (Admin, Manager, Mitarbeiter)
  - Automatische Deaktivierung bei Austritt

#### 2.1.2 Authentifizierung
- E-Mail/Passwort Login
- Single Sign-On (SAML 2.0)
- Zwei-Faktor-Authentifizierung (TOTP)
- Passwort-Reset Self-Service

### 2.2 Schulungsmanagement

#### 2.2.1 Kursverwaltung
- **Kurskatalog**
  - Basis-Module (Pflicht für alle)
  - Rollenspezifische Module
  - Branchenspezifische Module
  - Compliance-spezifische Module (NIS-2, DSGVO, etc.)

- **Kursstruktur**
  - Modularer Aufbau (5-15 Minuten pro Modul)
  - YouTube-Video Integration
  - Interaktive Wissensfragen
  - Downloadbare Zusammenfassungen (PDF)

#### 2.2.2 Automatisierte Kurszuweisung
- **Regelbasierte Zuweisung**
  - Nach Rolle/Abteilung
  - Nach Compliance-Anforderungen
  - Nach Risikoprofil (basierend auf Phishing-Tests)
  - Zeitbasierte Wiederholungen

- **Lernpfade**
  - Onboarding-Pfad für neue Mitarbeiter
  - Jährliche Auffrischung
  - Quartalsweise Mikro-Learnings
  - Event-basierte Schulungen (nach Sicherheitsvorfällen)

### 2.3 Phishing-Simulation

#### 2.3.1 Kampagnenmanagement
- **Template-Bibliothek**
  - 50+ vorgefertigte Phishing-Templates
  - Schwierigkeitsgrade (Einfach, Mittel, Schwer)
  - Branchenspezifische Templates
  - Aktuelle Bedrohungen (quartalsweise Updates)

- **Kampagnenplanung**
  - Automatische Kampagnen nach Zeitplan
  - Zielgruppenauswahl
  - A/B Testing Funktionalität
  - Whitelisting für Ausnahmen

#### 2.3.2 Durchführung und Tracking
- **Versand**
  - Integration mit eigenem Mail-Server
  - Personalisierung der E-Mails
  - Randomisierte Versandzeiten
  - Mobile-optimierte Landing Pages

- **Tracking**
  - E-Mail geöffnet
  - Link geklickt
  - Daten eingegeben
  - Gemeldet als Phishing

#### 2.3.3 Sofortiges Feedback
- Bei Klick: Aufklärungsseite mit Erklärung
- Micro-Learning Modul (2-3 Minuten)
- Tipps zur Erkennung
- Positive Verstärkung bei korrekter Meldung

### 2.4 Reporting und Analytics

#### 2.4.1 Dashboards
- **Executive Dashboard**
  - Compliance-Status Übersicht
  - Risiko-Score der Organisation
  - Trend-Analysen
  - Benchmark gegen Industrie

- **Manager Dashboard**
  - Team-Performance
  - Individuelle Fortschritte
  - Risiko-Hotspots
  - Anstehende Schulungen

- **Mitarbeiter Dashboard**
  - Persönlicher Fortschritt
  - Abgeschlossene Module
  - Phishing-Performance
  - Gamification-Elemente (Punkte, Badges)

#### 2.4.2 Compliance-Reporting
- **Automatische Reports**
  - NIS-2 Compliance Report
  - DSGVO Schulungsnachweis
  - ISO 27001 Awareness-Dokumentation
  - Branchenspezifische Reports (TISAX, BAIT, etc.)

- **Audit-Trail**
  - Vollständige Aktivitätshistorie
  - Manipulationssichere Zeitstempel
  - Export-Funktionen (PDF, CSV)
  - Digitale Signaturen

### 2.5 Content Management

#### 2.5.1 Kurserstellung
- Template-basiertes Authoring
- YouTube Video-Einbindung
- Quiz-Builder
- Mehrsprachigkeit (DE, EN, FR, IT)

#### 2.5.2 Zertifikate
- Automatische Generierung nach Abschluss
- QR-Code zur Verifizierung
- Individuelle Gestaltung pro Unternehmen
- Ablaufdatum und Erneuerungshinweise

### 2.6 Kommunikation

#### 2.6.1 Automatisierte E-Mails
- Willkommens-E-Mails
- Kurs-Einladungen
- Erinnerungen (3x vor Fälligkeit)
- Eskalation an Manager
- Zertifikatsversand

#### 2.6.2 In-App Benachrichtigungen
- Neue verfügbare Kurse
- Fällige Schulungen
- Team-Updates
- Sicherheitswarnungen

## 3. Nicht-funktionale Anforderungen

### 3.1 Performance
- Ladezeit < 3 Sekunden
- Gleichzeitige Nutzer: bis 1.000
- Video-Streaming ohne Unterbrechung
- API Response Time < 500ms

### 3.2 Sicherheit
- Ende-zu-Ende Verschlüsselung
- Sichere Passwort-Richtlinien
- Session-Management
- Rate Limiting
- Input Validation
- SQL Injection Schutz
- XSS Prävention

### 3.3 Datenschutz (DSGVO)
- Datenminimierung
- Zweckbindung
- Löschkonzepte
- Auskunftsrecht-Funktionen
- Datenportabilität
- Privacy by Design

### 3.4 Verfügbarkeit
- 99.5% Uptime SLA
- Tägliche Backups
- Disaster Recovery Plan
- Wartungsfenster nur nachts/Wochenende

### 3.5 Usability
- Responsive Design (Mobile, Tablet, Desktop)
- Barrierefreiheit (WCAG 2.1 Level AA)
- Intuitive Navigation
- Kontextsensitive Hilfe
- Mehrsprachigkeit

### 3.6 Integration
- REST API für Drittanbieter
- Webhook-Support
- CSV Import/Export
- SCORM Export
- Single Sign-On (SAML 2.0)

## 4. Technische Architektur

### 4.1 Frontend (React)
```
src/
├── components/
│   ├── auth/
│   ├── dashboard/
│   ├── courses/
│   ├── phishing/
│   ├── reporting/
│   └── common/
├── pages/
├── services/
├── hooks/
├── utils/
└── styles/
```

**Kernbibliotheken:**
- React Router (Navigation)
- Axios (API-Kommunikation)
- Chart.js (Visualisierungen)
- React Hook Form (Formulare)
- i18next (Mehrsprachigkeit)

### 4.2 Backend (Python)
```
app/
├── api/
│   ├── auth/
│   ├── users/
│   ├── courses/
│   ├── phishing/
│   ├── reporting/
│   └── admin/
├── models/
├── services/
├── tasks/
├── utils/
└── config/
```

**Kernbibliotheken:**
- FastAPI/Flask (Web Framework)
- SQLAlchemy (ORM)
- Celery (Background Tasks)
- Pydantic (Validation)
- Alembic (Migrations)

### 4.3 Datenbank-Schema (Auszug)
```sql
-- Unternehmen
companies (
  id, name, industry, size, compliance_profile,
  created_at, settings
)

-- Benutzer
users (
  id, company_id, email, role, department,
  risk_score, last_login, created_at
)

-- Kurse
courses (
  id, title, description, duration, difficulty,
  compliance_tags, youtube_url, questions
)

-- Fortschritt
user_progress (
  user_id, course_id, status, score,
  completed_at, certificate_id
)

-- Phishing
phishing_campaigns (
  id, company_id, name, template_id,
  scheduled_at, status
)

phishing_results (
  campaign_id, user_id, opened, clicked,
  data_entered, reported, timestamp
)
```

## 5. Implementierungsphasen

### Phase 1: MVP (3 Monate)
- Benutzerverwaltung (Basic)
- 10 Basis-Kurse
- Einfaches Reporting
- DSGVO-Compliance

### Phase 2: Erweiterung (2 Monate)
- Phishing-Simulation
- Erweiterte Reports
- API-Integrationen
- Mehrsprachigkeit

### Phase 3: Automatisierung (2 Monate)
- Regelbasierte Zuweisung
- Automatische Kampagnen
- KI-Personalisierung
- Mobile Apps

### Phase 4: Premium Features (2 Monate)
- Branchenspezifische Module
- White-Label Option
- Advanced Analytics
- Gamification

## 6. Compliance-Anforderungen

### 6.1 Regulatorische Standards
- **NIS-2**: Nachweis Führungskräfte-Training
- **DSGVO**: Art. 32, 39 Dokumentation
- **ISO 27001**: Awareness-Metriken
- **TISAX**: Automotive-spezifische Module
- **BAIT/MaRisk**: Finanz-Compliance

### 6.2 Zertifizierungen
- BSI Grundschutz-konform
- ISAE 3402 / SOC 2
- ISO 27001 vorbereitet
- TÜV-geprüft

## 7. Erfolgskriterien

### 7.1 Business KPIs
- Reduzierung Phishing-Klickrate < 5%
- Schulungs-Abschlussrate > 95%
- Kunde-Onboarding < 30 Minuten
- Support-Anfragen < 5% der Nutzer

### 7.2 Technische KPIs
- Verfügbarkeit > 99.5%
- Ladezeiten < 3 Sekunden
- Fehlerrate < 0.1%
- API-Latenz < 500ms

## 8. Wartung und Support

### 8.1 Content-Updates
- Quartalsweise neue Phishing-Templates
- Monatliche Kursaktualisierungen
- Jährliche Compliance-Reviews
- Ad-hoc Sicherheitswarnungen

### 8.2 Support-Level
- E-Mail Support (24h Response)
- Wissensdatenbank
- Video-Tutorials
- Quartalsweise Webinare

## 9. Preismodell

### 9.1 Abonnement-Stufen
- **Starter** (bis 50 Nutzer): 149€/Monat
- **Professional** (bis 500 Nutzer): 2,50€/Nutzer/Monat
- **Enterprise** (500+ Nutzer): Individuelle Preise

### 9.2 Inkludierte Leistungen
- Alle Basis-Module
- Unbegrenzte Phishing-Tests
- Compliance-Reports
- Support & Updates

## 10. Risiken und Mitigationen

### 10.1 Technische Risiken
- **YouTube-Abhängigkeit**: Backup-Hosting vorbereiten
- **Phishing-Blockierung**: Whitelisting-Guides
- **Performance**: CDN und Caching

### 10.2 Rechtliche Risiken
- **Datenschutz**: Externe DSGVO-Beratung
- **Haftung**: Klare AGB und Haftungsausschluss
- **Compliance**: Regelmäßige juristische Reviews

## 11. Anhänge

### A. Mockups und Wireframes
(Separat zu erstellen)

### B. API-Dokumentation
(Nach OpenAPI 3.0 Standard)

### C. Testszenarien
(Detaillierte Testfälle für alle Features)

### D. Deployment-Anleitung
(Infrastructure as Code mit Terraform)