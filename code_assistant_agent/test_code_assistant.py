"""
test_code_assistant.py
Quick standalone test. Run this after setting your API key in config.py.

    python test_code_assistant.py
"""

from code_assistant_agent import code_assistant_agent as coder

print("=== Orion Code Assistant Agent Test ===\n")

print("1. Writing code from a spec (1 API call):")
code = coder.write_code("a function that checks if a string is a palindrome")
print(code, "\n")

print("2. Explaining code (1 API call):")
explanation = coder.explain_code(code)
print(explanation, "\n")

print("3. Debugging broken code (1 API call):")
broken = """
def divide(a, b):
    return a / b

print(divide(10, 0))
"""
fix = coder.debug_code(broken, error_message="ZeroDivisionError: division by zero")
print(fix, "\n")

print("4. Reviewing code (1 API call):")
review = coder.review_code(code)
print(review, "\n")

print("5. Debug with real execution (runs code locally, then 1 API call if it fails):")
result = coder.debug_with_execution(broken)
print(result)
