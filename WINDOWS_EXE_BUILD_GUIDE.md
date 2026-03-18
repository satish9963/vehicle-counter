# 🪟 Vehicle Counter - Windows .EXE Installation Guide

## Quick Overview

This guide shows you how to:
1. **Build** the Windows `.exe` installer
2. **Install** on your computer
3. **Run** the application

---

## 📋 Requirements Before Building

### System Requirements
- **OS**: Windows 10 or later (64-bit)
- **Disk Space**: 15GB (5GB for building + 10GB for build output)
- **RAM**: 8GB minimum
- **Internet**: Required for downloading dependencies

### Software Installation (One-time setup)

#### 1. Install Python 3.9+
```
Download: https://www.python.org/downloads/
- Choose Windows installer (64-bit)
- ✅ IMPORTANT: Check "Add Python to PATH" during installation
- Click Install
```

**Verify installation**:
```bash
python --version
# Should show Python 3.9 or higher
```

#### 2. Install Node.js 16+
```
Download: https://nodejs.org/
- Choose "LTS" version (Long Term Support)
- Run installer
- Use default settings
- Click Install
```

**Verify installation**:
```bash
node --version
npm --version
# Should show version numbers
```

#### 3. Install Git (Optional but recommended)
```
Download: https://git-scm.com/download/win
- Run installer with default settings
```

---

## 🔧 Building the .EXE

### Step 1: Extract Project Files

```
1. Extract all 23 files to a folder, e.g.:
   C:\vehicle-counter\
   
2. Your folder should contain:
   - vehicle_counter_backend.py
   - VehicleCounter.jsx
   - package.json
   - setup.bat
   - build-windows-exe.bat
   - (and 17 other files)
```

### Step 2: Run Initial Setup

```bash
# Open Command Prompt in your project folder
# Windows: Shift + Right-click in folder → "Open PowerShell here"

# Run setup
setup.bat

# This will:
# ✓ Create Python virtual environment
# ✓ Install Python packages
# ✓ Download YOLOv8 model
# ✓ Install Node.js packages
# ✓ Create necessary folders

# Wait for completion (10-15 minutes on first run)
```

### Step 3: Build the .EXE

```bash
# After setup completes, run the builder

build-windows-exe.bat

# This will:
# 1. Build React app (npm run build)
# 2. Bundle with Electron
# 3. Create Windows installers
# 4. Generate portable .exe
#
# Wait for completion (5-10 minutes)
```

**What happens during build**:
```
[Progress...]
Building React application...    ✓ (2 min)
Installing Electron...           ✓ (3 min)
Creating installer...            ✓ (3 min)
Building executables...          ✓ (2 min)

[SUCCESS] 
✓ Vehicle Counter Setup 1.0.0.exe (installer)
✓ Vehicle Counter 1.0.0.exe (portable)
```

---

## 📦 Installation Methods

### Method 1: Using the Installer (Recommended)

**File**: `Vehicle Counter Setup 1.0.0.exe`  
**Location**: `dist\` folder  
**Size**: ~500 MB

```
Steps:
1. Open dist folder
2. Double-click "Vehicle Counter Setup 1.0.0.exe"
3. Follow installer wizard:
   ✓ Accept license
   ✓ Choose installation folder (default OK)
   ✓ Create Start Menu shortcut (recommended)
   ✓ Click "Finish"
4. App launches automatically

Time: 2-3 minutes
```

**After Installation**:
- Start Menu shortcut created
- Desktop shortcut (optional)
- Uninstall option in Control Panel
- Can be updated automatically

### Method 2: Portable Executable (No Installation)

**File**: `Vehicle Counter 1.0.0.exe`  
**Location**: `dist\` folder  
**Size**: ~400 MB

```
Steps:
1. Open dist folder
2. Double-click "Vehicle Counter 1.0.0.exe"
3. App launches directly (no installer dialog)

Advantages:
✓ No installation needed
✓ Run from USB drive
✓ No registry changes
✓ Can move anywhere
```

---

## 🚀 First Launch

### What Happens on First Run

```
1. Electron window opens
2. Backend starts automatically (Python FastAPI)
3. Frontend loads (React)
4. App is ready to use in 30-60 seconds

You'll see:
✓ Desktop application window
✓ Upload tab visible
✓ All features ready
```

### If It Doesn't Start

**Check these things**:

```
1. Is Python running in background?
   Task Manager → Look for "python.exe"
   
2. Is port 8000 available?
   netstat -ano | findstr :8000
   If busy, close the process
   
3. Does folder exist?
   C:\vehicle-counter\uploads\ (for uploads)
   
4. Check logs:
   Console window shows error messages
```

---

## 💻 Using the Application

### Basic Workflow

```
1. UPLOAD
   ✓ Click "Browse Files" or drag-drop
   ✓ Select video (MP4, AVI, MOV, MKV)
   ✓ Click "Upload & Continue"

2. PREVIEW (Optional)
   ✓ Watch video preview
   ✓ Check file info

3. PROCESS
   ✓ Set speed (1x-10x)
     - 1x = Slowest, most accurate
     - 10x = Fastest, good accuracy
   ✓ Click "Start Detection"
   ✓ Wait for processing (depends on video length)

4. RESULTS
   ✓ See vehicle count breakdown
   ✓ View accuracy metrics
   ✓ Export as CSV or JSON

5. EXPORT
   ✓ Download report
   ✓ Open in Excel or analysis tool
```

### Example: Processing a 1-Minute Video

```
Speed Factor: 10x

Processing time: ~6 seconds
- Video length: 60 seconds
- At 10x: process 6 frames/second instead of 30
- Results: ~500-1000 vehicles detected
```

---

## 🐛 Troubleshooting

### Issue: "Python not found" or "module not found"

**Solution**:
```
1. Check Python installation:
   python --version
   
2. If not found, reinstall Python:
   - Download from python.org
   - ✓ Check "Add Python to PATH"
   - Run installer
   
3. Reopen Command Prompt after installation
```

### Issue: App won't start

**Solution**:
```
1. Check if port 8000 is available:
   netstat -ano | findstr :8000
   
2. If port busy, kill the process:
   taskkill /PID <process_id> /F
   
3. Try again
```

### Issue: Very slow processing

**Solution**:
```
1. Close other applications
2. Increase speed factor (1x → 5x → 10x)
3. Reduce video resolution before uploading
4. Check GPU (see "GPU Acceleration" below)
```

### Issue: Out of memory

**Solution**:
```
1. Close other applications
2. Restart the app
3. Process smaller videos
4. Use 10x speed factor
```

### Issue: Can't find dist folder with .exe

**Solution**:
```
1. Make sure build completed successfully
   Last message should be "[SUCCESS]"
   
2. Check C:\vehicle-counter\dist\
   
3. If not there, the build may have failed
   Check error messages in console
   
4. Common reasons:
   - Not enough disk space
   - Python/Node not installed correctly
   - Antivirus blocking build process
```

---

## 🎮 GPU Acceleration (Optional but Recommended)

To make processing **3-5x faster**, enable GPU:

### Check if You Have NVIDIA GPU

```bash
# Open Command Prompt
nvidia-smi

# If this shows GPU info, you have NVIDIA GPU
# If not found, you don't have compatible GPU
```

### Enable CUDA Support

```bash
# Only if you have NVIDIA GPU:

# 1. Activate Python environment
venv\Scripts\activate

# 2. Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. Restart the app
# Processing will be 3-5x faster!
```

**Without GPU**: Uses CPU, slower but works fine
**With GPU**: 3-5x faster processing

---

## 📊 Expected Performance

### On Average Windows Machine (No GPU)

```
Video Length    Processing Time (Speed 1x)    Processing Time (Speed 10x)
10 seconds      2-3 minutes                   12-18 seconds
30 seconds      6-9 minutes                   36-54 seconds
1 minute        12-18 minutes                 1-2 minutes
5 minutes       60-90 minutes                 6-9 minutes
```

### With NVIDIA GPU

```
Same videos: 3-5x faster (divide above times by 4)
```

---

## 🔄 Updating the App

### When New Version Released

```
1. Download new files
2. Extract to same folder (overwrite)
3. Run setup.bat again
4. Run build-windows-exe.bat again
5. New .exe files ready in dist/
```

### Or Keep Both Versions

```
1. Create new folder: C:\vehicle-counter-v1.1\
2. Extract new files there
3. Build separately
4. Keep both installed
```

---

## 🗑️ Uninstalling

### If You Used Installer

```
Method 1: Control Panel
1. Settings → Apps → Apps & features
2. Find "Vehicle Counter"
3. Click "Uninstall"
4. Follow uninstaller

Method 2: Add/Remove Programs
1. Control Panel → Programs
2. Find "Vehicle Counter"
3. Click "Uninstall"
```

### If You Used Portable

```
1. Simply delete the .exe file
2. No registry or system changes
3. To remove completely:
   - Delete entire folder C:\vehicle-counter\
```

---

## 📁 File Organization After Build

```
C:\vehicle-counter\
├── node_modules\           (Node.js packages)
├── venv\                   (Python environment)
├── build\                  (React build output)
├── dist\                   ← YOUR .EXE FILES ARE HERE
│  ├── Vehicle Counter Setup 1.0.0.exe    (Installer)
│  ├── Vehicle Counter 1.0.0.exe          (Portable)
│  └── [other build files]
├── src\
├── public\
├── uploads\                (Your video files)
├── results\                (Exported reports)
└── [configuration files]
```

---

## 💡 Pro Tips

### Tip 1: Create Shortcut
```
1. Right-click Vehicle Counter.exe
2. Send to → Desktop (create shortcut)
3. Now easy access from desktop
```

### Tip 2: Run Without Console
```
To hide Python console window:
1. Right-click .exe shortcut
2. Properties → Advanced
3. Run with hidden window option
```

### Tip 3: Batch Processing
```
Process multiple videos:
1. Upload video 1 → Process → Export
2. Upload video 2 → Process → Export
3. Repeat for all videos
```

### Tip 4: Organize Results
```
Create folders for:
/results/traffic-survey-jan/
/results/parking-lot-analysis/
/results/urban-mobility-study/
```

---

## 🆘 Getting Help

### If Build Fails

```
1. Check error message in console
2. Most common issues:
   ✓ Missing Python/Node.js
   ✓ Antivirus blocking build
   ✓ Insufficient disk space
   ✓ Old Node.js version

3. Solutions:
   ✓ Reinstall Python/Node.js
   ✓ Temporarily disable antivirus during build
   ✓ Free up disk space (need 15GB)
   ✓ Update Node.js to latest LTS
```

### If App Crashes

```
1. Check console for error message
2. Most common causes:
   ✓ Port 8000 already in use
   ✓ Python not in PATH
   ✓ Missing YOLOv8 model
   ✓ Corrupted video file

3. Troubleshoot:
   ✓ Change port in code
   ✓ Reinstall Python
   ✓ Rerun setup.bat
   ✓ Try different video
```

---

## 📧 Support Resources

### Included Documentation
- README.md - Complete guide
- SETUP_GUIDE.md - Detailed setup
- IMPLEMENTATION_GUIDE.md - Quick start

### External Resources
- YOLOv8: https://docs.ultralytics.com/
- Electron: https://www.electronjs.org/
- FastAPI: https://fastapi.tiangolo.com/

---

## ✅ Build Verification Checklist

Before claiming success:
- [ ] setup.bat completed successfully
- [ ] No error messages in console
- [ ] build-windows-exe.bat completed
- [ ] dist/ folder has both .exe files
- [ ] File sizes are reasonable (>300 MB each)
- [ ] Double-click .exe and app launches
- [ ] Can upload and process test video
- [ ] Can export results

---

## 🎉 You're Ready!

Once you have the .exe files:
1. Send them to others (or upload to website)
2. No installation by others needed (if using portable)
3. Or they install using installer exe
4. Everyone can use the app!

---

**Total Build Time**: 15-25 minutes (first time)  
**Result**: Two ready-to-use Windows applications  

Let's build it! 🚀

---

*Vehicle Counter v1.0.0 - Windows .EXE Build Guide*
