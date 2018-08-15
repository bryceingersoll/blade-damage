# FAST_util.py includes a number of necessary parameters and functions, as well as optional plotting functions, that
# define how FAST is used in the optimization routine

from openmdao.api import Problem
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import random
import re
import shutil
from akima import Akima

# ========================================================================================================= #

def setupFAST_checks(FASTinfo):

    # === check splines / results === #
    # if any are set as true, False will stop
    FASTinfo['check_results'] = False  # Opt. stops if set as True
    FASTinfo['check_sgp_spline'] = False  # Opt. stops if set as True
    FASTinfo['check_stif_spline'] = False  # Opt. stops if set as True
    FASTinfo['check_peaks'] = False  # Opt. stops if set as True
    FASTinfo['check_rainflow'] = False  # Opt. stops if set as True
    FASTinfo['check_rm_time'] = False  # Opt. stops if set as True

    FASTinfo['check_damage'] = False  # Opt. stops if set as True
    FASTinfo['check_nom_DEM_damage'] = False # only works when check_damage is set as True

    FASTinfo['check_opt_DEMs'] = False # only called when opt_with_fixed_DEMs is True

    FASTinfo['check_fit'] = False  # Opt. stops if set as True
    FASTinfo['do_cv_DEM'] = False  # cross validation of surrogate model for DEMs
    FASTinfo['do_cv_Load'] = False  # cross validation of surrogate model for extreme loads
    FASTinfo['do_cv_def'] = False  # cross validation of surrogate model for tip deflection
    FASTinfo['check_sm_accuracy'] = False # checks accuracy of sm for initial design

    FASTinfo['check_point_dist'] = False  # plot distribution of points (works best in 2D)
    FASTinfo['check_cv'] = False # works best in 2D
    FASTinfo['check_kfold'] = False # plot how folds are distributed among training points

    FASTinfo['check_var_domains'] = False # plots

    FASTinfo['make_max_DEM_files'] = False # makes .txt files

    return FASTinfo

# ========================================================================================================= #

def setupFAST(FASTinfo, description):

    # === set up FAST top level options === #
    FASTinfo = setup_top_level_options(FASTinfo)

    # === set up FAST check options === #
    FASTinfo = setupFAST_checks(FASTinfo)

    # === set up other FAST options === #
    FASTinfo = setupFAST_other(FASTinfo)

    # === set up rotor === #
    rotor = setup_rotor(FASTinfo)

    # === constraint groups === #
    FASTinfo['use_fatigue_cons'] = True
    FASTinfo['use_ext_cons'] = True
    FASTinfo['use_tip_def_cons'] = False

    #=== ===#

    FASTinfo['description'] = description

    # === Platform (Local or SC) - unique to each user === #

    # path to RotorSE_FAST directory
    # FASTinfo['path'] = '/fslhome/ingerbry/GradPrograms/'
    FASTinfo['path'] = '/Users/bingersoll/Dropbox/GradPrograms/'

    # === dir_saved_plots === #
    # FASTinfo['dir_saved_plots'] = '/fslhome/ingerbry/GradPrograms/opt_plots'
    # FASTinfo['dir_saved_plots'] = '/Users/bingersoll/Desktop'
    FASTinfo['dir_saved_plots'] = '.'

    # === Optimization and Template Directories === #
    # FASTinfo['opt_dir'] = ''.join((FASTinfo['path'], 'RotorSE_FAST/' \
    #     'RotorSE/src/rotorse/FAST_Files/Opt_Files/', FASTinfo['description']))
    FASTinfo['opt_dir'] = ''.join((FASTinfo['path'], 'blade-damage/FAST_Files/Opt_Files/', FASTinfo['description']))


    if os.path.isdir(FASTinfo['opt_dir']):
        pass
    else:
        os.mkdir(FASTinfo['opt_dir'])

    # === set FAST template files === #

    # NREL5MW, WP_5.0MW, WP_3.0MW, WP_1.5MW, WP_0.75MW
    FASTinfo['FAST_template_name'] = 'NREL5MW'

    # FASTinfo['template_dir'] = FASTinfo['path'] + 'RotorSE_FAST/RotorSE/src/rotorse/' \
    #                         'FAST_Files/FAST_File_templates/' + FASTinfo['FAST_template_name'] + '/'
    FASTinfo['template_dir'] = FASTinfo['path'] + 'blade-damage/FAST_Files/FAST_File_templates/' + FASTinfo['FAST_template_name'] + '/'

    # === get FAST executable === #
    FASTinfo = get_FAST_executable(FASTinfo)

    # === get blade length === #
    FASTinfo = get_bladelength(FASTinfo)

    # === options if previous optimizations have been performed === #

    if FASTinfo['seq_run']:
        FASTinfo['prev_description'] = 'test_batch_1'

        # for running multiple times
        # FASTinfo['prev_opt_dir'] = ''.join((FASTinfo['path'], 'RotorSE_FAST/' \
        #     'RotorSE/src/rotorse/FAST_Files/Opt_Files/', FASTinfo['prev_description']))
        FASTinfo['prev_opt_dir'] = ''.join((FASTinfo['path'], 'blade-damage/FAST_Files/Opt_Files/', FASTinfo['prev_description']))

    FASTinfo['max_DEMx_file'] = FASTinfo['opt_dir'] + '/xDEM_max.txt'
    FASTinfo['max_DEMy_file'] = FASTinfo['opt_dir'] + '/yDEM_max.txt'

    # === choose .wnd file directories === #
    FASTinfo = choose_wnd_dir(FASTinfo)

    # airfoil group name
    FASTinfo['airfoil_group_name'] = 'af1'

    # === Surrogate Model Options === #

    if FASTinfo['train_sm'] or FASTinfo['Use_FAST_sm']:
        FASTinfo = create_surr_model_params(FASTinfo)

    if FASTinfo['train_sm']:

        if FASTinfo['training_point_dist'] == 'lhs':
            FASTinfo, rotor = create_surr_model_lhs_options(FASTinfo, rotor)
        else:
            raise Exception('Training point distribution not specified correctly.')

    # === ===#

    # === Add FAST outputs === #
    FASTinfo = add_outputs(FASTinfo)

    # === FAST Run Time === #
    FASTinfo['Tmax_turb'] = 615.0  # 640.0
    FASTinfo['Tmax_nonturb'] = 100.0  # 100.0
    FASTinfo['dT'] = 0.0125

    # remove artificially noisy data
    # must be greater than Tmax_turb, Tmax_nonturb
    FASTinfo['rm_time'] = 15.0 # 40.0

    FASTinfo['turb_sf'] = 1.0

    # option for cross validation
    if FASTinfo['do_cv_DEM'] or FASTinfo['do_cv_Load'] or FASTinfo['do_cv_def']:

        FASTinfo = kfold_params(FASTinfo)

        # check kfold
        if FASTinfo['check_kfold']:
            plot_kfolds(FASTinfo)

    # === strain gage placement === #
    FASTinfo['sgp'] = [1, 2, 3]
    # FASTinfo['sgp'] = [4]

    #for each position
    FASTinfo['NBlGages'] = []
    FASTinfo['BldGagNd'] = []
    FASTinfo['BldGagNd_config'] = []

    if 1 in FASTinfo['sgp']:
        FASTinfo['NBlGages'].append(7)  # number of strain gages (max is 7)
        FASTinfo['BldGagNd'].append([1, 2, 3, 4, 5, 6, 7])  # strain gage positions
        FASTinfo['BldGagNd_config'].append([1, 2, 3, 4, 5, 6, 7])  # strain gage positions
    if 2 in FASTinfo['sgp']:
        FASTinfo['NBlGages'].append(7)  # number of strain gages (max is 7)
        FASTinfo['BldGagNd'].append([8, 9, 10, 11, 12, 13, 14])  # strain gage positions
        FASTinfo['BldGagNd_config'].append([8, 9, 10, 11, 12, 13, 14])  # strain gage positions
    if 3 in FASTinfo['sgp']:
        FASTinfo['NBlGages'].append(3)  # number of strain gages (max is 7)
        FASTinfo['BldGagNd'].append([15, 16, 17])  # strain gage positions
        FASTinfo['BldGagNd_config'].append([15, 16, 17])  # strain gage positions
    if 4 in FASTinfo['sgp']:
        # over entire range
        FASTinfo['NBlGages'].append(7)  # number of strain gages (max is 7)
        FASTinfo['BldGagNd'].append([1, 3, 5, 7, 9, 12, 17])  # strain gage positions
        FASTinfo['BldGagNd_config'].append([1, 3, 5, 7, 9, 12, 17])  # strain gage positions

    # === specify which DLCs will be included (for calc_fixed_DEMs === #
    FASTinfo = specify_DLCs(FASTinfo)

    # === copy .wnd files === #
    if FASTinfo['train_sm']:
        copy_wnd_files(FASTinfo)

    # fatigue options
    FASTinfo['m_value'] = 10.0

    # === caseids === #
    FASTinfo['caseids'] = []
    for j in range(0, len(FASTinfo['sgp'])):
        for i in range(0 + 1, len(FASTinfo['wnd_list']) + 1):

            if 'wnd_number' in FASTinfo:
                cur_wnd_num = FASTinfo['wnd_number'] + 0
            else:
                cur_wnd_num = i

            FASTinfo['caseids'].append("WNDfile{0}".format(cur_wnd_num) + '_sgp' + str(FASTinfo['sgp'][j]))


    # === distribution type used for extreme moment extrapolation === #
    FASTinfo['eme_fit'] = 'gaussian'

    return FASTinfo, rotor

# ========================================================================================================= #

def setupFAST_other(FASTinfo):
    # these are options that can be changed, where optimization/calculations continue

    # turns off/on print statements from smt (surrogate model toolbox)
    FASTinfo['print_sm'] = False

    # use this when calculating DEMs for fixed-DEMs calculation
    FASTinfo['remove_fixedcalc_dir'] = True
    FASTinfo['remove_unnecessary_files'] = True

    # sequential or parallel calculation of turbine response for each .wnd file
    FASTinfo['calculation_type'] = 'sequential'

    # save rated torque
    FASTinfo['save_rated_torque'] = False

    # use this when training points for surrogate model
    FASTinfo['remove_sm_dir'] = False

    # === below are two useful options when training different designs for the surrogate model === #

    # run template files - no connection with RotorSE - used to train surrogate model using WindPact turbine designs
    # also used to calculate damage equivalent moments (DEMs)
    FASTinfo['run_template_files'] = False
    # change just chord, twist distributions
    FASTinfo['set_chord_twist'] = True

    # calculate DEMs, extreme moments without optimization routine, using surrogate model
    FASTinfo['calc_DEM_using_sm_no_opt'] = True

    return FASTinfo

# ========================================================================================================= #

def setup_rotor(FASTinfo):

    if FASTinfo['calculation_type'] == 'sequential':
        rotor = Problem()
    else:
        from openmdao.core.petsc_impl import PetscImpl
        rotor = Problem(impl=PetscImpl)

    return rotor

# ========================================================================================================= #

def specify_DLCs(FASTinfo):
    # === options if active DLC list has been created === #
    FASTinfo['use_DLC_list'] = False
    if FASTinfo['use_DLC_list']:
        FASTinfo['DLC_list_loc'] = FASTinfo['opt_dir'] + '/' + 'active_wnd.txt'

    if not FASTinfo['use_DLC_list']:

        # === for optimization === #
        # DLC_List = ['DLC_1_2', 'DLC_1_3', 'DLC_1_4','DLC_1_5', 'DLC_6_1', 'DLC_6_3']
        # DLC_List = ['DLC_0_0', 'DLC_1_2', 'DLC_1_3', 'DLC_1_4',' DLC_1_5', 'DLC_6_1', 'DLC_6_3']

        # === for testing === #

        # rated speed wind file
        DLC_List = ['DLC_0_0']

        # non turbulent DLCs
        # DLC_List = ['DLC_1_4','DLC_1_5','DLC_6_1','DLC_6_3']

        # turbulent DLCs
        # DLC_List = ['DLC_1_2','DLC_1_3']

    else:
        DLC_List_File = open(FASTinfo['DLC_list_loc'], 'r')

        DLC_lines = DLC_List_File.read().split('\n')
        DLC_List = []
        for i in range(0, len(DLC_lines) - 1):
            DLC_List.append(DLC_lines[i])
    FASTinfo['DLC_List'] = DLC_List

    # === turbulent wind file parameters === #
    #  random seeds (np.linspace(1,6,6) is pre-calculated)
    FASTinfo['rand_seeds'] = np.linspace(1, 6, 6)

    #  mean wind speeds (np.linspace(5,23,10) is pre-calculated)
    FASTinfo['mws'] = np.linspace(5, 23, 10)

    # === create list of .wnd files === #
    # .wnd files list
    FASTinfo['wnd_list'] = []

    # wnd type list
    FASTinfo['wnd_type_list'] = []

    # list of whether turbine is parked or not
    FASTinfo['parked'] = []

    for i in range(0, len(FASTinfo['DLC_List']) + 0):
        # call DLC function
        FASTinfo['wnd_list'], FASTinfo['wnd_type_list'] \
            = DLC_call(FASTinfo['DLC_List'][i], FASTinfo['wnd_list'], FASTinfo['wnd_type_list'],
                       FASTinfo['rand_seeds'], FASTinfo['mws'], len(FASTinfo['sgp']), FASTinfo['parked'])

    reordered_type_list = []
    reordered_parked_list = []
    for j in range(len(FASTinfo['sgp'])):
        for i in range(len(FASTinfo['wnd_list'])):
            reordered_type_list.append(FASTinfo['wnd_type_list'][i * len(FASTinfo['sgp']) + j])
            reordered_parked_list.append(FASTinfo['parked'][i * len(FASTinfo['sgp']) + j])

    FASTinfo['wnd_type_list'] = reordered_type_list
    FASTinfo['parked'] = reordered_parked_list

    if FASTinfo['calc_fixed_DEMs']:
        FASTinfo = choose_wnd_file(FASTinfo)

    return FASTinfo

# ========================================================================================================= #

def choose_wnd_dir(FASTinfo):

    # === turbulence/turbine class === #
    FASTinfo['turbulence_class'] = 'B'
    FASTinfo['turbine_class'] = 'I'

    if FASTinfo['turbulence_class'] == 'A':
        FASTinfo['turbulence_intensity'] = 0.12
    if FASTinfo['turbulence_class'] == 'B':
        FASTinfo['turbulence_intensity'] = 0.14
    if FASTinfo['turbulence_class'] == 'C':
        FASTinfo['turbulence_intensity'] = 0.16

    # === turbulent, nonturbulent directories === #
    FASTinfo['master_turb_wnd_dir'] = 'blade-damage/WND_Files/turb_wnd_dir_' \
    + FASTinfo['turbulence_class'] + '_' + FASTinfo['turbine_class'] + '/'

    FASTinfo['master_nonturb_wnd_dir'] = 'blade-damage/WND_Files/nonturb_wnd_dir/'


    if FASTinfo['train_sm']:

        try:
            training_point_num = int(sys.argv[1])
        except:
            training_point_num = 0

        new_wnd_dir = 'blade-damage/WND_Files/training_point_' + str(training_point_num)

        # create new wind directories if training points for surrogate model
        if not os.path.isdir(FASTinfo['path'] + new_wnd_dir):
            os.mkdir(FASTinfo['path'] + new_wnd_dir)

        FASTinfo['new_wnd_dir_sm'] = new_wnd_dir

        new_wnd_dir_turb = new_wnd_dir + '/turb_wnd_dir/'
        if not os.path.isdir(FASTinfo['path'] + new_wnd_dir_turb):
            os.mkdir(FASTinfo['path'] + new_wnd_dir_turb)

        new_wnd_dir_nonturb = new_wnd_dir + '/nonturb_wnd_dir/'
        if not os.path.isdir(FASTinfo['path'] + new_wnd_dir_nonturb):
            os.mkdir(FASTinfo['path'] + new_wnd_dir_nonturb)

        FASTinfo['turb_wnd_dir'] = new_wnd_dir_turb
        FASTinfo['nonturb_wnd_dir'] = new_wnd_dir_nonturb

    else:
        FASTinfo['turb_wnd_dir'] = FASTinfo['master_turb_wnd_dir']
        FASTinfo['nonturb_wnd_dir'] = FASTinfo['master_nonturb_wnd_dir']

    return FASTinfo

# ========================================================================================================= #

def copy_wnd_files(FASTinfo):

    for i in range(len(FASTinfo['wnd_list'])):

        if FASTinfo['wnd_type_list'][i] == 'turb':
            shutil.copyfile(FASTinfo['path'] + FASTinfo['master_turb_wnd_dir'] + FASTinfo['wnd_list'][i],
                            FASTinfo['path'] + FASTinfo['turb_wnd_dir'] + FASTinfo['wnd_list'][i])
        else:
            shutil.copyfile(FASTinfo['path'] + FASTinfo['master_nonturb_wnd_dir'] + FASTinfo['wnd_list'][i],
                            FASTinfo['path'] + FASTinfo['nonturb_wnd_dir'] + FASTinfo['wnd_list'][i])


# ========================================================================================================= #

def remove_sm_wnd_files(FASTinfo):

    shutil.rmtree(FASTinfo['path'] + FASTinfo['new_wnd_dir_sm'])

# ========================================================================================================= #

def choose_wnd_file(FASTinfo):

    try:
        FASTinfo['wnd_number'] = int(sys.argv[1])

        num_wnd_files = len(FASTinfo['wnd_list'])

        wnd_list = []
        wnd_list.append(FASTinfo['wnd_list'][FASTinfo['wnd_number']-1])
        FASTinfo['wnd_list'] = wnd_list

        FASTinfo['parked'] = [FASTinfo['parked'][FASTinfo['wnd_number']-1],
                              FASTinfo['parked'][FASTinfo['wnd_number']-1],
                              FASTinfo['parked'][FASTinfo['wnd_number']-1]]

        FASTinfo['wnd_type_list'] = [FASTinfo['wnd_type_list'][FASTinfo['wnd_number']-1],
                                     FASTinfo['wnd_type_list'][FASTinfo['wnd_number']-1],
                                     FASTinfo['wnd_type_list'][FASTinfo['wnd_number']-1]]

    except:
        pass

    return FASTinfo

# ========================================================================================================= #

def kfold_params(FASTinfo):

    # number of folds
    FASTinfo['num_folds'] = 5

    # check that num_pts/num_folds doesn't have a remainder (is divisible)
    if (FASTinfo['num_pts'] % FASTinfo['num_folds']) > 0:
        raise Exception('Number of folds (k) should be a factor of num_pts.')
    if FASTinfo['num_folds'] == FASTinfo['num_pts']:
        raise Exception('Number of folds (k) needs to be less than num_pts (for current setup).')
    num_pts_in_grp = FASTinfo['num_pts'] / FASTinfo['num_folds']

    # randomly divide pts into num_folds groups
    num_pts_list = np.linspace(0, FASTinfo['num_pts']-1, FASTinfo['num_pts']) # -1 so it's zero-based

    # === shuffled list === #
    shuffled_list_file = FASTinfo['opt_dir'] + '/shuffled_list.txt'

    use_preset_shuffled_list = True

    if use_preset_shuffled_list:

        if not os.path.isfile(shuffled_list_file):

            # create shuffled list
            shuffled_list = random.sample(num_pts_list, len(num_pts_list))

            f = open(shuffled_list_file, "w+")

            for i in range(0, FASTinfo['num_pts']):
                    f.write(str(shuffled_list[i]) + '\n')

            f.close()

        else:

            shuffled_list_lines = open(shuffled_list_file, "r+").readlines()
            shuffled_list = []
            for i in range(FASTinfo['num_pts']):
                shuffled_list.append(float(shuffled_list_lines[i]))

    else:
        shuffled_list = random.sample(num_pts_list, len(num_pts_list))

    FASTinfo['kfolds'] = []
    for i in range(FASTinfo['num_folds']):
        FASTinfo['kfolds'].append(shuffled_list[i*num_pts_in_grp:(i+1)*num_pts_in_grp])


    return FASTinfo

# ========================================================================================================= #

def plot_kfolds(FASTinfo):

    point_file = FASTinfo['opt_dir'] + '/pointfile.txt'

    f = open(point_file, "r")

    lines = f.readlines()

    var1 = []
    var2 = []

    for i in range(FASTinfo['num_pts']):
        line_test = re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", lines[i].strip('\n'))

        var1.append(0.1+0.4*float(line_test[0]))
        var2.append(1.3+4.0*float(line_test[1]))

    kfold_dict1 = dict()
    kfold_dict2 = dict()

    for i in range(FASTinfo['num_folds']):
        kfold_dict1['kfold_' + str(i)] = []
        kfold_dict2['kfold_' + str(i)] = []

        for j in range(FASTinfo['num_pts']/FASTinfo['num_folds']):

            kfold_dict1['kfold_' + str(i)].append(var1[int(FASTinfo['kfolds'][i][j]) ] )
            kfold_dict2['kfold_' + str(i)].append(var2[int(FASTinfo['kfolds'][i][j]) ] )

    plt.figure()

    for i in range(FASTinfo['num_folds']):
        if i == 0:
            # plt.plot(kfold_dict1['kfold_' + str(i)], kfold_dict2['kfold_' + str(i)], 'ro', label='1st k-fold group')
            plt.plot(kfold_dict1['kfold_' + str(i)], kfold_dict2['kfold_' + str(i)], 'ro', label='Cross Validation Points')
        else:
            plt.plot(kfold_dict1['kfold_' + str(i)], kfold_dict2['kfold_' + str(i)], 'bo')

    plt.xlabel('1st Chord Distribution Control Point (m)')
    plt.ylabel('2nd Chord Distribution Control Point (m)')
    plt.title('Cross Validation Example')
    plt.legend()

    plt.savefig(FASTinfo['dir_saved_plots'] + '/kfold_example.png')

    plt.show()

    quit()

# ========================================================================================================= #


def get_FAST_executable(FASTinfo):

    if FASTinfo['FAST_template_name'] == 'NREL5MW':
        FASTinfo['fst_exe'] = FASTinfo['path'] + 'blade-damage/FAST_exe/' + 'FAST_glin64'
    elif FASTinfo['FAST_template_name'] == 'WP_0.75MW':
        FASTinfo['fst_exe'] = FASTinfo['path'] + 'blade-damage/FAST_exe/' + 'FAST_WP_075MW_glin64'
    elif FASTinfo['FAST_template_name'] == 'WP_1.5MW':
        FASTinfo['fst_exe'] = FASTinfo['path'] + 'blade-damage/FAST_exe/' + 'FAST_WP_15MW_glin64'
    elif FASTinfo['FAST_template_name'] == 'WP_3.0MW':
        FASTinfo['fst_exe'] = FASTinfo['path'] + 'blade-damage/FAST_exe/' + 'FAST_WP_3MW_glin64'
    elif FASTinfo['FAST_template_name'] == 'WP_5.0MW':
        FASTinfo['fst_exe'] = FASTinfo['path'] + 'blade-damage/FAST_exe/' + 'FAST_WP_5MW_glin64'
    else:
        raise Exception('FAST executable unavailable, must be built from source.')

    return FASTinfo


# ========================================================================================================= #


def setup_top_level_options(FASTinfo):

    if FASTinfo['opt_with_FAST_in_loop']:
        FASTinfo['use_FAST'] = True
        FASTinfo['Run_Once'] = False
        FASTinfo['train_sm'] = False
        FASTinfo['Use_FAST_Fixed_DEMs'] = False
        FASTinfo['Use_FAST_sm'] = False
        FASTinfo['seq_run'] = False

    elif FASTinfo['opt_without_FAST']:
        FASTinfo['use_FAST'] = False
        FASTinfo['Run_Once'] = False
        FASTinfo['train_sm'] = False
        FASTinfo['Use_FAST_Fixed_DEMs'] = False
        FASTinfo['Use_FAST_sm'] = False
        FASTinfo['seq_run'] = False

    elif FASTinfo['calc_fixed_DEMs']:
        FASTinfo['use_FAST'] = True
        FASTinfo['Run_Once'] = True
        FASTinfo['train_sm'] = False
        FASTinfo['Use_FAST_Fixed_DEMs'] = False
        FASTinfo['Use_FAST_sm'] = False
        FASTinfo['seq_run'] = False

    elif FASTinfo['calc_fixed_DEMs_seq']:
        FASTinfo['use_FAST'] = True
        FASTinfo['Run_Once'] = True
        FASTinfo['train_sm'] = False
        FASTinfo['Use_FAST_Fixed_DEMs'] = False
        FASTinfo['Use_FAST_sm'] = False
        FASTinfo['seq_run'] = True

    elif FASTinfo['opt_with_fixed_DEMs']:
        FASTinfo['use_FAST'] = False
        FASTinfo['Run_Once'] = False
        FASTinfo['train_sm'] = False
        FASTinfo['Use_FAST_Fixed_DEMs'] = True
        FASTinfo['Use_FAST_sm'] = False
        FASTinfo['seq_run'] = False

    elif FASTinfo['opt_with_fixed_DEMs_seq']:
        FASTinfo['use_FAST'] = False
        FASTinfo['Run_Once'] = False
        FASTinfo['train_sm'] = False
        FASTinfo['Use_FAST_Fixed_DEMs'] = True
        FASTinfo['Use_FAST_sm'] = False
        FASTinfo['seq_run'] = True

    elif FASTinfo['calc_surr_model']:
        FASTinfo['use_FAST'] = True
        FASTinfo['Run_Once'] = True
        FASTinfo['train_sm'] = True
        FASTinfo['Use_FAST_Fixed_DEMs'] = False
        FASTinfo['Use_FAST_sm'] = False
        FASTinfo['seq_run'] = False

    elif FASTinfo['opt_with_surr_model']:
        FASTinfo['use_FAST'] = False
        FASTinfo['Run_Once'] = False
        FASTinfo['train_sm'] = False
        FASTinfo['Use_FAST_Fixed_DEMs'] = False
        FASTinfo['Use_FAST_sm'] = True
        FASTinfo['seq_run'] = False

    else:
        raise Exception('Must choose a FAST option.')

    return FASTinfo

# ========================================================================================================= #

def setup_FAST_seq_run_des_var(rotor, FASTinfo):

    rotor_test = dict()
    for i in range(5):
        rotor_test['rotor_desvar'+str(i)] = []
        rotor_test['rotor_desvar_strings'+str(i)] = []

    file_name = FASTinfo['prev_opt_dir'] + '/' + 'opt_results.txt'

    fp = open(file_name)
    line = fp.readlines()

    for i in range(0, 5):

        rotor_test['rotor_desvar_strings' + str(i)] = re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", line[i])

        rotor_test['rotor_desvar' + str(i)] = np.zeros(len(rotor_test['rotor_desvar_strings'+str(i)]))
        for j in range(0, len(rotor_test['rotor_desvar' + str(i)])):
            rotor_test['rotor_desvar' + str(i)][j] = float(rotor_test['rotor_desvar_strings'+str(i)][j])


    rotor['r_max_chord'] = rotor_test['rotor_desvar'+str(0)]
    rotor['chord_sub'] = rotor_test['rotor_desvar'+str(1)]
    rotor['theta_sub'] = rotor_test['rotor_desvar'+str(2)]
    rotor['sparT'] = rotor_test['rotor_desvar'+str(3)]
    rotor['teT'] = rotor_test['rotor_desvar'+str(4)]

    return rotor

# ========================================================================================================= #

def create_surr_model_params(FASTinfo):

    # total number of points (lhs)
    FASTinfo['num_pts'] = 1000

    # approximation model
    # implemented options - second_order_poly, least_squares, kriging, KPLS, KPLSK, RBF (radial basis functions)
    FASTinfo['approximation_model'] = 'RBF'

    # initial hyper-parameter value (kriging, KPLS, KPLSK only use)
    FASTinfo['theta0_val'] = [1e-2]

    # training point distribution
    FASTinfo['training_point_dist'] = 'lhs'

    if FASTinfo['training_point_dist'] == 'lhs':

        FASTinfo['sm_var_out_dir'] = 'sm_var_dir_' + FASTinfo['turbulence_class'] \
                                     + '_' + FASTinfo['turbine_class'] + '_' + FASTinfo['airfoil_group_name']

        FASTinfo['sm_var_file_master'] = FASTinfo['sm_var_out_dir'] + '/' + 'sm_master_var.txt'
        FASTinfo['sm_DEM_file_master'] = FASTinfo['sm_var_out_dir'] + '/' + 'sm_master_DEM.txt'
        FASTinfo['sm_load_file_master'] = FASTinfo['sm_var_out_dir'] + '/' + 'sm_master_load.txt'
        FASTinfo['sm_def_file_master'] = FASTinfo['sm_var_out_dir'] + '/' + 'sm_master_def.txt'
    else:
        FASTinfo['sm_var_file'] = 'sm_var.txt'
        FASTinfo['sm_DEM_file'] = 'sm_DEM.txt'

    # list of variables that we are varying
    FASTinfo['sm_var_names'] = ['chord_sub', 'theta_sub', 'turbulence_intensity']

    # indices of which variables are used
    FASTinfo['sm_var_index'] = [[0,1,2,3], [0,1,2,3], [0]]


    # total num of variables used, variable index
    var_index = []
    num_var = 0

    for i in range(0, len(FASTinfo['sm_var_names'])):
        for j in range(0, len(FASTinfo['sm_var_index'][i])):
            num_var += 1
            var_index.append(i)

    FASTinfo['var_index'] = var_index
    FASTinfo['num_var'] = num_var

    # use smaller domain to sample points
    FASTinfo['restrict_lhs_domain'] = True

    return FASTinfo

# ========================================================================================================= #

# full factorial data choice
# def create_surr_model_linear_options(FASTinfo, rotor):
#
#     # how many different points will be used (linear)
#     FASTinfo['sm_var_max'] = [[10], [10]]
#
#
#     var_index = []
#     for i in range(0, len(FASTinfo['sm_var_max'])):
#         for j in range(0, len(FASTinfo['sm_var_max'][i])):
#             var_index.append(i)
#
#     FASTinfo['var_index'] = var_index
#
#     # which specific points will be used for this run
#     # probably argv variables from command line
#     # FASTinfo['sm_var_spec'] = [[4], [2,2,2,2]]
#     # FASTinfo['sm_var_spec'] = [[2], [1,1,1,1]]
#     # FASTinfo['sm_var_spec'] = [[2]]
#
#     # create options for which points are being used for dist. variables
#     # how many total for each set of design variables
#
#     # try:
#     #     FASTinfo['sm_var_spec'] = []
#     #     for i in range(0, len(FASTinfo['sm_var_names'])):
#     #         FASTinfo['sm_var_spec'].append([])
#     #
#     #     for i in range(1, int(len(sys.argv))):
#     #         FASTinfo['sm_var_spec'][var_index[i-1]].append(int(sys.argv[i]))
#     # except:
#         # raise Exception('A system argument is needed to calculate training points for the surrogate model.')
#     FASTinfo['sm_var_spec'] = [[0], [0]]
#
#     # print(FASTinfo['sm_var_spec'])
#     # quit()
#
#     # min, max values of design variables
#     FASTinfo['sm_var_range'] = [[0.1, 0.5], [1.3, 5.3], [-10.0, 30.0], [0.005, 0.2], [0.005, 0.2]]
#
#     # === initialize design variable values === #
#     FASTinfo = initialize_dv(FASTinfo)
#
#     FASTinfo['var_range'] = []
#     # initialize rotor design variables
#     for i in range(0, len(FASTinfo['sm_var_names'])):
#
#         # create var_range
#         if FASTinfo['sm_var_names'][i] == 'r_max_chord':
#             var_range = FASTinfo['sm_var_range'][0]
#         elif FASTinfo['sm_var_names'][i] == 'chord_sub':
#             var_range = FASTinfo['sm_var_range'][1]
#         elif FASTinfo['sm_var_names'][i] == 'theta_sub':
#             var_range = FASTinfo['sm_var_range'][2]
#         elif FASTinfo['sm_var_names'][i] == 'sparT':
#             var_range = FASTinfo['sm_var_range'][3]
#         elif FASTinfo['sm_var_names'][i] == 'teT':
#             var_range = FASTinfo['sm_var_range'][4]
#         else:
#             Exception('A surrogate model variable was listed that is not a design variable.')
#
#
#         for j in range(0, len(FASTinfo['sm_var_max'][i])):
#
#             index = FASTinfo['sm_var_index'][i][j]
#
#             sm_range = np.linspace(var_range[0], var_range[1], FASTinfo['sm_var_max'][i][j])
#
#             FASTinfo['var_range'].append(sm_range)
#
#             if hasattr(FASTinfo[FASTinfo['sm_var_names'][i]+'_init'], '__len__'):
#
#                 print(i, j, index)
#
#                 FASTinfo[FASTinfo['sm_var_names'][i]+'_init'][index] = sm_range[FASTinfo['sm_var_spec'][i][j]-1]
#
#             else:
#
#                 FASTinfo[FASTinfo['sm_var_names'][i] + '_init'] = sm_range[FASTinfo['sm_var_spec'][i][j]-1]
#
#     # set design variables in rotor dictionary
#
#     if FASTinfo['check_point_dist']:
#
#         plt.figure()
#
#         plt.title('Linear Sampling Example')
#         # plt.xlabel(FASTinfo['sm_var_names'][0])
#         # plt.ylabel(FASTinfo['sm_var_names'][1])
#         plt.xlabel('1st Chord Distribution Control Point (m)')
#         plt.ylabel('2nd Chord Distribution Control Point (m)')
#
#
#         # plt.xlim([0.9*min(FASTinfo['var_range'][0]), 1.1*max(FASTinfo['var_range'][0])])
#         # plt.ylim([0.9*min(FASTinfo['var_range'][1]), 1.1*max(FASTinfo['var_range'][1])])
#
#         for i in range(0, FASTinfo['sm_var_max'][0][0]):
#             for j in range(0, FASTinfo['sm_var_max'][1][0]):
#                 # plt.plot( FASTinfo['var_range'][0][i], FASTinfo['var_range'][1][j], 'ob', label='training points')
#                 plt.plot( FASTinfo['var_range'][0][i], FASTinfo['var_range'][0][j], 'ob', label='training points')
#
#         # plt.legend()
#         plt.savefig(FASTinfo['dir_saved_plots'] + '/linear_' + FASTinfo['description'] + '.png')
#         plt.show()
#
#         quit()
#
#     return FASTinfo, rotor

# ========================================================================================================= #

# Latin Hypercube-Sampling data choice
def create_surr_model_lhs_options(FASTinfo, rotor):

    # determine initial values
    FASTinfo = initialize_dv(FASTinfo)

    # if more than 1000 points are trained for surrogate model, need to use second sys.argv
    try:
        FASTinfo['sm_var_spec'] = int(sys.argv[1]) + int(sys.argv[2])*10e3
    except:
        pass
    # if less than 1000 points are trained for sm, only need one sys.argv
    try:
        FASTinfo['sm_var_spec'] = int(sys.argv[1])
    except:
        # raise Exception('Need to have system input when latin-hypercube sampling used.')
        FASTinfo['sm_var_spec'] = 0

    # add FASTinfo['sm_dir'] so simultaneous runs don't clobber each other
    FASTinfo['sm_dir'] = FASTinfo['opt_dir'] + '/sm_' + str(FASTinfo['sm_var_spec'])

    # create directory
    if not os.path.isdir(FASTinfo['opt_dir']):
        os.mkdir(FASTinfo['opt_dir'])

    # name of sm .txt files (will be in description folder)
    if not os.path.isdir(FASTinfo['opt_dir'] + '/' + FASTinfo['sm_var_out_dir']):
        os.mkdir(FASTinfo['opt_dir'] + '/' + FASTinfo['sm_var_out_dir'])

    FASTinfo['sm_var_file'] = FASTinfo['sm_var_out_dir'] + '/' + 'sm_var_' + str(FASTinfo['sm_var_spec']) + '.txt'
    FASTinfo['sm_DEM_file'] = FASTinfo['sm_var_out_dir'] + '/' + 'sm_DEM_' + str(FASTinfo['sm_var_spec']) + '.txt'
    FASTinfo['sm_load_file'] = FASTinfo['sm_var_out_dir'] + '/' + 'sm_load_' + str(FASTinfo['sm_var_spec']) + '.txt'
    FASTinfo['sm_def_file'] = FASTinfo['sm_var_out_dir'] + '/' + 'sm_def_' + str(FASTinfo['sm_var_spec']) + '.txt'

    var_index = FASTinfo['var_index']
    num_var = FASTinfo['num_var']

    # ranges of said variables
    # min, max values of design variables
    FASTinfo['sm_var_range'] = [[1.3*FASTinfo['bladeLength']/61.5, 5.3*FASTinfo['bladeLength']/61.5], [-10.0, 30.0],
                                [FASTinfo['turbulence_intensity'], FASTinfo['turbulence_intensity']]]

    # === do linear hypercube spacing === #
    from pyDOE import lhs

    point_file = FASTinfo['opt_dir'] + '/pointfile.txt'

    if not os.path.isfile(point_file):
        print('Creating training point file...')

        points = lhs(num_var, samples=FASTinfo['num_pts'], criterion='center')

        f = open(point_file,"w+")

        for i in range(0, len(points)):
            for j in range(0, len(points[i])):
                f.write(str(points[i,j]))
                f.write(' ')

            f.write('\n')
        f.close()

    lines = open(point_file,"r+").readlines()

    points = np.zeros([FASTinfo['num_pts'], num_var])
    for i in range(0, len(lines)):
        spec_line = lines[i].strip('\n').split()
        for j in range(0, len(spec_line)):
            points[i,j] = float(spec_line[j])

    # === === #

    new_var_list = []
    old_var_list = []
    FASTinfo['var_range'] = []

    for i in range(0, num_var):

        spec_var_name = FASTinfo['sm_var_names'][var_index[i]]

        # create var_range
        if spec_var_name == 'chord_sub':
            var_range = FASTinfo['sm_var_range'][0]
        elif spec_var_name == 'theta_sub':
            var_range = FASTinfo['sm_var_range'][1]
        elif spec_var_name == 'turbulence':
            var_range = FASTinfo['sm_var_range'][2]
        else:
            Exception('A surrogate model variable was listed that is not a design variable.')

        if FASTinfo['restrict_lhs_domain']:

            index = -1
            # determine which index in spec_var_name we're at

            for j in range(len(var_index[0:i+1])):
                if var_index[i] == var_index[j]:
                    index += 1

            # get specific variable initial value
            if spec_var_name == 'turbulence_intensity':
                spec_val = FASTinfo[spec_var_name + '_init']
            else:
                spec_val = FASTinfo[spec_var_name + '_init'][index]

            # create new range
            FASTinfo['range_frac'] = 0.05  # 0.15, 0.25, 0.35
            range_frac =  FASTinfo['range_frac']
            range_len = var_range[1]-var_range[0]
            new_var_range = [spec_val-range_frac*range_len, spec_val+range_frac*range_len]

            # if new range is smaller/larger than old range, adjust
            if new_var_range[0] < var_range[0]:
                new_var_range[0] = var_range[0]
            if new_var_range[1] > var_range[1]:
                new_var_range[1] = var_range[1]

            # append lists
            new_var_list.append(new_var_range)
            old_var_list.append(var_range)

            # set var_range to new_var_range
            var_range = new_var_range

        points[:,i] = points[:,i]*(var_range[1]-var_range[0]) + var_range[0]

        FASTinfo['var_range'].append(var_range)

    # create .txt files for surrogate model use
    for i in range(len(FASTinfo['sm_var_names'])):

        domain_file = FASTinfo['opt_dir'] + '/' + 'domain_' + FASTinfo['sm_var_names'][i] + '.txt'

        f = open(domain_file, 'w+')
        f.write(FASTinfo['sm_var_names'][i] + '\n')

        for j in range(len(FASTinfo['var_index'])):
            if FASTinfo['var_index'][j] == i:
                f.write(str(FASTinfo['var_range'][j][0]) + '\n')
                f.write(str(FASTinfo['var_range'][j][1]) + '\n')
        f.close()

    # plotting routine
    if FASTinfo['check_var_domains']:

        # chord_sub domain plot
        plt.figure()
        j = 1

        print(old_var_list)
        print(new_var_list)
        quit()

        for i in range(len(FASTinfo['var_index'])):

            if FASTinfo['var_index'][i] == 1: # chord_sub
                plt.plot([j,j], old_var_list[i], 'bx')
                plt.plot([j,j], new_var_list[i], '--rx')
                j += 1

        plt.xticks(np.linspace(1,j-1,j-1))
        plt.xlabel('chord variable index')
        plt.ylabel('Var Domain (m)')
        plt.title('chord domain, restriction: ' + str(FASTinfo['range_frac']*100.0) + '%')

        plt.savefig(FASTinfo['dir_saved_plots'] + '/' + 'chord_sub_domain' + str(int(FASTinfo['range_frac']*100.0)) + '.png')
        plt.show()

        plt.close()

        # theta_sub domain plot
        plt.figure()
        j = 1

        for i in range(len(FASTinfo['var_index'])):

            if FASTinfo['var_index'][i] == 2: # theta_sub
                plt.plot([j,j], old_var_list[i], 'bx')
                plt.plot([j,j], new_var_list[i], '--rx')
                j += 1

        plt.xticks(np.linspace(1,j-1,j-1))
        plt.xlabel('twist variable index')
        plt.ylabel('Var Domain (deg)')
        plt.title('twist domain, restriction: ' + str(FASTinfo['range_frac']*100.0) + '%')


        plt.savefig(FASTinfo['dir_saved_plots'] + '/' + 'theta_sub_domain_' + str(int(FASTinfo['range_frac']*100.0)) + '.png')
        plt.show()

        plt.close()

        quit()

    # === plot checks === #

    if FASTinfo['check_cv']:

        cv_point_file = FASTinfo['opt_dir'] + '_cv' + '/pointfile.txt'

        cv_lines = open(cv_point_file, "r+").readlines()

        cv_points = np.zeros([len(cv_lines), num_var])
        for i in range(0, len(lines)):
            cv_spec_line = cv_lines[i].strip('\n').split()
            for j in range(0, len(cv_spec_line)):
                cv_points[i, j] = float(cv_spec_line[j])

        for i in range(0, num_var):

            spec_var_name = FASTinfo['sm_var_names'][var_index[i]]

            # create var_range
            if spec_var_name == 'r_max_chord':
                var_range = FASTinfo['sm_var_range'][0]
            elif spec_var_name == 'chord_sub':
                var_range = FASTinfo['sm_var_range'][1]
            elif spec_var_name == 'theta_sub':
                var_range = FASTinfo['sm_var_range'][2]
            elif spec_var_name == 'sparT':
                var_range = FASTinfo['sm_var_range'][3]
            elif spec_var_name == 'teT':
                var_range = FASTinfo['sm_var_range'][4]
            else:
                Exception('A surrogate model variable was listed that is not a design variable.')

            #
            cv_points[:, i] = cv_points[:, i] * (var_range[1] - var_range[0]) + var_range[0]

        plt.figure()

        plt.title('Latin Hypercube Cross Validation Example')
        plt.xlabel(FASTinfo['sm_var_names'][0])
        plt.ylabel(FASTinfo['sm_var_names'][1])

        # plt.xlim(FASTinfo['var_range'][0])
        # plt.ylim(FASTinfo['var_range'][1])

        plt.plot(points[:,0], points[:,1], 'o', label='training points')
        plt.plot(cv_points[:,0], cv_points[:,1], 'o', label='cross-validation points')
        plt.legend()

        plt.savefig(FASTinfo['dir_saved_plots'] + '/lhs_cv_' + FASTinfo['description'] + '.png')
        plt.show()

        quit()

    if FASTinfo['check_point_dist']:

        plt.figure()

        plt.title('Latin Hypercube Sampling Example')
        # plt.xlabel(FASTinfo['sm_var_names'][0])
        # plt.ylabel(FASTinfo['sm_var_names'][1])

        plt.xlabel('1st Chord Distribution Control Point (m)')
        plt.ylabel('2nd Chord Distribution Control Point (m)')

        # plt.xlim(FASTinfo['var_range'][0])
        # plt.ylim(FASTinfo['var_range'][1])

        plt.plot(points[:,0], points[:,1], 'bo', label='training points')
        plt.legend()

        plt.savefig(FASTinfo['dir_saved_plots'] + '/lhs_' + FASTinfo['description'] + '.png')
        plt.show()

        quit()

    # === assign values === #

    cur_var = 0
    for i in range(0, len(FASTinfo['sm_var_names'])):

        # spec_var_name = FASTinfo['sm_var_names'][var_index[i]]
        spec_var_name = FASTinfo['sm_var_names'][i]

        for j in range(0, len(FASTinfo['sm_var_index'][i])):

            # print('-- i j pair ---')
            # print(i)
            # print(j)

            if hasattr( FASTinfo[spec_var_name + '_init'], '__len__'):
                FASTinfo[spec_var_name + '_init'][FASTinfo['sm_var_index'][i][j]] = points[FASTinfo['sm_var_spec'],cur_var]
            else:
                FASTinfo[spec_var_name + '_init'] = points[FASTinfo['sm_var_spec'],cur_var]

            cur_var += 1

    return FASTinfo, rotor

# ========================================================================================================= #

def define_des_var_domains(FASTinfo, rotor):

    for i in range(len(FASTinfo['sm_var_names'])):

        domain_file = FASTinfo['opt_dir'] + '/' + 'domain_' + FASTinfo['sm_var_names'][i] + '.txt'

        if os.path.isfile(domain_file):

            f = open(domain_file, "r")
            des_var = f.readlines()
            des_var_name = des_var[0].strip('\n')

            lower_array = np.zeros(int((len(des_var)-1)/2.0))
            upper_array = np.zeros(int((len(des_var)-1)/2.0))

            for j in range(1, (len(des_var)+1)/2):
                lower_array[j-1] = float(des_var[2*j-1].strip('\n'))
                upper_array[j-1] = float(des_var[2*j].strip('\n'))

            rotor.driver.add_desvar(des_var_name, lower=lower_array, upper=upper_array)

        else:
            # rotor.driver.add_desvar('r_max_chord', lower=0.1, upper=0.5)
            rotor.driver.add_desvar('chord_sub', lower=1.3 * np.ones(4), upper=5.3 * np.ones(4))
            rotor.driver.add_desvar('theta_sub', lower=-10.0 * np.ones(4), upper=30.0 * np.ones(4))

    return FASTinfo, rotor

# ========================================================================================================= #

# initialize design variables
def initialize_dv(FASTinfo):

    if FASTinfo['FAST_template_name'] == 'NREL5MW':
        FASTinfo['chord_sub_init'] = np.array([3.2612, 4.5709, 3.3178,   1.4621])
        FASTinfo['theta_sub_init'] = np.array([13.2783, 7.46036, 2.89317,   -0.0878099])

    elif FASTinfo['FAST_template_name'] == 'WP_0.75MW':
        FASTinfo['chord_sub_init'] = np.array([1.392, 1.723, 1.132, 0.700])
        FASTinfo['theta_sub_init'] = np.array([11.10, 6.35, 0.95, 0.08])

    elif FASTinfo['FAST_template_name'] == 'WP_1.5MW':
        FASTinfo['chord_sub_init'] = np.array([1.949, 2.412, 1.585, 0.980])
        FASTinfo['theta_sub_init'] = np.array([11.10, 6.35, 0.95, 0.08])

    elif FASTinfo['FAST_template_name'] == 'WP_3.0MW':
        FASTinfo['chord_sub_init'] = np.array([2.756, 3.412, 2.242, 1.386])
        FASTinfo['theta_sub_init'] = np.array([11.10, 6.35, 0.95, 0.08])

    elif FASTinfo['FAST_template_name'] == 'WP_5.0MW':
        FASTinfo['chord_sub_init'] = np.array([3.564, 4.411, 2.898, 1.793])
        FASTinfo['theta_sub_init'] = np.array([11.10, 6.35, 0.95, 0.08])

    else:
        raise Exception('Still need to add other wind turbine initial designs')

    FASTinfo['turbulence_intensity_init'] = FASTinfo['turbulence_intensity']

    return FASTinfo

def get_bladelength(FASTinfo):

    if FASTinfo['FAST_template_name'] == 'NREL5MW':
        FASTinfo['bladeLength'] = 61.5
    elif FASTinfo['FAST_template_name'] == 'WP_0.75MW':
        FASTinfo['bladeLength'] = 23.75
    elif FASTinfo['FAST_template_name'] == 'WP_1.5MW':
        FASTinfo['bladeLength'] = 33.25
    elif FASTinfo['FAST_template_name'] == 'WP_3.0MW':
        FASTinfo['bladeLength'] = 49.5-2.475
    elif FASTinfo['FAST_template_name'] == 'WP_5.0MW':
        FASTinfo['bladeLength'] = 64.0-3.2
    else:
        raise Exception('Unknown FAST template.')

    return FASTinfo


# ========================================================================================================= #

# initialize design variables
def initialize_rotor_dv(FASTinfo, rotor):

    if FASTinfo['FAST_template_name'] == 'NREL5MW':
        rotor['chord_sub'] = np.array([3.2612, 4.5709, 3.3178,   1.4621])
        rotor['theta_sub'] = np.array([13.2783, 7.46036, 2.89317,   -0.0878099])

    elif FASTinfo['FAST_template_name'] == 'WP_0.75MW':
        rotor['chord_sub'] = np.array([1.392, 1.723, 1.132, 0.700])
        rotor['theta_sub'] = np.array([11.10, 6.35, 0.95, 0.08])

    elif FASTinfo['FAST_template_name'] == 'WP_1.5MW':
        rotor['chord_sub'] = np.array([1.949, 2.412, 1.585, 0.980])
        rotor['theta_sub'] = np.array([11.10, 6.35, 0.95, 0.08])

    elif FASTinfo['FAST_template_name'] == 'WP_3.0MW':
        rotor['chord_sub'] = np.array([2.756, 3.412, 2.242, 1.386])
        rotor['theta_sub'] = np.array([11.10, 6.35, 0.95, 0.08])

    elif FASTinfo['FAST_template_name'] == 'WP_5.0MW':
        rotor['chord_sub'] = np.array([3.564, 4.411, 2.898, 1.793])
        rotor['theta_sub'] = np.array([11.10, 6.35, 0.95, 0.08])

    else:
        raise Exception('Still need to add other wind turbine initial designs')

    rotor['r_max_chord'] = 1.0 / (len(rotor['chord_sub']) -1.0)

    rotor['sparT'] = np.array([0.05, 0.047754, 0.045376, 0.031085, 0.0061398])
    rotor['teT'] = np.array([0.1, 0.09569, 0.06569, 0.02569, 0.00569])

    return rotor

# ========================================================================================================= #

def DLC_call(dlc, wnd_list, wnd_list_type, rand_seeds, mws, num_sgp, parked_list):

    # for each possible dlc case
    # add .wnd files for each specified DLC

    # nominal .wnd file (not a DLC)
    if dlc == 'DLC_0_0':
        wnd_list.append('nom.wnd')

        for i in range(0, num_sgp):
            wnd_list_type.append('nonturb')
            parked_list.append('no')

    # turbulent DLCs
    if dlc == 'DLC_1_2':
        for i in range(1, len(rand_seeds) + 1):
            for j in range(0, len(mws)):

                inp_file_hh = 'dlc_{0}_seed{1}_mws{2}.hh'.format('NTM', i, int(mws[j]))
                wnd_list.append(inp_file_hh)

                for k in range(0, num_sgp):
                    wnd_list_type.append('turb')
                    parked_list.append('no')

    if dlc == 'DLC_1_3':
        for i in range(1, len(rand_seeds) + 1):
            for j in range(0, len(mws)):
                inp_file_hh = 'dlc_{0}_seed{1}_mws{2}.hh'.format('1ETM', i, int(mws[j]))
                wnd_list.append(inp_file_hh)

                for k in range(0, num_sgp):
                    wnd_list_type.append('turb')
                    parked_list.append('no')

    # nonturbulent DLCs
    if dlc == 'DLC_1_4':
        wnd_list.append('ECD+R+2.0.wnd')
        wnd_list.append('ECD+R-2.0.wnd')
        wnd_list.append('ECD-R+2.0.wnd')
        wnd_list.append('ECD-R-2.0.wnd')
        wnd_list.append('ECD+R.wnd')
        wnd_list.append('ECD-R.wnd')

        for i in range(0, num_sgp):
            wnd_list_type.append('nonturb')
            wnd_list_type.append('nonturb')
            wnd_list_type.append('nonturb')
            wnd_list_type.append('nonturb')
            wnd_list_type.append('nonturb')
            wnd_list_type.append('nonturb')

            parked_list.append('no')
            parked_list.append('no')
            parked_list.append('no')
            parked_list.append('no')
            parked_list.append('no')
            parked_list.append('no')

    if dlc == 'DLC_1_5':
        wnd_list.append('EWSH+12.0.wnd')
        wnd_list.append('EWSH-12.0.wnd')
        wnd_list.append('EWSV+12.0.wnd')
        wnd_list.append('EWSV-12.0.wnd')

        for i in range(0, num_sgp):
            wnd_list_type.append('nonturb')
            wnd_list_type.append('nonturb')
            wnd_list_type.append('nonturb')
            wnd_list_type.append('nonturb')

            parked_list.append('no')
            parked_list.append('no')
            parked_list.append('no')
            parked_list.append('no')

    if dlc == 'DLC_6_1':
        wnd_list.append('EWM50.wnd')

        for i in range(0, num_sgp):
            wnd_list_type.append('nonturb')
            parked_list.append('yes')

    if dlc == 'DLC_6_3':
        wnd_list.append('EWM01.wnd')

        for i in range(0, num_sgp):
            wnd_list_type.append('nonturb')
            parked_list.append('yes')

    return wnd_list, wnd_list_type

# ========================================================================================================= #

def Calc_max_DEMs(FASTinfo, rotor):

    # from FASTinfo, get number of wind files
    caseids = []
    for i in range(0, len(FASTinfo['wnd_list'])):
        caseids.append("WNDfile{0}".format(i + 1))

    # create array to hold all DEMs (for each wnd_file)
    DEMx_master_array = np.zeros([len(FASTinfo['wnd_list']), 18])
    DEMy_master_array = np.zeros([len(FASTinfo['wnd_list']), 18])

    for i in range(0, len(FASTinfo['wnd_list'])):

        DEMrange = [0, 1, 8, 15]
        sgp_range = [1, 1, 2, 3]

        lines_x = []
        lines_y = []

        for j in DEMrange:

            if j == DEMrange[0]:
                sgp = sgp_range[0]
            elif j == DEMrange[1]:
                sgp = sgp_range[1]
            elif j == DEMrange[2]:
                sgp = sgp_range[2]
            elif j == DEMrange[3]:
                sgp = sgp_range[3]

            # spec_wnd_dir = FASTinfo['description'] + '/' + 'sgp' + str(sgp) + '/' + caseids[i - 1] + '_sgp' + str(sgp)
            spec_wnd_dir = FASTinfo['description'] + '/' + 'sgp' + str(sgp) + '/' + caseids[i] + '_sgp' + str(sgp)

            # FAST_wnd_directory = ''.join((FASTinfo['path'], 'RotorSE_FAST/' \
            #                                                 'RotorSE/src/rotorse/FAST_Files/Opt_Files/', spec_wnd_dir))
            FAST_wnd_directory = ''.join((FASTinfo['path'], 'blade-damage/Opt_Files/', spec_wnd_dir))


            # xDEM / yDEM files

            if j == 0:
                xDEM_file = FAST_wnd_directory + '/' + 'xRoot.txt'
                yDEM_file = FAST_wnd_directory + '/' + 'yRoot.txt'
            else:
                xDEM_file = FAST_wnd_directory + '/' + 'xDEM_' + str(j) + '.txt'
                yDEM_file = FAST_wnd_directory + '/' + 'yDEM_' + str(j) + '.txt'

            lines_x.append([line.rstrip('\n') for line in open(xDEM_file)])
            lines_y.append([line.rstrip('\n') for line in open(yDEM_file)])

        xDEM = []
        yDEM = []

        for j in range(0, 4):
            for k in range(0, len(lines_x[j])):
                xDEM.append(float(lines_x[j][k]))

        for j in range(0, 4):
            for k in range(0, len(lines_y[j])):
                yDEM.append(float(lines_y[j][k]))

        xDEM = np.array(xDEM)
        yDEM = np.array(yDEM)

        DEMx_master_array[i][0:18] = xDEM
        DEMy_master_array[i][0:18] = yDEM

    # create DEM plots using DEMx_master_array, DEMy_master_array
    FASTinfo['createDEMplot'] = False

    if FASTinfo['createDEMplot']:

        plt.figure()
        plt.xlabel('strain gage position')
        plt.ylabel('DEM (kN*m)')
        plt.title('DEMx for various input .wnd files')  #: Bending Moment at Spanwise Station #1, Blade #1')
        for i in range(6): # 0, len(FASTinfo['wnd_list'])):
            plt.plot(DEMx_master_array[i][0:18], label=FASTinfo['wnd_list'][i])

            print(DEMx_master_array[i][0:18])

        plt.legend()
        plt.xticks(np.linspace(0,17,18))
        plt.savefig(FASTinfo['dir_saved_plots'] + '/DEMx_dif_wnd_files.png')
        plt.show()

        quit()

    # From DEMx_master_array, DEMy_master_array, determine DEMx_max, DEMy_max
    DEMx_max = np.zeros([1 + len(rotor['r_aero']), 1])
    DEMy_max = np.zeros([1 + len(rotor['r_aero']), 1])

    # DEMx_max_wnd_list = np.zeros([len(DEMx_max),1])
    DEMx_max_wnd_list = []
    DEMy_max_wnd_list = []

    for i in range(0, len(DEMx_max)):
        for j in range(0, len(FASTinfo['wnd_list'])):

            # determine max DEMx
            if DEMx_max[i] < DEMx_master_array[j][i]:
                # add name of .wnd file
                DEMx_max_wnd_list.append(FASTinfo['wnd_list'][j])

                # set max DEM
                DEMx_max[i] = DEMx_master_array[j][i]

            # determine max DEMy
            if DEMy_max[i] < DEMy_master_array[j][i]:
                # add name of .wnd file
                # DEMy_max_wnd_list[i] = FASTinfo['wnd_list'][j]
                DEMy_max_wnd_list.append(FASTinfo['wnd_list'][j])

                # set max DEM
                DEMy_max[i] = DEMy_master_array[j][i]

    # create list of active .wnd files at current design
    DEM_master_wnd_list = []
    for i in range(0, len(DEMx_max)):
        if not (DEMx_max_wnd_list[i] in DEM_master_wnd_list):
            DEM_master_wnd_list.append(DEMx_max_wnd_list[i])
    for i in range(0, len(DEMy_max)):
        if not (DEMy_max_wnd_list[i] in DEM_master_wnd_list):
            DEM_master_wnd_list.append(DEMy_max_wnd_list[i])

    active_wnd_file = FASTinfo['opt_dir'] + '/' + 'active_wnd.txt'
    file_wnd = open(active_wnd_file, "w")
    for j in range(0, len(DEM_master_wnd_list)):
        # write to xDEM file
        file_wnd.write(str(DEM_master_wnd_list[j]) + '\n')
    file_wnd.close()

    Mxb_damage = DEMx_max * 10.0 ** 3.0  # kN*m to N*m
    Myb_damage = DEMy_max * 10.0 ** 3.0  # kN*m to N*m

    # xDEM/yDEM files
    xDEM_file = FASTinfo['opt_dir'] + '/' + 'xDEM_max.txt'
    file_x = open(xDEM_file, "w")
    for j in range(0, len(Mxb_damage)):
        # write to xDEM file
        file_x.write(str(Mxb_damage[j][0]) + '\n')
    file_x.close()

    yDEM_file = FASTinfo['opt_dir'] + '/' + 'yDEM_max.txt'
    file_y = open(yDEM_file, "w")
    for j in range(0, len(Myb_damage)):
        # write to xDEM file
        file_y.write(str(Myb_damage[j][0]) + '\n')
    file_y.close()

    if FASTinfo['make_max_DEM_files']:
        quit()

# ========================================================================================================= #

def Use_FAST_DEMs(FASTinfo, rotor):

    # set rotor parameters
    rotor['rstar_damage'] = np.insert(rotor['r_aero'], 0, 0.0)
    rotor['rstar_damage'] = np.array([0.000, 0.022, 0.067, 0.111, 0.167, 0.233, 0.300, 0.367, 0.433, 0.500,
              0.567, 0.633, 0.700, 0.767, 0.833, 0.889, 0.933, 0.978])
    # set DEM parameters
    DEMx_max = np.zeros([len(rotor['rstar_damage']), 1])
    DEMy_max = np.zeros([len(rotor['rstar_damage']), 1])

    fx = open(FASTinfo['max_DEMx_file'], "r")

    linesx = fx.readlines()
    for i in range(len(linesx)):
        DEMx_max[i] = float(linesx[i])
    fx.close()

    fy = open(FASTinfo['max_DEMy_file'], "r")

    linesy = fy.readlines()
    for i in range(len(linesy)):
        DEMy_max[i] = float(linesy[i])
    fy.close()

    # print(DEMx_max)
    # print(DEMy_max)
    # quit()

    rotor['Mxb_damage'] = DEMx_max
    rotor['Myb_damage'] = DEMy_max

    if FASTinfo['check_opt_DEMs']:
        plot_DEMs(rotor, FASTinfo)


    return rotor

# ========================================================================================================= #

def plot_DEMs(rotor, FASTinfo):

    print(rotor['Mxb_damage']/1000.0)
    print(rotor['Myb_damage']/1000.0)
    print(rotor['rstar_damage'])
    quit()

    plt.figure()
    plt.plot(rotor['rstar_damage'], rotor['Mxb_damage']/1000.0, label='DEMx')
    plt.plot(rotor['rstar_damage'], rotor['Myb_damage']/1000.0, label='DEMy')

    plt.title('Maximum DEMs')
    plt.ylabel('DEM (kN*m)')
    plt.xlabel('Blade Fraction')

    plt.legend()

    plt.savefig(FASTinfo['dir_saved_plots'] + '/DEM_max_plot.png')

    plt.show()

    quit()

# ========================================================================================================= #

def add_outputs(FASTinfo):

    FASTinfo['output_list'] = []

    # OutputList = open("FAST_Files/FASTOutputList_full.txt", 'r')
    OutputList = open("FAST_Files/FASTOutputList.txt", 'r')

    lines = OutputList.read().split('\n')

    for i in range(0, len(lines)):  # in OutputList:
        FASTinfo['output_list'].append(lines[i])

    return FASTinfo

# ========================================================================================================= #

def extract_results(rotor,FASTinfo):

    # results file name
    opt_dir = FASTinfo['opt_dir']

    file_name = opt_dir + '/' + 'opt_results.txt'

    resultsfile = open(file_name, 'w')

    # design variables
    resultsfile.write(str(rotor['r_max_chord']) + '\n' )
    resultsfile.write(str(rotor['chord_sub']) + '\n' )
    resultsfile.write(str(rotor['theta_sub']) + '\n' )
    resultsfile.write(str(rotor['sparT']) + '\n' )
    resultsfile.write(str(rotor['teT']) + '\n' )

    resultsfile.close()

# ========================================================================================================= #

def remove_sm_dir(FASTinfo):

    spec_point = FASTinfo['sm_var_spec']

    dir_name = FASTinfo['opt_dir'] + '/sm_' + str(spec_point)

    shutil.rmtree(dir_name)

# ========================================================================================================= #

def removed_fixcalc_dir(FASTinfo):

    for i in range(1,5):

        dir_name = FASTinfo['opt_dir'] + '/sgp' + str(i)

        if os.path.isdir(dir_name):

            shutil.rmtree(dir_name)

# ========================================================================================================= #

def remove_fixcalc_unnecessary_files(FASTinfo):

    for i in range(1,5):

        dir_name = FASTinfo['opt_dir'] + '/sgp' + str(i)

        if 'wnd_number' in FASTinfo:
            wnd_dir_name = dir_name + '/WNDfile' + str(FASTinfo['wnd_number']) + '_sgp' + str(i)
        else:
            wnd_dir_name = dir_name + '/WNDfile' + str(1) + '_sgp' + str(i)

        if os.path.isdir(wnd_dir_name):

            # remove files
            try:
                shutil.rmtree(wnd_dir_name + '/AeroData')
            except:
                pass

            file_list = ['/fst_runfile.fsm', '/fst_runfile.fst', '/fst_runfile.opt', '/fst_runfile.out',
                         '/fst_runfile.outb', '/fst_runfile_ADAMS.acf', '/fst_runfile_ADAMS.acf',
                         '/fst_runfile_ADAMS.adm', '/fst_runfile_ADAMS_LIN.acf',
                         '/' + FASTinfo['FAST_template_name'] + '_ADAMSSpecific.dat',
                         '/' + FASTinfo['FAST_template_name'] + '_AD.ipt',
                         '/' + FASTinfo['FAST_template_name'] + '_Blade.dat',
                         '/' + FASTinfo['FAST_template_name'] + '_Linear.dat',
                         '/' + FASTinfo['FAST_template_name'] + '_Tower.dat',
                         '/' + FASTinfo['FAST_template_name'] + '.fst',
                         '/Pitch.ipt']

            for i in range(len(file_list)):
                try:
                    os.remove(wnd_dir_name + file_list[i])
                except:
                    pass


# ========================================================================================================= #

def test_dif_turbine(FASTinfo, rotor, turbine_name):

    if turbine_name == 'TUM335MW':

        # number of blades
        FASTinfo['nBlades'] = 3
        rotor['nBlades'] = 3

        # turbine class
        FASTinfo['turbine_class'] = 'I'
        rotor['turbine_class'] = 'I'

        # turbulence class
        FASTinfo['turbulence_class'] = 'B'
        rotor['turbulence_class'] = 'B'

        # blade length
        FASTinfo['bladeLength'] = 63.5
        rotor['bladeLength'] = 63.5

        # chord distribution
        f = open('FAST_Files/TUM_Files/TUM_335MW_chord.txt', "r")
        lines = f.readlines()
        chord_dist = np.zeros([len(lines)])
        for i in range(len(chord_dist)):
            chord_dist[i] = float(lines[i])
        f.close()

        f = open('FAST_Files/TUM_Files/TUM_335MW_chord_pos.txt', "r")
        lines = f.readlines()
        chord_pos = np.zeros([len(lines)])
        for i in range(len(chord_pos)):
            chord_pos[i] = float(lines[i])
        f.close()
        chord_pos = (chord_pos-chord_pos[0])/(chord_pos[-1]-chord_pos[0])

        chord_pos_plot = chord_pos
        chord_dist_plot = chord_dist

        rotor_points = np.linspace(0,1,len(rotor['chord_sub']))
        points17 = np.linspace(0,1,17)

        chord_spline = Akima(chord_pos, chord_dist)
        rotor['chord_sub'] = chord_spline.interp(rotor_points)[0]/1000.0 # mm to m

        rotor_spline = Akima(rotor_points, rotor['chord_sub'])
        rotor_chord_plot = rotor_spline.interp(points17)[0]

        plot_TUM = 0
        if plot_TUM:
            plt.figure()
            plt.plot(chord_pos_plot, chord_dist_plot/1000.0, label='TUM 3.35 MW Chord Distribution') # mm to m
            plt.plot(points17, rotor_chord_plot, '--x', label='RotorSE Chord Distribution Approximation')

            plt.title('TUM 3.35MW Chord Approximation')
            plt.xlabel('Blade Fraction')
            plt.ylabel('Chord Length (m)')
            plt.legend()

            plt.savefig(FASTinfo['dir_saved_plots'] + '/tum_chord.png')

            # plt.show()
            plt.close()

        # twist distribution
        f = open('FAST_Files/TUM_Files/TUM_335MW_twist.txt', "r")
        lines = f.readlines()
        twist_dist = np.zeros([len(lines)])
        for i in range(len(twist_dist)):
            twist_dist[i] = float(lines[i])
        f.close()

        f = open('FAST_Files/TUM_Files/TUM_335MW_twist_pos.txt', "r")
        lines = f.readlines()
        twist_pos = np.zeros([len(lines)])
        for i in range(len(twist_pos)):
            twist_pos[i] = float(lines[i])
        f.close()
        twist_pos = (twist_pos-twist_pos[0])/(twist_pos[-1]-twist_pos[0])

        twist_pos_plot = twist_pos
        twist_dist_plot = twist_dist


        rotor_points = np.linspace(0,1,len(rotor['theta_sub']))
        points17 = np.linspace(0,1,17)

        twist_spline = Akima(twist_pos, twist_dist)
        rotor['theta_sub'] = twist_spline.interp(rotor_points)[0]

        rotor_spline = Akima(rotor_points, rotor['theta_sub'])
        rotor_twist_plot = rotor_spline.interp(points17)[0]

        if plot_TUM:
            plt.figure()
            plt.plot(twist_pos_plot, twist_dist_plot, label='TUM 3.35 MW Twist Distribution')
            plt.plot(points17, rotor_twist_plot, '--x', label='RotorSE Twist Distribution Approximation')

            plt.title('TUM 3.35MW Twist Approximation')
            plt.xlabel('Blade Fraction')
            plt.ylabel('Twist (deg)')
            plt.legend()

            plt.savefig(FASTinfo['dir_saved_plots'] + '/tum_twist.png')

            # plt.show()
            plt.close()
            quit()

        # airfoil selection
        basepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'FAST_Files/TUM_Files/TUM335_AFFiles')

        # load all airfoils
        airfoil_types = [0] * 8
        airfoil_types[0] = os.path.join(basepath, 'circle.dat')
        airfoil_types[1] = os.path.join(basepath, 'circle.dat')
        airfoil_types[2] = os.path.join(basepath, 'FX77-W-500.dat')
        airfoil_types[3] = os.path.join(basepath, 'FX77-W-400.dat')
        airfoil_types[4] = os.path.join(basepath, 'DU00-W2-350.dat')
        airfoil_types[5] = os.path.join(basepath, 'DU97-W-300.dat')
        airfoil_types[6] = os.path.join(basepath, 'DDU91-W2-250.dat')
        airfoil_types[7] = os.path.join(basepath, 'DU08-W-210.dat')


        rotor['airfoil_types'] = airfoil_types  # (List): names of airfoil file or initialized CCAirfoils

        rotor['af_idx'] = np.array([0, 0, 1, 2, 3, 3, 4, 5, 5, 6, 6, 7, 7, 7, 7, 7, 7])
        rotor['af_str_idx'] = np.array(
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 3, 3, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7,
             7, 7])


    return FASTinfo, rotor

# ========================================================================================================= #
