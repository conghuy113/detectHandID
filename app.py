import os
import subprocess
import requests
from flask import Flask, request, redirect, render_template, send_from_directory

app = Flask(__name__)

# Define the directory where the video will be saved
UPLOAD_FOLDER = 'D:/DetectHandID'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML template

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Route to handle video upload, save, and conversion
@app.route('/save-video', methods=['POST'])
def save_video():
    # Check if 'video' is in the request files
    if 'video' not in request.files:
        return "No video part", 400

    video = request.files['video']

    # Check if the filename is empty
    if video.filename == '':
        return "No selected file", 400

    # Save the WebM video file in the designated folder
    webm_filepath = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    video.save(webm_filepath)

    # Check if the file is saved correctly
    if os.path.exists(webm_filepath):
        print(f"WebM video saved at: {webm_filepath}")
    else:
        return "Failed to save WebM video", 500

    try:
        # Convert the WebM video to MP4
        mp4_filepath = convert_to_mp4(webm_filepath)

        # Remove the WebM file after conversion to MP4
        os.remove(webm_filepath)

        # Extract the MP4 file name (without the directory)
        mp4_filename = os.path.basename(mp4_filepath)

        # Call the Java API to process the MP4 file
        response = requests.post(
            'http://localhost:8080/api/video/process',  # URL of the Java API
            data={'filename': mp4_filename}  # Send only the filename
        )

        print("Java API response:", response.text)

        return f"Video saved and sent to Java API: {mp4_filepath}", 200

    except Exception as e:
        return f"Error during conversion or API call: {str(e)}", 500

# Function to convert WebM to MP4 using ffmpeg
def convert_to_mp4(webm_filepath):
    """Convert a WebM file to MP4 format using ffmpeg."""
    mp4_filepath = webm_filepath.replace('.webm', '.mp4')

    # ffmpeg command to convert WebM to MP4
    command = [
        'ffmpeg', '-i', webm_filepath,  # Input WebM file
        '-c:v', 'libx264',  # Video codec
        '-c:a', 'aac',  # Audio codec
        '-strict', 'experimental',  # Required for aac codec
        mp4_filepath  # Output MP4 file
    ]

    # Run the ffmpeg command
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode != 0:
        # Log the ffmpeg error if the command fails
        print(f"ffmpeg error: {process.stderr.decode('utf-8')}")
        raise Exception("ffmpeg failed to convert the video")

    print(f"MP4 video saved at: {mp4_filepath}")
    return mp4_filepath

if __name__ == '__main__':
    app.run(debug=True)