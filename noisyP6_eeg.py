import random, os, numpy, pandas, platform, time, sys, serial
from psychopy.hardware import brainproducts
from psychopy import visual, core, event, monitors, gui, data, clock, logging, prefs
from string import ascii_letters, digits
from psychopy.tools.filetools import fromFile, toFile
logging.console.setLevel(logging.DEBUG) # change for real
# *TO DO*: add practice trials -- done
# *TO DO*: add breaks -- 10 blocks --done
# *TO DO*: 60/480 with comprehension questions --- done
# *TO DO*: send triggers
# *TO SOLVE*: unable to test with trigger box
# *TO SOLVE*: unable to take input from keyboard

# Switch to the script folder
script_path = os.path.dirname(sys.argv[0])
if len(script_path) != 0:
    os.chdir(script_path)

# Set this variable to True to run the script in "Dummy Mode"
##debug without port -- dummy mode
dummy_mode = True

# Set this variable to True to run the task in full screen mode
# It is easier to debug the script in non-fullscreen mode
full_screen = False

## input subject number
#subjnum = input('Please enter participant number: ' )
##debug with a random number
subjnum = 0
#adding a random number for filename to avoid accidental overwriting
srand = numpy.random.randint(1000,9999)

# Set up output file name and local data folder
results_folder = 'data'
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# make a csv file to save data
outputFileName = os.path.join(results_folder + '/s' + str(subjnum) + '_' + str(srand) + '.csv')
dataFile = open(outputFileName, 'w')  # a simple text file with 'comma-separated-values'
dataFile.write('subj,order,list,item,condition,sentence,question,correct_answer,response\n')

# read in information about items and conditions into a dataframe
listNum = numpy.random.randint(1,8)
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

# Open a window, be sure to specify monitor parameters
#mon = monitors.Monitor('myMonitor', width=53.0, distance=70.0)
win = visual.Window(fullscr=full_screen,
                    size=(800, 600),
                    color='white',
                    checkTiming = True
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


# define a few helper functions for trial handling
def clear_screen(win):
    """ clear up the PsychoPy window"""
#    win.fillColor = genv.getBackgroundColor()
    win.flip()


def show_msg(win, text, wait_for_keypress=True):
    """ Show a message and get responses"""
    key_pressed = None
    RT = None
    msg = visual.TextStim(win, text,
                         # color=genv.getForegroundColor(),
                          wrapWidth=scn_width/2,
                          color='black')
    clear_screen(win)
    msg.draw()
    time_msg = win.flip()

    if not dummy_mode:
        port.write([0x03])
        port.write([0x00])

    # wait indefinitely, terminates upon any key press
    if wait_for_keypress:
        key_time = event.waitKeys(timeStamped = True)
        #print(key_time)
        key_pressed = key_time[0][0]
        RT = key_time[0][1] - time_msg
        clear_screen(win)
    return key_pressed, RT

def show_word(win, text, dur, crit=False):
    """ Show one word of sentence at a time and send triggers """

    msg = visual.TextStim(win, text,
                         # color=genv.getForegroundColor(),
                          wrapWidth=scn_width/2,
                          color='black')
    clear_screen(win)

    clock = core.Clock()
    while clock.getTime() < dur:  # Clock times are in seconds
        msg.draw()
        win.flip()
        if not dummy_mode and crit:
            port.write([0x02])
        elif not dummy_mode:
            port.write([0x01])
    clear_screen(win)
    if not dummy_mode:
        port.write([0x00])
        
##decide whether to run comprehension question        
def run_question(quest, trial_index, question_index, total, consecutive, noquestion):
    randnum = numpy.random.randint(0,1000)
    consecutive = 0
    noquestion = noquestion + 1
    flag = False
    if (total < 60) and type(quest) is str:
        if (randnum < 125 and consecutive < 3) or (noquestion > 20) or (480 - trial_index <= 60 - total):
            question_index = trial_index
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
        words  = prac[i].split()
    
    # pre-trial fixation for 1000ms
        show_word(win,"+", dur = 1.0)

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
    #print(item, resp)
    # clear the screen
        clear_screen(win)
    
    prac_msg = 'This is the end of practice trial.\n' + \
    '\nNow, press ENTER to start the real experiment.\n'
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
    show_word(win,"+", dur = 1.0)

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
    
    question_index, consecutive, noquestion, total, flag = run_question(quest, trial_index, question_index, total, consecutive, noquestion)
    if flag == True:
        # show question and collect response
        event.clearEvents()  # clear cached PsychoPy events
        button_pressed = show_msg(win, quest+"\n\n1:YES\t\t\t2:NO")
        print(button_pressed)
    
        resp = button_pressed[0]
        RT = button_pressed[1]
    #print(item, resp)
        dataFile.write(str(subjnum) + ',' + str(trial_index) + ',' + str(listNum) + ',' + str(item) + ',' + cond + ',' + sent + ',' + quest + ',' + ans + ',' + str(resp) + ',' + str(RT) + '\n')
    else:
        event.clearEvents()  # clear cached PsychoPy events
        button_pressed = show_msg(win, 'Please press ENTER to continue')
        print(button_pressed)
        resp = button_pressed[0]
        RT = button_pressed[1]
    #print(item, resp)
        dataFile.write(str(subjnum) + ',' + str(trial_index) + ',' + str(listNum) + ',' + str(item) + ',' + cond + ',' + sent + ',' + 'NA' + ',' + 'NA' + ',' + str(resp) + ',' + str(RT) + '\n')
    # clear the screen
    clear_screen(win)
    
    if trial_index % 48 == 0:
        break_msg = 'Have a break now!\n' + \
    '\nPress ENTER to resume.\n'
        show_msg(win, break_msg)
        
    return question_index, consecutive, noquestion, total

def terminate_task():

    # close the PsychoPy window
    win.close()

    # quit PsychoPy
    core.quit()
    sys.exit()



# Show the task instructions
task_msg = 'Welcome to this brainwaves study!\n' + \
    '\nPress Ctrl-C to if you need to quit the task early\n'
if dummy_mode:
    task_msg = task_msg + '\nNow, press ENTER to start the task'
else:
    task_msg = task_msg + '\nNow, press ENTER twice to start the task'
show_msg(win, task_msg)


# instructions LOOP
instructions = ['In this task, you will read sentences one word at a time.\n (press any button to continue)',
        'Please read the sentences carefully.',
        'Some sentences will be followed by comprehension questions.',
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
