# Deployment Guide - Multi-Tenant Pebble iCloud Service

This guide walks you through deploying the Pebble iCloud Reminders service as a centralized multi-tenant backend.

## Overview

The service has been upgraded to support multi-tenant deployment where:
- **One server** handles all users
- Users no longer need to self-host
- Fixed backend URL (configured in the Pebble app)
- Production-grade security and scalability

---

## Deployment Options

### Option 1: Railway (Recommended)

**Why Railway?**
- Automatic deployments from GitHub
- Free tier available
- PostgreSQL included
- Automatic SSL/HTTPS
- Easy environment variable management

#### Step-by-Step Railway Deployment

**1. Prepare Secrets**

```bash
cd backend
python3 generate_secrets.py
```

This will output two secret keys. **Copy these** - you'll need them in step 4.

**2. Create Railway Account**
- Go to [railway.app](https://railway.app)
- Sign up with GitHub

**3. Create New Project**
- Click "New Project"
- Select "Deploy from GitHub repo"
- Authorize Railway to access your repository
- Select `pebble-iCloud` repository

**4. Add PostgreSQL Database**
- In your project, click "New"
- Select "Database" → "PostgreSQL"
- Railway will automatically provision a database
- The `DATABASE_URL` environment variable will be auto-set

**5. Configure Environment Variables**

In Railway dashboard, go to your service → "Variables" tab:

```
FLASK_ENV=production
JWT_SECRET_KEY=<paste from generate_secrets.py>
ENCRYPTION_KEY=<paste from generate_secrets.py>
```

**6. Configure Deployment**

Railway should auto-detect your Python app. Verify in "Settings" tab:
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --workers 4 --timeout 60 --bind 0.0.0.0:$PORT`
- Root Directory: `backend`

**7. Deploy**
- Click "Deploy"
- Railway will build and deploy your app
- You'll get a URL like: `https://pebble-icloud-api.up.railway.app`

**8. Update Pebble App**

Edit `pebble-app/src/pkjs/index.js`:

```javascript
var BACKEND_URL = 'https://YOUR-APP.up.railway.app';
```

**9. Verify Deployment**

```bash
curl https://YOUR-APP.up.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "environment": "production",
  "version": "2.0.0"
}
```

---

### Option 2: Fly.io

**1. Install Fly CLI**

```bash
curl -L https://fly.io/install.sh | sh
```

**2. Login**

```bash
fly auth login
```

**3. Create App**

```bash
cd backend
fly launch
```

Follow prompts:
- App name: `pebble-icloud-api`
- Region: Choose closest to you
- PostgreSQL: Yes
- Redis: No

**4. Set Secrets**

```bash
python3 generate_secrets.py  # Copy the output

fly secrets set JWT_SECRET_KEY="<your_jwt_secret>"
fly secrets set ENCRYPTION_KEY="<your_encryption_key>"
fly secrets set FLASK_ENV="production"
```

**5. Deploy**

```bash
fly deploy
```

**6. Get URL**

```bash
fly info
```

Note the URL and update `BACKEND_URL` in PebbleKit JS.

---

### Option 3: Render

**1. Create Account**
- Go to [render.com](https://render.com)
- Sign up with GitHub

**2. New Web Service**
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Configure:
  - Name: `pebble-icloud-api`
  - Environment: Python 3
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn app:app --workers 4 --timeout 60 --bind 0.0.0.0:$PORT`
  - Root Directory: `backend`

**3. Add PostgreSQL**
- In dashboard, click "New +" → "PostgreSQL"
- Link to your web service

**4. Environment Variables**

In your web service → "Environment":
```
FLASK_ENV=production
JWT_SECRET_KEY=<from generate_secrets.py>
ENCRYPTION_KEY=<from generate_secrets.py>
DATABASE_URL=<auto-set by Render>
```

**5. Deploy**
- Render will auto-deploy
- Get URL from dashboard
- Update PebbleKit JS `BACKEND_URL`

---

### Option 4: Heroku

**1. Install Heroku CLI**

```bash
brew install heroku/brew/heroku  # macOS
# or visit: https://devcenter.heroku.com/articles/heroku-cli
```

**2. Login**

```bash
heroku login
```

**3. Create App**

```bash
cd backend
heroku create pebble-icloud-api
```

**4. Add PostgreSQL**

```bash
heroku addons:create heroku-postgresql:mini
```

**5. Set Config Vars**

```bash
python3 generate_secrets.py  # Copy output

heroku config:set FLASK_ENV=production
heroku config:set JWT_SECRET_KEY="<your_secret>"
heroku config:set ENCRYPTION_KEY="<your_key>"
```

**6. Deploy**

```bash
git push heroku main
```

**7. Verify**

```bash
heroku open
# Visit /health endpoint
```

---

## Post-Deployment Steps

### 1. Update Pebble App

Edit `pebble-app/src/pkjs/index.js`:

```javascript
var BACKEND_URL = 'https://your-production-url.com';
```

Rebuild and deploy the Pebble app:

```bash
cd pebble-app
pebble build
pebble install --phone <PHONE_IP>
```

### 2. Test End-to-End

1. **Configure on watch**:
   - Open Pebble app settings
   - Enter username, Apple ID, app-specific password
   - Save

2. **Verify registration**:
   - Watch should show "Logged in"
   - Check server logs for "New user registered"

3. **Test reminders**:
   - Select a list
   - Verify reminders load
   - Complete a reminder
   - Verify in iCloud

### 3. Monitor

**Railway**: Dashboard → Metrics
**Fly.io**: `fly logs`
**Render**: Dashboard → Logs
**Heroku**: `heroku logs --tail`

---

## Security Checklist

Before going live, verify:

- [ ] `JWT_SECRET_KEY` is set to a random value (not default)
- [ ] `ENCRYPTION_KEY` is set to a Fernet key
- [ ] `FLASK_ENV=production`
- [ ] HTTPS is enabled (automatic on Railway/Render/Fly/Heroku)
- [ ] Database backups are enabled
- [ ] Monitoring/alerting is configured
- [ ] Rate limiting is active (automatic in code)
- [ ] `.env` files are in `.gitignore`

---

## Database Migrations

If you need to migrate from SQLite (development) to PostgreSQL (production):

```bash
# Export from SQLite
sqlite3 users.db .dump > backup.sql

# Import to PostgreSQL (adjust connection string)
psql $DATABASE_URL < backup.sql
```

---

## Troubleshooting

### App won't start

**Check environment variables**:
```bash
# Railway: Dashboard → Variables
# Fly.io: fly secrets list
# Render: Dashboard → Environment
# Heroku: heroku config
```

Ensure `JWT_SECRET_KEY` and `ENCRYPTION_KEY` are set.

### Database connection errors

**Verify DATABASE_URL**:
- Railway: Auto-set when PostgreSQL is added
- Fly.io: Check `fly postgres connect`
- Render: Auto-set when linked
- Heroku: Check `heroku config:get DATABASE_URL`

### Watch can't connect

1. **Verify backend URL**:
   ```bash
   curl https://your-app.com/health
   ```

2. **Check PebbleKit JS**:
   - Ensure `BACKEND_URL` matches your deployment
   - Rebuild Pebble app

3. **Check logs** for authentication errors

### 2FA issues

Currently, 2FA is not fully supported. To use this service:
1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Generate an app-specific password
3. Use that instead of your regular Apple password

---

## Scaling

### Performance Optimization

**For 100+ users:**
- Increase Gunicorn workers: `--workers 8`
- Add Redis for rate limiting: `RATELIMIT_STORAGE_URL=redis://...`
- Enable database connection pooling

**For 1000+ users:**
- Consider dedicated PostgreSQL instance
- Add CDN (Cloudflare) in front
- Horizontal scaling (multiple instances)

### Cost Estimates

| Platform | Free Tier | Paid (100 users) | Paid (1000 users) |
|----------|-----------|------------------|-------------------|
| Railway  | $5 credit/mo | ~$10/mo | ~$20/mo |
| Fly.io   | 3 shared VMs | ~$5/mo | ~$15/mo |
| Render   | Free | ~$7/mo | ~$20/mo |
| Heroku   | No free tier | ~$12/mo | ~$25/mo |

---

## Backup Strategy

### Automated Backups

**Railway**: Automatic daily backups (Postgres)
**Fly.io**: `fly postgres backup list`
**Render**: Automatic daily backups
**Heroku**: Enable with `heroku pg:backups:schedule`

### Manual Backup

```bash
# Get DATABASE_URL from your platform
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql
```

---

## Rollback Procedure

If deployment fails:

**Railway**: Dashboard → Deployments → Rollback
**Fly.io**: `fly releases` → `fly deploy --image <previous>`
**Render**: Dashboard → Deploys → Rollback
**Heroku**: `heroku rollback`

---

## Support

For issues:
1. Check logs (see "Monitor" section above)
2. Verify environment variables
3. Test with `/health` endpoint
4. Review GitHub issues

---

## Next Steps

After successful deployment:

1. **Share the app**: Users can install from Pebble appstore (if published)
2. **Monitor usage**: Set up alerts for errors/high traffic
3. **Optimize**: Review logs for slow endpoints
4. **Document**: Keep track of deployment configuration

---

**Congratulations!** You now have a production multi-tenant Pebble iCloud Reminders service.
