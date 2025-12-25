OS Context Intelligence Layer (Experimental)
An experimental project that explores how an AI system can understand operating-system context and generate safe, human-readable action proposals without executing them.
This is not an OS, and not an autonomous agent.
It is a reasoning layer that sits on top of the OS.
🚀 Idea
Modern AI tools lack awareness of what the user is doing at the system level.
This project experiments with:
Reading lightweight OS context (active window, process, activity)
Interpreting that context using an LLM
Generating suggested actions, not executing them
Focus is on reasoning, safety, and reversibility, not automation.
🧩 What It Does
Collects basic OS context
(process name, window title, timestamps)
Classifies user activity (coding, browsing, idle, etc.)
Sends context to an LLM for reasoning
Generates action proposals in structured JSON
Requires explicit user approval for any future execution layer
