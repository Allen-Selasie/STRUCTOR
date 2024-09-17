from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import google.generativeai as genai
import re
import os

app = Flask(__name__)

# Configure the Google Gemini API
Api_key = ''  # Replace with your actual API key
genai.configure(api_key=Api_key)

# Route for the homepage (form upload)
@app.route('/')
def index():
    return render_template('index.html')

# Route to upload the CSV file
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Load the CSV into pandas DataFrame with error handling
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Convert the DataFrame to a CSV string for the API request
    csv_string = df.to_csv(index=False)

    # Pass the content to Google Gemini API for cleanup
    prompt = f"use a meaningful csv structure to populate the dataset:\n{csv_string} only"
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    # Extract CSV content between ```csv and ```
    csv_content = re.search(r'```csv(.*?)```', response.text, re.DOTALL)
    if not csv_content:
        return jsonify({'error': 'No cleaned CSV content found'}), 500

    # Save the cleaned CSV content to a file
    cleaned_csv = csv_content.group(1).strip()
    cleaned_csv_path = 'cleaned_data.csv'
    with open(cleaned_csv_path, 'w') as f:
        f.write(cleaned_csv)

    # Load cleaned CSV into DataFrame for display on frontend
    try:
        cleaned_df = pd.read_csv(cleaned_csv_path)
        cleaned_table = cleaned_df.to_html(classes='table table-striped')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'cleaned_table': cleaned_table,
        'download_url': '/download'
    })

# Route to download the cleaned CSV
@app.route('/download')
def download_file():
    cleaned_csv_path = 'cleaned_data.csv'
    return send_file(cleaned_csv_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
