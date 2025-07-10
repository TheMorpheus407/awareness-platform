"""Backend internationalization support."""

from typing import Dict, Optional
from functools import lru_cache
import json
import os
from pathlib import Path
from fastapi import Request


class I18nBackend:
    """Backend internationalization handler."""
    
    def __init__(self):
        self.translations: Dict[str, Dict[str, str]] = {}
        self.default_locale = "en"
        self.supported_locales = ["en", "de"]
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files for backend messages."""
        translations_dir = Path(__file__).parent.parent / "translations"
        
        # Create translations directory if it doesn't exist
        translations_dir.mkdir(exist_ok=True)
        
        # Default English translations for API messages
        self.translations["en"] = {
            # Auth messages
            "auth.invalid_credentials": "Incorrect username or password",
            "auth.email_registered": "Email already registered",
            "auth.logout_success": "Successfully logged out",
            "auth.password_reset_sent": "If the email exists, a password reset link has been sent",
            "auth.password_reset_success": "Password reset successfully",
            "auth.invalid_reset_token": "Invalid reset token",
            "auth.token_expired": "Reset token has expired",
            "auth.password_too_short": "Password must be at least 12 characters long",
            "auth.password_complexity": "Password must contain uppercase, lowercase, number, and special character",
            "auth.account_locked": "Account is locked due to too many failed attempts",
            "auth.2fa_required": "Two-factor authentication required",
            "auth.invalid_2fa_code": "Invalid two-factor authentication code",
            
            # User messages
            "user.not_found": "User not found",
            "user.updated": "User updated successfully",
            "user.deleted": "User deleted successfully",
            "user.unauthorized": "Unauthorized access",
            
            # Company messages
            "company.not_found": "Company not found",
            "company.created": "Company created successfully",
            "company.updated": "Company updated successfully",
            
            # Course messages
            "course.not_found": "Course not found",
            "course.enrolled": "Successfully enrolled in course",
            "course.completed": "Course completed successfully",
            
            # Phishing messages
            "phishing.campaign_started": "Phishing campaign started",
            "phishing.template_created": "Phishing template created",
            
            # General messages
            "general.success": "Operation completed successfully",
            "general.error": "An error occurred",
            "general.not_found": "Resource not found",
            "general.unauthorized": "Unauthorized",
            "general.forbidden": "Forbidden",
            "general.bad_request": "Bad request",
        }
        
        # German translations
        self.translations["de"] = {
            # Auth messages
            "auth.invalid_credentials": "Ungültiger Benutzername oder Passwort",
            "auth.email_registered": "E-Mail bereits registriert",
            "auth.logout_success": "Erfolgreich abgemeldet",
            "auth.password_reset_sent": "Falls die E-Mail existiert, wurde ein Link zum Zurücksetzen des Passworts gesendet",
            "auth.password_reset_success": "Passwort erfolgreich zurückgesetzt",
            "auth.invalid_reset_token": "Ungültiger Zurücksetzungs-Token",
            "auth.token_expired": "Zurücksetzungs-Token ist abgelaufen",
            "auth.password_too_short": "Das Passwort muss mindestens 12 Zeichen lang sein",
            "auth.password_complexity": "Das Passwort muss Groß- und Kleinbuchstaben, Zahlen und Sonderzeichen enthalten",
            "auth.account_locked": "Konto ist aufgrund zu vieler fehlgeschlagener Versuche gesperrt",
            "auth.2fa_required": "Zwei-Faktor-Authentifizierung erforderlich",
            "auth.invalid_2fa_code": "Ungültiger Zwei-Faktor-Authentifizierungscode",
            
            # User messages
            "user.not_found": "Benutzer nicht gefunden",
            "user.updated": "Benutzer erfolgreich aktualisiert",
            "user.deleted": "Benutzer erfolgreich gelöscht",
            "user.unauthorized": "Unbefugter Zugriff",
            
            # Company messages
            "company.not_found": "Unternehmen nicht gefunden",
            "company.created": "Unternehmen erfolgreich erstellt",
            "company.updated": "Unternehmen erfolgreich aktualisiert",
            
            # Course messages
            "course.not_found": "Kurs nicht gefunden",
            "course.enrolled": "Erfolgreich für Kurs eingeschrieben",
            "course.completed": "Kurs erfolgreich abgeschlossen",
            
            # Phishing messages
            "phishing.campaign_started": "Phishing-Kampagne gestartet",
            "phishing.template_created": "Phishing-Vorlage erstellt",
            
            # General messages
            "general.success": "Vorgang erfolgreich abgeschlossen",
            "general.error": "Ein Fehler ist aufgetreten",
            "general.not_found": "Ressource nicht gefunden",
            "general.unauthorized": "Nicht autorisiert",
            "general.forbidden": "Verboten",
            "general.bad_request": "Ungültige Anfrage",
        }
    
    def get_locale_from_request(self, request: Request) -> str:
        """Extract locale from request headers."""
        # Check Accept-Language header
        accept_language = request.headers.get("Accept-Language", "")
        
        # Simple parsing - take first language
        if accept_language:
            # Format: "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
            first_lang = accept_language.split(",")[0].split("-")[0].lower()
            if first_lang in self.supported_locales:
                return first_lang
        
        # Check custom header
        custom_locale = request.headers.get("X-Language", "")
        if custom_locale in self.supported_locales:
            return custom_locale
        
        return self.default_locale
    
    def translate(self, key: str, locale: str = None, **kwargs) -> str:
        """Translate a message key to the specified locale."""
        if locale is None:
            locale = self.default_locale
        
        # Get translation
        message = self.translations.get(locale, {}).get(key)
        
        # Fallback to English if not found
        if message is None:
            message = self.translations.get("en", {}).get(key)
        
        # Fallback to key if still not found
        if message is None:
            return key
        
        # Format with kwargs if provided
        if kwargs:
            try:
                return message.format(**kwargs)
            except KeyError:
                return message
        
        return message
    
    def t(self, request: Request, key: str, **kwargs) -> str:
        """Translate with request context."""
        locale = self.get_locale_from_request(request)
        return self.translate(key, locale, **kwargs)


# Global instance
i18n = I18nBackend()


# Helper function for routes
def get_message(request: Request, key: str, **kwargs) -> str:
    """Get translated message for API response."""
    return i18n.t(request, key, **kwargs)