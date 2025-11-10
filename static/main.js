// Base URL for the API (since we run on the same server)
const BASE_URL = ''; 

function displayOutput(data, title) {
    const outputElement = document.getElementById('output');
    outputElement.textContent = `--- ${title} ---\n\n` + JSON.stringify(data, null, 2);
    console.log(title, data);
}

// --- Teacher Module Logic ---

async function triggerMlEvaluation() {
    const teacherId = 'T101'; // Fixed for simulation
    const assignmentId = 'a-001'; // Fixed for simulation
    const studentId = document.getElementById('studentIdGrade').value;
    const imagePath = document.getElementById('imagePath').value;
    const maxScore = parseInt(document.getElementById('maxScore').value);

    const data = {
        assignment_id: assignmentId,
        student_id: studentId,
        image_data_path: imagePath,
        max_score: maxScore
    };

    try {
        const response = await fetch(`${BASE_URL}/teacher/${teacherId}/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (response.ok) {
            displayOutput(result, `✅ ML Grading Successful for ${studentId}`);
        } else {
            displayOutput(result, `❌ Grading Error: ${response.status}`);
        }
    } catch (error) {
        displayOutput({ error: "Network error or server unreachable." }, "❌ Request Failed");
    }
}

// --- Student Module Logic ---

async function viewStudentAssignments() {
    const studentId = document.getElementById('studentIdView').value;

    try {
        const response = await fetch(`${BASE_URL}/student/${studentId}/assignments`);
        const result = await response.json();

        if (response.ok) {
            displayOutput(result, `📚 Assignments for ${studentId}`);
        } else {
            displayOutput(result, `❌ Error retrieving assignments: ${response.status}`);
        }
    } catch (error) {
        displayOutput({ error: "Network error or server unreachable." }, "❌ Request Failed");
    }
}

async function viewStudentMarks() {
    const studentId = document.getElementById('studentIdView').value;

    try {
        const response = await fetch(`${BASE_URL}/student/${studentId}/marks`);
        const result = await response.json();

        if (response.ok) {
            displayOutput(result, `💯 Marks and Feedback for ${studentId}`);
        } else {
            displayOutput(result, `❌ Error retrieving marks: ${response.status}`);
        }
    } catch (error) {
        displayOutput({ error: "Network error or server unreachable." }, "❌ Request Failed");
    }
}