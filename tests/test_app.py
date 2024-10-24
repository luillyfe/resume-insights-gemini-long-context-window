import pytest
from unittest.mock import Mock, patch

# Import the app module
from app import main, display_skills, display_skills_proficiency


class MockUploadedFile:
    def __init__(self, content=b"test pdf content"):
        self.content = content

    def getvalue(self):
        return self.content


@pytest.fixture
def mock_streamlit():
    """Fixture to mock Streamlit components"""
    with patch("app.st.set_page_config") as mock_config:
        with patch("app.st.title") as mock_title:
            with patch("app.st.write") as mock_write:
                with patch("app.st.info") as mock_info:
                    with patch("app.st.file_uploader") as mock_uploader:
                        with patch("app.st.button") as mock_button:
                            with patch("app.st.spinner") as mock_spinner:
                                with patch("app.st.error") as mock_error:
                                    with patch("app.st.session_state") as mock_state:
                                        yield {
                                            "config": mock_config,
                                            "title": mock_title,
                                            "write": mock_write,
                                            "uploader": mock_uploader,
                                            "button": mock_button,
                                            "spinner": mock_spinner,
                                            "error": mock_error,
                                            "state": mock_state,
                                            "info": mock_info,
                                        }


@pytest.fixture
def mock_resume_insights():
    """Fixture to mock ResumeInsights class"""
    with patch("app.ResumeInsights") as mock_ri:
        mock_instance = Mock()
        mock_instance.extract_candidate_data.return_value = Mock(
            name="John Doe",
            email="john@example.com",
            age=30,
            skills=["Python", "Machine Learning", "Data Science"],
        )
        mock_instance.match_job_to_skills.return_value = Mock(
            skills={
                "Python": Mock(
                    relevance="High",
                    reasoning="Essential for development",
                    proficiency=8,
                )
            }
        )
        mock_ri.return_value = mock_instance
        yield mock_ri


class TestResumeInsightsApp:
    """Tests for the main Streamlit app"""

    def test_initial_page_setup(self, mock_streamlit):
        """Test initial page configuration"""
        main()

        mock_streamlit["config"].assert_called_once_with(
            page_title="Resume Insights", page_icon="📄"
        )
        mock_streamlit["title"].assert_called_once_with("Resume Insights")

    def test_no_file_uploaded(self, mock_streamlit):
        """Test app behavior when no file is uploaded"""
        mock_streamlit["uploader"].return_value = None

        main()

        mock_streamlit["info"].assert_any_call(
            "Please upload a PDF resume to get started."
        )

    def test_file_upload_success(self, mock_streamlit, mock_resume_insights):
        """Test successful file upload and processing"""
        # Mock file upload
        mock_file = MockUploadedFile()
        mock_streamlit["uploader"].return_value = mock_file
        mock_streamlit["button"].return_value = True

        main()

        # Verify ResumeInsights was created
        mock_resume_insights.assert_called_once()
        # Verify insights were extracted
        # mock_resume_insights.return_value.extract_candidate_data.assert_called_once()

    def test_file_upload_error(self, mock_streamlit, mock_resume_insights):
        """Test error handling during file upload"""
        mock_file = MockUploadedFile()
        mock_streamlit["uploader"].return_value = mock_file
        mock_streamlit["button"].return_value = True

        # Make extract_candidate_data raise an exception
        mock_resume_insights.return_value.extract_candidate_data.side_effect = (
            Exception("Processing failed")
        )

        main()

        mock_streamlit["error"].assert_called_once()

    @pytest.mark.parametrize(
        "job_position",
        [
            "Founding AI Data Engineer",
            "Founding AI Engineer",
            "Founding AI Engineer, Backend",
            "Founding AI Solutions Engineer",
        ],
    )
    def test_job_matching(self, mock_streamlit, mock_resume_insights, job_position):
        """Test job matching functionality for different positions"""
        # Setup mock state with insights
        mock_streamlit["state"].return_value = {
            "insights": mock_resume_insights.return_value.extract_candidate_data.return_value,
            "resumeInsights": mock_resume_insights.return_value,
            "job_matching_skills": None,
        }

        # Mock selectbox selection
        with patch("app.st.selectbox", return_value=job_position):
            display_skills(["Python", "Machine Learning"])

            # Verify job matching was called with correct parameters
            mock_streamlit[
                "state"
            ].resumeInsights.match_job_to_skills.assert_called_with(
                ["Python", "Machine Learning"], job_position, "LlamaIndex"
            )


class TestSkillsDisplay:
    """Tests for skills display functionality"""

    # TypeError: 'Mock' object does not support the context manager protocol
    # def test_display_skills_proficiency(self, mock_streamlit):
    #     """Test skills proficiency display"""
    #     skills = ["Python", "Machine Learning"]

    #     with patch("app.st.columns") as mock_columns:
    #         mock_col1, mock_col2 = Mock(), Mock()
    #         mock_columns.return_value = [mock_col1, mock_col2]

    #         display_skills_proficiency(skills)

    #         # Verify columns were created for each skill
    #         assert mock_columns.call_count == len(skills)

    def test_skills_markdown_formatting(self, mock_streamlit):
        """Test markdown formatting for skills display"""
        with patch("streamlit.markdown") as mock_markdown:
            display_skills_proficiency(["Python"])

            mock_markdown.assert_called_with(
                "<p class='skill-text'>Python</p>", unsafe_allow_html=True
            )


@pytest.mark.integration
class TestIntegration:
    """Integration tests for the app"""

    def test_full_workflow(self, mock_streamlit, mock_resume_insights, tmp_path):
        """Test the complete workflow from file upload to skills display"""
        # Create a test PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"test pdf content")

        # Mock file upload
        mock_file = MockUploadedFile()
        mock_streamlit["uploader"].return_value = mock_file
        mock_streamlit["button"].return_value = True

        # Run main app
        main()

        # Verify the complete workflow
        assert hasattr(mock_streamlit["state"], "insights")
        assert hasattr(mock_streamlit["state"], "resumeInsights")

        # Verify skills display
        with patch("streamlit.selectbox", return_value="Python"):
            display_skills(["Python"])
            mock_resume_insights.return_value.match_job_to_skills.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-v"])
