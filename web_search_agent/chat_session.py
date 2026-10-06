"""
chat_session.py
Interactive continuous research chat mode for Orion Web Search Agent.
Allows multi-turn conversational exploration over search results without re-searching.
"""

import sys
import config
from google import genai
from google.genai import types


def run_interactive_chat(initial_context: str = None, topic: str = "Research Session"):
    """
    Launches an interactive continuous chat session with conversational memory.
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    system_instruction = f"""You are Orion's Interactive Research Copilot.
You have context from the user's recent web searches and research notes.
Answer follow-up questions directly, concisely, and accurately based on the established context.
Maintain a helpful, senior research analyst persona."""

    print("\n" + "═" * 60)
    print(f"💬 INTERACTIVE RESEARCH CHAT: {topic.upper()}")
    print("═" * 60)
    print("Ask any follow-up questions, drill into details, or request clarifications.")
    print("Type 'exit', 'back', or 'quit' to return to the main search prompt.\n")

    history = []
    if initial_context:
        history.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"Here is the research context from our search:\n\n{initial_context}\n\nPlease keep this context in mind for our conversation.")]
        ))
        history.append(types.Content(
            role="model",
            parts=[types.Part.from_text(text=f"I have reviewed the research context on '{topic}'. What specific aspect or question would you like to explore further?")]
        ))
        print(f"🤖 Copilot: I am ready with context on '{topic}'. What would you like to know?\n")

    while True:
        try:
            user_input = input("ResearchChat > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "back", "quit", "q", "done"):
                print("\n🔙 Exiting Research Chat session.\n")
                break

            # Add user message
            history.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)]
            ))

            print("\n🤖 Thinking...\n")
            response = client.models.generate_content(
                model=config.MODEL,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )

            assistant_reply = response.text.strip()
            print(f"🤖 Copilot:\n{assistant_reply}\n")
            print("─" * 60 + "\n")

            # Add model response to history
            history.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text=assistant_reply)]
            ))

        except KeyboardInterrupt:
            print("\n\n🔙 Exiting Research Chat.")
            break
        except Exception as e:
            print(f"⚠️ Chat Error: {e}\n")
