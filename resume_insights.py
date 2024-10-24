from typing import List
from llm import send_message, upload_to_gemini
from models import Candidate, JobSkill
import logging
from functools import lru_cache


class ResumeAnalysisError(Exception):
    """Custom exception for resume analysis errors."""
    pass


class ResumeInsights:
    def __init__(self, file_path: str):
        """
        Initialize ResumeInsights with a resume file.

        Args:
            file_path (str): Path to the resume file

        Raises:
            ResumeAnalysisError: If file upload fails
        """
        try:
            self.resume = upload_to_gemini(file_path)
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
        except Exception as e:
            raise ResumeAnalysisError(f"Failed to upload resume: {str(e)}")

    # Added caching for extract_candidate_data using @lru_cache
    @lru_cache(maxsize=1)
    def extract_candidate_data(self) -> Candidate:
        """
        Extracts candidate data from the resume using schema-based parsing.

        Returns:
            Candidate: Structured candidate data

        Raises:
            ResumeAnalysisError: If extraction or validation fails
        """
        try:
            output_schema = Candidate.model_json_schema()

            prompt = self._build_extraction_prompt(output_schema)
            self.logger.info("Sending extraction prompt to LLM")

            output = send_message(prompt, [self.resume])
            self.logger.debug(f"Raw LLM output: {output}")

            return Candidate.model_validate_json(output)

        except Exception as e:
            self.logger.error(f"Extraction failed: {str(e)}")
            raise ResumeAnalysisError(f"Failed to extract candidate data: {str(e)}")

    def match_job_to_skills(
        self, skills: List[str], job_position: str, company: str
    ) -> JobSkill:
        """
        Analyzes how candidate skills match a specific job position.

        Args:
            skills (List[str]): List of candidate skills
            job_position (str): Target job position
            company (str): Company name

        Returns:
            JobSkill: Structured skill matching analysis

        Raises:
            ResumeAnalysisError: If skill matching fails
        """
        try:
            if not skills or not job_position or not company:
                raise ValueError("Skills, job position and company are required")

            prompt = self._build_skills_analysis_prompt(skills, job_position, company)
            self.logger.info(f"Analyzing skills match for {job_position} at {company}")

            output = send_message(prompt, [self.resume])
            return JobSkill.model_validate_json(output)

        except Exception as e:
            self.logger.error(f"Skills matching failed: {str(e)}")
            raise ResumeAnalysisError(f"Failed to match skills to job: {str(e)}")

    def _build_extraction_prompt(self, schema: dict) -> str:
        """Builds the prompt for candidate data extraction."""
        return f"""
        Extract information according to this JSON schema:
        ```json
        {schema}
        ```
        Provide a structured JSON response without markdown formatting.
        Include only the properties defined in the schema.
        """

    def _build_skills_analysis_prompt(
        self, skills: List[str], job_position: str, company: str
    ) -> str:
        """Builds the prompt for skills analysis."""
        skills_prompts = [f"""'{skill}'""" for skill in skills]

        return f"""
        Analyze the following skills relevance to the {job_position} job position at {company}:
        {" ".join(skills_prompts)}

        - Provide a conprenhensive analysis.
        - If not relevant, explicitly state why.
        
        Extract information according to this JSON schema:
        ```json
        {JobSkill.model_json_schema()}
        ```
        
        Provide a structured JSON response without markdown formatting.
        Include only the properties defined in the schema.
        """


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        analyzer = ResumeInsights("resume.pdf")
        candidate = analyzer.extract_candidate_data()
        skills_match = analyzer.match_job_to_skills(
            skills=["Python", "ML"], job_position="Data Scientist", company="TechCorp"
        )
    except ResumeAnalysisError as e:
        logging.error(f"Resume analysis failed: {str(e)}")
