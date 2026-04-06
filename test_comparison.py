#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comparison Script: Baseline Chatbot vs ReAct Agent
Runs the same questions through both systems and compares results
"""

import os
import sys
import io
import json
from datetime import datetime
from dotenv import load_dotenv

# Force UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.gemini_provider import GeminiProvider
from src.agent.agent import ReActAgent
from src.tools.expense_tools import EXPENSE_TOOLS_MAP

def load_questions(file_path: str) -> list:
    """Load questions from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        questions = [line.strip() for line in f.readlines() if line.strip()]
    return questions

def run_baseline(llm, question: str) -> str:
    """Run baseline chatbot (simple LLM without tools)"""
    try:
        result = llm.generate(question)
        if isinstance(result, dict):
            return result.get('content', str(result))
        return str(result)
    except Exception as e:
        return f"[ERROR] {str(e)}"

def run_agent(agent, question: str) -> str:
    """Run ReAct Agent with tools"""
    try:
        result = agent.run(question)
        return result
    except Exception as e:
        return f"[ERROR] {str(e)}"

def save_report(results: list, output_file: str):
    """Save comparison results to file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write(f"CHATBOT COMPARISON REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"{'=' * 100}\n")
            f.write(f"QUESTION {i}\n")
            f.write(f"{'=' * 100}\n\n")
            
            f.write(f"📝 QUESTION:\n{result['question']}\n\n")
            
            f.write("-" * 100 + "\n")
            f.write("🤖 BASELINE CHATBOT (Simple LLM - No Tools):\n")
            f.write("-" * 100 + "\n")
            f.write(f"{result['baseline']}\n\n")
            
            f.write("-" * 100 + "\n")
            f.write("🧠 REACT AGENT (With Tools - Smart Reasoning):\n")
            f.write("-" * 100 + "\n")
            f.write(f"{result['agent']}\n\n")
            
            f.write("\n")

def main():
    load_dotenv()
    
    print("\n" + "=" * 100)
    print("🚀 CHATBOT COMPARISON: Baseline vs ReAct Agent")
    print("=" * 100 + "\n")
    
    # Load questions
    questions = load_questions("questions.txt")
    print(f"📚 Loaded {len(questions)} questions from questions.txt\n")
    
    # Initialize providers
    provider_name = os.getenv("DEFAULT_PROVIDER", "gemini").lower()
    print(f"🔧 Using provider: {provider_name}\n")
    
    try:
        if provider_name == "openai":
            from src.core.openai_provider import OpenAIProvider
            llm = OpenAIProvider(model_name="gpt-3.5-turbo")
        else:
            llm = GeminiProvider(model_name="gemini-2.5-flash-lite")
    except Exception as e:
        print(f"❌ Error initializing LLM: {e}")
        return
    
    # Create agent
    agent = ReActAgent(llm=llm, tools=EXPENSE_TOOLS_MAP, max_steps=6)
    
    results = []
    
    # Run comparison
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Running comparison for question {i}...")
        print(f"Question: {question[:60]}...")
        
        # Run baseline
        print(f"  → Running baseline chatbot...", end="", flush=True)
        baseline_result = run_baseline(llm, question)
        print(" ✓")
        
        # Run agent
        print(f"  → Running ReAct agent...", end="", flush=True)
        agent_result = run_agent(agent, question)
        print(" ✓")
        
        results.append({
            "question": question,
            "baseline": baseline_result,
            "agent": agent_result
        })
    
    # Save report
    output_file = f"report/comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    os.makedirs("report", exist_ok=True)
    save_report(results, output_file)
    
    print("\n" + "=" * 100)
    print(f"✅ Comparison completed! Report saved to: {output_file}")
    print("=" * 100 + "\n")
    
    # Print summary
    print("\n📊 SUMMARY:\n")
    for i, result in enumerate(results, 1):
        print(f"Q{i}: {result['question'][:60]}...")
        print(f"  Baseline length: {len(result['baseline'])} chars")
        print(f"  Agent length: {len(result['agent'])} chars")
        print()

if __name__ == "__main__":
    main()
