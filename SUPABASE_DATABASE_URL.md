# How to Get Supabase DATABASE_URL with SSL

## Step 1: Navigate to Supabase Project Settings

1. Go to: https://supabase.com
2. Sign in to your account
3. Select your project (or create one if you don't have one)

## Step 2: Find Database Connection String

### Option A: Project Settings → Database (Recommended)

1. In your Supabase project dashboard, click **"Settings"** (gear icon in left sidebar)
2. Click **"Database"** in the settings menu
3. Scroll down to **"Connection string"** section
4. You'll see different connection string formats

### Option B: Project Settings → Database → Connection Pooling

1. Go to **Settings** → **Database**
2. Look for **"Connection Pooling"** section
3. This shows connection strings optimized for serverless (better for Vercel!)

## Step 3: Choose the Right Connection String

### For Vercel (Serverless) - Use Connection Pooling:

**Recommended:** Use the **"Connection Pooling"** connection string because:
- ✅ Optimized for serverless functions
- ✅ Better connection management
- ✅ Handles cold starts better

**Format:**
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true&connection_limit=1
```

### For Direct Connection (if pooling doesn't work):

**Format:**
```
postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

## Step 4: Add SSL Parameter

**If the connection string doesn't have `?sslmode=require`:**

### For Connection Pooling URL:
If it looks like:
```
postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true
```

Add `&sslmode=require`:
```
postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres?pgbouncer=true&sslmode=require
```

### For Direct Connection URL:
If it looks like:
```
postgresql://postgres:[pass]@db.[ref].supabase.co:5432/postgres
```

Add `?sslmode=require`:
```
postgresql://postgres:[pass]@db.[ref].supabase.co:5432/postgres?sslmode=require
```

## Step 5: Copy the Full Connection String

1. Click the **"Copy"** button next to the connection string
2. Or manually copy the entire string including the SSL parameter
3. This is what you'll paste into Vercel as `DATABASE_URL`

## Example Connection Strings

### Connection Pooling (Recommended for Vercel):
```
postgresql://postgres.abcdefghijklmnop:your-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true&connection_limit=1&sslmode=require
```

### Direct Connection:
```
postgresql://postgres:your-password@db.abcdefghijklmnop.supabase.co:5432/postgres?sslmode=require
```

## Important Notes

### Connection Pooling vs Direct Connection:

**Connection Pooling (Port 6543):**
- ✅ Better for serverless (Vercel)
- ✅ Handles many concurrent connections
- ✅ Uses PgBouncer
- ✅ More reliable for serverless functions

**Direct Connection (Port 5432):**
- ✅ Direct database access
- ⚠️ Limited concurrent connections
- ⚠️ May have issues with serverless cold starts

### SSL Requirements:

- **Always use `sslmode=require`** for production
- Supabase requires SSL for all connections
- Without SSL, connections will fail

## Step 6: Add to Vercel

1. Go to Vercel Dashboard → Your Project
2. Settings → Environment Variables
3. Find or create `DATABASE_URL`
4. Paste the connection string with `?sslmode=require` (or `&sslmode=require` if URL already has `?`)
5. Make sure it's set for **Production** environment
6. Save
7. Redeploy

## Troubleshooting

### "Connection refused" error:
- Check if you're using the correct port (6543 for pooling, 5432 for direct)
- Verify SSL parameter is included
- Check Supabase project is active

### "SSL required" error:
- Make sure `sslmode=require` is in the connection string
- Check if you're using `&sslmode=require` (with `&`) when URL already has `?`

### "Too many connections" error:
- Use Connection Pooling instead of Direct Connection
- Connection Pooling handles this better

## Quick Checklist

- [ ] Found connection string in Supabase Settings → Database
- [ ] Chose Connection Pooling (recommended) or Direct Connection
- [ ] Added `?sslmode=require` (or `&sslmode=require` if URL has `?`)
- [ ] Copied the full connection string
- [ ] Added to Vercel as `DATABASE_URL`
- [ ] Set for Production environment
- [ ] Redeployed after adding

---

## Visual Guide

**Supabase Dashboard Path:**
```
Project Dashboard
  → Settings (⚙️ icon)
    → Database
      → Connection string
        → [Copy connection string]
```

**Connection Pooling Path:**
```
Project Dashboard
  → Settings
    → Database
      → Connection Pooling
        → [Copy pooled connection string]
```

