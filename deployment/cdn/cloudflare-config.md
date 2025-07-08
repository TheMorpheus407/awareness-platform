# CDN Configuration for Bootstrap Awareness Platform

## Cloudflare Setup Guide

### 1. DNS Configuration

Add the following DNS records in Cloudflare:

```
Type    Name                    Content             Proxy Status
A       bootstrap-awareness.de  83.228.205.20       Proxied (Orange Cloud)
A       www                     83.228.205.20       Proxied (Orange Cloud)
CNAME   cdn                     bootstrap-awareness.de   Proxied
```

### 2. SSL/TLS Configuration

1. Navigate to SSL/TLS → Overview
2. Set encryption mode to "Full (strict)"
3. Enable "Always Use HTTPS"
4. Enable "Automatic HTTPS Rewrites"

### 3. Page Rules

Create the following page rules:

#### Rule 1: Cache Static Assets
- URL: `*bootstrap-awareness.de/assets/*`
- Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 month

#### Rule 2: Cache Images
- URL: `*bootstrap-awareness.de/*.{jpg,jpeg,png,gif,svg,webp,ico}`
- Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 month
  - Polish: Lossless
  - WebP: On

#### Rule 3: Cache Fonts and CSS/JS
- URL: `*bootstrap-awareness.de/*.{css,js,woff,woff2,ttf,eot}`
- Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 week
  - Browser Cache TTL: 1 week

#### Rule 4: API Bypass
- URL: `*bootstrap-awareness.de/api/*`
- Settings:
  - Cache Level: Bypass
  - Disable Performance

### 4. Caching Configuration

Navigate to Caching → Configuration:

- Caching Level: Standard
- Browser Cache TTL: Respect Existing Headers
- Crawler Hints: On
- Always Online: On

### 5. Speed Optimization

Navigate to Speed → Optimization:

#### Auto Minify
- JavaScript: On
- CSS: On
- HTML: On

#### Brotli
- Enable Brotli compression

#### Rocket Loader
- Automatic (recommended)

#### Mirage
- On (for image optimization)

#### Polish
- Lossless

### 6. Security Settings

Navigate to Security:

#### WAF (Web Application Firewall)
- Enable Cloudflare Managed Ruleset
- Set Security Level to "Medium"

#### Rate Limiting Rules
Create rules for:
- `/api/auth/*` - 5 requests per minute per IP
- `/api/v1/login` - 5 requests per minute per IP
- `/api/v1/register` - 3 requests per minute per IP

#### Bot Management
- Enable Bot Fight Mode
- Configure JavaScript Challenge for suspicious traffic

### 7. Network Settings

- HTTP/3 (with QUIC): On
- 0-RTT Connection Resumption: On
- gRPC: On
- WebSockets: On

### 8. Analytics and Monitoring

Enable:
- Web Analytics
- Real User Monitoring (RUM)
- Configure alerts for:
  - Origin errors > 1%
  - Edge errors > 1%
  - Traffic spikes

### 9. Workers (Optional Advanced Configuration)

Create a Worker for advanced caching and routing:

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  
  // Cache API responses for 1 minute at edge
  if (url.pathname.startsWith('/api/v1/courses')) {
    const cacheKey = new Request(url.toString(), request)
    const cache = caches.default
    
    let response = await cache.match(cacheKey)
    
    if (!response) {
      response = await fetch(request)
      
      if (response.status === 200) {
        const headers = new Headers(response.headers)
        headers.set('Cache-Control', 'public, max-age=60')
        
        response = new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: headers
        })
        
        event.waitUntil(cache.put(cacheKey, response.clone()))
      }
    }
    
    return response
  }
  
  // Default handling
  return fetch(request)
}
```

### 10. Transform Rules

Create transform rules for:

#### Request Header Modification
- Add `X-Forwarded-Proto: https` to all requests
- Add `X-Real-IP` from `CF-Connecting-IP`

#### Response Header Modification
- Add security headers if missing:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `Referrer-Policy: strict-origin-when-cross-origin`

### 11. Load Balancing (Pro Plan)

If using Cloudflare Load Balancing:

1. Create health check:
   - URL: `https://bootstrap-awareness.de/api/health`
   - Interval: 60 seconds
   - Timeout: 5 seconds
   - Retries: 2

2. Configure origin pools with your servers

3. Set up geo-steering for optimal performance

### 12. Argo Smart Routing (Optional)

Enable Argo for:
- 30% average performance improvement
- Intelligent routing around congestion
- Real-time network optimizations

## Implementation in Application

### Nginx Configuration Updates

Add these headers to serve static assets optimally:

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header X-Cache-Status $upstream_cache_status;
    
    # Enable gzip
    gzip on;
    gzip_vary on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    
    # Cloudflare will respect these
    add_header CDN-Cache-Control "max-age=31536000";
}
```

### Frontend Build Optimization

Update `vite.config.ts` for CDN-friendly builds:

```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    },
    // Generate source maps for debugging
    sourcemap: true,
    // Optimize chunks
    chunkSizeWarningLimit: 1000,
  },
  // Use CDN URL in production
  base: process.env.NODE_ENV === 'production' 
    ? 'https://cdn.bootstrap-awareness.de/' 
    : '/'
})
```

## Monitoring and Optimization

### Key Metrics to Monitor

1. **Cache Hit Ratio**: Target > 85%
2. **Bandwidth Saved**: Monitor monthly savings
3. **Origin Response Time**: Should decrease with caching
4. **Error Rates**: Monitor 4xx and 5xx errors

### Regular Optimization Tasks

1. Review cache analytics monthly
2. Adjust cache TTLs based on content update frequency
3. Monitor and optimize largest content consumers
4. Review and update security rules

### Cost Optimization

1. Use appropriate cache levels
2. Implement smart image optimization
3. Use Workers for edge computing when beneficial
4. Monitor bandwidth usage and adjust plans

## Purge Strategy

### Automated Purge on Deployment

Add to deployment script:

```bash
# Purge Cloudflare cache after deployment
curl -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

### Selective Purge

For specific files:

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://bootstrap-awareness.de/assets/main.js"]}'
```

## Environment Variables

Add to `.env.production`:

```env
# Cloudflare Configuration
CF_ZONE_ID=your-zone-id
CF_API_TOKEN=your-api-token
CDN_URL=https://cdn.bootstrap-awareness.de
```

This configuration provides enterprise-grade CDN setup with optimal caching, security, and performance.