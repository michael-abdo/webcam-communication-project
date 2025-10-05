from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json
from datetime import datetime
from pathlib import Path

# Import baseline capture API
from baseline_capture.api import baseline_router

app = FastAPI(title="Bias-Resilient Assessment Platform")

# Include baseline capture API routes
app.include_router(baseline_router)

# Mount static files
app.mount("/static", StaticFiles(directory="assessments/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="assessments/templates")

# Create results directory if it doesn't exist
Path("assessments/results").mkdir(parents=True, exist_ok=True)
Path("assessments/results/core").mkdir(parents=True, exist_ok=True)
Path("assessments/results/advanced").mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with assessment options"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bias-Resilient Assessment Platform</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            .assessment-list {
                list-style: none;
                padding: 0;
            }
            .assessment-item {
                margin: 20px 0;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 8px;
                border-left: 4px solid #2196f3;
            }
            .assessment-item h3 {
                margin-top: 0;
                color: #2196f3;
            }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                background: #2196f3;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #1976d2;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Bias-Resilient Assessment Platform</h1>
            <p>Welcome to the interactive assessment platform. Choose an assessment to begin:</p>
            
            <ul class="assessment-list">
                <li class="assessment-item">
                    <h3>Cognitive Reflection Test (CRT)</h3>
                    <p>Measure your intuitive vs deliberative thinking style with classic reasoning problems.</p>
                    <a href="/assessment/crt" class="btn">Start CRT Assessment</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Actively Open-Minded Thinking (AOT)</h3>
                    <p>Assess your intellectual humility and resistance to cognitive biases.</p>
                    <a href="/assessment/aot" class="btn">Start AOT Assessment</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Reaction Time & Fatigue Test</h3>
                    <p>Test your reaction speed and detect any cognitive fatigue.</p>
                    <a href="/assessment/reaction" class="btn">Start Reaction Test</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Full Core Assessment (4 minutes)</h3>
                    <p>Complete cognitive assessment including CRT, AOT, numeracy, and intent attribution.</p>
                    <a href="/assessment/core" class="btn">Start Core Assessment</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Full Advanced Assessment (6 minutes)</h3>
                    <p>Personality and behavioral assessment including emotion regulation and decision biases.</p>
                    <a href="/assessment/advanced" class="btn">Start Advanced Assessment</a>
                </li>
                
                <li class="assessment-item">
                    <h3>Baseline Capture Setup</h3>
                    <p>Calibrate the system to your unique patterns for personalized assessments (25 seconds).</p>
                    <a href="/assessment/baseline" class="btn">Start Baseline Setup</a>
                </li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/assessment/crt", response_class=HTMLResponse)
async def crt_assessment():
    """Serve the CRT assessment page"""
    with open("assessments/static/crt_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/aot", response_class=HTMLResponse)
async def aot_assessment():
    """Serve the AOT assessment page"""
    with open("assessments/static/aot_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/reaction", response_class=HTMLResponse)
async def reaction_assessment():
    """Serve the reaction time assessment page"""
    with open("assessments/static/reaction_time_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/core", response_class=HTMLResponse)
async def core_assessment():
    """Serve the full Core assessment page"""
    with open("assessments/static/core_assessment.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/numeracy", response_class=HTMLResponse)
async def numeracy_assessment():
    """Serve the numeracy assessment page"""
    with open("assessments/static/numeracy_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/intent", response_class=HTMLResponse)
async def intent_assessment():
    """Serve the intent attribution assessment page"""
    with open("assessments/static/intent_attribution_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/nfc", response_class=HTMLResponse)
async def nfc_assessment():
    """Serve the need for closure assessment page"""
    with open("assessments/static/need_for_closure_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/anchoring", response_class=HTMLResponse)
async def anchoring_assessment():
    """Serve the anchoring test page"""
    with open("assessments/static/anchoring_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/advanced", response_class=HTMLResponse)
async def advanced_assessment():
    """Serve the full Advanced assessment page"""
    with open("assessments/static/advanced_assessment.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/emotion-regulation", response_class=HTMLResponse)
async def emotion_regulation_assessment():
    """Serve the emotion regulation assessment page"""
    with open("assessments/static/emotion_regulation_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/relationship-style", response_class=HTMLResponse)
async def relationship_style_assessment():
    """Serve the relationship style assessment page"""
    with open("assessments/static/relationship_style_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/listening-preferences", response_class=HTMLResponse)
async def listening_preferences_assessment():
    """Serve the listening preferences assessment page"""
    with open("assessments/static/listening_preferences_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/loss-aversion", response_class=HTMLResponse)
async def loss_aversion_assessment():
    """Serve the loss aversion assessment page"""
    with open("assessments/static/loss_aversion_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/perspective-taking", response_class=HTMLResponse)
async def perspective_taking_assessment():
    """Serve the perspective taking assessment page"""
    with open("assessments/static/perspective_taking_simple.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/assessment/baseline", response_class=HTMLResponse)
async def baseline_capture_assessment():
    """Serve the baseline capture setup page"""
    with open("assessments/static/baseline_capture.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/results/core/{user_id}", response_class=HTMLResponse)
async def core_results(user_id: str):
    """Serve the Core assessment results page"""
    try:
        with open("assessments/static/results_core.html", "r") as f:
            content = f.read()
            # Replace placeholder with actual user_id for JavaScript
            content = content.replace("{{USER_ID}}", user_id)
            return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Results page not found</h1>", status_code=404)

@app.get("/results/advanced/{user_id}", response_class=HTMLResponse)
async def advanced_results(user_id: str):
    """Serve the Advanced assessment results page"""
    try:
        with open("assessments/static/results_advanced.html", "r") as f:
            content = f.read()
            # Replace placeholder with actual user_id for JavaScript
            content = content.replace("{{USER_ID}}", user_id)
            return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Results page not found</h1>", status_code=404)

@app.get("/api/results/core/{user_id}")
async def get_core_results(user_id: str):
    """Get Core assessment results data"""
    try:
        with open(f"assessments/results/core/{user_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "User results not found", "user_id": user_id}
    except json.JSONDecodeError:
        return {"error": "Invalid results data", "user_id": user_id}

@app.get("/api/results/advanced/{user_id}")
async def get_advanced_results(user_id: str):
    """Get Advanced assessment results data"""
    try:
        with open(f"assessments/results/advanced/{user_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "User results not found", "user_id": user_id}
    except json.JSONDecodeError:
        return {"error": "Invalid results data", "user_id": user_id}

@app.get("/api/quiz/questions/{section}")
async def get_questions(section: str):
    """Get questions for a specific section"""
    question_files = {
        "crt": "assessments/core_4min/sections/cognitive_reflection/questions_simple.json",
        "aot": "assessments/core_4min/sections/actively_open_minded/questions_simple.json",
        "listening": "assessments/advanced_6min/sections/listening_preferences/questions.json",
        "relationship": "assessments/advanced_6min/sections/relationship_style/questions.json"
    }
    
    if section in question_files:
        with open(question_files[section], "r") as f:
            return json.load(f)
    
    return {"error": "Section not found"}

@app.post("/api/quiz/submit")
async def submit_quiz(request: Request):
    """Submit quiz responses"""
    data = await request.json()
    
    # Add timestamp
    data["timestamp"] = datetime.now().isoformat()
    
    # Determine assessment type and user ID
    assessment_type = data.get("assessmentType", "unknown")
    user_id = data.get("userId", "anonymous")
    
    # Save to user-specific results file
    try:
        if assessment_type in ["core", "advanced"]:
            # Ensure directory exists
            results_dir = Path(f"assessments/results/{assessment_type}")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            user_filename = f"assessments/results/{assessment_type}/{user_id}.json"
            with open(user_filename, "w") as f:
                json.dump(data, f, indent=2)
        else:
            # Fallback to old timestamp-based naming for unknown types
            results_dir = Path("assessments/results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"assessments/results/response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
                
        save_success = True
        error_message = None
    except Exception as e:
        save_success = False
        error_message = str(e)
    
    # Calculate basic scores (example for CRT)
    if "quiz_type" in data and data["quiz_type"] == "crt":
        correct_answers = {
            "bat_ball": 0.05,
            "widget": 5,
            "lily_pad": 47
        }
        score = 0
        for key, correct in correct_answers.items():
            if key in data["responses"]:
                try:
                    if float(data["responses"][key]["answer"]) == correct:
                        score += 1
                except:
                    pass
        
        return {
            "success": save_success,
            "status": "success" if save_success else "error",
            "user_id": user_id,
            "timestamp": data["timestamp"],
            "score": score,
            "total": 3,
            "message": f"You got {score} out of 3 correct!" if save_success else f"Quiz completed but save failed: {error_message}",
            "error": error_message if not save_success else None
        }
    
    # Standard response for assessment submissions
    if save_success:
        return {
            "success": True,
            "status": "success",
            "user_id": user_id,
            "timestamp": data["timestamp"],
            "message": "Assessment saved successfully"
        }
    else:
        return {
            "success": False,
            "status": "error",
            "user_id": user_id,
            "timestamp": data["timestamp"],
            "message": f"Assessment completed but save failed: {error_message}",
            "error": error_message
        }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Serve favicon if requested
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("assessments/static/favicon.ico") if os.path.exists("assessments/static/favicon.ico") else {"status": "no favicon"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)