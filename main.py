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