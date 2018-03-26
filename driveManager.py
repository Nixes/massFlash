# library for getting physical device handles for all devices currently connected
import wmi  # wmi is used to get list of physical drives on a windows system
import sys  # sys is used for operating system specific behaviour
from psutil import disk_partitions

class Drive:
    physical_disk = "";
    partitions = [];

    # since for some reason psutil disk_partitions returns the incorrect device names
    # for windows drives we have to modify the windows device name into a physical device name
    def preprocessDeviceName(self,device_name):
        # if sys.platform == 'win32':
        #     prefix = r"\\.\\"
        #     return prefix+device_name[:-1]
        if device_name.startswith("/dev/disk"):
            # rdisk works better on osx so we'll use that one
            device_name = device_name.replace("/dev/disk", "/dev/rdisk")
            # split remove partition descripter so we get the raw device
            device_name = re.sub('([s][0-9])','',device_name)
            return device_name
        else:
            return device_name

    def __init__(self, physical_disk):  # {
        self.physical_disk = self.preprocessDeviceName(physical_disk)
    # }

    def addPartition(self, partition_path):  # {
        self.partitions.append(partition_path)
    # }

    def unmount(self):
        if sys.platform == 'osx':
            for partition in self.partitions:
                call(["sudo", "umount", "-f", partition])

    def debug(self):
        print("physical_disk: "+self.physical_disk+" partitions: "+str(self.partitions))

class DriveManager:
    current_drives = None

    # windows specific version of get possible drives
    def _winGetPossibleDrives(self):
        converted_disks = []
        physical_disks = wmi.WMI().Win32_DiskDrive(MediaType="Removable Media")
        for physical_disk in physical_disks:
            converted_disk = Drive(physical_disk.Name)
            # partitions = []
            # for win_partition in physical_disk.associators ("Win32_DiskDriveToDiskPartition"):
            #     print(win_partition)

            converted_disks.append(converted_disk)
        return converted_disks

    def _unixGetPossibleDrives(self):  # {
        filtered_drives = []
        for disk in disk_partitions():
            # filter out all /dev/sda* volumes
            if disk.device.find('/dev/sda') != -1:
                continue

            converted_disk = Disk(disk.device)
            converted_disk.addPartition(disk.mountpoint)

            filtered_drives.append(converted_disk)

        return filtered_drives
    # }


    def getPossibleDrives(self):
        if sys.platform == 'win32':
            return self._winGetPossibleDrives()
        elif sys.platform == 'osx' or sys.platform == 'linux':
            return self._unixGetPossibleDrives()


    def isNewDrive(self, latest_drive):
        for current_drive in self.current_drives:  # {
            if latest_drive.physical_disk == current_drive.physical_disk:  # {
                return False
            # }
        # }
        return True

    def debugDrives(self,drives):
        for drive in drives:
            drive.debug()

    # get a list of new drives that might be those being flashed
    def getNewDrives(self):
        new_drives = []
        # check if this is the first time running
        latest_drives = self.getPossibleDrives()
        if self.current_drives != None:
            for latest_drive in latest_drives:  # {
                if self.isNewDrive(latest_drive):  # {
                    print("New drive detected")
                    new_drives.append(latest_drive)
                # }
            # }
        # }

        # update current_drives
        self.current_drives = latest_drives
        return new_drives
