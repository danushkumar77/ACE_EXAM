import json
import uuid
from datetime import datetime
import os
from flask import Flask, request, jsonify, abort, render_template, session, redirect, flash

# --- NEW: Imports for Real ML Evaluation ---
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

from werkzeug.utils import secure_filename

# Initialize Flask Application
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- In-Memory Data Store (Simulating a Database) ---
# (Keep the DATA_STORE definition exactly as it was before)
DATA_STORE = {
    'users': {
        'T101': {'name': 'Ms. Evelyn Reed', 'role': 'teacher', 'password': 'teacher@123'},
        'danushkumar@gmail.com': {'name': 'Danush Kumar', 'role': 'teacher', 'password': 'admin@123'}, # Mock user for login
        'S001': {'name': 'Alex Johnson', 'role': 'student', 'password': 'student@123'},
        'S002': {'name': 'Mia Chen', 'role': 'student', 'password': 'student@456'},
    },
    'assignments': [
        {
            'id': 'a-001',
            'teacher_id': 'danushkumar@gmail.com',
            'title': 'The Industrial Revolution Report',
            'description': 'Analyze the social and economic impact of early industrialization.',
            'deadline': '2025-11-20',
            'created_at': '2025-11-01',
        },
        {
            'id': 'a-002',
            'teacher_id': 'danushkumar@gmail.com',
            'title': 'World War II Essay',
            'description': 'Write an essay on the primary causes of World War II.',
            'deadline': '2025-12-01',
            'created_at': '2025-11-05',
        },
    ],
    'submissions': [
        {
            'id': 'sub-001',
            'assignment_id': 'a-001',
            'student_id': 'S002', # Example: Student 2 has submitted
            'file_path': 'uploads/some_submitted_file.jpg',
            'submitted_at': '2025-11-04',
        }
    ],
    'marks': [
        {
            'id': 'm-001',
            'assignment_id': 'a-001',
            'student_id': 'S001',
            'score': 88,
            'max_score': 100,
            'feedback': 'Good structure, but could use more primary source evidence.',
            'evaluated_at': '2025-11-05',
        }
    ]
}
# --- Utility Functions ---
# (Keep get_user, is_teacher, is_student, ml_evaluate_paper functions)
def get_user(user_id):
    """Retrieves user data or None."""
    return DATA_STORE['users'].get(user_id)

def is_teacher(user_id):
    """Checks if the user has teacher role."""
    user = get_user(user_id)
    return user and user['role'] == 'teacher'

def is_student(user_id):
    """Checks if the user has student role."""
    user = get_user(user_id)
    return user and user['role'] == 'student'

def ml_evaluate_paper(file_path: str, assignment_id: str, max_score: int) -> tuple:
    """
    Evaluates a submitted document (PDF or Image) using text extraction and keyword analysis.
    This is a more realistic simulation of an ML grading model.
    """
    # --- IMPORTANT: CONFIGURE TESSERACT PATH ---
    # Update this path to where you installed Tesseract OCR
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # --- 1. Text Extraction ---
    extracted_text = ""
    try:
        if file_path.lower().endswith('.pdf'):
            with fitz.open(file_path) as doc:
                for page in doc:
                    extracted_text += page.get_text()
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            extracted_text = pytesseract.image_to_string(Image.open(file_path))
        else:
            return 0, "Unsupported file type for ML evaluation."
    except Exception as e:
        print(f"Error during text extraction: {e}")
        return 0, "Failed to read text from file."

    if not extracted_text.strip():
        return 5, "Could not extract any text from the document. The file might be empty or an image without text."

    # --- 2. Text Analysis (Keyword-based) ---
    text_lower = extracted_text.lower()
    word_count = len(text_lower.split())

    # Define keywords for each assignment
    assignment_keywords = {
        'a-001': ['industrial', 'revolution', 'economy', 'social', 'factory', 'steam', 'engine', 'labor', 'urbanization'],
        'a-002': ['world war', 'wwii', 'axis', 'allies', 'hitler', 'churchill', 'roosevelt', 'pearl harbor', 'd-day']
    }

    keywords_to_check = assignment_keywords.get(assignment_id, [])
    
    # --- 3. Scoring Logic ---
    score = 0
    feedback_points = []

    # a) Score based on word count (basic check for effort)
    if word_count < 50:
        score += 10
        feedback_points.append("Submission is very brief.")
    elif word_count < 200:
        score += 30
        feedback_points.append("Submission length is adequate.")
    else:
        score += 50
        feedback_points.append("Submission is comprehensive in length.")

    # b) Score based on keyword matching
    found_keywords = [kw for kw in keywords_to_check if kw in text_lower]
    keyword_score = (len(found_keywords) / len(keywords_to_check)) * 50 if keywords_to_check else 0
    score += keyword_score

    if keyword_score < 25:
        feedback_points.append("Lacks focus on key topics.")
    else:
        feedback_points.append("Good use of relevant terminology.")

    # Final score scaling and feedback generation
    final_score = int((score / 100) * max_score)
    final_feedback = " ".join(feedback_points)

    print(f"ML Evaluation: Score={final_score}/{max_score}, Feedback='{final_feedback}'")
    return final_score, final_feedback

# --- Flask Configuration ---
app.secret_key = 'your_secret_key_here'  # Change this in a real application!
app.config['SESSION_TYPE'] = 'filesystem'

# --- NEW: Route to Serve the Webpage ---

@app.route('/')
def serve_frontend():
    """Serves the main HTML page."""
    # This automatically looks for index.html in the 'templates' folder
    return render_template('index.html')
@app.route('/dashboard')
def teacher_dashboard():
    """Serves the teacher dashboard page."""
    # Check if user is logged in and has the correct role
    if 'user_id' not in session or not is_teacher(session['user_id']):
        return redirect('/')  # Redirect to login if not logged in or not a teacher

    # Fetch teacher-specific data (e.g., assignments) if needed
    teacher_id = session['user_id']
    teacher_assignments = [a for a in DATA_STORE['assignments'] if a['teacher_id'] == teacher_id]

    # Create a detailed structure for assignments, including student submission and grading status
    assignments_with_details = []
    for assignment in teacher_assignments:
        detailed_assignment = assignment.copy()
        detailed_assignment['students'] = []

        for student_id, student in DATA_STORE['users'].items():
            if student['role'] == 'student':
                student_status = {
                    'id': student_id,
                    'name': student['name'],
                    'status': 'Not Submitted',
                    'mark': None
                }

                # Check if the student has a mark for this assignment
                for mark in DATA_STORE['marks']:
                    if mark['assignment_id'] == assignment['id'] and mark['student_id'] == student_id:
                        student_status['status'] = 'Graded'
                        student_status['mark'] = f"{mark['score']} / {mark['max_score']}"
                        break # Found the mark, no need to check further
                
                # If not graded, check if it has been submitted, and update the status
                if not student_status['mark']:
                    is_submitted = any(s['assignment_id'] == assignment['id'] and s['student_id'] == student_id for s in DATA_STORE['submissions'])
                    if is_submitted:
                        student_status['status'] = 'Submitted, Awaiting Grade'

                detailed_assignment['students'].append(student_status)
        assignments_with_details.append(detailed_assignment)

    return render_template(
        'teacher_dashboard.html', assignments=assignments_with_details)

@app.route('/student_dashboard')
def student_dashboard():
    """Serves the student dashboard page."""
    # Check if user is logged in and has the correct role
    if 'user_id' not in session or not is_student(session['user_id']):
        return redirect('/') # Redirect to login if not a student

    student_id = session['user_id']
    
    # Get assignments and marks for the logged-in student
    # We call the existing functions and get their JSON response
    student_assignments = get_student_assignments(student_id).get_json()
    student_marks = get_student_marks(student_id).get_json()
    user_info = get_user(student_id)

    return render_template(
        'student_dashboard.html', 
        assignments=student_assignments, 
        marks=student_marks,
        user=user_info)
# --- NEW: Authentication Endpoint ---
@app.route('/student/submit_assignment', methods=['POST'])
def submit_assignment():
    """Handles student assignment file uploads."""
    if 'user_id' not in session or not is_student(session['user_id']):
        abort(403, "Access Denied.")

    student_id = session['user_id']
    assignment_id = request.form.get('assignment_id')

    if 'assignment_file' not in request.files:
        flash('No file part in the request.', 'error')
        return redirect(request.url)
    
    file = request.files['assignment_file']

    if file.filename == '':
        flash('No selected file.', 'error')
        return redirect(request.url)

    if file and assignment_id:
        filename = secure_filename(f"{student_id}_{assignment_id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_submission = {
            'id': f"sub-{str(uuid.uuid4())[:8]}",
            'assignment_id': assignment_id,
            'student_id': student_id,
            'file_path': filepath,
            'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        DATA_STORE['submissions'].append(new_submission)
        return redirect('/student_dashboard')

@app.route('/auth', methods=['POST'])
def authenticate_user():
    """Authenticates a user based on username and password."""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        abort(400, description="Username and password are required.")

    user = DATA_STORE['users'].get(username)

    # In a real application, passwords should be hashed and securely compared.
    if user and user.get('password') == password:
        session['user_id'] = username  # Store user ID in session
        session['user_role'] = user['role']  # Store user role in session
        return jsonify({"message": "Login successful!", "user_role": user['role']}), 200
    else:
        session.pop('user_id', None) #Clear session
        return jsonify({"message": "Invalid username or password."}), 401

# --- API Endpoints (Keep the rest of the API routes: /teacher/..., /student/...)
@app.route('/teacher/<teacher_id>/assignments', methods=['POST'])
def create_assignment(teacher_id):
    # ... (Keep existing implementation)
    if not is_teacher(teacher_id):
        abort(403, description="Access Denied: Only teachers can create assignments.")

    data = request.json
    if not all(k in data for k in ['title', 'description', 'deadline']):
        abort(400, description="Missing required fields: title, description, deadline.")

    new_assignment = {
        'id': f"a-{str(uuid.uuid4())[:8]}",
        'teacher_id': teacher_id,
        'title': data['title'],
        'description': data['description'],
        'deadline': data['deadline'],
        'created_at': datetime.now().strftime('%Y-%m-%d'),
    }
    DATA_STORE['assignments'].append(new_assignment)
    return jsonify(new_assignment), 201

@app.route('/teacher/<teacher_id>/evaluate', methods=['POST'])
def process_evaluation(teacher_id):
    # ... (Keep existing implementation)
    if not is_teacher(teacher_id):
        abort(403, description="Access Denied: Only teachers can trigger evaluation.")

    data = request.json
    required_fields = ['assignment_id', 'student_id', 'image_data_path', 'max_score']
    if not all(k in data for k in required_fields):
        abort(400, description=f"Missing required fields: {', '.join(required_fields)}.")

    assignment_id = data['assignment_id']
    student_id = data['student_id']
    # The path is now derived from the submission record, not passed in JSON
    submission = next((s for s in DATA_STORE['submissions'] if s['assignment_id'] == assignment_id and s['student_id'] == student_id), None)
    if not submission:
        abort(404, "No submission found for this student and assignment.")
    file_path = submission['file_path']
    max_score = data['max_score']
    new_mark = {
        'id': f"m-{str(uuid.uuid4())[:8]}",
        'assignment_id': assignment_id,
        'student_id': student_id,
        'score': score,
        'max_score': max_score,
        'feedback': feedback,
        'evaluated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'teacher_id': teacher_id,
    }
    DATA_STORE['marks'].append(new_mark)

    return jsonify({
        "message": f"Evaluation complete. Marks stored and shared instantly with {student_id}.",
        "marks_data": new_mark
    }), 200

@app.route('/student/<student_id>/assignments', methods=['GET'])
def get_student_assignments(student_id):
    # ... (Keep existing implementation)
    if not is_student(student_id):
        abort(403, description="Access Denied: Only students can view assignments.")
    
    assignments_with_status = []
    
    for assignment in DATA_STORE['assignments']:
        is_graded = any(
            mark['assignment_id'] == assignment['id'] and mark['student_id'] == student_id
            for mark in DATA_STORE['marks']
        )
        
        is_submitted = any(
            sub['assignment_id'] == assignment['id'] and sub['student_id'] == student_id
            for sub in DATA_STORE['submissions']
        )

        assignment_info = assignment.copy()
        if is_graded:
            assignment_info['status'] = 'Graded'
        elif is_submitted:
            assignment_info['status'] = 'Submitted, Awaiting Grade'
        else:
            assignment_info['status'] = 'Pending Submission'
        
        # Simple check for deadline reminder notification simulation
        deadline_date = datetime.strptime(assignment['deadline'], '%Y-%m-%d')
        days_left = (deadline_date - datetime.now()).days
        
        if days_left <= 7 and days_left > 0 and not is_graded:
            assignment_info['reminder'] = f"Deadline is in {days_left} days! Submit soon."
        elif days_left <= 0 and not is_graded:
            assignment_info['reminder'] = "Deadline Passed."
        
        assignments_with_status.append(assignment_info)

    return jsonify(assignments_with_status)

@app.route('/student/<student_id>/marks', methods=['GET'])
def get_student_marks(student_id):
    # ... (Keep existing implementation)
    if not is_student(student_id):
        abort(403, description="Access Denied: Only students can view marks.")

    student_marks = [
        mark for mark in DATA_STORE['marks'] if mark['student_id'] == student_id
    ]

    assignment_map = {a['id']: a['title'] for a in DATA_STORE['assignments']}
    
    results = []
    for mark in student_marks:
        mark_data = mark.copy()
        mark_data['assignment_title'] = assignment_map.get(mark['assignment_id'], 'Unknown Assignment')
        results.append(mark_data)

    return jsonify(results)

if __name__ == '__main__':
    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    print("---------------------------------------------------------------------")
    print("🚀 AceExam (Smart Educational Management System) API Started (Flask) 🚀")
    print("🌐 Visit http://127.0.0.1:5000/ in your browser!")
    print("---------------------------------------------------------------------")
    app.run(debug=True, port=5000)