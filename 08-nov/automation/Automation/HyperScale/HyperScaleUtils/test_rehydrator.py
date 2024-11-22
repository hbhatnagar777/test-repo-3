from pathlib import Path
import random
import shutil
from unittest import TestCase

from HyperScale.HyperScaleUtils.rehydrator import Rehydrator

class TestRehydrator(TestCase):
    rehydrator_path = dir = Path("rehydrator")

    def setUp(self):
        dir = TestRehydrator.rehydrator_path
        if dir.exists() and dir.is_dir():
            shutil.rmtree(dir)
    
    def test_simple_bucket(self):
        rd_context = "test"
        value_initial = "45"
        rd_initial = Rehydrator(rd_context)
        bucket_initial = rd_initial.bucket("bucket")
        bucket_initial.set(value_initial)
        
        # now we simulate a new code execution context
        rd_final = Rehydrator(rd_context)
        bucket_final = rd_final.bucket("bucket")
        value = bucket_final.get()
        
        self.assertEqual(value_initial, value)
    
    def test_bucket_with_multiple_data_types(self):
        rd_context = "test"
        value_num_initial = 53
        value_float_initial = 110.72
        value_array_initial = [value_num_initial, value_float_initial]
        value_dict_initial = {"array": value_array_initial, "num": value_num_initial, "float":value_float_initial}

        rd_initial = Rehydrator(rd_context)
        bucket_num_initial = rd_initial.bucket("num")
        bucket_float_initial = rd_initial.bucket("float")
        bucket_array_initial = rd_initial.bucket("array")
        bucket_dict_initial = rd_initial.bucket("dict")

        bucket_num_initial.set(value_num_initial)
        bucket_float_initial.set(value_float_initial)
        bucket_array_initial.set(value_array_initial)
        bucket_dict_initial.set(value_dict_initial)
        
        # now we simulate a new code execution context
        rd_final = Rehydrator(rd_context)
        bucket_num_final = rd_final.bucket("num")
        bucket_float_final = rd_final.bucket("float")
        bucket_array_final = rd_final.bucket("array")
        bucket_dict_final = rd_final.bucket("dict")
        
        value_num_final = bucket_num_final.get()
        value_float_final = bucket_float_final.get()
        value_array_final = bucket_array_final.get()
        value_dict_final = bucket_dict_final.get()
        
        self.assertEqual(value_num_initial, value_num_final)
        self.assertEqual(value_float_initial, value_float_final)
        self.assertEqual(value_array_initial, value_array_final)
        self.assertEqual(value_dict_initial, value_dict_final)
    
    def test_rehydrator_cleanup(self):
        dir = TestRehydrator.rehydrator_path
        if dir.exists():
            self.fail("rehydrator folder shouldn't exist at the start of this TC")

        rd_context = "test"
        rd_initial = Rehydrator(rd_context)
        if dir.exists():
            self.fail("rehydrator folder shouldn't exist if an instance of rehydrator is created")
        bucket = rd_initial.bucket("num")
        bucket.set(52)
        if not dir.exists():
            self.fail("rehydator folder should get created when setting a value")
        db_path = dir / f"rehydrator_{rd_context}.pickle"
        if not db_path.exists():
            self.fail(f"{db_path} not found")
        
        rd_initial.cleanup()
        
        if db_path.exists():
            self.fail(f"{db_path} shouldn't exist after cleanup is called")
    
    def test_multiple_rehydrators(self):
        num_rehydrators = 100
        rd_contexts = [f"test{i}" for i in range(num_rehydrators)]
        values_initial = [random.randint(0, num_rehydrators*100) for _ in range(num_rehydrators)]
        
        rds_initial = [Rehydrator(context) for context in rd_contexts]
        buckets_initial = [rd.bucket("num") for rd in rds_initial]
        for bucket, value in zip(buckets_initial, values_initial):
            bucket.set(value)
            
        dir = TestRehydrator.rehydrator_path
        self.assertEqual(len(list(dir.iterdir())), num_rehydrators)
        
        # now we simulate a new code execution context
        rds_final = [Rehydrator(context) for context in rd_contexts]
        buckets_final = [rd.bucket("num") for rd in rds_final]
        for bucket, value in zip(buckets_final, values_initial):
            self.assertEqual(value, bucket.get())
        

# run with
# python -m unittest .\HyperScale\HyperScaleUtils\test_rehydrator.py