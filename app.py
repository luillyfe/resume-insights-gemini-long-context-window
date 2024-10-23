import streamlit as st

import tempfile

from resume_insights import ResumeInsights


def main():
    st.set_page_config(page_title="Resume Insights", page_icon="📄")

    st.title("Resume Insights")
    st.write("Upload a resume PDF to extract key information.")

    # Show upload file control
    uploaded_file = st.file_uploader(
        "Select Your Resume (PDF)", type="pdf", help="Choose a PDF file up to 5MB"
    )

    if uploaded_file is not None:
        if st.button("Get Insights"):
            with st.spinner("Parsing resume... This may take a moment."):
                try:
                    # Temporary file handling
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_file_path = temp_file.name

                    # Extract the candidate data from the resume
                    st.session_state.resumeInsights = ResumeInsights(temp_file_path)
                    st.session_state.insights = (
                        st.session_state.resumeInsights.extract_candidate_data()
                    )

                except Exception as e:
                    st.error(f"Failed to extract insights: {str(e)}")

        if "insights" in st.session_state:
            insights = st.session_state.insights

            st.subheader("Extracted Information")
            st.write(f"**Name:** {insights.name}")
            st.write(f"**Email:** {insights.email}")
            st.write(f"**Age:** {insights.age}")

            display_skills(insights.skills)

    else:
        st.info("Please upload a PDF resume to get started.")

    # App information
    st.sidebar.title("About")
    st.sidebar.info(
        "This app uses Gemini 1.5 Pro to parse resumes and extract key information. "
        "Upload a PDF resume to see it in action!"
    )
    st.sidebar.subheader("Long Rank Dependencies")
    st.sidebar.info(
        """Despite LlamaIndex remarkable ability to bind LLMs with vertical domain data, it faces limitations when reasoning across distributed knowledge nodes. Consider analyzing a Candidate's resume: based on the experience the candidate has been working with a particular skill provide an educated guess about its proficiency level in that ability. The system needs to account for temporal context, project complexity and interconnected experiences."""
    )
    st.sidebar.subheader("Long Context Window")
    st.sidebar.info(
        """Gemini's Long Context Window can help in this complex semantic analysis. Since it wouldn't split the text into smaller segments it processes the entire text into a cohesive unit, enabling more nuanced understanding of relationships between different part of the document."""
    )


def display_skills(skills: list[str]):
    if skills:
        st.subheader("Top Skills")

        # Custom CSS for skill bars
        st.markdown(
            """
        <style>
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #4CAF50, #8BC34A);
        }
        .skill-text {
            font-weight: bold;
            color: #1E1E1E;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Display skills with progress bars and hover effect
        if "job_matching_skills" not in st.session_state:
            display_skills_proficiency(skills)
        else:
            display_skills_proficiency(st.session_state.job_matching_skills)

        # Expandable section for skill details
        job_position = st.selectbox(
            "Select a job position:",
            [
                "Founding AI Data Engineer",
                "Founding AI Engineer",
                "Founding AI Engineer, Backend",
                "Founding AI Solutions Engineer",
            ],
            on_change=lambda: st.session_state.pop("job_matching_skills", None),
        )
        company = "LlamaIndex"

        st.subheader(
            f"How relevant are the skills for {job_position} Position at {company}?"
        )

        with st.spinner("Matching candidate's skills to job position..."):
            if "job_matching_skills" not in st.session_state:
                st.session_state.job_matching_skills = (
                    st.session_state.resumeInsights.match_job_to_skills(
                        skills, job_position, company
                    ).skills
                )
                st.rerun()

            with st.expander("Skill Relevance"):
                for skill in st.session_state.job_matching_skills:
                    st.write(
                        f"**{skill}**: {st.session_state.job_matching_skills[skill].relevance}"
                    )

        # # Interactive elements
        selected_skill = st.selectbox(
            "Select a skill to highlight:",
            st.session_state.job_matching_skills,
        )
        st.info(f"{st.session_state.job_matching_skills[selected_skill].reasoning}")


def display_skills_proficiency(skills):
    for skill in skills:
        col1, col2 = st.columns([3, 7])
        with col1:
            st.markdown(f"<p class='skill-text'>{skill}</p>", unsafe_allow_html=True)
        with col2:
            proficiency = (
                0
                if "job_matching_skills" not in st.session_state
                else skills[skill].proficiency
            )
            st.progress(proficiency / 10)


if __name__ == "__main__":
    main()
