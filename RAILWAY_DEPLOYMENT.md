# Railway Deployment Guide

This guide will help you deploy your TARA backend to Railway.

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app))
2. Your Supabase database URL (already configured)
3. Your OpenAI/OpenRouter API keys

## Step-by-Step Deployment

### Step 1: Install Railway CLI (Optional but Recommended)

```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# Or use npm
npm i -g @railway/cli
```

### Step 2: Login to Railway

```bash
railway login
```

### Step 3: Create a New Project

```bash
# Navigate to your project directory
cd "C:\Users\Aarushi Sharma\OneDrive - University of Rhode Island\Documents\tara-backend"

# Initialize Railway project
railway init
```

Or use the Railway web dashboard:
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo" (recommended) or "Empty Project"

### Step 4: Configure the Service

If using the web dashboard:
1. Click "New" → "GitHub Repo" (or "Empty Service")
2. Select your repository
3. Railway will auto-detect Python and use the `Procfile`

### Step 5: Set Environment Variables

In Railway dashboard, go to your service → Variables tab, and add:

```
DATABASE_URL=your-supabase-postgres-connection-string
OPENAI_API_KEY=your-openai-api-key
OPENROUTER_API_KEY=your-openrouter-api-key (if using)
USE_OPENROUTER=true
TARA_ENVIRONMENT=prod
CORS_ALLOW_ALL_ORIGINS=false
CORS_ADDITIONAL_ORIGINS=https://your-frontend-domain.com
```

**Important Environment Variables:**
- `DATABASE_URL`: Your Supabase PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENROUTER_API_KEY`: (Optional) If using OpenRouter
- `USE_OPENROUTER`: Set to `true` if using OpenRouter
- `TARA_ENVIRONMENT`: Set to `prod` for production
- `CORS_ALLOW_ALL_ORIGINS`: Set to `false` for security
- `CORS_ADDITIONAL_ORIGINS`: Comma-separated list of allowed frontend origins

### Step 6: Configure Build Settings

Railway should auto-detect:
- **Root Directory**: Leave empty (root of repository)
- **Build Command**: `pip install -r requirements.txt` (auto-detected)
- **Start Command**: Uses `Procfile` automatically

The `Procfile` contains:
```
web: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

If auto-detection doesn't work:
1. Go to Settings → Build & Deploy
2. Verify Root Directory is `.` (root of repo)
3. Railway will use the `Procfile` for the start command

### Step 7: Deploy

Railway will automatically deploy when you:
- Push to your connected GitHub branch, OR
- Click "Deploy" in the dashboard

### Step 8: Get Your Backend URL

After deployment:
1. Go to your service → Settings → Networking
2. Generate a domain (or use the provided one)
3. Your API will be available at: `https://your-app.railway.app/api`

### Step 9: Update Frontend Configuration

Update your frontend's API base URL to point to your Railway deployment:

```env
VITE_API_BASE_URL=https://your-app.railway.app/api
```

## Troubleshooting

### Issue: Build fails
- Check that `requirements.txt` is in the root directory
- Verify Python 3.11 is being used (Railway auto-detects)
- Check build logs in Railway dashboard

### Issue: App crashes on startup
- Verify all environment variables are set
- Check that `DATABASE_URL` is correct
- Review logs in Railway dashboard

### Issue: Database connection errors
- Ensure your Supabase database allows connections from Railway's IPs
- Check that `DATABASE_URL` includes SSL parameters if required
- Verify connection pool settings in your config

### Issue: CORS errors
- Set `CORS_ADDITIONAL_ORIGINS` to include your frontend domain
- Or temporarily set `CORS_ALLOW_ALL_ORIGINS=true` for testing (not recommended for production)

## Monitoring

- **Logs**: View real-time logs in Railway dashboard → Deployments → View Logs
- **Metrics**: Check CPU, Memory, and Network usage in the Metrics tab
- **Health Check**: Your app has a `/healthz` endpoint for monitoring

## Cost

Railway's free tier includes:
- $5 credit per month
- 500 hours of usage
- Perfect for development and small projects

For production, expect ~$5-20/month depending on usage.

## Next Steps

1. Set up a custom domain (optional)
2. Configure auto-deployments from main branch
3. Set up monitoring and alerts
4. Configure database backups (if using Railway's PostgreSQL)

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

