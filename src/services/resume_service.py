"""
Enhanced Resume Processing Service with Better PDF Parsing and Education Extraction
"""

from typing import Dict, List, Optional, Any
import asyncio
import re
import io
from datetime import datetime
import base64
import json

# Handle PDF/DOCX imports gracefully
try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Handle OpenAI import gracefully
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not available. Using fallback methods.")


class ResumeService:
    def __init__(self):
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        self.phone_pattern = re.compile(
            r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?[\d\s\-\.]{7,14}"
        )
        self.linkedin_pattern = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)
        self.github_pattern = re.compile(r"github\.com/[\w\-]+", re.IGNORECASE)

        # Enhanced technical skills list
        self.technical_skills = [
            # Frontend Technologies
            "HTML5",
            "HTML",
            "CSS3",
            "CSS",
            "SCSS",
            "SASS",
            "Bootstrap",
            "Bootstrap 5",
            "JavaScript",
            "TypeScript",
            "jQuery",
            "Angular",
            "React",
            "Vue",
            "Vue.js",
            "Next.js",
            "Nuxt.js",
            "Svelte",
            "Ember.js",
            # Backend Technologies
            "Python",
            "Java",
            "C++",
            "C#",
            "PHP",
            "Ruby",
            "Go",
            "Rust",
            "Swift",
            "Kotlin",
            "Node.js",
            "Express",
            "Express.js",
            "Django",
            "Flask",
            "FastAPI",
            "Spring Boot",
            ".NET Core",
            ".NET",
            "ASP.NET",
            "Entity Framework",
            # Databases
            "SQL",
            "MySQL",
            "PostgreSQL",
            "MongoDB",
            "Redis",
            "SQLite",
            "SQL Server",
            "Oracle",
            "DynamoDB",
            "Cassandra",
            "Elasticsearch",
            "Firebase",
            # Cloud & DevOps
            "AWS",
            "Azure",
            "GCP",
            "Google Cloud",
            "Docker",
            "Kubernetes",
            "Jenkins",
            "CI/CD",
            "DevOps",
            "Terraform",
            "Ansible",
            "Chef",
            "Puppet",
            # AWS Services
            "EC2",
            "S3",
            "RDS",
            "Lambda",
            "IAM",
            "CloudFormation",
            "ElasticBeanstalk",
            "CloudWatch",
            "API Gateway",
            "CloudFront",
            # Tools & Others
            "Git",
            "GitHub",
            "GitLab",
            "Bitbucket",
            "Swagger",
            "Postman",
            "Visual Studio Code",
            "SSMS",
            "DBeaver",
            "Jira",
            "TFS",
            "WordPress",
            "WooCommerce",
            "Shopify",
            # Data & AI
            "Machine Learning",
            "AI",
            "Data Science",
            "TensorFlow",
            "PyTorch",
            "Pandas",
            "NumPy",
            "Scikit-learn",
            "Jupyter",
            "Apache Spark",
            # Architecture & Patterns
            "REST API",
            "RESTful",
            "GraphQL",
            "Microservices",
            "MVC",
            "MVVM",
            "Agile",
            "Scrum",
            "Kanban",
            "TDD",
            "BDD",
            "Clean Architecture",
            # Mobile & Other
            "React Native",
            "Flutter",
            "Ionic",
            "Xamarin",
            "JSON",
            "XML",
            "YAML",
            "WebSocket",
            "OAuth",
            "JWT",
            "LDAP",
        ]

        # Education degree patterns
        self.degree_patterns = [
            r"(Bachelor|B\.?[ASE]\.?|B\.?Tech|B\.?Sc\.?|B\.?Com\.?|B\.?A\.?)\s*(?:of|in|degree)?\s*([^,\n\r]+)",
            r"(Master|M\.?[ASE]\.?|M\.?Tech|M\.?Sc\.?|M\.?Com\.?|M\.?B\.?A\.?|MBA)\s*(?:of|in|degree)?\s*([^,\n\r]+)",
            r"(PhD|Ph\.?D\.?|Doctorate|Doctor)\s*(?:of|in)?\s*([^,\n\r]+)",
            r"(Associate|A\.?A\.?|A\.?S\.?)\s*(?:of|in|degree)?\s*([^,\n\r]+)",
            r"(Diploma|Certificate)\s*(?:in|of)?\s*([^,\n\r]+)",
        ]

    async def parse_resume(
        self, file_content: bytes, filename: str, content_type: str
    ) -> dict:
        """Parse resume and extract information"""
        try:
            # Extract text based on file type
            text = ""
            if content_type == "application/pdf":
                text = await self._extract_pdf_text(file_content)
            elif (
                content_type
                in [
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ]
                and DOCX_AVAILABLE
            ):
                text = await self._extract_docx_text(file_content)
            else:
                # Fallback: try to extract as plain text
                try:
                    text = file_content.decode("utf-8", errors="ignore")
                except:
                    text = str(file_content, errors="ignore")

            if not text.strip():
                return {
                    "success": False,
                    "error": "Could not extract text from resume",
                    "extractedData": {},
                }

            print(f"Successfully extracted {len(text)} characters of text")
            print(f"Text sample: {text[:300]}...")

            # Try AI parsing first for better accuracy
            print("Attempting AI parsing for resume extraction...")
            ai_extracted = await self._extract_with_ai(text)

            if ai_extracted and ai_extracted.get("name"):
                extracted_data = ai_extracted
                print("AI extraction successful")
            else:
                print("AI extraction failed, using enhanced regex extraction")
                # Extract information using enhanced regex patterns as fallback
                extracted_data = await self._extract_information(text)

            return {
                "success": True,
                "extractedData": extracted_data,
                "confidence": self._calculate_confidence(extracted_data),
                "suggestions": self._generate_suggestions(extracted_data),
            }

        except Exception as e:
            print(f"Error processing resume: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "error": f"Error processing resume: {str(e)}",
                "extractedData": {},
            }

    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file using multiple methods"""
        text = ""

        # Method 1: Try PyMuPDF (most reliable for complex PDFs)
        if PYMUPDF_AVAILABLE:
            try:
                print("Trying PyMuPDF extraction...")
                doc = fitz.open("pdf", file_content)
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text.strip():
                        text += page_text + "\n"
                doc.close()

                if text.strip() and not text.startswith("%PDF"):
                    print(f"PyMuPDF successfully extracted {len(text)} characters")
                    return self._clean_extracted_text(text)
            except Exception as e:
                print(f"PyMuPDF extraction failed: {e}")

        # Method 2: Try PyPDF2 with enhanced extraction
        if PDF_AVAILABLE:
            try:
                print("Trying PyPDF2 extraction...")
                pdf_file = io.BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text += page_text + "\n"
                    except Exception as e:
                        print(f"Error extracting page {page_num}: {e}")
                        continue

                if text.strip() and not text.startswith("%PDF"):
                    print(f"PyPDF2 successfully extracted {len(text)} characters")
                    return self._clean_extracted_text(text)
            except Exception as e:
                print(f"PyPDF2 extraction failed: {e}")

        print("All PDF extraction methods failed or returned binary data")
        return ""

    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""

        # Remove null characters and clean up
        text = text.replace("\x00", "").replace("\ufffd", "").strip()

        # Remove PDF artifacts and binary data
        if text.startswith("%PDF") or "endobj" in text[:100]:
            print("Detected PDF binary data, cleaning...")
            # Try to extract readable text from PDF artifacts
            lines = text.split("\n")
            clean_lines = []
            for line in lines:
                # Skip lines that look like PDF metadata
                if any(
                    marker in line
                    for marker in ["%PDF", "obj", "endobj", "stream", "endstream"]
                ):
                    continue
                # Keep lines that look like text content
                if (
                    re.match(r"^[A-Za-z0-9\s\.,;:!?\-()]+$", line.strip())
                    and len(line.strip()) > 2
                ):
                    clean_lines.append(line.strip())
            text = "\n".join(clean_lines)

        # Remove excessive whitespace and invisible characters
        text = re.sub(
            r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text
        )  # Remove control characters
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        text = re.sub(r"\n\s*\n+", "\n", text)  # Remove empty lines

        # Validate that we have meaningful text content
        if len(text.strip()) < 50 or not re.search(r"[a-zA-Z]{3,}", text):
            print("Cleaned text appears to be insufficient or corrupted")
            return ""

        print(f"Cleaned text length: {len(text)} characters")
        print(f"First 200 chars: {text[:200]}")

        return text.strip()

    async def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text.strip() + "\n"
            return self._clean_extracted_text(text)
        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""

    async def _extract_information(self, text: str) -> dict:
        """Extract structured information from resume text using enhanced patterns"""

        # Extract basic information
        name = self._extract_name(text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        linkedin_url = self._extract_linkedin(text)
        skills = self._extract_skills(text)
        experience_years = self._extract_experience_years(text)
        current_title = self._extract_current_title(text)
        education = self._extract_education(text)

        print(f"Enhanced Extraction Results:")
        print(f"Name: '{name}'")
        print(f"Email: '{email}'")
        print(f"Phone: '{phone}'")
        print(f"Title: '{current_title}'")
        print(f"Experience: {experience_years} years")
        print(f"Skills: {len(skills)} found - {skills[:5]}...")
        print(f"Education: {len(education)} entries")

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedinUrl": linkedin_url,
            "currentTitle": current_title,
            "experienceYears": experience_years,
            "skills": skills,
            "education": education,
        }

    def _extract_name(self, text: str) -> str:
        """Extract name using multiple strategies"""
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Strategy 1: Look for name at the very beginning
        if lines:
            first_line = lines[0].strip()
            # Clean the first line and check for all caps name like "CHANNU PRAVEEN KUMAR"
            clean_first = re.sub(r"[^\w\s]", " ", first_line).strip()
            words = clean_first.split()

            # Check for all caps name (your resume format)
            if (
                2 <= len(words) <= 4
                and all(word.isupper() and word.isalpha() for word in words)
                and len(clean_first) < 50
            ):
                return clean_first

            # Check for title case name
            if (
                2 <= len(words) <= 4
                and all(word[0].isupper() and word.isalpha() for word in words)
                and len(clean_first) < 50
            ):
                return clean_first

        # Strategy 2: Look for specific name patterns
        name_patterns = [
            r"^([A-Z]{2,}\s+[A-Z]{2,}\s+[A-Z]{2,})",  # All caps like CHANNU PRAVEEN KUMAR
            r"^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",  # Title case
            r"Name:\s*([A-Z][a-zA-Z\s]{6,40})",  # Name: field
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                candidate = match.group(1).strip()
                if self._is_valid_name(candidate):
                    return candidate

        # Strategy 3: Look in first few lines for valid names
        for line in lines[:3]:
            clean_line = re.sub(r"[^\w\s]", " ", line).strip()
            if (
                clean_line
                and not any(
                    keyword in clean_line.lower()
                    for keyword in [
                        "phone",
                        "email",
                        "location",
                        "address",
                        "professional",
                        "summary",
                    ]
                )
                and 2 <= len(clean_line.split()) <= 4
                and self._is_valid_name(clean_line)
            ):
                return clean_line

        return ""

    def _is_valid_name(self, candidate: str) -> bool:
        """Validate if a string looks like a person's name"""
        words = candidate.split()
        return (
            2 <= len(words) <= 4
            and all(len(word) >= 2 for word in words)
            and all(word.isalpha() for word in words)
            and 6 <= len(candidate) <= 50
            and
            # Additional validation for common name patterns
            not any(
                word.lower() in ["phone", "email", "location", "summary"]
                for word in words
            )
        )

    def _extract_email(self, text: str) -> str:
        """Extract email address with enhanced patterns"""
        # Enhanced email pattern
        email_patterns = [
            r"Email:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})",
            r"E-mail:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})",
            r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b",
        ]

        for pattern in email_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        return ""

    def _extract_phone(self, text: str) -> str:
        """Extract phone number with enhanced patterns"""
        phone_patterns = [
            r"Phone:\s*([\+]?[\d\s\-\(\)\.]{7,15})",
            r"Mobile:\s*([\+]?[\d\s\-\(\)\.]{7,15})",
            r"Tel:\s*([\+]?[\d\s\-\(\)\.]{7,15})",
            r"\b(\d{10})\b",  # 10 digit numbers
            r"\b(\+?\d{1,3}[-.]?\s?\(?\d{3,4}\)?[-.]?\s?\d{3,4}[-.]?\s?\d{3,4})\b",
        ]

        for pattern in phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean and validate phone number
                clean_phone = re.sub(r"[^\d\+]", "", match)
                if 7 <= len(clean_phone) <= 15:
                    return match.strip()
        return ""

    def _extract_linkedin(self, text: str) -> str:
        """Extract LinkedIn URL"""
        patterns = [
            r"(linkedin\.com/in/[\w\-]+)",
            r"(www\.linkedin\.com/in/[\w\-]+)",
            r"(https?://(?:www\.)?linkedin\.com/in/[\w\-]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                url = matches[0]
                if not url.startswith("http"):
                    url = f"https://{url}"
                return url
        return ""

    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills with improved matching"""
        found_skills = set()
        text_lower = text.lower()

        # Look for skills section first
        skills_section = ""
        skills_patterns = [
            r"technical\s+skills?[:\-]?\s*(.*?)(?=\n\s*[A-Z]|\n\s*\n|\Z)",
            r"skills?[:\-]?\s*(.*?)(?=\n\s*[A-Z]|\n\s*\n|\Z)",
            r"technologies?[:\-]?\s*(.*?)(?=\n\s*[A-Z]|\n\s*\n|\Z)",
            r"programming\s+languages?[:\-]?\s*(.*?)(?=\n\s*[A-Z]|\n\s*\n|\Z)",
        ]

        for pattern in skills_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                skills_section = match.group(1)
                break

        # If we found a skills section, prioritize it
        search_text = skills_section if skills_section else text_lower

        # Match skills with context awareness - more flexible matching
        for skill in self.technical_skills:
            skill_lower = skill.lower()

            # Exact matches with word boundaries
            patterns = [
                rf"\b{re.escape(skill_lower)}\b",  # Exact word match
                rf"{re.escape(skill_lower)}(?=\s*[,;:\n|])",  # Followed by punctuation or pipe
                rf"(?<=[\s,;:|]){re.escape(skill_lower)}(?=[\s,;:\n|])",  # Surrounded by separators
                rf"(?<=[\s,;:|]){re.escape(skill_lower)}$",  # At end of line
                rf"^{re.escape(skill_lower)}(?=[\s,;:\n|])",  # At start of line
            ]

            for pattern in patterns:
                if re.search(pattern, search_text, re.IGNORECASE):
                    found_skills.add(skill)
                    break

        # Also search in the entire text if skills section was limited
        if len(found_skills) < 5:
            for skill in self.technical_skills:
                skill_lower = skill.lower()
                if re.search(rf"\b{re.escape(skill_lower)}\b", text_lower):
                    found_skills.add(skill)

        # Remove redundant skills (e.g., if both "HTML5" and "HTML" found, keep "HTML5")
        final_skills = []
        sorted_skills = sorted(list(found_skills), key=len, reverse=True)

        for skill in sorted_skills:
            is_redundant = False
            for existing_skill in final_skills:
                if skill.lower() in existing_skill.lower() and skill != existing_skill:
                    is_redundant = True
                    break
            if not is_redundant:
                final_skills.append(skill)

        return final_skills[:25]  # Return top 25 skills

    def _extract_experience_years(self, text: str) -> int:
        """Extract years of experience with improved patterns"""
        experience_patterns = [
            r"(\d+)\+?\s*years?\s+(?:of\s+)?experience",
            r"(\d+)\+?\s*years?\s+(?:in|with|working)",
            r"experience.*?(\d+)\+?\s*years?",
            r"(\d+)\+?\s*years?\s+(?:as|working as)",
            r"with\s+(\d+)\+?\s*years?",
        ]

        years = []
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            years.extend([int(match) for match in matches if match.isdigit()])

        if years:
            return max(years)

        # Fallback: estimate from work history dates
        date_pattern = r"\b(19|20)\d{2}\b"
        years_mentioned = re.findall(date_pattern, text)

        if len(years_mentioned) >= 2:
            unique_years = sorted(set(int(year) for year in years_mentioned))
            if len(unique_years) >= 2:
                return min(unique_years[-1] - unique_years[0], 20)  # Cap at 20 years

        return 0

    def _extract_current_title(self, text: str) -> str:
        """Extract current job title with improved detection"""
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Look in professional summary first
        summary_started = False
        for i, line in enumerate(lines):
            if "professional summary" in line.lower():
                summary_started = True
                continue

            if summary_started and line:
                # Look for job titles in the summary
                title_indicators = [
                    "full stack developer",
                    "frontend developer",
                    "backend developer",
                    "software developer",
                    "software engineer",
                    "web developer",
                    "senior developer",
                    "junior developer",
                    "lead developer",
                    "data analyst",
                    "data scientist",
                    "project manager",
                ]

                line_lower = line.lower()
                for title in title_indicators:
                    if title in line_lower:
                        # Extract the relevant part containing the title
                        sentences = re.split(r"[.!?]", line)
                        for sentence in sentences:
                            if title in sentence.lower():
                                return sentence.strip()
                        return line.strip()

                # Stop after a few lines of summary
                if i > 5:
                    break

        # Look for title patterns in first 10 lines
        title_patterns = [
            r"(Full Stack Developer.*?)(?=\s*\n|\s*\|)",
            r"(.*?Developer.*?)(?=\s*\n|\s*\|)",
            r"(.*?Engineer.*?)(?=\s*\n|\s*\|)",
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text[:1000], re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title.split()) <= 6 and len(title) < 60:
                    return title

        return ""

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information"""
        education_entries = []
        found_degrees = set()  # To avoid duplicates

        # Look for specific education patterns from your resume
        education_patterns = [
            # B.Sc. (Electronics) pattern
            r"(B\.Sc\.)\s*\(([^)]+)\)\s*([A-Z][a-zA-Z\s&,]+(?:College|University|Institute)).*?(\d{4})",
            # General Bachelor patterns
            r"(Bachelor|B\.[A-Za-z]+|B\.Sc|B\.Tech|B\.A)\s*(?:\(([^)]+)\))?\s*([A-Z][a-zA-Z\s&,]+(?:College|University|Institute)).*?(\d{4})",
            # Intermediate pattern
            r"(Intermediate)\s*\(([^)]+)\)\s*([A-Z][a-zA-Z\s&,]+(?:College|University|Institute)).*?(\d{4})",
            # General degree pattern
            r"([A-Z][A-Za-z\.]+)\s*(?:\(([^)]+)\))?\s*([A-Z][a-zA-Z\s&,]+(?:College|University|Institute)).*?(\d{4})",
        ]

        for pattern in education_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                groups = match.groups()
                degree_type = groups[0] if groups[0] else ""
                field_of_study = groups[1] if groups[1] else ""
                institution = groups[2] if groups[2] else ""
                year = groups[3] if groups[3] else ""

                # Clean up the data
                degree_type = degree_type.strip()
                field_of_study = field_of_study.strip() if field_of_study else ""
                institution = (
                    re.sub(r"[^a-zA-Z\s&]+", " ", institution).strip()
                    if institution
                    else ""
                )
                year = year.strip() if year else ""

                # Create a unique key to avoid duplicates
                unique_key = f"{degree_type}-{field_of_study}-{institution}"
                if unique_key not in found_degrees and degree_type:
                    found_degrees.add(unique_key)

                    education_entry = {
                        "degree": (
                            f"{degree_type} ({field_of_study})"
                            if field_of_study
                            else degree_type
                        ),
                        "field_of_study": field_of_study,
                        "institution": institution,
                        "graduation_year": year,
                        "gpa": "",
                    }
                    education_entries.append(education_entry)

        # If no structured education found, try simpler patterns
        if not education_entries:
            simple_patterns = [
                r"(B\.Sc\.|Bachelor|Intermediate|Diploma)\s*[^\n]{1,100}?(\d{4})",
                r"([A-Z][a-z]+)\s+(?:College|University).*?(\d{4})",
            ]

            for pattern in simple_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    degree_info = match.group(1).strip()
                    year = match.group(2) if len(match.groups()) > 1 else ""

                    education_entry = {
                        "degree": degree_info,
                        "field_of_study": "",
                        "institution": "",
                        "graduation_year": year,
                        "gpa": "",
                    }
                    education_entries.append(education_entry)
                    break  # Only take first match to avoid duplicates

        return education_entries[:3]  # Limit to 3 entries to avoid noise

    async def _extract_with_ai(self, text: str) -> Optional[dict]:
        """Extract resume information using OpenAI API"""
        if not OPENAI_AVAILABLE:
            print("OpenAI not available for AI extraction")
            return None

        try:
            from openai import OpenAI
            import os

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your_openai_api_key_here":
                print("OpenAI API key not configured")
                return None

            client = OpenAI(api_key=api_key)

            if len(text.strip()) < 50:
                print("Insufficient text content for AI processing")
                return None

            print(f"Processing {len(text)} characters with AI...")

            prompt = f"""
            Extract the following information from this resume text and return ONLY a valid JSON object:
            
            {{
                "name": "Full name of the person",
                "email": "Email address",
                "phone": "Phone number (clean format)",
                "currentTitle": "Current job title or most recent position",
                "experienceYears": number_of_years_experience,
                "skills": ["comprehensive list of technical skills"],
                "linkedinUrl": "LinkedIn URL if found",
                "education": [
                    {{
                        "degree": "Degree name",
                        "field_of_study": "Field of study",
                        "institution": "Institution name",
                        "graduation_year": "Year",
                        "gpa": "GPA if available"
                    }}
                ]
            }}
            
            Resume text:
            {text}
            
            Rules:
            - Return ONLY the JSON object, no other text
            - Extract ALL technical skills mentioned
            - Include education information if available
            - If a field is not found, use empty string "" or empty array []
            - For experienceYears, calculate from work history
            
            Return ONLY the JSON object:
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1,
            )

            ai_response = response.choices[0].message.content.strip()

            try:
                extracted_data = json.loads(ai_response)
                print(f"AI successfully extracted data")
                return extracted_data
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                    return extracted_data
                else:
                    print("Could not parse AI response as JSON")
                    return None

        except Exception as e:
            print(f"AI extraction error: {e}")
            return None

    def _calculate_confidence(self, data: dict) -> int:
        """Calculate extraction confidence score"""
        score = 0

        if data.get("name"):
            score += 20
        if data.get("email"):
            score += 20
        if data.get("phone"):
            score += 15
        if data.get("linkedinUrl"):
            score += 10
        if data.get("currentTitle"):
            score += 15
        if data.get("experienceYears", 0) > 0:
            score += 10
        if data.get("skills") and len(data.get("skills", [])) > 0:
            score += 10
        if data.get("education") and len(data.get("education", [])) > 0:
            score += 10

        return min(score, 100)

    def _generate_suggestions(self, data: dict) -> List[str]:
        """Generate suggestions based on extracted data"""
        suggestions = []

        if not data.get("name"):
            suggestions.append("Name could not be detected. Please verify.")

        if not data.get("email"):
            suggestions.append("Email address not found. Please add manually.")

        if not data.get("phone"):
            suggestions.append("Phone number not detected. Consider adding it.")

        if not data.get("skills") or len(data.get("skills", [])) < 3:
            suggestions.append(
                "Limited technical skills detected. Review and add more."
            )

        if not data.get("currentTitle"):
            suggestions.append("Current job title unclear. Please verify.")

        if data.get("experienceYears", 0) == 0:
            suggestions.append("Years of experience not clear. Please verify.")

        if not data.get("education") or len(data.get("education", [])) == 0:
            suggestions.append(
                "Education information not detected. Please add manually."
            )

        if not data.get("linkedinUrl"):
            suggestions.append("LinkedIn profile not found. Consider adding it.")

        return suggestions

    async def customize_resume(self, resume_data: dict, job_requirements: str) -> dict:
        """Customize resume for specific job"""
        # TODO: Implement AI resume customization
        await asyncio.sleep(0.5)  # Simulate processing
        return {"customized_resume": "Tailored resume content", "match_score": 90}

    async def generate_resume_versions(
        self, base_resume: dict, target_roles: List[str]
    ) -> List[dict]:
        """Generate multiple resume versions for different roles"""
        # TODO: Implement resume version generation
        return [{"role": role, "resume_id": i} for i, role in enumerate(target_roles)]
