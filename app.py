from flask import Flask, render_template, request, send_file
import sqlite3
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', selected_date='', no_data=False)

@app.route('/attendance', methods=['POST'])
def attendance():
    selected_date = request.form.get('selected_date')
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    formatted_date = selected_date_obj.strftime('%Y-%m-%d')

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT d.name, d.roll_no, 
           CASE 
               WHEN a.time IS NOT NULL THEN a.time 
               ELSE '-' 
           END AS time,
           CASE 
               WHEN a.time IS NOT NULL THEN 'Present' 
               ELSE 'Absent' 
           END AS status
    FROM data d 
    LEFT JOIN attendance a ON d.name = a.name AND a.date = ?
    ''', (formatted_date,))
    
    attendance_data = cursor.fetchall()
    conn.close()

    if not attendance_data:
        return render_template('index.html', selected_date=selected_date, no_data=True, attendance_data=attendance_data)

    return render_template('index.html', selected_date=selected_date, attendance_data=attendance_data)

@app.route('/download', methods=['GET'])
def download():
    selected_date = request.args.get('date')
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT d.name, d.roll_no, 
           CASE 
               WHEN a.time IS NOT NULL THEN a.time 
               ELSE '-' 
           END AS time,
           CASE 
               WHEN a.time IS NOT NULL THEN 'Present' 
               ELSE 'Absent' 
           END AS status
    FROM data d 
    LEFT JOIN attendance a ON d.name = a.name AND a.date = ?
    ''', (selected_date,))
    
    attendance_data = cursor.fetchall()
    conn.close()

    # Create a DataFrame from the fetched data
    df = pd.DataFrame(attendance_data, columns=['Name', 'Roll No', 'Time', 'Status'])
    
    # Save the DataFrame to an Excel file
    output_file = f'attendance_{selected_date}.xlsx'
    df.to_excel(output_file, index=False)

    # Send the file to the user
    return send_file(output_file, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
