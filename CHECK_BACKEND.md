# Check if Backend is Working

## Step 1: Test Backend Endpoint

After deployment completes, visit this URL in your browser:

```
https://your-app.vercel.app/api/healthz
```

**Expected Result:**
```json
{"status":"ok"}
```

**If you see this:**
- ✅ Backend is working!
- The "failed to fetch" is likely a frontend configuration issue
- Go to "Frontend Configuration" below

**If you see 404:**
- ❌ Backend function not deployed
- Go to "Backend Not Deployed" below

**If you see 500 or error:**
- ❌ Backend has an error
- Go to "Backend Error" below

---

## Step 2: Check Vercel Function Logs

1. Go to Vercel Dashboard
2. Your Project → **Deployments**
3. Click on the **latest deployment**
4. Click **"Functions"** tab
5. Click on **`api/index.py`**
6. View the logs

**Look for:**
- ✅ "Function deployed successfully"
- ❌ Import errors (ModuleNotFoundError)
- ❌ Environment variable errors
- ❌ Database connection errors

---

## Common Issues

### Issue 1: Backend Function Not Found (404)

**Symptoms:**
- `/api/healthz` returns 404
- Function logs show "Function not found"

**Check:**
- [ ] `api/index.py` exists in your repository
- [ ] `vercel.json` has the function configuration
- [ ] Files are committed and pushed to GitHub

**Fix:**
1. Verify files are in repo:
   ```bash
   git status
   git add api/ requirements.txt vercel.json
   git commit -m "Add backend serverless function"
   git push company master
   ```

2. Wait for Vercel to redeploy

---

### Issue 2: Python Import Error

**Symptoms:**
- Function logs show: `ModuleNotFoundError: No module named 'mangum'`

**Fix:**
1. Check `requirements.txt` includes all dependencies
2. Vercel should install from `requirements.txt` automatically
3. If not, check Vercel build logs for pip install errors

---

### Issue 3: Environment Variables Missing

**Symptoms:**
- Function logs show: `DATABASE_URL not found` or similar
- Backend returns 500 error

**Fix:**
1. Vercel → Settings → Environment Variables
2. Add all required variables:
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `OPENROUTER_API_KEY`
   - `USE_OPENROUTER`
3. Make sure they're set for **Production** environment
4. Redeploy

---

### Issue 4: Database Connection Error

**Symptoms:**
- Function logs show connection errors
- Backend returns 500

**Fix:**
1. Verify `DATABASE_URL` includes SSL:
   ```
   postgresql://user:pass@host:port/db?sslmode=require
   ```

2. Check Supabase allows connections from Vercel

---

## Frontend Configuration

If backend works (`/api/healthz` returns OK) but frontend still fails:

### Check Environment Variables:

1. Vercel → Settings → Environment Variables
2. Verify:
   - `VITE_USE_MOCK_API` = `false` (for Production)
   - `VITE_API_BASE_URL` = `/api` (or leave unset)

### Check Browser Console:

1. Open your app: `https://your-app.vercel.app`
2. Press F12 → Console
3. Look for errors
4. Press F12 → Network tab
5. Try using a feature
6. Check what URL requests are going to

**Should see:**
- ✅ `https://your-app.vercel.app/api/...`
- ❌ NOT `http://localhost:8000/api/...`

---

## Quick Test Commands

### Test Backend:
```bash
curl https://your-app.vercel.app/api/healthz
```

### Test from Browser Console:
```javascript
fetch('/api/healthz')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

---

## Next Steps Based on Results

**If `/api/healthz` works:**
- Backend is fine
- Check frontend configuration (mock mode, API URL)
- Check CORS settings

**If `/api/healthz` returns 404:**
- Backend function not deployed
- Check `api/index.py` exists
- Check Vercel function logs

**If `/api/healthz` returns 500:**
- Backend has an error
- Check Vercel function logs
- Check environment variables
- Check database connection

