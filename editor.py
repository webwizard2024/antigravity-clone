import streamlit as st
import google.generativeai as genai
import subprocess
import sys
import os
import json
from pathlib import Path
import tempfile

# Page config
st.set_page_config(
    page_title="Anti-Gravity IDE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for VS Code-like appearance
st.markdown("""
<style>
    /* Main IDE styling */
    .stApp {
        background-color: #1e1e1e;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #252526;
    }
    
    /* Text areas (editor) */
    .stTextArea textarea {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
        font-size: 14px !important;
        background-color: #1e1e1e !important;
        color: #d4d4d4 !important;
        border: 1px solid #3e3e42 !important;
        line-height: 1.5 !important;
    }
    
    /* Terminal styling */
    .terminal-output {
        background-color: #1e1e1e;
        color: #cccccc;
        font-family: 'Consolas', 'Monaco', monospace;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #3e3e42;
        min-height: 200px;
        max-height: 300px;
        overflow-y: auto;
        white-space: pre-wrap;
        font-size: 13px;
    }
    
    /* File tabs */
    .file-tab {
        display: inline-block;
        padding: 8px 16px;
        margin: 2px;
        background-color: #2d2d30;
        color: #cccccc;
        border-radius: 4px 4px 0 0;
        cursor: pointer;
        border: 1px solid #3e3e42;
        font-size: 13px;
    }
    
    .file-tab.active {
        background-color: #1e1e1e;
        border-bottom: 2px solid #007acc;
    }
    
    /* File explorer */
    .file-item {
        padding: 6px 12px;
        cursor: pointer;
        color: #cccccc;
        font-size: 13px;
        border-radius: 3px;
        margin: 2px 0;
    }
    
    .file-item:hover {
        background-color: #2a2d2e;
    }
    
    .file-item.selected {
        background-color: #37373d;
    }
    
    /* AI Chat styling */
    .ai-message {
        background-color: #2d2d30;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #007acc;
        color: #cccccc;
    }
    
    .user-message {
        background-color: #1e1e1e;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #4ec9b0;
        color: #cccccc;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #0e639c;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 13px;
    }
    
    .stButton button:hover {
        background-color: #1177bb;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #cccccc !important;
    }
    
    /* Status bar */
    .status-bar {
        background-color: #007acc;
        color: white;
        padding: 5px 15px;
        font-size: 12px;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'files' not in st.session_state:
    st.session_state.files = {
        'main.py': {
            'content': '# Welcome to Anti-Gravity IDE\n# Write your code here\n\nprint("Hello, World!")',
            'language': 'python'
        }
    }

if 'active_file' not in st.session_state:
    st.session_state.active_file = 'main.py'

if 'terminal_output' not in st.session_state:
    st.session_state.terminal_output = ''

if 'ai_chat_history' not in st.session_state:
    st.session_state.ai_chat_history = []

if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

# Sidebar - File Explorer & Settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key_input = st.text_input(
        "Gemini API Key", 
        type="password", 
        value=st.session_state.api_key,
        key="api_key_input"
    )
    if api_key_input:
        st.session_state.api_key = api_key_input
    
    st.markdown("---")
    st.markdown("### 📁 File Explorer")
    
    # New file creation
    with st.expander("➕ New File", expanded=False):
        new_filename = st.text_input("Filename", key="new_file_input")
        file_language = st.selectbox(
            "Language",
            ["python", "javascript", "java", "cpp", "c", "go", "rust", "html", "css"],
            key="file_lang"
        )
        if st.button("Create File", key="create_file_btn"):
            if new_filename and new_filename not in st.session_state.files:
                st.session_state.files[new_filename] = {
                    'content': f'# New {file_language} file\n',
                    'language': file_language
                }
                st.session_state.active_file = new_filename
                st.rerun()
    
    # File list
    st.markdown("#### Files:")
    for filename in st.session_state.files.keys():
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                f"📄 {filename}", 
                key=f"file_{filename}",
                use_container_width=True,
                type="primary" if filename == st.session_state.active_file else "secondary"
            ):
                st.session_state.active_file = filename
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{filename}"):
                if len(st.session_state.files) > 1:
                    del st.session_state.files[filename]
                    st.session_state.active_file = list(st.session_state.files.keys())[0]
                    st.rerun()

# Main content area
st.markdown("## ⚡ Anti-Gravity IDE")

# Create main layout
col_editor, col_ai = st.columns([2, 1])

# Editor section
with col_editor:
    st.markdown(f"### 📝 Editor - {st.session_state.active_file}")
    
    # Get current file
    current_file = st.session_state.files[st.session_state.active_file]
    
    # Code editor - use unique key that changes when content updates
    editor_key = f"editor_{st.session_state.active_file}_{hash(current_file['content'])}"
    code_content = st.text_area(
        "Code Editor",
        value=current_file['content'],
        height=400,
        key=editor_key,
        label_visibility="collapsed"
    )
    
    # Update file content only if user is typing (not after AI update)
    if code_content != current_file['content']:
        st.session_state.files[st.session_state.active_file]['content'] = code_content
    
    # Editor controls
    col_run, col_clear = st.columns([1, 1])
    with col_run:
        run_button = st.button("▶️ Run Code", use_container_width=True, type="primary")
    with col_clear:
        if st.button("🗑️ Clear Terminal", use_container_width=True):
            st.session_state.terminal_output = ''
            st.rerun()
    
    # Terminal section
    st.markdown("### 💻 Terminal")
    
    if run_button:
        if current_file['language'] == 'python':
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code_content)
                    temp_file = f.name
                
                # Run the code
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                output = f">>> Running {st.session_state.active_file}\n\n"
                if result.stdout:
                    output += result.stdout
                if result.stderr:
                    output += f"\n❌ Error:\n{result.stderr}"
                
                st.session_state.terminal_output = output
                
                # Clean up
                os.unlink(temp_file)
                
            except subprocess.TimeoutExpired:
                st.session_state.terminal_output = "❌ Execution timeout (10 seconds)"
            except Exception as e:
                st.session_state.terminal_output = f"❌ Error: {str(e)}"
        
        elif current_file['language'] == 'javascript':
            st.session_state.terminal_output = "ℹ️ JavaScript execution requires Node.js. Save file and run: node filename.js"
        
        else:
            st.session_state.terminal_output = f"ℹ️ Direct execution not supported for {current_file['language']}. Please compile/run manually."
    
    # Display terminal output
    st.markdown(
        f'<div class="terminal-output">{st.session_state.terminal_output if st.session_state.terminal_output else "Terminal ready..."}</div>',
        unsafe_allow_html=True
    )

# AI Agent section
with col_ai:
    st.markdown("### 🤖 AI Agent")
    
    # AI prompt input
    ai_prompt = st.text_area(
        "Enter your prompt:",
        height=100,
        placeholder="Examples:\n- Fix errors in my code\n- Add error handling\n- Create a function to...\n- Refactor this code\n- Generate a REST API",
        key="ai_prompt_input"
    )
    
    col_gen, col_fix = st.columns(2)
    with col_gen:
        generate_btn = st.button("✨ Generate", use_container_width=True)
    with col_fix:
        fix_btn = st.button("🔧 Fix Code", use_container_width=True)
    
    # AI Chat history
    st.markdown("#### 💬 Chat History")
    chat_container = st.container(height=400)
    
    with chat_container:
        for msg in st.session_state.ai_chat_history[-10:]:  # Show last 10 messages
            if msg['role'] == 'user':
                st.markdown(f'<div class="user-message">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-message">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

# AI Agent Logic
if (generate_btn or fix_btn) and st.session_state.api_key:
    if not ai_prompt and generate_btn:
        st.error("⚠️ Please enter a prompt")
    else:
        with st.spinner("🤖 AI Agent working..."):
            try:
                genai.configure(api_key=st.session_state.api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                current_code = st.session_state.files[st.session_state.active_file]['content']
                current_lang = st.session_state.files[st.session_state.active_file]['language']
                
                if fix_btn:
                    prompt = f"""You are an expert code reviewer. Fix all errors, bugs, and issues in this {current_lang} code.
                    
Current code:
```{current_lang}
{current_code}
```

Provide ONLY the corrected code without any explanations or markdown formatting. Just the raw code."""
                    
                    user_msg = "Fix all errors in my code"
                
                else:  # generate_btn
                    if "fix" in ai_prompt.lower() or "error" in ai_prompt.lower():
                        prompt = f"""You are an expert code reviewer. {ai_prompt}
                        
Current code:
```{current_lang}
{current_code}
```

Provide ONLY the corrected/modified code without any explanations or markdown formatting. Just the raw code."""
                    else:
                        prompt = f"""You are an expert {current_lang} programmer. {ai_prompt}

Current code context:
```{current_lang}
{current_code}
```

Provide ONLY the complete code without any explanations or markdown formatting. Just the raw code that fulfills the request."""
                    
                    user_msg = ai_prompt
                
                # Get AI response
                response = model.generate_content(prompt)
                ai_response = response.text
                
                # Clean up response (remove markdown code blocks if present)
                if "```" in ai_response:
                    # Extract code from markdown blocks
                    parts = ai_response.split("```")
                    for i, part in enumerate(parts):
                        if i % 2 == 1:  # Odd indices are code blocks
                            # Remove language identifier if present
                            lines = part.strip().split('\n')
                            if lines[0].strip() in ['python', 'javascript', 'java', 'cpp', 'c', 'go', 'rust', 'html', 'css']:
                                ai_response = '\n'.join(lines[1:])
                            else:
                                ai_response = part.strip()
                            break
                
                # Update the file with AI-generated code
                st.session_state.files[st.session_state.active_file]['content'] = ai_response.strip()
                
                # Add to chat history
                st.session_state.ai_chat_history.append({
                    'role': 'user',
                    'content': user_msg
                })
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'content': f"✅ Code updated in {st.session_state.active_file}"
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ AI Error: {str(e)}")
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'content': f"❌ Error: {str(e)}"
                })

elif (generate_btn or fix_btn) and not st.session_state.api_key:
    st.error("⚠️ Please enter your Gemini API key in the sidebar")

# Status bar
st.markdown(
    f'<div class="status-bar">Active File: {st.session_state.active_file} | Language: {st.session_state.files[st.session_state.active_file]["language"]} | Lines: {len(code_content.split(chr(10)))} | AI Agent: {"Ready" if st.session_state.api_key else "API Key Required"}</div>',
    unsafe_allow_html=True
)