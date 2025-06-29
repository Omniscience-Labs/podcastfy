# Production Deployment Guide for Podcastfy API

This guide provides comprehensive instructions for deploying Podcastfy API in a production environment with high availability, scalability, and monitoring.

## Architecture Overview

The production deployment includes:
- **Load Balancer**: Nginx for request distribution
- **API Servers**: Multiple FastAPI instances (3+ recommended)
- **Background Workers**: Celery workers for async processing
- **Database**: PostgreSQL for persistent storage
- **Cache/Queue**: Redis for caching and job queues
- **Object Storage**: MinIO/S3 for audio files
- **Monitoring**: Prometheus, Grafana, and Loki

## Prerequisites

- Docker and Docker Compose installed
- Domain name with DNS configured
- SSL certificates (Let's Encrypt recommended)
- Minimum 8GB RAM, 4 CPU cores
- 100GB+ storage for audio files

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/podcastfy.git
   cd podcastfy
   ```

2. **Copy environment template**
   ```bash
   cp env.production.example .env.production
   ```

3. **Update environment variables**
   Edit `.env.production` with your values:
   - Set secure passwords for all services
   - Add your AI service API keys
   - Configure storage settings
   - Set up monitoring credentials

4. **Start the services**
   ```bash
   docker-compose -f docker-compose.production.yml --env-file .env.production up -d
   ```

5. **Verify deployment**
   ```bash
   # Check service health
   curl http://localhost/health
   
   # View logs
   docker-compose -f docker-compose.production.yml logs -f
   ```

## Configuration

### API Keys

The API uses Bearer token authentication. Generate secure API keys:

```python
import secrets
api_key = f"pk_{secrets.token_urlsafe(32)}"
print(api_key)
```

### Rate Limiting

Default limits per API key:
- **Demo**: 10 requests/minute, 100 daily quota
- **Production**: 100 requests/minute, 10,000 daily quota

Customize in `podcastfy/api/auth.py` or via environment variables.

### Storage Options

#### Local MinIO (Default)
- Included in docker-compose
- Access console at http://localhost:9001
- Good for single-server deployments

#### AWS S3
1. Comment out MinIO service in docker-compose
2. Update `.env.production`:
   ```bash
   # S3_ENDPOINT_URL=  # Comment out
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   S3_BUCKET_NAME=your-bucket
   ```

#### Other S3-Compatible Storage
- DigitalOcean Spaces
- Backblaze B2
- Wasabi

Set appropriate `S3_ENDPOINT_URL` and credentials.

## Scaling

### Horizontal Scaling

1. **Add more API instances**
   ```yaml
   # docker-compose.production.yml
   api4:
     <<: *api
   api5:
     <<: *api
   ```

2. **Update Nginx upstream**
   ```nginx
   upstream api_backend {
       server api1:8000;
       server api2:8000;
       server api3:8000;
       server api4:8000;
       server api5:8000;
   }
   ```

3. **Scale workers**
   ```bash
   docker-compose -f docker-compose.production.yml up -d --scale worker=5
   ```

### Database Scaling

For high load, consider:
- Read replicas for PostgreSQL
- Connection pooling with PgBouncer
- Partitioning large tables

## Monitoring

### Metrics (Prometheus + Grafana)

1. Access Grafana at http://localhost:3000
2. Default login: admin/admin (change immediately)
3. Import dashboards from `grafana/dashboards/`

Key metrics to monitor:
- Request rate and latency
- Error rates
- Queue length
- Worker utilization
- Storage usage

### Logs (Loki + Promtail)

Centralized logging is configured automatically. View in Grafana:
1. Add Loki data source
2. Use LogQL queries:
   ```
   {service="api"} |= "error"
   {service="worker"} |= "generation failed"
   ```

### Alerts

Configure alerts in `alerts.yml`:
```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: High error rate detected
```

## Security

### SSL/TLS Setup

1. **Using Let's Encrypt**
   ```bash
   docker run -it --rm \
     -v ./ssl:/etc/letsencrypt \
     certbot/certbot certonly \
     --standalone \
     -d your-domain.com
   ```

2. **Update Nginx config**
   - Uncomment HTTPS server block
   - Update certificate paths
   - Enable HTTP to HTTPS redirect

### Security Best Practices

1. **Network Security**
   - Use private networks for internal services
   - Expose only Nginx to the internet
   - Configure firewall rules

2. **API Security**
   - Rotate API keys regularly
   - Use strong passwords for all services
   - Enable 2FA for admin interfaces

3. **Data Security**
   - Encrypt data at rest (database, storage)
   - Use encrypted connections (SSL/TLS)
   - Regular security audits

## Backup and Recovery

### Database Backup

```bash
# Automated daily backups
docker exec postgres pg_dump -U podcastfy podcastfy | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip < backup_20240101.sql.gz | docker exec -i postgres psql -U podcastfy podcastfy
```

### File Storage Backup

For S3/MinIO:
```bash
# Using MinIO client
mc mirror minio/podcastfy s3/podcastfy-backup

# Using AWS CLI
aws s3 sync s3://podcastfy s3://podcastfy-backup
```

## Maintenance

### Updates

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Rebuild and restart**
   ```bash
   docker-compose -f docker-compose.production.yml build
   docker-compose -f docker-compose.production.yml up -d
   ```

### Health Checks

Regular checks to perform:
- API endpoint availability
- Database connections
- Redis memory usage
- Disk space
- Certificate expiration

### Log Rotation

Configure Docker log rotation:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "10"
  }
}
```

## Troubleshooting

### Common Issues

1. **API not responding**
   - Check Nginx logs: `docker logs nginx`
   - Verify API health: `docker exec api1 curl localhost:8000/health`

2. **Jobs stuck in queue**
   - Check Redis: `docker exec redis redis-cli ping`
   - Monitor workers: http://localhost:5555 (Flower)

3. **Storage issues**
   - Check MinIO: http://localhost:9001
   - Verify permissions and bucket existence

### Debug Mode

Enable debug logging:
```bash
# In .env.production
LOG_LEVEL=DEBUG
SQL_ECHO=true
```

## Performance Optimization

1. **API Optimization**
   - Enable response caching
   - Use connection pooling
   - Optimize database queries

2. **Worker Optimization**
   - Adjust concurrency based on CPU
   - Use dedicated GPU nodes for AI tasks
   - Implement job priorities

3. **Storage Optimization**
   - Use CDN for audio delivery
   - Implement lifecycle policies
   - Compress audio files

## Production Checklist

Before going live:
- [ ] SSL certificates installed
- [ ] Environment variables secured
- [ ] Monitoring configured
- [ ] Backups automated
- [ ] Rate limits configured
- [ ] API keys generated
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Security scan performed
- [ ] Documentation updated

## Support

For production support:
- Check logs first
- Review monitoring dashboards
- Consult error tracking (Sentry)
- Open GitHub issue if needed

## Advanced Deployment Options

### Kubernetes

See `k8s/` directory for Kubernetes manifests and Helm charts.

### AWS ECS

Use provided CloudFormation templates in `aws/` directory.

### Google Cloud Run

Deploy using provided `cloudbuild.yaml` configuration.

Remember to always test changes in a staging environment before deploying to production! 