import sys
import tests.test_interview as t

def run_all_tests():
    print("=== Running AI Interview Agent Test Suite ===")
    
    test_functions = [
        ("Test 1: New interview session creation", t.test_01_new_interview_session),
        ("Test 2: Second conversation turn execution", t.test_02_second_conversation_turn),
        ("Test 3: Existing session retains state", t.test_03_existing_session_retains_state),
        ("Test 4: Minimum 8 questions enforcement", t.test_04_minimum_8_questions),
        ("Test 5: Minimum 4 curriculum days enforcement", t.test_05_minimum_4_curriculum_days),
        ("Test 6: Skipped topic is NOT treated as completed", t.test_06_skipped_topic_not_treated_as_completed),
        ("Test 7: Final response feedback structure validation (summary, strengths, gaps, next)", t.test_07_final_response_feedback_contract),
        ("Test 8: Unknown sessionId error handling (HTTP 404)", t.test_08_unknown_session_id_handling),
        ("Test 9: Invalid request payload error handling (HTTP 400)", t.test_09_invalid_request_handling),
        ("Test 10: Candidate personalization verification", t.test_10_candidate_personalization),
    ]

    passed = 0
    failed = 0

    for name, func in test_functions:
        try:
            func()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1

    print(f"\nTest Execution Summary: {passed} passed, {failed} failed.")
    if failed > 0:
        sys.exit(1)
    else:
        print("\nALL 10 AUTOMATED TEST CASES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
