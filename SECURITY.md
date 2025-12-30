# Security Considerations for Vercel Deployment

## Current Security Status

### ✅ Secure Aspects

1. **Environment Variables**: Vercel encrypts and securely stores environment variables
2. **HTTPS**: All traffic is automatically encrypted via HTTPS
3. **Serverless Isolation**: Each function invocation is isolated
4. **Automatic Updates**: Vercel keeps the runtime updated with security patches

### ⚠️ Security Concerns to Address

1. **CORS Configuration**: Currently allows all origins by default (insecure for production)
2. **No API Authentication**: Endpoints are publicly accessible
3. **Error Messages**: May leak sensitive information
4. **Database Connections**: Need to ensure SSL is enforced
5. **Global State**: Shared state across invocations could be a concern

## Security Improvements Needed

### 1. Restrict CORS (CRITICAL)

**Current Issue**: `CORS_ALLOW_ALL_ORIGINS=true` allows any website to call your API.

**Fix**: 
- Set `CORS_ALLOW_ALL_ORIGINS=false` in Vercel environment variables
- Add your specific domains to the allowed origins list

### 2. Add API Authentication

**Current Issue**: Anyone can call your API endpoints.

**Recommended Solutions**:
- API Key authentication
- JWT tokens
- Supabase Auth integration

### 3. Secure Database Connections

**Ensure**: Your `DATABASE_URL` includes SSL parameters:
```
postgresql://user:pass@host:port/db?sslmode=require
```

### 4. Sanitize Error Messages

**Current Issue**: Error messages may expose internal details.

**Fix**: Already partially implemented, but review error handlers.

### 5. Rate Limiting

**Recommendation**: Add rate limiting to prevent abuse.

## Quick Security Checklist

Before deploying to production:

- [ ] Set `CORS_ALLOW_ALL_ORIGINS=false`
- [ ] Add your Vercel domain to allowed CORS origins
- [ ] Verify `DATABASE_URL` uses SSL (`sslmode=require`)
- [ ] Add API authentication (API keys or JWT)
- [ ] Review and sanitize all error messages
- [ ] Enable Vercel's DDoS protection
- [ ] Set up monitoring and alerting
- [ ] Rotate API keys regularly
- [ ] Use Vercel's environment variable encryption
- [ ] Review Vercel function logs for sensitive data

## Production Security Configuration

### Environment Variables (Vercel)

```bash
# Security
CORS_ALLOW_ALL_ORIGINS=false
TARA_ENVIRONMENT=prod

# Database (must include SSL)
DATABASE_URL=postgresql://...?sslmode=require

# API Keys (already secure in Vercel)
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
```

### CORS Configuration

Update `backend/app/core/config.py` to include your production domain:

```python
cors_origins: List[AnyHttpUrl] = Field(
    default_factory=lambda: [
        AnyHttpUrl("http://localhost:8080"),
        AnyHttpUrl("http://localhost:5173"),
        AnyHttpUrl("https://your-app.vercel.app"),  # Add your domain
        AnyHttpUrl("https://your-custom-domain.com"),  # If you have one
    ]
)
```

## Additional Security Recommendations

### 1. API Authentication

Add middleware to protect your endpoints:

```python
# backend/app/middleware/auth.py
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
```

### 2. Rate Limiting

Use a library like `slowapi`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/patients/{patient_id}/summary")
@limiter.limit("10/minute")
async def get_summary(...):
    ...
```

### 3. Input Validation

FastAPI already validates inputs via Pydantic, but ensure:
- All user inputs are validated
- SQL injection is prevented (using parameterized queries - ✅ already done)
- XSS is prevented (sanitize outputs)

### 4. Logging Security

- Don't log sensitive data (API keys, passwords, tokens)
- Use structured logging
- Monitor for suspicious activity

### 5. Vercel Security Features

- Enable Vercel's DDoS protection
- Use Vercel's Web Application Firewall (WAF) if available
- Set up security headers
- Enable Vercel Analytics for monitoring

## Comparison: Vercel vs Separate Backend

### Vercel Serverless (Current Setup)
- ✅ Automatic HTTPS
- ✅ DDoS protection
- ✅ Isolated function execution
- ✅ Automatic security updates
- ⚠️ Cold starts (performance)
- ⚠️ 60-second timeout limit

### Separate Backend (Railway/Render)
- ✅ More control over security
- ✅ No timeout limits
- ✅ Better for long-running operations
- ⚠️ You manage security updates
- ⚠️ Need to configure HTTPS/SSL yourself

## Conclusion

**Vercel deployment is secure IF you:**
1. Restrict CORS properly
2. Add authentication
3. Use SSL for database connections
4. Follow security best practices

The serverless architecture itself is secure - the main concerns are application-level security (CORS, authentication, etc.) which apply regardless of hosting platform.

