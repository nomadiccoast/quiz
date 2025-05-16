
import requests
import json
import re
from flask import Flask, request, render_template, redirect, url_for, session
import os

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Use a secure key in production



# Free Groq API key
api_key = "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"

# Save questions to a JSON file
def save_question_to_file(question_data, topic):
    try:
        with open('question.json', 'r') as f:
            questions = json.load(f)
            if not isinstance(questions, list):
                questions = []
    except (FileNotFoundError, json.JSONDecodeError):
        questions = []

    questions.append({
        "topic": topic,
        "question": question_data
    })

    with open('question.json', 'w') as f:
        json.dump(questions, f, indent=2)

# Extract JSON from text response
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

# Generate a question from the Groq API
def generate_question(topic):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{
            "role": "user",
            "content": f"Generate exactly one CBSE previous year question for the topic: {topic}. "
                       f"Return ONLY the JSON object with these fields: "
                       f"'question', 'options', 'answer', and 'explanation'. "
                       f"No extra text or formatting, just valid JSON."
                        f"only give valid JSON"
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
            response_content = data['choices'][0]['message']['content']
            question_data = extract_json_from_response(response_content)

            if question_data:
                if all(field in question_data for field in ['question', 'options', 'answer', 'explanation']):
                    save_question_to_file(question_data, topic)
                    return question_data
                else:
                    print("Missing required fields in response.")
            else:
                print("Invalid JSON format from API.")
        else:
            print(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API Exception: {e}")
    return None

# Home page
@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')

# Start quiz
@app.route("/start", methods=["POST"])
def start():
    session.clear()
    topic = request.form["topic"].strip()
    if not topic:
        return redirect(url_for("index"))

    session["topic"] = topic
    session["num_questions"] = min(int(request.form["num_questions"]), 20)
    session["index"] = 0
    session["score"] = 0
    session["quiz"] = []

    first_question = generate_question(topic)
    if first_question:
        session["quiz"].append(first_question)
        return redirect(url_for("quiz"))
    return redirect(url_for("index"))

# Quiz route
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if not isinstance(session.get("quiz"), list):
        session["quiz"] = []

    if request.method == "POST":
        idx = session["index"]
        ans = request.form["answer"]
        correct = session["quiz"][idx]["answer"]
        session["feedback"] = "Correct!" if ans == correct else f"Wrong! Correct answer: {correct}"
        if ans == correct:
            session["score"] += 1
        session["index"] += 1

    if session["index"] < session["num_questions"]:
        if len(session["quiz"]) <= session["index"]:
            next_question = generate_question(session["topic"])
            if next_question:
                session["quiz"].append(next_question)
            else:
                return redirect(url_for("index"))

    if session["index"] >= session["num_questions"]:
        return redirect(url_for("result"))

    return render_template('quiz.html',
        topic=session["topic"],
        quiz=session["quiz"],
        index=session["index"],
        num_questions=session["num_questions"],
        feedback=session.pop("feedback", None))

# Result page
@app.route("/result")
def result():
    if not session.get("quiz"):
        return redirect(url_for("index"))
    score = session["score"]
    total = session["num_questions"]
    session.clear()
    return render_template('result.html', score=score, total=total)

# Run app
if __name__ == "__main__":

 app.run(debug=True)


import requests
import json
import re
from flask import Flask, request, render_template, redirect, url_for, session

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Use a secure key in production

# Free Groq API key
api_key = "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"

# Save questions to a JSON file
def save_question_to_file(question_data, topic):
    try:
        with open('question.json', 'r') as f:
            questions = json.load(f)
            if not isinstance(questions, list):
                questions = []
    except (FileNotFoundError, json.JSONDecodeError):
        questions = []

    questions.append({
        "topic": topic,
        "question": question_data
    })

    with open('question.json', 'w') as f:
        json.dump(questions, f, indent=2)

# Extract JSON from text response
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

# Generate a question from the Groq API
def generate_question(topic):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{
            "role": "user",
            "content": f"Generate exactly one CBSE previous year question for the topic: {topic}. "
                       f"Return ONLY the JSON object with these fields: "
                       f"'question', 'options', 'answer', and 'explanation'. "
                       f"No extra text or formatting, just valid JSON."
                        f"only give valid JSON"
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
            response_content = data['choices'][0]['message']['content']
            question_data = extract_json_from_response(response_content)

            if question_data:
                if all(field in question_data for field in ['question', 'options', 'answer', 'explanation']):
                    save_question_to_file(question_data, topic)
                    return question_data
                else:
                    print("Missing required fields in response.")
            else:
                print("Invalid JSON format from API.")
        else:
            print(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"API Exception: {e}")
    return None

# Home page
@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')

# Start quiz
@app.route("/start", methods=["POST"])
def start():
    session.clear()
    topic = request.form["topic"].strip()
    if not topic:
        return redirect(url_for("index"))

    session["topic"] = topic
    session["num_questions"] = min(int(request.form["num_questions"]), 20)
    session["index"] = 0
    session["score"] = 0
    session["quiz"] = []

    first_question = generate_question(topic)
    if first_question:
        session["quiz"].append(first_question)
        return redirect(url_for("quiz"))
    return redirect(url_for("index"))

# Quiz route
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if not isinstance(session.get("quiz"), list):
        session["quiz"] = []

    if request.method == "POST":
        idx = session["index"]
        ans = request.form["answer"]
        correct = session["quiz"][idx]["answer"]
        session["feedback"] = "Correct!" if ans == correct else f"Wrong! Correct answer: {correct}"
        if ans == correct:
            session["score"] += 1
        session["index"] += 1

    if session["index"] < session["num_questions"]:
        if len(session["quiz"]) <= session["index"]:
            next_question = generate_question(session["topic"])
            if next_question:
                session["quiz"].append(next_question)
            else:
                return redirect(url_for("index"))

    if session["index"] >= session["num_questions"]:
        return redirect(url_for("result"))

    return render_template('quiz.html',
        topic=session["topic"],
        quiz=session["quiz"],
        index=session["index"],
        num_questions=session["num_questions"],
        feedback=session.pop("feedback", None))

# Result page
@app.route("/result")
def result():
    if not session.get("quiz"):
        return redirect(url_for("index"))
    score = session["score"]
    total = session["num_questions"]
    session.clear()
    return render_template('result.html', score=score, total=total)

# Run app
if __name__ == "__main__":
    app.run(debug=True)
