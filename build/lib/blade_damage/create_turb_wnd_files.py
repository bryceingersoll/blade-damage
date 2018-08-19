# creates a bunch of wind files


import numpy as np
from shutil import copyfile, rmtree
import os.path
import subprocess

import time

def replace_line(file_name, line_num, text):
    lines = open(file_name, 'r').readlines()
    lines[line_num] = text
    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()

def gen_files(nom_wnd_file, rand_seeds, mws, DLC_cases,
              DLC_name, turbsim_dir, turbsim_exe, inp_dir, wnd_dir, turb_char, turb_class, ref_ht):

    # generate turbsim input files
    for i in range(1, len(rand_seeds)+1):
        for j in range(0, len(mws)):
            for k in range(0, len(DLC_cases)):
                # create name of input file
                inp_file_name = r'\dlc_{0}_seed{1}_mws{2}.inp'.format(DLC_name[k],i,int(mws[j]))

                if os.path.isdir(turbsim_dir+inp_dir):
                    pass
                else:
                    os.mkdir(turbsim_dir+inp_dir)

                if os.path.isfile(turbsim_dir+inp_dir+inp_file_name):
                    print('file already exists')
                else:
                    # open(turbsim_dir+inp_dir+inp_file_name,"w+")
                    open(turbsim_dir+inp_dir+inp_file_name,"w+")

                # copy turbsim input file
                copyfile(turbsim_dir+nom_wnd_file, turbsim_dir+inp_dir+inp_file_name)

                # make changes to file
                # remember that lines are 0 based

                # random seed number
                replace_line(turbsim_dir+inp_dir+inp_file_name,3,str(int(rand_seeds[i-1])) + '\n')

                # mws
                replace_line(turbsim_dir+inp_dir+inp_file_name,36,str(mws[j]) + '\n')

                # DLC
                replace_line(turbsim_dir+inp_dir+inp_file_name,32,DLC_cases[k] + '\n')

                # turb_char
                replace_line(turbsim_dir + inp_dir + inp_file_name, 31, turb_char + '\n')

                # turb_class
                replace_line(turbsim_dir + inp_dir + inp_file_name, 30, turb_class + '\n')

                # ref_ht
                replace_line(turbsim_dir + inp_dir + inp_file_name, 35, str(ref_ht) + '\n')

    # execute turbsim
    for i in range(1, len(rand_seeds) + 1):
        for j in range(0, len(mws)):
            for k in range(0, len(DLC_cases)):
                # get name of input file
                inp_file_name = r'\dlc_{0}_seed{1}_mws{2}.inp'.format(DLC_name[k], i, int(mws[j]))
                inp_file_hh = r'\dlc_{0}_seed{1}_mws{2}.hh'.format(DLC_name[k], i, int(mws[j]))
                inp_file_sum = r'\dlc_{0}_seed{1}_mws{2}.sum'.format(DLC_name[k], i, int(mws[j]))

                # execute turbsim
                filename =turbsim_dir+inp_dir+inp_file_name
                args = turbsim_exe + filename
                subprocess.call([turbsim_exe, filename])

                # time.sleep(1.0)  # delays for 5 seconds. You can Also Use Float Value.
                #
                # print(turbsim_dir +inp_dir + inp_file_hh)
                # print(turbsim_dir + wnd_dir + inp_file_hh)
                # quit()

    for i in range(1, len(rand_seeds) + 1):
        for j in range(0, len(mws)):
            for k in range(0, len(DLC_cases)):
                inp_file_hh = r'\dlc_{0}_seed{1}_mws{2}.hh'.format(DLC_name[k], i, int(mws[j]))
                inp_file_sum = r'\dlc_{0}_seed{1}_mws{2}.sum'.format(DLC_name[k], i, int(mws[j]))

                # put created files into wanted directory
                os.rename(turbsim_dir +inp_dir + inp_file_hh, turbsim_dir + wnd_dir + inp_file_hh)
                # os.rename(turbsim_dir +inp_dir + inp_file_sum, turbsim_dir + wnd_dir + inp_file_sum)
                os.remove(turbsim_dir +inp_dir + inp_file_sum)

if __name__ == "__main__":
    # get nominal turbsim input file
    nom_wnd_file = r'\TurbSim_5MW.inp'

    # add random seeds
    rand_seeds = np.linspace(1, 6, 6)
    # rand_seeds = np.linspace(1,1,1)

    # add mean wind speeds
    mws = np.linspace(5, 23, 10)
    # mws = np.linspace(5,5,1)

    # add DLC cases
    DLC_cases = ['"NTM"', '"1ETM"']
    DLC_name = ['NTM', '1ETM']

    # turbsim directory
    turbsim_dir = r"C:\Users\bryce\Dropbox\GradPrograms\WND_File_Generation\TurbSim"

    turbsim_exe = turbsim_dir + r'\TurbSim.exe'

    # turb_char
    turb_char = 'B'

    # turb_class
    turb_class = '1-ED3' # I correlates to 1-EDx, where x could be 1,2,3
    turb_class_num = '1'

    # ref_ht
    ref_ht = 90.0 # m

    # input file and .wnd file directories
    inp_dir = r'\input_dir' + '_' + turb_char + turb_class_num
    wnd_dir = r'\wnd_dir' + '_' + turb_char + turb_class_num

    gen_files(nom_wnd_file, rand_seeds, mws, DLC_cases,
              DLC_name, turbsim_dir, turbsim_exe, inp_dir, wnd_dir, turb_char, turb_class, ref_ht)