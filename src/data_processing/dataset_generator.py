import json
import random
import mysql.connector
from datetime import datetime

# Database connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Aashi@1234',
    'database': 'mydatabase'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Get all employees
cursor.execute("SELECT name, position, join_date FROM employees")
employee_data = cursor.fetchall()

# Create dataset
dataset = []

# 1. Core queries (essential questions)
core_queries = [
    ("How many employees work here?", "SELECT COUNT(*) FROM employees"),
    ("Who is the CEO?", "SELECT name FROM employees WHERE position LIKE '%CEO%'"),
    ("List all engineers", "SELECT name FROM employees WHERE position LIKE '%engineer%'"),
    ("Who joined after 2023?", "SELECT name FROM employees WHERE join_date > '2023-01-01'"),
    ("What positions do we have?", "SELECT DISTINCT position FROM employees"),
    ("Show management team", "SELECT name FROM employees WHERE position LIKE '%manager%'"),
    ("Most recent hires", "SELECT name FROM employees ORDER BY join_date DESC LIMIT 3"),
    ("Longest serving employees", "SELECT name FROM employees ORDER BY join_date ASC LIMIT 3")
]

# 2. Employee-specific queries
for name, position, join_date in employee_data:
    # Position queries
    dataset.append({
        "question": f"What is {name}'s position?",
        "sql": f"SELECT position FROM employees WHERE name = '{name}'"
    })
    
    dataset.append({
        "question": f"What job does {name} do?",
        "sql": f"SELECT position FROM employees WHERE name = '{name}'"
    })
    
    # Join date queries
    dataset.append({
        "question": f"When did {name} join the company?",
        "sql": f"SELECT join_date FROM employees WHERE name = '{name}'"
    })
    
    dataset.append({
        "question": f"What is {name}'s start date?",
        "sql": f"SELECT join_date FROM employees WHERE name = '{name}'"
    })
    
    # Position-type queries
    if 'engineer' in position.lower():
        dataset.append({
            "question": f"Is {name} an engineer?",
            "sql": f"SELECT name FROM employees WHERE name = '{name}' AND position LIKE '%engineer%'"
        })
    
    # Partial name queries - NEW
    last_name = name.split()[-1]  # Extract last name
    dataset.append({
        "question": f"What is {last_name}'s position?",
        "sql": f"SELECT position FROM employees WHERE name LIKE '%{last_name}%'"
    })
    
    dataset.append({
        "question": f"When did {name.split()[0]} join?",
        "sql": f"SELECT join_date FROM employees WHERE name LIKE '%{name.split()[0]}%'"
    })

# 3. Add core queries to dataset
for question, sql in core_queries:
    dataset.append({"question": question, "sql": sql})

# 4. Additional variations (20 questions)
additional_queries = [
    ("Total number of staff?", "SELECT COUNT(*) FROM employees"),
    ("Name of our chief executive?", "SELECT name FROM employees WHERE position LIKE '%CEO%'"),
    ("Show engineering team", "SELECT name FROM employees WHERE position LIKE '%engineer%'"),
    ("Employees hired since 2023", "SELECT name FROM employees WHERE join_date > '2023-01-01'"),
    ("Who has the longest tenure?", "SELECT name FROM employees ORDER BY join_date ASC LIMIT 1"),
    ("Newest team members", "SELECT name FROM employees ORDER BY join_date DESC LIMIT 3"),
    ("List management positions", "SELECT DISTINCT position FROM employees WHERE position LIKE '%manager%'"),
    ("Count of engineers", "SELECT COUNT(*) FROM employees WHERE position LIKE '%engineer%'"),
    ("All employee names", "SELECT name FROM employees ORDER BY name"),
    ("Hires in 2023", "SELECT name FROM employees WHERE YEAR(join_date) = 2023"),
    ("Non-engineer staff", "SELECT name FROM employees WHERE position NOT LIKE '%engineer%'"),
    ("Executive leadership", "SELECT name, position FROM employees WHERE position IN ('CEO', 'CFO')"),
    ("Staff hired last year", "SELECT name FROM employees WHERE YEAR(join_date) = YEAR(CURDATE()) - 1"),
    ("List UX designers", "SELECT name FROM employees WHERE position LIKE '%UX designer%'"),
    ("Product team members", "SELECT name FROM employees WHERE position LIKE '%product%'"),
    ("Marketing department", "SELECT name FROM employees WHERE position LIKE '%marketing%'"),
    ("Technical staff", "SELECT name FROM employees WHERE position LIKE '%engineer%' OR position LIKE '%developer%'"),
    ("Senior positions", "SELECT name FROM employees WHERE position LIKE '%senior%'"),
    ("Junior positions", "SELECT name FROM employees WHERE position LIKE '%junior%'"),
    ("Employee IDs and names", "SELECT id, name FROM employees")
]

# 5. Add additional queries to dataset
for question, sql in additional_queries:
    dataset.append({"question": question, "sql": sql})

# 6. Add targeted fix queries - NEW SECTION
fix_queries = [
    # CEO query fixes
    ("Who is the chief executive?", "SELECT name FROM employees WHERE position LIKE '%CEO%'"),
    ("Name of the top executive?", "SELECT name FROM employees WHERE position LIKE '%CEO%'"),
    ("Who is our chief executive officer?", "SELECT name FROM employees WHERE position LIKE '%CEO%'"),
    ("Who is the head of the company?", "SELECT name FROM employees WHERE position LIKE '%CEO%'"),
    ("Company leader?", "SELECT name FROM employees WHERE position LIKE '%CEO%'"),
    
    # Date query fixes
    ("Staff hired after 2023", "SELECT name FROM employees WHERE join_date > '2023-01-01'"),
    ("Employees joined since 2023", "SELECT name FROM employees WHERE join_date > '2023-01-01'"),
    ("Team members hired after 2023", "SELECT name FROM employees WHERE join_date > '2023-01-01'"),
    ("Employees hired this year", "SELECT name FROM employees WHERE YEAR(join_date) = YEAR(CURDATE())"),
    ("Hires in the last year", "SELECT name FROM employees WHERE join_date > DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"),
    
    # More partial name examples
    ("What is Verma's job?", "SELECT position FROM employees WHERE name LIKE '%Verma%'"),
    ("When did Singh start?", "SELECT join_date FROM employees WHERE name LIKE '%Singh%'"),
    ("What position does Sharma hold?", "SELECT position FROM employees WHERE name LIKE '%Sharma%'"),
    ("When did Kumar join?", "SELECT join_date FROM employees WHERE name LIKE '%Kumar%'"),
    
    # Position-specific fixes
    ("Who is the CFO?", "SELECT name FROM employees WHERE position LIKE '%CFO%'"),
    ("List HR staff", "SELECT name FROM employees WHERE position LIKE '%HR%'"),
    ("Marketing team members", "SELECT name FROM employees WHERE position LIKE '%marketing%'")
]

# Add fix queries to dataset
dataset.extend([{"question": q, "sql": s} for q, s in fix_queries])

# 7. Add comprehensive queries for better generalization - NEW
comprehensive_queries = [
    # Get all employees
    ("List all employees", "SELECT name FROM employees"),
    ("Show me all employees", "SELECT name FROM employees"),
    ("Tell me the names of all employees", "SELECT name FROM employees"),
    ("Who are all the employees in the company?", "SELECT name FROM employees"),
    ("Give me a list of every employee", "SELECT name FROM employees"),

    # Get all employees with their positions
    ("List all employees and their positions", "SELECT name, position FROM employees"),
    ("Show me all employees and their jobs", "SELECT name, position FROM employees"),
    ("Tell me the names and designations of all employees", "SELECT name, position FROM employees"),
    ("List all employees with their designations", "SELECT name, position FROM employees"),
    ("Who are all the employees and what are their roles?", "SELECT name, position FROM employees"),
]

# Add comprehensive queries to the dataset
dataset.extend([{"question": q, "sql": s} for q, s in comprehensive_queries])

date_comparisons = [
    ("Employees hired before 2023", "SELECT name FROM employees WHERE join_date < '2023-01-01'"),
    ("Staff joined after March", "SELECT name FROM employees WHERE MONTH(join_date) > 3"),
    ("Hires in Q1 2023", "SELECT name FROM employees WHERE QUARTER(join_date) = 1 AND YEAR(join_date) = 2023")
]

date_comparisons += [
    ("Employees hired before June 2022", "SELECT name FROM employees WHERE join_date < '2022-06-01'"),
    ("Staff joined after September 2021", "SELECT name FROM employees WHERE MONTH(join_date) > 9 AND YEAR(join_date) >= 2021"),
    ("Hires in Q2 2022", "SELECT name FROM employees WHERE QUARTER(join_date) = 2 AND YEAR(join_date) = 2022"),
    ("Employees who joined before 15th August 2020", "SELECT name FROM employees WHERE join_date < '2020-08-15'"),
    ("Hires after 2021", "SELECT name FROM employees WHERE YEAR(join_date) > 2021"),
]

# Multi-column requests
multi_column = [
    ("Employees and their designations", "SELECT name, position FROM employees"),
    ("Names and join dates of engineers", "SELECT name, join_date FROM employees WHERE position LIKE '%engineer%'")
]

# Add to dataset
for q, sql in date_comparisons + multi_column:
    dataset.append({"question": q, "sql": sql})

# In dataset_generator.py
join_queries = [
    ("Employees in Engineering department", 
     "SELECT employees.name FROM employees JOIN departments ON employees.department_id = departments.id WHERE departments.name = 'Engineering'"),
    
    ("Designations in New York office", 
     "SELECT position, departments.name FROM employees JOIN departments ON employees.department_id = departments.id WHERE departments.location = 'New York'")
]


join_queries += [
    ("List of employees working in Marketing department",
     "SELECT employees.name FROM employees JOIN departments ON employees.department_id = departments.id WHERE departments.name = 'Marketing'"),

    ("Names and positions of employees in San Francisco",
     "SELECT employees.name, employees.position FROM employees JOIN departments ON employees.department_id = departments.id WHERE departments.location = 'San Francisco'"),

    ("All employees with their department names",
     "SELECT employees.name, departments.name FROM employees JOIN departments ON employees.department_id = departments.id"),

    ("Engineers working in New York office",
     "SELECT employees.name FROM employees JOIN departments ON employees.department_id = departments.id WHERE employees.position LIKE '%Engineer%' AND departments.location = 'New York'"),

    ("Departments and total employees in each",
     "SELECT departments.name, COUNT(employees.id) FROM employees JOIN departments ON employees.department_id = departments.id GROUP BY departments.name")
]

dataset.extend([{"question": q, "sql": s} for q, s in join_queries])

# 8. Save dataset
with open("enhanced_dataset.json", "w") as f:
    json.dump(dataset, f, indent=2)

# Calculate statistics
employee_count = len(employee_data)
position_types = len(set(position for _, position, _ in employee_data))
first_join = min(join_date for _, _, join_date in employee_data)
last_join = max(join_date for _, _, join_date in employee_data)

print(f"✅ Created dataset with {len(dataset)} examples")
print(f"• Employees: {employee_count}")
print(f"• Unique positions: {position_types}")
print(f"• Date range: {first_join} to {last_join}")
print(f"• Example count per employee: {round(len(dataset)/employee_count, 1)}")
print(f"• CEO examples: {sum(1 for item in dataset if 'CEO' in item['sql'])}")
print(f"• Date examples: {sum(1 for item in dataset if 'join_date' in item['sql'])}")
print(f"• Partial name examples: {sum(1 for item in dataset if 'LIKE' in item['sql'] and '%' in item['sql'])}")

# Close connection
cursor.close()
conn.close()