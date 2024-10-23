import os
import json
import google.generativeai as genai
from typing import List, Any

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}


def send_message(prompt: str, files: List[str]):
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-002",
            generation_config=generation_config,
        )

        if files:
            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [files[0]],
                    }
                ]
            )
        else:
            chat_session = model.start_chat(history=[])

        response = chat_session.send_message(prompt)

        return response.text
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to send message"


def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file
