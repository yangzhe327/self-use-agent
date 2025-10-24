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
        
        # Ask user if they want to run the project first
        run_choice = input("Do you want to run the project? (y/n): ").strip().lower()
        if run_choice == 'y':
            try:
                agent.run_project()
                print("Project started successfully!")
            except Exception as e:
                print(f"Failed to start project: {str(e)}")
                # Let AI analyze the specific reason
                analysis_result = agent.analyze_failure_reason(str(e))
                print(f"Analysis result: {analysis_result}")
                
                # Decide next action based on AI analysis
                if "dependency issue" in analysis_result or "dependency" in analysis_result:
                    install_choice = input("Do you want to install project dependencies? (y/n): ").strip().lower()
                    if install_choice == 'y':
                        if agent.install_dependencies():
                            print("Dependencies installed successfully, trying to run project again...")
                            try:
                                agent.run_project()
                                print("Project started successfully!")
                            except Exception as e:
                                print(f"Project still failed to start after dependency installation: {str(e)}")
                                analysis_result = agent.analyze_failure_reason(str(e))
                                print(f"Analysis result: {analysis_result}")
                else:
                    # If it's not a dependency issue, AI has already provided detailed explanation
                    pass
        else:
            print("Skipping project run step.")
        
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