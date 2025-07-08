"""
app.py - Flexible Text2SQL Inference App

Switch between T5 and Llama (Ollama) models by setting the USE_T5 flag below.
- USE_T5 = True: Use T5 (fast, less accurate on small models)
- USE_T5 = False: Use Llama/Ollama (slower, more accurate, needs more resources)

All model-specific code is modularized. Shared functions are outside the model blocks.
"""

from flask import Flask, request, jsonify, render_template, send_file, flash, url_for
import pyttsx3
import os
import speech_recognition as sr
import mysql.connector
import subprocess
import re
import torch
from functools import lru_cache
import gc

# --- CONFIG: Set this to True for T5, False for Llama/Ollama ---
USE_T5 =    False

app = Flask(__name__)
app.secret_key = 'supersecretkey'

engine = pyttsx3.init()

# Configure database connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Aashi@1234',
    'database': 'mydatabase',
}

# Enhanced schema representation
SCHEMA = """
### Database Schema ###
Table: employees
Columns: 
- id (int, PK)
- name (varchar)
- position (varchar)
- join_date (date)
- department_id (int, FK to departments.id)

Table: departments
Columns: 
- id (int, PK)
- name (varchar)
- location (varchar)

Relationships:
- employees.department_id → departments.id
"""

# Ensure audio directory exists
audio_dir = 'audio_files'
if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)

def clear_audio_folder():
    for filename in os.listdir(audio_dir):
        file_path = os.path.join(audio_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f'Error deleting file {file_path}: {e}')

def execute_safe_query(sql):
    conn = None
    cursor = None
    try:
        # Fix common table name errors
        sql = re.sub(r'employeesmployees', 'employees', sql, flags=re.IGNORECASE)
        sql = re.sub(r'departmentspartments', 'departments', sql, flags=re.IGNORECASE)
        
        # Fix case sensitivity for UX designer query
        if "ux designer" in sql.lower():
            sql = "SELECT employees.name FROM employees WHERE LOWER(position) LIKE '%ux designer%'"
            
        # Block dangerous keywords
        blocked_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        if any(keyword in sql.upper() for keyword in blocked_keywords):
            return "Blocked: Potentially dangerous operation", []
            
        # Add LIMIT to prevent large results
        sql_upper = sql.upper()
        if "SELECT" in sql_upper and "LIMIT" not in sql_upper:
            if "COUNT(" not in sql_upper:  # Don't add LIMIT to counts
                sql += " LIMIT 100"
                
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(sql)
        
        results = cursor.fetchall()
        columns = [col[0] for col in cursor.description] if cursor.description else []
        return results, columns
        
    except mysql.connector.Error as err:
        return f"Database error: {err}", []
    except Exception as e:
        return f"Error: {str(e)}", []
    finally:
        if conn and conn.is_connected():
            if cursor:
                cursor.close()
            conn.close()

# --- Model Loading ---
if USE_T5:
    from transformers import T5Tokenizer, T5ForConditionalGeneration
    T5_MODEL_PATH = "./sql_generator/t5_base_finetuned_model"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    t5_tokenizer = T5Tokenizer.from_pretrained(T5_MODEL_PATH)
    t5_model = T5ForConditionalGeneration.from_pretrained(T5_MODEL_PATH).to(device)
else:
    import ollama
    # You can adjust the model name as needed
    LLAMA_MODEL_NAME = "llama3.2:3b"
    # No need to load the model in advance with Ollama; it loads on request

# --- Shared Utility Functions ---
def format_results(results, columns=None):
    """Improved result formatting"""
    if isinstance(results, str):
        return results  # Error message
    if not results:
        return "No results found"
    if columns:
        # Handle multiple columns
        if len(columns) > 1:
            formatted = []
            for row in results:
                row_data = [str(row.get(col, '')) for col in columns]
                formatted.append(", ".join(row_data))
            return "\n".join(formatted)
        # Handle single column
        return "\n".join([str(row.get(columns[0], '')) for row in results])
    # Fallback for tuple results
    if results and isinstance(results[0], tuple):
        return "\n".join([", ".join(map(str, row)) for row in results])
    return "Unexpected result format"

def validate_and_correct_sql(sql: str, user_text: str = '') -> str:
    # Fix common typos
    sql = re.sub(r'\bemployeess?\b', 'employees', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\bdepartmentss?\b', 'departments', sql, flags=re.IGNORECASE)
    
    # Remove double aliasing in SELECT clause
    sql = re.sub(r'(\bAS\s+\w+)\s+AS\s+', r'\1 ', sql, flags=re.IGNORECASE)
    
    # Remove aliases from WHERE clause conditions
    sql = re.sub(r'(\bWHERE\s+[^\s]+)\s+AS\s+\w+\s*([=<>!]+)', r'\1 \2', sql, flags=re.IGNORECASE)
    
    # Only add JOIN and related logic if both e. and d. are referenced
    if re.search(r'\be\.', sql) and re.search(r'\bd\.', sql):
        # Ensure JOIN condition exists
        if " JOIN " in sql.upper() and " ON " not in sql.upper():
            sql += " ON employees.department_id = departments.id"
        
        # Add table aliases if missing
        if not re.search(r'\bFROM\s+employees\s+[ed]', sql, re.IGNORECASE):
            sql = re.sub(r'\bFROM\s+employees\b', 'FROM employees e', sql, flags=re.IGNORECASE)
        if not re.search(r'\bFROM\s+departments\s+[ed]', sql, re.IGNORECASE):
            sql = re.sub(r'\bFROM\s+departments\b', 'FROM departments d', sql, flags=re.IGNORECASE)
        
        # Qualify ambiguous columns
        sql = re.sub(r'(?<![ed]\.)\bname\b', 'e.name', sql, flags=re.IGNORECASE)
        # Smart aliasing: only alias if both e.name and d.name are present in SELECT and not already aliased
        select_match = re.match(r'^(\s*SELECT\s+)(.*?)(\s+FROM\s+.*)', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_prefix = select_match.group(1)
            select_clause = select_match.group(2)
            rest_of_sql = select_match.group(3)
            # Only alias in SELECT, not in WHERE
            if re.search(r'\be\.name\b', select_clause) and re.search(r'\bd\.name\b', select_clause):
                # Alias e.name as employee, d.name as department only if not already aliased
                select_clause = re.sub(r'\be\.name\b(?!\s+AS\s+employee)', 'e.name AS employee', select_clause, flags=re.IGNORECASE)
                select_clause = re.sub(r'\bd\.name\b(?!\s+AS\s+department)', 'd.name AS department', select_clause, flags=re.IGNORECASE)
                sql = select_prefix + select_clause + rest_of_sql
    elif re.search(r'\be\.', sql) and not re.search(r'\bd\.', sql):
        # Only employees table referenced: remove d. but keep e.
        sql = re.sub(r'\bd\.', '', sql, flags=re.IGNORECASE)
    elif re.search(r'\bd\.', sql) and not re.search(r'\be\.', sql):
        # Only departments table referenced: remove e. but keep d.
        sql = re.sub(r'\be\.', '', sql, flags=re.IGNORECASE)
    else:
        # No aliases, leave as is
        pass
    
    # Add missing SELECT clause
    if not re.search(r'^\s*SELECT\s+', sql, re.IGNORECASE):
        if "COUNT" in sql.upper():
            sql = "SELECT COUNT(*) " + sql
        else:
            sql = "SELECT * " + sql
    
    # Add LIMIT clause if missing
    sql_upper = sql.upper()
    if "SELECT" in sql_upper and "LIMIT" not in sql_upper:
        if "COUNT(" not in sql_upper and "GROUP BY" not in sql_upper:
            sql = re.sub(r';\s*$', '', sql) + " LIMIT 100"

    # Remove unnecessary JOIN with employees if only departments info is needed
    if re.search(r'FROM departments', sql, re.IGNORECASE) and not re.search(r'e\.', sql):
        sql = re.sub(r'JOIN employees e ON d.id = e.department_id', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'JOIN employees e', '', sql, flags=re.IGNORECASE)

    # Remove unnecessary JOINs if only one table's columns are referenced in SELECT and WHERE
    select_and_where = ''
    select_match = re.match(r'^(\s*SELECT\s+.*?)(\s+FROM\s+.*)', sql, re.IGNORECASE | re.DOTALL)
    if select_match:
        select_and_where = select_match.group(1) + select_match.group(2)
        # If only d. is referenced, remove JOIN employees
        if re.search(r'\bd\.', select_and_where) and not re.search(r'\be\.', select_and_where):
            sql = re.sub(r'JOIN employees e ON d.id = e.department_id', '', sql, flags=re.IGNORECASE)
            sql = re.sub(r'JOIN employees e', '', sql, flags=re.IGNORECASE)
        # If only e. is referenced, remove JOIN departments
        if re.search(r'\be\.', select_and_where) and not re.search(r'\bd\.', select_and_where):
            sql = re.sub(r'JOIN departments d ON e.department_id = d.id', '', sql, flags=re.IGNORECASE)
            sql = re.sub(r'JOIN departments d', '', sql, flags=re.IGNORECASE)

    # If the query is only about position (not department), remove department from SELECT and remove JOIN
    if 'position' in sql.lower() and 'department' not in sql.lower():
        # Remove department from SELECT
        sql = re.sub(r',?\s*d\.name\s*(AS\s+\w+)?', '', sql, flags=re.IGNORECASE)
        # Remove JOIN with departments if present
        sql = re.sub(r'JOIN departments d ON e\.department_id = d\.id', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'JOIN departments d', '', sql, flags=re.IGNORECASE)

    # If the user_text contains 'position' and the SQL does not select 'position', rewrite the SELECT clause robustly
    if user_text and 'position' in user_text.lower() and not re.search(r'select\s+[^;]*position', sql, re.IGNORECASE):
        # Find the WHERE clause (if any)
        where_match = re.search(r'\bWHERE\b.*', sql, re.IGNORECASE)
        where_clause = where_match.group(0) if where_match else ''
        # Find the LIMIT clause (if any)
        limit_match = re.search(r'\bLIMIT\b.*', sql, re.IGNORECASE)
        limit_clause = limit_match.group(0) if limit_match else ''
        # Build the new SQL
        sql = f"SELECT position FROM employees {where_clause} {limit_clause}".strip()

    # If the user_text is about department location and the SQL is filtering on e.name, rewrite to filter on d.name
    if user_text and 'location' in user_text.lower() and 'department' in user_text.lower():
        # Replace WHERE e.name = ... with WHERE d.name = ...
        sql = re.sub(r'WHERE\s+e\.name\s*=\s*([\'\"].*?[\'\"]|\w+)', r'WHERE d.name = \1', sql, flags=re.IGNORECASE)

    return sql

def execute_and_format(sql):
    results, columns = execute_safe_query(sql)
    return format_results(results, columns)

# --- Model-Specific Inference Functions ---
def process_question_t5(user_text):
    try:
        input_text = user_text  # Use just the question, as in your training data
        input_ids = t5_tokenizer(input_text, return_tensors="pt").input_ids.to(device)
        outputs = t5_model.generate(input_ids, max_length=128)
        generated_sql = t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated_sql = validate_and_correct_sql(generated_sql)
        print(f"T5 Generated SQL: {generated_sql}")
        return execute_and_format(generated_sql)
    except Exception as e:
        return f"Error: {str(e)}"

def process_question_llama(user_text):
    try:
        # Enhanced prompt engineering
        prompt = f"""
        ### Task ###
        Convert natural language to complete MySQL query using ONLY these tables:
        {SCHEMA}
        
        ### Instructions ###
        1. ALWAYS include a FROM clause
        2. Use table aliases: employees AS e, departments AS d
        3. Qualify ambiguous columns (e.name, d.name)
        4. Use explicit JOIN conditions: e.department_id = d.id
        5. For date comparisons, use 'YYYY-MM-DD' format
        6. Return ONLY the SQL query, no explanations
        
        ### Examples ###
        Q: List all employees and their departments
        A: SELECT e.name AS employee, d.name AS department FROM employees e JOIN departments d ON e.department_id = d.id
        
        Q: How many employees in Engineering?
        A: SELECT COUNT(*) FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = 'Engineering'
        
        Q: Who joined after 2023?
        A: SELECT e.name, e.position FROM employees e WHERE e.join_date > '2023-01-01'
        
        ### Current Question ###
        {user_text}
        """
        
        client = ollama.Client(host='http://127.0.0.1:11434')
        response = client.generate(
            model="llama3.2:3b",
            prompt=prompt,
            options={
                'temperature': 0.1,
                'num_ctx': 4096,
                'num_thread': 8,
                'stop': [';', '\n']
            }
        )
        
        # Extract SQL from response
        generated_sql = response['response'].strip()
        if generated_sql.startswith("```sql"):
            generated_sql = generated_sql[7:-3].strip()
        elif generated_sql.startswith("SELECT"):
            generated_sql = generated_sql.split(';')[0].strip() + ';'
        
        # Apply validation and correction
        corrected_sql = validate_and_correct_sql(generated_sql, user_text)
        print(f"Generated SQL: {generated_sql}")
        print(f"Corrected SQL: {corrected_sql}")
        
        return execute_and_format(corrected_sql)
    except Exception as e:
        return f"Error: {str(e)}"

# --- Unified Inference Entry Point ---
def process_question(user_text):
    if USE_T5:
        return process_question_t5(user_text)
    else:
        return process_question_llama(user_text)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    try:
        text = request.form['text']
        output_file = os.path.join(audio_dir, 'output.mp3')

        # Generate speech
        engine.save_to_file(text, output_file)
        engine.runAndWait()

        # Save text to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO texts (text) VALUES (%s)", (text,))
        conn.commit()
        cursor.close()
        conn.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            audio_url = url_for('serve_tts_audio')
            return jsonify({'audio_url': audio_url})

        flash('Text has been converted to speech!', 'success')
        return send_file(output_file, as_attachment=True)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 500
        flash(f'Error: {str(e)}', 'error')
        return render_template('index.html')

@app.route('/tts-audio')
def serve_tts_audio():
    output_file = os.path.join(audio_dir, 'output.mp3')
    return send_file(output_file, mimetype='audio/mpeg')

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    try:
        if 'audio' not in request.files:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'No file part'}), 400
            flash('No file part', 'error')
            return render_template('index.html')

        file = request.files['audio']
        if file.filename == '':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'No selected file'}), 400
            flash('No selected file', 'error')
            return render_template('index.html')

        clear_audio_folder()

        recognizer = sr.Recognizer()
        webm_path = os.path.join(audio_dir, 'uploaded_audio.webm')
        audio_file_path = os.path.join(audio_dir, 'uploaded_audio.wav')
        file.save(webm_path)

        subprocess.run(['ffmpeg', '-y', '-i', webm_path, audio_file_path], check=True)

        with sr.AudioFile(audio_file_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

            # Save text to database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO texts (text) VALUES (%s)", (text,))
            conn.commit()
            cursor.close()
            conn.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            result_html = render_template('result.html', converted_text=text)
            return result_html

        flash('Speech has been converted to text!', 'success')
        return render_template('index.html', converted_text=text)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 500
        flash(f'Error: {str(e)}', 'error')
        return render_template('index.html')
    
@app.route('/ask', methods=['POST'])
def ask():
    user_text = request.form.get('text', '')
    if not user_text:
        return jsonify({'answer': 'No question provided.'})
    answer = process_question(user_text)
    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)