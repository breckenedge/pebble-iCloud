# Installation Guide

This guide explains how to install the pre-built Pebble iCloud Reminders app on your Pebble watch.

## Quick Install (Recommended)

### Option 1: Download Pre-built `.pbw` File

Every commit to the main branches automatically builds a ready-to-install `.pbw` file.

1. **Go to the [Actions tab](../../actions/workflows/pebble-build.yml)**
2. **Click on the latest successful build**
3. **Scroll down to "Artifacts"**
4. **Download `pebble-icloud-reminders-v2.0.0`** (or latest version)
5. **Extract the `.pbw` file** from the downloaded zip

### Option 2: Download from Releases

For tagged releases:

1. **Go to the [Releases page](../../releases)**
2. **Find the latest release**
3. **Download the `.pbw` file** from the Assets section

## Installing the `.pbw` File

Once you have the `.pbw` file, you have several installation options:

### Method 1: Pebble Mobile App (Easiest)

**iOS:**
1. Email the `.pbw` file to yourself or use AirDrop
2. Open the file on your phone
3. Tap "Share" → "Pebble"
4. The app will install automatically

**Android:**
1. Transfer the `.pbw` file to your phone
2. Open it with the Pebble app
3. The app will install automatically

### Method 2: Command Line (Advanced)

If you have the Pebble SDK installed:

```bash
# Connect your phone to the same network
# Find your phone's IP address (check Pebble app settings)

pebble install --phone <PHONE_IP> pebble-icloud-reminders-v2.0.0.pbw
```

Example:
```bash
pebble install --phone 192.168.1.100 pebble-icloud-reminders-v2.0.0.pbw
```

### Method 3: Rebble Web Interface

1. Go to [Rebble's side-loading page](https://apps.rebble.io/en_US/developer)
2. Log in with your Rebble account
3. Upload the `.pbw` file
4. The app will sync to your watch

## Automated Builds

This repository uses GitHub Actions to automatically build the Pebble app whenever changes are pushed.

### When Builds Trigger

- ✅ **On Push** to `main`, `master`, or `claude/**` branches
- ✅ **On Pull Request** to any branch
- ✅ **Manual trigger** via the Actions tab

### What Gets Built

Each successful build produces:

1. **`.pbw` file** - Ready-to-install Pebble bundle
   - Retention: 90 days
   - Artifact name: `pebble-icloud-reminders-v{version}`

2. **Full build output** - Complete build directory
   - Retention: 30 days
   - Artifact name: `pebble-build-output-v{version}`

### Accessing Build Artifacts

1. Navigate to the [Actions tab](../../actions)
2. Click on a successful workflow run
3. Scroll to the bottom to see "Artifacts"
4. Download the artifact you need

## Creating a Release

To create a GitHub Release with the `.pbw` file:

1. **Tag your commit:**
   ```bash
   git tag v2.0.0
   git push origin v2.0.0
   ```

2. **The workflow will automatically:**
   - Build the `.pbw` file
   - Create a GitHub Release
   - Attach the `.pbw` to the release
   - Generate release notes

3. **Users can download** directly from the Releases page

## Configuration After Installation

After installing the app:

1. **Open the Pebble mobile app**
2. **Go to Settings → iCloud Reminders**
3. **Configure:**
   - Backend Server URL (your Flask server)
   - Username
   - Apple ID
   - App-Specific Password

See the [main README](./pebble-app/README.md) for detailed configuration instructions.

## Troubleshooting

### "Build failed" in GitHub Actions

Check the workflow logs:
1. Go to Actions tab
2. Click on the failed workflow
3. Expand the failed step to see error details

Common issues:
- SDK download timeout → Retry the workflow
- Missing dependencies → Update the workflow file
- Build errors → Check your code changes

### ".pbw file won't install"

- Ensure the Pebble app is updated
- Check that your watch firmware is compatible
- Try reinstalling the Pebble mobile app

### "App crashes on launch"

- Check Pebble logs: `pebble logs`
- Verify the backend server is accessible
- Check your configuration settings

## Building from Source

If you prefer to build manually:

```bash
cd pebble-app

# Clean previous builds
pebble clean

# Build the app
pebble build

# The .pbw file will be in build/
ls build/*.pbw
```

## Support

For issues:
- Check [Troubleshooting](./pebble-app/README.md#troubleshooting) in the main README
- Review [GitHub Issues](../../issues)
- Check the [Actions logs](../../actions) for build problems
