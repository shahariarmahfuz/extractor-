import os
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Updated upload folder to /tmp
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_audio(video_path, audio_path):
    """Extract audio from video using FFmpeg"""
    try:
        # Using absolute path to ffmpeg to be safe
        os.system(f'/usr/bin/ffmpeg -i "{video_path}" -q:a 0 -map a "{audio_path}" -y')
        return True
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False

# def cleanup_old_files():
#     """Clean up files older than 5 minutes"""
#     while True:
#         now = datetime.now()
#         for filename in os.listdir(app.config['UPLOAD_FOLDER']):
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             try:
#                 file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
#                 if now - file_time > timedelta(minutes=5):
#                     os.remove(file_path)
#                     print(f"Deleted old file: {filename}")
#             except Exception as e:
#                 print(f"Error deleting file {filename}: {e}")
#         time.sleep(60)  # Check every minute

# Start cleanup thread
# cleanup_thread = threading.Thread(target=cleanup_old_files)
# cleanup_thread.daemon = True
# cleanup_thread.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Save the uploaded video
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)

            # Create audio filename
            audio_filename = f"{os.path.splitext(filename)[0]}.mp3"
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)

            # Extract audio
            if extract_audio(video_path, audio_path):
                # Delete the video file immediately
                try:
                    os.remove(video_path)
                except Exception as e:
                    print(f"Error deleting video file: {e}")

                # Provide download link for the audio
                return render_template('index.html',
                                    audio_file=audio_filename,
                                    message="Audio extracted successfully!")
            else:
                return render_template('index.html',
                                    error="Failed to extract audio from video.")

    return render_template('index.html')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
