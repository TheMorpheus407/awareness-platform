"""Enhanced security headers middleware with comprehensive CSP implementation."""

from typing import Dict, List, Optional, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.config import settings
from core.logging import logger


class SecurityHeadersPolicy:
    """Security headers policy configuration."""
    
    def __init__(self):
        """Initialize security headers policy."""
        self.csp_directives = self._get_csp_directives()
        self.permissions_policy = self._get_permissions_policy()
        self.feature_policy = self._get_feature_policy()
        
    def _get_csp_directives(self) -> Dict[str, List[str]]:
        """Get Content Security Policy directives."""
        # Base CSP directives
        directives = {
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'"],
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
            "media-src": ["'self'"],
            "object-src": ["'none'"],
            "child-src": ["'self'"],
            "frame-src": ["'none'"],
            "worker-src": ["'self'"],
            "frame-ancestors": ["'none'"],
            "form-action": ["'self'"],
            "base-uri": ["'self'"],
            "manifest-src": ["'self'"],
            "prefetch-src": ["'self'"],
            "script-src-elem": ["'self'"],
            "style-src-elem": ["'self'"],
            "script-src-attr": ["'none'"],
            "style-src-attr": ["'none'"],
            "upgrade-insecure-requests": []
        }
        
        # Environment-specific adjustments
        if settings.DEBUG:
            # Allow inline scripts and styles for development tools
            directives["script-src"].extend(["'unsafe-inline'", "'unsafe-eval'"])
            directives["style-src"].append("'unsafe-inline'")
            directives["connect-src"].extend(["ws:", "wss:"])
        
        # Add trusted external sources
        if hasattr(settings, 'CSP_TRUSTED_HOSTS'):
            for host in settings.CSP_TRUSTED_HOSTS:
                directives["script-src"].append(host)
                directives["style-src"].append(host)
                directives["connect-src"].append(host)
        
        # Add Stripe sources if payment integration is enabled
        if hasattr(settings, 'STRIPE_PUBLIC_KEY') and settings.STRIPE_PUBLIC_KEY:
            directives["script-src"].append("https://js.stripe.com")
            directives["frame-src"].extend(["https://js.stripe.com", "https://hooks.stripe.com"])
            directives["connect-src"].append("https://api.stripe.com")
        
        # Add font sources
        directives["font-src"].extend([
            "https://fonts.gstatic.com",
            "https://fonts.googleapis.com"
        ])
        directives["style-src"].append("https://fonts.googleapis.com")
        
        return directives
    
    def _get_permissions_policy(self) -> Dict[str, str]:
        """Get Permissions Policy directives."""
        return {
            "accelerometer": "()",
            "ambient-light-sensor": "()",
            "autoplay": "(self)",
            "battery": "()",
            "camera": "()",
            "cross-origin-isolated": "()",
            "display-capture": "()",
            "document-domain": "()",
            "encrypted-media": "(self)",
            "execution-while-not-rendered": "()",
            "execution-while-out-of-viewport": "()",
            "fullscreen": "(self)",
            "geolocation": "()",
            "gyroscope": "()",
            "keyboard-map": "()",
            "magnetometer": "()",
            "microphone": "()",
            "midi": "()",
            "navigation-override": "()",
            "payment": "(self)",
            "picture-in-picture": "()",
            "publickey-credentials-get": "()",
            "screen-wake-lock": "()",
            "sync-xhr": "()",
            "usb": "()",
            "web-share": "()",
            "xr-spatial-tracking": "()"
        }
    
    def _get_feature_policy(self) -> Dict[str, str]:
        """Get Feature Policy directives (legacy support)."""
        return {
            "accelerometer": "'none'",
            "camera": "'none'",
            "geolocation": "'none'",
            "gyroscope": "'none'",
            "magnetometer": "'none'",
            "microphone": "'none'",
            "payment": "'self'",
            "usb": "'none'"
        }
    
    def build_csp_header(self) -> str:
        """Build the Content Security Policy header value."""
        policy_parts = []
        for directive, sources in self.csp_directives.items():
            if sources:
                policy_parts.append(f"{directive} {' '.join(sources)}")
            else:
                policy_parts.append(directive)
        return "; ".join(policy_parts)
    
    def build_permissions_policy_header(self) -> str:
        """Build the Permissions Policy header value."""
        policy_parts = []
        for feature, allowlist in self.permissions_policy.items():
            policy_parts.append(f"{feature}={allowlist}")
        return ", ".join(policy_parts)
    
    def build_feature_policy_header(self) -> str:
        """Build the Feature Policy header value (legacy)."""
        policy_parts = []
        for feature, allowlist in self.feature_policy.items():
            policy_parts.append(f"{feature} {allowlist}")
        return "; ".join(policy_parts)


class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers middleware with comprehensive protection."""
    
    def __init__(self, app, report_only: bool = False, nonce_enabled: bool = True):
        """Initialize the middleware."""
        super().__init__(app)
        self.policy = SecurityHeadersPolicy()
        self.report_only = report_only
        self.nonce_enabled = nonce_enabled
        self.csp_header_name = "Content-Security-Policy-Report-Only" if report_only else "Content-Security-Policy"
    
    async def dispatch(self, request: Request, call_next):
        """Add comprehensive security headers to the response."""
        # Generate CSP nonce if enabled
        if self.nonce_enabled and settings.DEBUG:
            import secrets
            nonce = secrets.token_urlsafe(16)
            request.state.csp_nonce = nonce
            
            # Add nonce to script-src
            csp_header = self.policy.build_csp_header()
            csp_header = csp_header.replace("'self'", f"'self' 'nonce-{nonce}'", 1)
        else:
            csp_header = self.policy.build_csp_header()
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        response.headers[self.csp_header_name] = csp_header
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = self.policy.build_permissions_policy_header()
        response.headers["Feature-Policy"] = self.policy.build_feature_policy_header()
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-DNS-Prefetch-Control"] = "off"
        response.headers["X-Download-Options"] = "noopen"
        
        # Add HSTS in production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        # Add CSP report URI if configured
        if hasattr(settings, 'CSP_REPORT_URI') and settings.CSP_REPORT_URI:
            current_csp = response.headers[self.csp_header_name]
            response.headers[self.csp_header_name] = f"{current_csp}; report-uri {settings.CSP_REPORT_URI}"
        
        # Add security headers for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Log CSP violations if in debug mode
        if settings.DEBUG and self.report_only:
            logger.debug(f"CSP Header: {response.headers[self.csp_header_name]}")
        
        return response


class SecurityHeadersReportEndpoint:
    """Endpoint for receiving CSP violation reports."""
    
    @staticmethod
    async def handle_csp_report(request: Request) -> Dict:
        """Handle CSP violation reports."""
        try:
            report = await request.json()
            violation = report.get("csp-report", {})
            
            logger.warning(
                "CSP Violation Report",
                extra={
                    "document_uri": violation.get("document-uri"),
                    "violated_directive": violation.get("violated-directive"),
                    "effective_directive": violation.get("effective-directive"),
                    "original_policy": violation.get("original-policy"),
                    "blocked_uri": violation.get("blocked-uri"),
                    "status_code": violation.get("status-code"),
                    "referrer": violation.get("referrer"),
                    "source_file": violation.get("source-file"),
                    "line_number": violation.get("line-number"),
                    "column_number": violation.get("column-number")
                }
            )
            
            return {"status": "reported"}
        except Exception as e:
            logger.error(f"Error processing CSP report: {e}")
            return {"status": "error"}