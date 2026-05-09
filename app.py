import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
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

# Constants - Safe path handling for Vercel deployment
BASE_DIR = Path.cwd()
TEMPLATE_PATH = BASE_DIR / "templates" / "resume_template.docx"
JSON_PATH = BASE_DIR / "data" / "base_content.json"  # READ-ONLY input
RENDER_SCRIPT = BASE_DIR / "test_render.py"

# Use /tmp for output and temp files on Vercel, local for development
OUTPUT_DIR = Path("/tmp/generated_resumes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_JSON_PATH = Path("/tmp/resume_data.json")  # Writable temp JSON for rendering

print(f"[DEBUG] CWD: {Path.cwd()}")
print(f"[DEBUG] Template path: {TEMPLATE_PATH}")
print(f"[DEBUG] JSON path: {JSON_PATH}")
print(f"[DEBUG] Output dir: {OUTPUT_DIR}")
print(f"[DEBUG] Temp JSON path: {TMP_JSON_PATH}")

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

This is Sahi K, a Senior Java Developer with over a decade of experience in Java, Spring Boot, Microservices, AWS, React, Angular, and DevOps. I have worked across telecom, banking, healthcare, and retail domains, delivering scalable and cloud-based solutions.

I am currently available for C2C opportunities and open to relocation. Please find my resume attached for your review.  

Visa: H1B
Total Experience: 10+
LinkedIn: www.linkedin.com/in/sahi-javadeveloper



Best regards,
Sahi Kolukuluri
📧 kolukulurisahi7@gmail.com
📞 +1(919)-893-9289

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
        "cc": "zoya@stemsolllc.com",
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
        # 1. Validate input files exist
        print(f"[DEBUG] Checking template: {TEMPLATE_PATH}")
        print(f"[DEBUG] Template exists: {TEMPLATE_PATH.exists()}")
        
        if not TEMPLATE_PATH.exists():
            return {"error": f"Template not found: {TEMPLATE_PATH}"}
        
        print(f"[DEBUG] Checking JSON: {JSON_PATH}")
        print(f"[DEBUG] JSON exists: {JSON_PATH.exists()}")
        
        if not JSON_PATH.exists():
            return {"error": f"JSON not found: {JSON_PATH}"}
        
        # 2. Read base JSON and merge with request content (avoid writing to read-only data/)
        print(f"[DEBUG] Reading base JSON from: {JSON_PATH}")
        with open(JSON_PATH, "r") as f:
            base_content = json.load(f)
        
        # Merge request content with base content
        merged_content = {**base_content, **request.json_content}
        
        # Write merged content to /tmp (writable on Vercel)
        print(f"[DEBUG] Writing merged JSON to /tmp: {TMP_JSON_PATH}")
        with open(TMP_JSON_PATH, "w") as f:
            json.dump(merged_content, f, indent=4)
        
        # 3. Run test_render.py with environment variable pointing to /tmp JSON
        print(f"[DEBUG] Running render script: {RENDER_SCRIPT}")
        env = os.environ.copy()
        env["RESUME_DATA_PATH"] = str(TMP_JSON_PATH)  # Tell script where to read JSON
        
        result = subprocess.run(
            ["python3", str(RENDER_SCRIPT)], 
            capture_output=True, 
            text=True, 
            check=True,
            cwd=str(BASE_DIR),
            env=env
        )
        
        print(f"[DEBUG] Script stdout: {result.stdout}")
        if result.stderr:
            print(f"[DEBUG] Script stderr: {result.stderr}")
        
        # 4. Find the output path from stdout or logs
        # The script prints: "✓ Rendered OK: /path/to/file.docx"
        output_line = next((line for line in result.stdout.splitlines() if "✓ Rendered OK:" in line), None)
        
        if output_line:
            file_path = output_line.split("✓ Rendered OK:")[1].strip()
            print(f"[DEBUG] Generated file: {file_path}")
            
            # 5. Return the generated DOCX file as a downloadable response
            output_file = Path(file_path)
            print(f"[DEBUG] Output file path: {output_file}")
            print(f"[DEBUG] Output file exists: {output_file.exists()}")
            
            if not output_file.exists():
                return {
                    "success": False,
                    "error": f"Generated resume not found: {output_file}"
                }
            
            print(f"[DEBUG] Starting download: {output_file}")
            return FileResponse(
                path=str(output_file),
                filename="Sahi_Kolukuluri.docx",
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            print(f"[DEBUG] Could not find output line in stdout")
            raise HTTPException(status_code=500, detail="Could not determine output file path from script execution.")

    except subprocess.CalledProcessError as e:
        error_msg = f"Script execution failed.\nStdout: {e.stdout}\nStderr: {e.stderr}"
        print(f"[DEBUG] Error: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        print(f"[DEBUG] Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
