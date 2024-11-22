import importlib

parent_testcase_id = "63229"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for HSX 3.X node refresh
    The Implementation is Inherited from TestCase 63229"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "69126"
        self.name = "Test Case for node refresh HSX 3.X"