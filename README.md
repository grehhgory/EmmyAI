# EmmyAI

Installation
-------
- install miniconda
- install ffmpeg and git
- create the environment: ```conda create -n EmmyAI python=3.10.10```
- activate the environment: ```conda activate EmmyAI```
- install environment dependencies: ```pip install -r requirements.txt```
- route audio from python to vb-cable input, then from vb-cable input to vtube studio
- enable microphone with preview audio for vtuber model in vtube studio

Debugging
-------
- "running scripts is disabled on this system": ```Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser```
- "pyaudio wheel could not be built": install pyaudio
