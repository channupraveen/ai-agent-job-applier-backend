#!/usr/bin/env python3
"""
Quick test script to verify resume parsing setup
"""

try:
    import PyPDF2
    print("✅ PyPDF2 is installed")
except ImportError:
    print("❌ PyPDF2 is NOT installed. Run: pip install PyPDF2==3.0.1")
    exit(1)

try:
    from docx import Document
    print("✅ python-docx is installed")
except ImportError:
    print("❌ python-docx is NOT installed. Run: pip install python-docx==1.1.0")
    exit(1)

try:
    from services.resume_service import ResumeService
    print("✅ ResumeService imports successfully")
    
    # Test service initialization
    service = ResumeService()
    print(f"✅ ResumeService initialized with {len(service.technical_skills)} technical skills")
    
except ImportError as e:
    print(f"❌ Cannot import ResumeService: {e}")
    exit(1)

print("\n🎉 All dependencies are installed and working!")
print("\n📝 Next steps:")
print("1. Start the backend: uvicorn app:app --host 127.0.0.1 --port 8000 --reload")
print("2. Test the API: http://127.0.0.1:8000/docs#/")
print("3. Upload your resume using the frontend or API docs")
