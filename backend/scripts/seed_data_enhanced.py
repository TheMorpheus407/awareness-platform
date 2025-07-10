"""Enhanced seed data for development and testing with realistic German company data."""

import asyncio
from datetime import datetime, timedelta
import random
from typing import List
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session_maker
from models import (
    User, Company, Course, Quiz, QuizQuestion, 
    PhishingTemplate, PhishingCampaign, PhishingResult,
    UserCourseProgress, AuditLog, AnalyticsEvent
)
from models.user import UserRole
from models.company import CompanySize, CompanyStatus
from core.security import get_password_hash


# German first and last names for realistic data
GERMAN_FIRST_NAMES = [
    "Thomas", "Michael", "Andreas", "Stefan", "Christian", "Daniel", "Martin", "Markus",
    "Julia", "Sarah", "Anna", "Lisa", "Maria", "Christina", "Nicole", "Sandra",
    "Frank", "Peter", "Klaus", "Jürgen", "Wolfgang", "Matthias", "Alexander", "Sebastian",
    "Sabine", "Petra", "Monika", "Claudia", "Stefanie", "Andrea", "Katrin", "Susanne"
]

GERMAN_LAST_NAMES = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
    "Schulz", "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf",
    "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger", "Hofmann", "Lange"
]

DEPARTMENTS = [
    "IT", "Human Resources", "Finance", "Sales", "Marketing", "Operations", 
    "Customer Service", "R&D", "Legal", "Procurement", "Quality Assurance"
]

JOB_TITLES = {
    "IT": ["IT Manager", "System Administrator", "Developer", "IT Support", "Security Analyst"],
    "Human Resources": ["HR Manager", "HR Business Partner", "Recruiter", "HR Assistant"],
    "Finance": ["CFO", "Financial Controller", "Accountant", "Financial Analyst"],
    "Sales": ["Sales Director", "Account Manager", "Sales Representative", "Sales Support"],
    "Marketing": ["Marketing Manager", "Content Manager", "Marketing Specialist", "Social Media Manager"],
    "Operations": ["Operations Manager", "Supply Chain Manager", "Logistics Coordinator"],
    "Customer Service": ["Customer Service Manager", "Support Agent", "Customer Success Manager"],
    "R&D": ["R&D Director", "Research Scientist", "Product Developer", "Lab Technician"],
    "Legal": ["Legal Counsel", "Compliance Officer", "Contract Manager", "Legal Assistant"],
    "Procurement": ["Procurement Manager", "Buyer", "Supplier Manager", "Procurement Analyst"],
    "Quality Assurance": ["QA Manager", "Quality Inspector", "QA Engineer", "Compliance Auditor"]
}


async def create_companies(session: AsyncSession) -> List[Company]:
    """Create sample German companies."""
    companies = []
    
    company_data = [
        {
            "name": "TechVision GmbH",
            "domain": "techvision.de",
            "size": CompanySize.LARGE,
            "status": CompanyStatus.ACTIVE,
            "industry": "Information Technology",
            "country": "DE",
            "timezone": "Europe/Berlin",
            "max_users": 500,
            "trial_ends_at": datetime.utcnow() - timedelta(days=30),
            "subscription_ends_at": datetime.utcnow() + timedelta(days=335),
            "primary_color": "#0066CC",
            "secondary_color": "#FF6600"
        },
        {
            "name": "AutoWerk Bayern AG",
            "domain": "autowerk-bayern.de",
            "size": CompanySize.ENTERPRISE,
            "status": CompanyStatus.ACTIVE,
            "industry": "Automotive",
            "country": "DE",
            "timezone": "Europe/Berlin",
            "max_users": 5000,
            "trial_ends_at": datetime.utcnow() - timedelta(days=90),
            "subscription_ends_at": datetime.utcnow() + timedelta(days=700),
            "primary_color": "#003366",
            "secondary_color": "#C0C0C0"
        },
        {
            "name": "FinanzBeratung Hamburg",
            "domain": "finanzberatung-hh.de",
            "size": CompanySize.MEDIUM,
            "status": CompanyStatus.ACTIVE,
            "industry": "Financial Services",
            "country": "DE",
            "timezone": "Europe/Berlin",
            "max_users": 150,
            "trial_ends_at": datetime.utcnow() - timedelta(days=14),
            "subscription_ends_at": datetime.utcnow() + timedelta(days=351),
            "primary_color": "#006633",
            "secondary_color": "#FFD700"
        },
        {
            "name": "MediCare Klinikgruppe",
            "domain": "medicare-kliniken.de",
            "size": CompanySize.LARGE,
            "status": CompanyStatus.ACTIVE,
            "industry": "Healthcare",
            "country": "DE",
            "timezone": "Europe/Berlin",
            "max_users": 1200,
            "trial_ends_at": datetime.utcnow() - timedelta(days=60),
            "subscription_ends_at": datetime.utcnow() + timedelta(days=250),
            "primary_color": "#DC143C",
            "secondary_color": "#FFFFFF"
        },
        {
            "name": "StartUp Solutions Berlin",
            "domain": "startup-solutions.berlin",
            "size": CompanySize.SMALL,
            "status": CompanyStatus.TRIAL,
            "industry": "Technology Startup",
            "country": "DE",
            "timezone": "Europe/Berlin",
            "max_users": 25,
            "trial_ends_at": datetime.utcnow() + timedelta(days=14),
            "primary_color": "#FF1493",
            "secondary_color": "#00CED1"
        },
        {
            "name": "Logistik Express GmbH",
            "domain": "logistik-express.de",
            "size": CompanySize.MEDIUM,
            "status": CompanyStatus.ACTIVE,
            "industry": "Logistics",
            "country": "DE",
            "timezone": "Europe/Berlin",
            "max_users": 300,
            "trial_ends_at": datetime.utcnow() - timedelta(days=45),
            "subscription_ends_at": datetime.utcnow() + timedelta(days=180),
            "primary_color": "#FF8C00",
            "secondary_color": "#4B0082"
        }
    ]
    
    for data in company_data:
        company = Company(**data)
        session.add(company)
        companies.append(company)
    
    await session.flush()
    return companies


async def create_users(session: AsyncSession, companies: List[Company]) -> List[User]:
    """Create realistic German users with proper roles and departments."""
    users = []
    
    # System admin (Bootstrap Academy)
    system_admin = User(
        email="admin@bootstrap-awareness.de",
        password_hash=get_password_hash("SecureAdmin123!"),
        first_name="System",
        last_name="Administrator",
        role=UserRole.SYSTEM_ADMIN,
        company_id=companies[0].id,  # Assign to first company for RLS
        is_active=True,
        email_verified=True,
        email_verified_at=datetime.utcnow() - timedelta(days=365),
        job_title="Platform Administrator",
        department="IT",
        language="de"
    )
    session.add(system_admin)
    users.append(system_admin)
    
    # Create users for each company
    for company in companies:
        # Company admin
        admin_first = random.choice(GERMAN_FIRST_NAMES)
        admin_last = random.choice(GERMAN_LAST_NAMES)
        company_admin = User(
            email=f"admin@{company.domain}",
            password_hash=get_password_hash("CompanyAdmin123!"),
            first_name=admin_first,
            last_name=admin_last,
            company_id=company.id,
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
            email_verified=True,
            email_verified_at=datetime.utcnow() - timedelta(days=random.randint(30, 180)),
            job_title="IT Security Manager",
            department="IT",
            phone=f"+49 {random.randint(100, 999)} {random.randint(1000000, 9999999)}",
            language="de",
            last_login_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        session.add(company_admin)
        users.append(company_admin)
        
        # Determine number of employees based on company size
        employee_counts = {
            CompanySize.SMALL: random.randint(5, 15),
            CompanySize.MEDIUM: random.randint(20, 40),
            CompanySize.LARGE: random.randint(50, 100),
            CompanySize.ENTERPRISE: random.randint(100, 200)
        }
        num_employees = employee_counts.get(company.size, 10)
        
        # Create managers (10% of employees)
        num_managers = max(1, num_employees // 10)
        for i in range(num_managers):
            dept = random.choice(DEPARTMENTS)
            first_name = random.choice(GERMAN_FIRST_NAMES)
            last_name = random.choice(GERMAN_LAST_NAMES)
            
            manager = User(
                email=f"{first_name.lower()}.{last_name.lower()}@{company.domain}",
                password_hash=get_password_hash("Manager123!"),
                first_name=first_name,
                last_name=last_name,
                company_id=company.id,
                role=UserRole.MANAGER,
                is_active=True,
                email_verified=True,
                email_verified_at=datetime.utcnow() - timedelta(days=random.randint(7, 365)),
                department=dept,
                job_title=f"{dept} Manager",
                phone=f"+49 {random.randint(100, 999)} {random.randint(1000000, 9999999)}",
                language="de",
                last_login_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
            )
            session.add(manager)
            users.append(manager)
        
        # Create regular employees
        for i in range(num_employees - num_managers):
            dept = random.choice(DEPARTMENTS)
            first_name = random.choice(GERMAN_FIRST_NAMES)
            last_name = random.choice(GERMAN_LAST_NAMES)
            job_title = random.choice(JOB_TITLES.get(dept, ["Specialist"]))
            
            # Some employees might not be active or verified
            is_active = random.random() > 0.05  # 95% active
            is_verified = random.random() > 0.1 if is_active else False  # 90% verified if active
            
            employee = User(
                email=f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@{company.domain}",
                password_hash=get_password_hash("Employee123!"),
                first_name=first_name,
                last_name=last_name,
                company_id=company.id,
                role=UserRole.EMPLOYEE,
                is_active=is_active,
                email_verified=is_verified,
                email_verified_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)) if is_verified else None,
                department=dept,
                job_title=job_title,
                phone=f"+49 {random.randint(100, 999)} {random.randint(1000000, 9999999)}" if random.random() > 0.3 else None,
                language="de",
                last_login_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)) if is_active else None,
                failed_login_attempts=random.choice([0, 0, 0, 1, 2]) if is_active else 0
            )
            session.add(employee)
            users.append(employee)
    
    await session.flush()
    return users


async def create_comprehensive_courses(session: AsyncSession) -> List[Course]:
    """Create comprehensive cybersecurity awareness courses in German."""
    courses = []
    
    course_data = [
        # Basic Security Courses
        {
            "title": "Grundlagen der Passwortsicherheit",
            "description": "Lernen Sie, wie Sie sichere Passwörter erstellen und verwalten, um Ihre Konten zu schützen.",
            "category": "Grundlagen",
            "difficulty_level": "beginner",
            "duration_minutes": 15,
            "youtube_video_id": "3NjQ9b3pgIg",
            "tags": ["passwort", "sicherheit", "grundlagen", "authentifizierung"],
            "language": "de",
            "is_active": True
        },
        {
            "title": "Phishing-E-Mails erkennen",
            "description": "Meistern Sie die Kunst, Phishing-Angriffe zu identifizieren und zu vermeiden.",
            "category": "E-Mail-Sicherheit",
            "difficulty_level": "intermediate",
            "duration_minutes": 20,
            "youtube_video_id": "Y7zNlEMDmI4",
            "tags": ["phishing", "email", "sicherheit", "betrug"],
            "language": "de",
            "is_active": True
        },
        {
            "title": "DSGVO für Mitarbeiter",
            "description": "Verstehen Sie Ihre Verantwortlichkeiten im Rahmen der DSGVO-Vorschriften.",
            "category": "Compliance",
            "difficulty_level": "beginner",
            "duration_minutes": 30,
            "youtube_video_id": "ZyYW6Wc7Zno",
            "tags": ["dsgvo", "datenschutz", "compliance", "gdpr"],
            "language": "de",
            "is_active": True
        },
        {
            "title": "Social Engineering Abwehr",
            "description": "Schützen Sie sich vor Manipulation und Social Engineering Angriffen.",
            "category": "Fortgeschrittene Sicherheit",
            "difficulty_level": "advanced",
            "duration_minutes": 25,
            "youtube_video_id": "lc7scxvKQOo",
            "tags": ["social-engineering", "sicherheit", "manipulation", "psychologie"],
            "language": "de",
            "is_active": True
        },
        {
            "title": "Sicheres Arbeiten im Home Office",
            "description": "Best Practices für die Aufrechterhaltung der Sicherheit beim Arbeiten von zu Hause.",
            "category": "Remote-Arbeit",
            "difficulty_level": "intermediate",
            "duration_minutes": 20,
            "youtube_video_id": "We1rnNpV_rA",
            "tags": ["remote", "homeoffice", "vpn", "sicherheit"],
            "language": "de",
            "is_active": True
        },
        # Advanced Courses
        {
            "title": "Ransomware-Prävention",
            "description": "Verstehen und verhindern Sie Ransomware-Angriffe in Ihrem Unternehmen.",
            "category": "Bedrohungsabwehr",
            "difficulty_level": "advanced",
            "duration_minutes": 35,
            "youtube_video_id": "aMz8khLgpBs",
            "tags": ["ransomware", "malware", "backup", "krisenmanagement"],
            "language": "de",
            "is_active": True
        },
        {
            "title": "Sichere Nutzung von Cloud-Diensten",
            "description": "Lernen Sie den sicheren Umgang mit Cloud-Speicher und -Anwendungen.",
            "category": "Cloud-Sicherheit",
            "difficulty_level": "intermediate",
            "duration_minutes": 25,
            "youtube_video_id": "xpD6e9hGikM",
            "tags": ["cloud", "datenspeicherung", "verschlüsselung", "zugriffskontrolle"],
            "language": "de",
            "is_active": True
        },
        {
            "title": "Mobile Gerätesicherheit",
            "description": "Sicherer Umgang mit Smartphones und Tablets im Unternehmenskontext.",
            "category": "Mobile Sicherheit",
            "difficulty_level": "beginner",
            "duration_minutes": 18,
            "youtube_video_id": "WySeJE8cHYs",
            "tags": ["mobile", "byod", "smartphone", "tablet"],
            "language": "de",
            "is_active": True
        },
        {
            "title": "Incident Response Grundlagen",
            "description": "Was tun bei einem Sicherheitsvorfall? Erste Schritte und Meldewege.",
            "category": "Incident Management",
            "difficulty_level": "intermediate",
            "duration_minutes": 22,
            "youtube_video_id": "qF3kYMZJDyY",
            "tags": ["incident", "response", "notfall", "meldung"],
            "language": "de",
            "is_active": True
        },
        {
            "title": "NIS-2 Compliance Überblick",
            "description": "Die wichtigsten Anforderungen der NIS-2-Richtlinie für Ihr Unternehmen.",
            "category": "Compliance",
            "difficulty_level": "advanced",
            "duration_minutes": 40,
            "youtube_video_id": "5MmUyQtYbl8",
            "tags": ["nis2", "compliance", "eu", "regulierung"],
            "language": "de",
            "is_active": True
        }
    ]
    
    for idx, data in enumerate(course_data):
        # Set prerequisites for advanced courses
        if data["difficulty_level"] == "advanced" and idx > 0:
            data["prerequisites"] = [courses[0].id] if courses else []
        
        course = Course(**data)
        session.add(course)
        courses.append(course)
    
    await session.flush()
    
    # Create comprehensive quizzes for each course
    for course in courses:
        quiz = Quiz(
            course_id=course.id,
            title=f"{course.title} - Wissenstest",
            passing_score=70,
            time_limit_minutes=10,
            max_attempts=3,
            is_required=True
        )
        session.add(quiz)
        await session.flush()
        
        # Create diverse questions
        questions = []
        
        # Multiple choice question
        questions.append({
            "question_text": f"Was ist das Hauptthema des Kurses '{course.title}'?",
            "question_type": "multiple_choice",
            "options": {
                "a": "Netzwerksicherheit",
                "b": course.category,
                "c": "Datenbankmanagement",
                "d": "Cloud Computing"
            },
            "correct_answer": "b",
            "explanation": f"Dieser Kurs behandelt hauptsächlich {course.category}.",
            "points": 10,
            "order_index": 1
        })
        
        # True/False question
        questions.append({
            "question_text": f"Dieser Kurs ist für {course.difficulty_level}-Level Lernende geeignet.",
            "question_type": "true_false",
            "correct_answer": "true",
            "explanation": f"Ja, dieser Kurs wurde speziell für das {course.difficulty_level}-Level entwickelt.",
            "points": 5,
            "order_index": 2
        })
        
        # Additional specific questions based on course category
        if "phishing" in course.tags:
            questions.append({
                "question_text": "Welches ist KEIN typisches Merkmal einer Phishing-E-Mail?",
                "question_type": "multiple_choice",
                "options": {
                    "a": "Dringlichkeit und Zeitdruck",
                    "b": "Rechtschreibfehler",
                    "c": "Digitale Signatur des Absenders",
                    "d": "Generische Anrede"
                },
                "correct_answer": "c",
                "explanation": "Eine gültige digitale Signatur ist ein Zeichen für Authentizität, kein Phishing-Merkmal.",
                "points": 15,
                "order_index": 3
            })
        
        if "passwort" in course.tags:
            questions.append({
                "question_text": "Wie lang sollte ein sicheres Passwort mindestens sein?",
                "question_type": "multiple_choice",
                "options": {
                    "a": "6 Zeichen",
                    "b": "8 Zeichen",
                    "c": "12 Zeichen",
                    "d": "20 Zeichen"
                },
                "correct_answer": "c",
                "explanation": "Experten empfehlen mindestens 12 Zeichen für ein sicheres Passwort.",
                "points": 10,
                "order_index": 3
            })
        
        for q_data in questions:
            question = QuizQuestion(quiz_id=quiz.id, **q_data)
            session.add(question)
    
    await session.flush()
    return courses


async def create_phishing_templates(session: AsyncSession, companies: List[Company]) -> List[PhishingTemplate]:
    """Create realistic German phishing templates."""
    templates = []
    
    # Public templates (available to all companies)
    public_templates = [
        {
            "name": "IT-Support Passwort-Reset",
            "category": "IT Support",
            "difficulty": "easy",
            "subject": "Dringend: Passwort-Reset erforderlich",
            "sender_name": "IT-Support Team",
            "sender_email": "it-support@firma-intern.de",
            "html_content": """
                <p>Sehr geehrter Mitarbeiter,</p>
                <p>wir haben ungewöhnliche Aktivitäten in Ihrem Konto festgestellt. Bitte setzen Sie Ihr Passwort umgehend zurück.</p>
                <p><a href="{tracking_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Passwort jetzt zurücksetzen</a></p>
                <p>Mit freundlichen Grüßen,<br>Ihr IT-Support Team</p>
                <hr>
                <p style="font-size: 12px; color: #666;">Diese E-Mail wurde automatisch generiert. Bitte antworten Sie nicht darauf.</p>
            """,
            "text_content": "Passwort-Reset erforderlich. Bitte klicken Sie auf den Link.",
            "landing_page_html": """
                <div style="max-width: 600px; margin: 50px auto; padding: 20px; border: 2px solid #f44336; background-color: #ffebee;">
                    <h1 style="color: #f44336;">⚠️ Dies war eine Phishing-Simulation!</h1>
                    <p>Sie haben gerade auf einen simulierten Phishing-Link geklickt.</p>
                    <h2>Was Sie daraus lernen sollten:</h2>
                    <ul>
                        <li>Überprüfen Sie immer die Absender-E-Mail-Adresse genau</li>
                        <li>IT-Support fordert niemals per E-Mail zur Passwort-Eingabe auf</li>
                        <li>Bei Zweifeln kontaktieren Sie die IT-Abteilung direkt</li>
                    </ul>
                    <p><strong>Nächste Schritte:</strong> Absolvieren Sie den Kurs "Phishing-E-Mails erkennen" für mehr Informationen.</p>
                </div>
            """,
            "language": "de",
            "is_public": True
        },
        {
            "name": "CEO Dringende Bitte",
            "category": "CEO Betrug",
            "difficulty": "medium",
            "subject": "Dringend - Brauche Ihre Hilfe",
            "sender_name": "Dr. Schmidt (Geschäftsführer)",
            "sender_email": "geschaeftsfuehrung@firna.de",  # Note the typo
            "html_content": """
                <p>Hallo,</p>
                <p>ich bin gerade in einer wichtigen Besprechung und kann nicht telefonieren.</p>
                <p>Ich brauche Sie für eine dringende Angelegenheit. Bitte besorgen Sie Amazon-Gutscheine im Wert von 500€ für ein Kundengeschenk.</p>
                <p>Senden Sie mir die Codes so schnell wie möglich per E-Mail.</p>
                <p>Danke,<br>Dr. Schmidt</p>
            """,
            "text_content": "Dringende Bitte um Amazon-Gutscheine vom CEO.",
            "landing_page_html": """
                <div style="max-width: 600px; margin: 50px auto; padding: 20px; border: 2px solid #ff9800; background-color: #fff3e0;">
                    <h1 style="color: #ff9800;">⚠️ CEO-Betrugsversuch erkannt!</h1>
                    <p>Dies war eine Simulation eines CEO-Betrugs (auch "Chef-Masche" genannt).</p>
                    <h2>Warnsignale:</h2>
                    <ul>
                        <li>Ungewöhnliche Anfragen (Gutscheine kaufen)</li>
                        <li>Zeitdruck und Geheimhaltung</li>
                        <li>Fehlerhafte E-Mail-Adresse (firna statt firma)</li>
                        <li>Umgehung normaler Prozesse</li>
                    </ul>
                    <p><strong>Merken Sie sich:</strong> Verifizieren Sie ungewöhnliche Anfragen immer über offizielle Kanäle!</p>
                </div>
            """,
            "language": "de",
            "is_public": True
        },
        {
            "name": "Paketlieferung Benachrichtigung",
            "category": "Lieferung",
            "difficulty": "easy",
            "subject": "Ihr Paket konnte nicht zugestellt werden - Handlung erforderlich",
            "sender_name": "DHL Zustellung",
            "sender_email": "noreply@dhl-pakete.info",
            "html_content": """
                <div style="font-family: Arial, sans-serif;">
                    <img src="https://www.dhl.de/content/dam/dhlde/images/header/dhl-logo.svg" alt="DHL" style="height: 40px;">
                    <p>Sehr geehrter Kunde,</p>
                    <p>Ihr Paket konnte aufgrund einer unvollständigen Adresse nicht zugestellt werden.</p>
                    <p><strong>Sendungsnummer:</strong> 1234567890123</p>
                    <p>Um eine erneute Zustellung zu veranlassen, bestätigen Sie bitte Ihre Adresse:</p>
                    <p><a href="{tracking_link}" style="background-color: #ffcc00; color: #d40511; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">Adresse bestätigen</a></p>
                    <p>Mit freundlichen Grüßen,<br>Ihr DHL Team</p>
                </div>
            """,
            "text_content": "Paket konnte nicht zugestellt werden. Adresse bestätigen.",
            "landing_page_html": """
                <div style="max-width: 600px; margin: 50px auto; padding: 20px; border: 2px solid #f44336; background-color: #ffebee;">
                    <h1 style="color: #f44336;">🚨 Phishing-Simulation!</h1>
                    <p>Sie wurden fast Opfer eines Paketdienst-Phishing-Angriffs.</p>
                    <h2>So erkennen Sie echte DHL-E-Mails:</h2>
                    <ul>
                        <li>Offizielle DHL-E-Mails kommen von @dhl.de</li>
                        <li>DHL fragt nie nach persönlichen Daten per E-Mail</li>
                        <li>Überprüfen Sie Sendungsnummern immer auf dhl.de</li>
                    </ul>
                </div>
            """,
            "language": "de",
            "is_public": True
        },
        {
            "name": "Microsoft Teams Update",
            "category": "Software Update",
            "difficulty": "medium",
            "subject": "Wichtiges Microsoft Teams Sicherheitsupdate",
            "sender_name": "Microsoft Teams",
            "sender_email": "teams@microsoft-update.net",
            "html_content": """
                <div style="font-family: 'Segoe UI', Arial, sans-serif;">
                    <div style="background-color: #5558AF; color: white; padding: 20px;">
                        <h2>Microsoft Teams</h2>
                    </div>
                    <div style="padding: 20px;">
                        <p>Sehr geehrter Teams-Nutzer,</p>
                        <p>Ein kritisches Sicherheitsupdate für Microsoft Teams ist verfügbar. Installieren Sie es umgehend, um Ihre Daten zu schützen.</p>
                        <p><a href="{tracking_link}" style="background-color: #5558AF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Update jetzt installieren</a></p>
                        <p>Dieses Update behebt mehrere Sicherheitslücken und verbessert die Performance.</p>
                        <p>Mit freundlichen Grüßen,<br>Das Microsoft Teams Team</p>
                    </div>
                </div>
            """,
            "text_content": "Kritisches Teams Sicherheitsupdate verfügbar.",
            "landing_page_html": """
                <div style="max-width: 600px; margin: 50px auto; padding: 20px; border: 2px solid #2196F3; background-color: #e3f2fd;">
                    <h1 style="color: #2196F3;">💡 Lernmoment: Software-Update-Phishing</h1>
                    <p>Dies war eine Simulation eines gefälschten Software-Updates.</p>
                    <h2>Wichtige Sicherheitsregeln:</h2>
                    <ul>
                        <li>Software-Updates kommen über die Software selbst, nicht per E-Mail</li>
                        <li>Microsoft sendet Updates nie von Domains wie "microsoft-update.net"</li>
                        <li>Lassen Sie Updates von Ihrer IT-Abteilung verwalten</li>
                    </ul>
                </div>
            """,
            "language": "de",
            "is_public": True
        },
        {
            "name": "Gehaltsabrechnung Fehler",
            "category": "HR/Payroll",
            "difficulty": "hard",
            "subject": "Korrektur Ihrer Gehaltsabrechnung - Rückzahlung erforderlich",
            "sender_name": "Personalabteilung",
            "sender_email": "personal@ihrefirma.de",
            "html_content": """
                <div style="font-family: Arial, sans-serif;">
                    <p>Sehr geehrte/r Mitarbeiter/in,</p>
                    <p>bei der Überprüfung der Gehaltsabrechnungen wurde festgestellt, dass Ihnen in den letzten 3 Monaten versehentlich zu viel Gehalt ausgezahlt wurde.</p>
                    <p><strong>Überzahlter Betrag:</strong> 1.247,53 €</p>
                    <p>Gemäß Arbeitsvertrag sind Sie zur Rückzahlung verpflichtet. Um Unannehmlichkeiten zu vermeiden, bieten wir Ihnen eine Ratenzahlung an.</p>
                    <p>Bitte bestätigen Sie die Rückzahlungsvereinbarung bis spätestens morgen:</p>
                    <p><a href="{tracking_link}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Rückzahlungsvereinbarung prüfen</a></p>
                    <p>Bei Fragen wenden Sie sich an: personal@ihrefirma.de</p>
                    <p>Mit freundlichen Grüßen,<br>Ihre Personalabteilung</p>
                </div>
            """,
            "text_content": "Gehaltsüberzahlung - Rückzahlung erforderlich.",
            "landing_page_html": """
                <div style="max-width: 600px; margin: 50px auto; padding: 20px; border: 3px solid #dc3545; background-color: #f8d7da;">
                    <h1 style="color: #dc3545;">🎯 Fortgeschrittener Phishing-Angriff!</h1>
                    <p>Dies war eine besonders raffinierte Phishing-Simulation.</p>
                    <h2>Was machte diesen Angriff gefährlich?</h2>
                    <ul>
                        <li>Verwendung interner Begriffe und Prozesse</li>
                        <li>Emotionaler Druck (Angst vor Konsequenzen)</li>
                        <li>Zeitdruck ("bis morgen")</li>
                        <li>Scheinbar legitime Firmen-Domain</li>
                    </ul>
                    <p><strong>Goldene Regel:</strong> Die Personalabteilung klärt Gehaltsangelegenheiten NIEMALS per E-Mail mit Links!</p>
                </div>
            """,
            "language": "de",
            "is_public": True
        }
    ]
    
    for template_data in public_templates:
        template = PhishingTemplate(**template_data)
        session.add(template)
        templates.append(template)
    
    # Create company-specific templates
    for company in companies[:2]:  # First two companies get custom templates
        custom_template = PhishingTemplate(
            name=f"{company.name} Interne Umfrage",
            category="Interne Kommunikation",
            difficulty="medium",
            subject=f"Ihre Meinung ist gefragt - {company.name} Mitarbeiterumfrage",
            sender_name="HR Team",
            sender_email=f"umfrage@{company.domain}",
            html_content=f"""
                <p>Liebe Kolleginnen und Kollegen,</p>
                <p>im Rahmen unserer jährlichen Mitarbeiterbefragung möchten wir Ihre Meinung zu verschiedenen Themen einholen.</p>
                <p>Die Umfrage dauert nur 5 Minuten und ist vollständig anonym.</p>
                <p><a href="{{tracking_link}}">Zur Umfrage</a></p>
                <p>Vielen Dank für Ihre Teilnahme!<br>Ihr {company.name} HR Team</p>
            """,
            landing_page_html=f"""
                <h1>Phishing-Warnung!</h1>
                <p>Dies war ein Test. Echte Mitarbeiterumfragen werden über das Intranet angekündigt.</p>
            """,
            language="de",
            is_public=False,
            company_id=company.id
        )
        session.add(custom_template)
        templates.append(custom_template)
    
    await session.flush()
    return templates


async def create_phishing_campaigns(
    session: AsyncSession, 
    companies: List[Company], 
    templates: List[PhishingTemplate],
    users: List[User]
) -> List[PhishingCampaign]:
    """Create phishing campaigns with results."""
    campaigns = []
    
    for company in companies[:4]:  # First 4 companies have campaigns
        # Get company admin
        admin = next((u for u in users if u.company_id == company.id and u.role == UserRole.COMPANY_ADMIN), None)
        if not admin:
            continue
        
        # Past campaign (completed)
        past_template = random.choice([t for t in templates if t.is_public])
        past_campaign = PhishingCampaign(
            company_id=company.id,
            created_by_id=admin.id,
            name=f"{past_template.category} Test - Q3 2024",
            description=f"Quarterly phishing awareness test using {past_template.name} template",
            status="completed",
            template_id=past_template.id,
            target_groups={"departments": ["all"]},
            scheduled_at=datetime.utcnow() - timedelta(days=30),
            started_at=datetime.utcnow() - timedelta(days=30),
            completed_at=datetime.utcnow() - timedelta(days=28),
            settings={
                "track_clicks": True,
                "track_submissions": True,
                "redirect_url": "/phishing-awareness"
            }
        )
        session.add(past_campaign)
        await session.flush()
        campaigns.append(past_campaign)
        
        # Create results for past campaign
        company_users = [u for u in users if u.company_id == company.id and u.role == UserRole.EMPLOYEE]
        for user in random.sample(company_users, min(len(company_users), 20)):
            # Simulate realistic click rates (30% click rate)
            clicked = random.random() < 0.3
            reported = random.random() < 0.1 if not clicked else False
            
            result = PhishingResult(
                campaign_id=past_campaign.id,
                user_id=user.id,
                email_sent_at=past_campaign.started_at,
                email_opened_at=past_campaign.started_at + timedelta(hours=random.randint(1, 24)) if random.random() < 0.7 else None,
                link_clicked_at=past_campaign.started_at + timedelta(hours=random.randint(1, 48)) if clicked else None,
                reported_at=past_campaign.started_at + timedelta(hours=random.randint(1, 12)) if reported else None,
                ip_address=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            session.add(result)
        
        # Current campaign (running)
        current_template = random.choice([t for t in templates if t.is_public and t.id != past_template.id])
        current_campaign = PhishingCampaign(
            company_id=company.id,
            created_by_id=admin.id,
            name=f"{current_template.category} Test - Q4 2024",
            description=f"Current quarterly test with {current_template.name}",
            status="running",
            template_id=current_template.id,
            target_groups={"departments": random.sample(DEPARTMENTS, 3)},
            scheduled_at=datetime.utcnow() - timedelta(days=2),
            started_at=datetime.utcnow() - timedelta(days=2),
            settings={
                "track_clicks": True,
                "track_submissions": True,
                "send_training": True
            }
        )
        session.add(current_campaign)
        campaigns.append(current_campaign)
    
    await session.flush()
    return campaigns


async def create_user_progress(
    session: AsyncSession, 
    users: List[User], 
    courses: List[Course],
    companies: List[Company]
):
    """Create realistic user course progress."""
    # Get all non-admin users
    learners = [u for u in users if u.role in [UserRole.EMPLOYEE, UserRole.MANAGER] and u.is_active]
    
    for user in learners:
        # Each user completes different number of courses based on their join date
        if user.email_verified_at:
            days_since_joined = (datetime.utcnow() - user.email_verified_at).days
            if days_since_joined > 180:
                courses_to_take = courses[:6]  # Experienced users
            elif days_since_joined > 60:
                courses_to_take = courses[:4]  # Medium tenure
            else:
                courses_to_take = courses[:2]  # New users
        else:
            courses_to_take = []
        
        for course in courses_to_take:
            # Determine progress based on course difficulty and user engagement
            if course.difficulty_level == "beginner":
                progress_chance = 0.8
            elif course.difficulty_level == "intermediate":
                progress_chance = 0.6
            else:  # advanced
                progress_chance = 0.4
            
            if random.random() < progress_chance:
                progress = random.choices(
                    [100, random.randint(50, 99), random.randint(10, 49)],
                    weights=[0.6, 0.3, 0.1]
                )[0]
                
                status = "completed" if progress == 100 else "in_progress"
                started_at = datetime.utcnow() - timedelta(days=random.randint(1, 60))
                
                user_progress = UserCourseProgress(
                    user_id=user.id,
                    course_id=course.id,
                    company_id=user.company_id,
                    status=status,
                    progress_percentage=progress,
                    started_at=started_at,
                    completed_at=started_at + timedelta(days=random.randint(1, 7)) if progress == 100 else None,
                    certificate_issued=progress == 100 and random.random() > 0.1,  # 90% get certificates
                    certificate_url=f"https://certs.bootstrap-awareness.de/{user.id}/{course.id}" if progress == 100 else None
                )
                session.add(user_progress)
    
    await session.flush()


async def create_audit_logs(
    session: AsyncSession,
    users: List[User],
    companies: List[Company]
):
    """Create sample audit logs."""
    actions = [
        ("login", "user", "User login"),
        ("logout", "user", "User logout"),
        ("create", "phishing_campaign", "Created phishing campaign"),
        ("update", "user", "Updated user profile"),
        ("update", "company", "Updated company settings"),
        ("complete", "course", "Completed course"),
        ("view", "analytics", "Viewed analytics dashboard"),
        ("export", "report", "Exported compliance report")
    ]
    
    for _ in range(100):  # Create 100 audit logs
        user = random.choice([u for u in users if u.is_active])
        action, resource_type, description = random.choice(actions)
        
        audit_log = AuditLog(
            user_id=user.id,
            company_id=user.company_id,
            action=action,
            resource_type=resource_type,
            resource_id=random.randint(1, 100),
            changes={"description": description, "timestamp": datetime.utcnow().isoformat()},
            ip_address=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        )
        session.add(audit_log)
    
    await session.flush()


async def seed_database():
    """Main function to seed the database with comprehensive data."""
    async with async_session_maker() as session:
        try:
            # Check if data already exists
            result = await session.execute(select(Company).limit(1))
            if result.scalar_one_or_none():
                print("Database already contains data. Skipping seed.")
                return
            
            print("🚀 Starting comprehensive database seeding...")
            
            # Create all data
            print("📦 Creating companies...")
            companies = await create_companies(session)
            print(f"✅ Created {len(companies)} companies")
            
            print("👥 Creating users...")
            users = await create_users(session, companies)
            print(f"✅ Created {len(users)} users")
            
            print("📚 Creating courses...")
            courses = await create_comprehensive_courses(session)
            print(f"✅ Created {len(courses)} courses with quizzes")
            
            print("🎣 Creating phishing templates...")
            templates = await create_phishing_templates(session, companies)
            print(f"✅ Created {len(templates)} phishing templates")
            
            print("📧 Creating phishing campaigns...")
            campaigns = await create_phishing_campaigns(session, companies, templates, users)
            print(f"✅ Created {len(campaigns)} phishing campaigns")
            
            print("📊 Creating user progress...")
            await create_user_progress(session, users, courses, companies)
            print("✅ Created user progress records")
            
            print("📝 Creating audit logs...")
            await create_audit_logs(session, users, companies)
            print("✅ Created audit logs")
            
            # Commit all changes
            await session.commit()
            print("\n✨ Database seeding completed successfully!")
            
            # Print sample login credentials
            print("\n" + "="*60)
            print("📋 SAMPLE LOGIN CREDENTIALS")
            print("="*60)
            print("\n🔐 System Admin:")
            print("   Email: admin@bootstrap-awareness.de")
            print("   Password: SecureAdmin123!")
            
            print("\n🏢 Company Admins:")
            for company in companies[:3]:
                print(f"\n   {company.name}:")
                print(f"   Email: admin@{company.domain}")
                print(f"   Password: CompanyAdmin123!")
            
            print("\n👤 Sample Employee (TechVision GmbH):")
            employee = next((u for u in users if u.company_id == companies[0].id and u.role == UserRole.EMPLOYEE), None)
            if employee:
                print(f"   Name: {employee.full_name}")
                print(f"   Email: {employee.email}")
                print(f"   Password: Employee123!")
            
            print("\n📊 Summary Statistics:")
            print(f"   Total Users: {len(users)}")
            print(f"   Total Companies: {len(companies)}")
            print(f"   Total Courses: {len(courses)}")
            print(f"   Total Phishing Templates: {len(templates)}")
            print(f"   Total Phishing Campaigns: {len(campaigns)}")
            print("="*60)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())