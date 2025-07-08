import mysql.connector
import json

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Aashi@1234',
    'database': 'mydatabase'
}

# Connect to database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Prepare dataset list
dataset = []

# 1. Total employees question
dataset.append({
    "question": "How many employees work here?",
    "sql": "SELECT COUNT(*) FROM employees"
})

# 2. CEO name
dataset.append({
    "question": "Who is the CEO of the company?",
    "sql": "SELECT name FROM employees WHERE position LIKE '%ceo%'"
})

# 3. List all engineers
dataset.append({
    "question": "List all engineers in the company",
    "sql": "SELECT name FROM employees WHERE position LIKE '%engineer%'"
})

# 4. List employees joined after 2023
dataset.append({
    "question": "Who joined after 2023?",
    "sql": "SELECT name FROM employees WHERE join_date > '2023-01-01'"
})

cursor.execute("SELECT name FROM employees")
names = cursor.fetchall()

# Adding personalized employee position questions
for (name,) in names:
    dataset.append({
        "question": f"What is {name}'s position?",
        "sql": f"SELECT position FROM employees WHERE name = '{name}'"
    })

# Save to JSON file
with open("employee_dataset.json", "w") as f:
    json.dump(dataset, f, indent=4)

print("✅ Custom dataset generated as 'employee_dataset.json'")

# Close connection
cursor.close()
conn.close()
