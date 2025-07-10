import mysql.connector
from datetime import date

# Database configuration - UPDATE THESE VALUES FOR YOUR SYSTEM!
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password_here',  # Change to your MySQL password
    'database': 'mydatabase'
}

def create_database():
    try:
        # Connect to MySQL server (without specifying database)
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        print(f"✅ Database '{db_config['database']}' created")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def setup_tables():
    try:
        # Connect to the specific database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Create departments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            location VARCHAR(255) NOT NULL
        )
        """)

        # Create employees table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            position VARCHAR(255) NOT NULL,
            join_date DATE NOT NULL,
            department_id INT,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
        """)

        # Departments data
        departments = [
            (1, 'Engineering', 'New York'),
            (2, 'Marketing', 'San Francisco'),
            (3, 'HR', 'New York'),
            (4, 'Product', 'San Francisco'),
            (5, 'Design', 'New York'),
            (6, 'Data Science', 'Chicago'),
            (7, 'Management', 'Boston'),
            (8, 'Executive', 'New York'),
            (9, 'DevOps', 'Austin'),
            (10, 'UX', 'New York')
        ]

        # Employees data
        employees = [
            (1, 'Aarav Sharma', 'CEO', date(2020, 1, 15), 8),
            (2, 'Priya Patel', 'CFO', date(2021, 3, 22), 8),
            (3, 'Rohan Mehta', 'Software Engineer', date(2022, 7, 1), 1),
            (4, 'Sonia Singh', 'HR Manager', date(2021, 9, 10), 3),
            (5, 'Rahul Verma', 'Senior Software Engineer', date(2023, 2, 14), 1),
            (6, 'Ananya Desai', 'Marketing Manager', date(2023, 5, 1), 2),
            (7, 'Vikram Singh', 'Data Scientist', date(2023, 7, 15), 6),
            (8, 'Meera Patel', 'Product Manager', date(2023, 9, 10), 4),
            (9, 'Arjun Kumar', 'DevOps Engineer', date(2024, 1, 5), 9),
            (10, 'Priyanka Sharma', 'UK Designer', date(2024, 2, 20), 10)
        ]

        # Insert departments
        cursor.executemany(
            "INSERT IGNORE INTO departments (id, name, location) VALUES (%s, %s, %s)",
            departments
        )

        # Insert employees
        cursor.executemany(
            """INSERT IGNORE INTO employees (id, name, position, join_date, department_id)
            VALUES (%s, %s, %s, %s, %s)""",
            employees
        )

        conn.commit()
        print("✅ Tables created and data inserted successfully")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_database()
    setup_tables()
    print("\nDatabase setup complete!")
    print("You can now run your application with:")
    print("python app.py")