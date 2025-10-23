#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Frontend Auto-modification Agent Main Entry File
"""

import os
import sys
from agents.application import UIProjectAgent
from exceptions.project_exceptions import ProjectBaseException


if __name__ == '__main__':
    try:
        project_path = input("Please enter your UI project root directory path: ").strip()
        if not os.path.isdir(project_path):
            print("Project path does not exist!")
            sys.exit(1)
        
        agent = UIProjectAgent(project_path=project_path)
        
        # Actually test run the project to see if all dependencies are properly installed
        test_runnable, test_message = agent.test_run_project()
        if not test_runnable:
            print(f"Project test run failed: {test_message}")
            # Let AI analyze the specific reason
            analysis_result = agent.analyze_failure_reason(test_message)
            print(f"Analysis result: {analysis_result}")
            
            # Decide next action based on AI analysis
            if "dependency issue" in analysis_result or "dependency" in analysis_result:
                install_choice = input("Do you want to install project dependencies? (y/n): ").strip().lower()
                if install_choice == 'y':
                    if agent.install_dependencies():
                        run_choice = input("Dependencies installed successfully, do you want to run the project? (y/n): ").strip().lower()
                        if run_choice == 'y':
                            agent.run_project()
            else:
                # If it's not a dependency issue, AI has already provided detailed explanation, user can decide whether to continue
                run_choice = input("Do you still want to try running the project? (y/n): ").strip().lower()
                if run_choice == 'y':
                    agent.run_project()
        else:
            print(f"Project test run successful: {test_message}")
            run_choice = input("Do you want to run the project? (y/n): ").strip().lower()
            if run_choice == 'y':
                agent.run_project()
        
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