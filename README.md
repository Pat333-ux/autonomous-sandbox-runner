# autonomous-sandbox-runner
Whenever an autonomous refactoring PR or swarm agent proposes code changes, this repository checks them out in an isolated workspace, runs the test suite, and—if tests fail—automatically loops an LLM agent to patch the code until it passes 100% before Governing Officer Tarwater ever has to look at it.
