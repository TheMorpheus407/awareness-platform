/**
 * Secure token storage utility
 * Uses sessionStorage with encryption for better security than localStorage
 * In production, tokens should be stored in httpOnly cookies
 */

class SecureTokenStorage {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly REFRESH_KEY = 'refresh_token';
  private readonly ENCRYPTION_KEY = 'cyb3rs3c_2025'; // In production, use env variable

  /**
   * Simple XOR encryption (for demonstration)
   * In production, use a proper encryption library
   */
  private encrypt(text: string): string {
    let encrypted = '';
    for (let i = 0; i < text.length; i++) {
      encrypted += String.fromCharCode(
        text.charCodeAt(i) ^ this.ENCRYPTION_KEY.charCodeAt(i % this.ENCRYPTION_KEY.length)
      );
    }
    return btoa(encrypted); // Base64 encode
  }

  /**
   * Simple XOR decryption
   */
  private decrypt(encrypted: string): string {
    try {
      const decoded = atob(encrypted); // Base64 decode
      let decrypted = '';
      for (let i = 0; i < decoded.length; i++) {
        decrypted += String.fromCharCode(
          decoded.charCodeAt(i) ^ this.ENCRYPTION_KEY.charCodeAt(i % this.ENCRYPTION_KEY.length)
        );
      }
      return decrypted;
    } catch {
      return '';
    }
  }

  /**
   * Store access token securely
   */
  setAccessToken(token: string): void {
    if (token) {
      // Use sessionStorage instead of localStorage (cleared on tab close)
      sessionStorage.setItem(this.TOKEN_KEY, this.encrypt(token));
      
      // Set token expiry (30 minutes)
      const expiry = new Date().getTime() + (30 * 60 * 1000);
      sessionStorage.setItem(`${this.TOKEN_KEY}_expiry`, expiry.toString());
    }
  }

  /**
   * Get access token if valid
   */
  getAccessToken(): string | null {
    const encrypted = sessionStorage.getItem(this.TOKEN_KEY);
    const expiry = sessionStorage.getItem(`${this.TOKEN_KEY}_expiry`);

    if (!encrypted || !expiry) {
      return null;
    }

    // Check if token expired
    if (new Date().getTime() > parseInt(expiry)) {
      this.clearTokens();
      return null;
    }

    return this.decrypt(encrypted);
  }

  /**
   * Store refresh token
   */
  setRefreshToken(token: string): void {
    if (token) {
      sessionStorage.setItem(this.REFRESH_KEY, this.encrypt(token));
    }
  }

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    const encrypted = sessionStorage.getItem(this.REFRESH_KEY);
    return encrypted ? this.decrypt(encrypted) : null;
  }

  /**
   * Clear all tokens
   */
  clearTokens(): void {
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(`${this.TOKEN_KEY}_expiry`);
    sessionStorage.removeItem(this.REFRESH_KEY);
    
    // Also clear from localStorage for migration
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  /**
   * Check if user has valid token
   */
  hasValidToken(): boolean {
    return this.getAccessToken() !== null;
  }

  /**
   * Migrate from localStorage to secure storage
   */
  migrateFromLocalStorage(): void {
    const oldToken = localStorage.getItem('access_token');
    if (oldToken) {
      this.setAccessToken(oldToken);
      localStorage.removeItem('access_token');
    }
  }
}

// Export singleton instance
export const secureStorage = new SecureTokenStorage();

// Security recommendations comment
/**
 * SECURITY RECOMMENDATIONS:
 * 
 * 1. **Use HttpOnly Cookies**: The most secure approach is to store tokens in httpOnly cookies
 *    set by the backend. This prevents JavaScript access entirely.
 * 
 * 2. **Implement CSRF Protection**: When using cookies, implement CSRF tokens to prevent
 *    cross-site request forgery attacks.
 * 
 * 3. **Use Secure Flag**: Ensure cookies have the Secure flag set in production (HTTPS only).
 * 
 * 4. **Implement Token Rotation**: Rotate tokens regularly and implement refresh token flow.
 * 
 * 5. **Add Content Security Policy**: Implement CSP headers to prevent XSS attacks.
 * 
 * 6. **Use SameSite Cookie Attribute**: Set SameSite=Strict or SameSite=Lax for cookies.
 * 
 * 7. **Implement Rate Limiting**: Add rate limiting to prevent brute force attacks.
 * 
 * 8. **Monitor for Anomalies**: Log and monitor authentication events for suspicious activity.
 */