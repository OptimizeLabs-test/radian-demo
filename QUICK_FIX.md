# Quick Fix for "Failed to Fetch" Error

## Immediate Steps to Try

### 1. Test if Backend is Working

Open your browser and visit:
```
https://your-app.vercel.app/api/healthz
```

**If you see `{"status":"ok"}`:**
- ✅ Backend is working!
- Problem is likely CORS or frontend configuration
- Go to Step 2

**If you see 404 or error:**
- ❌ Backend isn't deployed
- Go to Step 3

---

### 2. Fix CORS (If Backend Works)

**Quick Fix - Allow All Origins Temporarily:**

1. Go to Vercel Dashboard
2. Your Project → Settings → Environment Variables
3. Add/Update:
   - **Name**: `CORS_ALLOW_ALL_ORIGINS`
   - **Value**: `true`
   - **Environments**: ✅ Production, ✅ Preview, ✅ Development
4. Click "Save"
5. Go to Deployments → Latest → Click "..." → "Redeploy"

**After testing, restrict CORS:**
- Set `CORS_ALLOW_ALL_ORIGINS` = `false`
- Add `CORS_ADDITIONAL_ORIGINS` = `https://your-app.vercel.app`

---

### 3. Fix Backend Deployment (If 404)

**Check these files exist in your repo:**

- [ ] `api/index.py` exists
- [ ] `requirements.txt` exists in root
- [ ] `vercel.json` exists in root
- [ ] `backend/app/` directory exists

**Verify vercel.json:**
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

**Redeploy:**
1. Push a commit to trigger deployment, OR
2. Vercel Dashboard → Deployments → "..." → Redeploy

---

### 4. Fix Frontend Configuration

**Check Environment Variables in Vercel:**

1. Vercel → Settings → Environment Variables
2. Verify these are set:
   - `VITE_USE_MOCK_API` = `false` ✅
   - `VITE_API_BASE_URL` = `/api` (or leave unset - it defaults correctly)

**Check Browser Console:**

1. Open your app: `https://your-app.vercel.app`
2. Press F12 → Console tab
3. Look for errors
4. Press F12 → Network tab
5. Try using a feature
6. Check what URL it's trying to call

**Should see requests to:**
- ✅ `https://your-app.vercel.app/api/...`
- ❌ NOT `http://localhost:8000/api/...`

---

### 5. Check Vercel Function Logs

1. Vercel Dashboard → Your Project
2. Deployments → Latest Deployment
3. Click "Functions" tab
4. Click on `api/index.py`
5. View logs for errors

**Common errors:**
- `ModuleNotFoundError` → Check `requirements.txt`
- `DATABASE_URL not found` → Add environment variable
- `Connection refused` → Check database URL/SSL

---

## Most Common Issue: Mock Mode Still On

**Check this first!**

1. Vercel → Settings → Environment Variables
2. Look for `VITE_USE_MOCK_API`
3. If it's missing or set to `true`, change to `false`
4. Make sure it's set for **Production** environment
5. Redeploy

---

## Still Not Working?

**Share these details:**

1. **What URL are you visiting?** (your Vercel app URL)
2. **What happens when you visit `/api/healthz`?**
3. **Browser console error message** (exact text)
4. **Network tab** - what URL is the request going to?
5. **Vercel function logs** - any errors?

---

## Expected Working Setup

### Vercel Environment Variables:
```
DATABASE_URL=postgresql://...?sslmode=require
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
USE_OPENROUTER=true
VITE_USE_MOCK_API=false
CORS_ALLOW_ALL_ORIGINS=true  (temporarily)
```

### Test Commands:
```bash
# Test backend
curl https://your-app.vercel.app/api/healthz

# Should return: {"status":"ok"}
```

