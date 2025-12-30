# Troubleshooting "Failed to Fetch" Error

## Quick Diagnostic Steps

### Step 1: Check if Backend is Deployed

Visit: `https://your-app.vercel.app/api/healthz`

**Expected**: `{"status":"ok"}`

**If you get 404 or error:**
- Backend serverless function isn't deployed
- See "Deployment Issues" below

**If you get CORS error:**
- Backend is working but CORS is blocking
- See "CORS Issues" below

### Step 2: Check Browser Console

1. Open your Vercel app in browser
2. Press F12 → Console tab
3. Look for the exact error message:
   - `Failed to fetch` = Network/CORS issue
   - `404 Not Found` = Route not found
   - `500 Internal Server Error` = Backend error
   - `CORS policy` = CORS configuration issue

### Step 3: Check Network Tab

1. Press F12 → Network tab
2. Try to use a feature that calls the backend
3. Look for the API request:
   - **Request URL**: Should be `https://your-app.vercel.app/api/...`
   - **Status**: Check the HTTP status code
   - **Response**: Click to see error details

---

## Common Issues & Solutions

### Issue 1: Backend Not Deployed / 404 Error

**Symptoms:**
- `GET https://your-app.vercel.app/api/healthz` returns 404
- Function logs show "Function not found"

**Solution:**

1. **Verify `api/index.py` exists** in your repository
2. **Check Vercel deployment logs:**
   - Go to Vercel dashboard → Your project → Deployments
   - Click on latest deployment → View Function Logs
   - Look for Python/import errors

3. **Verify `vercel.json` is correct:**
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api"
    }
  ],
  "functions": {
    "api/index.py": {
      "runtime": "python3.11",
      "maxDuration": 60
    }
  }
}
```

4. **Redeploy:**
   - Push a new commit, or
   - Go to Deployments → Click "..." → Redeploy

---

### Issue 2: CORS Error

**Symptoms:**
- Browser console shows: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`
- Network tab shows: Status 200 but request blocked

**Solution:**

1. **Set CORS environment variable in Vercel:**
   - Go to Vercel → Settings → Environment Variables
   - Add: `CORS_ALLOW_ALL_ORIGINS` = `true` (temporarily for testing)
   - Or add your domain: `CORS_ADDITIONAL_ORIGINS` = `https://your-app.vercel.app`

2. **Redeploy after changing CORS settings**

3. **For production, use specific origins:**
   - Set `CORS_ALLOW_ALL_ORIGINS` = `false`
   - Set `CORS_ADDITIONAL_ORIGINS` = `https://your-app.vercel.app,https://your-custom-domain.com`

---

### Issue 3: Environment Variables Missing

**Symptoms:**
- Backend returns 500 error
- Function logs show: `DATABASE_URL not found` or similar

**Solution:**

1. **Check Vercel environment variables:**
   - Go to Vercel → Settings → Environment Variables
   - Verify all required variables are set:
     - `DATABASE_URL`
     - `OPENAI_API_KEY`
     - `OPENROUTER_API_KEY` (if using)
     - `USE_OPENROUTER`
     - `VITE_USE_MOCK_API` = `false`

2. **Check which environments they're set for:**
   - Production deployments need Production variables
   - Preview deployments need Preview variables

3. **Redeploy after adding variables**

---

### Issue 4: Wrong API Path

**Symptoms:**
- Requests go to wrong URL
- Frontend trying to call `http://localhost:8000/api` in production

**Solution:**

1. **Check `src/lib/api/config.ts`:**
   - Should use relative path `/api` in production
   - Current code: `import.meta.env.PROD ? '/api' : 'http://localhost:8000/api'`

2. **Set environment variable in Vercel:**
   - `VITE_API_BASE_URL` = `/api` (or leave unset, it defaults correctly)

3. **Verify in browser:**
   - Network tab should show requests to: `https://your-app.vercel.app/api/...`
   - NOT: `http://localhost:8000/api/...`

---

### Issue 5: Mock Mode Still Enabled

**Symptoms:**
- No network requests in Network tab
- App works but uses mock data

**Solution:**

1. **Set environment variable in Vercel:**
   - `VITE_USE_MOCK_API` = `false`
   - Make sure it's set for Production environment

2. **Redeploy**

3. **Verify:**
   - Check Network tab - should see API requests
   - Check browser console - should see real API calls

---

### Issue 6: Python Dependencies Missing

**Symptoms:**
- Function logs show: `ModuleNotFoundError: No module named 'mangum'`
- Or other import errors

**Solution:**

1. **Verify `requirements.txt` exists** in root directory
2. **Check it includes all dependencies:**
   ```
   fastapi>=0.115.0
   mangum>=0.17.0
   asyncpg>=0.29.0
   pgvector>=0.2.5
   # ... etc
   ```

3. **Redeploy** - Vercel should install from requirements.txt

---

### Issue 7: Database Connection Error

**Symptoms:**
- Backend returns 500 error
- Function logs show: `connection refused` or `SSL required`

**Solution:**

1. **Verify `DATABASE_URL` includes SSL:**
   ```
   postgresql://user:pass@host:port/db?sslmode=require
   ```

2. **Check Supabase connection settings:**
   - Supabase → Settings → Database
   - Verify connection pooling is enabled
   - Check IP restrictions allow Vercel

3. **Test connection:**
   - Visit: `https://your-app.vercel.app/api/healthz`
   - Check function logs for connection errors

---

## Step-by-Step Debugging

### 1. Test Backend Directly

```bash
# Test health endpoint
curl https://your-app.vercel.app/api/healthz

# Should return: {"status":"ok"}
```

### 2. Test from Browser Console

Open browser console on your Vercel app and run:

```javascript
// Test API call
fetch('/api/healthz')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

### 3. Check Vercel Function Logs

1. Go to Vercel dashboard
2. Your project → Deployments
3. Click latest deployment
4. Click "Functions" tab
5. Click on `api/index.py`
6. View logs for errors

### 4. Check Network Requests

1. Open browser DevTools (F12)
2. Network tab
3. Try using a feature
4. Look for failed requests
5. Click on failed request → Check:
   - Request URL
   - Status code
   - Response body
   - Headers (especially CORS headers)

---

## Quick Fix Checklist

Run through this checklist:

- [ ] Backend deployed? Test `/api/healthz`
- [ ] Environment variables set in Vercel?
- [ ] `VITE_USE_MOCK_API=false` set?
- [ ] CORS configured? (set `CORS_ALLOW_ALL_ORIGINS=true` temporarily)
- [ ] `requirements.txt` includes all dependencies?
- [ ] `vercel.json` rewrite pattern correct?
- [ ] `api/index.py` exists and is correct?
- [ ] Database URL includes SSL?
- [ ] Redeployed after making changes?

---

## Still Not Working?

1. **Share the exact error message** from browser console
2. **Share the Network tab details** (request URL, status, response)
3. **Share Vercel function logs** (if available)
4. **Check if it works locally:**
   - Run backend: `cd backend && uvicorn app.main:app --reload`
   - Run frontend: `npm run dev`
   - Test if local works, then compare with Vercel

---

## Expected Working Configuration

### vercel.json
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api"
    }
  ],
  "functions": {
    "api/index.py": {
      "runtime": "python3.11",
      "maxDuration": 60
    }
  }
}
```

### Vercel Environment Variables
```
DATABASE_URL=postgresql://...?sslmode=require
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
USE_OPENROUTER=true
VITE_USE_MOCK_API=false
CORS_ALLOW_ALL_ORIGINS=true  (or false with CORS_ADDITIONAL_ORIGINS)
```

### File Structure
```
/
├── api/
│   └── index.py          ✅ Must exist
├── backend/
│   └── app/              ✅ Must exist
├── requirements.txt       ✅ Must exist
├── vercel.json           ✅ Must exist
└── src/                  ✅ Frontend
```

