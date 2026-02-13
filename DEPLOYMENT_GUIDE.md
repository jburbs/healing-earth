# Deploying healingearthwithtech.com — Step-by-Step

## What's Ready

Your site folder has been prepared with:
- `.gitignore` — excludes database files, archives, and reports (~600MB saved)
- `netlify.toml` — caching config + www→apex redirect
- All post HTML, images, CSS, JS, and search index are ready to deploy

---

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Name it `healing-earth-with-tech` (or whatever you prefer)
3. Set it to **Public** (or Private — Netlify works with both)
4. Do **NOT** check "Add a README" or ".gitignore" (we already have these)
5. Click **Create repository**

## Step 2: Push Your Site to GitHub

Open Terminal on your Mac and run these commands (replace YOUR_USERNAME):

```bash
cd "/path/to/Substack Site Localized"
git add .
git commit -m "Initial commit: Healing Earth with Technology archive site"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/healing-earth-with-tech.git
git push -u origin main
```

> Note: If the push is slow, that's normal — the posts/images folder is ~230MB.
> If you get an auth error, you may need a GitHub Personal Access Token or SSH key.

## Step 3: Deploy on Netlify

1. Go to https://app.netlify.com and sign up / log in (GitHub login is easiest)
2. Click **"Add new site"** → **"Import an existing project"**
3. Choose **GitHub** → authorize Netlify → select your `healing-earth-with-tech` repo
4. Build settings should auto-detect from `netlify.toml`:
   - **Publish directory:** `.` (just a dot)
   - **Build command:** leave blank (no build step needed)
5. Click **Deploy site**
6. Wait ~1-2 minutes — Netlify will give you a random URL like `random-name-123.netlify.app`
7. **Test it!** Make sure the site loads, posts work, search works

## Step 4: Connect Your Domain (GoDaddy → Netlify)

### In Netlify:
1. Go to **Site settings** → **Domain management** → **Add custom domain**
2. Enter `healingearthwithtech.com` and click **Verify** → **Add domain**
3. Netlify will show you the required DNS records

### In GoDaddy:
1. Log into GoDaddy → **My Products** → find `healingearthwithtech.com` → **DNS**
2. **Option A (Recommended): Use Netlify DNS**
   - In Netlify, go to Domain settings → click **Set up Netlify DNS**
   - Netlify will give you 4 nameservers (like `dns1.p01.nsone.net`)
   - In GoDaddy, change the nameservers to those 4 Netlify nameservers
   - This gives Netlify full DNS control and auto-configures everything

3. **Option B: Keep GoDaddy DNS**
   - Add an **A record**: `@` → `75.2.60.5` (Netlify's load balancer)
   - Add a **CNAME record**: `www` → `your-site-name.netlify.app`
   - Delete any existing A records for `@` that conflict

### Enable HTTPS:
- In Netlify → **Domain management** → **HTTPS** → **Verify DNS** → **Provision certificate**
- Netlify provides free SSL via Let's Encrypt

## Step 5: Verify

After DNS propagates (5 min to 48 hours, usually ~15 min with Netlify DNS):
- Visit https://healingearthwithtech.com
- Visit https://www.healingearthwithtech.com (should redirect to apex)
- Test a few post links
- Test search functionality

---

## Future Updates

To update the site, just push to GitHub and Netlify auto-deploys:

```bash
cd "/path/to/Substack Site Localized"
git add .
git commit -m "Update: description of changes"
git push
```
