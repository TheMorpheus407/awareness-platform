# Project Credentials and Access Information

## 🔐 Server Access

### Production Server
- **IP Address**: 83.228.205.20
- **OS**: Ubuntu 24.04 LTS
- **Domain**: https://bootstrap-awareness.de
- **SSH Port**: 22 (default)
- **SSH User**: root (or as configured)

### SSH Keys
- **Public Key**: Located in `/bootstrap awareness public key.txt`
- **Private Key**: Located in `/bootstrap-awareness private key.txt`
- **Key Type**: RSA 2048-bit
- **Generated By**: phpseclib

## 📧 Email Configuration

### SMTP Settings
- **Host**: smtp.gmail.com (or as configured)
- **Port**: 587
- **Security**: TLS/STARTTLS
- **Username**: (to be documented)
- **Password**: `5X58dee2u3ov6ffGTMBUjh6tjZFB3vU2qhGvyRC`

## 🐙 GitHub Repository

### Repository Details
- **URL**: https://github.com/TheMorpheus407/awareness-platform
- **Owner**: TheMorpheus407
- **Repository Name**: awareness-platform
- **Visibility**: Private (assumed)

### GitHub Actions Secrets
Required secrets for CI/CD:
1. **SSH_PRIVATE_KEY**: Content of private key file
2. **DB_PASSWORD**: `AwarenessDB2024Secure`
3. **SECRET_KEY**: `8eb9afc6e39da58b95628f1505bf1107c7f9f0243990d7acd4ba23f82694b1e5`
4. **EMAIL_PASSWORD**: `5X58dee2u3ov6ffGTMBUjh6tjZFB3vU2qhGvyRC`
5. **REDIS_PASSWORD**: `redis_595e9ffc5e32e7fc6d8cbae32a9e610c`

## 🗄️ Database Access

### PostgreSQL
- **Host**: localhost (in production)
- **Port**: 5432
- **Database**: cybersecurity_platform
- **Username**: postgres (default)
- **Password**: `AwarenessDB2024Secure`

### Redis
- **Host**: localhost
- **Port**: 6379
- **Password**: `redis_595e9ffc5e32e7fc6d8cbae32a9e610c`

## 🔑 Application Secrets

### JWT/Security
- **SECRET_KEY**: `8eb9afc6e39da58b95628f1505bf1107c7f9f0243990d7acd4ba23f82694b1e5`
- **Algorithm**: HS256
- **Access Token Expiry**: 30 minutes
- **Refresh Token Expiry**: 7 days

## 📱 2FA Configuration
- **Issuer**: Bootstrap Awareness Platform
- **Algorithm**: TOTP
- **Digits**: 6
- **Period**: 30 seconds

## 🚀 Deployment Commands

### SSH Access
```bash
ssh -i "bootstrap-awareness private key.txt" root@83.228.205.20
```

### Quick Deploy
```bash
git push origin main  # Triggers GitHub Actions
```

## ⚠️ Security Notes

1. **NEVER** commit these credentials to Git
2. Store private keys securely with restricted permissions (600)
3. Rotate passwords and keys regularly
4. Use environment variables for all secrets
5. Enable 2FA on all admin accounts

## 📅 Last Updated
- Date: 2025-07-09
- Updated By: System Administrator

---

**Note**: This file should be stored securely and access should be restricted to authorized personnel only.