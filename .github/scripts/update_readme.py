import os
import json
import subprocess
import google.generativeai as genai

# Initialize Gemini API
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found. Exiting.")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Detect changed notebook files in the commit
cmd = "git diff --name-only HEAD~1 HEAD"
try:
    changed_files = subprocess.check_output(cmd, shell=True).decode().split()
except Exception:
    changed_files = []

notebook_diffs = []
for file in changed_files:
    if file.endswith(".ipynb") and os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                nb = json.load(f)
                # Pull non-empty code cells
                code_cells = [
                    "".join(cell.get("source", []))
                    for cell in nb.get("cells", [])
                    if cell.get("cell_type") == "code" and "".join(cell.get("source", [])).strip()
                ]
                if code_cells:
                    # Capture the last few executed logic blocks
                    notebook_diffs.append(f"### File: {file}\n" + "\n---\n".join(code_cells[-6:]))
        except Exception as e:
            print(f"Error reading {file}: {e}")

if not notebook_diffs:
    print("No relevant code modifications found in notebooks. Skipping README update.")
    exit(0)

notebook_code = "\n\n".join(notebook_diffs)
readme_path = "README.md"

with open(readme_path, "r", encoding="utf-8") as f:
    current_readme = f.read()

prompt = f"""
You are an automated evaluator tracking a student's hands-on machine learning and agentic AI progress.

Recent Notebook Code Executed:
{notebook_code}

Current README:
{current_readme}

Instructions:
1. Analyze what core algorithms, data processing techniques, or model evaluations were performed in the lab notebook.
2. Determine skill mastery percentages (0-100%) across core areas based on the cumulative work shown:
   - Data Wrangling & Exploration
   - Classical Machine Learning & Regression/Classification
   - Deep Learning & Neural Architectures
   - Agentic Workflows & Tool Calling
3. Add or update the recent technical learnings log.
4. Output ONLY markdown bounded strictly between `<!-- START_SKILLS -->` and `<!-- END_SKILLS -->`.

Output Format:
<!-- START_SKILLS -->
### 📊 Skill Mastery Tracker
- **Data Wrangling & Exploration**: [████████░░] 80%
- **Classical ML & Modeling**: [██████░░░░] 60%
- **Deep Learning**: [███░░░░░░░] 30%
- **Agentic AI & Tool Integration**: [██░░░░░░░░] 20%

### 🧠 Latest Concepts Applied
- **<Topic/Lab Name>**: <Concise 1-sentence technical takeaway about what logic was implemented>
<!-- END_SKILLS -->
"""

response = model.generate_content(prompt)
output_text = response.text.strip()

if "<!-- START_SKILLS -->" in output_text and "<!-- END_SKILLS -->" in output_text:
    new_block = output_text[output_text.find("<!-- START_SKILLS -->"):output_text.find("<!-- END_SKILLS -->") + len("<!-- END_SKILLS -->")]

    if "<!-- START_SKILLS -->" in current_readme and "<!-- END_SKILLS -->" in current_readme:
        prefix = current_readme.split("<!-- START_SKILLS -->")[0]
        suffix = current_readme.split("<!-- END_SKILLS -->")[1]
        final_readme = f"{prefix}{new_block}{suffix}"
    else:
        final_readme = f"{current_readme.strip()}\n\n{new_block}\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(final_readme)
    print("README.md updated.")
else:
    print("LLM did not return expected markers. No changes written.")