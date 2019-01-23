from psutil import disk_partitions
from threading import Thread
import ctypes, sys
import time
import re
from flash import Flash

class MassFlash:
    disk_image_path = ""
    current_drives = []
    flashing_operations = []

    def __init__(self, disk_image_path):
        self.disk_image_path = disk_image_path

    # since for some reason psutil disk_partitions returns the incorrect device names
    # for windows drives we have to modify the windows device name into a physical device name
    def preprocessDeviceName(self, device_name):
        if sys.platform == 'win32':
            prefix = r"\\.\\"
            return prefix+device_name[:-1]
        elif device_name.startswith("/dev/disk"):
            # rdisk works better on osx so we'll use that one
            device_name = device_name.replace("/dev/disk", "/dev/rdisk")
            # split remove partition descriptor
            device_name = re.sub('([s][0-9])','',device_name)
            return device_name
        else:
            return device_name

    def getPossibleDrives(self):
        filtered_drives = []
        for disk in disk_partitions():
            # filter out all /dev/sda* volumes
            if disk.device.find('/dev/sda') != -1:
                continue

            # if disk.fstype == 'vfat' and disk.device.find('/dev/sdb') >= 0:
            filtered_drives.append(disk)

        return filtered_drives

    def isNewDrive(self, latest_drive):
        for current_drive in self.current_drives:
            if latest_drive.device == current_drive.device:
                return False
        return True

    # get a list of new drives that might be those being flashed
    def getNewDrives(self):
        new_drives = []
        # check if this is the first time running
        latest_drives = self.getPossibleDrives()
        if len(self.current_drives) > 0:
            for latest_drive in latest_drives:
                if self.isNewDrive(latest_drive):
                    new_drives.append(latest_drive)

        # update current_drives
        self.current_drives = latest_drives
        return new_drives

    def startFlash(self, disk):
        processed_disk_name = self.preprocessDeviceName(disk)
        print("Processed File Name: "+processed_disk_name)
        flashing_operation = Flash(processed_disk_name, self.disk_image_path,disk)
        flashing_operation.start()
        self.flashing_operations.append(flashing_operation)

    def askStartFlashing(self):
        start_flashing_input = input("Are you sure you want to start flashing this new device? This will overwrite all existing contents. y/n? ")
        if start_flashing_input == 'y':
            return True
        elif start_flashing_input == 'n':
            return False
        else:
            # if answer did not match expected, ask again
            return self.askStartFlashing()

    def showStatus(self):
        indexes_to_remove = []
        for index, flashing_operation in enumerate(self.flashing_operations):
            if flashing_operation.status() == False:
                indexes_to_remove.append(index)

        print('\n')
        # sort index by index largest to smallest to allow all to be removed
        indexes_to_remove = sorted(indexes_to_remove, reverse=True)
        for index_to_remove in indexes_to_remove:
            del self.flashing_operations[index_to_remove]

    def run(self):
        while True:
            newDrives = self.getNewDrives()
            for newDrive in newDrives:
                print(newDrive)
                if self.askStartFlashing():
                    print('Starting flashing...')
                    self.startFlash(newDrive.device)
                else:
                    print('Ignoring this device')
                # self.startFlash()
            # get all flashing progress
            self.showStatus()
            time.sleep(0.05)


# checks if currently logged in user is an admin
def isAdmin():
    try:
        user_is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print("user admin: "+str(user_is_admin))
        return user_is_admin
    except:
        print("Failed to read admin status")
        return False


def checkAdmin():
    if isAdmin() == False:
        print('User not admin, requesting admin')
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, sys.argv[0], None, 1)
        exit()
# checkAdmin()

image_path = sys.argv[1]
print("Starting mass flash using image: "+image_path)

massFlash = MassFlash(image_path)
massFlash.run()
