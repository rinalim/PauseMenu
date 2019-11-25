#-*-coding: utf-8 -*-
#!/usr/bin/python

import os, re, time, sys
from subprocess import *
import xml.etree.ElementTree as ET

reload(sys)
sys.setdefaultencoding('utf-8')


CONFIG = '/home/csle/retro/PauseOptionDev/configs/'
PATH_PAUSEOPTION = '/home/csle/retro/PauseOptionDev/'
PATH_PAUSEMODE = '/home/csle/retro/PauseOptionDev/PauseMode/'
XML = PATH_PAUSEOPTION+'xml/'
FONT = "'NanumBarunGothic'"

user_key = {}
btn_map = {}
es_conf = 1

capcom_fight = ['mshvsf', 'vsav', 'sfa', 'sfa2', 'sfa3', 'sf2', 'sf2ce', 'ssf2']
capcom_dd = ['ddtod', 'ddsom']


def run_cmd(cmd):
# runs whatever in the cmd variable
    p = Popen("LANG=en_US.UTF-8 " + cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output
	

def check_update(romname):
    RESUME = PATH_PAUSEOPTION+'result/' + romname + '_resume.png'
    XML+romname+'.xml'
    CORECFG = CONFIG + 'fba/FB Alpha/FB Alpha.rmp'
    GAMECFG = CONFIG + 'fba/FB Alpha/' + romname + '.rmp'
   
    if os.path.isfile(RESUME) == False:
        return True
    else:
        _time = os.path.getmtime(RESUME)
        if _time < os.path.getmtime(PATH_PAUSEOPTION+'layout.cfg'):
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
        
    #print 'No need to update PNG'
    return False


def load_layout():

    global es_conf

    #' -(1)-----  -(2)-----  -(3)----- '
    #' | X Y L |  | Y X L |  | L Y X | '
    #' | A B R |  | B A R |  | R B A | '
    #' ---------  ---------  --------- '

    f = open(PATH_PAUSEOPTION+"layout.cfg", 'r')
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

            
def get_info(romname):

    #INPUT = './controls.xml'   
    if os.path.isfile(XML+romname+'.xml') == False:
        print 'No xml found'
        name = romname
        buttons = ['A 버튼', 'B 버튼', 'C 버튼', 'D 버튼', 'None', 'None']
    else:
        doc = ET.parse(XML+romname+'.xml')
        game = doc.getroot()
    #game = root.find('./game[@romname=\"' + romname + '\"]')
    #if game == None:
    #   print 'No Game Found'
        name = str(unicode(game.get('gamename')))
        print name
        player = game.find('player')
        controls = player.find('controls')
        labels = player.findall('labels')
        buttons = []
        for i in labels[0]:
            if 'BUTTON' in i.get('name'):
                btn = str(unicode(i.get('value')))
                # Translate to Korean
                btn = btn.replace("Jab", "약")
                btn = btn.replace("Strong", "중")
                btn = btn.replace("Fierce", "강")
                btn = btn.replace("Short", "약")
                btn = btn.replace("Roundhouse", "강")
                btn = btn.replace("Light", "약")
                btn = btn.replace("Middle", "중")
                btn = btn.replace("Heavy", "강")
                btn = btn.replace("Punch", "펀치")
                btn = btn.replace("Kick", "킥")
                btn = btn.replace("Attack", "공격")
                btn = btn.replace("Jump", "점프")
                btn = btn.replace("Select", "선택")
                btn = btn.replace("Magic", "마법")
                btn = btn.replace("Fire", "총알")
                btn = btn.replace("Loop", "회전")
                btn = btn.replace("Bubble", "방울")
                btn = btn.replace("Left", "왼쪽")
                btn = btn.replace("Center", "가운데")
                btn = btn.replace("Right", "오른쪽")
                btn = btn.replace(" - ", "-")
                #btn = btn[:10]
                buttons.append(btn)
                print i.get('name'), btn
        for j in range(len(buttons), 6):
            buttons.append("None")
    
    return name, buttons


def get_btn_layout(system, romname, buttons):

    # FBA button sequence   
    btn_map['b'] = '"0"'
    btn_map['a'] = '"8"'
    btn_map['y'] = '"1"'
    btn_map['x'] = '"9"'
    btn_map['l'] = '"10"'
    btn_map['r'] = '"11"'

    if os.path.isfile(CONFIG + 'fba/FB Alpha/' + romname + '.rmp') == True:
        print 'Use game specific setting'
        f = open(CONFIG + 'fba/FB Alpha/' + romname + '.rmp', 'r')
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
	
    elif os.path.isfile(CONFIG + 'fba/FB Alpha/FB Alpha.rmp') == True:
        print 'Use FBA setting'
        f = open(CONFIG + 'fba/FB Alpha/FB Alpha.rmp', 'r')
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

    if romname in capcom_fight:
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

    
def draw_picture(system, romname, name, buttons):

    CONTROL = " " + PATH_PAUSEOPTION+'result/' + romname + '_control.png'
    RESUME = " " + PATH_PAUSEOPTION+'result/' + romname + '_resume.png'
    STOP = " " + PATH_PAUSEOPTION+'result/' + romname + '_stop.png'

    # Layout
    #cmd = "composite -geometry 300x160+8+185 " + PATH_PAUSEOPTION + "images/layout" + str(es_conf) + ".png" + " images/bg_resume.png" + RESUME
    cmd = "cp " + PATH_PAUSEOPTION + "images/layout" + str(es_conf) + ".png" + CONTROL
    run_cmd(cmd)


    if system == "lr-fbalpha":
        get_btn_layout(system, romname, buttons)
    
        # Configured button layout
        #pos = ["90x25+70+253", "90x25+150+227", "90x25+230+204", "90x25+70+318", "90x25+150+293", "90x25+230+267"]
        pos = ["90x25+62+68", "90x25+142+42", "90x25+222+19", "90x25+62+133", "90x25+142+108", "90x25+222+82"]
        for i in range(1,7):
            btn = btn_map[user_key[str(i)]]
            if btn != 'None':
                cmd = "convert -background none -fill black -font " + FONT + "-Bold -pointsize 20 label:'" + btn + "' /tmp/text.png"
                run_cmd(cmd)
                cmd = "composite -geometry " + pos[i-1] + " /tmp/text.png" + CONTROL + CONTROL
                run_cmd(cmd)


    #Generate a PAUSE image
    cmd = "composite -geometry 300x160+8+185 " + CONTROL + " " + PATH_PAUSEOPTION + "images/bg_resume.png" + RESUME
    run_cmd(cmd)
    # Generate a STOP image
    cmd = "composite " + PATH_PAUSEOPTION + "images/bg_stop.png " + RESUME + STOP
    run_cmd(cmd)
    # Generate a Controll image
    cmd = "composite " + CONTROL + " " + PATH_PAUSEOPTION + "images/bg_control.png" + CONTROL
    run_cmd(cmd)



def main():

    system = 'lr-fbalpha'
    romname = sys.argv[1]
    if check_update(romname) == True:
        load_layout()
        name, buttons = get_info(romname)
        #print name, buttons
        draw_picture(system, romname, name, buttons)

'''
            RESUME = " " + PATH_PAUSEOPTION+'result/' + romname + '_resume.png'
            STOP = " " + PATH_PAUSEOPTION+'result/' + romname + '_stop.png'
            # Copy images to PauseMode 
            run_cmd("cp " + RESUME + " " + PATH_PAUSEMODE + "pause_resume.png")
            run_cmd("cp " + STOP + " " + PATH_PAUSEMODE + "pause_stop.png")
'''


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
