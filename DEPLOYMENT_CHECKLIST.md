# Production Deployment Checklist

## Pre-Deployment

- [ ] Test locally with `./test-local.sh`
- [ ] All tests passing (`make test`)
- [ ] Environment variables configured in `.env`
- [ ] Database backup (if updating existing)
- [ ] Domain name and DNS configured
- [ ] SSL certificates ready (or use Let's Encrypt)

## Server Requirements

- [ ] Ubuntu 20.04+ or similar Linux
- [ ] 2+ CPU cores
- [ ] 4GB+ RAM
- [ ] 20GB+ disk space
- [ ] Open ports: 80, 443, 22
- [ ] Docker and Docker Compose installed

## Deployment Steps

1. **Configure Production Environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values:
   # - DATABASE_PASSWORD (strong password)
   # - SECRET_KEY (generate with: openssl rand -hex 32)
   # - STRIPE_SECRET_KEY
   # - SMTP credentials
   # - Domain names
   ```

2. **Deploy to Server**
   ```bash
   REMOTE_HOST=your-server.com ./deploy.sh
   ```

3. **Post-Deployment**
   ```bash
   # SSH to server
   ssh -i ".ssh/bootstrap-awareness private key.txt" ubuntu@your-server.com
   
   # Create admin user
   cd /opt/awareness-platform
   docker-compose -f docker-compose.prod.yml exec backend python create_admin_user.py
   
   # Setup SSL (if using Let's Encrypt)
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com
   
   # Check logs
   docker-compose -f docker-compose.prod.yml logs -f
   ```

## Security Checklist

- [ ] Strong database password
- [ ] Unique SECRET_KEY
- [ ] SSL/HTTPS enabled
- [ ] Firewall configured (ufw)
- [ ] Regular security updates
- [ ] Backup strategy in place
- [ ] Monitoring configured

## Monitoring

- [ ] Health checks configured
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Log aggregation
- [ ] Uptime monitoring

## Backup Strategy

- [ ] Database backups automated
- [ ] Backup retention policy
- [ ] Restore procedure tested
- [ ] Off-site backup storage

## Troubleshooting

### Services not starting
```bash
docker-compose -f docker-compose.prod.yml logs [service-name]
docker-compose -f docker-compose.prod.yml ps
```

### Database connection issues
```bash
# Check database is running
docker-compose -f docker-compose.prod.yml exec db psql -U postgres
```

### Permission issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER /opt/awareness-platform
```

### Migration issues
```bash
# Run migrations manually
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Rollback Procedure

1. Stop services: `docker-compose -f docker-compose.prod.yml down`
2. Restore database backup
3. Deploy previous version
4. Run migrations if needed
5. Start services

## Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Logs: `/opt/awareness-platform/logs`