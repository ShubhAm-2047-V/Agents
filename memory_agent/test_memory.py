"""
test_memory.py
Quick standalone test - run this after adding your API key in config.py
to make sure everything works before wiring it into Orion.

    python test_memory.py
"""

from memory_agent import memory_agent

print("=== Orion Memory Agent Test ===\n")

# 1. Seed a couple of manual memories (no API call, instant)
memory_agent.add_manual_memory("User's name is Shubham and he runs Shubdeep Labs.", "personal")
memory_agent.add_manual_memory("User prefers free/zero-cost tech stacks.", "preference")

# 2. Simulate a conversation turn and let Gemini decide if it's worth saving
user_input = "I just switched my Orion assistant to use Gemini Flash-Lite instead of phi3 for most tasks."
assistant_reply = "Got it, noted that Orion now uses Gemini Flash-Lite as the primary model."

print("Running remember()... (this makes 1 API call)")
saved = memory_agent.remember(user_input, assistant_reply)
print("Saved:", saved, "\n")

# 3. Recall relevant memories for a new query (fully offline, no API call)
query = "what model does my assistant use"
context = memory_agent.recall(query)
print("Recall for:", query)
print(context, "\n")

# 4. List everything stored
print("All memories:")
for row in memory_agent.list_memories():
    print(" ", row)
