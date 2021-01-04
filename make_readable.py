import tscribe
import os

numargs = len(sys.argv)

print("Number of arguments:" + str(numargs))
print(" arguments " + str(sys.argv))
if numargs > 1:
    usage_demo(numargs, sys.argv)
else:
   print("must pass directory path for json files to walk")
   exit()

json_base_directory = sys.argv[1]

for (dirpath, dirnames, filenames) in os.walk(json_base_directory):
    for filename in filenames:
        if "json" in filename:
            print("filename is " + filename)
            infile = dirpath + "/" + filename
            outfile = infile + ".docx"
            print("infile is " + infile)
            print("outfile is " + outfile)
            ret = tscribe.write(infile, save_as=outfile)
