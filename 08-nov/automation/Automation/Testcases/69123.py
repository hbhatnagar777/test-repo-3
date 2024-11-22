import importlib

parent_testcase_id = "60717"
parent_test_case_module = importlib.import_module(parent_testcase_id)

class TestCase(parent_test_case_module.TestCase):
    """Hyperscale test class for HSX 3.X platform upgrade via command line
    The Implementation is Inherited from TestCase 60717"""
    
    def __init__(self, *args, **kwargs):
        """Initialization function"""
        super().__init__(*args, **kwargs)
        self.id = "69123"
        self.name = "Test Case for command line platform upgrade HSX 3.X"