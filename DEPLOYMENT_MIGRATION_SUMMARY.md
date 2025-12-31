# Migration from Vercel to Railway - Summary

## Changes Made

### ✅ Files Removed (Vercel-specific)
1. **`vercel.json`** - Vercel configuration file
2. **`api/index.py`** - Vercel serverless function handler (used Mangum adapter)
3. **`api/` directory** - Empty directory that contained Vercel serverless functions

### ✅ Files Created (Railway-specific)
1. **`Procfile`** - Tells Railway how to start your application
   - Command: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **`railway.json`** - Railway deployment configuration
   - Uses NIXPACKS builder (auto-detects Python)
   - Configures restart policy

3. **`RAILWAY_DEPLOYMENT.md`** - Complete step-by-step deployment guide

### ✅ Files Updated
1. **`requirements.txt`** - Removed `mangum>=0.17.0` (Vercel-specific dependency)
   - Updated comments to reflect Railway usage
   - All other dependencies remain the same

## What's Next?

### Immediate Steps:
1. **Review the deployment guide**: Read `RAILWAY_DEPLOYMENT.md` for detailed instructions

2. **Sign up for Railway**: Go to [railway.app](https://railway.app) and create an account

3. **Deploy your app**:
   - Option A: Use Railway web dashboard (easiest)
     - Connect your GitHub repo
     - Railway will auto-detect Python and use the Procfile
   - Option B: Use Railway CLI
     ```bash
     npm i -g @railway/cli
     railway login
     railway init
     railway up
     ```

4. **Set environment variables** in Railway dashboard:
   - `DATABASE_URL` - Your Supabase PostgreSQL connection string
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `OPENROUTER_API_KEY` - (if using OpenRouter)
   - `USE_OPENROUTER=true` - (if using OpenRouter)
   - `TARA_ENVIRONMENT=prod`
   - `CORS_ALLOW_ALL_ORIGINS=false`
   - `CORS_ADDITIONAL_ORIGINS=https://your-frontend-domain.com`

5. **Get your Railway URL** and update your frontend's `VITE_API_BASE_URL`

## Key Differences: Vercel vs Railway

| Feature | Vercel (Old) | Railway (New) |
|---------|--------------|---------------|
| **Architecture** | Serverless functions | Traditional server |
| **Cold Starts** | Yes (can be slow) | No (always warm) |
| **Connection Pooling** | Limited effectiveness | Full support |
| **Request Timeout** | 60s max (risky) | Configurable (default 5min) |
| **Long-running Operations** | Not ideal | Perfect for RAG/LLM |
| **State Management** | Stateless (lazy init) | Persistent connections |

## Benefits of Railway

✅ **Better for your use case**:
- Persistent database connections (connection pooling works properly)
- No cold starts (faster response times)
- Better for long-running LLM/RAG operations
- More predictable performance

✅ **Easier deployment**:
- Auto-detects Python
- Uses Procfile automatically
- Simple environment variable management
- Great logging and monitoring

✅ **Cost-effective**:
- $5 free credit per month
- Pay-as-you-go pricing
- ~$5-20/month for typical usage

## Testing Locally

Before deploying, you can test the Railway setup locally:

```bash
# In the backend directory
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

This simulates how Railway will run your app.

## Need Help?

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Check `RAILWAY_DEPLOYMENT.md` for detailed troubleshooting

