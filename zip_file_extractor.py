from StringIO import StringIO
from zipfile import ZipFile
import os

if __name__ == "__main__":

    path_zipped = "/home/jerry/Desktop/STL-files-zipped/"
    path_stl = "/home/jerry/Desktop/STL-files/"

    for zipped_file in os.listdir(path_zipped):
        zipfile = ZipFile(path_zipped+zipped_file)
        for name in zipfile.namelist():
            if ".stl" in name:
                with open(path_stl+name, 'w') as handle:
                    handle.write(zipfile.open(name).read())
