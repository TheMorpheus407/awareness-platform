#!/bin/bash
cd /opt/awareness
cp .env.example .env

# Generate secure passwords
DB_PASSWORD=$(openssl rand -base64 24)
REDIS_PASSWORD=$(openssl rand -base64 24)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Update .env file
sed -i "s|your-secure-password-here|$DB_PASSWORD|g" .env
sed -i "s|your-redis-password-here|$REDIS_PASSWORD|g" .env
sed -i "s|your-secret-key-here-min-32-chars|$SECRET_KEY|g" .env
sed -i "s|your-jwt-secret-key-here|$JWT_SECRET|g" .env

# Update DATABASE_URL with the new password
sed -i "s|postgresql://awareness:your-secure-password-here|postgresql://awareness:$DB_PASSWORD|g" .env
sed -i "s|redis://default:your-redis-password-here|redis://default:$REDIS_PASSWORD|g" .env

echo "Environment file created successfully"