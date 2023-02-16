import random, os, numpy, pandas, platform, time, sys, serial
from psychopy.hardware import brainproducts
from psychopy import visual, core, event, monitors, gui, data, clock, logging, prefs
from string import ascii_letters, digits
from psychopy.tools.filetools import fromFile, toFile
logging.console.setLevel(logging.DEBUG) # change for real

# Switch to the script folder
script_path = os.path.dirname(sys.argv[0])
if len(script_path) != 0:
    os.chdir(script_path)

# Set this variable to True to run the script in "Dummy Mode"
##debug without port -- dummy mode
dummy_mode = True

# Set this variable to True to run the task in full screen mode
# It is easier to debug the script in non-fullscreen mode
full_screen = True

## input subject number
subjnum = input('Please enter participant number: ' )
##debug with a random number
#subjnum = 0
#adding a random number for filename to avoid accidental overwriting
srand = numpy.random.randint(1000,9999)

# Set up output file name and local data folder
results_folder = 'data'
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# make a csv file to save data
outputFileName = os.path.join(results_folder + '/s' + str(subjnum) + '_' + str(srand) + '.tsv')
dataFile = open(outputFileName, 'w')  # a simple text file with 'comma-separated-values'
dataFile.write('subj\torder\tlist\titem\tcondition\tsentence\tquestion\tcorrect_answer\tresponse\ttime\n')

# read in information about items and conditions into a dataframe
#listNum = numpy.random.randint(1,8)
listNum = input('Please enter list number: ' )
listFilename = 'noisyP6_list' + str(listNum) + '.csv'
# change encoding
itemInfo = pandas.read_csv(listFilename, encoding = 'latin-1')

# construct a list of trials
trial_order = itemInfo.values.tolist()

# randomize the trial list
random.shuffle(trial_order)

# port that trigger box is connected to
if not dummy_mode:
    port = serial.Serial('COM3')
    port.write([0x00])

# Open a window, be sure to specify monitor parameters
#mon = monitors.Monitor('myMonitor', width=53.0, distance=70.0)
win = visual.Window(fullscr=full_screen,
                    size=(800, 600),
                    color=(0,0,0), 
                    checkTiming=True
                    #monitor=mon,
                    #winType='pyglet',
                    #units='pix'
                    )

# get the native screen resolution used by PsychoPy
scn_width, scn_height = win.size
print(scn_width, scn_height)


# Set background and foreground colors for the calibration target
# in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
foreground_color = (-1, -1, -1)
background_color = (1, 1, 1)
#genv.setCalibrationColors(foreground_color, background_color)

def key_to_trigger(key):
    """ map button box responses to trigger codes"""
    if key == '1':
        trigger = [0x07]
    elif key == '2':
        trigger = [0x08]
    else:
        trigger = [0x09]

    return trigger

def condition_to_trigger(condition):
    """ map target conditions to trigger codes"""
    if condition == 'Control':
        trigger = [0x01]
    elif condition == 'Sem':
        trigger = [0x02]
    elif condition == 'SemCrit':
        trigger = [0x03]
    elif condition == 'Synt':
        trigger = [0x04]
    else:
        trigger = [0x05]

    return trigger

# define a few helper functions for trial handling
def clear_screen(win):
    """ clear up the PsychoPy window"""
#    win.fillColor = genv.getBackgroundColor()
    win.flip()


def show_msg(win, text, wait_for_keypress=True, dummy_mode=dummy_mode):
    """ Show a message and get responses"""
    key_time = False
    key_pressed = None
    rt = None
    pulse_started = False
    pulse_ended = False
    resp_pulse_started = False
    resp_pulse_ended = False
    msg = visual.TextStim(win, text,
                         # color=genv.getForegroundColor(),
                          wrapWidth=scn_width/2,
                          color='black')

    clock = core.Clock()

    clear_screen(win)
    msg.draw()
    time_msg = win.flip()

    if not dummy_mode and not pulse_started:
        port.write([0x06])  # any instruction sends S6 trigger
        pulse_start_time = clock.getTime()
        pulse_started = True

    if not dummy_mode and pulse_started and not pulse_ended:
        if clock.getTime() - pulse_start_time >= 0.005:
            port.write([0x00])
            pulse_ended = True

    # wait indefinitely, terminates upon any key press
    if wait_for_keypress:
        key_time = event.waitKeys(timeStamped=True)
        if not dummy_mode and key_time and not resp_pulse_started:
            response_code = key_to_trigger(key_time[0][0])
            port.write(response_code)  # button press sends S4 trigger
            resp_pulse_start_time = clock.getTime()
            resp_pulse_started = True

        if not dummy_mode and resp_pulse_started and not resp_pulse_ended:
            if clock.getTime() - resp_pulse_start_time >= 0.005:
                port.write([0x00])
                resp_pulse_ended = True

        #print(key_time)
        key_pressed = key_time[0][0]
        rt = key_time[0][1] - time_msg

        if key_pressed == 'escape':
            terminate_task()

        clear_screen(win)
    return key_pressed, rt

def show_word(win, text, dur, crit=False, dummy_mode=dummy_mode):
    """ Show one word of sentence at a time and send triggers """
    crit_pulse_started = False
    crit_pulse_ended = False
    trigger_code = condition_to_trigger(crit)
    msg = visual.TextStim(win, text,
                         # color=genv.getForegroundColor(),
                          wrapWidth=scn_width/2,
                          color='black')
    clear_screen(win)

    clock = core.Clock()
    while clock.getTime() < dur:  # Clock times are in seconds
        msg.draw()
        win.flip()
        if not dummy_mode:
            if not crit_pulse_started and not crit_pulse_ended:
                port.write(trigger_code)  # if last word of a critical sentence, indicates the condition, else trigger is 5
                crit_pulse_start_time = clock.getTime()
                crit_pulse_started = True

            elif crit_pulse_started and not crit_pulse_ended:
                if clock.getTime() - crit_pulse_start_time >= 0.005:
                    port.write([0x00])
                    #pulse_started = False
                    crit_pulse_ended = True

    clear_screen(win)
        
##decide whether to run comprehension question        
def run_question(quest, trial_index, question_index, total, consecutive, noquestion):
    randnum = numpy.random.randint(0,1000)
    consecutive = 0
    noquestion = noquestion + 1
    flag = False
    #print(randnum)
    if (total < 60) and type(quest) is str:
        if (randnum < 125 and consecutive < 3) or (noquestion > 20) or (480 - trial_index <= 60 - total):
            question_index = trial_index
            noquestion = 0
            consecutive = consecutive + 1
            total = total + 1
            flag = True
    return question_index, consecutive, noquestion, total, flag
    
def run_practice():
    """ Helper function specifying the events that will occur in a single trial
    trial_pars - a list containing trial parameters
    liistNum - counterbalanicng list (passing to output file)
    trial_index - record the order of trial presentation in the task
    """

    # unpacking the trial parameters
    
    prac = ['Emily has three dogs and two cats. ','The man passed the exam and went home to celebrate it.' ]
    quest = ['Does Emily have more cats than dogs?'+'\nYou should answer No to this question.', 
    'Did the man pass the exam?'+'\nYou should answer Yes to this question.']
    for i in range(len(prac)):
        words = prac[i].split()
    
    # pre-trial fixation for 1000ms
        show_word(win, "+", dur=1.0)

    # blank screen for 500ms
        preISI = clock.StaticPeriod()# can add screen refresh for more precision
        preISI.start(0.5)
        preISI.complete()
    #clear_screen(win)
        for w in words:
            if w == words[-1]:
                show_word(win, w, dur = 0.4, crit = True)
            else:
                show_word(win, w, dur = 0.4)
            ISI = clock.StaticPeriod()# can add screen refresh for more precision
            ISI.start(0.1)  # start a period of 0.5s
            ISI.complete()  # finish the 0.5s, taking into account one 60Hz frame
    # additional 800ms of ISI after last word
        postISI = clock.StaticPeriod()# can add screen refresh for more precision
        postISI.start(0.8)
        postISI.complete()

    # show question and collect response
        event.clearEvents()  # clear cached PsychoPy events
        button_pressed = show_msg(win, quest[i]+"\n\n1:YES\t\t\t2:NO")
        print(button_pressed)
        resp = button_pressed[0]
        RT = button_pressed[1]
        show_msg(win, 'Please press any button to continue')
    #print(item, resp)
    # clear the screen
        clear_screen(win)
    
    prac_msg = 'This is the end of practice trial.\n' + \
    '\nNow, press any button to start the real experiment.\n'
    show_msg(win, prac_msg)
        
def run_eeg_vis_trial(trial_pars,listNum,trial_index, question_index, total, consecutive, noquestion):
    """ Helper function specifying the events that will occur in a single trial
    trial_pars - a list containing trial parameters
    liistNum - counterbalanicng list (passing to output file)
    trial_index - record the order of trial presentation in the task
    """

    # unpacking the trial parameters
    item, cond, sent, quest, ans = trial_pars

    words = sent.split()
    #print(words)

    # pre-trial fixation for 1000ms
    show_word(win, "+", dur=1.0)

    # blank screen for 500ms
    preISI = clock.StaticPeriod()# can add screen refresh for more precision
    preISI.start(0.5)
    preISI.complete()
    #clear_screen(win)

    for w in words:
        if w == words[-1]:
            show_word(win, w, dur=0.4, crit=cond)
        else:
            show_word(win, w, dur=0.4)
        ISI = clock.StaticPeriod()# can add screen refresh for more precision
        ISI.start(0.1)  # start a period of 0.5s
        ISI.complete()  # finish the 0.5s, taking into account one 60Hz frame


    # additional 800ms of ISI after last word
    postISI = clock.StaticPeriod()# can add screen refresh for more precision
    postISI.start(0.8)
    postISI.complete()
    
    question_index, consecutive, noquestion, total, flag = run_question(quest, trial_index, question_index, total, consecutive, noquestion)
    if flag == True:
        # show question and collect response
        event.clearEvents()  # clear cached PsychoPy events
        button_pressed = show_msg(win, quest+"\n\n1:YES\t\t\t2:NO")
        print(button_pressed)
    
        resp = button_pressed[0]
        RT = button_pressed[1]
    #print(item, resp)
        dataFile.write(str(subjnum) + '\t' + str(trial_index) + '\t' + str(listNum) + '\t' + str(item) + '\t' + cond + '\t' + sent + '\t' + quest + '\t' + ans + '\t' + str(resp) + '\t' + str(RT) + '\n')
        show_msg(win, 'Please press any button to continue')
    else:
        event.clearEvents()  # clear cached PsychoPy events
        button_pressed = show_msg(win, 'Please press any button to continue')
        print(button_pressed)
        resp = button_pressed[0]
        RT = button_pressed[1]
    #print(item, resp)
        dataFile.write(str(subjnum) + '\t' + str(trial_index) + '\t' + str(listNum) + '\t' + str(item) + '\t' + cond + '\t' + sent + '\t' + 'NA' + '\t' + 'NA' + '\t' + str(resp) + '\t' + str(RT) + '\n')
    # clear the screen
    clear_screen(win)
    
    if (trial_index % 48 == 0) and (trial_index != 0):
        block_num = trial_index // 48
        break_msg = f'You have completed {block_num} out of 10 sessions.\n Take a break now!\n' + \
    '\nPress any button to resume.\n'
        show_msg(win, break_msg)
        
    return question_index, consecutive, noquestion, total

def terminate_task():

    # close the PsychoPy window
    win.close()

    # quit PsychoPy
    core.quit()
    sys.exit()



# Show the task instructions
task_msg = 'Welcome to this brainwaves study!\n\nNow, press any button to start the task.'
# if dummy_mode:
#     task_msg = task_msg + '\nNow, press ENTER to start the task'
# else:
#     task_msg = task_msg + '\nNow, press ENTER twice to start the task'
show_msg(win, task_msg)


# instructions LOOP
instructions = ['In this task, you will read sentences one word at a time.\n (press any button to continue)',
        'Please read the sentences carefully.',
        'Some sentences will be followed by comprehension questions.',
        'The question always pertains to the immediate preceding sentence.',
        'Use the 1 button to answer YES and...\nthe 2 button to answer NO.',
        'You will start by doing a few practice trials.',
        'Please let the experimenter know if you have any questions.',
        'If you have no questions, you may begin!']

for m in range(0, len(instructions)):
    show_msg(win, instructions[m])
    
run_practice()

# run trials
trial_index = 0
question_index, total, consecutive, noquestion = 0,0,0,0

for trial_pars in trial_order:
   # print("trial_pars")
   # print(trial_pars)
    question_index, consecutive, noquestion, total = run_eeg_vis_trial(trial_pars, listNum, trial_index, question_index, total, consecutive, noquestion)
    trial_index += 1
    
    
# goodbye
bye = 'You have completed this experiment.\nThank you for participating!'
show_msg(win, bye)

terminate_task()
