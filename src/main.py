# main.py

import asyncio
import aioconsole
import os
import requests

from authenticator import Authenticator
from connection import Connection
from devices import AudioDevices
from dotenv import load_dotenv
from pyaudio import PyAudio, paInt16

# Audio format and parameters
FORMAT = paInt16
CHANNELS = 1
SAMPLE_WIDTH = 2  # PyAudio.get_sample_size(pyaudio, format=paInt16)
CHUNK_SIZE = 1024


async def main():
    """
    Main asynchronous function to set up audio devices, authenticate, and connect to the Hume AI websocket.
    """
    # Initialize PyAudio instance
    pyaudio = PyAudio()
    
    # List available audio input and output devices
    input_devices, output_devices = AudioDevices.list_audio_devices(pyaudio)
    
    # Choose the audio input device and get its sample rate
    input_device_index, input_device_sample_rate = AudioDevices.choose_device(
        input_devices, "input"
    )
    
    # Choose the audio output device
    output_device_index = AudioDevices.choose_device(output_devices, "output")

    # Open the audio stream with the selected parameters
    audio_stream = pyaudio.open(
        format=FORMAT,
        channels=CHANNELS,
        frames_per_buffer=CHUNK_SIZE,
        rate=input_device_sample_rate,
        input=True,
        output=True,
        input_device_index=input_device_index,
        output_device_index=output_device_index,
    )

    # Fetch the access token for authentication
    access_token = get_access_token()


    # Create prompt (POST /v0/evi/prompts)
    prompt_response = requests.post(
        "https://api.hume.ai/v0/evi/prompts",
        headers={
            "X-Hume-Api-Key": os.getenv("HUME_API_KEY"),
            "Content-Type": "application/json"
        },
        json={
            "name": "test",
            "text": build_system_prompt()
        },
    )

    # Create config (POST /v0/evi/configs)
    response = requests.post(
        "https://api.hume.ai/v0/evi/configs",
        headers={
            "X-Hume-Api-Key": os.getenv("HUME_API_KEY"),
            "Content-Type": "application/json"
        },
        json={
            "name": "test",
            "voice": {
                "name": "KORA"
                },
            "prompt": {'id': prompt_response.json()['id']},
            "language_model": {
                "model_provider": "OPEN_AI",
                "model_resource": "gpt-4o"
            }
        },
    )

    config_id = response.json()['id']


    # Construct the websocket URL with the access token
    socket_url = (
        "wss://api.hume.ai/v0/evi/chat?"
        f"access_token={access_token}&config_id={config_id}"
    )
    #stop_event = asyncio.Event()
    # Connect to the websocket and start the audio stream
    #print('hello')
    # task = asyncio.create_task(Connection.connect(
    #     socket_url,
    #     audio_stream,
    #     input_device_sample_rate,
    #     SAMPLE_WIDTH,
    #     CHANNELS,
    #     CHUNK_SIZE,
    #     stop_event
    # ))

    #await aioconsole.ainput()

    #stop_event.set()

    #await task
    
    await Connection.connect(
        socket_url,
        audio_stream,
        input_device_sample_rate,
        SAMPLE_WIDTH,
        CHANNELS,
        CHUNK_SIZE,
    )

    transcript = Connection.transcript
    

    # Close the PyAudio stream and terminate PyAudio
    audio_stream.stop_stream()
    audio_stream.close()
    pyaudio.terminate()

    ''' Revisit this when we integrate in streamlit, perhaps wrap it in a cleanup function '''
    # response = requests.delete(
    #     "https://api.hume.ai/v0/evi/configs/{config_id}".format(config_id=config_id),
    #     headers={
    #         "X-Hume-Api-Key": os.getenv("HUME_API_KEY")
    #     },
    # )


def get_access_token() -> str:
    """
    Load API credentials from environment variables and fetch an access token.

    Returns:
        str: The access token.

    Raises:
        SystemExit: If API key or Secret key are not set.
    """
    load_dotenv()

    # Attempt to retrieve API key and Secret key from environment variables
    HUME_API_KEY = os.getenv("HUME_API_KEY")
    HUME_SECRET_KEY = os.getenv("HUME_SECRET_KEY")

    # Ensure API key and Secret key are set
    if HUME_API_KEY is None or HUME_SECRET_KEY is None:
        print(
            "Error: HUME_API_KEY and HUME_SECRET_KEY must be set either in a .env file or as environment variables."
        )
        exit()

    # Create an instance of Authenticator with the API key and Secret key
    authenticator = Authenticator(HUME_API_KEY, HUME_SECRET_KEY)

    # Fetch the access token
    access_token = authenticator.fetch_access_token()
    return access_token


def build_system_prompt():
    return """
        ## Voice Only Response Format Instructions
        Everything you output will be spoken aloud with expressive
        text-to-speech, so tailor all of your responses for voice-only
        conversations. NEVER output text-specific formatting like markdown,
        lists, or anything that is not normally said out loud. Always prefer
        easily pronounced words. Seamlessly incorporate natural vocal
        inflections like “oh wow” and discourse markers like “I mean” to
        make your conversation human-like and to ease user comprehension.

        Be assertive and professional, but polite. 

        If you see "[continue]" never ever go back on your words, don't say
        sorry, and make sure to discreetly pick up where you left off.
        For example:
        Assistant: Hey there!
        User: [continue]
        Assistant: How are you doing?


        ## Role
        You are a recruiter for a company who is looking for someone to fill an open role. Ask the candidate any interview questions about their background and experience.
        
        ## Task
        Below you are provided with a list of questions to ask. Your job is to go through and ask each question. Be sure to allow the candidate a chance to answer each question 
        before moving on to the next. Do not simply agree with or applaud everything the candidate says. Be critical, but professional at the same time. 
        If the answer provided is vague, ask any follow up questions as you see necessary to obtain a sufficient understanding of what the candidate's background and achievements are like. Again, your goal is
        to gain the best understanding of this candidate as possible.
        
        
        1. Can you provide more details on your experience managing data pipelines at Amaze?
        2. You listed several programming languages (Python, Java, R, SQL, etc.). Which of these do you feel most confident with? Can you share specific examples of projects where you've leveraged these skills?
        3. Could you elaborate on the models you developed?
        4. How have you used Google BigQuery in your projects, and what are some best practices you've learned through this?
        """
        # with Apache Airflow, particularly how you utilized it to
# specifically the RNN for Karbon and the multiple RNNs for the Joy Causal Inference NLP Model project?

if __name__ == "__main__":
    """
    Entry point for the script. Runs the main asynchronous function.
    """
    asyncio.run(main())