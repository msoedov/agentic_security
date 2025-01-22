class OperatorToolBox:
    def __init__(self, llm_spec, datasets):
        self.llm_spec = llm_spec
        self.datasets = datasets

    def get_spec(self):
        return self.llm_spec

    def get_datasets(self):
        return self.datasets

    def validate(self):
        # Validate the tool box
        pass

    def stop(self):
        # Stop the tool box
        pass

    def run(self):
        # Run the tool box
        pass

    def get_results(self):
        # Get the results
        pass

    def get_failures(self):
        # Handle failure
        pass
