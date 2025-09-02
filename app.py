from flask import Flask, render_template, request, redirect, url_for, session
from groq import Groq
import os
import re
import dotenv

dotenv.load_dotenv()
groq_api = os.getenv("groq_api")
client = Groq(api_key=groq_api)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  


def analyze_symptoms(symptoms, age=None, gender=None):
    PROMPT_TEMPLATE = f"""
    Symptoms: {symptoms}
    Age: {age if age else 'Not provided'}
    Gender: {gender if gender else 'Not provided'}

    You are a medical assistant. Based on the symptoms, provide:
    1. A simple summary of what these symptoms could mean.
    2. Possible causes (list).
    3. Advice on what to do next (list).

    Format your response like this:

    Summary:
    ...

    Possible Causes:
    - ...
    - ...

    Advice:
    - ...
    - ...

    Only reply in this format, nothing else.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": PROMPT_TEMPLATE
            }
        ],
        temperature=0.3,
        max_tokens=800,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    expected_response = response.choices[0].message.content
    print("Groq response:", expected_response)
    if not expected_response or expected_response.strip() == "":
        return None, "No response from Groq API. Please check your API key, prompt, or try again."

    # Parse plain text response
    summary = ""
    causes = []
    advice = []
    try:
        summary_match = re.search(r"Summary:\s*(.*?)(?:Possible Causes:|$)", expected_response, re.DOTALL)
        causes_match = re.search(r"Possible Causes:\s*(.*?)(?:Advice:|$)", expected_response, re.DOTALL)
        advice_match = re.search(r"Advice:\s*(.*)", expected_response, re.DOTALL)

        if summary_match:
            summary = summary_match.group(1).strip()
        if causes_match:
            causes = [line.strip('- ').strip() for line in causes_match.group(1).strip().split('\n') if line.strip()]
        if advice_match:
            advice = [line.strip('- ').strip() for line in advice_match.group(1).strip().split('\n') if line.strip()]

        result = {
            "summary": summary,
            "causes": causes,
            "advice": advice
        }
        return result, None
    except Exception as e:
        return None, f"Error parsing response: {e}. Raw response: {expected_response}"

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    if request.method == 'POST':
        symptoms = request.form.get('symptoms', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        if symptoms:
            result, error = analyze_symptoms(symptoms, age, gender)
            session['result'] = result
            session['error'] = None if result else error
            return redirect(url_for('index'))
        else:
            error = "Please provide your symptoms."
            session['result'] = None
            session['error'] = error
            return redirect(url_for('index'))
    else:
        result = session.pop('result', None)
        error = session.pop('error', None)
    return render_template('index.html', result=result, error=error)
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')
@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=False)