import pytest
from unittest.mock import Mock, patch
import os
import tempfile

# Import the functions to test
from llm import send_message, upload_to_gemini


@pytest.fixture
def mock_genai():
    """Fixture to mock the entire genai module"""
    # Mock 'llm.genai' because what matters in mocking is how is used not how is defined!
    with patch("llm.genai") as mock_gen:
        # Mock the configure method
        mock_gen.configure = Mock()

        # Create a mock response
        mock_response = Mock()
        mock_response.text = '{"response": "test response"}'

        # Mock the chat session
        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response

        # Mock the GenerativeModel
        mock_model = Mock()
        mock_model.start_chat.return_value = mock_chat
        mock_gen.GenerativeModel.return_value = mock_model

        yield mock_gen


@pytest.fixture
def mock_file():
    """Fixture to create a temporary test file"""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"Test content")
        tmp.flush()
        yield tmp.name
    # Cleanup after test
    os.unlink(tmp.name)


@pytest.fixture
def mock_upload_response():
    """Fixture for mocked upload response"""
    mock_file = Mock()
    mock_file.display_name = "test.txt"
    mock_file.uri = "gemini://test-file"
    return mock_file


class TestSendMessage:
    """Tests for the send_message function"""

    def test_send_message_without_files(self, mock_genai):
        """Test sending a message without any files"""
        result = send_message("Test prompt", [])

        # Verify GenerativeModel was created with correct params
        mock_genai.GenerativeModel.assert_called_once_with(
            model_name="gemini-1.5-flash-002",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
        )

        # Verify chat was started without history
        mock_genai.GenerativeModel.return_value.start_chat.assert_called_once_with(
            history=[]
        )

        assert result == '{"response": "test response"}'

    def test_send_message_with_files(self, mock_genai):
        """Test sending a message with a file"""
        test_file = "test_file_content"
        result = send_message("Test prompt", [test_file])

        # Verify chat was started with file in history
        mock_genai.GenerativeModel.return_value.start_chat.assert_called_once_with(
            history=[
                {
                    "role": "user",
                    "parts": [test_file],
                }
            ]
        )

        assert result == '{"response": "test response"}'

    def test_send_message_error_handling(self, mock_genai):
        """Test error handling in send_message"""
        # Make the GenerativeModel raise an exception
        mock_genai.GenerativeModel.side_effect = Exception("API Error")

        result = send_message("Test prompt", [])
        assert result == "Failed to send message"

    @pytest.mark.parametrize(
        "prompt,files",
        [
            ("", []),  # Empty prompt
            ("test", None),  # None files
            (None, []),  # None prompt
            ("test", [None]),  # None file in list
        ],
    )
    def test_send_message_edge_cases(self, mock_genai, prompt, files):
        """Test edge cases with various input combinations"""
        try:
            result = send_message(prompt, files)
            # Should either return a valid response or error message
            assert result in ['{"response": "test response"}', "Failed to send message"]
        except Exception as e:
            # Some combinations might raise TypeError
            assert isinstance(e, (TypeError, AttributeError))


class TestUploadToGemini:
    """Tests for the upload_to_gemini function"""

    def test_upload_success(self, mock_genai, mock_file, mock_upload_response):
        """Test successful file upload"""
        mock_genai.upload_file.return_value = mock_upload_response

        result = upload_to_gemini(mock_file)

        # Verify upload_file was called
        mock_genai.upload_file.assert_called_once_with(mock_file, mime_type=None)

        assert result.display_name == "test.txt"
        assert result.uri == "gemini://test-file"

    def test_upload_with_mime_type(self, mock_genai, mock_file, mock_upload_response):
        """Test upload with specific mime type"""
        mock_genai.upload_file.return_value = mock_upload_response

        result = upload_to_gemini(mock_file, mime_type="text/plain")

        mock_genai.upload_file.assert_called_once_with(
            mock_file, mime_type="text/plain"
        )

        assert result.display_name == "test.txt"

    def test_upload_error_handling(self, mock_genai, mock_file):
        """Test error handling during upload"""
        mock_genai.upload_file.side_effect = Exception("Upload failed")

        with pytest.raises(Exception) as exc_info:
            upload_to_gemini(mock_file)

        assert "Upload failed" in str(exc_info.value)

    def test_upload_nonexistent_file(self):
        """Test uploading a non-existent file"""
        with pytest.raises(Exception):
            upload_to_gemini("nonexistent_file.txt")

    # @pytest.mark.integration
    def test_environment_variables(self):
        """Test that required environment variables are set"""
        assert "GEMINI_API_KEY" in os.environ, "GEMINI_API_KEY not set in environment"


if __name__ == "__main__":
    pytest.main(["-v"])
