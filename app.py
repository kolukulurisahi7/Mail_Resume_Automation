import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import re
import subprocess
import json
import os
from pathlib import Path

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Data models
class JDEmailRequest(BaseModel):
    jd_text: str

class ResumeRequest(BaseModel):
    json_content: dict

# Constants
BASE_DIR = Path(__file__).parent.resolve()
JSON_PATH = BASE_DIR / "data/base_content.json"
RENDER_SCRIPT = BASE_DIR / "test_render.py"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(BASE_DIR / "static/index.html", "r") as f:
        return f.read()

@app.post("/api/draft-email")
async def draft_email(request: JDEmailRequest):
    jd_text = request.jd_text
    
    # 1. Extract Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', jd_text)
    if not email_match:
        # Fallback if no email found
        recipient = ""
    else:
        recipient = email_match.group(0)

    # 2. Extract Job Title
    # Try to find common patterns for job titles
    title_match = re.search(r"(?:Job Title|Role|Position|Title):\s*(.*)", jd_text, re.IGNORECASE)
    if title_match:
        job_title = title_match.group(1).strip()
    else:
        # If no specific label, maybe use the first non-empty line if it's short?
        # For now, per user request, default to "Java Developer" if clear title isn't found.
        job_title = "Java Developer"

    # 3. Construct Subject and Body
    subject = f"Interested in {job_title}"
    
    # Generic Template
    body_template = """Hi,

This is Sasank Talluri, a Senior Java Developer with over a decade of experience in Java, Spring Boot, Microservices, AWS, React, Angular, and DevOps. I have worked across banking, healthcare, and retail domains, delivering scalable and cloud-based solutions.

I am currently available for C2C opportunities and open to relocation. Please find my resume attached for your review.  

Visa: H1B
Total Experience: 10+
LinkedIn: https://www.linkedin.com/in/sasankt/


Best regards,
Sasank Talluri
📧 sasanktalluri5@gmail.com
📞 (984) 225-5569

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Job Description Reference:
{jd}
"""
    body = body_template.format(jd=jd_text)
    
    # 4. Open Gmail Draft (Simple URL Method)
    import urllib.parse
    import webbrowser
    
    base_url = "https://mail.google.com/mail/?view=cm&fs=1"
    params = {
        "to": recipient,
        "cc": "shekar@stemsolllc.com",
        "su": subject,
        "body": body
    }
    # Encode parameters safely
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    gmail_url = f"{base_url}&{query_string}"
    
    try:
        webbrowser.open(gmail_url)
        return {"status": "success", "message": "Draft opened in Gmail", "recipient": recipient}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open browser: {str(e)}")

@app.post("/api/generate-resume")
async def generate_resume(request: ResumeRequest):
    try:
        # 1. Update JSON
        with open(JSON_PATH, "w") as f:
            json.dump(request.json_content, f, indent=4)
        
        # 2. Run test_render.py
        result = subprocess.run(
            ["python3", str(RENDER_SCRIPT)], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # 3. Find the output path from stdout or logs
        # The script prints: "✓ Rendered OK: /path/to/file.docx"
        output_line = next((line for line in result.stdout.splitlines() if "✓ Rendered OK:" in line), None)
        
        if output_line:
            file_path = output_line.split("✓ Rendered OK:")[1].strip()
            
            # 4. Reveal in Finder
            subprocess.run(["open", "-R", file_path])
            return {"status": "success", "message": "Resume generated and opened in Finder", "path": file_path}
        else:
             raise HTTPException(status_code=500, detail="Could not determine output file path from script execution.")

    except subprocess.CalledProcessError as e:
        error_msg = f"Script execution failed.\nStdout: {e.stdout}\nStderr: {e.stderr}"
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
