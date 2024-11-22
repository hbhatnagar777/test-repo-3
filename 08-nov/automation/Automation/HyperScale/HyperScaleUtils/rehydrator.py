from datetime import datetime
from pathlib import Path
import pickle

class Rehydrator:
    
    class Bucket:
        def __init__(self, parent_store, name):
            self.parent_store:Rehydrator = parent_store
            self.name = name
            self.value = None
        
        def set(self, value):
            self.parent_store._save(self.name, value)
            self.value = value
        
        def get(self, default=None):
            if not self.parent_store._key_exists(self.name):
                self.parent_store._save(self.name, default)
            self.value = self.parent_store._load(self.name)
            return self.value
        
        def exists(self):
            return self.parent_store._key_exists(self.name)

    def __init__(self, store_name, store_dir='rehydrator'):
        self.store_name = store_name
        self.store_path = Path(store_dir) / f"rehydrator_{store_name}.pickle"
    
    def cleanup(self):
        if self._store_exists():
            self.store_path.unlink()

    def store_exists(self):
        return self._store_exists()
    
    def bucket(self, name):
        return Rehydrator.Bucket(self, name)
    
    def _save(self, name, value):
        if not self._store_exists():
            db = {}
        else:
            db = self._load_keys()
        db[name] = value
        self._save_keys(db)
    
    def _load_keys(self):
        with open(self.store_path, 'rb') as file_obj:
            db = pickle.load(file_obj)
            return db
    
    def _save_keys(self, db):
        if not self._store_exists():
            self.store_path.parent.mkdir(exist_ok=True, parents=True)
        with open(self.store_path, 'wb') as file_obj:
                pickle.dump(db, file_obj)
        
    def _load(self, name):
        db = self._load_keys()
        return db[name]
    
    def _store_exists(self):
        return self.store_path.is_file()
    
    def _key_exists(self, name):
        if not self._store_exists():
            return False
        db = self._load_keys()
        return name in db
    
    def __str__(self):
        if not self._store_exists():
            return f"{self.store_path} doesn't exist"
        db = self._load_keys()
        return str(db)


if __name__ == '__main__':
    '''
    Example scenarios
    1. Check if previous run was cleaned up, if not, then run it
    Run 1:
    def setup():
        ...
        self.rehydrator = Rehydrator(self.id)
        self.cleaned_up = self.rehydrator.bucket("cleaned_up")
    
    def cleanup():
        ...
        self.cleaned_up.set(True)
    
    Run 2:
        def run():
            if not self.cleaned_up.get(False):  #"False" indicates default value
                cleanup()
                
        
    2. Pass information across test cases
    Test case: 70001:
    def setup():
        self.local_rehydrator = Rehydrator(70001)
        self.local_bucket = self.local_rehydrator.bucket('local_bucket')
        ...
        
        self.global_rehydrator = Rehydrator(testset_id)
        self.last_result = self.global_rehydrator.bucket('last_result')
        
    def tear_down():
        self.last_result.set({"id": 70001, "duration": time_taken, "status": self.status})
    
    Test case: 70002:
    def setup():
        self.local_rehydrator = Rehydrator(70002)
        self.local_bucket = self.local_rehydrator.bucket('local_bucket')
        ...
        
        self.global_rehydrator = Rehydrator(testset_id)
        self.last_result = self.global_rehydrator.bucket('last_result')
    
    def run():
        if self.last_result.exists():
            self.log.info(self.last_result.get()) # {"id": 70001, "duration": 5000, "status": "SUCCESS"}
        
    '''
    # this playground automatically switches between the Day and Night cycle, 
    # remembering how many days have passed, thanks to rehydrator
    # it starts with Day -> Night -> Day -> Night -> ... 
    # 1 day = Day + Night
    # give it a try! run this code multiple times and see the difference in output
    rehydrator_controls = Rehydrator('playground-controls')
    is_day = rehydrator_controls.bucket('is_day')
    total_days = rehydrator_controls.bucket('total_days')
    
    if is_day.get(True):
        # Day
        print("Day time. Yay!")
        rehydrator = Rehydrator('playground')
        print(rehydrator)
        wake_up_time = rehydrator.bucket("wake_up_time")
        wake_up_time.set(str(datetime.now()))
        print(rehydrator)
        sleeping_time = rehydrator.bucket("sleeping_time")
        if sleeping_time.get() is not None:
            print(f"I slept at {sleeping_time.get()}")
    else:
        # Night
        print("Night time. ZzzZZz")
        rehydrator = Rehydrator('playground')
        print(rehydrator)
        sleeping_time = rehydrator.bucket("sleeping_time")
        sleeping_time.set(str(datetime.now()))
        print(rehydrator)
        wake_up_time = rehydrator.bucket("wake_up_time")
        print(f"I woke up at {wake_up_time.get()}")
        
    is_day.set(not is_day.get())                  # toggle is_day
    total_days.set(total_days.get(0) + 0.5)       # increment day count, start from 0
    print(f"You've run this playground {total_days.get()*2} time(s).")
    print(f"And {total_days.get()} day(s) have gone by.")
    print(f"Next time it will be a {'day' if is_day.get() else 'night'}")
    
    '''
    Sample Output:
    
    ==== RUN 1 ====
    Day time. Yay!
    rehydrator\rehydrator_playground.pickle doesn't exist
    {'wake_up_time': '2024-09-02 14:55:53.486589'}
    You've run this playground 1.0 time(s).
    And 0.5 day(s) have gone by.
    Next time it will be a night
    
    ==== RUN 2 ====
    Night time. ZzzZZz
    {'wake_up_time': '2024-09-02 14:55:53.486589', 'sleeping_time': None}
    {'wake_up_time': '2024-09-02 14:55:53.486589', 'sleeping_time': '2024-09-02 14:56:18.784270'}
    I woke up at 2024-09-02 14:55:53.486589
    You've run this playground 2.0 time(s).
    And 1.0 day(s) have gone by.
    Next time it will be a day

    ==== RUN 3 ====
    Day time. Yay!
    {'wake_up_time': '2024-09-02 14:55:53.486589', 'sleeping_time': '2024-09-02 14:56:18.784270'}
    {'wake_up_time': '2024-09-02 14:56:46.747069', 'sleeping_time': '2024-09-02 14:56:18.784270'}
    I slept at 2024-09-02 14:56:18.784270
    You've run this playground 3.0 time(s).
    And 1.5 day(s) have gone by.
    Next time it will be a night
    '''
    
    # to reset the stats, run the below line:
    # rehydrator_controls.cleanup()
    # or just delete the rehydrator folder under CWD
    
    # Want to contribute? Make the changes and test it: HyperScale\HyperScaleUtils\rehydrator.py
    # and add your cases too!
    
    '''
    ===== CHANGELOG ===== 
    
    September 2, 2024
        Revamped the playground to have meaningful data
        Removed caching as there was a cleanup bug identified by Manoj Kumar Gopinath
        Added test_rehydrator
        Added CHANGELOG
    
    August 12, 2024
        store_exists was added by Virakti
    
    July 3, 2024
        Added _store_exists and _key_exists APIs
        Created the playground
    
    May 24, 2024
        Rehydrator was born
        Refer email: "[Automation] Improving test case resumability - Rehydrator"
    
    '''
