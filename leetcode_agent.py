import streamlit as st
import os, textwrap
from git import Repo
import ollama
from PIL import Image

# ========= CONFIG =========
MODEL_CANDIDATES = ["qwen:4b", "qwen2:1.5b"]

def get_available_model():
    """Find first available model installed in Ollama."""
    try:
        models = os.popen("ollama list").read().lower()
        for m in MODEL_CANDIDATES:
            if m.split(":")[0] in models:
                return m
    except Exception:
        pass
    return MODEL_CANDIDATES[-1]

MODEL = get_available_model()

st.set_page_config(page_title="LeetCode Note Agent", page_icon="🤖", layout="centered")
st.title("🤖 LeetCode Note Generator (English Edition, 2-Stage Prompt)")

# ========= INPUT UI =========
col1, col2 = st.columns(2)
with col1:
    leetcode_id = st.text_input("📘 Problem ID", "")
with col2:
    leetcode_name = st.text_input("🧩 Problem Title", "")

code = st.text_area("💻 Paste your solution code", height=200)
uploaded_file = st.file_uploader("📸 Upload screenshot (optional)", type=["png", "jpg", "jpeg"])
note = st.text_area("🗒️ Your notes / reflections", height=150)
repo_path = st.text_input("📂 Local GitHub repository path", placeholder="D:\\Codes\\Algorithm-Lab")
commit_message = st.text_input("💬 Commit message", value="Add new LeetCode note")

# ========= GENERATE =========
if st.button("✨ Generate and Commit"):
    if not all([leetcode_id.strip(), leetcode_name.strip(), code.strip(), repo_path.strip()]):
        st.warning("⚠️ Please fill in Problem ID, Title, Code, and Repository Path.")
        st.stop()

    repo_path = repo_path.strip().rstrip(">").rstrip("\\/")
    if not os.path.exists(repo_path):
        st.error(f"❌ Invalid path: {repo_path}")
        st.stop()

    safe_name = leetcode_name.strip().replace(" ", "_").lower()
    filename = f"leetcode_{leetcode_id}_{safe_name}.md"
    notes_dir = os.path.join(repo_path, "notes")
    os.makedirs(notes_dir, exist_ok=True)
    save_path = os.path.join(notes_dir, filename)

    image_md = ""
    if uploaded_file:
        img_name = f"{leetcode_id}_{safe_name}.png"
        img_path = os.path.join(notes_dir, img_name)
        with open(img_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        image_md = f"![Result Screenshot]({img_name})\n"

    # -------- Stage 1: Outline generation --------
    plan_prompt = textwrap.dedent(f"""
    You are a senior algorithm engineer.
    Analyze the following LeetCode problem and create a concise English outline
    for a GitHub README with five sections:
    1. Problem Overview
    2. Approach and Key Ideas
    3. Code Implementation
    4. Complexity Analysis
    5. Personal Reflection

    Problem ID: {leetcode_id}
    Title: {leetcode_name}

    User notes:
    {note}
    """)

    st.write("🧠 Stage 1: Creating outline using model:", MODEL)
    try:
        plan_resp = ollama.chat(model=MODEL, messages=[{"role": "user", "content": plan_prompt}],
                                options={"temperature": 0.3})
        outline = plan_resp["message"]["content"]
    except Exception as e:
        st.error(f"Outline generation failed: {e}")
        st.stop()

    # -------- Stage 2: Full README generation --------
    gen_prompt = textwrap.dedent(f"""
    You are a professional software engineer and technical writer.
    Using the outline below, write a complete **English GitHub README** in Markdown format.

    ### Guidelines
    - Include sections: Problem Overview, Approach and Key Ideas, Code Implementation, Complexity Analysis, Personal Reflection.
    - Under *Code Implementation*, include the user's code verbatim inside a ```python fenced block.
    - Expand and enrich the *Personal Reflection* section by adding 2–3 additional meaningful sentences
      about what can be learned or generalized from this problem.
    - Keep total length under 600 words, clear and professional.

    Outline:
    {outline}

    Code:
    {code}

    User Notes:
    {note}
    """)

    st.write("🧾 Stage 2: Generating full README ...")
    try:
        response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": gen_prompt}],
                               options={"temperature": 0.25})
        readme_md = response["message"]["content"]
    except Exception as e:
        st.error(f"README generation failed: {e}")
        st.stop()

    # -------- Write to file --------
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(f"# LeetCode {leetcode_id} - {leetcode_name}\n\n")
        f.write(image_md)
        f.write(readme_md)

    st.success(f"✅ README created: {save_path}")

    # -------- Git commit & push --------

    # -------- Preview --------
    st.markdown("---")
    st.markdown("### 📝 Generated README Preview")
    st.markdown(readme_md)
