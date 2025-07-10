/**
 * Secure token storage utility
 * Uses sessionStorage with AES encryption for better security than localStorage
 * In production, tokens should be stored in httpOnly cookies
 */

import CryptoJS from 'crypto-js';

class SecureTokenStorage {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly REFRESH_KEY = 'refresh_token';
  private readonly ENCRYPTION_KEY = process.env.VITE_ENCRYPTION_KEY || 'cyb3rs3c_2025_d3v_k3y'; // Use env variable in production

  /**
   * AES encryption using crypto-js library
   * Provides proper encryption with PKCS7 padding
   */
  private encrypt(text: string): string {
    try {
      // Generate a random IV for each encryption
      const iv = CryptoJS.lib.WordArray.random(16);
      
      // Create key from string
      const key = CryptoJS.SHA256(this.ENCRYPTION_KEY);
      
      // Encrypt with AES
      const encrypted = CryptoJS.AES.encrypt(text, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      });
      
      // Return IV + encrypted data as base64
      const combined = iv.concat(encrypted.ciphertext);
      return CryptoJS.enc.Base64.stringify(combined);
    } catch (error) {
      console.error('Encryption error:', error);
      return '';
    }
  }

  /**
   * AES decryption using crypto-js library
   */
  private decrypt(encrypted: string): string {
    try {
      // Decode from base64
      const combined = CryptoJS.enc.Base64.parse(encrypted);
      
      // Extract IV (first 16 bytes)
      const iv = CryptoJS.lib.WordArray.create(combined.words.slice(0, 4), 16);
      
      // Extract ciphertext (remaining bytes)
      const ciphertext = CryptoJS.lib.WordArray.create(
        combined.words.slice(4),
        combined.sigBytes - 16
      );
      
      // Create key from string
      const key = CryptoJS.SHA256(this.ENCRYPTION_KEY);
      
      // Decrypt
      const decrypted = CryptoJS.AES.decrypt(
        { ciphertext: ciphertext } as any,
        key,
        {
          iv: iv,
          mode: CryptoJS.mode.CBC,
          padding: CryptoJS.pad.Pkcs7
        }
      );
      
      return decrypted.toString(CryptoJS.enc.Utf8);
    } catch (error) {
      console.error('Decryption error:', error);
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