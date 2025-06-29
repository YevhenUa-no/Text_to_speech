import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from streamlit_mic_recorder import mic_recorder # Import the mic_recorder

# Setting up the Streamlit page configuration
st.set_page_config(page_title="StreamlitChatMessageHistory", page_icon="💬")
st.title("Chatbot")

# Initialize session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio_transcription" not in st.session_state: # New session state for transcription
    st.session_state.audio_transcription = ""

# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# Setup stage for collecting user details
if not st.session_state.setup_complete:
    st.subheader('Personal Information')

    # Initialize session state for personal information
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    # Option to input via text or voice
    input_method = st.radio("How would you like to provide your information?", ("Type", "Speak"))

    if input_method == "Type":
        # Get personal information input via text
        st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], placeholder="Enter your name", max_chars=40)
        st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", max_chars=200)
        st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", max_chars=200)
    else: # input_method == "Speak"
        st.write("Record your personal information (Name, Experience, Skills):")
        # Microphone recorder button
        mic_recorder_output = mic_recorder(
            start_prompt="🎙️ Speak",
            stop_prompt="⏹️ Stop",
            just_once=True, # Transcribe once per recording (re-enables button after stop)
            use_container_width=True,
            key="mic_recorder_button"
        )

        if mic_recorder_output:
            # Initialize OpenAI client for transcription
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            audio_bytes = mic_recorder_output['bytes']
            if audio_bytes:
                # Save the audio to a temporary file
                with open("audio.webm", "wb") as f:
                    f.write(audio_bytes)
                audio_file = open("audio.webm", "rb")

                # Transcribe the audio
                with st.spinner("Transcribing audio..."):
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                st.session_state.audio_transcription = transcript.text
                st.write(f"**Transcription:** {st.session_state.audio_transcription}")

                # You'll need to parse this transcription into name, experience, skills
                # This is a simplified example; a real-world scenario might need more robust NLP
                st.info("Please manually review and edit the transcribed information below.")
                st.session_state["name"] = st.text_input(label="Name (from audio)", value=st.session_state["name"] or st.session_state.audio_transcription.split(',')[0].strip() if st.session_state.audio_transcription else "", placeholder="Enter your name", max_chars=40)
                st.session_state["experience"] = st.text_area(label="Experience (from audio)", value=st.session_state["experience"] or st.session_state.audio_transcription, placeholder="Describe your experience", max_chars=200)
                st.session_state["skills"] = st.text_area(label="Skills (from audio)", value=st.session_state["skills"] or st.session_state.audio_transcription, placeholder="List your skills", max_chars=200)


    # Company and Position Section
    st.subheader('Company and Position')

    # Initialize session state for company and position information and setting default values
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose level",
            key="visibility",
            options=["Junior", "Mid-level", "Senior"],
            index=["Junior", "Mid-level", "Senior"].index(st.session_state["level"])
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"),
            index=("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst").index(st.session_state["position"])
        )

    st.session_state["company"] = st.selectbox(
        "Select a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
        index=("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(st.session_state["company"])
    )


    # Button to complete setup
    if st.button("Start Interview", on_click=complete_setup):
        # You might want to add a check here to ensure at least some fields are filled
        if not (st.session_state["name"] or st.session_state["experience"] or st.session_state["skills"]):
            st.warning("Please provide your personal information before starting the interview.")
            st.session_state.setup_complete = False # Prevent setup from completing if fields are empty
        else:
            st.write("Setup complete. Starting interview...")
            # If setup is complete and data is provided, refresh to proceed
            streamlit_js_eval(js_expressions="parent.window.location.reload()")


# Interview phase
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
    """
    Start by introducing yourself
    """,
    icon="👋",
    )

    # Initialize OpenAI client
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Setting OpenAI model if not already initialized
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    # Initializing the system prompt for the chatbot
    if not st.session_state.messages:
        st.session_state.messages = [{
                "role": "system",
                "content": (f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                            f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                            f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                            f"at the company {st.session_state['company']}")
            }]

    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Handle user input and OpenAI response
    # Put a max_chars limit
    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your response", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True,
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})

            # Increment the user message count
            st.session_state.user_message_count += 1

    # Check if the user message count reaches 5
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

# Show "Get Feedback"
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for feedback
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Generate feedback using the stored messages and write a system prompt for the feedback
    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overall Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questions.
             """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any conversation: {conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
