from llm import send_message, upload_to_gemini
from models import Candidate, JobSkill


class ResumeInsights:
    def __init__(self, file_path):
        # Upload file to Gemini File API
        self.resume = upload_to_gemini(file_path)
        # pass

    def extract_candidate_data(self) -> Candidate:
        """
        Extracts candidate data from the resume.

        Returns:
            Candidate: The extracted candidate data.
        """
        # Output Schema
        output_schema = Candidate.model_json_schema()

        # Prompt
        prompt = f"""
                Use the following JSON schema describing the information I need to extract.  Please extract the properties defined in the JSON schema:
                ```json
                {output_schema}
                ```json
                Provide the result in a structured JSON format. Please remove any ```json ``` characters from the output.
                """

        # Text output
        output = send_message(prompt, [self.resume])
        print(output)
        # Pydanctic model
        return Candidate.model_validate_json(output)

    def match_job_to_skills(self, skills, job_position, company) -> JobSkill:
        skills_job_prompt = [
            f"""Given this skill: {skill}, please provide your reasoning for why this skill 
                    matter to the follloging job position: {job_position} at {company}.
                    if the skill is not relevant please say so.
                    Use system thinking level 3 to accomplish this task"""
            for skill in skills
        ]

        skills_job_prompt = f"""{", ".join(skills_job_prompt)}
            Please use the following schema: {JobSkill.model_json_schema()}
            Provide the result in a structured JSON format. Please remove any ```json ``` characters from the output.
            """

        output = send_message(skills_job_prompt, [self.resume])
        return JobSkill.model_validate_json(output)


if __name__ == "__main__":
    pass


# Resources
# https://docs.llamaindex.ai/en/stable/examples/structured_outputs/structured_outputs/
# https://docs.llamaindex.ai/en/stable/module_guides/querying/structured_outputs/pydantic_program/
# https://docs.llamaindex.ai/en/stable/examples/node_parsers/semantic_chunking/
# https://docs.llamaindex.ai/en/stable/module_guides/indexing/vector_store_index/
# https://docs.llamaindex.ai/en/stable/examples/metadata_extraction/PydanticExtractor/
# https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/
# https://github.com/run-llama/llama_index/discussions/13271
# https://www.llamaindex.ai/blog/introducing-llamaextract-beta-structured-data-extraction-in-just-a-few-clicks
