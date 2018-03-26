import sys
import threading
import time
from subprocess import call
from tqdm import tqdm

class Flash:
    disk_path = ""
    image_path = ""
    thread_handle = None
    bytes_to_write = 0
    bytes_written = 0
    progress_bar = None

    def getFileSize(self,path):
        filesize = 0
        with open(path, 'rb') as file:
            # seek to end of file
            file.seek(0, 2)
            filesize = file.tell()
        file.close()
        return filesize


    def __init__(self, disk, image):  # {
        self.disk_path = disk
        self.image_path = image
        # get the size of the image to write for percentage calculations
        # self.bytes_to_write = os.path.getsize(image)
        self.bytes_to_write = self.getFileSize(image)
        self.progress_bar = tqdm(total=self.bytes_to_write, desc="Disk: "+self.disk_path)
    # }

    # disk_path = /dev/sda, image_path = ~/imagingtest.dd
    def _writeDiskToFile(self, destImage, sourcedisk_path):  # {
        with open(sourcedisk_path, 'rb') as disk:
            with open('test.img', 'wb') as image:
                while True:
                    if image.write(disk.read(512)) == 0:
                        break

                    self.bytes_written += 512
        # close file/device handles
        disk.close()
        image.close()
    # }

    def _testWriteFileToDisk(self, sourceimage_path,  destdisk_path):  # {
        while self.bytes_written < self.bytes_to_write:
            self.bytes_written += 512
            time.sleep(0.0000001)
    # }

    def unmountDrive(self,destdisk_path):
        if sys.platform == 'osx':
            call(["sudo", "umount", "-f", destdisk_path])

    # may need rb+ for disk (+ does update mode), there are some indications that block devices can only be written to in this mode (especially in windows)
    def _writeFileToDisk(self, sourceimage_path,  destdisk_path):  # {
        # unmount drive
        self.unmountDrive(destdisk_path)

        with open(sourceimage_path, 'rb') as image:
            with open(destdisk_path, 'rb+') as disk:  # was wb
                while True:
                    bytes_read = image.read(512)
                    if len(bytes_read) == 0:
                        print("No bytes read")
                        break
                    num_bytes_written = disk.write(bytes_read)
                    self.bytes_written += num_bytes_written
                    if num_bytes_written == 0:  # {
                        print("No bytes written")
                        break
                    # }

        # close file/device handles
        disk.close()
        image.close()
    # }

    # simple wrapper that starts image flash in a thread
    def writeFileToDisk(self,sourceimage_path,  destdisk_path):
        thread_handle = threading.Thread(target=self._writeFileToDisk, args=[sourceimage_path, destdisk_path])
        thread_handle.start()
        self.thread_handle = thread_handle

    def start(self):
        self.writeFileToDisk(self.image_path,self.disk_path)

    def calculatePercentage(self):
        return (self.bytes_written/self.bytes_to_write)*100

    # prints a string showing current status of this flashing operation
    def status(self):  # {
        # self.progress_bar.update(self.bytes_written)
        percentage_string = str(self.calculatePercentage())
        print('Drive: '+self.disk_path+' Percentage: '+percentage_string+"\n")
    # }
