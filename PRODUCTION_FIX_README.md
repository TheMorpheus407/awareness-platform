# Production Fix Scripts

This directory contains scripts to fix production issues on the Awareness Schulungen server.

## Server Details
- **Server**: ubuntu@83.228.205.20
- **Directory**: /opt/awareness
- **Website**: https://awareness-schulungen.de

## Available Scripts

### 1. EXECUTE_PRODUCTION_FIX.sh
Standard production fix script that:
- Connects to the production server
- Creates and executes a fix script
- Cleans up Docker resources
- Updates configuration files
- Restarts services with correct images
- Verifies everything is working

**Usage:**
```bash
./EXECUTE_PRODUCTION_FIX.sh
```

### 2. EXECUTE_PRODUCTION_FIX_SAFE.sh
Enhanced version with safety features:
- Creates a backup before making changes
- Includes rollback capability
- More comprehensive health checks
- Detailed verification steps
- Resource usage monitoring

**Usage:**
```bash
./EXECUTE_PRODUCTION_FIX_SAFE.sh
```

### 3. EMERGENCY_PRODUCTION_FIX.sh
Quick emergency fix for when the site is down:
- Minimal steps for fastest recovery
- Stops services and recreates configuration
- Uses latest Docker images
- Basic verification only

**Usage:**
```bash
./EMERGENCY_PRODUCTION_FIX.sh
```

## Prerequisites

1. **SSH Access**: You must have SSH key access to ubuntu@83.228.205.20
2. **Permissions**: Scripts require sudo access on the server
3. **Network**: Ensure you can reach the server and https://awareness-schulungen.de

## Common Issues and Solutions

### Issue: Website shows wrong content
**Solution**: Run `EXECUTE_PRODUCTION_FIX.sh` to ensure correct images are used

### Issue: Services won't start
**Solution**: Run `EXECUTE_PRODUCTION_FIX_SAFE.sh` for comprehensive cleanup and restart

### Issue: Site is completely down
**Solution**: Run `EMERGENCY_PRODUCTION_FIX.sh` for fastest recovery

### Issue: Need to rollback changes
**Solution**: Use the backup path shown by `EXECUTE_PRODUCTION_FIX_SAFE.sh`

## Manual Commands

If scripts fail, you can SSH directly:

```bash
# Connect to server
ssh ubuntu@83.228.205.20

# Navigate to app directory
cd /opt/awareness

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Full reset
docker-compose down
docker system prune -af
docker-compose up -d
```

## Verification Steps

After running any fix script:

1. Check website: https://awareness-schulungen.de
2. Verify correct content is displayed
3. Test login functionality
4. Monitor logs for errors
5. Check resource usage

## Important Notes

- Always check current state before running fixes
- The SAFE version creates backups - use it for critical changes
- Emergency fix is fastest but skips some checks
- Monitor logs after any changes
- Keep these scripts updated with any infrastructure changes

## Support

If issues persist after running these scripts:
1. Check Docker logs for specific errors
2. Verify DNS and SSL certificates
3. Check server resources (disk, memory, CPU)
4. Review nginx/reverse proxy configuration
5. Contact infrastructure team if needed