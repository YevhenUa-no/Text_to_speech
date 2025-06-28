import streamlit as st
from audio_recorder_streamlit import audio_recorder # Using the robust audio recorder
import openai
import base64
import os
from streamlit_js_eval import streamlit_js_eval # Still needed for reload

# ... (rest of your existing code - functions, client setup, etc. - remains the same) ...

# Global client setup (moved outside functions for easier access)
client = None
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = setup_openai_client(api_key)
except KeyError:
    st.error("OpenAI API Key not found in Streamlit secrets. Please configure `OPENAI_API_KEY`.")
    client = None # Ensure client is None if key is missing
except Exception as e:
    st.error(f"Error setting up OpenAI client: {e}")
    client = None

# --- NEW: Function to handle audio recording and transcription for a field ---
# This function is already correct for the setup fields, no changes needed here.
def record_and_transcribe_field(field_label, field_session_key, unique_key):
    # Use st.columns to place the text input and recorder side-by-side
    col_text, col_mic = st.columns([0.8, 0.2])

    with col_text:
        current_value = st.session_state.get(field_session_key, "")
        if "recorded_text_" + unique_key in st.session_state and st.session_state["recorded_text_" + unique_key]:
            current_value = st.session_state["recorded_text_" + unique_key]
            # Clear it after using to prevent re-populating on subsequent reruns
            st.session_state["recorded_text_" + unique_key] = "" 

        if field_session_key == "name":
            st.session_state[field_session_key] = st.text_input(
                label=field_label,
                value=current_value,
                placeholder=f"Enter your {field_label.lower()}",
                max_chars=40,
                key=unique_key + "_text_input"
            )
        else: # For Experience and Skills which are text_area
            st.session_state[field_session_key] = st.text_area(
                label=field_label,
                value=current_value,
                placeholder=f"Describe your {field_label.lower()}" if field_session_key == "experience" else f"List your {field_label.lower()}",
                max_chars=200,
                key=unique_key + "_text_input"
            )

    with col_mic:
        # Check if client is available before showing recorder
        if client:
            recorded_audio = audio_recorder(
                text="",
                icon_size="1x", # Smaller icon for fields
                use_container_width=True,
                key=unique_key + "_audio_recorder" # Unique key for each recorder
            )

            if recorded_audio:
                temp_audio_file = f"temp_{unique_key}.wav"
                try:
                    with open(temp_audio_file, "wb") as f:
                        f.write(recorded_audio)
                    
                    # Transcribe and store the text in a temporary session state key
                    st.session_state["recorded_text_" + unique_key] = transcribe_audio(client, temp_audio_file)
                    st.experimental_rerun() # Rerun to update the text input immediately

                except Exception as e:
                    st.error(f"Error processing audio for {field_label}: {e}")
                finally:
                    if os.path.exists(temp_audio_file):
                        os.remove(temp_audio_file)
        else:
            st.warning("API client not set up for audio input.")

def main():
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
    # Initialize a separate session state variable for chat input's transcribed text
    if "transcribed_chat_input_value" not in st.session_state:
        st.session_state.transcribed_chat_input_value = ""


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

        # Use the new helper function for each field
        record_and_transcribe_field("Name", "name", "name_input")
        record_and_transcribe_field("Experience", "experience", "experience_input")
        record_and_transcribe_field("Skills", "skills", "skills_input")


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
        if st.button("Start Interview", on_click=complete_setup):
            st.write("Setup complete. Starting interview...")

    # Interview phase
    if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

        st.info(
        """
        Start by introducing yourself
        """,
        icon="👋",
        )

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

        # --- Main Chat Input with Audio Recorder ---
        col_chat_input, col_chat_mic = st.columns([0.8, 0.2])

        with col_chat_input:
            # Use transcribed_chat_input_value for the chat_input's value
            prompt = st.chat_input(
                "Your response",
                max_chars=1000,
                key="chat_text_input",
                value=st.session_state.transcribed_chat_input_value # Read from separate variable
            )
            # Clear the transcribed value immediately after the chat_input potentially uses it
            st.session_state.transcribed_chat_input_value = ""


        with col_chat_mic:
            if client:
                recorded_chat_audio = audio_recorder(
                    text="",
                    icon_size="2x", # A bit larger for the main chat
                    use_container_width=True,
                    key="main_chat_audio_recorder"
                )

                if recorded_chat_audio:
                    temp_chat_audio_file = "temp_chat_audio.wav"
                    try:
                        with open(temp_chat_audio_file, "wb") as f:
                            f.write(recorded_chat_audio)
                        
                        voice_transcript = transcribe_audio(client, temp_chat_audio_file)
                        if voice_transcript:
                            # Store the transcript in the new session state variable
                            st.session_state.transcribed_chat_input_value = voice_transcript
                            st.experimental_rerun() # Rerun to update the chat_input immediately

                    except Exception as e:
                        st.error(f"Error processing chat audio: {e}")
                    finally:
                        if os.path.exists(temp_chat_audio_file):
                            os.remove(temp_chat_audio_file)
            else:
                st.warning("API client not set up for chat audio input.")

        # Handle user input (either typed or from audio recorder)
        if st.session_state.user_message_count < 5:
            if prompt: # If there's a prompt (either typed or from Whisper)
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get assistant response if user message count allows
                if st.session_state.user_message_count < 4:
                    # Note: client is already initialized globally at the top
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
                st.rerun() # Rerun to display the new messages and potentially update chat_complete
            else:
                pass # No prompt yet, waiting for user input or audio


        # Check if the user message count reaches 5
        if st.session_state.user_message_count >= 5 and not st.session_state.chat_complete:
            st.session_state.chat_complete = True
            st.rerun() # Rerun to transition to feedback stage

    # Show "Get Feedback"
    if st.session_state.chat_complete and not st.session_state.feedback_shown:
        if st.button("Get Feedback", on_click=show_feedback):
            st.write("Fetching feedback...")
            st.rerun() # Rerun to display feedback

    # Show feedback screen
    if st.session_state.feedback_shown:
        st.subheader("Feedback")

        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

        # Initialize new OpenAI client instance for feedback
        # client is already initialized globally
        feedback_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
                 Before the Feedback give a score of 1 to 10.
                 Follow this format:
                 Overal Score: //Your score
                 Feedback: //Here you put your feedback
                 Give only the feedback do not ask any additional questins.
                 """},
                {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
            ]
        )

        st.write(feedback_completion.choices[0].message.content)

        # Button to restart the interview
        if st.button("Restart Interview", type="primary"):
            # This will clear all session state variables and force a full reload
            for key in st.session_state.keys():
                del st.session_state[key]
            streamlit_js_eval(js_expressions="parent.window.location.reload()")


if __name__ == "__main__":
    main()
