# Why Authentication Issues with Company GitHub?

## The Difference

### Your Personal Account (Works Easily)

**Why it works:**
1. **SSH Keys Set Up**: Your personal account likely has SSH keys configured
   - When you first set up Git, you probably added your SSH key to your personal GitHub account
   - Git uses SSH automatically for `git@github.com:username/repo.git` URLs
   - No password/token needed

2. **Credential Manager Cached**: Windows Credential Manager has your personal account credentials saved
   - Once you entered your credentials once, Windows saved them
   - Git automatically uses them for your personal account

3. **HTTPS with Saved Credentials**: If using HTTPS, your browser or Git might have saved your personal account credentials

### Company Account (Authentication Issues)

**Why it doesn't work:**
1. **No SSH Key for Company Account**: 
   - Your SSH key is associated with your personal GitHub account
   - The company account (OptimizeLabs-test) doesn't have your SSH key
   - Git can't authenticate automatically

2. **Credential Manager Doesn't Have Company Credentials**:
   - Windows Credential Manager only has your personal account saved
   - It doesn't know how to authenticate with the company account
   - Git tries to use saved credentials, fails, but doesn't prompt for new ones

3. **Different Authentication Method Needed**:
   - Company accounts often require Personal Access Tokens (not passwords)
   - Git doesn't know to prompt for a token
   - It just fails silently with "Repository not found"

4. **Repository Might Be Private**:
   - Private repositories require authentication
   - Without proper auth, Git returns "Repository not found" (for security, it doesn't reveal if repo exists)

---

## Why "Repository not found" Instead of "Authentication failed"?

GitHub intentionally returns "Repository not found" for private repositories when:
- You're not authenticated
- Your credentials are wrong
- You don't have access

This is a **security feature** - it doesn't reveal whether the repository exists or not.

---

## Solutions (From Easiest to Most Secure)

### Solution 1: Use Personal Access Token (Easiest - Works Now)

**Why this works:**
- Tokens work with HTTPS URLs
- No SSH key setup needed
- Works immediately

**How:**
1. Create token on company account
2. Embed in URL temporarily
3. Push
4. Remove from URL

**Pros:** Quick, works immediately
**Cons:** Token visible in git config (temporarily)

---

### Solution 2: Set Up SSH Key for Company Account (Recommended)

**Why this works:**
- Same as your personal account setup
- No passwords/tokens needed
- Secure and permanent

**How:**
1. Generate SSH key (or use existing)
2. Add public key to company GitHub account
3. Change remote to use SSH
4. Push works automatically

**Pros:** Secure, permanent, same as personal account
**Cons:** Requires one-time setup

---

### Solution 3: Use GitHub CLI (gh)

**Why this works:**
- Handles authentication automatically
- Works with multiple accounts
- Secure token management

**How:**
1. Install GitHub CLI
2. Run `gh auth login`
3. Select company account
4. Push works

**Pros:** Handles multiple accounts easily
**Cons:** Requires installing GitHub CLI

---

### Solution 4: Configure Git Credential Helper Properly

**Why this works:**
- Makes Git prompt for credentials
- Can save credentials for company account
- Works with HTTPS

**How:**
1. Configure credential helper
2. Git will prompt for username/token
3. Windows will save it for future use

**Pros:** Works with HTTPS, credentials saved
**Cons:** Need to enter token each time (or save it)

---

## Why Your Personal Account Was "Easy"

When you first set up Git, you probably:

1. **Generated SSH key**: `ssh-keygen -t ed25519`
2. **Added to personal GitHub**: Copied public key to GitHub Settings → SSH Keys
3. **Used SSH URL**: `git@github.com:your-username/repo.git`
4. **It just worked**: No passwords, no tokens, no prompts

The company account needs the same setup, but:
- You haven't added your SSH key to the company account
- Or you're using HTTPS which requires tokens
- Or credential manager doesn't have company credentials

---

## Quick Comparison

| Method | Personal Account | Company Account |
|--------|-----------------|-----------------|
| **SSH** | ✅ Key added, works automatically | ❌ Key not added to company account |
| **HTTPS with Password** | ✅ Credentials cached | ❌ GitHub doesn't accept passwords anymore |
| **HTTPS with Token** | ✅ Might have token saved | ❌ No token configured |
| **Credential Manager** | ✅ Has your credentials | ❌ Doesn't have company credentials |

---

## Recommended Solution

**For immediate fix:** Use Personal Access Token (Solution 1)
- Quick, works now
- Gets your code pushed

**For long-term:** Set up SSH key for company account (Solution 2)
- Same experience as personal account
- No tokens needed
- Secure and permanent

---

## How to Set Up SSH for Company Account (Like Personal)

### Step 1: Check if you have SSH key

```powershell
ls ~/.ssh/id_ed25519.pub
# or
ls ~/.ssh/id_rsa.pub
```

### Step 2: If you have one, add it to company account

1. Copy your public key:
   ```powershell
   cat ~/.ssh/id_ed25519.pub
   ```

2. Go to: https://github.com/settings/keys (while logged into OptimizeLabs-test)
3. Click "New SSH key"
4. Paste your public key
5. Save

### Step 3: Change remote to SSH

```powershell
git remote set-url company git@github.com:OptimizeLabs-test/radian-mvp.git
```

### Step 4: Test

```powershell
git push company master
```

Should work without any prompts!

---

## Summary

**Why personal account works:**
- SSH key is set up
- Credentials are cached
- Everything is configured

**Why company account doesn't:**
- No SSH key for company account
- No credentials cached
- Needs authentication setup

**Solution:**
- Quick fix: Use Personal Access Token
- Long-term: Set up SSH key for company account (same as personal)

The authentication isn't harder - it just needs to be set up once, just like you did for your personal account initially!

