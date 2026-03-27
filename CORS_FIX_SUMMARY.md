# CORS Fix Summary

## Problem
The frontend at `https://healthtrace-fe.vercel.app` was getting CORS errors when trying to access the backend API at `https://healthtrace-j1uc.onrender.com`. The error messages showed:
- "No 'Access-Control-Allow-Origin' header is present on the requested resource"
- 404 (Not Found) errors for API endpoints

## Root Causes
1. **Frontend API URL**: The frontend `.env` file was pointing to `http://localhost:8000` instead of the Render backend URL
2. **CORS Configuration**: The backend CORS settings needed to explicitly allow the Vercel frontend origin

## Changes Made

### 1. Backend CORS Settings (`healthtrace_be/core/settings.py`)
Updated the CORS configuration to be more explicit:
- Set `CORS_ALLOW_ALL_ORIGINS = True` (explicitly)
- Added `https://healthtrace-fe.vercel.app` to `CORS_ALLOWED_ORIGINS` list
- Added explicit `CORS_ALLOW_METHODS` list (GET, POST, PUT, PATCH, DELETE, OPTIONS)
- Added explicit `CORS_ALLOW_HEADERS` list for common headers

### 2. Backend Environment Variables (`healthtrace_be/.env`)
Added `CORS_ALLOWED_ORIGINS` environment variable with the Vercel frontend URL

### 3. Frontend API URL (`healthtrace-fe/.env`)
Updated `VITE_API_URL` from `http://localhost:8000` to `https://healthtrace-j1uc.onrender.com`

## What You Need to Do

### Step 1: Set Vercel Environment Variable
The frontend `.env` file is only used for local development. For the deployed Vercel app, you need to:

1. Go to your Vercel dashboard
2. Select the `healthtrace-fe` project
3. Go to Settings → Environment Variables
4. Add a new environment variable:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://healthtrace-j1uc.onrender.com`
   - **Environment**: Production (and Preview if needed)
5. Redeploy the frontend on Vercel

### Step 2: Redeploy Backend on Render
The backend CORS changes need to be deployed:

1. Commit the changes to your Git repository:
   ```bash
   git add healthtrace_be/core/settings.py
   git add healthtrace_be/.env
   git add healthtrace-fe/.env
   git commit -m "Fix CORS configuration for Vercel frontend"
   git push
   ```

2. If Render is connected to your Git repository, it will auto-deploy
3. Otherwise, manually trigger a deployment in the Render dashboard

### Step 3: Verify the Fix
After both deployments are complete:

1. Open the frontend at `https://healthtrace-fe.vercel.app`
2. Check the browser console for CORS errors
3. Verify that API calls are successful

## API Endpoints Available
Once the fix is deployed, these endpoints will be accessible:

- `GET /api/screenings/` - List all screenings
- `POST /api/screenings/` - Create new screening
- `GET /api/screenings/{id}/` - Get specific screening
- `PUT /api/screenings/{id}/` - Update screening
- `DELETE /api/screenings/{id}/` - Delete screening
- `GET /api/screenings/summary/` - Get statistics
- `GET /api/screenings/notifications/` - Get notifications
- `GET /api/screenings/analytics/` - Get analytics
- `POST /api/screenings/{id}/consult/` - Doctor consultation

## Troubleshooting

If CORS errors persist after deployment:

1. **Check Render logs** for any deployment errors
2. **Verify environment variables** are set correctly on Render:
   - `DJANGO_SECRET_KEY`
   - `DEBUG=False` (for production)
   - `ALLOWED_HOSTS=healthtrace-j1uc.onrender.com,healthtrace-fe.vercel.app`
   - `CORS_ALLOW_ALL_ORIGINS=True`

3. **Test the API directly**:
   ```bash
   curl https://healthtrace-j1uc.onrender.com/api/screenings/
   ```

4. **Check Vercel environment variables**:
   - Ensure `VITE_API_URL` is set to `https://healthtrace-j1uc.onrender.com`
   - Redeploy after setting the variable

## Additional Notes

- The backend uses `django-cors-headers` package for CORS handling
- The middleware is correctly ordered (CorsMiddleware before CommonMiddleware)
- The `.env` file changes are for local development; production uses environment variables set in the hosting platform
