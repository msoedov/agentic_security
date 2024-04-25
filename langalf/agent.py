"""Quality Assurance Testing Agent.

The goal of this agent is to perform quality assurance testing on a product or service.

Agents:
- Test Case Generator
- Test Executor
- Test Report Writer

Tasks:
- Generate test cases
- Execute test cases
- Write test report
"""

import json
import os

from crewai import Agent, Crew, Process, Task
from langchain.schema import AgentFinish
from langchain_groq import ChatGroq

agent_outputs = []


def print_agent_output(agent_output, agent_name="Generic Agent", state=[0]):
    state[0] += 1
    call_number = state[0]
    with open("agent_logs.txt", "a") as log_file:
        if isinstance(agent_output, str):
            try:
                agent_output = json.loads(agent_output)
            except json.JSONDecodeError:
                pass

        if isinstance(agent_output, list) and all(
            isinstance(item, tuple) for item in agent_output
        ):
            print(
                f"-{call_number}----Dict------------------------------------------",
                file=log_file,
            )
            for action, description in agent_output:
                print(f"Agent Name: {agent_name}", file=log_file)
                print(f"Tool used: {getattr(action, 'tool', 'Unknown')}", file=log_file)
                print(
                    f"Tool input: {getattr(action, 'tool_input', 'Unknown')}",
                    file=log_file,
                )
                print(f"Action log: {getattr(action, 'log', 'Unknown')}", file=log_file)
                print(f"Description: {description}", file=log_file)
                print(
                    "--------------------------------------------------", file=log_file
                )

        elif isinstance(agent_output, AgentFinish):
            print(
                f"-{call_number}----AgentFinish---------------------------------------",
                file=log_file,
            )
            print(f"Agent Name: {agent_name}", file=log_file)
            agent_outputs.append(agent_output)
            output = agent_output.return_values
            print(f"AgentFinish Output: {output['output']}", file=log_file)
            print("--------------------------------------------------", file=log_file)

        else:
            print(f"-{call_number}-Unknown format of agent_output:", file=log_file)
            print(type(agent_output), file=log_file)
            print(agent_output, file=log_file)


QA_TESTING_LLM = ChatGroq(
    model="llama3-70b-8192", groq_api_key=os.getenv("GROQ_API_KEY")
)


class QATestingAgents:
    def make_test_case_generator(self):
        return Agent(
            role="Test Case Generator",
            goal="""Generate comprehensive test cases for the given product or service based on the provided requirements and specifications.""",
            backstory="""You are an experienced quality assurance professional responsible for creating thorough test cases to ensure the product or service meets all requirements and functions as expected.""",
            llm=QA_TESTING_LLM,
            verbose=True,
            allow_delegation=False,
            max_iter=5,
            memory=True,
            step_callback=lambda x: print_agent_output(x, "Test Case Generator"),
        )

    def make_test_executor(self):
        return Agent(
            role="Test Executor",
            goal="""Execute the generated test cases and record the results.""",
            backstory="""You are responsible for running all the test cases and documenting the outcomes, including any issues or failures encountered during testing.""",
            llm=QA_TESTING_LLM,
            verbose=True,
            max_iter=5,
            allow_delegation=False,
            memory=True,
            tools=[],  # Add any tools needed for test execution
            step_callback=lambda x: print_agent_output(x, "Test Executor"),
        )

    def make_test_report_writer(self):
        return Agent(
            role="Test Report Writer",
            goal="""Analyze the test results and generate a comprehensive test report detailing the findings, issues, and recommendations.""",
            backstory="""You are tasked with creating a detailed test report that summarizes the testing process, highlights any defects or issues discovered, and provides recommendations for addressing them.""",
            llm=QA_TESTING_LLM,
            verbose=True,
            allow_delegation=False,
            max_iter=5,
            memory=True,
            step_callback=lambda x: print_agent_output(x, "Test Report Writer"),
        )


class QATestingTasks:
    def generate_test_cases(self, product_requirements):
        return Task(
            description=f"""Based on the provided product requirements and specifications, generate a comprehensive set of test cases to ensure the product meets all criteria and functions as expected.

            Product Requirements:
            {product_requirements}

            Expected Output:
            A list of detailed test cases covering various scenarios, edge cases, and user interactions.
            """,
            expected_output="""A list of test cases with the following format:

            1. Test Case Description
               - Steps to reproduce
               - Expected result

            2. Test Case Description
               - Steps to reproduce
               - Expected result

            ...
            """,
            output_file="test_cases.txt",
            agent=test_case_generator,
        )

    def execute_test_cases(self, test_cases):
        return Task(
            description=f"""Execute the provided test cases and document the results.

            Test Cases:
            {test_cases}

            Expected Output:
            A report detailing the outcome of each test case, including any issues or failures encountered.
            """,
            expected_output="""A report with the following format:

            1. Test Case Description
               - Result: Pass/Fail
               - Observations/Issues (if any)

            2. Test Case Description
               - Result: Pass/Fail
               - Observations/Issues (if any)

            ...
            """,
            output_file="test_execution_report.txt",
            agent=test_executor,
        )

    def write_test_report(self, test_execution_report):
        return Task(
            description=f"""Analyze the test execution report and generate a comprehensive test report detailing the findings, issues, and recommendations.

            Test Execution Report:
            {test_execution_report}

            Expected Output:
            A detailed test report summarizing the testing process, highlighting any defects or issues discovered, and providing recommendations for addressing them.
            """,
            expected_output="""A test report with the following sections:

            1. Executive Summary
            2. Test Scope and Approach
            3. Test Results Summary
            4. Detailed Test Findings
            5. Recommendations
            6. Conclusion
            """,
            output_file="test_report.txt",
            agent=test_report_writer,
        )


"""## Instantiate Agents and Tasks"""

# Instantiate agents
agents = QATestingAgents()
test_case_generator = agents.make_test_case_generator()
test_executor = agents.make_test_executor()
test_report_writer = agents.make_test_report_writer()

# Instantiate tasks
tasks = QATestingTasks()
product_requirements = """
    • The product is a mobile application for managing personal finances.
    • Users should be able to create and manage multiple accounts (e.g., checking, savings, credit cards).
    • Users can record income and expenses, categorize transactions, and set budgets.
    • The app should provide detailed reports and visualizations of spending and income over time.
    • Users can set reminders for upcoming bills and recurring payments.
    • The app should support integration with bank accounts for automatic transaction import.
    • User data must be securely stored and encrypted.
    • The app should be available for both iOS and Android platforms.
"""

generate_test_cases = tasks.generate_test_cases(product_requirements)
execute_test_cases = tasks.execute_test_cases(generate_test_cases)
write_test_report = tasks.write_test_report(execute_test_cases)


crew = Crew(
    agents=[test_case_generator, test_executor, test_report_writer],
    tasks=[generate_test_cases, execute_test_cases, write_test_report],
    verbose=2,
    process=Process.sequential,
    full_output=True,
    share_crew=False,
    step_callback=lambda x: print_agent_output(x, "QA Testing Crew"),
)

# Kick off the crew's work
results = crew.kickoff()

# Print the results
print("Crew Work Results:")
print(results)

# Print usage metrics
print(crew.usage_metrics)
