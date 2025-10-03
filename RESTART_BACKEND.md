# Backend Server Restart Instructions

## The Issue
The uvicorn --reload flag is not picking up code changes. The server is still running old code.

## Solution: Manual Restart Required

### Step 1: Stop the Backend Server
1. Go to the terminal/console running the backend
2. Press `Ctrl+C` to stop the server
3. Wait for it to fully shut down

### Step 2: Start the Backend Server
Run one of these commands:

**Option 1 (Recommended):**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 2 (Alternative):**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3 (Windows PowerShell):**
```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify Server Started
You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 4: Test the Fix

1. **Cancel existing pending job** (click Cancel button in UI)

2. **Click "Regenerate All Embeddings"** button

3. **Check backend console** for these lines:
```
[REGENERATE] regenerate_embeddings called: db_alias=analytics_db, metadata_type=all
[REGENERATE] background_tasks type: <class 'fastapi.background.BackgroundTasks'>, is None: False
[REGENERATE] Adding background task for job {uuid}...
[REGENERATE] Background task added successfully via BackgroundTasks for job {uuid}
[REGENERATE] Background task STARTED for job {uuid}...
```

4. **Job should start processing** - status changes to "In Progress" with progress bar

## Why This Happened
- The `--reload` flag uses file watchers that sometimes don't detect changes
- Windows file system events can be delayed
- Multiple rapid edits can confuse the reloader
- Manual restart ensures clean code reload

## Alternative: Check if Server is Running Old Code
If you want to verify the server is running old code before restarting:
```bash
curl -X POST "http://localhost:8000/api/v1/vector-metadata/regenerate-embeddings?db_alias=test&metadata_type=all"
```
- If you see print statements → server has new code
- If no print statements → server needs restart
