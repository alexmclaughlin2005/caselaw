# Quick Start Guide

## Docker Not Found?

If Docker commands aren't working, follow these steps:

### Step 1: Start Docker Desktop

1. **Open Docker Desktop** from Applications or Spotlight
2. **Wait for Docker to fully start** - Look for the Docker whale icon in your menu bar
3. **Verify Docker is running** - The icon should be steady (not animated)

### Step 2: Add Docker to PATH (if needed)

If Docker Desktop is running but commands still don't work, add Docker to your PATH:

**For zsh (default on newer macOS):**
```bash
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**For bash:**
```bash
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

### Step 3: Start Services

Once Docker is running, use one of these methods:

**Option A: Use the startup script**
```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener"
./start.sh
```

**Option B: Manual commands**
```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener"

# Try newer syntax first
docker compose up -d

# Or older syntax
docker-compose up -d
```

**Option C: Use Docker Desktop Terminal**
1. Open Docker Desktop
2. Click the terminal icon or use Docker Desktop's integrated terminal
3. Navigate to the project directory
4. Run: `docker compose up -d`

### Step 4: Verify Services

```bash
# Check status
docker compose ps

# View logs
docker compose logs -f

# Check specific service
docker compose logs frontend
docker compose logs backend
```

### Step 5: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## Troubleshooting

### "Cannot connect to Docker daemon"
- Docker Desktop is not running
- Start Docker Desktop and wait for it to fully initialize

### "Port already in use"
- Another application is using port 3000 or 8001
- Check: `lsof -i :3000` or `lsof -i :8001`
- Kill the process or change ports in `.env`

### "Permission denied"
- Docker Desktop may need permission to access the project directory
- Go to Docker Desktop → Settings → Resources → File Sharing
- Add: `/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener`

## Still Having Issues?

1. **Restart Docker Desktop** completely
2. **Check Docker Desktop is running**: Look for whale icon in menu bar
3. **Try Docker Desktop GUI**: Use the GUI to start containers
4. **Check logs**: `docker compose logs` to see what's happening

