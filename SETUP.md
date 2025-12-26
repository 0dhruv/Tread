# Indian Stock Market Trading Platform - Setup Guide

## Prerequisites Installation

### 1. Install PostgreSQL

**Windows:**
```powershell
# Download and install from https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE stock_trading;

# Create user (optional)
CREATE USER stock_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE stock_trading TO stock_user;

# Exit
\q
```

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Get Google Gemini API Key (Free)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the API key

### 5. Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings:
   ```env
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/stock_trading
   GOOGLE_API_KEY=your_google_gemini_api_key_here
   ```

### 6. Initialize Database

```bash
python -c "from app.database import init_db; init_db()"
```

### 7. Collect Initial Data

```bash
# Start with a small dataset for testing
python scripts/collect_data.py --stocks 20 --days 90

# This will take a few minutes
# For full dataset (7500+ stocks):
# python scripts/collect_data.py --days 365
```

### 8. Create First User

Start the application first:
```bash
uvicorn main:app --reload
```

Then in another terminal:
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trader@example.com",
    "username": "trader1",
    "password": "SecurePass123",
    "full_name": "Demo Trader"
  }'
```

### 9. Access Application

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### 10. Login and Start Trading

Use the credentials you created:
- Email: `trader@example.com`
- Password: `SecurePass123`

## Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
# Windows:
Get-Service postgresql*

# macOS/Linux:
sudo systemctl status postgresql
```

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### AI Not Working

- Verify `GOOGLE_API_KEY` in `.env`
- Check API quota at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Free tier: 60 requests/minute

### Port Already in Use

```bash
# Change port in .env:
API_PORT=8001

# Or specify in command:
uvicorn main:app --port 8001
```

## Production Deployment

### Using Gunicorn (Linux/macOS)

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using PM2 (Windows/Linux/macOS)

```bash
npm install -g pm2
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name stock-trading
```

### Docker (Optional)

```dockerfile
# Dockerfile (create this)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t stock-trading .
docker run -p 8000:8000 --env-file .env stock-trading
```

## Development Tips

### Enable Debug Mode

In `.env`:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

### Auto-reload on Code Changes

```bash
uvicorn main:app --reload
```

### View Logs

Check `app.log` file for detailed logs.

### Database Migrations (Alembic)

```bash
# Initialize migrations
alembic init migrations

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Performance Tuning

### Database

```sql
-- Add additional indexes if needed
CREATE INDEX idx_market_data_performance ON market_data(stock_id, date DESC);
```

### Increase Worker Processes

In `.env`:
```env
API_WORKERS=8  # Adjust based on CPU cores
```

### Enable Redis Caching

```bash
# Install Redis
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server

# Update .env
REDIS_URL=redis://localhost:6379/0
```

## Scheduled Data Updates

### Linux/macOS (Cron)

```bash
# Edit crontab
crontab -e

# Add job to update prices every 5 minutes during market hours
*/5 9-15 * * 1-5 cd /path/to/app && python scripts/collect_data.py --stocks 100 --days 1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at market open
4. Action: Start program
   - Program: `python`
   - Arguments: `scripts/collect_data.py --stocks 100 --days 1`
   - Start in: `C:\path\to\app`

## Next Steps

1. ✅ Collect more stock data
2. ✅ Create user accounts
3. ✅ Start paper trading
4. ✅ Explore AI insights
5. ✅ Analyze portfolio performance

For issues, check [GitHub Issues](https://github.com/yourusername/repo/issues).
