import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from streamlit_mic_recorder import mic_recorder
import os # Import os for removing temporary audio files

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

# Session state variables for initial personal information audio transcriptions
if "name_audio_transcription" not in st.session_state:
    st.session_state.name_audio_transcription = ""
if "experience_audio_transcription" not in st.session_state:
    st.session_state.experience_audio_transcription = ""
if "skills_audio_transcription" not in st.session_state:
    st.session_state.skills_audio_transcription = ""

# New session state for temporary voice input during the chat interview
if "current_chat_voice_input" not in st.session_state:
    st.session_state.current_chat_voice_input = ""

# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# Function to handle audio recording and transcription for initial setup
def handle_audio_input_setup(slot_name, key):
    mic_recorder_output = mic_recorder(
        start_prompt="🎙️ Speak",
        stop_prompt="⏹️ Stop",
        just_once=True,
        use_container_width=True,
        key=key
    )

    if mic_recorder_output:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        audio_bytes = mic_recorder_output['bytes']
        if audio_bytes:
            temp_audio_file_path = f"audio_{slot_name}.webm"
            with open(temp_audio_file_path, "wb") as f:
                f.write(audio_bytes)

            with st.spinner(f"Transcribing {slot_name}..."):
                audio_file = open(temp_audio_file_path, "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                audio_file.close() # Close the file after use
                os.remove(temp_audio_file_path) # Clean up the temporary file

            setattr(st.session_state, f"{slot_name}_audio_transcription", transcript.text)
            st.write(f"**Transcription for {slot_name}:** {transcript.text}")
            # Automatically set the text input with the transcription
            st.session_state[slot_name] = transcript.text
            # Rerun the app to update the text_input immediately
            st.rerun()
    return getattr(st.session_state, f"{slot_name}_audio_transcription")


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
    input_method = st.radio("How would you like to provide your information?", ("Type", "Speak"), key="input_method_radio")

    if input_method == "Type":
        st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], placeholder="Enter your name", max_chars=40, key="name_text_input")
        st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", max_chars=200, key="experience_text_input")
        st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", max_chars=200, key="skills_text_input")
    else: # input_method == "Speak"
        st.write("### Name")
        current_name_transcription = handle_audio_input_setup("name", "mic_recorder_name")
        st.session_state["name"] = st.text_input(
            label="Name (from audio or manual edit)",
            value=st.session_state["name"] if st.session_state["name"] else current_name_transcription,
            placeholder="Enter your name or speak it", max_chars=40,
            key="name_input_final"
        )
        st.markdown("---")

        st.write("### Experience")
        current_experience_transcription = handle_audio_input_setup("experience", "mic_recorder_experience")
        st.session_state["experience"] = st.text_area(
            label="Experience (from audio or manual edit)",
            value=st.session_state["experience"] if st.session_state["experience"] else current_experience_transcription,
            placeholder="Describe your experience or speak it", max_chars=200,
            key="experience_input_final"
        )
        st.markdown("---")

        st.write("### Skills")
        current_skills_transcription = handle_audio_input_setup("skills", "mic_recorder_skills")
        st.session_state["skills"] = st.text_area(
            label="Skills (from audio or manual edit)",
            value=st.session_state["skills"] if st.session_state["skills"] else current_skills_transcription,
            placeholder="List your skills or speak them", max_chars=200,
            key="skills_input_final"
        )
        st.markdown("---")


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
            key="level_radio", # Unique key
            options=["Junior", "Mid-level", "Senior"],
            index=["Junior", "Mid-level", "Senior"].index(st.session_state["level"])
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"),
            index=("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst").index(st.session_state["position"]),
            key="position_selectbox" # Unique key
        )

    st.session_state["company"] = st.selectbox(
        "Select a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
        index=("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(st.session_state["company"]),
        key="company_selectbox" # Unique key
    )


    # Button to complete setup
    if st.button("Start Interview", on_click=complete_setup, key="start_interview_button"):
        if not (st.session_state["name"] or st.session_state["experience"] or st.session_state["skills"]):
            st.warning("Please provide your personal information before starting the interview.")
            st.session_state.setup_complete = False
        else:
            st.write("Setup complete. Starting interview...")
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
                # Add audio playback for assistant messages
                if message["role"] == "assistant" and "audio_file_path" in message:
                    st.audio(message["audio_file_path"], format="audio/mpeg", loop=False, autoplay=False)


    # Handle user input (voice or text) and OpenAI response
    if st.session_state.user_message_count < 5:
        # Voice recording button for chat input
        mic_recorder_chat_output = mic_recorder(
            start_prompt="🎙️ Speak your answer",
            stop_prompt="⏹️ Stop Recording",
            just_once=True,
            use_container_width=True,
            key=f"mic_recorder_chat_turn_{st.session_state.user_message_count}" # Unique key for each turn
        )

        if mic_recorder_chat_output and mic_recorder_chat_output['bytes']:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            audio_bytes = mic_recorder_chat_output['bytes']
            temp_audio_file_path = "chat_audio_response.webm" # Use a generic name for chat audio
            with open(temp_audio_file_path, "wb") as f:
                f.write(audio_bytes)

            with st.spinner("Transcribing your answer..."):
                audio_file = open(temp_audio_file_path, "rb")
                transcribed_text = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                ).text
                audio_file.close()
                os.remove(temp_audio_file_path)

            st.session_state.current_chat_voice_input = transcribed_text
            st.rerun() # Rerun to update the text area with transcription

        # Text input area (pre-filled with transcription if available)
        user_prompt_input = st.text_area(
            "Your answer:",
            value=st.session_state.current_chat_voice_input,
            placeholder="Type your response here or speak it...",
            max_chars=1000,
            key=f"chat_text_area_{st.session_state.user_message_count}" # Unique key for each turn
        )

        # "Send" button to process the input
        if st.button("Send Answer", key=f"send_answer_button_{st.session_state.user_message_count}"):
            if user_prompt_input:
                st.session_state.messages.append({"role": "user", "content": user_prompt_input})
                with st.chat_message("user"):
                    st.markdown(user_prompt_input)

                # Reset current voice input after sending
                st.session_state.current_chat_voice_input = ""

                # Only get assistant response if there are turns left
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
                        response_text = st.write_stream(stream) # Get the full response text

                        # Generate speech from the assistant's response
                        speech_file_path = f"assistant_response_{st.session_state.user_message_count}.mp3"
                        with client.audio.speech.create(
                            model="tts-1",
                            voice="alloy", # You can choose other voices like "onyx", "nova", "shimmer", "echo", "fable"
                            input=response_text,
                        ) as speech_stream:
                            speech_stream.write_to_file(speech_file_path)

                        # Append the response and audio file path to messages
                        st.session_state.messages.append({"role": "assistant", "content": response_text, "audio_file_path": speech_file_path})
                        
                        # Immediately play the audio for the current response
                        st.audio(speech_file_path, format="audio/mpeg", loop=False, autoplay=True)

                st.session_state.user_message_count += 1
                st.rerun() # Rerun to update chat history and prepare for next input
            else:
                st.warning("Please provide an answer before sending.")

    # Check if the user message count reaches 5
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

---

### Get Feedback

If the interview is complete, you'll see a button to get feedback.

If st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback, key="get_feedback_button"):
        st.write("Fetching feedback...")

---

### Feedback Screen

Once feedback is requested, it will be generated and displayed.

if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
    if st.button("Restart Interview", type="primary", key="restart_interview_button_final"):
        # Before reloading, clean up generated audio files to prevent accumulation
        for message in st.session_state.messages:
            if message.get("audio_file_path") and os.path.exists(message["audio_file_path"]):
                os.remove(message["audio_file_path"])
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
