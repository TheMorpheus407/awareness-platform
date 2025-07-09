"""Default phishing email templates."""

from backend.schemas.phishing import TemplateCategory, TemplateDifficulty

PHISHING_TEMPLATES = [
    {
        "name": "IT Support Password Reset",
        "category": TemplateCategory.CREDENTIAL_HARVESTING,
        "difficulty": TemplateDifficulty.EASY,
        "subject": "Urgent: Password Reset Required",
        "sender_name": "IT Support",
        "sender_email": "it-support@company-support.com",
        "html_content": """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #d32f2f;">Urgent Security Notice</h2>
                <p>Dear {{first_name}},</p>
                <p>Our security team has detected unusual activity on your account. For your protection, we require you to reset your password immediately.</p>
                <p style="background-color: #ffeb3b; padding: 10px; border-radius: 5px;">
                    <strong>Action Required:</strong> Your account will be locked in 24 hours if you don't reset your password.
                </p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://phishing-link.example.com/reset" style="background-color: #2196f3; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Reset Password Now</a>
                </p>
                <p>If you have any questions, please contact IT Support.</p>
                <p>Best regards,<br>IT Support Team</p>
            </div>
        </body>
        </html>
        """,
        "text_content": "Your account requires immediate password reset. Click the link to proceed.",
        "landing_page_html": """
        <html>
        <body>
            <h1>This was a phishing simulation!</h1>
            <p>You clicked on a simulated phishing email. In a real attack, your credentials could have been stolen.</p>
            <h2>Red flags in this email:</h2>
            <ul>
                <li>Urgent language creating pressure</li>
                <li>Generic greeting</li>
                <li>Suspicious sender domain</li>
                <li>Threat of account lockout</li>
            </ul>
            <p><a href="/training/phishing-awareness">Learn more about phishing</a></p>
        </body>
        </html>
        """,
        "language": "en"
    },
    {
        "name": "CEO Urgent Request",
        "category": TemplateCategory.BUSINESS_EMAIL_COMPROMISE,
        "difficulty": TemplateDifficulty.MEDIUM,
        "subject": "Urgent - Need your help",
        "sender_name": "John Smith (CEO)",
        "sender_email": "ceo@companyname-mail.com",
        "html_content": """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p>Hi {{first_name}},</p>
                <p>I'm in a meeting right now and need your urgent assistance. Can you process a wire transfer for me?</p>
                <p>I need you to transfer €25,000 to our new vendor for the project we discussed. This is time-sensitive.</p>
                <p>Here are the details:<br>
                Bank: International Business Bank<br>
                IBAN: DE89 3704 0044 0532 0130 00<br>
                Reference: Project Alpha Payment</p>
                <p>Please confirm once done. Don't call me as I'm in a confidential meeting.</p>
                <p>Thanks,<br>John</p>
                <p style="font-size: 12px; color: #666;">Sent from my iPhone</p>
            </div>
        </body>
        </html>
        """,
        "text_content": "Urgent wire transfer request from CEO. Please process immediately.",
        "language": "en"
    },
    {
        "name": "Package Delivery Notification",
        "category": TemplateCategory.PACKAGE_DELIVERY,
        "difficulty": TemplateDifficulty.EASY,
        "subject": "Your package could not be delivered",
        "sender_name": "DHL Express",
        "sender_email": "noreply@dhl-delivery.net",
        "html_content": """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #ffcc00; padding: 10px; text-align: center;">
                    <h2 style="color: #d40511;">DHL Express</h2>
                </div>
                <p>Dear Customer,</p>
                <p>We attempted to deliver your package today but were unable to complete the delivery.</p>
                <p><strong>Tracking Number:</strong> 1234567890</p>
                <p>To reschedule delivery or provide additional delivery instructions, please click the link below:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://phishing-link.example.com/track" style="background-color: #d40511; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Track Package</a>
                </p>
                <p>Your package will be returned to sender if not collected within 5 business days.</p>
                <p>DHL Customer Service</p>
            </div>
        </body>
        </html>
        """,
        "text_content": "DHL delivery failed. Click to reschedule.",
        "language": "en"
    },
    {
        "name": "LinkedIn Connection Request",
        "category": TemplateCategory.SOCIAL_MEDIA,
        "difficulty": TemplateDifficulty.MEDIUM,
        "subject": "You have a new connection request on LinkedIn",
        "sender_name": "LinkedIn",
        "sender_email": "notifications@linkedin-alerts.com",
        "html_content": """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f3f2ef;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px;">
                <div style="background-color: #0077b5; padding: 20px; color: white;">
                    <h2>LinkedIn</h2>
                </div>
                <p>Hi {{first_name}},</p>
                <p>You have a new connection request from a Senior Recruiter at a Fortune 500 company.</p>
                <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0;">
                    <p><strong>Sarah Johnson</strong><br>
                    Senior Talent Acquisition Manager<br>
                    Tech Giants Inc.</p>
                    <p>"I came across your profile and was impressed by your experience. I'd like to discuss some exciting opportunities with you."</p>
                </div>
                <p style="text-align: center;">
                    <a href="https://phishing-link.example.com/linkedin" style="background-color: #0077b5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">View Profile</a>
                </p>
                <p style="font-size: 12px; color: #666;">This email was sent to {{email}}</p>
            </div>
        </body>
        </html>
        """,
        "text_content": "New LinkedIn connection request from recruiter.",
        "language": "en"
    },
    {
        "name": "Microsoft 365 Storage Full",
        "category": TemplateCategory.CREDENTIAL_HARVESTING,
        "difficulty": TemplateDifficulty.HARD,
        "subject": "Action Required: Your Microsoft 365 storage is almost full",
        "sender_name": "Microsoft 365",
        "sender_email": "noreply@microsoft365.com",
        "html_content": """
        <html>
        <body style="font-family: Segoe UI, Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="https://fake-microsoft-logo.com/logo.png" alt="Microsoft" style="height: 30px;">
                </div>
                <h2>Your storage is 95% full</h2>
                <p>Hi {{first_name}},</p>
                <p>Your Microsoft 365 account is running out of storage space. You're currently using 4.75 GB of your 5 GB quota.</p>
                <div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <div style="background-color: #0078d4; height: 20px; width: 95%; border-radius: 3px;"></div>
                    <p style="text-align: center; margin-top: 10px;">4.75 GB / 5 GB used</p>
                </div>
                <p>To continue receiving emails and using OneDrive, please:</p>
                <ul>
                    <li>Delete unnecessary files</li>
                    <li>Empty your deleted items folder</li>
                    <li>Or upgrade your storage plan</li>
                </ul>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://phishing-link.example.com/upgrade" style="background-color: #0078d4; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Manage Storage</a>
                </p>
                <p style="font-size: 12px; color: #666;">Microsoft Corporation<br>One Microsoft Way, Redmond, WA 98052</p>
            </div>
        </body>
        </html>
        """,
        "text_content": "Your Microsoft 365 storage is almost full. Manage your storage now.",
        "language": "en"
    },
    {
        "name": "IT-Support Passwort Zurücksetzen",
        "category": TemplateCategory.CREDENTIAL_HARVESTING,
        "difficulty": TemplateDifficulty.EASY,
        "subject": "Dringend: Passwort-Zurücksetzung erforderlich",
        "sender_name": "IT-Support",
        "sender_email": "it-support@firma-support.de",
        "html_content": """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #d32f2f;">Dringende Sicherheitswarnung</h2>
                <p>Sehr geehrte(r) {{first_name}},</p>
                <p>unser Sicherheitsteam hat ungewöhnliche Aktivitäten in Ihrem Konto festgestellt. Zu Ihrem Schutz müssen Sie Ihr Passwort sofort zurücksetzen.</p>
                <p style="background-color: #ffeb3b; padding: 10px; border-radius: 5px;">
                    <strong>Handlung erforderlich:</strong> Ihr Konto wird in 24 Stunden gesperrt, wenn Sie Ihr Passwort nicht zurücksetzen.
                </p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://phishing-link.example.com/reset" style="background-color: #2196f3; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Passwort jetzt zurücksetzen</a>
                </p>
                <p>Bei Fragen wenden Sie sich bitte an den IT-Support.</p>
                <p>Mit freundlichen Grüßen<br>IT-Support-Team</p>
            </div>
        </body>
        </html>
        """,
        "text_content": "Ihr Konto erfordert eine sofortige Passwort-Zurücksetzung.",
        "language": "de"
    },
    {
        "name": "Geschäftsführer Dringende Anfrage",
        "category": TemplateCategory.BUSINESS_EMAIL_COMPROMISE,
        "difficulty": TemplateDifficulty.MEDIUM,
        "subject": "Dringend - Brauche Ihre Hilfe",
        "sender_name": "Max Müller (Geschäftsführer)",
        "sender_email": "ceo@firmenname-mail.de",
        "html_content": """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p>Hallo {{first_name}},</p>
                <p>ich bin gerade in einer Besprechung und benötige dringend Ihre Hilfe. Können Sie eine Überweisung für mich durchführen?</p>
                <p>Ich brauche Sie, um 25.000 € an unseren neuen Lieferanten für das besprochene Projekt zu überweisen. Das ist zeitkritisch.</p>
                <p>Hier sind die Details:<br>
                Bank: Internationale Geschäftsbank<br>
                IBAN: DE89 3704 0044 0532 0130 00<br>
                Verwendungszweck: Projekt Alpha Zahlung</p>
                <p>Bitte bestätigen Sie, sobald erledigt. Rufen Sie mich nicht an, da ich in einer vertraulichen Sitzung bin.</p>
                <p>Danke,<br>Max</p>
                <p style="font-size: 12px; color: #666;">Von meinem iPhone gesendet</p>
            </div>
        </body>
        </html>
        """,
        "text_content": "Dringende Überweisungsanfrage vom Geschäftsführer.",
        "language": "de"
    }
]