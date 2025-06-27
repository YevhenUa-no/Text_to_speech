#import necessary libraries
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import openai
import base64
import os

# SETUP OPEN AI client

def setup_openai_client(api_key):
    return openai.OpenAI(api_key=api_key)

# function to transcribe audio to text

def transcribe_audio(client, audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text

# taking response from OpenAI
# Modified to accept a system_prompt
def fetch_ai_response(client, input_text, user_system_prompt="You are a helpful AI assistant."):
    # Define the fixed background prompt part
    background_prompt_part = "Also, tell a variation of a joke about a Truck driver that is coming back to the gas station and the worker says 'Loooong time no see!'"

    # Combine the user's prompt with the background prompt
    combined_system_prompt = f"{user_system_prompt} {background_prompt_part}"

    messages = []
    # Add the combined system prompt as the first message
    if combined_system_prompt:
        messages.append({"role": "system", "content": combined_system_prompt})
    messages.append({"role":"user","content":input_text})

    response = client.chat.completions.create(model='gpt-3.5-turbo-1106', messages=messages)
    return response.choices[0].message.content

# convert text to audio

def text_to_audio(client, text, audio_path):
    response = client.audio.speech.create(model="tts-1", voice="onyx", input=text)
    response.stream_to_file(audio_path)


# text card function
def create_text_card(text, title="Response"):
    """
    Generates an HTML string for a styled card with a title and text content.
    """
    card_html = f"""
    <style>
    .card {{
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
        border-radius: 5px;
        padding: 15px; /* From image_b075dd.jpg */
    }}
    .card:hover {{
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }}
    .container {{
        padding: 2px 16px;
    }}
    </style>
    <div class="card">
        <div class="container">
            <h4><b>{title}</b></h4>
            <p>{text}</p>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

#autoplay audio

def auto_play_audio(audio_file_path):
    if os.path.exists(audio_file_path):
        with open(audio_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
    else:
        st.error(f"Error: Audio file not found at {audio_file_path}")


def main():
    # Remove API Key input from sidebar
    st.sidebar.title("Configuration") # Renamed title since API key input is gone

    # New: Add a text area for the system prompt
    st.sidebar.subheader("AI Behavior Prompt")
    user_defined_system_prompt = st.sidebar.text_area(
        "Define the AI's behavior (e.g., 'You are a friendly chatbot.', 'You are a sarcastic comedian.')",
        value="You are a helpful AI assistant." # Default prompt
    )

    st.title("Aurora SpeakEasy")
    st.write("Hi there! Click on the voice record to interact with me. How can I help you today?")

    # --- API Key handling from secrets ---
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        client = setup_openai_client(api_key)
    except KeyError:
        st.error("OpenAI API Key not found in Streamlit secrets. Please configure `OPENAI_API_KEY`.")
        client = None # Ensure client is None if key is missing
    except Exception as e:
        st.error(f"Error setting up OpenAI client: {e}")
        client = None

    recorded_audio = None # Initialize recorded_audio

    # Only show audio recorder if client is successfully set up
    if client:
        recorded_audio = audio_recorder()
    else:
        # If client is not set up, we should not proceed with audio recording/processing
        # The error message above should guide the user.
        pass # No need for a separate warning here as the error already states the problem

    # check if recording is done and available AND if client is initialized
    if recorded_audio and client:
        audio_file_path = "recorded_audio.mp3"
        try:
            with open(audio_file_path, "wb") as f:
                f.write(recorded_audio)
        except Exception as e:
            st.error(f"Error saving recorded audio: {e}")
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return

        st.spinner("Transcribing your audio...")
        transcribed_text = transcribe_audio(client, audio_file_path)

        if transcribed_text:
            create_text_card(transcribed_text, "Transcribed Text")

            st.spinner("Getting AI response...")
            ai_response = fetch_ai_response(client, transcribed_text, user_defined_system_prompt)

            if ai_response:
                response_audio_file = "ai_response_audio.mp3"

                st.spinner("Converting AI response to audio...")
                text_to_audio(client, ai_response, response_audio_file)

                auto_play_audio(response_audio_file)
                create_text_card(ai_response, "AI Response")

        # Clean up temporary audio files at the end of processing
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
        if os.path.exists(response_audio_file):
            os.remove(response_audio_file)


if __name__ == "__main__":
    main()
