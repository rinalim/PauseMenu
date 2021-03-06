#-*-coding: utf-8 -*-
#!/usr/bin/python

import os, sys, struct, time, fcntl, termios, signal, keyboard, datetime
import curses, errno
from pyudev import Context
from subprocess import *
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
import ast

#    struct js_event {
#        __u32 time;     /* event timestamp in milliseconds */
#        __s16 value;    /* value */
#        __u8 type;      /* event type */
#        __u8 number;    /* axis/button number */
#    };

reload(sys)
sys.setdefaultencoding('utf-8')

JS_MIN = -32768
JS_MAX = 32768
JS_REP = 0.20

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

CONFIG_DIR = '/opt/retroarena/configs/'
RETROARCH_CFG = CONFIG_DIR + 'all/retroarch.cfg'
PATH_PAUSEMENU = CONFIG_DIR + 'all/PauseMenu/'
XML = PATH_PAUSEMENU+'images/control/xml/'
VIEWER = "sudo fbi -T 2 -d /dev/fb0 -noverbose -cachemem 0 /tmp/pause.png /tmp/pause_1.png /tmp/pause_2.png > /dev/null 2>&1"
VIEWER_LAYOUT = "pqiv -c -i -f --display=:0 /tmp/pause_layout.png"
VIEWER_BG = "pqiv -c -i -f -z 3 --display=:0 " + PATH_PAUSEMENU + "images/pause_bg.png"
#VIEWER_OSD = PATH_PAUSEMENU + "omxiv-pause /tmp/pause_osd.txt -f -t 5 -T blend --duration 20 -l 30001 -a center"
#VIEWER_OSD = PATH_PAUSEMENU + "omxiv-pause /tmp/pause.txt -f -t 5 -T blend --duration 20 -l 30001 -a center --win 724,608,1024,768"

SELECT_BTN_ON = False
START_BTN_ON = False
UP_ON = False
DOWN_ON = False
PAUSE_MODE_ON = False

VIEW_MODE = "default"
MENU_INDEX = 0
STATE_INDEX = 0
LAYOUT_INDEX = 0

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []
btn_select = -1
btn_start = -1
btn_pausemenu = -1
btn_a = -1
btn_x = -1
button_num = 0
layout_num = 0

retroarch_key = {}
user_key = {}
btn_map = {}
kor_map = {
    "Jab": "약",
    "Strong": "중",
    "Fierce": "강",
    "Short": "약",
    "Roundhouse": "강",
    "Light": "약",
    "Middle": "중",
    "Heavy": "강",
    "Punch": "펀치",
    "Kick": "킥", 
    "Attack": "공격",
    "Jump": "점프",
    "Select": "선택",
    "Magic": "마법",
    "Fire": "총알",
    "Loop": "회전",
    "Bubble": "방울",
    "Left": "왼쪽",
    "Center": "가운데",
    "Right": "오른쪽",
    " - ": "-"
}
sys_map = {
    "lr-fbneo": "FinalBurn Neo",
    "lr-fbalpha": "FB Alpha"
}
es_conf = 1
romname = ""
sysname = ""
corename = ""

capcom_dd = ['ddtod', 'ddsom']


def run_cmd(cmd):
    # runs whatever in the cmd variable
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

def update_image(src, dst):
    if os.path.isfile(src) == True:
        os.system('rm ' + dst)
        os.system('cp "' + src + '" ' + dst)
        prev_size = 0
        counts = 0
        while True:
            cur_size = os.path.getsize(dst)
            if cur_size > prev_size:
                keyboard.press("n")
                time.sleep(0.01)
                keyboard.release("n")
                break
            else:
                counts = counts+1
                if counts >= 5:
                    break
                else:
                    time.sleep(0.3) 

def generate_image(src, dst):
    if os.path.isfile(dst) == False:
        target = images_snap.copy()
        target.paste(src, (0,0), src)
        target.save(dst)

def check_update(system):
    
    if system != 'lr-fbneo' and system != 'lr-fbalpha':
        return False
    
    RESUME = PATH_PAUSEMENU + "images/control/" + sysname + "/" + romname + '_layout0.png'
    CORECFG = CONFIG_DIR + 'fba/' + sys_map[system] + '/' + sys_map[system] + '.rmp'
    GAMECFG = CONFIG_DIR + 'fba/' + sys_map[system] + '/' + romname + '.rmp'
   
    if os.path.isfile(RESUME) == False:
        return True
    else:
        _time = os.path.getmtime(RESUME)
        if _time < os.path.getmtime(PATH_PAUSEMENU + "images/control/"+'layout.cfg'):
            return True
        if os.path.isfile(XML+romname+'.xml') == True:
            if _time < os.path.getmtime(XML+romname+'.xml'):
                return True
        if os.path.isfile(CORECFG) == True:
            if _time < os.path.getmtime(CORECFG):
                return True
        if os.path.isfile(GAMECFG) == True:
            if _time < os.path.getmtime(GAMECFG):
                return True
        
    # print 'No need to update PNG'
    return False

def full_arg():
    if len(sys.argv) > 2 and sys.argv[2] == '-full':
        return True
    else:
        return False

def load_button():

    global retroarch_key

    f = open(PATH_PAUSEMENU + "button.cfg", 'r')
    retroarch_key = ast.literal_eval(f.readline())
    f.close()

def load_layout():

    global es_conf, user_key

    #' -(1)-----  -(2)-----  -(3)----- '
    #' | X Y L |  | Y X L |  | L Y X | '
    #' | A B R |  | B A R |  | R B A | '
    #' ---------  ---------  --------- '

    f = open(PATH_PAUSEMENU + "images/control/layout.cfg", 'r')
    es_conf = int(f.readline())

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

    f.close()

def get_info():

    #INPUT = './controls.xml'   
    if os.path.isfile(XML+romname+'.xml') == False:
        #print 'No xml found'
        name = romname
        buttons = ['A 버튼', 'B 버튼', 'C 버튼', 'D 버튼', 'None', 'None']
        button_num = 4
    else:
        doc = ET.parse(XML+romname+'.xml')
        game = doc.getroot()
    #game = root.find('./game[@romname=\"' + romname + '\"]')
    #if game == None:
        #print 'No Game Found'
        name = str(unicode(game.get('gamename')))
        #print 'Generate pause images for ' + name
        player = game.find('player')
        controls = player.find('controls')
        labels = player.findall('labels')
        buttons = []
        button_num = 0
        for i in labels[0]:
            if 'BUTTON' in i.get('name'):
                btn = str(unicode(i.get('value')))
                # Translate to Korean
                for key in kor_map:
                    if key in btn:
                        btn = btn.replace(key, kor_map[key])
                #btn = btn[:10]
                if btn == '':
                    btn = "None"
                buttons.append(btn)
                button_num = button_num+1
                #print i.get('name'), btn
        for j in range(len(buttons), 6):
            buttons.append("None")
    if button_num == 6:
        layout_num = 2
    elif romname in capcom_dd:
        layout_num = 3
    else:
        layout_num = 6
            
    return buttons, button_num, layout_num

def get_btn_layout(buttons):

    # FBA button sequence   
    btn_map['b'] = '"0"'
    btn_map['a'] = '"8"'
    btn_map['y'] = '"1"'
    btn_map['x'] = '"9"'
    btn_map['l'] = '"10"'
    btn_map['r'] = '"11"'

    #if os.path.isfile(CONFIG_DIR + 'fba/FinalBurn Neo/' + romname + '.rmp') == True:
    if os.path.isfile(CONFIG_DIR + 'fba/' + sys_map[corename] + '/' + romname + '.rmp') == True:
        #print 'Use game specific setting'
        #f = open(CONFIG_DIR + 'fba/FinalBurn Neo/' + romname + '.rmp', 'r')
        f = open(CONFIG_DIR + 'fba/' + sys_map[corename] + '/' + romname + '.rmp', 'r')
        while True:
            line = f.readline()
            if not line: 
                break
            if 'btn' not in line:
                continue
            line = line.replace('\n','')
            line = line.replace('input_','')
            line = line.replace('_btn','')
            line = line.replace('=','')
            words = line.split()
            if 'player1' in words[0]:    # input_player1_btn_a = "1"
                btn_map[words[0][8]] = words[1]  
        f.close()

    #elif os.path.isfile(CONFIG_DIR + 'fba/FinalBurn Neo/FinalBurn Neo.rmp') == True:
    elif os.path.isfile(CONFIG_DIR + 'fba/' + sys_map[corename] + '/' + sys_map[corename] + '.rmp') == True:
        #print 'Use FinalBurn remap setting'
        #f = open(CONFIG_DIR + 'fba/FinalBurn Neo/FinalBurn Neo.rmp', 'r')
        f = open(CONFIG_DIR + 'fba/' + sys_map[corename] + '/' + sys_map[corename] + '.rmp', 'r')
        while True:
            line = f.readline()
            if not line: 
                break
            if 'btn' not in line:
                continue
            line = line.replace('\n','')
            line = line.replace('input_','')
            line = line.replace('_btn','')
            line = line.replace('=','')
            words = line.split()
            if 'player1' in words[0]:    # input_player1_btn_a = "1"
                btn_map[words[0][8]] = words[1]  
        f.close()

    #print btn_map

    # Convert from the FBA sequence to the normal sequence (0~5)
    convert = {}

    if button_num == 6:
        convert['"0"'] = 3
        convert['"8"'] = 4
        convert['"1"'] = 0
        convert['"9"'] = 1
        convert['"10"'] = 2
        convert['"11"'] = 5
    elif romname in capcom_dd:
        convert['"0"'] = 0
        convert['"8"'] = 1
        convert['"1"'] = 3
        convert['"9"'] = 2
        convert['"10"'] = 4
        convert['"11"'] = 5
    else:
        convert['"0"'] = 0
        convert['"8"'] = 1
        convert['"1"'] = 2
        convert['"9"'] = 3
        convert['"10"'] = 4
        convert['"11"'] = 5 

    # Map the button sequnece and the button description   
    btn_map['a'] = buttons[convert[btn_map['a']]]
    btn_map['b'] = buttons[convert[btn_map['b']]]
    btn_map['x'] = buttons[convert[btn_map['x']]]
    btn_map['y'] = buttons[convert[btn_map['y']]]
    btn_map['l'] = buttons[convert[btn_map['l']]]
    btn_map['r'] = buttons[convert[btn_map['r']]]
    #print btn_map

def get_location():
    if is_running("bin/retroarch") == True:
        game_conf = run_cmd("ps -ef | grep emulators | grep -v grep | awk '{print $13}'").rstrip()+".cfg"
        if os.path.isfile(game_conf) == True:
            res = run_cmd("cat " + game_conf + " | grep video_rotation").replace("\n","")
            if len(res) > 1:
                if res.split(' ')[2] == '"1"':
                    return " -o 270"
                elif res.split(' ')[2] == '"3"':
                    return " -o 90"
            #else:
            #    print "No game conf"
        sys_conf = run_cmd("ps -ef | grep emulators | grep -v grep | awk '{print $12}'").rstrip()
        res = run_cmd("cat " + sys_conf + " | grep video_rotation").replace("\n","")
        if len(res) > 1:
            if res.split(' ')[2] == '"1"':
                return " -o 270"
            elif res.split(' ')[2] == '"3"':
                return " -o 90"
    return ""

def get_turbo_key():
    rom_config = run_cmd("ps -ef | grep bin/retroarch | grep -v grep | awk '{print $13}'").replace("\n","")+".cfg"
    if os.path.isfile(rom_config) == True:
        line = run_cmd("cat " + rom_config + " | grep input_player1_turbo_btn")
        if len(line.split()) == 3:
            return line.split()[2]
    return '-1'

def draw_text(text, outfile):
    font_size = 54
    font = ImageFont.truetype('NanumBarunGothicBold.ttf', font_size)
    image = Image.new('RGBA', (font.getsize(unicode(text))[0], font.getsize(unicode(text))[1]), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"
    draw.text((0,0), unicode(text), font=font, fill="black")
    image.save(outfile)

def draw_picture(buttons):

    LAYOUT = " " + PATH_PAUSEMENU + "images/control/fba/" + romname + '_layout'
    #OSD = " " + PATH_PAUSEMENU + "images/control/fba/" + romname + '_osd.png'

    get_btn_layout(buttons)

    # Generate OSD image
    #pos_osd = ["80x22+62+67", "80x22+142+41", "80x22+222+17", "80x22+62+132", "80x22+142+108", "80x22+222+82"]
    #for i in range(1,7):
    #    btn = btn_map[user_key[str(i)]]
    #    if btn != 'None':
    #        draw_text(btn, "/tmp/text.png")
    #        cmd = "composite -geometry " + pos_osd[i-1] + " /tmp/text.png" + OSD + OSD
    #        os.system(cmd)
    #cmd = "composite " + OSD + " " + PATH_PAUSEOPTION + "images/bg_control.png" + OSD
    #os.system(cmd)
    
    # Generate current layout image
    pos = ["80x22+320+188", "80x22+400+162", "80x22+480+138", "80x22+320+253", "80x22+400+229", "80x22+480+203"]
    cmd = "cp " + PATH_PAUSEMENU + "images/control/background/bg_layout0.png" + LAYOUT+"0.png"
    os.system(cmd)
    for i in range(1,7):
        btn = btn_map[user_key[str(i)]]
        if btn != 'None':
            # check turbo key
            if retroarch_key[user_key[str(i)]] == get_turbo_key():
                btn = btn+"*"
            draw_text(btn, "/tmp/text.png")
            cmd = "composite -geometry " + pos[i-1] + " /tmp/text.png" + LAYOUT+"0.png" + LAYOUT+"0.png"
            os.system(cmd)

    # Generate control setup images
    if button_num == 6:     # capcom fighting games
        for i in range(1,3):
            print_map = {}
            if i == 1:
                print_map['1'] = buttons[0]
                print_map['2'] = buttons[1]
                print_map['3'] = buttons[2]
                print_map['4'] = buttons[3]
                print_map['5'] = buttons[4]
                print_map['6'] = buttons[5] 
            elif i == 2:
                print_map['1'] = buttons[3]
                print_map['2'] = buttons[4]
                print_map['3'] = buttons[5]
                print_map['4'] = buttons[0]
                print_map['5'] = buttons[1]
                print_map['6'] = buttons[2] 
            cmd = "cp " + PATH_PAUSEMENU + "images/control/background/bg_layout0.png" + LAYOUT+str(i)+".png"
            os.system(cmd)
            for j in range(1,7):
                btn = print_map[str(j)]
                if btn != 'None':
                    draw_text(btn, "/tmp/text.png")
                    cmd = "composite -geometry " + pos[j-1] + " /tmp/text.png" + LAYOUT+str(i)+".png" + LAYOUT+str(i)+".png"
                    os.system(cmd)
            draw_text("[" + str(i) + "/2]", "/tmp/text.png")
            cmd = "composite -geometry " + "80x22+490+252" + " /tmp/text.png" + LAYOUT+str(i)+".png" + LAYOUT+str(i)+".png"
            os.system(cmd)
    elif romname in capcom_dd:
        for i in range(1,4):
            print_map = {}
            if i == 1:
                print_map['1'] = buttons[2]
                print_map['2'] = buttons[3]
                print_map['3'] = 'None'
                print_map['4'] = buttons[0]
                print_map['5'] = buttons[1]
                print_map['6'] = 'None' 
            elif i == 2:
                print_map['1'] = buttons[0]
                print_map['2'] = buttons[1]
                print_map['3'] = 'None'
                print_map['4'] = buttons[2]
                print_map['5'] = buttons[3]
                print_map['6'] = 'None'
            elif i == 3:
                print_map['1'] = buttons[3]
                print_map['2'] = 'None'
                print_map['3'] = 'None'
                print_map['4'] = buttons[0]
                print_map['5'] = buttons[1]
                print_map['6'] = buttons[2]
            cmd = "cp " + PATH_PAUSEMENU + "images/control/background/bg_layout0.png" + LAYOUT+str(i)+".png"
            os.system(cmd)
            for j in range(1,7):
                btn = print_map[str(j)]
                if btn != 'None':
                    draw_text(btn, "/tmp/text.png")
                    cmd = "composite -geometry " + pos[j-1] + " /tmp/text.png" + LAYOUT+str(i)+".png" + LAYOUT+str(i)+".png"
                    os.system(cmd)
            draw_text("[" + str(i) + "/3]", "/tmp/text.png")
            cmd = "composite -geometry " + "80x22+490+252" + " /tmp/text.png" + LAYOUT+str(i)+".png" + LAYOUT+str(i)+".png"
            os.system(cmd)
    else:
        for i in range(1,7):
            print_map = {}
            if i == 1:
                print_map['1'] = buttons[2]
                print_map['2'] = buttons[3]
                print_map['3'] = 'None'
                print_map['4'] = buttons[0]
                print_map['5'] = buttons[1]
                print_map['6'] = 'None' 
            elif i == 2:
                print_map['1'] = buttons[0]
                print_map['2'] = buttons[1]
                print_map['3'] = 'None'
                print_map['4'] = buttons[2]
                print_map['5'] = buttons[3]
                print_map['6'] = 'None'
            elif i == 3:
                print_map['1'] = buttons[3]
                print_map['2'] = 'None'
                print_map['3'] = 'None'
                print_map['4'] = buttons[0]
                print_map['5'] = buttons[1]
                print_map['6'] = buttons[2]
            elif i == 4:
                print_map['1'] = buttons[1]
                print_map['2'] = buttons[2]
                print_map['3'] = 'None'
                print_map['4'] = buttons[0]
                print_map['5'] = buttons[0]+'*'
                print_map['6'] = 'None' 
            elif i == 5:
                print_map['1'] = buttons[0]
                print_map['2'] = buttons[0]+'*'
                print_map['3'] = 'None'
                print_map['4'] = buttons[1]
                print_map['5'] = buttons[2]
                print_map['6'] = 'None'
            elif i == 6:
                print_map['1'] = buttons[0]+'*'
                print_map['2'] = buttons[1]
                print_map['3'] = buttons[2]
                print_map['4'] = buttons[0]
                print_map['5'] = buttons[1]
                print_map['6'] = buttons[2]
            cmd = "cp " + PATH_PAUSEMENU + "images/control/background/bg_layout0.png" + LAYOUT+str(i)+".png"
            os.system(cmd)
            for j in range(1,7):
                btn = print_map[str(j)]
                if btn != 'None':
                    draw_text(btn, "/tmp/text.png")
                    cmd = "composite -geometry " + pos[j-1] + " /tmp/text.png" + LAYOUT+str(i)+".png" + LAYOUT+str(i)+".png"
                    os.system(cmd)
            draw_text("[" + str(i) + "/6]", "/tmp/text.png")
            cmd = "composite -geometry " + "80x22+490+252" + " /tmp/text.png" + LAYOUT+str(i)+".png" + LAYOUT+str(i)+".png"
            os.system(cmd)

def send_hotkey(key, repeat):
    # Press and release "2" once before actual input (bug?)
    keyboard.press("2")
    time.sleep(0.1)
    keyboard.release("2")
    time.sleep(0.1)

    keyboard.press("2")
    time.sleep(0.1)
    
    for i in range(repeat):
        keyboard.press(key)
        time.sleep(0.1)
        keyboard.release(key)
        time.sleep(0.1)
    
    keyboard.release("2")
    time.sleep(0.1)
    
def start_viewer():

    global images_snap 

    os.system("rm " + PATH_PAUSEMENU + "images/fbdev/* > /dev/null 2>&1")

    if VIEW_MODE == "fba":
        submenu = "fba/"+romname
    else:
        submenu = "libretro"
    if os.path.isfile(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_resume.png") == True :
        #os.system("fbgrab -d /dev/fb0 " + PATH_PAUSEMENU + "images/fbdev/snapshot.png")
        os.system("fbcat /dev/fb0 > /tmp/snapshot.ppm")
        images_snap = Image.open("/tmp/snapshot.ppm")
        target = images_snap.copy()
        target.paste(images_resume, (0,0), images_resume)
        target.save("/tmp/pause.png")
        generate_image(images_stop, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_stop.png")
        os.system("cp /tmp/pause.png " + PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_resume.png")
        os.system("convert /tmp/snapshot.ppm /tmp/snapshot.png &")
        os.system(VIEWER + " &")

def stop_viewer():
    if is_running("fbi") == True:
        #os.system("sudo pkill fbi")
        #time.sleep(0.5)
        os.system("cp /tmp/snapshot.png /tmp/pause.png")
        keyboard.press("n")
        time.sleep(0.05)
        keyboard.release("n")
        time.sleep(0.05)
        os.system("sudo pkill -9 fbi")
        #keyboard.press("esc")
        #time.sleep(0.1)
        #keyboard.release("esc")
        
def change_viewer(menu, index):

    global images_save0, images_save1, images_save2, images_save3
    global images_load0, images_load1, images_load2, images_load3

    if VIEW_MODE == "fba":
        submenu = "fba/"+romname
    else:
        submenu = "libretro"
    if index == "0":
       state_index = "state"
    else:
       state_index = "state" + index

    if menu == "RESUME":
        update_image(PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_resume.png", "/tmp/pause.png")

    elif menu == "STOP":
        update_image(PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_stop.png", "/tmp/pause.png")
        if VIEW_MODE == "fba" or VIEW_MODE == "libretro":
            generate_image(images_reset, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_reset.png")

    elif menu == "RESET":
        update_image(PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_reset.png", "/tmp/pause.png")
        if VIEW_MODE == "fba" or VIEW_MODE == "libretro":
            generate_image(images_save0, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save0" + ".png")

    elif menu == "SAVE":
        update_image(PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save" + index + ".png", "/tmp/pause.png")
        if index == "0":
            generate_image(images_save1, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save1.png")
        if index == "1":
            generate_image(images_save2, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save2.png")
        if index == "2":
            generate_image(images_save3, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save3.png")
        if VIEW_MODE == "fba" or VIEW_MODE == "libretro":
            generate_image(images_load0, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_load0.png")

    elif menu == "LOAD":
        update_image(PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE +  "_load" + index + ".png", "/tmp/pause.png")
        if index == "0":
            generate_image(images_load1, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_load1.png")
        if index == "1":
            generate_image(images_load2, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_load2.png")
        if index == "2":
            generate_image(images_load3, PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_load3.png")
        if VIEW_MODE == "fba":
            generate_image(images_control1, PATH_PAUSEMENU + "images/fbdev/" + "_button1.png")

    elif menu == "BUTTON":
        if VIEW_MODE == "fba":
            update_image(PATH_PAUSEMENU + "images/fbdev/" + "_button" + index + ".png", "/tmp/pause.png")
            if index == "1" and layout_num >= 2:
                generate_image(images_control2, PATH_PAUSEMENU + "images/fbdev/" + "_button2.png")
            if index == "2" and layout_num >= 3:
                generate_image(images_control3, PATH_PAUSEMENU + "images/fbdev/" + "_button3.png")
            if index == "3" and layout_num >= 4:
                generate_image(images_control4, PATH_PAUSEMENU + "images/fbdev/" + "_button4.png")
            if index == "4" and layout_num >= 5:
                generate_image(images_control5, PATH_PAUSEMENU + "images/fbdev/" + "_button5.png")
            if index == "5" and layout_num >= 6:
                generate_image(images_control6, PATH_PAUSEMENU + "images/fbdev/" + "_button6.png")

def save_snapshot(index):
    if index == 0:
        pngname = "state.png"
        state = "state"
    else:
        pngname = "state" + str(index) + ".png"
        state = "state" + str(index)
    
    now = datetime.datetime.now()
    nowDatetime = now.strftime('%Y/%m/%d %H:%M:%S')
    font_size = 14
    font = ImageFont.truetype('FreeSans.ttf', font_size)
    image_date = Image.new('RGBA', (260, 20), (0, 0, 0, 256))
    draw = ImageDraw.Draw(image_date)
    w, h = draw.textsize(nowDatetime)
    draw.fontmode = "L" # "1"=normal, "L"=antialiasing
    draw.text(((260-w)/2,(20-h)/2-2), nowDatetime, font=font, fill="white")
    
    backgroud = Image.open(PATH_PAUSEMENU + "images/save/" + pngname, "r")
    backgroud.paste(image_date, (282, 304))
    
    pngpath = "/home/pigaming/RetroArena/roms/" + sysname + "/" + romname + "." + pngname
    if os.path.isfile(pngpath) == True:
        prev_size = 0
        counts = 0
        while True:
            cur_size = os.path.getsize(pngpath)
            if cur_size > prev_size:
                try:
                    image_thumb = Image.open(pngpath, "r")
                except:
                    print "Cannot read thumbnail"
                    prev_size = cur_size
                    time.sleep(0.3)
                else:
                    image_thumb_resize = image_thumb.resize((260, 195), Image.BICUBIC) # NEAREST, BILINEAR, BICUBIC, ANTIALIAS
                    backgroud.paste(image_thumb_resize, (282, 109))
                    break
            else:
                counts = counts+1
                if counts >= 5:
                    break
                else:
                    time.sleep(1)
        time.sleep(0.5)

    if os.path.isfile("/home/pigaming/RetroArena/roms/" + sysname + "/" + romname + "." + state) == True:
        backgroud.save(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + "." + pngname)
    else:
        #start_viewer_failed()
        pass #time.sleep(2)
        
    '''
    pngpath = "/home/pi/RetroPie/roms/" + sysname + "/" + romname + "." + pngname
    if os.path.isfile(pngpath):
        while True:
            if os.path.getsize(pngpath) > 0:
                break
            time.sleep(0.1)    
        cmd = "composite -geometry 260x195!+282+109 " + \
              pngpath + " " + \
              PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname_fix + "." + pngname + " " + \
              PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname_fix + "." + pngname 
        os.system(cmd)
    '''

def is_running(pname):
    ps_grep = run_cmd("ps -ef | grep " + pname + " | grep -v grep")
    if len(ps_grep) > 1 and "bash" not in ps_grep:
        return True
    else:
        return False
    
def kill_proc(name):
    ps_grep = run_cmd("ps -aux | grep " + name + "| grep -v 'grep'")
    if len(ps_grep) > 1: 
        os.system("killall " + name)

def signal_handler(signum, frame):
    close_fds(js_fds)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def get_devices():
    devs = []
    if sys.argv[1] == '/dev/input/jsX':
        for dev in os.listdir('/dev/input'):
            if dev.startswith('js'):
                devs.append('/dev/input/' + dev)
    else:
        devs.append(sys.argv[1])

    return devs

def open_devices():
    devs = get_devices()

    fds = []
    for dev in devs:
        try:
            fds.append(os.open(dev, os.O_RDONLY | os.O_NONBLOCK ))
        except:
            pass

    return devs, fds

def close_fds(fds):
    for fd in fds:
        os.close(fd)

def read_event(fd):
    while True:
        try:
            event = os.read(fd, event_size)
        except OSError, e:
            if e.errno == errno.EWOULDBLOCK:
                return None
            return False

        else:
            return event

def process_event(event):

    global SELECT_BTN_ON, START_BTN_ON, UP_ON, DOWN_ON
    global PAUSE_MODE_ON, MENU_INDEX, STATE_INDEX, LAYOUT_INDEX
    global images_save0, images_save1, images_save2, images_save3
    global images_load0, images_load1, images_load2, images_load3

    (js_time, js_value, js_type, js_number) = struct.unpack(event_format, event)

    # ignore init events
    if js_type & JS_EVENT_INIT:
        return False

    if js_type == JS_EVENT_AXIS and js_number <= 7:
        if js_number % 2 == 0:
            UP_ON = False
            DOWN_ON = False
            if js_value <= JS_MIN * JS_THRESH:
                if PAUSE_MODE_ON == True:
                    if MENU_INDEX == 4:
                        if STATE_INDEX > 0:
                            STATE_INDEX = STATE_INDEX-1
                            change_viewer("SAVE", str(STATE_INDEX))
                    elif MENU_INDEX == 5:
                        if STATE_INDEX > 0:
                            STATE_INDEX = STATE_INDEX-1
                            change_viewer("LOAD", str(STATE_INDEX))
                    elif MENU_INDEX == 6:
                        if LAYOUT_INDEX > 1:
                            LAYOUT_INDEX = LAYOUT_INDEX-1
                            change_viewer("BUTTON", str(LAYOUT_INDEX))
            if js_value >= JS_MAX * JS_THRESH:
                if PAUSE_MODE_ON == True:                     
                    if MENU_INDEX == 4:
                        if STATE_INDEX < 3:
                            STATE_INDEX = STATE_INDEX+1
                            change_viewer("SAVE", str(STATE_INDEX))
                    elif MENU_INDEX == 5:
                        if STATE_INDEX < 3:
                            STATE_INDEX = STATE_INDEX+1
                            change_viewer("LOAD", str(STATE_INDEX))
                    elif MENU_INDEX == 6:
                        if LAYOUT_INDEX < layout_num:
                            LAYOUT_INDEX = LAYOUT_INDEX+1
                            change_viewer("BUTTON", str(LAYOUT_INDEX))
        elif js_number % 2 == 1:
            if js_value <= JS_MIN * JS_THRESH:
                UP_ON = True
                DOWN_ON = False
                if PAUSE_MODE_ON == True:
                    if MENU_INDEX == 2:
                        MENU_INDEX = 1
                        change_viewer("RESUME", "-1")
                    elif MENU_INDEX == 3:
                        MENU_INDEX = 2
                        change_viewer("STOP", "-1")
                    elif MENU_INDEX == 4:
                        MENU_INDEX = 3
                        change_viewer("RESET", "0")
                    elif MENU_INDEX == 5:
                        MENU_INDEX = 4
                        STATE_INDEX = 0
                        change_viewer("SAVE", "0")
                    elif MENU_INDEX == 6:
                        MENU_INDEX = 5
                        STATE_INDEX = 0
                        change_viewer("LOAD", "0")
                #elif SELECT_BTN_ON == True:
                    #print "OSD mode on"
                    #start_viewer_osd()
            if js_value >= JS_MAX * JS_THRESH:
                DOWN_ON = True
                UP_ON = False
                if PAUSE_MODE_ON == True:
                    if MENU_INDEX == 1:
                        MENU_INDEX = 2
                        change_viewer("STOP", "-1")
                    elif MENU_INDEX == 2:
                        if VIEW_MODE != "default":
                            MENU_INDEX = 3
                            change_viewer("RESET", "-1")
                    elif MENU_INDEX == 3:
                        MENU_INDEX = 4
                        STATE_INDEX = 0
                        change_viewer("SAVE", "0")
                    elif MENU_INDEX == 4:
                        MENU_INDEX = 5
                        STATE_INDEX = 0
                        change_viewer("LOAD", "0")
                    elif MENU_INDEX == 5:
                        if VIEW_MODE == "fba":
                            MENU_INDEX = 6
                            LAYOUT_INDEX = 1
                            change_viewer("BUTTON", "1")
                #elif SELECT_BTN_ON == True:
                    #print "OSD mode off"
                    #stop_viewer()
        if js_value == 0:
            UP_ON = False
            DOWN_ON = False
    
    if js_type == JS_EVENT_BUTTON:
        if js_value == 1:
            if js_number == btn_a:
                if PAUSE_MODE_ON == True:
                    if MENU_INDEX == 1:
                        #print "Resume"
                        stop_viewer()
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                        PAUSE_MODE_ON = False
                    elif MENU_INDEX == 2:
                        #print "Kill"
                        stop_viewer()
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGINT")
                        close_fds(js_fds)
                        sys.exit(0)
                    elif MENU_INDEX == 3:
                        #print "Reset"
                        stop_viewer()
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                        send_hotkey("z", 1)
                        PAUSE_MODE_ON = False
                    elif MENU_INDEX == 4:
                        #print "Save"
                        stop_viewer()
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                        #start_viewer_saving()
                        send_hotkey("left", 3)
                        send_hotkey("right", STATE_INDEX)
                        send_hotkey("f2", 1)
                        save_snapshot(STATE_INDEX)
                        if STATE_INDEX == 0 :
                            os.system("rm " + PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save0" + ".png")
                            images_slot0 = Image.open(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state.png")
                            images_save0 = img_paste(images_bg,
                                Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png"),
                                images_slot0)
                            images_load0 = img_paste(images_bg,
                                Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png"),
                                images_slot0)
                        elif STATE_INDEX == 1 :
                            os.system("rm " + PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save1" + ".png")
                            images_slot1 = Image.open(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state1.png")
                            images_save1 = img_paste(images_bg,
                                Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png"),
                                images_slot1)
                            images_load1 = img_paste(images_bg,
                                Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png"),
                                images_slot1)
                        elif STATE_INDEX == 2 :
                            os.system("rm " + PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save2" + ".png")
                            images_slot2 = Image.open(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state2.png")
                            images_save2 = img_paste(images_bg,
                                Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png"),
                                images_slot2)
                            images_load0 = img_paste(images_bg,
                                Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png"),
                                images_slot2)
                        elif STATE_INDEX == 3 :
                            os.system("rm " + PATH_PAUSEMENU + "images/fbdev/" + VIEW_MODE + "_save3" + ".png")
                            images_slot3 = Image.open(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state3.png")
                            images_save3 = img_paste(images_bg,
                                Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png"),
                                images_slot3)
                            images_load0 = img_paste(images_bg,
                                Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png"),
                                images_slot3)
                        #stop_viewer()
                        PAUSE_MODE_ON = False
                    elif MENU_INDEX == 5:
                        #print "Load"
                        stop_viewer()
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                        send_hotkey("left", 3)
                        send_hotkey("right", STATE_INDEX)
                        send_hotkey("f4", 1)
                        PAUSE_MODE_ON = False
                    elif MENU_INDEX == 6:
                        #print "Button"
                        stop_viewer()
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGINT")
                        close_fds(js_fds)
                        cmd = "python " + PATH_PAUSEMENU + "KeyMapper.py " + corename + " " + romname + " " + str(LAYOUT_INDEX)+"/"+str(layout_num)
                        os.system(cmd)
                        sys.exit(0)
            elif js_number == btn_x:
                if PAUSE_MODE_ON == True:
                    #print "RGUI"
                    stop_viewer()
                    os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                    PAUSE_MODE_ON = False
                    send_hotkey("s", 1)
            elif js_number == btn_select:
                SELECT_BTN_ON = True
            elif js_number == btn_start:
                START_BTN_ON = True
            elif js_number == btn_pausemenu:
                SELECT_BTN_ON = True
                START_BTN_ON = True
            else:
                return False
        elif js_value == 0:
            if js_number == btn_select:
                SELECT_BTN_ON = False
            elif js_number == btn_start:
                START_BTN_ON = False
            elif js_number == btn_pausemenu:
                SELECT_BTN_ON = False
                START_BTN_ON = False
            else:
                return False
        
        if SELECT_BTN_ON == True and START_BTN_ON == True:
            #print "Select+Start Pushed"
            if PAUSE_MODE_ON == False:
                PAUSE_MODE_ON = True
                MENU_INDEX = 1    # Resume
                #stop_viewer()
                os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGSTOP &")
                start_viewer()
        #elif SELECT_BTN_ON == True and UP_ON == True:
            #print "OSD mode on"
            #if PAUSE_MODE_ON == False:
            #    start_viewer_osd()
        #elif SELECT_BTN_ON == True and DOWN_ON == True:
            #print "OSD mode off"
            #if PAUSE_MODE_ON == False:
            #    stop_viewer()

    return True

def img_paste(bg, fg, fg1=None):
    fg_trans = Image.new("RGBA", (int(res_x),int(res_y)))
    box = ((bg.size[0] - fg.size[0]) // 2, (bg.size[1] - fg.size[1]) // 2)
    fg_trans.paste(fg, box, fg)
    if fg1 != None:
        fg_trans.paste(fg1, box, fg1)
    bg_ret = Image.alpha_composite(bg,fg_trans)
    return bg_ret

def fbdev_setup():

    global images_resume, images_stop, images_reset, images_bg
    global images_save0, images_save1, images_save2, images_save3
    global images_load0, images_load1, images_load2, images_load3
    global images_control1, images_control2, images_control3, images_control4, images_control5, images_control6

    if os.path.isfile("/tmp/pause.png") == False :
        os.system("touch /tmp/pause.png")
    if os.path.isfile("/tmp/pause_1.png") == False :
        os.system("ln -s /tmp/pause.png /tmp/pause_1.png")
    if os.path.isfile("/tmp/pause_2.png") == False :
        os.system("ln -s /tmp/pause.png /tmp/pause_2.png")

    #images_bg = Image.open(PATH_PAUSEMENU + "images/pause_bg.png").resize((int(res_x),int(res_y)))
    images_bg = Image.new("RGBA", (int(res_x),int(res_y)), (0,0,0,180))

    if VIEW_MODE == "fba":
        submenu = "fba/"+romname
    else:
        submenu = "libretro"
    
    if VIEW_MODE == "fba" or VIEW_MODE == "libretro":
        images_layout0 = Image.open(PATH_PAUSEMENU + "images/control/" + submenu + "_layout0.png")
        images_resume = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_resume.png"),
            images_layout0)
        images_stop = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_stop.png"),
            images_layout0)
        images_reset = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_reset.png"),
            images_layout0)
        
        if os.path.isfile(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state.png") == True :
            images_slot0 = Image.open(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state.png")
        else:
            images_slot0 = Image.open(PATH_PAUSEMENU + "images/save/state.png")
        if os.path.isfile(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state1.png") == True :
            images_slot1 = Image.open(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state1.png")
        else:
            images_slot1 = Image.open(PATH_PAUSEMENU + "images/save/state1.png")
        if os.path.isfile(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state2.png") == True :
            images_slot2 = Image.open(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state2.png")
        else:
            images_slot2 = Image.open(PATH_PAUSEMENU + "images/save/state2.png")
        if os.path.isfile(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state3.png") == True :
            images_slot3 = Image.open(PATH_PAUSEMENU + "images/save/" + sysname + "/" + romname + ".state3.png")
        else:
            images_slot3 = Image.open(PATH_PAUSEMENU + "images/save/state3.png")
        images_save0 = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png"),
            images_slot0)
        images_save1 = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png"),
            images_slot1)
        images_save2 = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png"),
            images_slot2)
        images_save3 = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_save.png"),
            images_slot3)
        images_load0 = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png"),
            images_slot0)
        images_load1 = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png"),
            images_slot1)
        images_load2 = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png"),
            images_slot2)
        images_load3 = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_load.png"),
            images_slot3)
        
        if os.path.isfile(PATH_PAUSEMENU + "images/control/" + submenu + "_layout1.png") == True :
            images_button = Image.open(PATH_PAUSEMENU + "images/" + sysname + "_button" + str(es_conf) + ".png")
            images_control1 = img_paste(images_bg,
                images_button,
                Image.open(PATH_PAUSEMENU + "images/control/" + submenu + "_layout1.png"))
        if os.path.isfile(PATH_PAUSEMENU + "images/control/" + submenu + "_layout2.png") == True :
            images_control2 = img_paste(images_bg,
                images_button,
                Image.open(PATH_PAUSEMENU + "images/control/" + submenu + "_layout2.png"))
        if os.path.isfile(PATH_PAUSEMENU + "images/control/" + submenu + "_layout3.png") == True :
            images_control3 = img_paste(images_bg,
                images_button,
                Image.open(PATH_PAUSEMENU + "images/control/" + submenu + "_layout3.png"))
        if os.path.isfile(PATH_PAUSEMENU + "images/control/" + submenu + "_layout4.png") == True :
            images_control4 = img_paste(images_bg,
                images_button,
                Image.open(PATH_PAUSEMENU + "images/control/" + submenu + "_layout4.png"))
        if os.path.isfile(PATH_PAUSEMENU + "images/control/" + submenu + "_layout5.png") == True :
            images_control5 = img_paste(images_bg,
                images_button,
                Image.open(PATH_PAUSEMENU + "images/control/" + submenu + "_layout5.png"))
        if os.path.isfile(PATH_PAUSEMENU + "images/control/" + submenu + "_layout6.png") == True :
            images_control6 = img_paste(images_bg,
                images_button,
                Image.open(PATH_PAUSEMENU + "images/control/" + submenu + "_layout6.png"))

    else:
        images_resume = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_resume.png"))
        images_stop = img_paste(images_bg,
            Image.open(PATH_PAUSEMENU + "images/" + VIEW_MODE + "_stop.png"))

def main():
    
    global btn_select, btn_start, btn_a, btn_x, btn_pausemenu
    global romname, sysname, corename, button_num, layout_num, VIEW_MODE
    global res_x, res_y

    load_button()

    fbset = run_cmd("fbset -s | grep mode | grep -v endmode | awk '{print $2}'").replace('"', '')
    res_x = fbset.split("x")[0]
    res_y = fbset.split("x")[1].replace('\n', '')

    is_retroarch = False
    while True:
        if is_running("bin/retroarch") == True:
            if full_arg() == True:
                is_retroarch = True
            #time.sleep(3)
            #send_hotkey("f", 1)
            break
        elif is_running("emulators") == True and is_running("bin/retroarch") == False:
            break
        else:
            time.sleep(0.5)    # wait for launching game

    #print "Check update.."
    if is_retroarch == True:
        sysname = run_cmd("ps -ef | grep bin/retroarch | grep -v grep | awk '{print $13}'").split("/")[5]
        if os.path.isdir(PATH_PAUSEMENU + "images/control/" + sysname) == False:
            os.mkdir(PATH_PAUSEMENU + "images/control/" + sysname)
        if os.path.isdir(PATH_PAUSEMENU + "images/save/" + sysname) == False:
            os.mkdir(PATH_PAUSEMENU + "images/save/" + sysname)
        corename = run_cmd("ps -ef | grep bin/retroarch | grep -v grep | awk '{print $10}'").split("/")[4]
        #romname = run_cmd("ps -ef | grep bin/retroarch | grep -v grep | awk '{print $13}'").split("/")[6][0:-5]
        pid = run_cmd("ps -ef | grep bin/retroarch | grep -v grep").split()[1]  
        if os.path.isfile("/proc/"+pid+"/cmdline") == True:
            path = run_cmd("strings -n 1 /proc/"+pid+"/cmdline | grep roms")
            romname = path.replace('"','').split("/")[-1].split(".")[0]
            if corename == "lr-fbneo" or corename == "lr-fbalpha":
                VIEW_MODE = "fba"
                #VIEWER_OSD = VIEWER_OSD + " --win " + \
                #    str(int(res_x)-300) + "," + str(int(res_y)-160) + "," + res_x + "," + res_y
                buttons, button_num, layout_num = get_info()
                if check_update(corename) == True:
                    #start_viewer_saving()
                    load_layout()
                    draw_picture(buttons)
                    #stop_viewer()
            else:
                VIEW_MODE = "libretro"
    #else: # advmame, ppsspp, drastic, ...
    #    VIEW_MODE = "default"
    '''            
    if os.path.isfile(PATH_PAUSEMENU + "button.cfg") == False:
        return False
    f = open(PATH_PAUSEMENU + "button.cfg", 'r')
    line = f.readline()
    words = line.split()
    btn_select = int(words[0])
    btn_start = int(words[1])
    btn_a = int(words[2])
    '''
    btn_select = int(retroarch_key['select'])
    btn_start = int(retroarch_key['start'])
    btn_a = int(retroarch_key['a'])
    btn_x = int(retroarch_key['x'])
    if 'pausemenu' in retroarch_key:
        btn_pausemenu = int(retroarch_key['pausemenu'])
        btn_start = -1

    fbdev_setup()

    #print "PauseMenu is ready.."
    
    js_fds=[]
    rescan_time = time.time()
    while True:
        do_sleep = True
        if not js_fds:
            js_devs, js_fds = open_devices()
            if js_fds:
                i = 0
                current = time.time()
                js_last = [None] * len(js_fds)
                for js in js_fds:
                    js_last[i] = current
                    i += 1
            else:
                time.sleep(1)
        else:
            i = 0
            for fd in js_fds:
                event = read_event(fd)
                if event:
                    do_sleep = False
                    #if time.time() - js_last[i] > JS_REP:
                    if time.time() - js_last[i] > 0:                        
                        if process_event(event):
                            js_last[i] = time.time()
                elif event == False:
                    close_fds(js_fds)
                    js_fds = []
                    break
                i += 1

        if time.time() - rescan_time > 2:
            rescan_time = time.time()
            if cmp(js_devs, get_devices()):
                close_fds(js_fds)
                js_fds = []

        if do_sleep:
            time.sleep(0.01)

if __name__ == "__main__":
    import sys

    try:
        main()

    # Catch all other non-exit errors
    except Exception as e:
        sys.stderr.write("Unexpected exception: %s" % e)
        sys.exit(1)

    # Catch the remaining exit errors
    except:
        sys.exit(0)
