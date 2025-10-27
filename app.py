import streamlit as st
import google.generativeai as genai
import os

# --- Configuration ---
# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="AI Fitness Coach",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# Configure the Gemini API
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}. Make sure you have a .streamlit/secrets.toml file with your GEMINI_API_KEY.")
    st.stop()

# --- Model and Agent Definition ---

def get_gemini_response(prompt):
    """Generates a response from the Gemini model."""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {e}"

def build_agent_prompt(user_profile, chat_history, user_query):
    """Builds the full prompt for the AI agent."""
    
    # 1. The Agent's Persona and Instructions
    system_prompt = f"""
    You are "CoachFit AI", an expert personal trainer and nutritionist. 
    Your goal is to provide safe, effective, and personalized fitness and diet advice.

    **Your User's Profile:**
    - Age: {user_profile.get('age', 'Not provided')}
    - Weight: {user_profile.get('weight', 'Not provided')} kg
    - Height: {user_profile.get('height', 'Not provided')} cm
    - Fitness Goal: {user_profile.get('goal', 'Not provided')}
    - Experience Level: {user_profile.get('experience', 'Not provided')}

    **Your Task:**
    1.  **Always** use the user's profile to tailor your advice.
    2.  Be encouraging, clear, and professional.
    3.  If you provide a workout plan, format it clearly (e.g., using Markdown tables or lists).
    4.  If the user asks for something outside of fitness, nutrition, or wellness,
        gently remind them you are a fitness coach and cannot help with that.
    5.  Keep your answers concise but informative.
    
    **Conversation History:**
    {chat_history}
    
    **User's New Query:**
    {user_query}
    
    **CoachFit AI's Response:**
    """
    return system_prompt

# --- Streamlit App UI ---

st.title("🏋️‍♂️ Your Personal AI Fitness Coach")
st.caption("Powered by Google Gemini")

# --- 1. User Profile Setup (in Sidebar) ---

with st.sidebar:
    st.header("Your Profile")
    st.write("Please fill in your details so I can personalize your plan.")
    
    # Check if profile is already in session state
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {}

    # Form for user details
    with st.form(key="profile_form"):
        age = st.number_input("Age", min_value=16, max_value=100, 
                             value=st.session_state.user_profile.get('age', 25))
        weight = st.number_input("Weight (kg)", min_value=40.0, max_value=200.0, 
                                value=st.session_state.user_profile.get('weight', 70.0), format="%.1f")
        height = st.number_input("Height (cm)", min_value=140.0, max_value=230.0, 
                                value=st.session_state.user_profile.get('height', 175.0), format="%.1f")
        goal = st.selectbox("Primary Fitness Goal", 
                            ["Lose Weight", "Build Muscle", "Improve Endurance", "General Fitness", "Learn a specific skill (e.g., pull-up)"],
                            index=["Lose Weight", "Build Muscle", "Improve Endurance", "General Fitness", "Learn a specific skill (e.g., pull-up)"].index(st.session_state.user_profile.get('goal', 'General Fitness')))
        experience = st.selectbox("Experience Level", 
                                  ["Beginner", "Intermediate", "Advanced"],
                                  index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.user_profile.get('experience', 'Beginner')))
        
        submit_button = st.form_submit_button(label="Save Profile")

    if submit_button:
        st.session_state.user_profile = {
            "age": age,
            "weight": weight,
            "height": height,
            "goal": goal,
            "experience": experience
        }
        st.success("Profile saved!")
        st.rerun() # Rerun to update the main app state

# --- 2. Main Chat Interface ---

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Check if the profile is set. If not, ask the user to set it.
if not st.session_state.user_profile:
    st.info("Please fill out your profile in the sidebar to start chatting!")
    st.stop()

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input for new messages
if prompt := st.chat_input("What's on your mind? (e.g., 'Create a 3-day workout plan for me')"):
    
    # 1. Add user message to chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Build the full prompt for the agent
    # We create a simple string history for the prompt
    history_string = ""
    for msg in st.session_state.messages[:-1]: # All but the last message
        history_string += f"**{msg['role'].title()}**: {msg['content']}\n\n"
        
    full_prompt = build_agent_prompt(
        user_profile=st.session_state.user_profile,
        chat_history=history_string,
        user_query=prompt
    )

    # 3. Get response from the AI agent
    with st.spinner("Your AI Coach is thinking..."):
        response = get_gemini_response(full_prompt)
    
    # 4. Add AI response to chat history and display it
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)