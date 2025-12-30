# Fix "Failed to Fetch" Error - Step by Step

## Quick Diagnostic

### Step 1: Test Backend Directly

Open your browser and visit:
```
https://your-vercel-app.vercel.app/api/healthz
```

**What do you see?**
- ✅ `{"status":"ok"}` → Backend works! Go to Step 2
- ❌ 404 → Backend not deployed. Go to Step 3
- ❌ 500/Error → Backend error. Go to Step 4
- ❌ CORS error → Go to Step 5

---

## Step 2: Check Frontend Configuration

If backend works (`/api/healthz` returns OK):

### Check Environment Variables in Vercel:

1. Vercel Dashboard → Your Project
2. Settings → Environment Variables
3. Verify these are set for **Production**:
   - `VITE_USE_MOCK_API` = `false` ✅ **CRITICAL**
   - `VITE_API_BASE_URL` = `/api` (or leave unset - defaults correctly)

### Check Browser Console:

1. Open your app: `https://your-app.vercel.app`
2. Press **F12** → **Console** tab
3. Look for errors
4. Press **F12** → **Network** tab
5. Try to load patient data
6. Check what URL the request is going to

**Should see:**
- ✅ Requests to: `https://your-app.vercel.app/api/...`
- ❌ NOT: `http://localhost:8000/api/...`

**If wrong URL:**
- Set `VITE_API_BASE_URL` = `/api` in Vercel
- Redeploy

---

## Step 3: Fix Backend Not Deployed (404)

If `/api/healthz` returns 404:

### Check Files Exist:

- [ ] `api/index.py` exists in repository
- [ ] `requirements.txt` exists in root
- [ ] `vercel.json` exists in root
- [ ] `backend/app/` directory exists

### Check Vercel Function Detection:

1. Vercel Dashboard → Your Project
2. Settings → **Functions** tab
3. Look for `api/index.py` in the list

**If not there:**
- Function isn't being detected
- Check file is committed to repository
- Verify file path is correct (`/api/index.py` in root)

### Check Deployment Logs:

1. Vercel Dashboard → Deployments → Latest
2. View build logs
3. Look for:
   - "Installing Python dependencies"
   - "Deploying functions"
   - Any errors

### Fix: Redeploy

1. Make sure all files are committed:
   ```bash
   git add api/ requirements.txt vercel.json
   git commit -m "Add backend serverless function"
   git push
   ```

2. Wait for Vercel to auto-deploy, OR
3. Manually redeploy: Deployments → "..." → Redeploy

---

## Step 4: Fix Backend Errors (500)

If `/api/healthz` returns 500 or error:

### Check Vercel Function Logs:

1. Vercel Dashboard → Deployments → Latest
2. Click **"Functions"** tab
3. Click on `api/index.py`
4. View logs for errors

### Common Errors:

**"ModuleNotFoundError: No module named 'mangum'"**
- Solution: Check `requirements.txt` includes all dependencies
- Redeploy

**"DATABASE_URL not found"**
- Solution: Add `DATABASE_URL` in Vercel environment variables
- Make sure it includes `?sslmode=require`
- Redeploy

**"Connection refused" or database errors**
- Solution: Check `DATABASE_URL` is correct
- Verify it includes `?sslmode=require`
- Check Supabase allows connections

**Import errors from backend**
- Solution: Check `backend/app/` structure is correct
- Verify Python path in `api/index.py`

---

## Step 5: Fix CORS Errors

If you see CORS errors in browser console:

### Quick Fix (Temporary):

1. Vercel → Settings → Environment Variables
2. Add/Update:
   - `CORS_ALLOW_ALL_ORIGINS` = `true`
3. Redeploy

### Permanent Fix:

1. Set `CORS_ALLOW_ALL_ORIGINS` = `false`
2. Add `CORS_ADDITIONAL_ORIGINS` = `https://your-app.vercel.app`
3. Redeploy

---

## Step 6: Most Common Issue - Mock Mode Still On

**This is the #1 cause of "failed to fetch"!**

### Check:

1. Vercel → Settings → Environment Variables
2. Find `VITE_USE_MOCK_API`
3. **Must be set to `false`** for Production
4. If missing or set to `true`, that's the problem!

### Fix:

1. Set `VITE_USE_MOCK_API` = `false`
2. Make sure it's set for **Production** environment
3. Redeploy

**How to verify it's off:**
- Open browser console on your app
- Run: `console.log(import.meta.env.VITE_USE_MOCK_API)`
- Should show: `"false"` or `undefined` (which means false)

---

## Complete Checklist

Run through this checklist:

### Backend:
- [ ] `/api/healthz` returns `{"status":"ok"}`
- [ ] `api/index.py` exists in repository
- [ ] `vercel.json` has function configuration
- [ ] `requirements.txt` includes all dependencies
- [ ] Vercel Functions tab shows `api/index.py`

### Environment Variables:
- [ ] `DATABASE_URL` set (with `?sslmode=require`)
- [ ] `OPENAI_API_KEY` set
- [ ] `OPENROUTER_API_KEY` set (if using)
- [ ] `USE_OPENROUTER` set
- [ ] `VITE_USE_MOCK_API` = `false` ✅ **CRITICAL**
- [ ] `CORS_ALLOW_ALL_ORIGINS` = `true` (temporarily)

### Frontend:
- [ ] Browser Network tab shows requests to `/api/...`
- [ ] NOT requests to `localhost:8000`
- [ ] No CORS errors in console

---

## Quick Test Commands

### Test Backend:
```bash
curl https://your-app.vercel.app/api/healthz
```

### Test from Browser Console:
```javascript
// Test API
fetch('/api/healthz')
  .then(r => r.json())
  .then(data => console.log('✅ Backend works:', data))
  .catch(err => console.error('❌ Error:', err));

// Check mock mode
console.log('Mock mode:', import.meta.env.VITE_USE_MOCK_API);
```

---

## Most Likely Fixes (In Order)

1. **Mock mode still on** → Set `VITE_USE_MOCK_API=false` in Vercel
2. **Backend not deployed** → Check `api/index.py` exists, redeploy
3. **CORS blocking** → Set `CORS_ALLOW_ALL_ORIGINS=true` temporarily
4. **Missing env vars** → Add `DATABASE_URL`, `OPENAI_API_KEY`, etc.
5. **Wrong API URL** → Frontend calling `localhost` instead of `/api`

---

## Still Not Working?

**Share these details:**

1. Result of `/api/healthz` test
2. Browser console error (exact message)
3. Network tab - what URL is being called?
4. Vercel function logs - any errors?
5. Environment variables - which ones are set?

---

## Expected Working State

### Backend:
- ✅ `/api/healthz` → `{"status":"ok"}`
- ✅ Function logs show no errors
- ✅ Database connection works

### Frontend:
- ✅ Network requests go to `/api/...`
- ✅ No CORS errors
- ✅ Mock mode is off
- ✅ Patient data loads successfully

