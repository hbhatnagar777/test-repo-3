def validate_disk(self, vm, other, method, restore_options, **kwargs):
        if len(self.vm.vm.disk_dict) != len(other.vm.vm.disk_dict):
                    self.log.info("Disk validation failed")
                    return False
            