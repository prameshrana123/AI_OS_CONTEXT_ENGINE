from executor import ActionExecutor

def test_executor():
    print("🧪 Testing ActionExecutor...")

    # Test 1: Allowed action (notify_user)
    print("\n--- Test 1: notify_user ---")
    prop = {"action": "notify_user", "reason": "Test notification"}
    result = ActionExecutor.execute(prop)
    print(f"Result: {result} (Expected: True)")

    # Test 2: Disallowed action
    print("\n--- Test 2: delete_system32 ---")
    prop = {"action": "delete_system32", "reason": "Malicious intent"}
    result = ActionExecutor.execute(prop)
    print(f"Result: {result} (Expected: False)")

    # Test 3: None action
    print("\n--- Test 3: none ---")
    prop = {"action": "none", "reason": "No action needed"}
    result = ActionExecutor.execute(prop)
    print(f"Result: {result} (Expected: True)")
    
    # Test 4: Copy to clipboard
    print("\n--- Test 4: copy_to_clipboard ---")
    prop = {"action": "copy_to_clipboard", "content": "Executor Test Success"}
    result = ActionExecutor.execute(prop)
    print(f"Result: {result} (Expected: True)")

if __name__ == "__main__":
    test_executor()
