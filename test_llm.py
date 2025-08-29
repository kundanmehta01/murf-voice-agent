import asyncio
from config import GEMINI_API_KEY
from services.llm import llm_generate   # <-- fixed import

async def main():
    print("🔑 GEMINI_API_KEY loaded:", bool(GEMINI_API_KEY))

    response = await llm_generate("gemini-pro", "Hello, how are you?")
    print("🤖 Gemini response:", response)

asyncio.run(main())
