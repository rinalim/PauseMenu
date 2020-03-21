import sys, os, time
import xml.etree.ElementTree as ET
from subprocess import *
import ast

if os.path.isdir('/opt/retropie') == True:
    OPT = '/opt/retropie'
elif os.path.isdir('/opt/retroarena') == True:
    OPT = '/opt/retroarena'
PATH_PAUSEMENU = OPT+'/configs/all/PauseMenu/'
if os.path.isdir('/home/pi/RetroPie') == True:
    FBA_ROMPATH = '/home/pi/RetroPie/roms/fba/'
elif os.path.isdir('/home/pigaming/RetroArena') == True:
    FBA_ROMPATH = '/home/pigaming/RetroArena/roms/fba/'

retroarch_key = {}
user_key = {}
key_map = {}
turbo_key = ''

capcom_dd = ['ddtod', 'ddsom']

sys_map = {
    "lr-fbneo": "FinalBurn Neo",
    "lr-fbalpha": "FB Alpha"
}

def run_cmd(cmd):
# runs whatever in the cmd variable
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

def load_layout():

    global retroarch_key

    #' -(1)-----  -(2)-----  -(3)----- '
    #' | X Y L |  | Y X L |  | L Y X | '
    #' | A B R |  | B A R |  | R B A | '
    #' ---------  ---------  --------- '

    f = open(PATH_PAUSEMENU+"images/control/layout.cfg", 'r')
    es_conf = int(f.readline())
    f.close()

    if es_conf == 1:
        user_key['1'] = 'x'
        user_key['2'] = 'y'
        user_key['3'] = 'l'
        user_key['4'] = 'a'
        user_key['5'] = 'b'
        user_key['6'] = 'r'
    elif es_conf == 2:
        user_key['1'] = 'y'
        user_key['2'] = 'x'
        user_key['3'] = 'l'
        user_key['4'] = 'b'
        user_key['5'] = 'a'
        user_key['6'] = 'r'
    elif es_conf == 3:
        user_key['1'] = 'l'
        user_key['2'] = 'y'
        user_key['3'] = 'x'
        user_key['4'] = 'r'
        user_key['5'] = 'b'
        user_key['6'] = 'a'

    f = open(PATH_PAUSEMENU+"button.cfg", 'r')
    retroarch_key = ast.literal_eval(f.readline())
    f.close()

def set_keymap(romname, layout_index):
    
    global turbo_key
    
    if layout_index[2] == '2':    # capcom fighting game
        if layout_index[0] == '1':
            key_map['1'] = user_key['1']     # LP
            key_map['9'] = user_key['2']     # MP
            key_map['10'] = user_key['3']    # HP
            key_map['0'] = user_key['4']     # LK
            key_map['8'] = user_key['5']     # MK
            key_map['11'] = user_key['6']    # HK
        elif layout_index[0] == '2':
            key_map['1'] = user_key['4']
            key_map['9'] = user_key['5']
            key_map['10'] = user_key['6']
            key_map['0'] = user_key['1']
            key_map['8'] = user_key['2']
            key_map['11'] = user_key['3']
    elif romname in capcom_dd:
        if layout_index[0] == '1':
            key_map['0'] = user_key['4']    # A
            key_map['8'] = user_key['5']    # B
            key_map['1'] = user_key['2']    # C
            key_map['9'] = user_key['1']    # D
        elif layout_index[0] == '2':
            key_map['0'] = user_key['1']
            key_map['8'] = user_key['2']
            key_map['1'] = user_key['5']
            key_map['9'] = user_key['4']
        elif layout_index[0] == '3':
            key_map['0'] = user_key['4']
            key_map['8'] = user_key['5']
            key_map['1'] = user_key['1']
            key_map['9'] = user_key['6']
            key_map['10'] = user_key['2']
    else:
        if layout_index[0] == '1':
            key_map['0'] = user_key['4']    # A
            key_map['8'] = user_key['5']    # B
            key_map['1'] = user_key['1']    # C
            key_map['9'] = user_key['2']    # D
        elif layout_index[0] == '2':
            key_map['0'] = user_key['1']
            key_map['8'] = user_key['2']
            key_map['1'] = user_key['4']
            key_map['9'] = user_key['5']
        elif layout_index[0] == '3':
            key_map['0'] = user_key['4']
            key_map['8'] = user_key['5']
            key_map['1'] = user_key['6']
            key_map['9'] = user_key['1']
            key_map['10'] = user_key['2']
        elif layout_index[0] == '4':
            key_map['0'] = user_key['4'] + user_key['5']
            key_map['8'] = user_key['1']
            key_map['1'] = user_key['2']
            turbo_key = retroarch_key[user_key['5']]
        elif layout_index[0] == '5':
            key_map['0'] = user_key['1'] + user_key['2'] 
            key_map['8'] = user_key['4']
            key_map['1'] = user_key['5']
            turbo_key = retroarch_key[user_key['2']]
        elif layout_index[0] == '6':
            key_map['0'] = user_key['4'] + user_key['1'] 
            key_map['8'] = user_key['5'] + user_key['2'] 
            key_map['1'] = user_key['6'] + user_key['3']
            turbo_key = retroarch_key[user_key['1']]


def update_fba_rmp(system, romname, index):

    if os.path.isdir(OPT + '/configs/fba/'+sys_map[system]) == False:
        run_cmd('mkdir ' + OPT + '/configs/fba/' + sys_map[system].replace(" ","\ "))
    buf = ''
    run_cmd("sed -i \'/input_player" + str(index) + "/d\' " + OPT + "/configs/fba/"+sys_map[system].replace(" ","\ ") + '/'  + romname + ".rmp")
    f = open(OPT + '/configs/fba/'+ sys_map[system] + '/'  + romname + '.rmp', 'a')
    for key in key_map:
        res = 'input_player' + str(index) + '_btn_' + key_map[key][0] + ' = ' + '\"' + key + '\"'
        buf += res + '\n'
        if len(key_map[key]) == 2:
            res = 'input_player' + str(index) + '_btn_' + key_map[key][1] + ' = ' + '\"' + key + '\"'
            buf += res + '\n'
    f.write(buf)
    f.close()
    if os.path.isfile(FBA_ROMPATH + romname + ".zip.cfg") == True:
        run_cmd("sed -i \'/input_player" + str(index) + "_turbo_btn/d\' " + FBA_ROMPATH + romname + ".zip.cfg")
    if turbo_key != '':
        run_cmd("echo 'input_player" + str(index) + "_turbo_btn = " + turbo_key + "' >> " + FBA_ROMPATH + romname + ".zip.cfg")
    if os.path.isdir('/home/pi/.config/retroarch/config/remaps') == True:
        run_cmd("cp -r '/opt/retropie/configs/fba/" + sys_map[system] + "' /home/pi/.config/retroarch/config/remaps")

if __name__ == "__main__":

    system = sys.argv[1]
    romname = sys.argv[2]
    layout_index = sys.argv[3]
    load_layout()
    set_keymap(romname, layout_index)
    update_fba_rmp(system, romname, 1)
