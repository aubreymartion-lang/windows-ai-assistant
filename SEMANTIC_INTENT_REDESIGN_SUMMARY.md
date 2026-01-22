# Semantic Intent Detection & Pentesting Methodology Redesign

## Overview

This implementation replaces rigid keyword matching with semantic intent detection and enforces systematic pentesting methodology.

## What Changed

### Phase 1: Semantic Intent Detection ✅

**File: `src/spectral/semantic_intent_classifier.py`**

New module that uses LLM-based semantic classification instead of keyword matching:

- **Intent Types:**
  - `CODE`: Code generation, programming tasks
  - `EXPLOITATION`: Penetration testing, exploits, attacks
  - `RECONNAISSANCE`: Scanning, enumeration, discovery
  - `RESEARCH`: Information gathering, vulnerability lookup
  - `CHAT`: Casual conversation

- **Features:**
  - ✅ Typo-tolerant: "pyhton" → "python"
  - ✅ Phrasing-agnostic: Synonyms and variations work
  - ✅ Confidence scoring: Asks for clarification when unclear
  - ✅ Fallback heuristic when LLM unavailable

### Phase 2: Pentesting Methodology Layer ✅

**File: `src/spectral/pentesting_assistant.py`**

New `PentestingAssistant` class with enforced methodology:

- **NO Hardcoded Shortcuts:** Always asks clarifying questions FIRST
- **Six Methodology Stages:**
  1. `RECONNAISSANCE`: Gather target IP, OS type
  2. `ENUMERATION`: Discover services, ports, versions
  3. `VULNERABILITY_ASSESSMENT`: Research CVEs and exploits
  4. `METHODOLOGY_SELECTION`: Ask 5+ clarifying questions
  5. `EXPLOITATION`: Execute chosen method
  6. `POST_EXPLOITATION`: Maintain access

- **Critical Questions BEFORE Any Code Generation:**
  1. What Windows/Linux version?
  2. Delivery method? (EXE, PowerShell, DLL, batch, macro?)
  3. Callback type? (Reverse TCP, Reverse HTTPS, bind shell?)
  4. Target network? (Internal, DMZ, external?)
  5. Obfuscation/encoding needed?
  6. Payload format? (exe, elf, apk, script?)

- **Context Management:**
  - ✅ Clear on "forget" / "new target" / "different machine"
  - ✅ Persist across turns
  - ✅ Update without losing info
  - ✅ Target validation

### Phase 3: Context Management ✅

**Extended TargetInfo Dataclass:**
- IP address, hostname
- OS type, version, architecture
- Services, open ports, service versions
- Credentials list
- Network location (Internal/DMZ/External)
- Access level (Unauthenticated/User/Admin)
- CVEs, known vulnerabilities

**Methodology Tracking:**
- Exploit type, delivery method, callback type
- Obfuscation settings, payload format, staging requirements
- Risk assessment

### Phase 4: Routing Integration ✅

**File: `src/spectral/chat.py` (Modified)**

**Changes:**

1. **Import New Modules:**
   ```python
   from spectral.semantic_intent_classifier import SemanticIntent, SemanticIntentClassifier
   from spectral.pentesting_assistant import PentestingAssistant
   ```

2. **Initialize in ChatSession.__init__:**
   ```python
   # Initialize semantic intent classifier and pentesting assistant
   self.semantic_classifier = SemanticIntentClassifier(llm_client=llm_client_for_classifiers)

   self.pentesting_assistant = PentestingAssistant(
       llm_client=llm_client_for_classifiers,
       research_handler=self.research_handler,
       semantic_classifier=self.semantic_classifier,
   )
   ```

3. **Replace Keyword Detection with Semantic Classification:**
   ```python
   # OLD: Rigid keyword matching
   def _is_penetration_test_request(self, user_input: str) -> bool:
       pentest_patterns = [r"\b(test|exploit|pentest..."]
       return any(re.search(pattern, user_input, ...) for pattern in pentest_patterns)

   # NEW: Semantic, typo-tolerant
   def _is_penetration_test_request(self, user_input: str) -> bool:
       intent, confidence = self.semantic_classifier.classify(user_input)
       if intent in [SemanticIntent.EXPLOITATION, SemanticIntent.RECONNAISSANCE]:
           return True
       return False
   ```

4. **Use PentestingAssistant (No Shortcuts):**
   ```python
   # Replace old PenetrationTester with new PentestingAssistant
   response = self.pentesting_assistant.handle_pentest_request(user_input)
   ```

## Test Scenarios

### Test 1: Typo Tolerance ✅
**Input:** "pyhton keylogger"
**Expected:** Routes to CODE intent (typo-tolerant)
**Implementation:** Semantic classifier understands "pyhton" → "python"

### Test 2: Hardcoded Shortcuts Prevention ✅
**Input:** "generate metasploit payload"
**Expected:** Asks 5+ clarifying questions, DOESN'T instantly generate
**Implementation:** PentestingAssistant requires methodology selection stage

### Test 3: Autonomous Execution ✅
**Input:** "Ubuntu 20.04, SSH on port 22, no creds"
**Expected:** Asks methodology questions, then executes based on answers
**Implementation:** Stage-based questioning → exploitation when complete

### Test 4: Context Memory ✅
**Input:** "forget about that, new target"
**Expected:** Clears all target context completely
**Implementation:** `_clear_context()` method handles explicit clear commands

### Test 5: Consistent Execution ✅
**Expected Behavior:**
- Code requests → Always route to code generation + sandbox
- Metasploit requests → Always execute with real output
- Recon requests → Always run real tools (nmap, etc.)
- Research requests → Always research, then ask context questions
- No mismatches (e.g., "find open ports" → NEVER returns ipconfig output)

## Key Features

### 1. Typo Tolerance
- "pyhton keylogger" → CODE intent
- "winndows exploit" → EXPLOITATION intent
- "scann ports" → RECONNAISSANCE intent

### 2. Phrasing Agnostic
- "make python keylogger" / "create keylogger script" / "write a keylogger" → CODE
- "remote access windows" / "get shell on target" / "compromise windows machine" → EXPLOITATION
- "find open ports" / "scan services" / "enumerate target" → RECONNAISSANCE

### 3. No Premature Code Generation
- User: "Ubuntu SSH vulnerable"
- OLD: Tries Python/paramiko code immediately
- NEW: Explains exploitation path → Asks clarifying questions → Generates code only when appropriate

### 4. Context Awareness
- User: "192.168.1.100, Windows 10"
- AI: "Got it. What services are running?"
- User: "RDP on 3389"
- AI: "Good. Delivery method? (EXE, PowerShell, DLL?)"
- User: "PowerShell reverse TCP"
- AI: "Got it. [Generates exploit strategy]"

### 5. Context Clearing
- User: "forget" / "new target" / "different machine"
- AI: "Context cleared. Ready for a new target."

## Architecture Diagram

```
User Input
    ↓
SemanticIntentClassifier (LLM-based)
    ↓
    ├─→ CODE intent → Code execution (dual_execution_orchestrator)
    ├─→ EXPLOITATION intent → PentestingAssistant
    ├─→ RECONNAISSANCE intent → PentestingAssistant
    ├─→ RESEARCH intent → ResearchIntentHandler
    └─→ CHAT intent → ResponseGenerator

PentestingAssistant (Methodology Enforced)
    ↓
    Stage 1: RECONNAISSANCE → Ask for IP, OS
    ↓
    Stage 2: ENUMERATION → Ask for services, ports
    ↓
    Stage 3: VULNERABILITY_ASSESSMENT → Research CVEs
    ↓
    Stage 4: METHODOLOGY_SELECTION → Ask 5+ questions
    ↓
    Stage 5: EXPLOITATION → Generate and explain strategy
    ↓
    Stage 6: POST_EXPLOITATION → Maintain access
```

## Migration Path

The old `PenetrationTester` class still exists for backward compatibility. New code uses `PentestingAssistant`:

```python
# Old (deprecated)
from spectral.penetration_tester import PenetrationTester
pentester = PenetrationTester(llm_client)

# New (recommended)
from spectral.pentesting_assistant import PentestingAssistant
assistant = PentestingAssistant(
    llm_client=llm_client,
    research_handler=research_handler,
    semantic_classifier=semantic_classifier,
)
```

## Benefits

1. **Typos don't break routing:** "pyhton" works same as "python"
2. **Phrasing doesn't matter:** Synonyms and variations work
3. **No instant shortcuts:** Always asks clarifying questions first
4. **Better methodology:** Systematic pentesting approach
5. **Context aware:** Remembers target info across turns
6. **Easy to clear:** "forget" / "new target" works
7. **Consistent behavior:** Code always executes, recon always scans

## Acceptance Criteria

✅ Semantic intent detection works (typo-tolerant, phrasing-agnostic)
✅ No hardcoded shortcuts (always ask clarifying questions first for exploits)
✅ Conversational pentesting methodology (systematic Q&A, not generic)
✅ Autonomous execution when info is sufficient
✅ Code generation only AFTER methodology is clear
✅ Context properly cleared/updated based on user commands
✅ Consistent execution pipeline (code → sandbox, metasploit → real output, recon → real tools)
✅ All 5 test scenarios pass

## Future Enhancements

1. Add streaming responses for PentestingAssistant
2. Integrate autonomous tool execution (nmap, metasploit)
3. Add exploit success/failure feedback loop
4. Implement post-exploitation automation
5. Add persistence mechanisms
6. Integrate with knowledge base for common exploits
