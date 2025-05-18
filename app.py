import os
import json
import re
import requests
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace this in production

api_key = "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"

# Ensure question.json is always saved in the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTION_FILE = os.path.join(BASE_DIR, 'question.json')

# Save question to JSON file
def save_question_to_file(question_data, topic):
    try:
        with open(QUESTION_FILE, 'r') as f:
            questions = json.load(f)
            if not isinstance(questions, list):
                questions = []
    except (FileNotFoundError, json.JSONDecodeError):
        questions = []

    questions.append({
        "topic": topic,
        "question": question_data
    })

    with open(QUESTION_FILE, 'w') as f:
        json.dump(questions, f, indent=2)

    print(f"[✅] Saved question to {QUESTION_FILE}")

# Extract JSON from response
def extract_json_from_response(text):
    pattern = r'```(?:json)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

# Generate a question using Groq API
def generate_question(topic):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{
            "role": "user",
            "content": (
                f"Generate one unique CBSE previous year question based on the topic: {topic}. "
                f"Ensure it is significantly different from any recent questions—change the wording, style, and options. "
                f"Vary the type of question (MCQ, assertion-reason, match the following, diagram-based, etc.) where applicable. "
                f"Make sure all four options are plausible but only one is correct. "
                f"Format the output strictly as a single valid JSON object with the following fields: "
                f"'question' (string), 'options' (list of 4 strings), 'answer' (string, must match one of the options), and 'explanation' (string). "
                f"Return ONLY valid JSON. No text, no commentary—only the JSON object. "
                f"Make the output different each and every time, even if the topic is the same."
            )
        }]
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            question_data = extract_json_from_response(content)

            if question_data:
                required_keys = ['question', 'options', 'answer', 'explanation']
                if all(k in question_data for k in required_keys):
                    save_question_to_file(question_data, topic)
                    return question_data
                else:
                    print("[❌] Missing required fields in AI response.")
            else:
                print("[❌] Invalid JSON format returned from Groq.")
        else:
            print(f"[❌] API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[❌] API Exception: {e}")
    return None

# Home page
@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')

# Start quiz
@app.route("/start", methods=["POST"])
def start():
    session.clear()
    topic = request.form.get("topic", "").strip()
    if not topic:
        return redirect(url_for("index"))

    try:
        num_questions = int(request.form.get("num_questions", 5))
    except ValueError:
        num_questions = 5

    session["topic"] = topic
    session["num_questions"] = min(num_questions, 20)
    session["index"] = 0
    session["score"] = 0
    session["quiz"] = []

    question = generate_question(topic)
    if question:
        session["quiz"].append(question)
        return redirect(url_for("quiz"))
    return redirect(url_for("index"))

# Quiz page
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if not isinstance(session.get("quiz"), list):
        session["quiz"] = []

    if request.method == "POST":
        idx = session["index"]
        answer = request.form.get("answer")
        correct = session["quiz"][idx]["answer"]
        session["feedback"] = "Correct!" if answer == correct else f"Wrong! Correct answer: {correct}"
        if answer == correct:
            session["score"] += 1
        session["index"] += 1

    if session["index"] < session["num_questions"]:
        if len(session["quiz"]) <= session["index"]:
            question = generate_question(session["topic"])
            if question:
                session["quiz"].append(question)
            else:
                return redirect(url_for("index"))

        return render_template('quiz.html',
            topic=session["topic"],
            quiz=session["quiz"],
            index=session["index"],
            num_questions=session["num_questions"],
            feedback=session.pop("feedback", None))

    return redirect(url_for("result"))

# Result page
@app.route("/result", methods=["GET"])
def result():
    if not session.get("quiz"):
        return redirect(url_for("index"))

    score = session.get("score", 0)
    total = session.get("num_questions", 0)
    session.clear()
    return render_template('result.html', score=score, total=total)

# View all saved questions (for debug)
@app.route("/all-questions", methods=["GET"])
def all_questions():
    try:
        with open(QUESTION_FILE, 'r') as f:
            data = json.load(f)
        return {"questions": data}
    except Exception as e:
        return {"error": str(e)}, 500

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
