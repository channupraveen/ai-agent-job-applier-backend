"""
Resume Processing Service
"""

from typing import Dict, List, Optional
import asyncio
import re
import io
from datetime import datetime
import base64

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
            r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?[\d\s\-\.]{7,14}"
        )
        self.linkedin_pattern = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)
        self.github_pattern = re.compile(r"github\.com/[\w\-]+", re.IGNORECASE)

        # Common skills to look for (enhanced list)
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
            # AWS Services
            "EC2",
            "S3",
            "RDS",
            "Lambda",
            "IAM",
            "CloudFormation",
            "ElasticBeanstalk",
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
            # Mobile & Other
            "React Native",
            "Flutter",
            "Ionic",
            "Xamarin",
            "JSON",
            "XML",
            "YAML",
            "WebSocket",
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

            # Always try AI parsing first for better accuracy
            print("Attempting AI parsing for resume extraction...")
            ai_extracted = await self._extract_with_ai(file_content, content_type, text)
            if ai_extracted and ai_extracted.get("name"):
                extracted_data = ai_extracted
                print("AI extraction successful")
            else:
                print("AI extraction failed, using basic regex extraction")
                # Extract information using regex patterns as fallback
                extracted_data = await self._extract_information(text)

            return {
                "success": True,
                "extractedData": extracted_data,
                "confidence": self._calculate_confidence(extracted_data),
                "suggestions": self._generate_suggestions(extracted_data),
            }

        except Exception as e:
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
                    text += page.get_text() + "\n"
                doc.close()

                if text.strip():
                    print(f"PyMuPDF extracted {len(text)} characters")
                    return self._clean_extracted_text(text)
            except Exception as e:
                print(f"PyMuPDF extraction failed: {e}")

        # Method 2: Try PyPDF2
        if PDF_AVAILABLE:
            try:
                print("Trying PyPDF2 extraction...")
                pdf_file = io.BytesIO(file_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        else:
                            # Try alternative extraction method
                            text += str(page.extractText()) + "\n"
                    except Exception as e:
                        print(f"Error extracting page {page_num}: {e}")
                        continue

                if text.strip():
                    print(f"PyPDF2 extracted {len(text)} characters")
                    return self._clean_extracted_text(text)
            except Exception as e:
                print(f"PyPDF2 extraction failed: {e}")

        # Method 3: If both fail, try to parse as text (sometimes PDFs contain plain text)
        try:
            print("Trying plain text extraction...")
            text_attempt = file_content.decode("utf-8", errors="ignore")
            if len(text_attempt) > 100:  # If we got substantial text
                return self._clean_extracted_text(text_attempt)
        except Exception as e:
            print(f"Plain text extraction failed: {e}")

        print("All PDF extraction methods failed")
        return ""

    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove null characters and clean up
        text = text.replace("\x00", "").strip()

        # Remove excessive whitespace
        import re

        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n", text)

        print(f"Cleaned text length: {len(text)} characters")
        print(f"First 200 chars: {text[:200]}")

        return text

    async def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""

    async def _extract_information(self, text: str) -> dict:
        """Extract structured information from resume text"""
        lines = text.split("\n")

        print(f"Processing {len(lines)} lines of text")
        print(f"Sample lines: {lines[:5]}")

        # Extract basic information
        name = self._extract_name(lines)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        linkedin_url = self._extract_linkedin(text)
        skills = self._extract_skills(text)
        experience_years = self._extract_experience_years(text)
        current_title = self._extract_current_title(lines)

        print(f"Extracted - Name: '{name}', Email: '{email}', Phone: '{phone}'")
        print(
            f"Extracted - Title: '{current_title}', Experience: {experience_years}, Skills: {len(skills)}"
        )

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedinUrl": linkedin_url,
            "currentTitle": current_title,
            "experienceYears": experience_years,
            "skills": skills,
        }

    def _extract_name(self, lines: List[str]) -> str:
        """Extract name from the first few lines"""
        # Combine all text to handle single-line extraction
        full_text = " ".join(lines)

        # Remove invisible Unicode characters
        full_text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", full_text)

        # Look for name patterns at the beginning
        name_patterns = [
            r"^([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)(?=\s+Phone:|\s+Email:|\s+Location:)",
            r"^([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+)(?=\s)",
            r"^([A-Z][A-Z\s]+)(?=\s+Phone:|\s+Email:)",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, full_text)
            if match:
                name = match.group(1).strip()
                # Validate it's actually a name
                if re.match(r"^[A-Za-z\s]+$", name) and 2 <= len(name.split()) <= 4:
                    return name

        # Fallback: look in individual lines
        clean_lines = [line.strip() for line in lines[:5] if line.strip()]
        for line in clean_lines:
            # Remove invisible characters
            line = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", line)
            if (
                line
                and not self.email_pattern.search(line)
                and not self.phone_pattern.search(line)
                and not any(
                    word.lower() in line.lower()
                    for word in ["phone", "email", "location", "address", "summary"]
                )
                and len(line.split()) >= 2
                and len(line.split()) <= 5
                and len(line) > 5
                and len(line) < 50
                and re.match(r"^[A-Za-z\s]+$", line)
            ):
                return line
        return ""

    def _extract_email(self, text: str) -> str:
        """Extract email address"""
        matches = self.email_pattern.findall(text)
        return matches[0] if matches else ""

    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        # Remove invisible Unicode characters
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)

        # Enhanced phone patterns
        phone_patterns = [
            r"Phone:\s*([\+]?[\d\s\-\(\)\.]{7,15})",  # Phone: 8106775767
            r"Phone\s*[:\-]\s*([\+]?[\d\s\-\(\)\.]{7,15})",  # Phone - 8106775767
            r"(?:Mobile|Cell|Tel):\s*([\+]?[\d\s\-\(\)\.]{7,15})",  # Mobile: numbers
            r"(\d{10})",  # Direct 10 digit numbers
            r"([\+]?\d{1,3}[\s\-]?\(?\d{3}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4})",  # International formats
        ]

        for pattern in phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    phone = re.sub(r"[^\d\+\(\)\-\s]", "", match)
                    if len(re.sub(r"[^\d]", "", phone)) >= 7:  # At least 7 digits
                        return phone.strip()
        return ""

    def _extract_linkedin(self, text: str) -> str:
        """Extract LinkedIn URL"""
        matches = self.linkedin_pattern.findall(text)
        return f"https://{matches[0]}" if matches else ""

    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills"""
        found_skills = []
        text_lower = text.lower()

        # Create a set to avoid duplicates
        skills_set = set()

        for skill in self.technical_skills:
            skill_lower = skill.lower()

            # Check for exact match or skill with common variations
            if (
                skill_lower in text_lower
                or f" {skill_lower} " in f" {text_lower} "
                or f"{skill_lower}," in text_lower
                or f"{skill_lower}." in text_lower
                or f"\n{skill_lower}" in text_lower
            ):
                skills_set.add(skill)

        # Sort skills by length (longer matches first) to avoid duplicates
        found_skills = sorted(list(skills_set), key=len, reverse=True)

        # Remove redundant skills (e.g., if both "HTML5" and "HTML" found, keep "HTML5")
        final_skills = []
        for skill in found_skills:
            is_redundant = False
            for existing_skill in final_skills:
                if skill.lower() in existing_skill.lower() and skill != existing_skill:
                    is_redundant = True
                    break
            if not is_redundant:
                final_skills.append(skill)

        return final_skills[:20]  # Limit to top 20 skills

    async def _extract_with_ai(
        self, file_content: bytes, content_type: str, extracted_text: str = ""
    ) -> Optional[dict]:
        """Extract resume information using OpenAI API with actual resume content"""
        if not OPENAI_AVAILABLE:
            print("OpenAI not available for AI extraction")
            return None

        try:
            # Initialize OpenAI client
            from openai import OpenAI
            import os

            # Get API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your_openai_api_key_here":
                print("OpenAI API key not configured")
                return None

            client = OpenAI(api_key=api_key)

            # Use extracted text if available, otherwise try to extract from content
            resume_text = extracted_text.strip()

            # If no readable text was extracted, try basic PDF parsing
            if not resume_text or len(resume_text) < 100:
                print("No readable text found, attempting basic content extraction...")
                try:
                    # Try to decode as text
                    resume_text = file_content.decode("utf-8", errors="ignore")
                    # Clean up common PDF artifacts
                    import re

                    resume_text = re.sub(
                        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]", " ", resume_text
                    )
                    resume_text = re.sub(r"\s+", " ", resume_text)
                except:
                    print("Could not extract any readable text for AI processing")
                    return None

            # Ensure we have meaningful content
            if len(resume_text.strip()) < 50:
                print("Insufficient text content for AI processing")
                return None

            print(f"Processing {len(resume_text)} characters with AI...")
            print(f"Text preview: {resume_text[:200]}...")

            prompt = f"""
            Extract the following information from this resume text and return ONLY a valid JSON object:
            
            {{
                "name": "Full name of the person",
                "email": "Email address",
                "phone": "Phone number (with country code if present)",
                "currentTitle": "Current job title or most recent position",
                "experienceYears": number_of_years_experience,
                "skills": ["comprehensive list of technical skills"],
                "linkedinUrl": "LinkedIn URL if found"
            }}
            
            Resume text:
            {resume_text}
            
            Rules:
            - Return ONLY the JSON object, no other text
            - Extract ALL technical skills mentioned in the resume
            - If a field is not found, use empty string "" or empty array []
            - For experienceYears, calculate from work history or experience mentioned
            - Be thorough and accurate
            
            Return ONLY the JSON object:
            """

            print("Calling OpenAI API...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.1,
            )

            ai_response = response.choices[0].message.content.strip()
            print(f"AI response: {ai_response}")

            # Parse JSON response
            import json

            try:
                extracted_data = json.loads(ai_response)
                print(f"AI successfully extracted: {extracted_data}")
                return extracted_data
            except json.JSONDecodeError:
                # Try to find JSON in response
                import re

                json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                    print(f"AI extracted from regex match: {extracted_data}")
                    return extracted_data
                else:
                    print("Could not parse AI response as JSON")
                    print(f"Raw response: {ai_response}")
                    return None

        except Exception as e:
            print(f"AI extraction error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _extract_experience_years(self, text: str) -> int:
        """Extract years of experience"""
        # Look for patterns like "5 years", "5+ years", "5-7 years"
        experience_patterns = [
            r"(\d+)[\+\-\s]*years?\s+(?:of\s+)?experience",
            r"(\d+)[\+\-\s]*years?\s+in",
            r"(\d+)[\+\-\s]*years?\s+(?:working|developing)",
            r"experience.*?(\d+)[\+\-\s]*years?",
        ]

        years = []
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            years.extend([int(match) for match in matches if match.isdigit()])

        # Return the maximum years found, or estimate based on content
        if years:
            return max(years)

        # Fallback: count job positions or estimate
        job_indicators = len(re.findall(r"\b(19|20)\d{2}\b", text))  # Years (dates)
        return min(job_indicators, 15) if job_indicators > 0 else 0

    def _extract_current_title(self, lines: List[str]) -> str:
        """Extract current job title"""
        # Clean lines
        clean_lines = [line.strip() for line in lines if line.strip()]

        # Look for professional summary section first
        for i, line in enumerate(clean_lines):
            if "professional summary" in line.lower():
                # Check the next few lines for title
                for j in range(i + 1, min(i + 5, len(clean_lines))):
                    next_line = clean_lines[j].lower()
                    if any(
                        title in next_line
                        for title in ["developer", "engineer", "analyst", "manager"]
                    ):
                        return clean_lines[j]

        # Look for common title patterns in first 20 lines
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
            "product manager",
            "designer",
            "architect",
            "consultant",
            "specialist",
            "coordinator",
        ]

        text_content = " ".join(clean_lines[:20]).lower()

        for title in title_indicators:
            if title in text_content:
                # Find the line containing this title
                for line in clean_lines[:20]:
                    if title in line.lower() and len(line) < 100:
                        return line.strip()

        # Fallback: look for lines with key title words
        for line in clean_lines[:15]:
            line_lower = line.lower()
            if (
                any(
                    indicator in line_lower
                    for indicator in ["developer", "engineer", "analyst", "manager"]
                )
                and len(line.split()) <= 6
                and len(line) > 10
            ):
                return line.strip()

        return ""

    def _calculate_confidence(self, data: dict) -> int:
        """Calculate extraction confidence score"""
        score = 0
        total_fields = 7

        if data.get("name"):
            score += 20
        if data.get("email"):
            score += 20
        if data.get("phone"):
            score += 10
        if data.get("linkedinUrl"):
            score += 10
        if data.get("currentTitle"):
            score += 15
        if data.get("experienceYears", 0) > 0:
            score += 15
        if data.get("skills") and len(data.get("skills", [])) > 0:
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
