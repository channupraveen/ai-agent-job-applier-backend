# Resume Upload API Setup & Testing Instructions

## 🚀 What Was Added/Fixed

### Enhanced Backend Features:
1. **Complete Resume Parsing Service** - Extracts text from PDF/DOCX files
2. **AI-Powered Information Extraction** - Uses regex patterns to extract:
   - Name, Email, Phone
   - Current Job Title
   - Years of Experience  
   - LinkedIn URL
   - Technical Skills (50+ common skills)
3. **Intelligent Profile Updates** - Only updates non-empty fields
4. **Confidence Scoring** - Rates extraction accuracy (0-100%)
5. **Smart Suggestions** - Provides recommendations for missing data

### API Endpoints:
- `POST /api/v1/resume/upload` - Upload & parse resume
- `POST /api/v1/resume/parse-test` - Test parsing without saving
- `GET /api/v1/resume/versions` - List resume versions
- `DELETE /api/v1/resume/{file_id}` - Delete resume

## 📦 Installation Steps

### 1. Install Required Dependencies
```bash
cd C:\Users\pk055\Desktop\ai-agent-job-applier

# Install new dependencies for PDF/DOCX processing
pip install PyPDF2==3.0.1 python-docx==1.1.0

# Or install all requirements
pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
# Make sure you're in the backend directory
cd src

# Start the FastAPI server
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Verify API is Running
Open: http://127.0.0.1:8000/docs#/
You should see the Resume Management endpoints.

## 🧪 Testing the Resume Upload

### Frontend Testing:
1. **Start Frontend**: `ng serve`
2. **Go to Personal Info**: http://localhost:4200/profile/personal-info
3. **Click "Choose Resume File"** - File dialog should open
4. **Select a PDF/DOCX resume**
5. **Check browser console** for debug logs:
   ```
   File upload triggered: [object]
   Selected file: [file details]
   Starting file upload...
   Upload result: [parsed data]
   ```

### API Testing (Using FastAPI Docs):
1. **Go to**: http://127.0.0.1:8000/docs#/
2. **Find**: `POST /api/v1/resume/upload`
3. **Click "Try it out"**
4. **Upload a resume file**
5. **Check response**:

**Expected Success Response**:
```json
{
  "success": true,
  "message": "Resume uploaded and parsed successfully",
  "extractedData": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "currentTitle": "Software Engineer",
    "experienceYears": 5,
    "skills": ["Python", "JavaScript", "React"],
    "linkedinUrl": "https://linkedin.com/in/johndoe"
  },
  "confidence": 85,
  "suggestions": ["Consider adding more skills"],
  "filename": "resume.pdf",
  "user_id": 1
}
```

## 🐛 Troubleshooting

### Common Issues:

1. **"Choose Resume File" button not opening file dialog**
   - Check browser console for errors
   - Verify PrimeNG FileUpload module is imported

2. **"PyPDF2 not found" error**
   ```bash
   pip install PyPDF2==3.0.1
   ```

3. **"python-docx not found" error**
   ```bash
   pip install python-docx==1.1.0
   ```

4. **API returns parsing error**
   - Check file type (only PDF, DOC, DOCX supported)
   - Check file size (max 10MB)
   - Try the test endpoint: `/resume/parse-test`

5. **Frontend not connecting to backend**
   - Verify backend is running on port 8000
   - Check environment.ts has correct apiUrl

### Debug Steps:
1. **Check backend logs** in terminal
2. **Open browser DevTools** → Console tab
3. **Check Network tab** for API calls
4. **Test with Postman** or FastAPI docs

## 📋 Sample Resume Data Extraction

The system can extract:
- ✅ **Names** from document headers
- ✅ **Email addresses** using regex patterns
- ✅ **Phone numbers** in various formats
- ✅ **LinkedIn URLs** and GitHub profiles
- ✅ **Technical skills** from 50+ predefined list
- ✅ **Experience years** from text patterns
- ✅ **Job titles** using keyword matching

## 🎯 Next Steps

1. **Test with your actual resume**
2. **Check extraction accuracy**
3. **Verify data appears in form**
4. **Test theme color integration**
5. **Add more technical skills** to the extraction list if needed

The complete resume upload and parsing functionality is now ready! 🚀
