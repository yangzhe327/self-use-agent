#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Frontend Auto-modification Agent Main Entry File
"""

import os
import sys
from agents.application import UIProjectAgent
from exceptions.project_exceptions import ProjectBaseException

def main():
    try:
        project_path = input("Please enter your UI project root directory path: ").strip()
        if not os.path.isdir(project_path):
            print("Project path does not exist!")
            return
        
        agent = UIProjectAgent(project_path=project_path)
        
        # Test if project can be run directly
        print("Testing if project can be run...")
        test_run_success, test_run_message = agent.check_project_runnable()
        if test_run_success:
            print(f"Project test run successful: {test_run_message}")
            run_choice = input("Do you want to run the project? (y/n): ").strip().lower()
            if run_choice == 'y':
                agent.run_project()
        else:
            print(f"Project test run failed: {test_run_message}")
            # Let AI analyze the specific reason
            analysis_result = agent.analyze_failure_reason(test_run_message)
            print(f"Analysis result: {analysis_result}")
            
            # Decide next action based on AI analysis
            if "dependency issue" in analysis_result or "dependency" in analysis_result or "node_modules" in test_run_message:
                install_choice = input("Do you want to install project dependencies? (y/n): ").strip().lower()
                if install_choice == 'y':
                    if agent.install_dependencies():
                        # Test run again after installing dependencies
                        test_run_success, test_run_message = agent.check_project_runnable()
                        if test_run_success:
                            run_choice = input("Dependencies installed successfully, do you want to run the project? (y/n): ").strip().lower()
                            if run_choice == 'y':
                                agent.run_project()
                        else:
                            print(f"Project still failed to start after dependency installation: {test_run_message}")
                            analysis_result = agent.analyze_failure_reason(test_run_message)
                            print(f"Analysis result: {analysis_result}")
            else:
                # If it's not a dependency issue, AI has already provided detailed explanation, user can decide whether to continue
                pass
        
        # Then analyze the project and enter modification mode
        print("\nEnter your new requirements, 'exit' to quit")
        while True:
            user_input = input("Your requirement: ").strip()
            if user_input.lower() == "exit":
                # Stop running project
                agent.stop_project()
                break
            agent.modify_project(user_input)
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        sys.exit(0)
    except ProjectBaseException as e:
        print(f"Project error: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"Program runtime error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()