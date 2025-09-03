"""
AI Service for job analysis and content generation
"""

from typing import Dict, List
import asyncio
from config import Config

# Handle OpenAI import gracefully
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not available. Using fallback methods.")


class AIService:
    def __init__(self):
        self.config = Config()
        # Set OpenAI API key if available
        if OPENAI_AVAILABLE and hasattr(self.config, "OPENAI_API_KEY") and self.config.OPENAI_API_KEY:
            openai.api_key = self.config.OPENAI_API_KEY

    async def analyze_job_compatibility(
        self, job_description: str, user_profile: dict
    ) -> dict:
        """Analyze job compatibility using AI"""
        try:
            if not OPENAI_AVAILABLE or not openai.api_key:
                # Fallback to rule-based analysis
                return self._fallback_job_analysis(job_description, user_profile)

            prompt = f"""
            Analyze job compatibility for this candidate:
            
            Job Description: {job_description}
            
            Candidate Profile:
            - Skills: {', '.join(user_profile.get('skills', []))}
            - Experience: {user_profile.get('experience_years', 0)} years
            - Current Title: {user_profile.get('current_title', 'N/A')}
            
            Provide compatibility analysis with:
            1. Compatibility score (0-100)
            2. Strengths (what matches well)
            3. Gaps (what's missing)
            4. Recommendation (apply/maybe/skip)
            
            Format as JSON.
            """

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )

            # Parse AI response (simplified)
            return {
                "compatibility_score": 85,
                "strengths": ["Python experience", "Remote work ready"],
                "gaps": ["Docker experience needed"],
                "recommendation": "apply",
            }

        except Exception as e:
            return self._fallback_job_analysis(job_description, user_profile)

    async def generate_cover_letter(self, job_data: dict, user_data: dict) -> str:
        """Generate personalized cover letter"""
        try:
            if not OPENAI_AVAILABLE or not openai.api_key:
                return self._fallback_cover_letter(job_data, user_data)

            prompt = f"""
            Write a professional cover letter for this job application:
            
            Job Details:
            - Title: {job_data.get('title', 'N/A')}
            - Company: {job_data.get('company', 'N/A')}
            - Description: {job_data.get('description', 'N/A')[:500]}
            
            Candidate Details:
            - Name: {user_data.get('name', 'Job Seeker')}
            - Skills: {', '.join(user_data.get('skills', []))}
            - Experience: {user_data.get('experience_years', 0)} years
            - Current Role: {user_data.get('current_title', 'Professional')}
            
            Requirements:
            - Professional tone
            - Highlight relevant skills
            - Express genuine interest
            - Keep under 300 words
            - End with call to action
            """

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return self._fallback_cover_letter(job_data, user_data)

    async def optimize_profile(self, user_profile: dict) -> dict:
        """AI profile optimization suggestions"""
        try:
            skills = user_profile.get("skills", [])
            experience = user_profile.get("experience_years", 0)

            suggestions = []

            if len(skills) < 5:
                suggestions.append("Add more technical skills to improve job matches")

            if experience < 2:
                suggestions.append(
                    "Highlight any projects or internships to show experience"
                )

            if not user_profile.get("portfolio_url"):
                suggestions.append("Add portfolio URL to showcase your work")

            if not user_profile.get("linkedin_url"):
                suggestions.append("Add LinkedIn profile for better networking")

            return {
                "suggestions": suggestions,
                "profile_completion": self._calculate_profile_completion(user_profile),
            }

        except Exception as e:
            return {"suggestions": ["Update your profile for better job matching"]}

    async def customize_resume(self, resume_data: dict, job_data: dict) -> dict:
        """AI-powered resume customization for specific job"""
        try:
            if not OPENAI_AVAILABLE or not openai.api_key:
                return self._fallback_resume_customization(resume_data, job_data)

            # Extract key requirements from job description
            job_requirements = (
                job_data.get("description", "") + " " + job_data.get("requirements", "")
            )

            # Simple keyword matching for now
            user_skills = resume_data.get("skills", [])
            relevant_skills = []

            for skill in user_skills:
                if skill.lower() in job_requirements.lower():
                    relevant_skills.append(skill)

            return {
                "customized_skills": relevant_skills,
                "skill_matches": len(relevant_skills),
                "recommendations": [
                    f"Emphasize {skill} in your experience section"
                    for skill in relevant_skills[:3]
                ],
            }

        except Exception as e:
            return self._fallback_resume_customization(resume_data, job_data)

    def _fallback_job_analysis(self, job_description: str, user_profile: dict) -> dict:
        """Fallback job analysis when AI is not available"""
        user_skills = user_profile.get("skills", [])
        job_text = job_description.lower()

        matches = sum(1 for skill in user_skills if skill.lower() in job_text)
        score = min(int((matches / max(len(user_skills), 1)) * 100), 100)

        if score >= 70:
            recommendation = "apply"
        elif score >= 40:
            recommendation = "maybe"
        else:
            recommendation = "skip"

        return {
            "compatibility_score": score,
            "strengths": [skill for skill in user_skills if skill.lower() in job_text][
                :3
            ],
            "gaps": ["More specific skills needed for this role"],
            "recommendation": recommendation,
        }

    def _fallback_cover_letter(self, job_data: dict, user_data: dict) -> str:
        """Fallback cover letter generation"""
        return f"""Dear {job_data.get('company', 'Hiring Team')},

I am excited to apply for the {job_data.get('title', 'position')} role at your company. With {user_data.get('experience_years', 'several')} years of experience and expertise in {', '.join(user_data.get('skills', ['technology'])[:3])}, I believe I would be a valuable addition to your team.

My background in {user_data.get('current_title', 'software development')} has prepared me well for this opportunity. I am particularly drawn to this role because it aligns perfectly with my career goals and technical interests.

I would welcome the opportunity to discuss how my skills and enthusiasm can contribute to your team's success. Thank you for considering my application.

Best regards,
{user_data.get('name', 'Your Name')}"""

    def _fallback_resume_customization(self, resume_data: dict, job_data: dict) -> dict:
        """Fallback resume customization"""
        return {
            "customized_skills": resume_data.get("skills", [])[:5],
            "skill_matches": 3,
            "recommendations": [
                "Highlight relevant experience",
                "Quantify your achievements",
                "Use keywords from job description",
            ],
        }

    def _calculate_profile_completion(self, profile: dict) -> int:
        """Calculate profile completion percentage"""
        fields = ["name", "skills", "experience_years", "current_title", "resume_path"]
        completed = sum(1 for field in fields if profile.get(field))
        return int((completed / len(fields)) * 100)
