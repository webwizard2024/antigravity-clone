import streamlit as st
import google.generativeai as genai
import subprocess
import sys
import os
import tempfile

st.set_page_config(page_title="Anti-Gravity IDE ⚡", layout="wide")

# ------------------- STYLES -------------------
st.markdown("""
<style>
.stApp{background:#1e1e1e;}
[data-testid=stSidebar]{background:#252526;}
textarea{background:#1e1e1e!important;color:#d4d4d4!important;font-family:Consolas,monospace!important;}
.terminal{background:#111;color:#0f0;padding:10px;height:250px;overflow:auto;border-radius:5px;}
.ai{background:#2d2d30;padding:10px;border-left:3px solid #007acc;margin:5px;}
.user{background:#1e1e1e;padding:10px;border-left:3px solid #4ec9b0;margin:5px;}
</style>
""", unsafe_allow_html=True)

# ------------------- SESSION -------------------
if "files" not in st.session_state:
    st.session_state.files = {
        "main.py": {"content": 'print("Hello Anti-Gravity IDE 🚀")', "lang": "python"}
    }

if "active" not in st.session_state:
    st.session_state.active = "main.py"

if "terminal" not in st.session_state:
    st.session_state.terminal = ""

if "chat" not in st.session_state:
    st.session_state.chat = []

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# ------------------- SIDEBAR -------------------
with st.sidebar:
    st.markdown("### 📁 Files")
    for f in list(st.session_state.files):
        if st.button(f, use_container_width=True):
            st.session_state.active = f

    st.markdown("---")
    new_file = st.text_input("New file")
    if st.button("➕ Create"):
        if new_file:
            st.session_state.files[new_file] = {"content": "", "lang": "python"}
            st.session_state.active = new_file

# ------------------- EDITOR -------------------
col1, col2 = st.columns([2,1])
with col1:
    file = st.session_state.files[st.session_state.active]
    code = st.text_area("Editor", file["content"], height=400)
    file["content"] = code

    if st.button("▶ Run Python"):
        blocked = ["import os","import subprocess","open(","sys.exit"]
        if any(b in code.lower() for b in blocked):
            st.session_state.terminal = "❌ BLOCKED FOR SECURITY"
        else:
            with tempfile.NamedTemporaryFile(delete=False,suffix=".py") as f:
                f.write(code.encode())
                path=f.name
            try:
                out = subprocess.run([sys.executable,path],capture_output=True,text=True,timeout=10,cwd=tempfile.gettempdir())
                st.session_state.terminal = out.stdout + out.stderr
            except:
                st.session_state.terminal = "❌ Execution failed"
            os.unlink(path)

    st.markdown(f"<div class='terminal'>{st.session_state.terminal}</div>",unsafe_allow_html=True)

# ------------------- AI AGENT -------------------
with col2:
    prompt = st.text_area("Ask AI")
    if st.button("✨ Generate / Fix"):
        if not API_KEY:
            st.error("Add GEMINI_API_KEY in Streamlit Secrets")
        else:
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            p = f"Fix or improve this python code. Return ONLY code:\n{code}"
            res = model.generate_content(p).text
            st.session_state.files[st.session_state.active]["content"] = res
            st.session_state.chat.append(("user",prompt))
            st.session_state.chat.append(("ai","Code updated"))

    for role,msg in st.session_state.chat[-6:]:
        if role=="user":
            st.markdown(f"<div class='user'>{msg}</div>",unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai'>{msg}</div>",unsafe_allow_html=True)
