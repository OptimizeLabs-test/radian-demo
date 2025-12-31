# How to Push with Personal Access Token

Since Git isn't prompting for credentials, here are ways to provide your token:

## Option 1: Embed Token in URL (Temporary - Works Immediately)

**Step 1:** Create a Personal Access Token:
1. Go to: https://github.com/settings/tokens (while logged into OptimizeLabs-test account)
2. Click "Generate new token (classic)"
3. Name it: "vercel-push"
4. Select scope: `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)

**Step 2:** Update the remote URL with your token:
```powershell
git remote set-url company https://YOUR_USERNAME:YOUR_TOKEN@github.com/OptimizeLabs-test/radian-mvp.git
```

Replace:
- `YOUR_USERNAME` with your OptimizeLabs-test GitHub username
- `YOUR_TOKEN` with the token you just created

**Step 3:** Push:
```powershell
git push company master
```

**Step 4:** Remove token from URL (for security):
```powershell
git remote set-url company https://github.com/OptimizeLabs-test/radian-mvp.git
```

---

## Option 2: Use Git Credential Helper (More Secure)

**Step 1:** Clear cached credentials:
```powershell
git credential-manager-core erase
```

When prompted, enter:
- protocol: `https`
- host: `github.com`
- path: `OptimizeLabs-test/radian-mvp.git`

**Step 2:** Try pushing again:
```powershell
git push company master
```

It should now prompt for:
- Username: Your OptimizeLabs-test GitHub username
- Password: Your Personal Access Token

---

## Option 3: Check if Repository Exists

The "Repository not found" error might mean:
1. Repository doesn't exist
2. You don't have access
3. Repository name is wrong

**Verify:**
1. Go to: https://github.com/OptimizeLabs-test/radian-mvp
2. Can you see the repository?
3. Do you have write access?

**If repository doesn't exist:**
1. Go to: https://github.com/organizations/OptimizeLabs-test/repositories/new
2. Create repository: `radian-mvp`
3. Make it private (if needed)
4. Don't initialize with README
5. Create repository
6. Then try pushing again

---

## Option 4: Use SSH Instead

**Step 1:** Set up SSH key (if not already):
```powershell
ssh-keygen -t ed25519 -C "your-email@example.com"
```

**Step 2:** Add SSH key to GitHub:
1. Copy public key: `cat ~/.ssh/id_ed25519.pub`
2. Go to: https://github.com/settings/keys
3. Click "New SSH key"
4. Paste the key and save

**Step 3:** Change remote to SSH:
```powershell
git remote set-url company git@github.com:OptimizeLabs-test/radian-mvp.git
```

**Step 4:** Push:
```powershell
git push company master
```

---

## Quick Fix (Recommended)

**Fastest way to push right now:**

1. Create Personal Access Token (see Option 1, Step 1)
2. Run this command (replace YOUR_USERNAME and YOUR_TOKEN):
```powershell
git remote set-url company https://YOUR_USERNAME:YOUR_TOKEN@github.com/OptimizeLabs-test/radian-mvp.git
git push company master
git remote set-url company https://github.com/OptimizeLabs-test/radian-mvp.git
```

This embeds the token temporarily, pushes, then removes it.

---

## Troubleshooting

**Still getting "Repository not found"?**

1. Verify repository exists: https://github.com/OptimizeLabs-test/radian-mvp
2. Check you're logged into the correct GitHub account
3. Verify you have write access to the repository
4. Try creating the repository if it doesn't exist

**Token not working?**

1. Make sure token has `repo` scope
2. Check token hasn't expired
3. Verify you're using the token (not password) when prompted


