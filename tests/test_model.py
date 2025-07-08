import ollama
import mysql.connector
import re

# Database connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Aashi@1234',
    'database': 'mydatabase'
}

def run_query(sql):
    """Execute SQL query safely"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        return f"ERROR: {str(e)}"

def generate_sql_with_ollama(question):
    schema = """employees(id,name,position,join_date,department_id) 
                departments(id,name,location) 
                department_id=employees.department_id=departments.id"""
    prompt = f"Database Schema:\n{schema}\n\nConvert to MySQL SQL: {question}\nReturn ONLY SQL:"
    response = ollama.generate(
        model='llama3.2:3b',
        prompt=prompt,
        options={'temperature': 0, 'num_ctx': 2048}
    )
    return response['response'].strip()

def extract_sql(text):
    # Remove code block markers
    text = re.sub(r'```sql|```', '', text, flags=re.IGNORECASE).strip()
    # Find the first SELECT statement and everything until the first semicolon
    match = re.search(r'(SELECT[\s\S]+?;)', text, re.IGNORECASE)
    if match:
        sql = match.group(1)
    else:
        # Fallback: return the first line that starts with SELECT
        for line in text.splitlines():
            if line.strip().upper().startswith('SELECT'):
                sql = line.strip()
                break
        else:
            sql = text.strip()
    # Fix common syntax issues
    sql = re.sub(r'COUNT\s*\(', 'COUNT(', sql)
    sql = re.sub(r'DISTINCT\s*\(', 'DISTINCT(', sql)
    return sql

def test_question(question):
    print(f"\n{'='*50}")
    print(f"Question: {question}")
    generated_sql = generate_sql_with_ollama(question)
    generated_sql = extract_sql(generated_sql)
    print(f"Generated SQL: {generated_sql}")
    results = run_query(generated_sql)
    print(f"Results: {results}")

# Test questions
test_questions = [
    "How many employees?",
    "Who is the CEO?",
    "List engineers",
    "Employees hired after 2023",
    "What is Priya Patel's position?",
    "When did Rohan join?",
    "Most recent hires",
    # New security/edge case tests
    "Total engineers in New York",
    "Average salary by department",  # Test handling of non-existent columns
    "Employees hired before 2023 in Marketing",
    "Who reports to Priya Patel?"
]

print("🔥 Starting Tests 🔥")
for q in test_questions:
    test_question(q)