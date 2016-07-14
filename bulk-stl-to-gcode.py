import os

if __name__ == "__main__":

    path_stl = "/home/jerry/Desktop/STL-files/"
    path_gcode = "/home/jerry/Desktop/Gcode-files/"


    for filename in os.listdir(path_stl):
        os.system('/home/jerry/CuraEngine/CuraEngine/build/CuraEngine slice -v -j /home/jerry/CuraEngine/CuraEngine/resources/ultimaker2_go.def.json -o \"'+path_gcode+filename+'.gcode\" -e1 -s infill_line_distance=0 -e0 -l \"'+path_stl+filename+'\"')


