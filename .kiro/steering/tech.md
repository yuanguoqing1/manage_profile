# Technology Stack

## Backend
- **Framework**: FastAPI 0.111.0
- **Server**: Uvicorn 0.30.1
- **Database**: SQLModel 0.0.21 (SQLite with SQLAlchemy)
- **Cache/Sessions**: Redis 5.0.7
- **HTTP Client**: httpx 0.27.0
- **Language**: Python 3.x with type hints

## Frontend
- **Framework**: Vue 3.4.27
- **Build Tool**: Vite 4.4.9
- **Language**: JavaScript (ES modules)

## Common Commands

### Backend
```bash
cd backend
python -m venv .venv
source .\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Default: http://localhost:8000

### Frontend
```bash
cd frontend
npm install
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
```
Default: http://localhost:5173

## Environment Variables
- `VITE_API_BASE`: Backend API URL (frontend, default: http://127.0.0.1:8001)
- `TOKEN_EXPIRES_DAYS`: Token expiration (backend, default: 7)
- `REDIS_HOST`: Redis host (backend, default: localhost)
- `REDIS_PORT`: Redis port (backend, default: 6379)
- `REDIS_PASSWORD`: Redis password (backend, optional)
