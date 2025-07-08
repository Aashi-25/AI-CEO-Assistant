import mysql.connector
import random
from datetime import datetime, timedelta

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Aashi@1234',
    'database': 'mydatabase'
}

# Connect to database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Employee data to add (6 new employees)
new_employees = [
    {"name": "Rahul Verma", "position": "Senior Software Engineer", "join_date": "2023-02-14"},
    {"name": "Ananya Desai", "position": "Marketing Manager", "join_date": "2023-05-01"},
    {"name": "Vikram Singh", "position": "Data Scientist", "join_date": "2023-07-15"},
    {"name": "Meera Patel", "position": "Product Manager", "join_date": "2023-09-10"},
    {"name": "Arjun Kumar", "position": "DevOps Engineer", "join_date": "2024-01-05"},
    {"name": "Priyanka Sharma", "position": "UX Designer", "join_date": "2024-02-20"}
]

# Insert new employees
for emp in new_employees:
    sql = "INSERT INTO employees (name, position, join_date) VALUES (%s, %s, %s)"
    values = (emp["name"], emp["position"], emp["join_date"])
    cursor.execute(sql, values)

# Commit changes
conn.commit()

# Verify insertion
cursor.execute("SELECT * FROM employees")
employees = cursor.fetchall()

print("✅ Added 6 new employees. Total employees now:", len(employees))
print("\nCurrent Employees:")
print("ID | Name             | Position                  | Join Date")
print("-" * 50)
for emp in employees:
    print(f"{emp[0]:2} | {emp[1]:<15} | {emp[2]:<24} | {emp[3]}")

# Close connection
cursor.close()
conn.close()