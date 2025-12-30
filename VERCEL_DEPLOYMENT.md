# Vercel Deployment Guide

## Problem: "Failing to fetch" Error

When deployed on Vercel, the frontend shows "failing to fetch" because it's trying to connect to `http://localhost:8000/api` (the default development URL).

## Solution

You need to:
1. **Deploy your backend** to a hosting service (Railway, Render, Fly.io, etc.)
2. **Set environment variables in Vercel** to point to your deployed backend

## Step 1: Deploy Your Backend

Your FastAPI backend needs to be deployed separately. Here are recommended options:

### Option A: Railway (Recommended - Easy Setup)
1. Go to [railway.app](https://railway.app)
2. Create a new project
3. Connect your GitHub repository
4. Add a new service → Deploy from GitHub repo
5. Select your repository and the `backend` folder
6. Set environment variables:
   - `DATABASE_URL` - Your Supabase Postgres connection string
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `OPENROUTER_API_KEY` - Your OpenRouter API key (if using)
   - `USE_OPENROUTER` - Set to `true` if using OpenRouter
7. Railway will automatically detect it's a Python app and deploy it
8. Note the deployed URL (e.g., `https://your-app.railway.app`)

### Option B: Render
1. Go to [render.com](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repository
4. Set:
   - **Build Command**: `cd backend && poetry install`
   - **Start Command**: `cd backend && poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
5. Add environment variables (same as Railway)
6. Deploy and note the URL

### Option C: Fly.io
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. In the `backend` folder, run: `fly launch`
3. Follow the prompts and set environment variables
4. Deploy: `fly deploy`

## Step 2: Configure Vercel Environment Variables

Once your backend is deployed, you need to tell Vercel where it is:

1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add the following variables:

### For Production:
- **Name**: `VITE_API_BASE_URL`
- **Value**: `https://your-backend-url.com/api` (replace with your actual backend URL)
- **Environment**: Production, Preview, Development

- **Name**: `VITE_USE_MOCK_API`
- **Value**: `false`
- **Environment**: Production, Preview, Development

### Example:
If your backend is deployed at `https://tara-backend.railway.app`, then:
- `VITE_API_BASE_URL` = `https://tara-backend.railway.app/api`

## Step 3: Update CORS in Backend (If Needed)

If you're getting CORS errors, update `backend/app/main.py` to include your Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:5173",
        "https://your-vercel-app.vercel.app",  # Add your Vercel domain
        "https://your-custom-domain.com",     # Add your custom domain if you have one
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Or keep `allow_origins=["*"]` for development (current setting).

## Step 4: Redeploy

After setting environment variables:
1. Go to your Vercel project
2. Click **Deployments**
3. Click the three dots on the latest deployment → **Redeploy**
4. Or push a new commit to trigger a redeploy

## Verification

After redeploying, check:
1. Open your Vercel app in the browser
2. Open browser DevTools (F12) → Network tab
3. Try to use a feature that calls the backend
4. Check if requests are going to your backend URL (not localhost)

## Troubleshooting

### Still seeing "failing to fetch"?
1. **Check environment variables**: Make sure `VITE_API_BASE_URL` is set correctly in Vercel
2. **Check backend is running**: Visit `https://your-backend-url.com/healthz` - should return `{"status": "ok"}`
3. **Check CORS**: Make sure your backend allows requests from your Vercel domain
4. **Check browser console**: Look for specific error messages

### Backend not responding?
1. Check backend logs on your hosting platform (Railway/Render/etc.)
2. Verify environment variables are set correctly in backend
3. Test backend locally first: `cd backend && uvicorn app.main:app --reload`

### CORS errors?
- Update `allow_origins` in `backend/app/main.py` to include your Vercel domain
- Make sure `allow_credentials=True` is set

## Quick Test

To test if your backend is accessible:
```bash
curl https://your-backend-url.com/healthz
```

Should return: `{"status":"ok"}`

