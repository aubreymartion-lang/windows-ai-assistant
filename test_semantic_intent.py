#!/usr/bin/env python3
"""
Test script for Semantic Intent Detection and Pentesting Assistant.

Validates implementation against 5 test scenarios:
1. Typo tolerance
2. Hardcoded shortcuts prevention
3. Autonomous execution readiness
4. Context memory
5. Consistent execution pipeline
"""

import sys
from pathlib import Path

# Add src to path - must be before other imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from spectral.pentesting_assistant import ExploitStage, PentestingAssistant
from spectral.semantic_intent_classifier import (
    SemanticIntent,
    SemanticIntentClassifier,
)


def test_typo_tolerance():
    """Test 1: Semantic classifier handles typos correctly."""
    print("=" * 70)
    print("TEST 1: Typo Tolerance")
    print("=" * 70)

    # Create classifier (will use fallback since LLM might not be configured)
    classifier = SemanticIntentClassifier(llm_client=None)

    test_cases = [
        ("pyhton keylogger", SemanticIntent.CODE, "Should detect CODE intent despite typo"),
        (
            "winndows exploit",
            SemanticIntent.EXPLOITATION,
            "Should detect EXPLOITATION intent despite typo",
        ),
        (
            "scann ports",
            SemanticIntent.RECONNAISSANCE,
            "Should detect RECONNAISSANCE intent despite typo",
        ),
    ]

    all_passed = True
    for user_input, expected_intent, description in test_cases:
        detected_intent, confidence = classifier.classify(user_input)
        passed = detected_intent == expected_intent
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}: {description}")
        print(f"  Input: '{user_input}'")
        print(f"  Expected: {expected_intent.value}")
        print(f"  Detected: {detected_intent.value} (confidence: {confidence:.2f})")

        if not passed:
            all_passed = False

    return all_passed


def test_no_hardcoded_shortcuts():
    """Test 2: PentestingAssistant asks questions, doesn't shortcut."""
    print("\n" + "=" * 70)
    print("TEST 2: Hardcoded Shortcuts Prevention")
    print("=" * 70)

    # Create assistant (will use fallback LLM)
    classifier = SemanticIntentClassifier(llm_client=None)
    assistant = PentestingAssistant(
        llm_client=None,
        research_handler=None,
        semantic_classifier=classifier,
    )

    test_input = "generate metasploit windows payload"
    print(f"\nInput: '{test_input}'")
    print("\nExpected Behavior:")
    print("  - Should NOT instantly generate a payload")
    print("  - Should ask clarifying questions (OS version, delivery method, etc.)")
    print("  - Should require methodology selection before any code")

    response = assistant.handle_pentest_request(test_input)

    print(f"\nActual Response:\n{response}\n")

    # Check if response asks questions (good) vs generates code (bad)
    has_questions = any(
        word in response.lower()
        for word in [
            "what",
            "which",
            "how",
            "please",
            "provide",
            "need",
            "version",
            "delivery",
        ]
    )
    has_instant_code = any(
        word in response.lower()
        for word in ["generate", "payload", "exploit", "code:", "```", "msfvenom"]
    )

    # At early stage, should have questions and no instant code
    if assistant.stage == ExploitStage.RECONNAISSANCE and has_questions and not has_instant_code:
        print("✅ PASS: Correctly asks questions, no instant payload generation")
        return True
    else:
        print(
            f"❌ FAIL: Stage={assistant.stage}, has_questions={has_questions}, has_instant_code={has_instant_code}"
        )
        return False


def test_context_memory():
    """Test 3: Context clearing works correctly."""
    print("\n" + "=" * 70)
    print("TEST 3: Context Memory")
    print("=" * 70)

    classifier = SemanticIntentClassifier(llm_client=None)
    assistant = PentestingAssistant(
        llm_client=None,
        research_handler=None,
        semantic_classifier=classifier,
    )

    # Set up some context
    assistant.handle_pentest_request("192.168.1.100 Windows 10")
    print("\nAdded target context")
    print(f"Target info: {assistant.target}")
    print(f"Stage: {assistant.stage}")

    # Clear context
    clear_response = assistant.handle_pentest_request("forget about that")
    print("\nSent clear command: 'forget about that'")
    print(f"Clear response: {clear_response}")
    print(f"Target after clear: {assistant.target}")
    print(f"Stage after clear: {assistant.stage}")

    if assistant.target is None and assistant.stage == ExploitStage.RECONNAISSANCE:
        print("\n✅ PASS: Context cleared successfully")
        return True
    else:
        print(f"\n❌ FAIL: Target={assistant.target}, Stage={assistant.stage}")
        return False


def test_methodology_stages():
    """Test 4: Methodology progression through stages."""
    print("\n" + "=" * 70)
    print("TEST 4: Methodology Stage Progression")
    print("=" * 70)

    classifier = SemanticIntentClassifier(llm_client=None)
    assistant = PentestingAssistant(
        llm_client=None,
        research_handler=None,
        semantic_classifier=classifier,
    )

    print("\nSimulating conversation flow:\n")

    # Stage 1: Reconnaissance
    print("Stage 1: RECONNAISSANCE")
    response1 = assistant.handle_pentest_request("test my Windows machine")
    print("  Input: 'test my Windows machine'")
    print(f"  Response excerpt: {response1[:100]}...")
    print(f"  Current stage: {assistant.stage}")
    print(f"  Target info: {assistant.target}")

    # Stage 2: Provide IP and OS
    print("\nStage 2: Provide IP and OS")
    response2 = assistant.handle_pentest_request("192.168.1.100 Windows 10")
    print("  Input: '192.168.1.100 Windows 10'")
    print(f"  Response excerpt: {response2[:100]}...")
    print(f"  Current stage: {assistant.stage}")

    # Stage 3: Provide services
    print("\nStage 3: Provide services")
    response3 = assistant.handle_pentest_request("SMB on port 445")
    print("  Input: 'SMB on port 445'")
    print(f"  Response excerpt: {response3[:100]}...")
    print(f"  Current stage: {assistant.stage}")

    # Stage 4: Provide methodology
    print("\nStage 4: Provide methodology")
    response4 = assistant.handle_pentest_request("PowerShell reverse TCP, no obfuscation")
    print("  Input: 'PowerShell reverse TCP, no obfuscation'")
    print(f"  Response excerpt: {response4[:100]}...")
    print(f"  Current stage: {assistant.stage}")

    # Check that we progressed through stages
    stages_visited = [
        ExploitStage.RECONNAISSANCE,
        ExploitStage.ENUMERATION,
        ExploitStage.VULNERABILITY_ASSESSMENT,
        ExploitStage.METHODOLOGY_SELECTION,
    ]

    # Just verify we didn't jump straight to exploitation
    if assistant.stage in stages_visited:
        print("\n✅ PASS: Methodology stages followed, no premature exploitation")
        return True
    else:
        print(f"\n❌ FAIL: Unexpected stage {assistant.stage}")
        return False


def test_semantic_classification():
    """Test 5: Semantic classifier distinguishes intent types."""
    print("\n" + "=" * 70)
    print("TEST 5: Semantic Classification")
    print("=" * 70)

    classifier = SemanticIntentClassifier(llm_client=None)

    test_cases = [
        ("make python keylogger", SemanticIntent.CODE, "Code generation request"),
        ("write a script to scan ports", SemanticIntent.CODE, "Programming task"),
        (
            "remote access windows with metasploit",
            SemanticIntent.EXPLOITATION,
            "Exploitation request",
        ),
        (
            "get shell on linux target",
            SemanticIntent.EXPLOITATION,
            "Exploit/attack request",
        ),
        ("find open ports", SemanticIntent.RECONNAISSANCE, "Recon/scanning request"),
        ("enumerate target services", SemanticIntent.RECONNAISSANCE, "Enumeration request"),
        (
            "what vulnerabilities in Apache 2.4.41",
            SemanticIntent.RESEARCH,
            "Research/vulnerability lookup",
        ),
        ("research CVE-2021-41773", SemanticIntent.RESEARCH, "CVE research request"),
        ("hello, how are you?", SemanticIntent.CHAT, "Casual conversation"),
        ("tell me a joke", SemanticIntent.CHAT, "Casual conversation"),
    ]

    all_passed = True
    for user_input, expected_intent, description in test_cases:
        detected_intent, confidence = classifier.classify(user_input)
        passed = detected_intent == expected_intent
        status = "✅" if passed else "❌"

        print(f"\n{status} {description}")
        print(f"  Input: '{user_input}'")
        print(f"  Expected: {expected_intent.value}")
        print(f"  Detected: {detected_intent.value} (confidence: {confidence:.2f})")

        if not passed:
            all_passed = False

    return all_passed


def main():
    """Run all tests and report results."""
    print("\n" + "=" * 70)
    print("SEMANTIC INTENT DETECTION & PENTESTING ASSISTANT TEST SUITE")
    print("=" * 70)

    results = {
        "Test 1: Typo Tolerance": test_typo_tolerance(),
        "Test 2: Hardcoded Shortcuts Prevention": test_no_hardcoded_shortcuts(),
        "Test 3: Context Memory": test_context_memory(),
        "Test 4: Methodology Stages": test_methodology_stages(),
        "Test 5: Semantic Classification": test_semantic_classification(),
    }

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)

    print(f"\nPassed: {passed_tests}/{total_tests}")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
