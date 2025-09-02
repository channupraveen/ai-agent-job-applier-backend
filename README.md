# AI Agent Job Applier

An intelligent web API that automates job applications using AI. Search jobs, generate personalized cover letters, and track applications from any device - laptop or mobile.

## Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the API server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. Access the API:
   - **API Documentation:** http://localhost:8000/docs
   - **From mobile:** http://YOUR_LAPTOP_IP:8000/docs

## Project Structure

```
ai-agent-job-applier/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── README.md           # This file
├── config.py           # Configuration
└── src/                # Source code
    ├── __init__.py
    └── app.py          # Main application logic
```

## Features

🚀 **Smart Job Search**
- Multi-platform job discovery (LinkedIn, Indeed, etc.)
- AI-powered job matching based on your skills
- Configurable search parameters

🤖 **AI-Powered Automation**
- Personalized cover letter generation
- Resume customization for each application
- Intelligent job relevance scoring

📱 **Cross-Platform Access**
- RESTful API accessible from any device
- Mobile-friendly interface
- Real-time application tracking

📊 **Application Management**
- Track all applications in database
- Monitor application status
- View detailed application history
- Session-based progress tracking

## Next Steps

- Configure job search parameters in `config.py`
- Add job board APIs and scraping logic
- Implement AI resume/cover letter customization
- Set up application tracking database
