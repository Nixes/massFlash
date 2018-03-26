from threading import Thread
import ctypes, sys
import time
import re
from flash import Flash
from driveManager import DriveManager

class MassFlash:
    disk_image_path = ""
    drive_manager = None
    flashing_operations = []

    def __init__(self, disk_image_path):  # {
        self.disk_image_path = disk_image_path
        self.drive_manager = DriveManager()
    # }


    def startFlash(self,disk):
        flashing_operation = Flash(disk, self.disk_image_path)
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

    def showStatus(self):  # {
        indexes_to_remove = []
        for index, flashing_operation in enumerate(self.flashing_operations):
            if flashing_operation.status() == False:
                indexes_to_remove.append(index)

        # only print newline if there was some flashing operation in progress
        if len(self.flashing_operations) > 0:
            print('\n')

        # sort index by index largest to smallest to allow all to be removed
        indexes_to_remove = sorted(indexes_to_remove, reverse=True)
        for index_to_remove in indexes_to_remove:
            del self.flashing_operations[index_to_remove]
    # }

    def run(self):  # {
        while True:  # {
            newDrives = self.drive_manager.getNewDrives()
            for newDrive in newDrives:
                print(newDrive)
                if self.askStartFlashing():
                    print('Starting flashing...')
                    self.startFlash(newDrive)
                else:
                    print('Ignoring this device')
            # get all flashing progress
            self.showStatus()
            time.sleep(0.5)
        # }
    # }

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
checkAdmin()

image_path = sys.argv[1]
print("Starting mass flash using image: "+image_path)

massFlash = MassFlash(image_path)
massFlash.run()
