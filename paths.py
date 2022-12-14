from os.path import join, dirname


CURRENT_FILE_DIR    = dirname(__file__)
APP_UI              = join(CURRENT_FILE_DIR, 'ui', 'ui.ui')
SPLASH              = join(CURRENT_FILE_DIR, 'ui', 'images', 'splash.jpg')
SPLASH_LOADING      = join(CURRENT_FILE_DIR, 'ui', 'images', 'splashLoading.jpg')
SHOT_SOUND          = join(CURRENT_FILE_DIR, 'ui', 'sounds', 'shot.wav')
TOUCH_SOUND         = join(CURRENT_FILE_DIR, 'ui', 'sounds', 'touch.wav')
KEYBOARD_SOUND      = join(CURRENT_FILE_DIR, 'ui', 'sounds', 'keyboard.wav')
WELLCOME_SOUND      = join(CURRENT_FILE_DIR, 'ui', 'sounds', 'wellcome.wav')
STARTUP_SOUND       = join(CURRENT_FILE_DIR, 'ui', 'sounds', 'startup.wav')
SHUTDOWN_SOUND      = join(CURRENT_FILE_DIR, 'ui', 'sounds', 'shutdown.wav')
IRANIAN_SANS        = join(CURRENT_FILE_DIR, 'ui', 'fonts', 'IranianSans.ttf')
IRAN_NASTALIQ       = join(CURRENT_FILE_DIR, 'ui', 'fonts', 'IranNastaliq.ttf')
VAUGE_FONT          = join(CURRENT_FILE_DIR, 'ui', 'fonts', 'Orbitron', 'Orbitron-VariableFont_wght.ttf')
ADSS_DEMO           = join(CURRENT_FILE_DIR, 'ui', 'adssDemo.mp4')
CONFIG_FILE         = join(CURRENT_FILE_DIR, 'configs', 'config')
COPY_RIGHT_PASS     = join(CURRENT_FILE_DIR, 'configs', 'pass')
CASES_DIR           = join(CURRENT_FILE_DIR, 'configs', 'cases')
LOGS_PATH           = join(CURRENT_FILE_DIR, 'configs', 'systemLog')
USERS_DATA          = join(CURRENT_FILE_DIR, 'configs', 'USERS_DATA')
COEFFICIENTS        = join(CURRENT_FILE_DIR, 'configs', 'coefficients')
TUTORIALS_DIR       = join(CURRENT_FILE_DIR, 'tutorials')
MONITOR_COMMAND     = join(CURRENT_FILE_DIR, 'getMonitorInfo')
MONITOR_INFO_FILE   = join(CURRENT_FILE_DIR, 'monitorInfo')
THEMES_DIR          = join(CURRENT_FILE_DIR, 'ui', 'images', 'themes')
IMAGES_DIR          = join(CURRENT_FILE_DIR, 'ui', 'images')
SHUTDONW_GIF        = join(IMAGES_DIR, 'shutdown.gif')
INFORMATION_ICON    = join(IMAGES_DIR, 'information.png')
DEC_BLUE            = join(IMAGES_DIR, 'decBlue.png')
DEC_BLACK           = join(IMAGES_DIR, 'decBlack.png')
INC_BLUE            = join(IMAGES_DIR, 'incBlue.png')
INC_BLACK           = join(IMAGES_DIR, 'incBlack.png')
DELETE_ICON         = join(IMAGES_DIR, 'delete.png')
LOCK                = join(IMAGES_DIR, 'lock.png')
UNLOCK              = join(IMAGES_DIR, 'unlock.png')
COOLING_OFF         = join(IMAGES_DIR, 'coolingOff.png')
PLAY_ICON           = join(IMAGES_DIR, 'play.png')
PAUSE_ICON          = join(IMAGES_DIR, 'pause.png')
LOOP_MUSIC_ICON     = join(IMAGES_DIR, 'loopMusic.png')
SINGLE_MUSIC_ICON   = join(IMAGES_DIR, 'singleMusic.png')
SELECTED_LANG_ICON  = join(IMAGES_DIR, 'downArrow.png')
RELAY_ICON          = join(IMAGES_DIR, 'relay.png')
DRIVER_CURRENT      = join(IMAGES_DIR, 'driverCurrent.png')
LOCK_GIF            = join(IMAGES_DIR, 'lock.gif')
MUSIC_GIF           = join(IMAGES_DIR, 'music.gif')
COOLING_GIF         = join(IMAGES_DIR, 'cooling.gif')
RELAY_GIF           = join(IMAGES_DIR, 'relayLoading.gif')
SPARK_ICON          = join(IMAGES_DIR, 'spark.png')
LASER_LOGO          = join(IMAGES_DIR, 'laserLogo.png')
RIGHT_BLUE          = join(IMAGES_DIR, 'rightBlue.png')
LEFT_BLUE           = join(IMAGES_DIR, 'leftBlue.png')
RIGHT_RED           = join(IMAGES_DIR, 'rightRed.png')
LEFT_RED            = join(IMAGES_DIR, 'leftRed.png')
RIGHT_GREEN         = join(IMAGES_DIR, 'rightGreen.png')
LEFT_GREEN          = join(IMAGES_DIR, 'leftGreen.png')
RIGHT_YELLOW        = join(IMAGES_DIR, 'rightYellow.png')
LEFT_YELLOW         = join(IMAGES_DIR, 'leftYellow.png')
CASE_I              = join(IMAGES_DIR, 'I.png')
CASE_II             = join(IMAGES_DIR, 'II.png')
CASE_III            = join(IMAGES_DIR, 'III.png')
CASE_IV             = join(IMAGES_DIR, 'IV.png')
CASE_V              = join(IMAGES_DIR, 'V.png')
CASE_SAVE           = join(IMAGES_DIR, 'save.png')
CLOSE_FILM          = join(IMAGES_DIR, 'close.png')
FULLSCREEN_ICON     = join(IMAGES_DIR, 'fullscreen.png')
NOT_FULLSCREEN_ICON = join(IMAGES_DIR, 'notFullscreen.png')
BODY_PART_ICONS = {
        'f face':    join(IMAGES_DIR, 'fFace'),
        'f armpit':  join(IMAGES_DIR, 'fArmpit'),
        'f arm':     join(IMAGES_DIR, 'fArm'),
        'f body':    join(IMAGES_DIR, 'fBody'),
        'f bikini':  join(IMAGES_DIR, 'fBikini'),
        'f leg':     join(IMAGES_DIR, 'fLeg'),
        'm face':    join(IMAGES_DIR, 'mFace'),
        'm armpit':  join(IMAGES_DIR, 'mArmpit'),
        'm arm':     join(IMAGES_DIR, 'mArm'),
        'm body':    join(IMAGES_DIR, 'mBody'),
        'm bikini':  join(IMAGES_DIR, 'mBikini'),
        'm leg':     join(IMAGES_DIR, 'mLeg')
    }
