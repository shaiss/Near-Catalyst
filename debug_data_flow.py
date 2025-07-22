#!/usr/bin/env python3
"""
Debug Data Flow Script for NEAR Partnership Analysis

This script helps diagnose data flow issues between agents and database storage.
It analyzes the database for common problems and provides detailed debugging information.

Usage:
    python debug_data_flow.py                    # List all issues
    python debug_data_flow.py --project NAME     # Debug specific project
    python debug_data_flow.py --fix-empty        # Attempt to fix empty analyses
"""

import argparse
import json
from database import DatabaseManager
from agents import DIAGNOSTIC_QUESTIONS


def main():
    """Main debugging interface."""
    parser = argparse.ArgumentParser(description='Debug NEAR Partnership Analysis data flow issues')
    parser.add_argument('--project', type=str, help='Debug specific project by name')
    parser.add_argument('--list-issues', action='store_true', help='List all problematic projects')
    parser.add_argument('--summary', action='store_true', help='Show summary of database issues')
    args = parser.parse_args()
    
    db_manager = DatabaseManager()
    
    if args.project:
        debug_specific_project(db_manager, args.project)
    elif args.list_issues:
        list_all_issues(db_manager)
    elif args.summary:
        show_summary(db_manager)
    else:
        show_overview(db_manager)


def debug_specific_project(db_manager, project_name):
    """Debug a specific project in detail."""
    print(f"🔍 Debugging project: {project_name}")
    print("=" * 60)
    
    debug_info = db_manager.debug_project_data(project_name)
    
    # General research status
    print("📊 GENERAL RESEARCH:")
    if debug_info["general_research"]:
        gr = debug_info["general_research"]
        print(f"  ✅ Success: {gr['success']}")
        print(f"  📄 Data length: {gr['data_length']:,} chars")
        print(f"  🔗 Sources: {gr['sources_count']}")
        if gr['error']:
            print(f"  ❌ Error: {gr['error']}")
    else:
        print("  ❌ No general research found")
    
    # Deep research status
    print("\n🔬 DEEP RESEARCH:")
    if debug_info["deep_research"]:
        dr = debug_info["deep_research"]
        print(f"  ✅ Success: {dr['success']}")
        print(f"  🚀 Enabled: {dr['enabled']}")
        print(f"  📄 Data length: {dr['data_length']:,} chars")
        print(f"  🔗 Sources: {dr['sources_count']}")
        print(f"  ⚙️ Tool calls: {dr['tool_calls']}")
        print(f"  ⏱️ Elapsed time: {dr['elapsed_time']:.1f}s")
        print(f"  📝 Enhanced prompt length: {dr['enhanced_prompt_length']:,} chars")
        if dr['error']:
            print(f"  ❌ Error: {dr['error']}")
    else:
        print("  ⚠️ No deep research data")
    
    # Question analyses status
    print("\n❓ QUESTION ANALYSES:")
    if debug_info["question_analyses"]:
        total_score = 0
        for q in debug_info["question_analyses"]:
            question_text = get_question_text(q["question_id"])
            status = "✅" if q["has_analysis"] else "❌"
            score_display = f"{q['score']:+d}" if q['score'] is not None else "NULL"
            
            print(f"  {status} Q{q['question_id']}: {question_text}")
            print(f"      Research: {q['research_data_length']:,} chars")
            print(f"      Analysis: {q['analysis_length']:,} chars")
            print(f"      Score: {score_display} | Confidence: {q['confidence']}")
            
            if q["analysis_preview"]:
                print(f"      Preview: {q['analysis_preview'][:80]}...")
            
            if q['score'] is not None:
                total_score += q['score']
        
        print(f"\n  📊 Total Score: {total_score}/6")
    else:
        print("  ❌ No question analyses found")
    
    # Final summary status
    print("\n📋 FINAL SUMMARY:")
    if debug_info["final_summary"]:
        fs = debug_info["final_summary"]
        print(f"  ✅ Success: {fs['success']}")
        print(f"  📊 Total Score: {fs['total_score']}/6")
        print(f"  🎯 Recommendation: {fs['recommendation']}")
        print(f"  📄 Summary length: {fs['summary_length']:,} chars")
        if fs['error']:
            print(f"  ❌ Error: {fs['error']}")
    else:
        print("  ❌ No final summary found")
    
    # Issues summary
    if debug_info["issues"]:
        print("\n🚨 IDENTIFIED ISSUES:")
        for issue in debug_info["issues"]:
            print(f"  • {issue}")
    else:
        print("\n✅ No issues detected")


def list_all_issues(db_manager):
    """List all problematic projects."""
    print("🚨 PROBLEMATIC PROJECTS ANALYSIS")
    print("=" * 60)
    
    issues = db_manager.list_problematic_projects()
    
    # Empty analyses
    if issues["empty_analyses"]:
        print(f"\n❌ PROJECTS WITH EMPTY ANALYSES ({len(issues['empty_analyses'])}):")
        for project in issues["empty_analyses"]:
            print(f"  • {project}")
    
    # Failed summaries
    if issues["failed_summaries"]:
        print(f"\n💥 PROJECTS WITH FAILED SUMMARIES ({len(issues['failed_summaries'])}):")
        for project, error in issues["failed_summaries"]:
            print(f"  • {project}: {error}")
    
    # Missing deep research
    if issues["missing_deep_research"]:
        print(f"\n🔬 PROJECTS WITHOUT DEEP RESEARCH ({len(issues['missing_deep_research'])}):")
        for project in issues["missing_deep_research"][:10]:  # Show first 10
            print(f"  • {project}")
        if len(issues["missing_deep_research"]) > 10:
            print(f"  ... and {len(issues['missing_deep_research']) - 10} more")
    
    # Zero scores (potential parsing issues)
    if issues["zero_scores"]:
        print(f"\n0️⃣ PROJECTS WITH ALL ZERO SCORES ({len(issues['zero_scores'])}):")
        for project, question_count in issues["zero_scores"]:
            print(f"  • {project} ({question_count} questions)")


def show_summary(db_manager):
    """Show high-level summary of database status."""
    print("📊 DATABASE SUMMARY")
    print("=" * 60)
    
    projects = db_manager.list_projects()
    issues = db_manager.list_problematic_projects()
    
    print(f"Total projects: {len(projects)}")
    print(f"Projects with deep research: {sum(1 for p in projects if p['deep_research_performed'])}")
    print(f"Projects with empty analyses: {len(issues['empty_analyses'])}")
    print(f"Projects with failed summaries: {len(issues['failed_summaries'])}")
    print(f"Projects with zero scores: {len(issues['zero_scores'])}")
    
    # Score distribution
    scores = [p['score'] for p in projects if p['score'] is not None]
    if scores:
        print(f"\nScore distribution:")
        print(f"  Min: {min(scores)}")
        print(f"  Max: {max(scores)}")
        print(f"  Avg: {sum(scores) / len(scores):.1f}")


def show_overview(db_manager):
    """Show overview of debugging options."""
    print("🔍 NEAR Partnership Analysis - Data Flow Debugger")
    print("=" * 60)
    print("Available debugging options:")
    print()
    print("  --project NAME     Debug specific project in detail")
    print("  --list-issues      List all projects with data issues")
    print("  --summary          Show high-level database summary")
    print()
    print("Examples:")
    print("  python debug_data_flow.py --project 'MyProject'")
    print("  python debug_data_flow.py --list-issues")
    print("  python debug_data_flow.py --summary")
    print()
    
    # Quick summary
    show_summary(db_manager)


def get_question_text(question_id):
    """Get question text by ID."""
    for q in DIAGNOSTIC_QUESTIONS:
        if q['id'] == question_id:
            return q['question']
    return f"Question {question_id}"


if __name__ == "__main__":
    main() 