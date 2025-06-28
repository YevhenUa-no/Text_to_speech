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

    try:

        with open(audio_path, "rb") as audio_file:

            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

            return transcript.text

    except Exception as e:

        st.error(f"Error during audio transcription: {e}")

        return ""



# taking response from OpenAI

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



    try:

        response = client.chat.completions.create(model='gpt-3.5-turbo-1106', messages=messages)

        return response.choices[0].message.content

    except Exception as e:

        st.error(f"Error fetching AI response: {e}")

        return ""



# convert text to audio

def text_to_audio(client, text, audio_path):

    try:

        response = client.audio.speech.create(model="tts-1", voice="onyx", input=text)

        response.stream_to_file(audio_path)

    except Exception as e:

        st.error(f"Error converting text to audio: {e}")



# autoplay audio

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

    st.set_page_config(page_title="Aurora SpeakEasy", page_icon="🎙️")

    st.title("Aurora SpeakEasy")

    st.write("Hi there! Click on the voice record to interact with me. How can I help you today?")



    # Sidebar for configuration

    st.sidebar.title("Configuration")

    user_defined_system_prompt = st.sidebar.text_area(

        "Define the AI's behavior (e.g., 'You are a friendly chatbot.', 'You are a sarcastic comedian.')",

        value="You are a helpful AI assistant." # Default prompt

    )



    # Initialize OpenAI client

    client = None

    try:

        api_key = st.secrets["OPENAI_API_KEY"]

        client = setup_openai_client(api_key)

    except KeyError:

        st.error("OpenAI API Key not found in Streamlit secrets. Please configure `OPENAI_API_KEY`.")

    except Exception as e:

        st.error(f"Error setting up OpenAI client: {e}")



    # Only show audio recorder if client is successfully set up

    if client:

        # Use a specific temporary file name

        temp_audio_file = "temp_recorded_audio.wav" # audio_recorder_streamlit saves as WAV by default



        # Display the audio recorder

        recorded_audio_bytes = audio_recorder(

            text="", # No text needed, just the icon

            icon_size="3x", # Make the icon larger

            # You can add the icon directly if needed, e.g., icon="microphone"

            # Setting 'key' helps maintain state across reruns if multiple recorders were present

        )



        # Process recorded audio if available

        if recorded_audio_bytes:

            # Save the recorded bytes to a temporary file

            try:

                with open(temp_audio_file, "wb") as f:

                    f.write(recorded_audio_bytes)

            except Exception as e:

                st.error(f"Error saving recorded audio: {e}")

                if os.path.exists(temp_audio_file):

                    os.remove(temp_audio_file) # Clean up if save failed

                return



            st.spinner("Transcribing your audio...")

            transcribed_text = transcribe_audio(client, temp_audio_file)



            if transcribed_text:

                st.subheader("Transcribed Text")

                st.info(transcribed_text) # Using st.info for a styled box



                st.spinner("Getting AI response...")

                ai_response = fetch_ai_response(client, transcribed_text, user_defined_system_prompt)



                if ai_response:

                    response_audio_file = "ai_response_audio.mp3"



                    st.spinner("Converting AI response to audio...")

                    text_to_audio(client, ai_response, response_audio_file)



                    if os.path.exists(response_audio_file): # Check if audio file was successfully created

                        auto_play_audio(response_audio_file)

                        st.subheader("AI Response")

                        # Using st.success for a different styled box for AI response

                        st.success(ai_response)

                    else:

                        st.warning("Could not generate audio for AI response.")



            # Clean up temporary audio files at the end of processing

            if os.path.exists(temp_audio_file):

                os.remove(temp_audio_file)

            if os.path.exists(response_audio_file):

                os.remove(response_audio_file)



    else: # If client is not set up

        st.warning("Please ensure your OpenAI API Key is configured in Streamlit secrets to use the voice feature.")



if __name__ == "__main__":

    main()
