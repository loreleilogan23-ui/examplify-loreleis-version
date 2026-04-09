import streamlit as st
import pandas as pd
import random
import re

# --- 1. Initialization ---
if "state_v5_4" not in st.session_state:
    st.session_state.update({
        "full_bank": None, "current_quiz": [], "user_answers": {}, 
        "idx": 0, "exam_complete": False, "shuffled_options_map": {}, 
        "seen_ids": set(), "quiz_size": 40, "filename": "Practice Exam", 
        "state_v5_4": True
    })

# --- 2. Professional Styling ---
st.set_page_config(page_title="Examplify (Lorelei's version)", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #f2f5f7; }
    
    /* SIDEBAR - Clean Navigator */
    section[data-testid="stSidebar"] {
        background-color: #1a2c3d !important;
        border-right: 1px solid #c8d1d9;
    }
    
    /* ACTION BAR */
    .action-bar {
        background-color: #0d1e2e;
        color: white; padding: 15px 30px;
        display: flex; justify-content: space-between; align-items: center;
        margin: -10px -10px 20px -10px;
    }

    /* WORKSPACE */
    .exam-workspace {
        background-color: white; padding: 40px; border-radius: 4px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); min-height: 450px;
    }
    .question-header {
        color: #7f8c8d; font-size: 1.1rem; font-weight: 500;
        margin-bottom: 10px; text-transform: uppercase;
    }
    .vignette-text {
        font-size: 1.25rem; line-height: 1.7; color: #1a1a1a;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Sampling Logic ---
def get_weighted_quiz(df, quiz_size):
    available_df = df[~df.index.isin(st.session_state.seen_ids)].copy()
    if len(available_df) < quiz_size:
        st.session_state.seen_ids = set()
        available_df = df.copy()

    def extract_lec_id(topic):
        match = re.search(r'(CIB\d+-\d+)', str(topic))
        return match.group(1) if match else "Misc"

    available_df['Lec_ID'] = available_df['Topic'].apply(extract_lec_id)
    counts = available_df['Lec_ID'].value_counts()
    total_available = len(available_df)
    selected_indices = []
    
    for lec, count in counts.items():
        num_to_pick = round((count / total_available) * quiz_size)
        if num_to_pick > 0:
            lec_indices = available_df[available_df['Lec_ID'] == lec].index.tolist()
            selected_indices.extend(random.sample(lec_indices, min(len(lec_indices), num_to_pick)))
    
    random.shuffle(selected_indices)
    final_indices = selected_indices[:quiz_size]
    st.session_state.seen_ids.update(final_indices)
    return available_df.loc[final_indices].to_dict('records')

# --- 4. Sidebar (Navigator only) ---
with st.sidebar:
    if st.session_state.current_quiz and not st.session_state.exam_complete:
        st.write("") # Spacer instead of text
        for i in range(len(st.session_state.current_quiz)):
            is_ans = i in st.session_state.user_answers
            label = f"✓ {i+1}" if is_ans else f" {i+1}"
            if st.button(label, key=f"nav_{i}", type="primary" if i == st.session_state.idx else "secondary", use_container_width=True):
                st.session_state.idx = i
                st.rerun()

# --- 5. Main Content ---
if st.session_state.full_bank is None:
    st.header("Welcome to Examplify (Lorelei's Version)")
    uploaded_file = st.file_uploader("To begin, upload your practice question bank (CSV format). Lectures will be proportionally represented in each randomized quiz.", type="csv")
    if uploaded_file:
        st.session_state.full_bank = pd.read_csv(uploaded_file)
        st.session_state.filename = uploaded_file.name.replace('.csv', '')
        st.rerun()

elif not st.session_state.current_quiz:
    st.header(f"{st.session_state.filename}")
    q_size = st.number_input("Question Count:", min_value=1, max_value=len(st.session_state.full_bank), value=40)
    if st.button("START EXAM"):
        st.session_state.quiz_size = q_size
        st.session_state.current_quiz = get_weighted_quiz(st.session_state.full_bank, q_size)
        st.rerun()

elif not st.session_state.exam_complete:
    idx = st.session_state.idx
    q = st.session_state.current_quiz[idx]
    
    st.markdown(f"""
    <div class="action-bar">
        <div style="font-weight:bold;">{st.session_state.filename}</div>
        <div>QUESTION {idx + 1} OF {len(st.session_state.current_quiz)}</div>
        <div style="font-size: 0.85rem; opacity: 0.7;">ID: {q.get('Topic', 'N/A')[:10]}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="exam-workspace">
            <div class="question-header">Question {idx + 1}</div>
            <div class="vignette-text">{q['Question']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("") 

    if idx not in st.session_state.shuffled_options_map:
        opts = [q[k] for k in ['A', 'B', 'C', 'D', 'E'] if k in q and pd.notna(q[k])]
        random.shuffle(opts)
        st.session_state.shuffled_options_map[idx] = opts
    
    current_opts = st.session_state.shuffled_options_map[idx]
    saved_val = st.session_state.user_answers.get(idx, None)
    
    user_choice = st.radio("Options", current_opts, index=current_opts.index(saved_val) if saved_val in current_opts else None, key=f"r_{idx}", label_visibility="collapsed")
    
    if user_choice:
        st.session_state.user_answers[idx] = user_choice

    st.divider()
    b1, _, b3 = st.columns([1,1.5,1])
    if b1.button("⬅️ PREVIOUS") and idx > 0:
        st.session_state.idx -= 1; st.rerun()
    if b3.button("NEXT ➡️") and idx < len(st.session_state.current_quiz) - 1:
        st.session_state.idx += 1; st.rerun()
    
    if st.button("🏁 FINISH & SCORE EXAM", type="primary", use_container_width=True):
        st.session_state.exam_complete = True; st.rerun()

else:
    # --- Results ---
    st.header(f"Performance: {st.session_state.filename}")
    correct_count = sum(1 for i, q in enumerate(st.session_state.current_quiz) if st.session_state.user_answers.get(i) == q[q['Correct_Answer']])
    st.metric("Final Accuracy", f"{int(correct_count/len(st.session_state.current_quiz)*100)}%")

    missed_lecs = []
    missed_details = []
    for i, q in enumerate(st.session_state.current_quiz):
        correct = q[q['Correct_Answer']]
        user = st.session_state.user_answers.get(i)
        if user != correct:
            match = re.search(r'(CIB\d+-\d+)', str(q['Topic']))
            lec = match.group(1) if match else "Misc"
            missed_lecs.append(lec)
            missed_details.append({"Q": i+1, "Lec": lec, "Stem": q['Question'], "User": user, "Correct": correct})

    if missed_lecs:
        st.subheader("🚩 Weakness Tracker")
        st.table(pd.Series(missed_lecs).value_counts().reset_index().rename(columns={0: 'Misses', 'index': 'Lecture ID'}))
        
        st.subheader("📖 Question Review")
        for miss in missed_details:
            with st.expander(f"Question {miss['Q']} - Topic: {miss['Lec']}", expanded=True):
                st.write(miss['Stem'])
                st.markdown(f"<span style='color:#d63031; font-weight:bold;'>❌ Your Answer:</span> {miss['User']}", unsafe_allow_html=True)
                st.markdown(f"✅ **Correct Answer:** {miss['Correct']}")

    if st.button("🚀 NEW BALANCED QUIZ", type="primary", use_container_width=True):
        st.session_state.update({"current_quiz": [], "user_answers": {}, "idx": 0, "exam_complete": False, "shuffled_options_map": {}})
        st.rerun()
