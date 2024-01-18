# Installation
1. Install the Python packages in requirements.txt (`pip install -r requirements.txt`).
2. Install FFMPEG (https://ffmpeg.org/download.html), VB-Cable (https://download.vb-audio.com/), and VTube Studio.
3. Route the audio from Python to VB Cable's input, and from VB Cable's input to VTube Studio.
4. In VTube Studio, enable "preview audio".

# Debugging
- "running scripts is disabled on this system": Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` on Powershell.
- "pyaudio wheel could not be built": Ensure PyAudio (https://pypi.org/project/PyAudio/) is properly installed.
