# This file reduces the def, DEM, and load results, as well as the design variables, into a single master file.
# Originally, this was how the results were recorded, but the results needed to be separated to individual files
# so that different runs wouldn't clobber each other.

import os, shutil

def remove_files(sm_name, num_pts, turbine, turbulence, airfoil_name, file_type):

    for k in range(len(file_type)):

        ft = file_type[k]

        for j in range(len(sm_name)):

            # get directory name
            dir_name = 'Opt_Files/' + sm_name[j] + '/sm_var_dir_' + turbulence + '_' + turbine + '_' + airfoil_name + '/'

            # create new master file
            file_master= dir_name + 'sm_master_' + ft + '.txt'

            file_name = dir_name + 'sm_' + ft + '_0.txt'
            f = open(file_name, "r")
            lines = f.readlines()
            lines_header = lines[0]
            f.close()

            line_list = [lines_header]

            # read lines / remove file
            for i in range(num_pts[j]):

                try:
                    # get file names
                    file_name = dir_name + 'sm_' + ft + '_' + str(i) + '.txt'

                    f = open(file_name, "r")
                    lines = f.readlines()
                    f.close()
                    line_list.append(lines[i + 1])

                    # remove file
                    os.remove(file_name)
                except:
                    pass

            # write lines
            f_master = open(file_master, "w+")
            for i in range(len(line_list)):
                f_master.write(line_list[i])
            f_master.close()

if __name__ == "__main__":

    sm_name = ['test_3MW_1']
    num_pts = [5]

    turbine = 'I'
    turbulence = 'B'
    airfoil_name = 'af1'

    file_type = ['def', 'load', 'DEM', 'var']

    remove_files(sm_name, num_pts, turbine, turbulence, airfoil_name, file_type)
