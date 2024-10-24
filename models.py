from pydantic import BaseModel, Field
from typing import Optional, Dict


# Candidate Data Structure Definition (output definition)
class Candidate(BaseModel):
    name: Optional[str] = Field(None, description="The full name of the candidate")
    email: Optional[str] = Field(None, description="The email of the candidate")
    age: Optional[str] = Field(
        None,
        description="The age of the candidate. If not explicitly stated, please provide an educated guess based on how long the candiate has been in scholl and/or working.",
    )
    skills: Optional[list[str]] = Field(
        None, description="A list of skills possessed by the candidate"
    )


class Skill(BaseModel):
    relevance: Optional[str] = Field(
        None, description="How relevant is the skill to the job position"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Why this skill is relevant to the job position",
    )
    proficiency: Optional[int] = Field(
        None,
        description="Based on the year's he worked using this skill, please provide an educated guess from his proficiency level",
    )


class JobSkill(BaseModel):
    skills: Dict[str, Skill] = Field(None, description="Skill")
    jobName: str = Field(None, description="Job position name")
