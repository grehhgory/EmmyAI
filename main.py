# Import standard libraries
import io, queue, tempfile, os, threading
# Import third-party libraries
from pydub import AudioSegment
import speech_recognition as sr
import whisper
import click
import torch
import numpy as np
import openai
import azure.cognitiveservices.speech as speechsdk
from dotenv import dotenv_values

# Import config and retrieve API key from config
config = dotenv_values(".env")
openai.api_key = config["OPENAI_API_KEY"]

def speak(response):
	# Create speech and audio configs
	speech_config = speechsdk.SpeechConfig(
		subscription = config["AZURE_SPEECH_KEY"],
		region = config["AZURE_SERVICE_REGION"]
	)
	audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
	# Create speech synthesiser from speech and audio configs
	speech_synth = speechsdk.SpeechSynthesizer(
		speech_config = speech_config,
		audio_config = audio_config
	)
	# Define SSML
	ssml = f"""
	<speak version='1.0' xml:lang='en-US' xmlns='http://www.w3.org/2001/10/synthesis'>
		<voice name='{config["AZURE_VOICE_NAME"]}'>
			<prosody pitch='{config["AZURE_VOICE_PITCH"]}' rate='{config["AZURE_VOICE_RATE"]}'>{response}</prosody>
		</voice>
	</speak>"""
	# Get asynchronous speech to be played
	speech_synth.speak_ssml_async(ssml).get()
	print("Emmy is listening!")

def record_audio(audio_queue, energy, pause, dynamic_energy, save_file, temp_dir):
	# Create speech recogniser
	r = sr.Recognizer()
	# Set speech recogniser's parameters
	r.energy_threshold, r.pause_threshold, r.dynamic_energy_threshold = energy, pause, dynamic_energy
	with sr.Microphone(sample_rate=16000) as source:
		print("Emmy is listening! " + str(source))
		i = 0
		while True:
			audio = r.listen(source)
			if save_file:
				data = io.BytesIO(audio.get_wav_data())
				audio_clip = AudioSegment.from_file(data)
				filename = os.path.join(temp_dir, f"temp{i}.wav")
				audio_clip.export(filename, format = "wav")
				audio_data = filename
			else:
				torch_audio = torch.from_numpy(np.frombuffer(audio.get_raw_data(), np.int16)
								   .flatten()
								   .astype(np.float32) / 32768.0)
				audio_data = torch_audio
			audio_queue.put_nowait(audio_data)
			i += 1

def transcribe_forever(audio_queue, result_queue, audio_model, english, verbose, save_file):
	while True:
		audio_data = audio_queue.get()
		if english: result = audio_model.transcribe(audio_data, language="english")
		else: result = audio_model.transcribe(audio_data)
		if not verbose:
			transcript = result["text"]
			result_queue.put_nowait("You said: " + transcript)
			completion = openai.Completion.create(
				model = config["OPENAI_MODEL_NAME"],
				prompt = config["OPENAI_PROMPT"] + f" {config['USERNAME']}: " + transcript + config["OPENAI_START_SEQUENCE"],
				temperature = 1,
				frequency_penalty = 1,
				presence_penalty = 1,
				max_tokens = 28
			)
			print(f"""
		 		Prompt Tokens: {str(completion["usage"]["prompt_tokens"])}
				Completion Tokens: {str(completion["usage"]["completion_tokens"])}
				Billed Tokens: {str(completion["usage"]["total_tokens"])}
		 	""")
			trimmed_completion = completion["choices"][0]["text"].split(config["OPENAI_STOP_SEQUENCE"], 1)[0]
			result_queue.put_nowait("Emmy:" + trimmed_completion)
			speak(trimmed_completion)
		else: result_queue.put_nowait(result)
		# Remove audio data if save_file is set to True
		if save_file: os.remove(audio_data)

@click.command()
@click.option("--model", default="base", help="Model to use", type=click.Choice(["tiny", "base", "small", "medium", "large"]))
@click.option("--device", default=("cuda" if torch.cuda.is_available() else "cpu"), help="Device to use", type=click.Choice(["cpu", "cuda"]))
@click.option("--english", default=False, help="Whether to use English model", is_flag=True, type=bool)
@click.option("--verbose", default=False, help="Whether to print verbose output", is_flag=True, type=bool)
@click.option("--energy", default=300, help="Energy level for mic to detect", type=int)
@click.option("--dynamic_energy", default=False, is_flag=True, help="Flag to enable dynamic energy", type=bool)
@click.option("--pause", default=0.8, help="Pause time before entry ends", type=float)
@click.option("--save_file", default=False, help="Flag to save file", is_flag=True, type=bool)

def main(model, english, verbose, energy, pause, dynamic_energy, save_file, device):
	temp_dir = tempfile.mkdtemp() if save_file else None
	if model != "large" and english:
		model = model + ".en"
	audio_model = whisper.load_model(model).to(device)
	audio_queue = queue.Queue()
	result_queue = queue.Queue()
	threading.Thread(target=record_audio, args=(
		audio_queue, energy, pause, dynamic_energy, save_file, temp_dir)).start()
	threading.Thread(target=transcribe_forever, args=(
		audio_queue, result_queue, audio_model, english, verbose, save_file)).start()
	while True:
		print(result_queue.get())

main()
