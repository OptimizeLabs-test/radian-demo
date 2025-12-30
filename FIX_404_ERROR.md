# Fix 404 Error - Backend Not Found

## Problem
Getting `404: NOT_FOUND` when accessing `/api/healthz` means Vercel isn't recognizing your Python serverless function.

## Solutions Applied

### 1. Fixed Function Export
- Updated `api/index.py` to properly export the handler
- Vercel needs the handler to be accessible

### 2. Added Route Configuration
- Added explicit route in `vercel.json` to map `/api/*` to the function

### 3. DATABASE_URL SSL Fix

**IMPORTANT:** Your `DATABASE_URL` needs SSL parameters for production.

**Current (insecure):**
```
postgresql://user:pass@host:port/db
```

**Should be:**
```
postgresql://user:pass@host:port/db?sslmode=require
```

**How to fix:**
1. Go to Vercel → Settings → Environment Variables
2. Find `DATABASE_URL`
3. Edit it to add `?sslmode=require` at the end
4. Save
5. Redeploy

---

## Next Steps

### Step 1: Update DATABASE_URL

1. Vercel Dashboard → Your Project
2. Settings → Environment Variables
3. Find `DATABASE_URL`
4. Click Edit
5. Add `?sslmode=require` to the end:
   - If it ends with `/db`, change to `/db?sslmode=require`
   - If it already has `?`, change to `&sslmode=require`
6. Save

### Step 2: Commit and Push Changes

The `vercel.json` and `api/index.py` files have been updated. Commit and push:

```bash
git add vercel.json api/index.py
git commit -m "Fix Vercel serverless function routing"
git push company master
```

### Step 3: Wait for Deployment

1. Vercel will automatically detect the push
2. Wait for deployment to complete (1-3 minutes)
3. Check deployment logs for any errors

### Step 4: Test Again

After deployment completes:

1. Visit: `https://your-app.vercel.app/api/healthz`
2. Should return: `{"status":"ok"}`

### Step 5: Check Function Logs

If still getting 404:

1. Vercel Dashboard → Deployments → Latest
2. Click "Functions" tab
3. Look for `api/index.py`
4. If it's missing, the function isn't being detected
5. Check build logs for Python/import errors

---

## Alternative: Check if Function is Detected

1. Vercel Dashboard → Your Project
2. Settings → Functions
3. Look for `api/index.py` in the list
4. If not there, Vercel isn't detecting it

**Possible reasons:**
- File not in repository
- Wrong file path
- Python runtime not configured

---

## Verification Checklist

After making changes:

- [ ] `api/index.py` exists in repository
- [ ] `vercel.json` has function configuration
- [ ] `requirements.txt` exists in root
- [ ] `DATABASE_URL` includes `?sslmode=require`
- [ ] Changes committed and pushed
- [ ] Deployment completed successfully
- [ ] `/api/healthz` returns `{"status":"ok"}`

---

## If Still Not Working

**Check these:**

1. **File structure:**
   ```
   /
   ├── api/
   │   └── index.py    ← Must exist
   ├── backend/
   │   └── app/        ← Must exist
   ├── requirements.txt
   └── vercel.json
   ```

2. **Vercel build logs:**
   - Look for "Installing Python dependencies"
   - Look for "Deploying functions"
   - Check for any errors

3. **Function detection:**
   - Settings → Functions
   - Should see `api/index.py` listed

4. **Try different endpoint:**
   - `/api/` (without path)
   - Should still route to function

---

## Common Issues

### Issue: Function not in Functions list

**Solution:**
- Verify `api/index.py` is committed
- Check file is in root `api/` directory (not `backend/api/`)
- Redeploy

### Issue: Import errors in logs

**Solution:**
- Check `requirements.txt` has all dependencies
- Verify `backend/app/` structure is correct
- Check Python path in `api/index.py`

### Issue: Still 404 after fixes

**Solution:**
- Clear Vercel cache
- Delete and recreate deployment
- Check Vercel project settings → Functions tab

