import pytest
from unittest.mock import patch
import io

from resume_insights import ResumeInsights, ResumeAnalysisError
from models import Candidate, JobSkill


@pytest.fixture
def mock_llm():
    """Fixture for mocking LLM interactions"""
    # Pathc where is being used not where is defined.
    with patch("resume_insights.send_message") as mock_send:
        with patch("resume_insights.upload_to_gemini") as mock_upload:
            # Set up mock responses
            mock_upload.return_value = {
                "file_id": "abc123",
                "content": "mocked_resume_content",
                "mime_type": "application/pdf",
            }
            yield {"send": mock_send, "upload": mock_upload}


@pytest.fixture
def sample_resume_file():
    """Fixture for sample resume file"""
    return io.BytesIO(b"Sample resume content")


@pytest.fixture
def sample_candidate_json():
    """Sample candidate data fixture"""
    return """{
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "skills": ["Python", "Machine Learning", "Data Analysis"],
        "experience": [
            {
                "company": "Tech Corp",
                "position": "Senior Developer",
                "duration": "2 years"
            }
        ],
        "education": [
            {
                "degree": "Masters in Computer Science",
                "institution": "University of Tech",
                "year": 2020
            }
        ]
    }"""


@pytest.fixture
def sample_job_skill_json():
    """Sample job skill analysis fixture"""
    return """{
        "jobName": "Data Scientist",
        "company": "AI Corp",
        "skills": {
            "Python": {
                "relevance": "9",
                "reasoning": "Essential for data analysis and ML tasks"
            }
        }
    }"""


class TestResumeInsights:
    def test_initialization_success(self, mock_llm):
        """Test successful initialization of ResumeInsights"""
        # Test with different file types
        file_paths = ["resume.pdf", "resume.docx", "resume.txt"]

        for file_path in file_paths:
            analyzer = ResumeInsights(file_path)

            # Verify the upload was called with correct file path
            mock_llm["upload"].assert_called_with(file_path)

            # Verify the uploaded content was stored
            assert analyzer.resume["file_id"] == "abc123"
            assert analyzer.resume["content"] == "mocked_resume_content"

            # Reset mock for next iteration
            mock_llm["upload"].reset_mock()

    def test_initialization_with_different_file_sizes(self, mock_llm):
        """Test initialization with different file sizes"""
        # Mock different file size responses
        file_sizes = [
            (1024, True),  # 1KB - should succeed
            (5 * 1024 * 1024, True),  # 5MB - should succeed
            (20 * 1024 * 1024, False),  # 20MB - should fail
        ]

        for size, should_succeed in file_sizes:
            mock_llm["upload"].reset_mock()
            if not should_succeed:
                mock_llm["upload"].side_effect = Exception("File too large")
            else:
                mock_llm["upload"].side_effect = None

            if should_succeed:
                analyzer = ResumeInsights(f"resume_{size}.pdf")
                assert analyzer.resume is not None
            else:
                with pytest.raises(ResumeAnalysisError) as exc_info:
                    ResumeInsights(f"resume_{size}.pdf")
                assert "Failed to upload resume" in str(exc_info.value)

    def test_initialization_failure_cases(self, mock_llm):
        """Test various initialization failure scenarios"""
        error_cases = [
            ("network_error.pdf", Exception("Network timeout"), "Network timeout"),
            (
                "invalid_type.xyz",
                ValueError("Unsupported file type"),
                "Unsupported file type",
            ),
            ("corrupted.pdf", IOError("File corrupted"), "File corrupted"),
            ("", ValueError("Empty file path"), "Empty file path"),
        ]

        for file_path, error, expected_message in error_cases:
            mock_llm["upload"].reset_mock()
            mock_llm["upload"].side_effect = error

            # Uses pytest.raises context manager to expect an `ResumeAnalysisError`
            with pytest.raises(ResumeAnalysisError) as exc_info:
                ResumeInsights(file_path)
            assert expected_message in str(exc_info.value)
            mock_llm["upload"].assert_called_once_with(file_path)

    def test_extract_candidate_data_success(self, mock_llm, sample_candidate_json):
        """Test successful candidate data extraction"""
        mock_llm["send"].return_value = sample_candidate_json
        analyzer = ResumeInsights("dummy.pdf")

        candidate = analyzer.extract_candidate_data()

        assert isinstance(candidate, Candidate)
        assert candidate.name == "John Doe"
        assert len(candidate.skills) == 3
        mock_llm["send"].assert_called_once()

    def test_extract_candidate_data_with_upload_verification(
        self, mock_llm, sample_candidate_json
    ):
        """Test candidate data extraction with upload verification"""
        # Set up the mock responses
        mock_llm["upload"].return_value = {
            "file_id": "abc123",
            "content": "mocked_resume_content",
            "mime_type": "application/pdf",
        }
        mock_llm["send"].return_value = sample_candidate_json

        # Initialize and extract data
        analyzer = ResumeInsights("resume.pdf")
        candidate = analyzer.extract_candidate_data()

        # Verify upload was called correctly
        mock_llm["upload"].assert_called_once_with("resume.pdf")

        # Verify send_message was called with the uploaded content
        mock_llm["send"].assert_called_once()
        args, _ = mock_llm["send"].call_args
        assert len(args) == 2
        assert args[1] == [
            {
                "file_id": "abc123",
                "content": "mocked_resume_content",
                "mime_type": "application/pdf",
            }
        ]
        assert isinstance(candidate, Candidate)

    def test_extract_candidate_data_caching(self, mock_llm, sample_candidate_json):
        """Test that extraction results are properly cached"""
        mock_llm["send"].return_value = sample_candidate_json
        analyzer = ResumeInsights("dummy.pdf")

        # First call
        result1 = analyzer.extract_candidate_data()
        # Second call should use cache
        result2 = analyzer.extract_candidate_data()

        assert result1 == result2
        mock_llm[
            "send"
        ].assert_called_once()  # Should only be called once due to caching

    def test_extract_candidate_data_invalid_response(self, mock_llm):
        """Test handling of invalid LLM response"""
        mock_llm["send"].return_value = {"invalid": "data"}
        analyzer = ResumeInsights("dummy.pdf")

        with pytest.raises(ResumeAnalysisError) as exc_info:
            analyzer.extract_candidate_data()
        assert "Failed to extract candidate data" in str(exc_info.value)

    def test_match_job_to_skills_success(self, mock_llm, sample_job_skill_json):
        """Test successful job skills matching"""
        mock_llm["send"].return_value = sample_job_skill_json
        analyzer = ResumeInsights("dummy.pdf")

        skills = ["Python", "ML"]
        job_position = "Data Scientist"
        company = "AI Corp"

        result = analyzer.match_job_to_skills(skills, job_position, company)

        assert isinstance(result, JobSkill)
        assert result.jobName == "Data Scientist"
        assert len(result.skills) == 1

    @pytest.mark.parametrize(
        "skills,position,company",
        [
            (["Python"], "Data Scientist", ""),
            ([], "Data Scientist", "Company"),
            (["Python"], "", "Company"),
        ],
    )
    def test_match_job_to_skills_invalid_inputs(
        self, mock_llm, skills, position, company
    ):
        """Test job skills matching with various invalid inputs"""
        analyzer = ResumeInsights("dummy.pdf")

        with pytest.raises(ResumeAnalysisError):
            analyzer.match_job_to_skills(skills, position, company)

    def test_prompt_construction(self, mock_llm):
        """Test proper construction of prompts"""
        analyzer = ResumeInsights("dummy.pdf")

        # Test extraction prompt
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        extraction_prompt = analyzer._build_extraction_prompt(schema)
        assert "JSON schema" in extraction_prompt
        assert str(schema) in extraction_prompt

        # Test skills analysis prompt
        skills_prompt = analyzer._build_skills_analysis_prompt(
            ["Python"], "Developer", "Company"
        )
        assert "Python" in skills_prompt
        assert "Developer" in skills_prompt
        assert "Company" in skills_prompt

    @pytest.mark.integration
    def test_end_to_end_workflow(
        self, mock_llm, sample_candidate_json, sample_job_skill_json
    ):
        """Integration test for complete workflow"""
        mock_llm["send"].side_effect = [
            sample_candidate_json,  # For extract_candidate_data
            sample_job_skill_json,  # For match_job_to_skills
        ]

        analyzer = ResumeInsights("dummy.pdf")

        # Extract candidate data
        candidate = analyzer.extract_candidate_data()
        assert isinstance(candidate, Candidate)

        # Match skills to job
        job_match = analyzer.match_job_to_skills(
            candidate.skills, "Data Scientist", "AI Corp"
        )
        assert isinstance(job_match, JobSkill)

        # Verify all expected calls were made
        assert mock_llm["send"].call_count == 2


if __name__ == "__main__":
    pytest.main(["-v"])
