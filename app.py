from flask import Flask, request, jsonify
import whisper
from flask_cors import CORS
import tempfile
import os
import uuid
import random
import difflib
from Levenshtein import distance as levenshtein_distance

app = Flask(__name__)
CORS(app)

# Load whisper model (tiny for speed)
model = whisper.load_model("tiny")

# In-memory storage for questions
questions = [
    "The quick brown fox jumps over the lazy dog",
    "Hello world, this is a test sentence",
    "Python is a great programming language",
    "Machine learning is transforming the world",
    "Speech recognition technology is amazing"
]


def calculate_accuracy(original, transcribed):
    """Calculate accuracy between original and transcribed text using multiple methods"""
    # Normalize text (lowercase, strip whitespace)
    original = original.lower().strip()
    transcribed = transcribed.lower().strip()

    # Method 1: SequenceMatcher (difflib)
    similarity_ratio = difflib.SequenceMatcher(None, original, transcribed).ratio()

    # Method 2: Levenshtein distance (normalized)
    max_len = max(len(original), len(transcribed))
    if max_len == 0:
        levenshtein_accuracy = 1.0
    else:
        levenshtein_accuracy = 1 - (levenshtein_distance(original, transcribed) / max_len)

    # Use the average of both methods
    accuracy = (similarity_ratio + levenshtein_accuracy) / 2
    return round(accuracy, 3)


@app.route("/transcribe", methods=["POST"])
def transcribe():
    print("Transcribing...")
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files["file"]

    # Save file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        audio_file.save(tmp.name)
        temp_path = tmp.name

    try:
        # Transcribe using Whisper
        result = model.transcribe(audio=temp_path, fp16=False)
        return jsonify({"result": result["text"]})
    finally:
        os.remove(temp_path)


@app.route("/new-question", methods=["GET"])
def new_question():
    print("getting new question...")
    """Returns a random question from the questions list"""
    if not questions:
        return jsonify({"error": "No questions available"}), 404

    random_question = random.choice(questions)
    question_id = str(uuid.uuid4())

    return jsonify({
        "id": question_id,
        "text": random_question
    })


@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    """Accept audio file and question text, transcribe audio and compare with question"""
    print("Processing answer submission...")

    # Check if audio file is present
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    # Check if question text is present
    if "question" not in request.form:
        return jsonify({"error": "No question text provided"}), 400

    audio_file = request.files["audio"]
    original_question = request.form["question"]

    # Save audio file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        audio_file.save(tmp.name)
        temp_path = tmp.name

    try:
        # Transcribe the audio
        result = model.transcribe(audio=temp_path, fp16=False)
        transcribed_text = result["text"]

        # Calculate accuracy
        accuracy = calculate_accuracy(original_question, transcribed_text)

        # Determine success based on accuracy threshold (e.g., 70%)
        success = accuracy >= 0.7

        if success:
            message = f"Great job! Your pronunciation accuracy is {accuracy * 100:.1f}%"
        else:
            message = f"Keep practicing! Your pronunciation accuracy is {accuracy * 100:.1f}%. Try speaking more clearly."

        return jsonify({
            "success": success,
            "message": message,
            "accuracy": accuracy,
            "transcribed": transcribed_text  # Optional: include transcription for debugging
        })

    finally:
        os.remove(temp_path)


@app.route("/audio-to-text", methods=["POST"])
def audio_to_text():
    """Simple audio to text transcription"""
    print("Converting audio to text...")

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files["file"]

    # Save file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        audio_file.save(tmp.name)
        temp_path = tmp.name

    try:
        # Transcribe using Whisper
        result = model.transcribe(audio=temp_path, fp16=False)
        return jsonify({"text": result["text"]})
    finally:
        os.remove(temp_path)


@app.route("/add-question", methods=["POST"])
def add_question():
    """Add a new question to the questions list"""
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    question_text = data["text"].strip()

    if not question_text:
        return jsonify({"error": "Question text cannot be empty"}), 400

    questions.append(question_text)
    print(f"Added new question: {question_text}")

    return jsonify({"success": True})


@app.route("/add-multiple-questions", methods=["POST"])
def add_multiple_questions():
    """Add multiple questions by transcribing multiple audio files"""
    print("Processing multiple audio files...")

    # Get all audio files from the request
    audio_files = []
    file_keys = [key for key in request.files.keys() if key.startswith('audio_')]

    if not file_keys:
        return jsonify({"error": "No audio files uploaded"}), 400

    # Sort the keys to maintain order
    file_keys.sort(key=lambda x: int(x.split('_')[1]))

    successful_additions = 0
    errors = []

    for file_key in file_keys:
        audio_file = request.files[file_key]

        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            audio_file.save(tmp.name)
            temp_path = tmp.name

        try:
            # Transcribe using Whisper
            result = model.transcribe(audio=temp_path, fp16=False)
            transcribed_text = result["text"].strip()

            if transcribed_text:
                questions.append(transcribed_text)
                successful_additions += 1
                print(f"Added question from {file_key}: {transcribed_text}")
            else:
                errors.append(f"Empty transcription for {file_key}")

        except Exception as e:
            errors.append(f"Error processing {file_key}: {str(e)}")
        finally:
            os.remove(temp_path)

    if successful_additions > 0:
        message = f"Successfully added {successful_additions} questions"
        if errors:
            message += f" with {len(errors)} errors"

        return jsonify({
            "success": True,
            "message": message,
            "added_count": successful_additions,
            "errors": errors if errors else None
        })
    else:
        return jsonify({
            "success": False,
            "message": "No questions were added",
            "errors": errors
        }), 400


@app.route("/questions", methods=["GET"])
def get_questions():
    """Get all current questions (useful for debugging/admin)"""
    return jsonify({
        "questions": questions,
        "count": len(questions)
    })


@app.route("/questions", methods=["DELETE"])
def clear_questions():
    """Clear all questions (useful for testing)"""
    global questions
    questions = []
    return jsonify({"success": True, "message": "All questions cleared"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)