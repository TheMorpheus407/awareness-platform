/**
 * Security utilities for frontend protection
 */

import DOMPurify from 'dompurify';

// XSS Protection
export const sanitizeHTML = (dirty: string): string => {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'i', 'b', 'ul', 'ol', 'li', 
                   'blockquote', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                   'a', 'img'],
    ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'id', 'target'],
    ALLOW_DATA_ATTR: false,
  });
};

// Input validation
export const validateInput = (input: string, type: 'email' | 'url' | 'alphanumeric' | 'numeric'): boolean => {
  const patterns = {
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    url: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
    alphanumeric: /^[a-zA-Z0-9]+$/,
    numeric: /^[0-9]+$/,
  };

  return patterns[type].test(input);
};

// Prevent clickjacking
export const preventClickjacking = () => {
  if (window.top !== window.self) {
    window.top?.location.replace(window.self.location.href);
  }
};

// Content Security Policy helper
export const setCSPMeta = () => {
  const meta = document.createElement('meta');
  meta.httpEquiv = 'Content-Security-Policy';
  meta.content = `
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    font-src 'self' https://fonts.gstatic.com;
    img-src 'self' data: https:;
    connect-src 'self' https://api.stripe.com wss: ws:;
    frame-src 'self' https://js.stripe.com https://hooks.stripe.com;
    object-src 'none';
    base-uri 'self';
    form-action 'self';
  `.replace(/\s+/g, ' ').trim();
  document.head.appendChild(meta);
};

// Secure storage wrapper with encryption
export class SecureStorage {
  private static encode(data: string): string {
    // Basic encoding - in production, use proper encryption
    return btoa(encodeURIComponent(data));
  }

  private static decode(data: string): string {
    try {
      return decodeURIComponent(atob(data));
    } catch {
      return '';
    }
  }

  static setItem(key: string, value: any): void {
    const data = JSON.stringify(value);
    const encoded = this.encode(data);
    localStorage.setItem(key, encoded);
  }

  static getItem(key: string): any {
    const encoded = localStorage.getItem(key);
    if (!encoded) return null;
    
    try {
      const decoded = this.decode(encoded);
      return JSON.parse(decoded);
    } catch {
      return null;
    }
  }

  static removeItem(key: string): void {
    localStorage.removeItem(key);
  }

  static clear(): void {
    localStorage.clear();
  }
}

// Rate limiting for client-side actions
export class RateLimiter {
  private attempts: Map<string, number[]> = new Map();

  constructor(
    private maxAttempts: number,
    private windowMs: number
  ) {}

  isAllowed(key: string): boolean {
    const now = Date.now();
    const attempts = this.attempts.get(key) || [];
    
    // Remove old attempts outside the window
    const validAttempts = attempts.filter(time => now - time < this.windowMs);
    
    if (validAttempts.length >= this.maxAttempts) {
      return false;
    }
    
    validAttempts.push(now);
    this.attempts.set(key, validAttempts);
    
    return true;
  }

  reset(key: string): void {
    this.attempts.delete(key);
  }
}

// CSRF token management
export class CSRFTokenManager {
  private static token: string | null = null;

  static setToken(token: string): void {
    this.token = token;
  }

  static getToken(): string | null {
    // First check memory
    if (this.token) return this.token;
    
    // Then check cookie
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(';');
    
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.indexOf(name) === 0) {
        const fullToken = cookie.substring(name.length);
        // Extract the actual token (before the signature)
        this.token = fullToken.split('.')[0];
        return this.token;
      }
    }
    
    return null;
  }

  static clearToken(): void {
    this.token = null;
  }
}

// Password strength checker
export const checkPasswordStrength = (password: string): {
  score: number;
  feedback: string[];
} => {
  let score = 0;
  const feedback: string[] = [];

  // Length check
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (password.length < 8) feedback.push('Password should be at least 8 characters long');

  // Character variety
  if (/[a-z]/.test(password)) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^a-zA-Z0-9]/.test(password)) score += 1;

  // Common patterns to avoid
  if (/(.)\1{2,}/.test(password)) {
    score -= 1;
    feedback.push('Avoid repeated characters');
  }
  
  if (/^[0-9]+$/.test(password)) {
    score -= 1;
    feedback.push('Avoid using only numbers');
  }
  
  if (/^[a-zA-Z]+$/.test(password)) {
    score -= 1;
    feedback.push('Include numbers or special characters');
  }

  // Common weak passwords
  const weakPasswords = ['password', '12345678', 'qwerty', 'admin', 'letmein'];
  if (weakPasswords.some(weak => password.toLowerCase().includes(weak))) {
    score = 0;
    feedback.push('This password is too common');
  }

  // Add recommendations based on score
  if (score < 3) feedback.push('Consider using a mix of uppercase, lowercase, numbers, and symbols');
  if (score < 4) feedback.push('Consider making your password longer');

  return {
    score: Math.max(0, Math.min(5, score)),
    feedback
  };
};

// Secure random string generator
export const generateSecureRandom = (length: number = 32): string => {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
};

// URL sanitization
export const sanitizeURL = (url: string): string => {
  try {
    const parsed = new URL(url);
    
    // Only allow http and https protocols
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return '';
    }
    
    // Remove any potential XSS in URL
    const sanitized = parsed.toString();
    if (sanitized.includes('javascript:') || sanitized.includes('data:')) {
      return '';
    }
    
    return sanitized;
  } catch {
    return '';
  }
};

// File upload validation
export const validateFileUpload = (file: File, options: {
  maxSize?: number; // in bytes
  allowedTypes?: string[];
  allowedExtensions?: string[];
}): { valid: boolean; error?: string } => {
  const { maxSize = 10 * 1024 * 1024, allowedTypes = [], allowedExtensions = [] } = options;

  // Check file size
  if (file.size > maxSize) {
    return { valid: false, error: `File size exceeds ${maxSize / 1024 / 1024}MB limit` };
  }

  // Check file type
  if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
    return { valid: false, error: 'File type not allowed' };
  }

  // Check file extension
  if (allowedExtensions.length > 0) {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !allowedExtensions.includes(extension)) {
      return { valid: false, error: 'File extension not allowed' };
    }
  }

  // Check for double extensions (potential attack)
  if (file.name.split('.').length > 2) {
    return { valid: false, error: 'Multiple file extensions not allowed' };
  }

  return { valid: true };
};

// Initialize security measures
export const initializeSecurity = () => {
  // Prevent clickjacking
  preventClickjacking();
  
  // Set CSP if not already set by server
  if (!document.querySelector('meta[http-equiv="Content-Security-Policy"]')) {
    setCSPMeta();
  }
  
  // Disable right-click in production (optional)
  if (process.env.NODE_ENV === 'production') {
    document.addEventListener('contextmenu', (e) => {
      if ((e.target as HTMLElement).tagName !== 'INPUT' && 
          (e.target as HTMLElement).tagName !== 'TEXTAREA') {
        e.preventDefault();
      }
    });
  }
  
  // Clear sensitive data on visibility change
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Clear any sensitive form data or temporary tokens
      CSRFTokenManager.clearToken();
    }
  });
};

export default {
  sanitizeHTML,
  validateInput,
  SecureStorage,
  RateLimiter,
  CSRFTokenManager,
  checkPasswordStrength,
  generateSecureRandom,
  sanitizeURL,
  validateFileUpload,
  initializeSecurity,
};