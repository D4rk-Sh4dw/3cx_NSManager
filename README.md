# Emergency Service Management System

A web-based system to manage on-call duty rosters with 3CX Call Routing and Microsoft 365 Calendar integration.

## Features
- **Web GUI**: Responsive Calendar view (Next.js + FullCalendar).
- **Scheduling**: Manage on-call duties with conflict detection.
- **Automation**: Automatic 3CX forwarding updates based on time and roster.
- **Integration**:
  - **3CX**: Updates routing to Central Office (Biz Hours) or On-Call Person (Off Hours).
  - **MS Graph**: Snyc rosters to Office 365 Calendars.
- **Audit**: Full audit log of all changes.

## Quick Start

### Prerequisites
- Docker & Docker Compose

### Running the System
```bash
docker-compose up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000/docs](http://localhost:8000/docs)

### Deployment Notes
- **Environment Variables**: Check `docker-compose.yml` for default values. For production, create a `.env` file.
- **3CX Config**: Update `scheduler/main.py` or env vars with your 3CX API keys and extension numbers.
- **Database**: PostgreSQL data is persisted in the `postgres_data` volume.

## Project Structure
- `frontend/`: Next.js Web App
- `backend/`: FastAPI Backend
- `scheduler/`: Python 3CX Automation Service
