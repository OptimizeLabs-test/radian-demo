# Diagnostic Checklist - Run Through This

## Step 1: Is Backend Deployed?

**Test:** Visit `https://your-app.vercel.app/api/healthz`

- [ ] ✅ Returns `{"status":"ok"}` → Backend is working! Go to Step 2
- [ ] ❌ Returns 404 → Backend not deployed. Go to Step 5
- [ ] ❌ Returns 500 → Backend error. Go to Step 6
- [ ] ❌ CORS error → Go to Step 3

---

## Step 2: Check Frontend Configuration

**In Vercel Dashboard:**
- [ ] `VITE_USE_MOCK_API` = `false` (set for Production)
- [ ] `VITE_API_BASE_URL` = `/api` (or unset - defaults correctly)

**In Browser (F12 → Network tab):**
- [ ] Requests go to: `https://your-app.vercel.app/api/...`
- [ ] NOT: `http://localhost:8000/api/...`

**If wrong URL:**
- Set `VITE_API_BASE_URL` = `/api` in Vercel
- Redeploy

---

## Step 3: Fix CORS

**Quick Test:**
1. Vercel → Settings → Environment Variables
2. Add: `CORS_ALLOW_ALL_ORIGINS` = `true`
3. Redeploy
4. Test again

**If it works:**
- Backend is working, CORS was the issue
- Now restrict CORS properly (see SECURITY.md)

---

## Step 4: Check Environment Variables

**Required variables in Vercel:**
- [ ] `DATABASE_URL` (with `?sslmode=require`)
- [ ] `OPENAI_API_KEY`
- [ ] `OPENROUTER_API_KEY` (if using)
- [ ] `USE_OPENROUTER` = `true`
- [ ] `VITE_USE_MOCK_API` = `false`
- [ ] `CORS_ALLOW_ALL_ORIGINS` = `true` (temporarily)

**All set for Production environment?**
- [ ] Yes → Redeploy
- [ ] No → Add missing ones, then redeploy

---

## Step 5: Deploy Backend

**Check files exist:**
- [ ] `api/index.py` exists in repo
- [ ] `requirements.txt` exists in root
- [ ] `vercel.json` exists in root
- [ ] `backend/app/` directory exists

**If missing:**
- Commit and push these files
- Vercel will auto-deploy

**If all exist:**
- Check Vercel function logs for errors
- See TROUBLESHOOTING.md

---

## Step 6: Check Backend Errors

**Vercel Dashboard:**
1. Deployments → Latest
2. Functions → `api/index.py`
3. View logs

**Common errors:**
- `ModuleNotFoundError` → Add to `requirements.txt`
- `DATABASE_URL not found` → Add environment variable
- `Connection refused` → Check database URL/SSL

---

## Quick Test Script

Open browser console on your Vercel app and run:

```javascript
// Test 1: Health check
fetch('/api/healthz')
  .then(r => r.json())
  .then(data => console.log('✅ Backend works:', data))
  .catch(err => console.error('❌ Backend error:', err));

// Test 2: Check API config
console.log('API Base URL:', import.meta.env.VITE_API_BASE_URL || 'default');
console.log('Mock Mode:', import.meta.env.VITE_USE_MOCK_API);
```

---

## Most Likely Issues (In Order)

1. **Mock mode still on** → Set `VITE_USE_MOCK_API=false`
2. **Backend not deployed** → Check `api/index.py` exists
3. **CORS blocking** → Set `CORS_ALLOW_ALL_ORIGINS=true` temporarily
4. **Missing env vars** → Add `DATABASE_URL`, `OPENAI_API_KEY`, etc.
5. **Wrong API URL** → Frontend calling `localhost` instead of `/api`

---

## Share This Info for Help

1. Result of `/api/healthz` test
2. Browser console error (exact message)
3. Network tab - what URL is being called?
4. Vercel function logs - any errors?
5. Environment variables set? (list which ones)

