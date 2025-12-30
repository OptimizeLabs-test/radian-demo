# Fix: api/index.py Not Showing in Vercel

## Problem
Vercel deployment doesn't show `api/index.py` even though it exists in your git repository.

## Solutions

### Solution 1: Verify File is Pushed to Repository

**Check if file is in the remote repository:**

1. Go to: https://github.com/OptimizeLabs-test/radian-mvp
2. Navigate to the `api/` folder
3. Check if `index.py` exists there

**If it's missing:**
- The file wasn't pushed to the company remote
- You need to push it

### Solution 2: Force Vercel to Redeploy

**Option A: Push a New Commit**

1. Make a small change to trigger deployment:
   ```bash
   # Add a comment to api/index.py or touch the file
   git add api/index.py
   git commit -m "Ensure api/index.py is included in deployment"
   git push company master
   ```

**Option B: Manual Redeploy in Vercel**

1. Vercel Dashboard → Your Project
2. Deployments → Latest
3. Click "..." (three dots)
4. Click "Redeploy"
5. This will pull the latest code from GitHub

### Solution 3: Check Vercel Project Settings

**Verify Vercel is connected to the right repository:**

1. Vercel Dashboard → Your Project
2. Settings → Git
3. Verify:
   - Repository: `OptimizeLabs-test/radian-mvp`
   - Production Branch: `master` (or `main`)
   - Root Directory: `./` (should be root)

**If wrong:**
- Disconnect and reconnect the repository
- Or update the settings

### Solution 4: Check Vercel Ignore Files

**Check if there's a `.vercelignore` file:**

1. Look for `.vercelignore` in your repository
2. If it exists, make sure `api/` is NOT in it
3. If `api/` is ignored, remove it from `.vercelignore`

### Solution 5: Verify File Structure in Vercel

**After redeploying, check:**

1. Vercel Dashboard → Your Project
2. Deployments → Latest
3. Click "Source" tab
4. Look for `api/` folder
5. Check if `index.py` is there

**If still missing:**
- Check Vercel build logs for errors
- Verify the file is actually in the GitHub repository
- Try disconnecting and reconnecting the repository

---

## Quick Fix Steps

### Step 1: Verify File is Committed

```bash
git status api/index.py
```

Should show: "nothing to commit" (file is tracked)

### Step 2: Verify File is in Remote

```bash
git ls-remote company -- api/index.py
```

Or check on GitHub directly.

### Step 3: Push if Needed

If file isn't in remote:
```bash
git add api/index.py
git commit -m "Add api/index.py for Vercel serverless function"
git push company master
```

### Step 4: Trigger Vercel Deployment

**Option A:** Wait for auto-deployment (happens on push)

**Option B:** Manual redeploy:
1. Vercel → Deployments → Latest → "..." → Redeploy

### Step 5: Verify Deployment

1. Check Vercel deployment logs
2. Look for "Deploying functions"
3. Check Functions tab shows `api/index.py`

---

## About the Empty Network Tab

The Network tab is empty because:
- **No requests have been made yet**
- You need to **interact with the app** to trigger API calls
- Or **reload the page** to see initial requests

**To see network activity:**

1. **Reload the page** (Ctrl+R or F5)
   - This will show all requests made during page load

2. **Interact with the app:**
   - Click on a patient
   - Try to load patient data
   - Make a chat request
   - These actions will trigger API calls

3. **Check if mock mode is on:**
   - If `VITE_USE_MOCK_API=true`, no network requests will be made
   - The app uses mock data instead
   - Set it to `false` in Vercel to enable real API calls

---

## Complete Checklist

- [ ] `api/index.py` exists locally
- [ ] `api/index.py` is committed to git
- [ ] `api/index.py` is pushed to GitHub (company remote)
- [ ] Vercel is connected to the correct repository
- [ ] Vercel deployment has completed
- [ ] Vercel Functions tab shows `api/index.py`
- [ ] `/api/healthz` returns `{"status":"ok"}` (not 404)
- [ ] `VITE_USE_MOCK_API=false` in Vercel environment variables
- [ ] Network tab shows requests when you interact with the app

---

## Next Steps After Fix

Once `api/index.py` is deployed:

1. **Test backend:**
   - Visit: `https://your-app.vercel.app/api/healthz`
   - Should return: `{"status":"ok"}`

2. **Test frontend:**
   - Reload your app
   - Interact with it (click patient, load data)
   - Check Network tab for API requests
   - Should see requests to `/api/...`

3. **If still getting errors:**
   - Check Vercel function logs
   - Check browser console for errors
   - Verify environment variables are set

