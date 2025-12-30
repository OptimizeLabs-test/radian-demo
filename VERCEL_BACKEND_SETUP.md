# Deploying Backend on Vercel

Yes! You can deploy your FastAPI backend directly on Vercel using serverless functions. This guide explains how.

## What's Been Set Up

1. **`vercel.json`** - Configuration for Vercel deployment
2. **`api/index.py`** - Serverless function handler that routes requests to FastAPI
3. **`requirements.txt`** - Python dependencies for Vercel
4. **Serverless-compatible initialization** - Database connections are initialized lazily

## How It Works

- Vercel routes all `/api/*` requests to the `api/index.py` serverless function
- The handler uses Mangum to convert Vercel's request format to ASGI (which FastAPI uses)
- Database connections are initialized on first request and reused across invocations
- The frontend and backend are deployed together on the same domain

## Deployment Steps

### 1. Set Environment Variables in Vercel

Go to your Vercel project → **Settings** → **Environment Variables** and add:

**Required:**
- `DATABASE_URL` - Your Supabase Postgres connection string
- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENROUTER_API_KEY` - Your OpenRouter API key (if using)
- `USE_OPENROUTER` - Set to `true` if using OpenRouter

**Optional:**
- `CORS_ALLOW_ALL_ORIGINS` - Set to `true` to allow all origins (default: `false`)
- `TARA_ENVIRONMENT` - Set to `prod` for production

### 2. Update Frontend API Configuration

Since the backend is on the same domain, update your Vercel environment variables:

- `VITE_API_BASE_URL` = `/api` (relative path - same domain)
- `VITE_USE_MOCK_API` = `false`

**OR** you can leave `VITE_API_BASE_URL` unset and it will default to `/api` (relative path).

### 3. Deploy

1. Push your code to GitHub
2. Vercel will automatically detect the changes and deploy
3. The deployment will:
   - Build the frontend (`npm run build`)
   - Install Python dependencies from `requirements.txt`
   - Set up the serverless function

### 4. Verify

After deployment:
1. Visit `https://your-app.vercel.app/api/healthz`
   - Should return: `{"status":"ok"}`
2. Visit your app and test the backend features

## File Structure

```
tara-backend/
├── api/
│   └── index.py          # Vercel serverless function handler
├── backend/
│   └── app/              # FastAPI application
├── src/                   # Frontend React app
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies for Vercel
└── package.json          # Frontend dependencies
```

## Important Notes

### Serverless Limitations

1. **Cold Starts**: First request after inactivity may be slower (1-3 seconds)
2. **Execution Time**: Maximum 60 seconds per request (configured in `vercel.json`)
3. **Connection Pooling**: Connections are reused within the same container, but each cold start creates new connections

### Database Connections

- Connections are initialized lazily on first request
- They're reused across requests within the same container
- For high-traffic apps, consider using a connection pooler like PgBouncer

### CORS

The backend is configured to allow all origins by default in development. For production:
- Set `CORS_ALLOW_ALL_ORIGINS=false` in Vercel environment variables
- Add your Vercel domain to `cors_origins` in `backend/app/core/config.py`

## Troubleshooting

### "Module not found" errors
- Make sure `requirements.txt` includes all dependencies
- Check that `backend/` directory is included in your repository

### Database connection errors
- Verify `DATABASE_URL` is set correctly in Vercel
- Check that your Supabase database allows connections from Vercel's IPs
- Ensure connection string includes SSL parameters

### Timeout errors
- Increase `maxDuration` in `vercel.json` (up to 60 seconds on Pro plan)
- Optimize your RAG queries if they're taking too long

### CORS errors
- Set `CORS_ALLOW_ALL_ORIGINS=true` temporarily to test
- Or add your Vercel domain to the allowed origins list

## Alternative: Separate Backend Deployment

If you encounter issues with serverless or need better performance, you can still deploy the backend separately on:
- Railway (recommended)
- Render
- Fly.io

Then set `VITE_API_BASE_URL` to your backend URL in Vercel.

