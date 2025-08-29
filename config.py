import os
from dotenv import load_dotenv

load_dotenv()

FALLBACK_TEXT = "I'm having trouble connecting right now. Please try again."

# ✅ Use the variable names, not the keys themselves
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Persona configuration
DEFAULT_PERSONA_ID = os.getenv("DEFAULT_PERSONA_ID", "default")
