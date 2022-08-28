import pathlib
import jdatetime
import hashlib
import pickle
import time 
import math
import sys
import os
from glob import glob
from itertools import chain
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
from PyQt5.uic import loadUi
from pygame import mixer

import communication
import promotions
import utility
import styles
import paths
import case  
import user
import lang
from lock import Lock

mixer.init(buffer=2048)
mixer.music.set_volume(0.5)

HW_PAGE_ADMIN_PASSWORD = '1'
HW_PAGE_USER_PASSWORD  = '0'
RESET_COUNTER_PASSWORD = 'zzxxcc'


class MainWin(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWin, self).__init__(*args, **kwargs)
        loadUi(paths.APP_UI, self)
        self.setupUi()
        
    def setupUi(self):
        self.configs = utility.loadConfigs()
        self.coefficients = utility.loadCoefficients()
        self.usersData = user.loadUsers()
        self.usersList = list(self.usersData.values())
        self.langIndex = 0
        self.lblEnSelected.setPixmap(QPixmap(paths.SELECTED_LANG_ICON).scaled(70, 70))
        self.serialC = communication.SerialThread()
        self.sensorFlags = [True, True, True, False, False, True]
        self.sensors = promotions.Sensors(
            self.btnLock,
            self.btnWaterLevel,
            self.btnWaterflow,
            self.btnOverHeat,
            self.btnPhysicalDamage,
            self.btnTemp,
            self.btnLockCalib,
            self.btnWaterLevelCalib,
            self.btnWaterflowCalib,
            self.btnOverHeatCalib,
            self.btnPhysicalDamageCalib,
            self.btnTempCalib
        )
        self.serialC.sensorFlags.connect(self.setSensorFlags)
        self.serialC.tempValue.connect(self.setTemp)
        self.serialC.shot.connect(self.shot)
        self.serialC.serialNumber.connect(self.txtSerialNumber.setText)
        self.serialC.productionDate.connect(self.txtProductionDate.setText)
        self.serialC.laserEnergy.connect(self.txtLaserDiodeEnergy.setText)
        self.serialC.laserWavelenght.connect(self.txtLaserWavelength.setText)
        self.serialC.laserBarType.connect(self.txtLaserBarType.setText)
        self.serialC.driverVersion.connect(self.txtDriverVersion.setText)
        self.serialC.mainControl.connect(self.txtMainControlVersion.setText)
        self.serialC.firmwareVesion.connect(self.txtFirmwareVersion.setText)
        self.serialC.receivingSensors.connect(self.setReceivingSensorsData)
        self.serialC.updateProgress.connect(self.setUpdateFirmwareProgress)
        self.serialC.readCooling.connect(lambda: communication.laserPage({'cooling': self.cooling}))
        self.serialC.readEnergy.connect(lambda: communication.laserPage({'energy': self.energy}))
        self.serialC.readPulseWidht.connect(lambda: communication.laserPage({'pulseWidht': self.pulseWidth}))
        self.serialC.readFrequency.connect(lambda: communication.laserPage({'frequency': self.frequency}))
        self.serialC.sysDate.connect(self.receiveDate)
        self.serialC.sysClock.connect(self.adjustTime)
        self.serialC.start()
        self.updateT = communication.UpdateFirmware()
        self.readMusicT = utility.ReadMusics()
        self.readMusicT.result.connect(self.readMusicResult)
        self.readMusicT.paths.connect(self.addMusics)
        self.updateT.result.connect(self.updateGuiResult)
        self.shutdownMovie = QMovie(paths.SHUTDONW_GIF)
        self.musicMovie = QMovie(paths.MUSIC_GIF)
        self.coolingMovie = {}
        self.musicMovie.setCacheMode(QMovie.CacheAll)
        self.musicMovie.jumpToFrame(95)
        self.lblMusicGif.setMovie(self.musicMovie)
        self.musicMovie.start()
        self.musicMovie.stop()
        self.lblShutdownGif.setMovie(self.shutdownMovie)
        self.adssMedia = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.adssMedia.setVideoOutput(self.adssVideo)
        self.adssMedia.stateChanged.connect(self.adssDemoEnd)
        self.musicSound = QMediaPlayer()
        self.touchSound = mixer.Sound(paths.TOUCH_SOUND)
        self.keyboardSound = mixer.Sound(paths.KEYBOARD_SOUND)
        self.playlist = QMediaPlaylist()
        self.playlist.currentIndexChanged.connect(self.playlistIndexChanged)
        self.touchSound.set_volume(0.5)
        self.keyboardSound.set_volume(0.5)
        self.lblSplash = promotions.Label(self.splashPage)
        self.lblSplash.setGeometry(0, 0, 1920, 1080)
        self.lblSplash.setPixmap(QPixmap(paths.SPLASH).scaled(1920,1080))
        self.lblSplash.clicked.connect(lambda: self.changeAnimation('vertical'))
        self.lblSplash.clicked.connect(self.onSplashClicked)
        font_db = QFontDatabase()
        font_id = font_db.addApplicationFont(paths.IRAN_NASTALIQ)
        font_id = font_db.addApplicationFont(paths.IRANIAN_SANS)
        self.ownerInfoSplash = QLabel(self.lblSplash)
        self.ownerInfoSplash.setText('')
        ownerInfo = self.configs['OwnerInfo']
        if ownerInfo and utility.isFarsi(ownerInfo):
            self.ownerInfoSplash.setStyleSheet(styles.OWNER_INFO_STYLE_FA)
        else:
            self.ownerInfoSplash.setStyleSheet(styles.OWNER_INFO_STYLE_EN)
        self.ownerInfoSplash.setAlignment(Qt.AlignCenter)
        self.ownerInfoSplash.setAlignment(Qt.AlignHCenter)
        self.ownerInfoSplash.setText(ownerInfo)
        self.ownerInfoSplash.move(0, 880)
        self.ownerInfoSplash.setMinimumHeight(200)
        self.lblMsg = QLabel(self)
        self.lblMsg.setStyleSheet(styles.MESSAGE_LABLE)
        self.lblMsg.setAlignment(Qt.AlignCenter)
        self.lblMsg.setVisible(False)
        self.lblMsg.clear()
        if not ownerInfo: self.ownerInfoSplash.setVisible(False)
        self.user = None
        self.userNextSession = None
        self.sortBySession = False
        self.selectedUsers = []
        self.laserNoUser = False
        self.shift = False
        self.farsi = False
        self.sex = 'female'
        self.bodyPart = ''
        self.case = 'I'
        self.cooling = 0
        self.energy = case.MIN_ENRGEY
        self.pulseWidth = case.MIN_PULSE_WIDTH
        self.frequency = case.MIN_FREQUENCY
        self.currentCounter = 0
        self.receivedTime = ()
        self.startupEditTime = False
        self.ready = False
        self.logingSettingAdmin = False
        self.findIndex = -1
        self.receivingSensorsData = True
        self.calibrationPageActive = False
        self.musicFiles = []
        self.po = promotions.PowerOption(self.mainPage)
        self.po.shutdown.connect(lambda: self.playShutdown('powerOff'))
        self.po.restart.connect(lambda: self.playShutdown('restart'))
        xpos = 1920 - self.po.size().width()
        ypos = self.btnPowerOption.iconSize().height() + 20
        self.po.move(xpos , ypos)
        self.energyWidget = promotions.Parameter(self.laserPage)
        self.energyWidget.move(230, 30)
        self.energyWidget.setParameter('Energy')
        self.frequencyWidget = promotions.Parameter(self.laserPage)
        self.frequencyWidget.move(230, 430)
        self.frequencyWidget.setParameter('Frequency')
        self.pulseWidthWidget = promotions.Parameter(self.laserPage)
        self.pulseWidthWidget.move(1110, 30)
        self.pulseWidthWidget.setParameter('Pulse Width')
        self.pulseWidthWidget.setEnabled(False)
        self.coolingWidget = promotions.Parameter(self.laserPage)
        self.coolingWidget.move(1110, 430)
        self.coolingWidget.setParameter('Cooling')
        self.coolingWidget.setValue(self.cooling)
        self.counterWidget = promotions.CounterParameter(self.laserPage)
        self.counterWidget.move(670, 230)
        self.counterWidget.setParameter('Counter')
        self.counterWidget.setValue(self.currentCounter)
        self.skinGradeWidget = promotions.SkinGrade(self.laserPage)
        self.skinGradeWidget.setGeometry(-1, 60, 200, 800)
        self.selectedBodyPart = promotions.SelectedBodyPart(self.laserPage)
        self.selectedBodyPart.setGeometry(1600,650, 600, 600)
        self.updateSystemTime(edit=True)
        self.initHwTest()
        self.initTutorials()   
        self.initPages()
        self.initTimers()
        self.initButtons()
        self.initTables()
        self.initTextboxes()
        self.initThemes()
        self.changeTheme(self.configs['Theme'])
        self.changeSliderColor(styles.SLIDER_GB, styles.SLIDER_GW)
        self.loadLocksTable()
        self.bodyPartsSignals()
        self.keyboardSignals()
        self.casesSignals()
        self.initMusics()
        self.checkUUID()
        communication.readTime()
        icon = QPixmap(paths.SPARK_ICON)
        self.lblSpark.setPixmap(icon.scaled(130, 130))
        self.lblSpark.setVisible(False)
        self.lblLasing.setVisible(False)
        if self.configs['Language'] == 'fa': self.changeLanguage(self.configs['Language'])
        self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        self.shortcut.activated.connect(self.exit)
        self.chbSlideTransition.setFixedSize(150, 48)
        self.chbSlideTransition.setChecked(self.configs['SlideTransition'])
        self.chbSlideTransition.toggled.connect(self.setTransition)
        self.chbTouchSound.setFixedSize(150, 48)
        self.chbTouchSound.setChecked(self.configs['TouchSound'])
        self.chbTouchSound.toggled.connect(self.setTouchSound)
        self.setTemp(0)
        op = QGraphicsOpacityEffect(self)
        op.setOpacity(0.8) 
        self.musicFrame.setGraphicsEffect(op)
        self.lblDemo = promotions.Label(self.mainPage)
        self.lblDemo.setGeometry(170, 200, 700, 700)
        self.lblDemo.setPixmap(QPixmap(paths.LASER_LOGO))
        self.txtFSdays.setText(str(self.configs['FutureSessionsDays']))
        mixer.Channel(0).set_volume(0.5)
        mixer.Channel(0).play(mixer.Sound(paths.STARTUP_SOUND))

    def onSplashClicked(self):
        self.stackedWidget.setCurrentWidget(self.mainPage) 
    
    def setTouchSound(self, active):
        self.configs['TouchSound'] = active
        if not self.saveConfigs():
            self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex], 4)

    def playTouchSound(self, sound):
        if self.configs['TouchSound']:
            if sound == 't':
                self.touchSound.play()
            else:
                self.keyboardSound.play()

    def initPages(self):
        self.stackedWidget.setCurrentWidget(self.splashPage)
        self.stackedWidgetLaser.setCurrentIndex(0)
        self.stackedWidgetSex.setCurrentIndex(0)
        self.stackedWidgetSettings.setCurrentIndex(0)
        self.stackedWidgetLock.setCurrentIndex(0)
        for sw in self.findChildren(QStackedWidget):
            sw.setTransitionDirection(Qt.Horizontal)
            sw.setTransitionSpeed(500)
            sw.setTransitionEasingCurve(QEasingCurve.OutQuart)
            sw.setSlideTransition(self.configs['SlideTransition'])

        self.stackedWidgetSex.setTransitionEasingCurve(QEasingCurve.OutBack)
        self.stackedWidgetSex.setTransitionDirection(Qt.Vertical)
        self.hwStackedWidget.setTransitionDirection(Qt.Vertical)
        
    def setTransition(self, checked):
        self.stackedWidget.setSlideTransition(checked)
        self.stackedWidgetSex.setSlideTransition(checked)
        self.stackedWidgetLaser.setSlideTransition(checked)
        self.stackedWidgetSettings.setSlideTransition(checked)
        self.hwStackedWidget.setSlideTransition(checked)
        self.configs['SlideTransition'] = checked
        if not self.saveConfigs():
            self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex], 4)

    def initTimers(self):        
        self.incDaysTimer = QTimer()
        self.decDaysTimer = QTimer()
        self.backspaceTimer = QTimer()
        self.hwWrongPassTimer = QTimer()
        self.resetCounterPassTimer = QTimer()
        self.updateFirmwareLabelTimer = QTimer()
        self.systemTimeTimer = QTimer()
        self.monitorSensorsTimer = QTimer()
        self.monitorReceivingSensors = QTimer()
        self.sparkTimer = QTimer()
        self.loadUsersTimer = QTimer()
        self.shutdownTimer = QTimer()
        self.restartTimer = QTimer()
        self.keyboardTimer = QTimer()
        self.messageTimer = QTimer()
        self.messageTimer.timeout.connect(self.clearMessageLabel)
        self.keyboardTimer.timeout.connect(lambda: self.setKeyboard('hide'))
        self.shutdownTimer.timeout.connect(self.powerOff)
        self.restartTimer.timeout.connect(self.restart)
        self.loadUsersTimer.timeout.connect(self.addUsersTable)
        self.loadUsersTimer.start(20)
        self.systemTimeTimer.timeout.connect(self.updateSystemTime)
        self.incDaysTimer.timeout.connect(lambda: self.incDecDayNS('inc'))
        self.decDaysTimer.timeout.connect(lambda: self.incDecDayNS('dec'))
        self.backspaceTimer.timeout.connect(self.typeToInput(lambda: 'backspace'))
        self.hwWrongPassTimer.timeout.connect(self.resetHardwareWrongPass)
        self.resetCounterPassTimer.timeout.connect(self.resetCounterWrongPass)
        self.sparkTimer.timeout.connect(self.hideSpark)
        self.monitorSensorsTimer.timeout.connect(self.monitorSensors)
        self.monitorReceivingSensors.timeout.connect(self.setReceivingSensorsDataTimer)

    def initTables(self):
        for tbl in self.findChildren(QTableWidget):
            op = QGraphicsOpacityEffect(self)
            op.setOpacity(0.8)
            tbl.verticalHeader().setDefaultSectionSize(75)                
            tbl.horizontalHeader().setFixedHeight(60)                
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)                    
            tbl.verticalHeader().setVisible(False)                    
            tbl.setGraphicsEffect(op)
        
        header = self.userInfoTable.horizontalHeader()
        header.setSectionResizeMode(0,  QHeaderView.ResizeToContents) 
        self.tableMusic.cellClicked.connect(self.musicSelected)

    def initButtons(self):
        self.btnEnLang.clicked.connect(lambda: self.changeLanguage('en'))
        self.btnFaLang.clicked.connect(lambda: self.changeLanguage('fa'))
        self.btnEnter.clicked.connect(self.unlockLIC)
        self.btnSort.clicked.connect(self.sortUsers)
        self.btnAdss.clicked.connect(self.playAdssDemo)
        self.btnEndSession.clicked.connect(lambda: self.setNextSession('lazer'))
        self.btnEndSession.clicked.connect(lambda: communication.enterPage(communication.MAIN_PAGE))
        self.btnPowerOption.clicked.connect(lambda: self.showPowerOptions('show'))
        self.btnStartSession.clicked.connect(self.startSession)
        self.btnStartUserSession.clicked.connect(self.startSession)
        self.btnSubmit.clicked.connect(lambda: self.changeAnimation('horizontal'))
        self.btnSubmit.clicked.connect(self.submitNewUser)
        self.btnSystemLogs.clicked.connect(self.hwPageChanged)
        self.btnSystemLogs.clicked.connect(self.enterLogsPage)
        self.btnHwTesst.clicked.connect(lambda: self.hwStackedWidget.setCurrentWidget(self.hwTestPage))
        self.btnHwTesst.clicked.connect(self.hwPageChanged)
        self.btnHwTesst.clicked.connect(lambda: communication.enterPage(communication.HARDWARE_TEST_PAGE))
        self.btnMusic.clicked.connect(lambda: self.changeAnimation('horizontal'))
        self.btnMusic.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.musicPage))
        self.btnBackMusic.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.btnBackMusic.clicked.connect(lambda: self.musicPage.setVisible(False))
        self.btnBackNewSession.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.btnBackManagement.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.btnBackManagement.clicked.connect(lambda: self.txtSearchUsers.clear())
        self.btnBackManagement.clicked.connect(self.saveUsers)
        self.btnBackSettings.clicked.connect(self.backSettings)
        self.btnBackSettings.clicked.connect(self.systemTimeTimer.stop)
        self.btnBackSettings.clicked.connect(self.settingsMenuSelected('back'))
        self.btnBackEditUser.clicked.connect(lambda: self.changeAnimation('horizontal'))
        self.btnBackEditUser.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.userManagementPage))
        self.btnSettings.clicked.connect(lambda: self.changeAnimation('horizontal'))
        self.btnSettings.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))
        self.btnUiSettings.clicked.connect(lambda: self.stackedWidgetSettings.setCurrentWidget(self.uiPage))
        self.btnEnterHw.clicked.connect(self.loginHardwareSettings)
        self.btnHwSettings.clicked.connect(self.btnHwSettingClicked)
        self.btnSaveInfo.clicked.connect(self.saveUserInfo)
        self.btnDeleteUser.clicked.connect(self.deleteUserFromDB)
        self.btnUserManagement.clicked.connect(lambda: self.changeAnimation('horizontal'))
        self.btnUserManagement.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.userManagementPage))
        self.btnNotify.clicked.connect(lambda: self.changeAnimation('horizontal'))
        self.btnNotify.clicked.connect(self.setFutureSessionsPage)
        self.btnNotify.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.notifyPage))
        self.btnBackNotify.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.btnTutorials.clicked.connect(lambda: self.changeAnimation('horizontal'))
        self.btnTutorials.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.tutorialPage))
        self.btnBackTutorials.clicked.connect(lambda: self.player.close(fast=True))
        self.btnBackTutorials.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.btnNextSession.clicked.connect(lambda: self.changeAnimation('vertical'))
        self.btnNextSession.clicked.connect(lambda: self.setNextSession('edit'))
        self.btnCancelNS.clicked.connect(self.cancelNextSession)
        self.btnCancelNS.clicked.connect(lambda: self.setKeyboard('hide'))
        self.btnOkNS.clicked.connect(lambda: self.setKeyboard('hide'))
        self.btnDecDayNS.clicked.connect(lambda: self.incDecDayNS('dec'))
        self.btnIncDayNS.clicked.connect(lambda: self.incDecDayNS('inc'))
        self.btnDecDayFS.clicked.connect(lambda: self.incDecDayFS('dec'))
        self.btnIncDayFS.clicked.connect(lambda: self.incDecDayFS('inc'))
        self.btnOkNS.clicked.connect(self.saveNextSession)
        self.btnMale.clicked.connect(lambda: self.setSex('male'))
        self.btnFemale.clicked.connect(lambda: self.setSex('female'))
        self.btnBackspace.pressed.connect(lambda: self.backspaceTimer.start(100))
        self.btnBackspace.released.connect(lambda: self.backspaceTimer.stop())
        self.btnIncDayNS.pressed.connect(lambda: self.incDaysTimer.start(100))
        self.btnIncDayNS.released.connect(lambda: self.incDaysTimer.stop())
        self.btnDecDayNS.pressed.connect(lambda: self.decDaysTimer.start(100))
        self.btnDecDayNS.released.connect(lambda: self.decDaysTimer.stop())
        self.btnDecDac.clicked.connect(lambda: self.setDac(operation='dec'))
        self.btnIncDac.clicked.connect(lambda: self.setDac(operation='inc'))
        self.energyWidget.inc.connect(lambda: self.setEnergy('inc'))
        self.energyWidget.dec.connect(lambda: self.setEnergy('dec'))
        self.sliderEnergyCalib.sliderMoved.connect(lambda v: self.setEnergySlider(v*10))
        self.sliderEnergyCalib.valueChanged.connect(lambda v: self.setCurrentCoeff(v*10))
        self.frequencyWidget.inc.connect(lambda: self.setFrequency('inc'))
        self.frequencyWidget.dec.connect(lambda: self.setFrequency('dec'))
        self.sliderFrequencyCalib.sliderMoved.connect(self.setFrequencySlider)
        self.sliderFrequencyCalib.sliderReleased.connect(self.frequencySliderReleased)
        self.coolingWidget.dec.connect(lambda: self.setCooling('dec'))
        self.coolingWidget.inc.connect(lambda: self.setCooling('inc'))
        self.skinGradeWidget.btnSave.clicked.connect(self.saveCase)
        self.btnDeleteLogs.clicked.connect(self.deleteLogs)
        self.btnPlayMusic.clicked.connect(self.playMusic)
        self.btnLoadMusic.clicked.connect(self.startLoadingMusics)
        self.btnFindNext.clicked.connect(lambda : self.findWord(self.txtSearchLogs.text()))
        self.btnFindBefor.clicked.connect(lambda : self.findWord(self.txtSearchLogs.text(), True))
        self.btnSaveHw.clicked.connect(self.saveHwSettings)
        self.btnResetCounter.clicked.connect(self.btnResetCounterClicked)
        self.btnResetCounter2.clicked.connect(self.checkResetCounterPass)
        self.btnReady.clicked.connect(lambda: self.setReady(True))
        self.btnReadyCalib.clicked.connect(lambda: self.setReady(True))
        self.btnStandby.clicked.connect(lambda: self.setReady(False))
        self.btnStandByCalib.clicked.connect(lambda: self.setReady(False))
        self.btnUUIDEnter.clicked.connect(self.unlockUUID)
        self.btnHwinfo.clicked.connect(lambda: self.hwStackedWidget.setCurrentWidget(self.infoPage))
        self.btnHwinfo.clicked.connect(lambda: self.enterSettingPage(communication.REPORT))
        self.btnSystemLock.clicked.connect(lambda: self.hwStackedWidget.setCurrentWidget(self.lockSettingsPage))
        self.btnSystemLock.clicked.connect(self.hwPageChanged)
        self.btnSystemLock.clicked.connect(lambda: communication.lockPage(communication.REPORT))
        self.btnCalibration.clicked.connect(self.enterCalibrationPage)
        self.btnAddLock.clicked.connect(self.addLock)
        self.btnResetLock.clicked.connect(self.clearLocksTabel)
        self.btnBackLaser.clicked.connect(lambda: self.changeAnimation('horizontal'))
        self.btnBackLaser.clicked.connect(lambda: self.stackedWidgetLaser.setCurrentWidget(self.bodyPartPage))
        self.btnBackLaser.clicked.connect(lambda: self.btnBackLaser.setVisible(False))
        self.btnBackLaser.clicked.connect(lambda: self.setReady(False))
        self.btnBackLaser.clicked.connect(lambda: communication.enterPage(communication.BODY_PART_PAGE))
        self.btnBackLaser.setVisible(False)
        self.btnUpdateFirmware.clicked.connect(self.startUpdateSystem)
        self.btnShowSplash.clicked.connect(self.showSplash)
        self.btnDelSelectedUsers.clicked.connect(self.removeSelectedUsers)
        self.btnSelectAll.clicked.connect(self.selectAllUsers)
        self.btnResetMsgNo.clicked.connect(lambda : self.showResetCounterConfirm('hide'))
        self.btnResetMsgYes.clicked.connect(self.resetCounterYes)
        self.btnSetDac.clicked.connect(self.sendDacVoltage)
        self.btnApplyCoeff.clicked.connect(self.applyCalibrationCoeffs)
        self.selectAllFlag = False
        self.btnLoop.clicked.connect(self.setLoopMusic)
        self.LoopMusicFlag = self.configs['LoopMusic']
        sensors = [
            'btnPhysicalDamage', 'btnOverHeat', 'btnTemp',
            'btnLock', 'btnWaterLevel', 'btnWaterflow',
            'btnOverHeatCalib', 'btnPhysicalDamageCalib', 
            'btnLockCalib', 'btnTempCalib', 'btnWaterLevelCalib',
            'btnWaterflowCalib', 'txtTempCalib'
        ]
        keyboardButtons = list(chain(
            utility.getLayoutWidgets(self.keyboardRow1, QPushButton),
            utility.getLayoutWidgets(self.keyboardRow2, QPushButton),
            utility.getLayoutWidgets(self.keyboardRow3, QPushButton),
            utility.getLayoutWidgets(self.numRow1, QPushButton),
            utility.getLayoutWidgets(self.numRow2, QPushButton),
            utility.getLayoutWidgets(self.numRow3, QPushButton)
        ))
        keyboardButtons.append(self.btnBackspace)
        keyboardButtons.append(self.btnReturn)
        keyboardButtons.append(self.btnShift)
        keyboardButtons.append(self.btnFa)
        keyboardButtons.append(self.btnSpace)
        allButtons = self.findChildren(QPushButton) 

        for btn in allButtons:
            if btn.objectName() == 'btnSelectedBodyPart':
                continue
            elif 'btnCooling' in btn.objectName() or 'Test' in btn.objectName():
                continue
            elif 'Pass' in btn.objectName() or 'Fail' in btn.objectName():
                continue
            elif btn in keyboardButtons:
                btn.pressed.connect(lambda: self.playTouchSound('k'))
            elif btn.objectName() not in sensors:
                btn.pressed.connect(lambda: self.playTouchSound('t'))       

        buttons = utility.getFrameWidgets(self.hwbtnsFrame, QPushButton)
        for btn in buttons:
            if btn.objectName() == 'btnSaveHw':
                continue
            btn.clicked.connect(self.settingsMenuSelected(btn))
    
    def initThemes(self):
        photos = []
        for f in ['.png', '.jpg', '.jpeg']:
            photos.extend(glob(os.path.join('ui/images/themes', '*' + f)))

        cols = 2
        rows = len(photos) // cols if len(photos) % cols == 0 else len(photos) // cols + 1

        def makeSlot(x):
            return lambda : self.changeTheme(x)

        for x in range(rows):
            for y in range(cols):
                if photos:
                    photo = photos.pop()
                    btn = QPushButton()
                    btn.setIconSize(QSize(150, 100))
                    btn.setIcon(QIcon(QPixmap(photo).scaled(150, 100)))
                    btn.clicked.connect(makeSlot(photo))
                    self.themeLayout.addWidget(btn, x, y)

    def initTextboxes(self):
        self.txtNumber.returnPressed.connect(self.startSession)
        self.txtNameSubmit.returnPressed.connect(self.submitNewUser)
        self.txtNumberSubmit.returnPressed.connect(self.submitNewUser)
        self.txtHwPass.returnPressed.connect(self.loginHardwareSettings)
        self.txtOwnerInfo.returnPressed.connect(self.showSplash)
        self.txtResetCounterPass.returnPressed.connect(self.checkResetCounterPass)
        self.txtReadValue.returnPressed.connect(self.applyCalibrationCoeffs)
        self.txtPassword.returnPressed.connect(self.unlockLIC)
        self.txtPassUUID.returnPressed.connect(self.unlockUUID)
        
        for txt in self.findChildren(promotions.LineEdit):
            if isinstance(txt, promotions.LineEdit):
                txt.fIn.connect(lambda: self.setKeyboard('show'))

        self.txtOwnerInfo.setText(self.configs['OwnerInfo'])
        self.txtOwnerInfo.textChanged.connect(self.setOwnerInfo)
        self.txtDays.textChanged.connect(self.setDateText)
        self.txtNsYear.textChanged.connect(self.setDaysText)
        self.txtNsMonth.textChanged.connect(self.setDaysText)
        self.txtNsDay.textChanged.connect(self.setDaysText)
        input_validator = QRegExpValidator(QRegExp("\d*"), self.txtDays)
        self.txtDays.setValidator(input_validator)
        self.txtEditMinute.setValidator(input_validator)
        self.txtEditHour.setValidator(input_validator)
        self.txtLockYear.setValidator(input_validator)        
        self.txtLockMonth.setValidator(input_validator)
        self.txtLockDay.setValidator(input_validator)
        self.txtEditDay.setValidator(input_validator)
        self.txtEditMonth.setValidator(input_validator)
        self.txtEditYear.setValidator(input_validator)        
        self.txtNsYear.setValidator(input_validator)    
        self.txtNsMonth.setValidator(input_validator)
        self.txtNsDay.setValidator(input_validator)
        reg_ex = QRegExp("^-?[0-9]\d*(\.\d+)?$")
        input_validator = QRegExpValidator(reg_ex, self.txtReadValue)
        self.txtReadValue.setValidator(input_validator)     
        self.txtDays.setText('30')
        self.txtSearchUsers.textChanged.connect(self.searchUsers)
        self.txtSearchMusic.textChanged.connect(self.searchMusic)

    def initHwTest(self):
        self.handPiece = promotions.Relay(self.btnHandpiece, self.btnPassHP, self.btnFailHP, 0)
        self.radiator = promotions.Relay(self.btnRadiator, self.btnPassRad, self.btnFailRad, 1)
        self.laserPower = promotions.Relay(self.btnLaserPower, self.btnPassLP, self.btnFailLP, 2)
        self.airCooling = promotions.Relay(self.btnAirCooling, self.btnPassAC, self.btnFailAC, 3)
        self.reservedRelay = promotions.Relay(self.btnReserved, self.btnPassRes, self.btnFailRes, 4)
        self.driverCurrent = promotions.DriverCurrent(self.btnDriverCurrentStart, self.widget, 6)
        self.flowMeter = promotions.SensorTest(txt=self.txtFlowMeter, unit='Lit/min')
        self.waterTempSensor = promotions.SensorTest(txt=self.txtWaterTempSensor, unit='°C')
        self.handpieceTemp = promotions.SensorTest(txt=self.txtHandpieceTemp, unit='°C')
        self.airTempSensor = promotions.SensorTest(txt=self.txtAirTempSensor, unit='°C')
        self.interLockTest = promotions.SensorTest(btnOk=self.btnInterLockPass, btnNotOk=self.btnInterLockFail)
        self.waterLevelTest = promotions.SensorTest(btnOk=self.btnWaterLevelPass, btnNotOk=self.btnWaterLevelFail)

        self.serialC.handPiece.connect(self.handPiece.setTests)
        self.serialC.radiator.connect(self.radiator.setTests)
        self.serialC.laserPower.connect(self.laserPower.setTests)
        self.serialC.airCooling.connect(self.airCooling.setTests)
        self.serialC.reservedRelay.connect(self.reservedRelay.setTests)
        self.serialC.driverCurrent.connect(self.driverCurrent.setValue)
        self.serialC.dacVoltage.connect(lambda v: self.setDac(value=v))
        self.serialC.flowMeter.connect(self.flowMeter.setValue)
        self.serialC.waterTempSensor.connect(self.waterTempSensor.setValue)
        self.serialC.handpieceTemp.connect(self.handpieceTemp.setValue)
        self.serialC.airTempSensor.connect(self.airTempSensor.setValue)
        self.serialC.interLockTest.connect(self.interLockTest.setOk)
        self.serialC.waterLevelTest.connect(self.waterLevelTest.setOk)

        self.dacSlider.setSingleStep(0.01)
        self.dacSlider.setMinimum(0.2)
        self.dacSlider.setMaximum(1.4)
        self.dacSlider.setValue(1.2)
        self.dacSlider.doubleValueChanged.connect(lambda: self.lblDacValue.setText(f"{self.dacSlider.value()}"))
        self.dacSlider.doubleValueChanged.connect(self.setDacSlidrColor)
    
    def setDacSlidrColor(self):
        if self.configs['Theme'] in ['C1', 'C2', 'C4']:
            self.dacSlider.setStyleSheet(styles.DAC_SLIDER_B_CHANGED)
        else:
            self.dacSlider.setStyleSheet(styles.DAC_SLIDER_W_CHANGED)

    def setDac(self, operation='set', value=0):
        if operation == 'inc':
            self.dacSlider.setValue(self.dacSlider.value() + 0.01)
        elif operation == 'dec':
            self.dacSlider.setValue(self.dacSlider.value() - 0.01)
        else:
            self.dacSlider.setValue(value)

        self.lblDacValue.setText(f"{self.dacSlider.value()}")

    def sendDacVoltage(self):
        communication.sendPacket(
            {'dacVolt': 7},
            {'dacVolt': str(self.dacSlider.value())},
            communication.HARDWARE_TEST_PAGE, 
            communication.WRITE
        )
        self.changeSliderColor(styles.SLIDER_GB, styles.SLIDER_GW)  

    def playAdssDemo(self):
        self.changeAnimation('vertical')
        self.setKeyboard('hide')
        self.adssMedia.setMedia(QMediaContent(QUrl.fromLocalFile(paths.ADSS_DEMO)))
        self.adssMedia.play()
        index = self.stackedWidget.indexOf(self.adssPage)
        self.stackedWidget.setCurrentIndex(index)
    
    def adssDemoEnd(self):
        index = self.stackedWidget.indexOf(self.adssPage)
        if self.stackedWidget.currentIndex() == index:
            self.adssMedia.setMedia(QMediaContent())
            self.stackedWidget.setCurrentWidget(self.mainPage)       
            
    def setSensorFlags(self, flags):
        self.sensorFlags = flags

    def setTemp(self, value):
        self.txtTemp.setText(str(value) + ' °C')
        self.txtTempCalib.setText(str(value) + ' °C')

    def setReceivingSensorsData(self):
        self.receivingSensorsData = True

    def setReceivingSensorsDataTimer(self):
        if self.receivingSensorsData:
            self.receivingSensorsData = False
        else:
            self.sensorFlags = [True, True, True, False, False, True]
            self.setTemp(0)

    def monitorSensors(self):
        index = self.stackedWidget.indexOf(self.laserMainPage)
        if self.stackedWidget.currentIndex() == index:
            page = 'Laser'
        else:
            page = 'Calib'

        self.sensors.toggle(self.sensorFlags, page)

        if any(self.sensorFlags):
            if self.ready:
                self.setReady(False)    

    def enterCalibrationPage(self):
        self.hwStackedWidget.setCurrentWidget(self.calibrationPage)
        self.calibrationPageActive = True
        fields = {
                'energy': self.energy, 
                'pulseWidth': self.pulseWidth,
                'frequency': self.frequency, 
                'ready-standby': 'Ready' if self.ready else 'StandBy'
            } 
        communication.laserPage(fields) # testing ...
        self.txtSpotSizeCalib.setText(self.configs['SpotSizeArea'])
        self.setCurrentCoeff(self.sliderEnergyCalib.value() * 10)
        self.monitorSensorsTimer.start(500)
        self.monitorReceivingSensors.start(3000)
    
    def setCurrentCoeff(self, value):
        index, interval = utility.getCoeffIndex(value, interval = True)
        self.txtCurrentCoeff.setText(f"{interval} → {round(self.coefficients[index], 2)}")
        
    def applyCalibrationCoeffs(self):
        try:
            readValue = self.txtReadValue.text()
            readValue = float(readValue) if readValue else self.sliderEnergyCalib.value() * 10
            energy = self.sliderEnergyCalib.value() * 10
            ratio = energy / readValue

            if not 0.8 <= ratio <= 1.2:
                raise Exception('out of range')

            index = utility.getCoeffIndex(energy)
            self.coefficients[index] = ratio
            self.setCurrentCoeff(energy)

            if not utility.saveCoefficients(self.coefficients):
                self.setMessageLabel(lang.TEXT['saveCoeffError'][self.langIndex], 4)
            else:
                self.setMessageLabel(lang.TEXT['Coeff'][self.langIndex] + str(round(ratio, 2)), 4)

        except Exception:
            self.setMessageLabel(lang.TEXT['CoeffError'][self.langIndex], 3)
               
    def hwPageChanged(self):
        if self.calibrationPageActive:
            if self.ready:
                self.setReady(False)

            self.monitorSensorsTimer.stop()
            self.monitorReceivingSensors.stop()
        
        self.calibrationPageActive = False

    def changeTheme(self, theme):
        inc = QIcon()
        dec = QIcon()
        if utility.is_dark(theme):
            self.sliderEnergyCalib.setStyleSheet(styles.SLIDER_GW)           
            self.sliderFrequencyCalib.setStyleSheet(styles.SLIDER_GW)
            self.sliderPulseWidthCalib.setStyleSheet(styles.SLIDER_DISABLED_GW)
            self.dacSlider.setStyleSheet(styles.SLIDER_GW)
            inc.addPixmap(QPixmap(paths.INC_BLUE))
            dec.addPixmap(QPixmap(paths.DEC_BLUE))
        else:          
            self.sliderEnergyCalib.setStyleSheet(styles.SLIDER_GB)
            self.sliderFrequencyCalib.setStyleSheet(styles.SLIDER_GB)
            self.sliderPulseWidthCalib.setStyleSheet(styles.SLIDER_DISABLED_GB)
            self.dacSlider.setStyleSheet(styles.SLIDER_GB)
            inc.addPixmap(QPixmap(paths.INC_BLACK))
            dec.addPixmap(QPixmap(paths.DEC_BLACK))

        self.btnDecDac.setIcon(dec)
        self.btnIncDac.setIcon(inc)
        style = """QWidget#centralwidget {{
                    border-image: url(ui/images/themes/{0}) 0 0 0 0 stretch stretch;
                }}""".format(pathlib.Path(theme).name)
        
        if os.path.isfile(theme):
            self.centralWidget().setStyleSheet(style)
        else:
            self.centralWidget().setStyleSheet('background-color: rgb(32, 74, 135)')


        if utility.is_dark(theme):
            self.po.setStyleSheet(styles.POWER_OPTION_L)
        else:
            self.po.setStyleSheet(styles.POWER_OPTION_D)

        self.configs['Theme'] = theme
        if not self.saveConfigs():
            self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex], 4)

    def setOwnerInfo(self, text):
        self.ownerInfoSplash.setText(text)
        self.ownerInfoSplash.adjustSize()
        self.configs['OwnerInfo'] = text
        if not self.saveConfigs():
            self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex], 4)

        if not text:
            self.ownerInfoSplash.setVisible(False)
        else:
            self.ownerInfoSplash.setVisible(True)
        if text and utility.isFarsi(text):
            self.ownerInfoSplash.setStyleSheet(styles.OWNER_INFO_STYLE_FA)
        else:
            self.ownerInfoSplash.setStyleSheet(styles.OWNER_INFO_STYLE_EN)

    def showSplash(self):
        self.setKeyboard('hide')
        index = self.stackedWidget.indexOf(self.splashPage)
        self.stackedWidget.setCurrentIndex(index) 
        self.stackedWidgetSettings.setCurrentWidget(self.settingsMenuPage)  

    def receiveDate(self, date):
        self.receivedTime += date

    def adjustTime(self, clock):
        self.receivedTime += clock + (0,)
        try:
            if not self.startupEditTime:
                utility.setSystemTime(self.receivedTime)
                self.startupEditTime = True
                nextDate = jdatetime.datetime.now() + jdatetime.timedelta(120) 
                self.txtLockYear.setText(str(nextDate.year))
                self.txtLockMonth.setText(str(nextDate.month))
                self.txtLockDay.setText(str(nextDate.day)) 
                self.checkLIC()
        except Exception as e:
            utility.log('Startup Setting Time', str(e) + '\n')
            
    def playShutdown(self, i):
        mixer.Channel(0).set_volume(0.5)
        mixer.Channel(0).play(mixer.Sound(paths.SHUTDOWN_SOUND))
        self.musicSound.stop()
        self.setKeyboard('hide')
        if i == 'powerOff':
            self.shutdownTimer.start(3000)
        else:
            self.restartTimer.start(3000)
            self.lblShuttingdown.setText('Restarting...')
        self.shutdownMovie.start()
        self.changeAnimation('vertical')
        self.stackedWidget.setSlideTransition(True)
        self.stackedWidget.setCurrentWidget(self.shutdownPage)

    def exit(self):
        utility.log('Exit Shortcut', 'Shortcut activated. Exiting from UI...\n')
        communication.enterPage(communication.SHUTDONW_PAGE)
        self.serialC.closePort()
        communication.gpioCleanup()
        self.close()

    def powerOff(self):
        communication.enterPage(communication.SHUTDONW_PAGE)
        self.serialC.closePort()
        communication.gpioCleanup()
        if utility.platform.system() == 'Windows':
            self.close()
        else:
            os.system('poweroff')
        
    def restart(self):
        communication.enterPage(communication.SHUTDONW_PAGE)
        self.serialC.closePort()
        communication.gpioCleanup()
        if utility.platform.system() == 'Windows':
            self.close()
        else:
            os.system('reboot')

    def updateGuiResult(self, result):
        if result == 'Done GUI':
            utility.log('Update Firmware', 'GUI successfully updated.\n')
            for i in range(5, -1, -1):
                self.setMessageLabel(f'Your system will restart in {i} seconds...')
                QApplication.processEvents()
                time.sleep(1)
            self.playShutdown('restart')
        else:
            self.setMessageLabel(result)
            self.btnUpdateFirmware.setDisabled(False)

    def setUpdateFirmwareProgress(self, status):
        self.setMessageLabel(status, 100)
        if status == 'Rebooting Control System ...':
            self.btnUpdateFirmware.setDisabled(False)
            utility.log('Update Firmware', 'Firmware successfully updated.')
            self.setMessageLabel('Rebooting Control System ...',  6)

    def startUpdateSystem(self):
        self.btnUpdateFirmware.setDisabled(True)
        self.setMessageLabel('Please wait...')
        self.updateT.start()

    def shot(self):
        self.currentCounter += 1
        self.counterWidget.setValue(self.currentCounter)
        self.sparkTimer.start(1000//self.frequency + 100)
        self.lblSpark.setVisible(True)
        self.lblLasing.setVisible(True)
        if not self.laserNoUser:
            self.user.incShot(self.bodyPart)

    def hideSpark(self):
        self.sparkTimer.stop()
        self.lblLasing.setVisible(False)
        self.lblSpark.setVisible(False)

    def updateSystemTime(self, edit=False):
        now = jdatetime.datetime.now()
        hour = "{:02d}".format(now.hour) 
        minute = "{:02d}".format(now.minute)
        second = now.second
        year = str(now.year)
        month = "{:02d}".format(now.month)
        day = "{:02d}".format(now.day)
        self.txtSysClock.setText(now.strftime('%H : %M : %S'))
        self.txtSysDate.setText(now.strftime('%Y / %m / %d'))

        if second == 0 or edit:
            if edit:
                nextDate = jdatetime.datetime.today() + jdatetime.timedelta(120) 
                self.txtLockYear.setText(str(nextDate.year))
                self.txtLockMonth.setText(str(nextDate.month))
                self.txtLockDay.setText(str(nextDate.day))
            self.txtEditYear.setText(year)
            self.txtEditMonth.setText(month)
            self.txtEditDay.setText(day)
            self.txtEditHour.setText(hour)
            self.txtEditMinute.setText(minute)

    def addLock(self):
        try:
            year = int(self.txtLockYear.text())
            month = int(self.txtLockMonth.text())
            day = int(self.txtLockDay.text())
        except ValueError:
            self.setMessageLabel('Please fill in the fields.', 4)
            return

        try:
            date = jdatetime.datetime(year, month, day)
        except Exception as e:
            self.setMessageLabel(str(e).capitalize() + '.')
            return

        numOfLocks = len(self.configs['Locks'])

        if numOfLocks == 3:
            self.setMessageLabel(lang.TEXT['maxLock'][self.langIndex])
            return

        if utility.getDiff(date) <= -1:
            self.setMessageLabel(lang.TEXT['passedDate'][self.langIndex])
            return

        for lock in self.configs['Locks']:
            if (date - utility.toJalali(lock.date)).days <= 0:
                self.setMessageLabel(lang.TEXT['anyLockBefor'][self.langIndex])
                return
        
        license = self.configs['License'][f'{numOfLocks + 1}']
        lock = Lock(date.togregorian(), license)
        self.configs['Locks'].append(lock)
        if not self.saveConfigs():
            self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex])

        info = f"Lock license: {license}\nLock date: {utility.toJalali(lock.date).strftime('%Y-%m-%d')}\n"
        utility.log('Lock added', info)
        nextDate = date + jdatetime.timedelta(120) 
        self.txtLockYear.setText(str(nextDate.year))
        self.txtLockMonth.setText(str(nextDate.month))
        self.txtLockDay.setText(str(nextDate.day))        
        self.loadLocksTable()

    def loadLocksTable(self):
        self.configs['Locks'].sort(key=lambda x: x.date)
        locks = self.configs['Locks']
        self.tableLock.setRowCount(len(locks))
        for i, lock in enumerate(locks):
            date = promotions.TableWidgetItem(str(utility.toJalali(lock.date).date()))
            self.tableLock.setItem(i, 0, date)
            diff = utility.getDiff(utility.toJalali(lock.date))
            status = ''
            if diff == 0:
                status = lang.TEXT['today'][self.langIndex]
            elif diff == -1:
                status = lang.TEXT['1dayPassed'][self.langIndex]
            elif diff < -1:
                status = f'{abs(diff)} {lang.TEXT["nDayPassed"][self.langIndex]}'
            elif diff == 1:
                status = lang.TEXT['1dayleft'][self.langIndex]
            else:
                status = f'{diff} {lang.TEXT["nDayLeft"][self.langIndex]}'

            status = promotions.TableWidgetItem(status)
            self.tableLock.setItem(i, 1, status)
            paid = promotions.TableWidgetItem(
                lang.TEXT['yes'][self.langIndex] if lock.paid else lang.TEXT['no'][self.langIndex]
            )
            self.tableLock.setItem(i, 2, paid)
            
    def clearLocksTabel(self):
        self.configs['Locks'] = []
        if not self.saveConfigs():
            self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex])

        utility.log('Lock reset', 'Lock table cleared.\n')
        self.updateSystemTime(edit=True)
        self.loadLocksTable()

    def unlockUUID(self):
        user_pass = self.txtPassUUID.text().upper()
        hwid = utility.getID()
        hwid += '@mohammaad_haji'
        
        if hashlib.sha256(hwid.encode()).hexdigest()[:10].upper() == user_pass:
            index = self.stackedWidgetLock.indexOf(self.enterLaserPage)
            self.stackedWidgetLock.setCurrentIndex(index)
            
            with open(paths.COPY_RIGHT_PASS, 'w') as f:
                f.write(user_pass)
            
            self.saveConfigs()
            self.setKeyboard('hide')
        else:
            self.txtPassUUID.setFocus()
            self.txtPassUUID.selectAll()
            self.setMessageLabel(lang.TEXT['wrongPass'][self.langIndex], 3)

    def checkUUID(self):
        hwid = utility.getID()
        self.txtUUID.setText(hwid)
        hwid += '@mohammaad_haji'
        password = ''
        if os.path.isfile(paths.COPY_RIGHT_PASS):
            with open(paths.COPY_RIGHT_PASS, 'r') as f:
                password = f.read()

        if not hashlib.sha256(hwid.encode()).hexdigest()[:10].upper() == password:
            index = self.stackedWidgetLock.indexOf(self.copyRightPage)
            self.stackedWidgetLock.setCurrentIndex(index)

    def getLocks(self):
        locks = []
        for lock in self.configs['Locks']:
            date = utility.toJalali(lock.date)
            if not lock.paid and utility.getDiff(date) <= 0:
                locks.append(lock)

        locks.sort(key=lambda x: x.date)
        return locks

    def unlockLIC(self):
        userPass = self.txtPassword.text().strip()
        locks = self.getLocks()

        if not locks:
            self.setKeyboard('hide')
            index = self.stackedWidgetLock.indexOf(self.enterLaserPage)
            self.stackedWidgetLock.setCurrentIndex(index)
            self.checkUUID()
            return

        if locks[0].checkPassword(userPass):
            self.saveConfigs()
            self.setKeyboard('hide')
            index = self.stackedWidgetLock.indexOf(self.enterLaserPage)
            self.stackedWidgetLock.setCurrentIndex(index)
            self.checkUUID()
        else:
            self.setMessageLabel(lang.TEXT['wrongPass'][self.langIndex], 3)
            self.txtPassword.setFocus()
            self.txtPassword.selectAll()

    def checkLIC(self):
        locks = self.getLocks()

        if locks:
            index = self.stackedWidgetLock.indexOf(self.licLockPage)
            self.stackedWidgetLock.setCurrentIndex(index)
            self.txtID.setText(str(locks[0].license))

    def loginHardwareSettings(self):
        password = self.txtHwPass.text()
        self.hwStackedWidget.setCurrentIndex(0)
        txts = chain(
            utility.getLayoutWidgets(self.prodGridLayout, QLineEdit),
            utility.getLayoutWidgets(self.laserGridLayout, QLineEdit),
            utility.getLayoutWidgets(self.driverGridLayout, QLineEdit),
            utility.getLayoutWidgets(self.embeddGridLayout, QLineEdit)
        )
        self.btnHwinfo.setStyleSheet(styles.SETTINGS_MENU_SELECTED)
        if password == HW_PAGE_ADMIN_PASSWORD:
            for txt in txts:
                txt.setReadOnly(False)
                txt.setDisabled(False)

            self.logingSettingAdmin = True
            self.txtRpiVersion.setReadOnly(True)
            self.txtMonitor.setReadOnly(True)
            self.txtOsSpecification.setReadOnly(True)
            self.txtTotalShotCounter.setReadOnly(True)
            self.txtRpiVersion.setDisabled(True)
            self.txtMonitor.setDisabled(True)            
            self.txtOsSpecification.setDisabled(True)
            self.txtTotalShotCounter.setDisabled(True)
            self.setKeyboard('hide')
            self.showHwPassInput('hide')
            self.readHwInfo()
            self.loadLocksTable()
            self.hwbtnsFrame.show()
            self.txtRpiVersion.setVisible(True)
            self.lblRpiVersion.setVisible(True)            
            self.txtHwPass.clear()
            self.systemTimeTimer.start(1000)
            self.stackedWidgetSettings.setCurrentWidget(self.hWPage)
            self.enterSettingPage(communication.REPORT)

        elif password == HW_PAGE_USER_PASSWORD:
            for txt in txts:
                txt.setReadOnly(True)
                txt.setDisabled(True)

            self.logingSettingAdmin = False
            self.setKeyboard('hide')
            self.showHwPassInput('hide')
            self.readHwInfo()
            self.hwbtnsFrame.hide()
            self.txtRpiVersion.setVisible(False)
            self.lblRpiVersion.setVisible(False)
            self.txtHwPass.clear()
            self.stackedWidgetSettings.setCurrentWidget(self.hWPage)
            self.enterSettingPage(communication.REPORT)
            
        else:
            self.txtHwPass.setStyleSheet(styles.TXT_HW_WRONG_PASS)
            self.txtHwPass.selectAll()
            self.txtHwPass.setFocus()
            self.hwWrongPassTimer.start(4000)

    def resetHardwareWrongPass(self):
        self.hwWrongPassTimer.stop()
        self.txtHwPass.setStyleSheet(styles.TXT_HW_PASS)

    def resetCounterWrongPass(self):
        self.resetCounterPassTimer.stop()
        self.txtResetCounterPass.setStyleSheet(styles.TXT_RESET_COUNTER_PASS)

    def readHwInfo(self):
        self.txtOsSpecification.setText(utility.getOS())
        self.txtRpiVersion.setText(utility.getRPiModel())
        self.txtMonitor.setText(utility.monitorInfo())
        self.txtSerialNumber.setText(self.configs['SerialNumber'])                
        self.txtLaserDiodeEnergy.setText(self.configs['LaserDiodeEnergy'])                
        self.txtLaserBarType.setText(self.configs['LaserBarType'])
        self.txtSpotSize.setText(self.configs['SpotSizeArea'])
        self.txtLaserWavelength.setText(self.configs['LaserWavelength'])                
        self.txtDriverVersion.setText(self.configs['DriverVersion'])                
        self.txtMainControlVersion.setText(self.configs['MainControlVersion'])                
        self.txtFirmwareVersion.setText(self.configs['FirmwareVersion'])
        self.txtProductionDate.setText(self.configs['ProductionDate']) 
        self.txtGuiVersion.setText(self.configs['GuiVersion'])
        if self.logingSettingAdmin:
            text = str(self.configs['TotalShotCounter']) + ' : ' + str(self.configs['TotalShotCounterAdmin'])
        else:
            text = str(self.configs['TotalShotCounter'])
        self.txtTotalShotCounter.setText(text)              

    def saveHwSettings(self):
        index = self.hwStackedWidget.indexOf(self.systemLogPage)
        if self.hwStackedWidget.currentIndex() == index:
            return
 
        index = self.hwStackedWidget.indexOf(self.lockSettingsPage)
        if self.hwStackedWidget.currentIndex() == index:
            try:
                year = int(self.txtEditYear.text())
                month = int(self.txtEditMonth.text())
                day = int(self.txtEditDay.text())
                gregorian = jdatetime.datetime(year, month, day).togregorian()
                year = gregorian.year
                month = gregorian.month
                day = gregorian.day
                hour = int(self.txtEditHour.text())
                minute = int(self.txtEditMinute.text())
                second = jdatetime.datetime.now().second
                milisecond = 0
                time = (year, month, day, hour, minute, second, milisecond)
                utility.setSystemTime(time)
                dateAfter120 = jdatetime.datetime.now() + jdatetime.timedelta(120) 
                self.txtLockYear.setText(str(dateAfter120.year))
                self.txtLockMonth.setText(str(dateAfter120.month))
                self.txtLockDay.setText(str(dateAfter120.day)) 
                communication.lockPage(communication.WRITE)
                self.loadLocksTable()
            except Exception as e:
                print(e)
                utility.log('Setting Time', str(e) + '\n')
                self.setMessageLabel(lang.TEXT['systemTimeStatusError'][self.langIndex], 4)
                return

            self.setMessageLabel(lang.TEXT['systemTimeStatus'][self.langIndex], 3)

        
        index = self.hwStackedWidget.indexOf(self.infoPage)
        if self.hwStackedWidget.currentIndex() == index:
            self.configs['SerialNumber'] = self.txtSerialNumber.text()            
            self.configs['LaserDiodeEnergy'] = self.txtLaserDiodeEnergy.text()            
            self.configs['LaserBarType'] = self.txtLaserBarType.text()            
            self.configs['LaserWavelength'] = self.txtLaserWavelength.text()            
            self.configs['DriverVersion'] = self.txtDriverVersion.text()            
            self.configs['MainControlVersion'] = self.txtMainControlVersion.text()            
            self.configs['FirmwareVersion'] = self.txtFirmwareVersion.text()
            self.configs['ProductionDate'] = self.txtProductionDate.text()
            self.configs['GuiVersion'] = self.txtGuiVersion.text()
            self.configs['SpotSizeArea'] = self.txtSpotSize.text() 
            self.enterSettingPage(communication.WRITE)

            if not self.saveConfigs():
                self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex], 4)
            else:
                self.setMessageLabel(lang.TEXT['saveHw'][self.langIndex], 3)
    
    def settingsMenuSelected(self, selectedBtn):
        def wrapper():
            buttons = utility.getFrameWidgets(self.hwbtnsFrame, QPushButton)
            for btn in buttons:
                btn.setStyleSheet('')
            if not selectedBtn == 'back':
                selectedBtn.setStyleSheet(styles.SETTINGS_MENU_SELECTED)

        return wrapper

    def enterSettingPage(self, cmdType):
        self.hwPageChanged()
        fieldValues = {
            'serial': self.txtSerialNumber.text(),
            'totalCounter': self.txtTotalShotCounter.text(), 
            'pDate': self.txtProductionDate.text(),
            'LaserEnergy': self.txtLaserDiodeEnergy.text(), 
            'waveLength': self.txtLaserWavelength.text(), 
            'LaserBarType': self.txtLaserBarType.text(),
            'DriverVersion': self.txtDriverVersion.text(), 
            'controlVersion': self.txtMainControlVersion.text(), 
            'firmware': self.txtFirmwareVersion.text(),
            'monitor': self.txtMonitor.text(),
            'os': self.txtOsSpecification.text(),
            'gui': self.txtGuiVersion.text(),
            'rpi': self.txtRpiVersion.text(),
            'SpotSize': self.txtSpotSize.text()
        }
        communication.settingsPage(fieldValues, cmdType)

    def resetTotalShot(self):
        if self.logingSettingAdmin:
            text = '0 : ' + str(self.configs['TotalShotCounterAdmin'])
            logText = 'The counter was reset by the admin.\n'
        else:
            text = '0'
            logText = 'The counter was reset by the user.\n'
        
        logText += 'Counter value: ' + str(self.configs['TotalShotCounter']) + ' --> 0\n'
        utility.log('Reset Counter', logText)
            
        self.txtTotalShotCounter.setText(text)

        self.configs['TotalShotCounter'] = 0
        if not self.saveConfigs():
            self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex], 4)

    def addMusics(self, paths):
        self.musicFiles = paths
        self.musicSound.setPlaylist(self.playlist)
        for path in paths:
            url = QUrl.fromLocalFile(path)
            self.playlist.addMedia(QMediaContent(url))
            name = os.path.basename(path)
            rowPosition = self.tableMusic.rowCount()
            self.tableMusic.insertRow(rowPosition)
            item = QTableWidgetItem(name)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.tableMusic.setItem(rowPosition, 0, item)

    def readMusicResult(self, res):
        self.setMessageLabel(res, 4)
        self.musicFiles.clear()
        self.tableMusic.setRowCount(0)
        self.lblMusicName.clear()
        self.lblLengthMusic.setText('00:00:00')
    
    def startLoadingMusics(self):
        self.musicFiles.clear()
        self.playlist.clear()
        self.tableMusic.setRowCount(0)
        self.readMusicT.start()

    def initMusics(self):
        self.musicLength = '00:00:00'
        self.lblLengthMusic.setText(self.musicLength)
        self.sliderVolumeMusic.valueChanged.connect(self.setMusicVolume)
        self.musicSound.setVolume(self.configs['MusicVolume'])
        self.sliderVolumeMusic.setValue(self.configs['MusicVolume'])
        self.musicSound.stateChanged.connect(self.mediaStateChanged)
        self.musicSound.positionChanged.connect(self.positionChangedMusic)
        self.musicSound.durationChanged.connect(self.durationChangedMusic)
        self.positionSliderMusic.sliderMoved.connect(self.setPositionMusic)
        self.positionSliderMusic.setRange(0, 0)
        self.loopIco = QIcon()
        self.singleIco = QIcon()
        self.loopIco.addPixmap(QPixmap(paths.LOOP_MUSIC_ICON))
        self.singleIco.addPixmap(QPixmap(paths.SINGLE_MUSIC_ICON))
        self.playIco = QIcon()
        self.pauseIco = QIcon()
        self.playIco.addPixmap(QPixmap(paths.PLAY_ICON))
        self.pauseIco.addPixmap(QPixmap(paths.PAUSE_ICON))
        if self.LoopMusicFlag:
            self.btnLoop.setIcon(self.loopIco)
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        else:
            self.btnLoop.setIcon(self.singleIco)
            self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        self.btnLoop.setIconSize(QSize(80, 80))

    def initTutorials(self):
        self.player = promotions.Player(self.tutorialPage)
        ax = (1920 - self.player.size().width()) // 2
        ay = (1080 - self.player.size().height()) // 2
        self.player.move(ax, ay)

        files = utility.getVideosAndPictures()
        rows = len(files) // 3 if len(files) % 3 == 0 else len(files) // 3 + 1
        if not rows:
            lblTutorialMsg = QLabel(lang.TEXT['lblTutorialMsg'][self.langIndex])
            lblTutorialMsg.setObjectName('lblTutorialMsg')
            lblTutorialMsg.setAlignment(Qt.AlignCenter)
            lblTutorialMsg.setFont(QFont('Arial', 20))
            self.videosLayout.addWidget(lblTutorialMsg)

        for x in range(rows):
            for y in range(3):
                if files:
                    button = QPushButton()
                    file = files.pop()
                    if file[1]:
                        button.setIcon(QIcon(file[1]))
                    else:
                        button.setText(pathlib.Path(file[0]).name)
                    button.setIconSize(QSize(410, 290))
                    self.videosLayout.addWidget(button, x, y)
                    button.clicked.connect(self.player.onOpen(file[0]))
        
    def setLoopMusic(self):
        self.LoopMusicFlag = not self.LoopMusicFlag
        if self.LoopMusicFlag:
            self.btnLoop.setIcon(self.loopIco)
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        else:
            self.btnLoop.setIcon(self.singleIco)
            self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        
        self.configs['LoopMusic'] = self.LoopMusicFlag
        self.saveConfigs()

    def setMusicVolume(self, v):
        self.musicSound.setVolume(v)
        self.configs['MusicVolume'] = v
        self.saveConfigs()
        
    def musicSelected(self, r, c):
        name = os.path.basename(self.musicFiles[r])
        name = name[:50] + '...' if len(name) > 50 else name
        self.lblMusicName.setText(name)
        self.musicSound.playlist().setCurrentIndex(r)
        self.musicSound.play()

    def playlistIndexChanged(self):
        name = self.playlist.currentMedia().canonicalUrl().fileName()
        name = name[:50] + '...' if len(name) > 50 else name
        self.lblMusicName.setText(name)
        self.tableMusic.clearSelection()
        self.tableMusic.selectRow(self.playlist.currentIndex())
           
    def playMusic(self):
        if self.musicSound.state() == QMediaPlayer.PlayingState:
            self.musicSound.pause()
            self.musicMovie.stop()
        else:
            self.musicSound.play()
            if self.btnPlayMusic.icon() == self.pauseIco:
                self.musicMovie.start()
    
    def setPositionMusic(self, position):
        self.musicSound.setPosition(position)

    def mediaStateChanged(self):
        if self.musicSound.state() == QMediaPlayer.PlayingState:
            self.btnPlayMusic.setIcon(self.pauseIco)
            self.musicMovie.start()
        else:
            self.btnPlayMusic.setIcon(self.playIco)
            self.musicMovie.stop()

    def positionChangedMusic(self, position):
        self.positionSliderMusic.setValue(position)
        current = '{:02d}:{:02d}:{:02d} / '.format(*utility.calcPosition(position)) + self.musicLength
        self.lblLengthMusic.setText(current)

    def durationChangedMusic(self, duration):
        self.musicLength = '{:02d}:{:02d}:{:02d}'.format(*utility.calcPosition(duration))
        self.lblLengthMusic.setText('00:00:00 / ' + self.musicLength)
        self.positionSliderMusic.setRange(0, duration)

    def changeAnimation(self, animation):
        if animation == 'horizontal':
            self.stackedWidget.setTransitionDirection(Qt.Horizontal)

        elif animation == 'vertical':
            self.stackedWidget.setTransitionDirection(Qt.Vertical)

    def saveNextSession(self):
        try:
            year = self.txtNsYear.text()
            month = self.txtNsMonth.text()
            day = self.txtNsDay.text()
            if '' in [year, month, day]:
                self.setMessageLabel('Please fill in the fields.', 4)
                return

            date = jdatetime.datetime(int(year), int(month), int(day))
            if utility.getDiff(date) <= -1:
                self.setMessageLabel(lang.TEXT['passedDate'][self.langIndex], 4)
                return

            self.userNextSession.setNextSession(date.togregorian())
            if self.userNextSession.currentSession == 'started':
                self.endSession()
            else:
                self.setUserInfoPage(self.userNextSession.phoneNumber)

        except Exception as e:
            utility.log('Function: saveNextSession()', str(e) + '\n')
            self.setMessageLabel(str(e).capitalize() + '.')

    def cancelNextSession(self):
        if self.userNextSession.currentSession == 'started':
            self.userNextSession.setNextSession(None)
            self.changeAnimation('vertical')
            self.endSession()
        else:
            self.setUserInfoPage(self.userNextSession.phoneNumber)

    def incDecDayNS(self, operation):
        if not self.txtDays.text():
            self.txtDays.setText('1')
        else:
            num = int(self.txtDays.text())
            num = num + 1 if operation == 'inc' else num - 1

            if num in range(0, 10000):
                self.txtDays.setText(str(num))
        
    def setDateText(self, num):
        if num and int(num) in range(0, 10000):
            today = jdatetime.datetime.today()
            afterNday = jdatetime.timedelta(int(num))
            nextSessionDate = today + afterNday
            year = str(nextSessionDate.year)
            month = str(nextSessionDate.month).zfill(2)
            day = str(nextSessionDate.day).zfill(2)
            self.txtNsYear.setText(year)
            self.txtNsMonth.setText(month)
            self.txtNsDay.setText(day)

    def setDaysText(self):
        try:
            year = int(self.txtNsYear.text())
            month = int(self.txtNsMonth.text())
            day = int(self.txtNsDay.text())
            nextSessionDate = jdatetime.datetime(year, month, day)
            diff = utility.getDiff(nextSessionDate)
            if 0 <= diff < 10000:
                self.txtDays.setText(str(diff))
            
        except Exception:
            pass

    def setNextSession(self, page):
        self.laserMainPage.setVisible(False)
        if self.laserNoUser and page == 'lazer':
            self.endSession()
            self.setReady(False)
        else:
            if page == 'lazer':
                self.userNextSession = self.user
                self.setReady(False)
                self.btnCancelNS.setText(lang.TEXT['btnLaterNS'][self.langIndex])
            elif page == 'edit':
                self.userNextSession = self.userInfo
                self.btnCancelNS.setText(lang.TEXT['btnCancelNS'][self.langIndex])
                
            self.changeAnimation('vertical')
            self.stackedWidget.setCurrentWidget(self.nextSessionPage)

    def setReady(self, ready):
        if ready == self.ready:
            return

        if (not ready) == (not self.ready):
            return

        if ready:
            logErrors = ''
            if self.sensorFlags[5]:
                logErrors += lang.TEXT['tempError'][0] + '\n'
                
            if self.sensorFlags[2]:
                logErrors += lang.TEXT['waterflowError'][0] + '\n'
                
            if self.sensorFlags[1]:
                logErrors += lang.TEXT['waterLevelError'][0] + '\n'
            
            if self.sensorFlags[0]:
                logErrors += lang.TEXT['interLockError'][0] + '\n'

            if self.sensorFlags[3]:
                logErrors += lang.TEXT['overHeatError'][0] + '\n'

            if self.sensorFlags[4]:
                logErrors += lang.TEXT['physicalDamage'][0] + '\n'
            
            if logErrors:
                self.setMessageLabel(lang.TEXT['SensorError'][self.langIndex], 2)
                utility.log('Sensors', logErrors)

            
            else:
                self.ready = True
                index = self.stackedWidget.indexOf(self.laserMainPage)
                if self.stackedWidget.currentIndex() == index:
                    fields = {
                        'cooling': self.cooling , 'energy': self.correctEnergy(),
                        'pulseWidth': self.correctEnergy(),'frequency': self.frequency, 
                        'couter': self.currentCounter, 'ready-standby': 'Ready'
                    } 
                    communication.laserPage(fields)
                else:
                    fields = {
                        'energy': self.energy, 'pulseWidth': self.pulseWidth,
                        'frequency': self.frequency, 'ready-standby': 'Ready'
                    } 
                    communication.laserPage(fields)
                
                self.btnStandby.setStyleSheet(styles.READY_NOT_SELECTED)
                self.btnStandByCalib.setStyleSheet(styles.READY_NOT_SELECTED)
                self.btnReady.setStyleSheet(styles.READY_SELECTED)
                self.btnReadyCalib.setStyleSheet(styles.READY_SELECTED)
                self.frequencyWidget.setEnabled(False)
                self.energyWidget.setEnabled(False)
                self.pulseWidthWidget.setEnabled(False)
                self.skinGradeWidget.setEnabled(False)
                self.sliderEnergyCalib.setEnabled(False)
                self.sliderFrequencyCalib.setEnabled(False)
                self.changeSliderColor(styles.SLIDER_DISABLED_GB, styles.SLIDER_DISABLED_GW)

        else:
            self.ready = False
            index = self.stackedWidget.indexOf(self.laserMainPage)
            if self.stackedWidget.currentIndex() == index:
                communication.laserPage({'ready-standby': 'StandBy'})
            else:
                communication.laserPage({'ready-standby': 'StandBy'})
            self.btnStandby.setStyleSheet(styles.READY_SELECTED)
            self.btnStandByCalib.setStyleSheet(styles.READY_SELECTED)
            self.btnReady.setStyleSheet(styles.READY_NOT_SELECTED)
            self.btnReadyCalib.setStyleSheet(styles.READY_NOT_SELECTED)
            self.frequencyWidget.setEnabled(True)
            self.energyWidget.setEnabled(True)
            self.pulseWidthWidget.setEnabled(True)
            self.skinGradeWidget.setEnabled(True)
            self.sliderEnergyCalib.setEnabled(True)
            self.sliderFrequencyCalib.setEnabled(True)
            self.changeSliderColor(styles.SLIDER_GB, styles.SLIDER_GW)

    def correctEnergy(self):
        index = utility.getCoeffIndex(self.energy)
        return int(self.energy * self.coefficients[index])

    def setCooling(self, operation):
        if operation == 'inc':
            if self.cooling < 5:
                self.cooling += 1
                self.coolingWidget.setValue(self.cooling)
                communication.laserPage({'cooling': self.cooling})
        else:
            if self.cooling >= 1:
                self.cooling -= 1       
                self.coolingWidget.setValue(self.cooling)
                communication.laserPage({'cooling': self.cooling})

    def changeSliderColor(self, c1, c2):
        if self.configs['Theme'] in ['C1', 'C2', 'C4']:
            self.sliderEnergyCalib.setStyleSheet(c1)
            self.sliderFrequencyCalib.setStyleSheet(c1)
            self.sliderPulseWidthCalib.setStyleSheet(styles.SLIDER_DISABLED_GB)
            self.dacSlider.setStyleSheet(c1)
        else:
            self.sliderEnergyCalib.setStyleSheet(c2)
            self.sliderFrequencyCalib.setStyleSheet(c2)             
            self.sliderPulseWidthCalib.setStyleSheet(styles.SLIDER_DISABLED_GW)
            self.dacSlider.setStyleSheet(c2)

    def setEnergy(self, operation):
        e = self.energy
        e = e + 1 if operation == 'inc' else e - 1
        if case.MIN_ENRGEY <= e <= case.MAX_ENERGY:
            self.energy = e
            self.energyWidget.setValue(e)
            self.pulseWidth = e
            self.pulseWidthWidget.setValue(e)
            pl = self.pulseWidth
            if case.MIN_PULSE_WIDTH <= pl <= case.MAX_PULSE_WIDTH:
                self.pulseWidth = pl
                self.pulseWidthWidget.setValue(pl)
                maxF_pl = 1000 / (2 * self.pulseWidth)
                maxF_pl_con = case.MAX_FREQUENCY >= maxF_pl
                if maxF_pl_con and self.frequency >= maxF_pl:
                    self.frequency = math.floor(maxF_pl)
                    self.frequencyWidget.setValue(self.frequency)
                    
    def setEnergySlider(self, value):
        self.energy = value
        self.lblEnergyValueCalib.setText(str(value))
        self.pulseWidth = value
        self.pulseWidthWidget.setValue(value)
        self.sliderPulseWidthCalib.setValue(value)
        self.lblPulseWidthValueCalib.setText(str(value))
        maxF_pl = 1000 / (2 * self.pulseWidth)
        maxF_pl_con = case.MAX_FREQUENCY >= maxF_pl
        if maxF_pl_con and self.frequency >= maxF_pl:
            self.frequency = math.floor(maxF_pl)
            self.frequencyWidget.setValue(self.frequency)
            self.sliderFrequencyCalib.setValue(self.frequency)
            self.lblFrequencyValueCalib.setText(str(self.frequency))

    def setFrequency(self, operation):
        freq = self.frequency
        freq = freq + 1 if operation == 'inc' else freq - 1
        if case.MIN_FREQUENCY <= freq <= case.MAX_FREQUENCY:
            self.frequency = freq
            self.frequencyWidget.setValue(freq)
            maxF_pl = math.floor(1000 / (2 * self.pulseWidth))
            maxF_pl_con = case.MAX_FREQUENCY >= maxF_pl
            if maxF_pl_con and self.frequency >= maxF_pl:
                self.frequency = maxF_pl
                self.frequencyWidget.setValue(maxF_pl)
    
    def setFrequencySlider(self, value):
            self.frequency = value
            self.lblFrequencyValueCalib.setText(str(value))
    
    def frequencySliderReleased(self):
        maxF_pl = math.floor(1000 / (2 * self.pulseWidth))
        maxF_pl_con = case.MAX_FREQUENCY >= maxF_pl
        if maxF_pl_con and self.frequency >= maxF_pl:
            self.frequency = maxF_pl
            self.frequencyWidget.setValue(maxF_pl)
            self.sliderFrequencyCalib.setValue(maxF_pl)
            self.lblFrequencyValueCalib.setText(str(maxF_pl))        
    
    def saveCase(self):
        caseObj = case.openCase(self.case)
        caseObj.save(
            self.sex, self.bodyPart, (self.energy, self.pulseWidth, self.frequency)
        )
        self.setMessageLabel(lang.TEXT['saved'][self.langIndex], 1.5)

    def bodyPartsSignals(self):
        buttons = chain(
            utility.getLayoutWidgets(self.fBodyPartsLayout, QPushButton),
            utility.getLayoutWidgets(self.mBodyPartsLayout, QPushButton)
        )

        for btn in buttons:
            btn.clicked.connect(lambda: self.stackedWidgetLaser.setCurrentWidget(self.laserPage))
            btn.clicked.connect(lambda: self.btnBackLaser.setVisible(True))
            sex = btn.objectName().split('btn')[1][0].lower()
            bodyPart = btn.objectName().split('btn')[1][1:].lower()
            btn.clicked.connect(self.setBodyPart(sex, bodyPart))
            btn.clicked.connect(self.loadCase)
            btn.clicked.connect(self.sendLaserFields)
        
    def sendLaserFields(self):
        fields = {
            'cooling': self.cooling , 'energy': self.correctEnergy(),
            'pulseWidth': self.correctEnergy(),'frequency': self.frequency, 
            'couter': self.currentCounter, 
        }
        communication.laserPage(fields)
    
    def setBodyPart(self, sex, bodyPart):
        def wrapper():
            self.bodyPart = bodyPart
            key = sex + ' ' + bodyPart
            self.selectedBodyPart.setText(lang.TEXT[bodyPart][self.langIndex])
            self.selectedBodyPart.setIcon(paths.BODY_PART_ICONS[key])
            
        return wrapper

    def setSex(self, sex):
        if sex == 'male':
            self.stackedWidgetSex.setCurrentWidget(self.malePage)
            self.btnMale.setStyleSheet(styles.SELECTED_SEX)
            self.btnFemale.setStyleSheet(styles.NOT_SELECTED_SEX)
            self.sex = 'male'
        else:
            self.stackedWidgetSex.setCurrentWidget(self.femalePage)
            self.btnMale.setStyleSheet(styles.NOT_SELECTED_SEX)
            self.btnFemale.setStyleSheet(styles.SELECTED_SEX)
            self.sex = 'female'

    def casesSignals(self):
        for btn in self.skinGradeWidget.allButtons:
            caseName = btn.objectName().split('Case')[1]
            btn.clicked.connect(self.setCase(caseName))
            btn.clicked.connect(self.loadCase)

    def setCase(self, case):
        def wrapper():
            self.case = case
            self.loadCase()

        return wrapper

    def loadCase(self):
        caseObj = case.openCase(self.case)
        energy, pl, freq = caseObj.getValue(self.sex, self.bodyPart)
        self.energy = energy
        self.pulseWidth = pl
        self.frequency = freq
        self.energyWidget.setValue(energy)
        self.pulseWidthWidget.setValue(pl)
        self.frequencyWidget.setValue(freq)

    def backSettings(self):
        self.showHwPassInput('hide')
        self.showResetCounterPassInput('hide') 
        index = self.stackedWidgetSettings.indexOf(self.settingsMenuPage)
        if self.stackedWidgetSettings.currentIndex() == index:
            self.stackedWidget.setCurrentWidget(self.mainPage)
            communication.enterPage(communication.MAIN_PAGE)
        else:
            self.stackedWidgetSettings.setCurrentWidget(self.settingsMenuPage)
            self.hWPage.setVisible(False)
            self.uiPage.setVisible(False)
            if self.ready:
                self.setReady(False)
            communication.enterPage(communication.OTHER_PAGE) 

    def searchUsers(self):
        name = self.txtSearchUsers.text().lower()
        for row in range(self.usersTable.rowCount()):
            item1 = self.usersTable.item(row, 0)
            item2 = self.usersTable.item(row, 1)
            self.usersTable.setRowHidden(
                row, name not in item1.text().lower() and name not in item2.text().lower()
            )

    def searchMusic(self):
        name = self.txtSearchMusic.text().lower()
        for row in range(self.tableMusic.rowCount()):
            item = self.tableMusic.item(row, 0)
            self.tableMusic.setRowHidden(row, name not in item.text().lower())

    def typeToInput(self, letter):
        def wrapper():
            self.keyboardTimer.start(30000)
            widget = QApplication.focusWidget()
            lang = 2 if self.farsi else 0

            if hasattr(widget, 'insert'):
                
                if letter() == 'backspace':
                    widget.backspace() 

                elif len(letter()) == 3: # then it's a letter
                    widget.insert(letter()[lang])

                elif len(letter()) == 1: # then it's a number
                    widget.insert(letter())

                elif letter() == 'enter':
                    if widget is not None:
                        modifiers = Qt.KeyboardModifiers()    
                        for evType in (QEvent.KeyPress, QEvent.KeyRelease):
                            event = QKeyEvent(evType, Qt.Key_Return, modifiers)
                            QApplication.postEvent(widget, event)

        return wrapper

    def mousePressEvent(self, event):
        left = (self.width() - self.keyboardFrame.width()) / 2
        right = left + self.keyboardFrame.width()
        bottom = 0
        top = self.keyboardFrame.height() 

        x = left < event.x() < right
        y = bottom < self.height() - event.y() < top

        if not (x and y):
            self.showPowerOptions('hide')
            self.showResetCounterPassInput('hide')
            self.showResetCounterConfirm('hide')
            self.setKeyboard('hide')

    def keyboardSignals(self):
        buttons = chain(
            utility.getLayoutWidgets(self.keyboardRow1, QPushButton),
            utility.getLayoutWidgets(self.keyboardRow2, QPushButton),
            utility.getLayoutWidgets(self.keyboardRow3, QPushButton),
            utility.getLayoutWidgets(self.numRow1, QPushButton),
            utility.getLayoutWidgets(self.numRow2, QPushButton),
            utility.getLayoutWidgets(self.numRow3, QPushButton)
        )

        for btn in buttons:
            btn.clicked.connect(self.typeToInput(btn.text))

        self.btnBackspace.clicked.connect(self.typeToInput(lambda: 'backspace'))
        self.btnReturn.clicked.connect(self.typeToInput(lambda: 'enter'))
        self.btnSpace.clicked.connect(self.typeToInput(lambda: '   '))
        self.btnShift.clicked.connect(self.shiftPressed)
        self.btnFa.clicked.connect(self.farsiPressed)

    def shiftPressed(self):
        self.shift = not self.shift

        buttons = chain(
            utility.getLayoutWidgets(self.keyboardRow1, QPushButton),
            utility.getLayoutWidgets(self.keyboardRow2, QPushButton),
            utility.getLayoutWidgets(self.keyboardRow3, QPushButton),
        )
            
        if self.shift:
            self.btnShift.setStyleSheet(styles.SHIFT_PRESSED)
            self.btnH.setText('H\nآ')
            for btn in buttons:
                btn.setText(btn.text().upper())

        else:
            self.btnShift.setStyleSheet(styles.SHIFT)
            self.btnH.setText('h\nا')
            for btn in buttons:
                btn.setText(btn.text().lower())

    def farsiPressed(self):
        self.farsi = not self.farsi
        
        if self.farsi:
            self.btnFa.setStyleSheet(styles.FARSI_PRESSED)
        else:
            self.btnFa.setStyleSheet('')

    def setKeyboard(self, i):
        height = self.keyboardFrame.height()
        if i == 'hide' and height == 0:
            return

        if i == 'show' and height > 0:
            return

        if i == 'hide':
            height = 350
            newHeight = 0
            self.keyboardTimer.stop()
        else:
            height = 0
            newHeight = 350
            self.keyboardTimer.start(30000)

        self.animation = QPropertyAnimation(self.keyboardFrame, b"maximumHeight")
        self.animation.setDuration(250)
        self.animation.setStartValue(height)
        self.animation.setEndValue(newHeight)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation.start()

    def showHwPassInput(self, i):
        height = self.hwPassFrame.height()
        if i == 'hide' and height == 0:
            return

        if i == 'show' and height > 0:
            return

        if i == 'hide':
            height = 90
            newHeight = 0
        else:
            height = 0
            newHeight = 90

        self.animation2 = QPropertyAnimation(self.hwPassFrame, b"maximumHeight")
        self.animation2.setDuration(500)
        self.animation2.setStartValue(height)
        self.animation2.setEndValue(newHeight)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation2.start()

    def showResetCounterPassInput(self, i):
        width = self.resetCounterFrame.width()
        if i == 'hide' and width == 0:
            return

        if i == 'show' and width > 0:
            return

        if i == 'hide':
            width = 330
            newWidth = 0
        else:
            width = 0
            newWidth = 330

        self.animation3 = QPropertyAnimation(self.resetCounterFrame, b"maximumWidth")
        self.animation3.setDuration(500)
        self.animation3.setStartValue(width)
        self.animation3.setEndValue(newWidth)
        self.animation3.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation3.start()

    def showResetCounterConfirm(self, i):
        width = self.resetCounterMsgFrame.width()
        if i == 'hide' and width == 0:
            return

        if i == 'show' and width > 0:
            return

        if i == 'hide':
            width = 430
            newWidth = 0
        else:
            width = 0
            newWidth = 430

        self.animation4 = QPropertyAnimation(self.resetCounterMsgFrame, b"maximumWidth")
        self.animation4.setDuration(500)
        self.animation4.setStartValue(width)
        self.animation4.setEndValue(newWidth)
        self.animation4.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation4.start()
    
    def showPowerOptions(self, i):
        height = self.po.height()
        if i == 'hide' and height <= 10:
            return

        if i == 'show' and height > 10:
            return

        if i == 'hide':
            height = 300
            newHeight = 0
        else:
            height = 0
            newHeight = 300

        self.animation5 = QPropertyAnimation(self.po, b'maximumHeight')
        self.animation5.setDuration(500)
        self.animation5.setStartValue(height)
        self.animation5.setEndValue(newHeight)
        self.animation5.setEasingCurve(QEasingCurve.InOutQuart)
        self.animation5.valueChanged.connect(lambda value: self.po.setFixedHeight(value))
        self.animation5.start()

    def btnHwSettingClicked(self):
        self.showHwPassInput('show')
        self.setKeyboard('show')
        self.txtHwPass.setFocus()

    def btnResetCounterClicked(self):
        if self.logingSettingAdmin:
            self.showResetCounterConfirm('show')
        else:
            self.showResetCounterPassInput('show')
            self.setKeyboard('show')
            self.txtResetCounterPass.setFocus()

    def checkResetCounterPass(self):
        password = self.txtResetCounterPass.text()
        if password == RESET_COUNTER_PASSWORD:
            self.resetTotalShot()
            self.showResetCounterPassInput('hide')
            self.txtResetCounterPass.clear()
            self.setKeyboard('hide')
        else:
            self.txtResetCounterPass.setStyleSheet(styles.TXT_RESET_COUNTER_WRONG_PASS)
            self.txtResetCounterPass.setFocus()
            self.txtResetCounterPass.selectAll()
            self.resetCounterPassTimer.start(4000)

    def resetCounterYes(self):
        self.resetTotalShot()
        self.showResetCounterConfirm('hide')

    def sortUsers(self):
        self.sortBySession = not self.sortBySession

        if self.sortBySession:
            self.usersTable.sortItems(2, Qt.DescendingOrder)
        else:
            self.usersTable.sortItems(2, Qt.AscendingOrder)

    def addUsersTable(self):
        for i in range(10):
            if len(self.usersList) == 0:
                self.loadUsersFinished()
                return
            self.insertUserTabel(self.usersList[0])
            self.usersList.pop(0)

    def loadUsersFinished(self):
        self.loadUsersTimer.stop()

    def insertUserTabel(self, user):
        rowPosition = self.usersTable.rowCount()
        self.usersTable.insertRow(rowPosition)
        action = promotions.Action(self.usersTable, user.phoneNumber)
        action.btnInfo.pressed.connect(lambda: self.playTouchSound('t'))
        action.info.connect(self.setUserInfoPage)
        action.chbDel.pressed.connect(lambda: self.playTouchSound('t'))
        action.delete.connect(self.userDeleteChbToggled)
        self.usersTable.setCellWidget(rowPosition, 3, action)
        number = QTableWidgetItem(user.phoneNumber)
        name = QTableWidgetItem(user.name)
        sessions = QTableWidgetItem()
        sessions.setData(Qt.EditRole, user.sessionNumber - 1)
        number.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        name.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        sessions.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.usersTable.setItem(rowPosition, 0, number)
        self.usersTable.setItem(rowPosition, 1, name)
        self.usersTable.setItem(rowPosition, 2, sessions)
        self.lblTotalUsersCount.setText(f'{self.usersTable.rowCount()}')

    def userDeleteChbToggled(self, number):
        if number in self.selectedUsers:
            self.selectedUsers.remove(number)
        else:
            self.selectedUsers.append(number)
        
        self.lblSelectedUsersValue.setText(f'{len(self.selectedUsers)}')

    def selectAllUsers(self):
        self.selectAllFlag = not self.selectAllFlag

        for row in range(self.usersTable.rowCount()):
            self.usersTable.cellWidget(row, 3).chbDel.setChecked(self.selectAllFlag)

        if self.selectAllFlag:
            self.btnSelectAll.setText(lang.TEXT['btnDeselectAll'][self.langIndex])
        else:
            self.btnSelectAll.setText(lang.TEXT['btnSelectAll'][self.langIndex])

    def removeSelectedUsers(self):
        for num in self.selectedUsers:
            self.removeUserFromTabel(num)
            del self.usersData[num]
        
        self.lblSelectedUsersValue.setText('0')
        self.btnSelectAll.setText(lang.TEXT['btnSelectAll'][self.langIndex])
        self.selectAllFlag = False
        self.selectedUsers.clear()

    def removeUserFromTabel(self, number=None):
        if number:
            for row in range(self.usersTable.rowCount()):
                if self.usersTable.model().index(row, 0).data() == number:
                    self.usersTable.removeRow(row)
                    self.lblTotalUsersCount.setText(f'{self.usersTable.rowCount()}')
                    return
                    
        else:
            button = self.sender()
            if button:
                row = self.usersTable.indexAt(button.pos()).row()
                number = self.usersTable.item(row, 0).text()
                del self.usersData[number]
                self.usersTable.removeRow(row)
                totalUsers = len(self.usersData)
                self.lblTotalUsersCount.setText(f'{totalUsers}')

    def deleteUserFromDB(self):
        number = self.userInfo.phoneNumber        
        del self.usersData[number]
        for row in range(self.usersTable.rowCount()):
            if self.usersTable.model().index(row, 0).data() == number:
                self.usersTable.cellWidget(row, 3).chbDel.setChecked(False)
        self.removeUserFromTabel(number)
        self.saveUsers()
        self.changeAnimation('horizontal')
        self.stackedWidget.setCurrentWidget(self.userManagementPage)

    def setUserInfoPage(self, num):
        self.stackedWidget.setCurrentWidget(self.editUserPage)
        self.userInfo = self.usersData[num]
        nextSessionDate = utility.toJalali(self.userInfo.nextSession)
        if not nextSessionDate:
            self.txtNextSession.setText(lang.TEXT['notSet'][self.langIndex])
        else:
            diff = utility.getDiff(nextSessionDate)

            if diff == 0:
                self.txtNextSession.setText(lang.TEXT['today'][self.langIndex])
            elif diff == -1:
                self.txtNextSession.setText(lang.TEXT['1dayPassed'][self.langIndex])
            elif diff < -1:
                self.txtNextSession.setText(f'{abs(diff)} {lang.TEXT["nDayPassed"][self.langIndex]}')
            elif diff == 1:
                self.txtNextSession.setText(lang.TEXT['1dayleft'][self.langIndex])
            else:
                self.txtNextSession.setText(f'{diff} {lang.TEXT["nDayLeft"][self.langIndex]}')

        self.txtEditNumber.setText(self.userInfo.phoneNumber)
        self.txtEditName.setText(self.userInfo.name)
        sessions = self.userInfo.sessions
        totalSessions = len(sessions)+1 if len(sessions) > 0 else 0
        self.userInfoTable.setRowCount(totalSessions)
        totalCellColor = QColor(245, 151, 125)
        dateColor = QColor(213, 140, 255)
        for sn in sessions:
            date = promotions.TableWidgetItem(str(utility.toJalali(sessions[sn]['date']).date()), dateColor)
            face = promotions.TableWidgetItem(str(sessions[sn]['face']))
            armpit = promotions.TableWidgetItem(str(sessions[sn]['armpit']))
            arm = promotions.TableWidgetItem(str(sessions[sn]['arm']))
            body = promotions.TableWidgetItem(str(sessions[sn]['body']))
            bikini = promotions.TableWidgetItem(str(sessions[sn]['bikini']))
            leg = promotions.TableWidgetItem(str(sessions[sn]['leg']))
            dateShots = [shot for key, shot in sessions[sn].items() if key != 'date']
            totalRow = promotions.TableWidgetItem(str(sum(dateShots)), totalCellColor)

            self.userInfoTable.setItem(sn - 1, 0, date)
            self.userInfoTable.setItem(sn - 1, 1, face)
            self.userInfoTable.setItem(sn - 1, 2, armpit)
            self.userInfoTable.setItem(sn - 1, 3, arm)
            self.userInfoTable.setItem(sn - 1, 4, body)
            self.userInfoTable.setItem(sn - 1, 5, bikini)
            self.userInfoTable.setItem(sn - 1, 6, leg)
            self.userInfoTable.setItem(sn - 1, 7, totalRow)

        lastRow = len(sessions)
        self.userInfoTable.setItem(lastRow, 0, promotions.TableWidgetItem(''))

        bodyParts = self.userInfo.shot.keys()
        totalColumn = dict.fromkeys(bodyParts, 0)
        for shots in sessions.values():
            for part in bodyParts:
                totalColumn[part] += shots[part] 

        face = promotions.TableWidgetItem(str(totalColumn['face']), totalCellColor)
        armpit = promotions.TableWidgetItem(str(totalColumn['armpit']), totalCellColor)
        arm = promotions.TableWidgetItem(str(totalColumn['arm']), totalCellColor)
        body = promotions.TableWidgetItem(str(totalColumn['body']), totalCellColor)
        bikini = promotions.TableWidgetItem(str(totalColumn['bikini']), totalCellColor)
        leg = promotions.TableWidgetItem(str(totalColumn['leg']), totalCellColor)
        datesShots = sum(totalColumn.values())
        totalShots = promotions.TableWidgetItem(str(datesShots), QColor(247, 104, 64))
        
        self.userInfoTable.setItem(lastRow, 1, face)
        self.userInfoTable.setItem(lastRow, 2, armpit)
        self.userInfoTable.setItem(lastRow, 3, arm)
        self.userInfoTable.setItem(lastRow, 4, body)
        self.userInfoTable.setItem(lastRow, 5, bikini)
        self.userInfoTable.setItem(lastRow, 6, leg)
        self.userInfoTable.setItem(lastRow, 7, totalShots)

    def setFutureSessionsPage(self):
        users = self.usersData.values()
        row = 0
        
        for user in users:
            if user.sessionNumber == 1:
                nextSession = utility.toJalali(user.nextSession)
                num = promotions.TableWidgetItem(user.phoneNumber)
                name = promotions.TableWidgetItem(user.name)
                text = lang.TEXT['firstTime'][self.langIndex] 
                lastSession = promotions.TableWidgetItem(text)
                sn = promotions.TableWidgetItem(str(user.sessionNumber))
                if nextSession and utility.getDiff(nextSession) == int(self.txtFSdays.text()):
                    self.tableFutureSessions.setRowCount(row + 1)
                    self.tableFutureSessions.setItem(row, 0, num)
                    self.tableFutureSessions.setItem(row, 1, name)
                    self.tableFutureSessions.setItem(row, 2, sn)
                    self.tableFutureSessions.setItem(row, 3, lastSession)
                    row += 1

            else:
                nextSession = utility.toJalali(user.nextSession)
                lastSession = utility.toJalali(user.sessions[user.sessionNumber -1]['date'])
                lastSession = promotions.TableWidgetItem(str(lastSession.date()))
                num = promotions.TableWidgetItem(user.phoneNumber)
                name = promotions.TableWidgetItem(user.name)
                sn = promotions.TableWidgetItem(str(user.sessionNumber))
                if nextSession and utility.getDiff(nextSession) == int(self.txtFSdays.text()):
                    self.tableFutureSessions.setRowCount(row + 1)
                    self.tableFutureSessions.setItem(row, 0, num)
                    self.tableFutureSessions.setItem(row, 1, name)
                    self.tableFutureSessions.setItem(row, 2, sn)
                    self.tableFutureSessions.setItem(row, 3, lastSession)
                    row += 1

        self.lblFutureSessionsCount.setText(f'{row}')
        self.tableFutureSessions.setRowCount(row)
        fsDays = int(self.txtFSdays.text())
        if fsDays == 0:
            self.lblFutureSessionsTableTitle.setText(lang.TEXT['today'][self.langIndex])
        elif fsDays == 1:
            self.lblFutureSessionsTableTitle.setText(lang.TEXT['tomorrow'][self.langIndex])
        elif fsDays > 1:
            self.lblFutureSessionsTableTitle.setText(
                self.txtFSdays.text() + ' ' + lang.TEXT['daysLater'][self.langIndex]
            )

    def incDecDayFS(self, operation): 
        num = int(self.txtFSdays.text())
        num = num + 1 if operation == 'inc' else num - 1

        if num in range(0, 10000):
            self.txtFSdays.setText(str(num))
            self.configs['FutureSessionsDays'] = num
            self.saveConfigs()

        self.setFutureSessionsPage()

    def saveUserInfo(self):
        numberEdit = self.txtEditNumber.text()
        nameEdit = self.txtEditName.text()
        numberEdited = False

        if not numberEdit or numberEdit.isspace():
            self.setMessageLabel(lang.TEXT['emptyNumber'][self.langIndex], 4)
            self.txtEditNumber.setFocus()
            return

        if numberEdit != self.userInfo.phoneNumber:
            if numberEdit in self.usersData:
                self.setMessageLabel(lang.TEXT['alreadyExists'][self.langIndex], 4)
                self.txtEditNumber.setFocus()
                return

            oldNumber = self.userInfo.phoneNumber
            self.userInfo.setPhoneNumber(numberEdit)
            newNumber = self.userInfo.phoneNumber
            self.usersData[newNumber] = self.usersData.pop(oldNumber)
            numberEdited = True
            self.removeUserFromTabel(oldNumber)


        if not nameEdit or nameEdit.isspace():
            nameEdit = 'Nobody'

        self.userInfo.setName(nameEdit)

        if not numberEdited:
            self.removeUserFromTabel(self.userInfo.phoneNumber)

        self.insertUserTabel(self.userInfo)
        self.setMessageLabel(lang.TEXT['userUpdated'][self.langIndex], 4)

    def submitNewUser(self):
        number = self.txtNumberSubmit.text()
        name = self.txtNameSubmit.text()
        name = name if name else 'User ' + str(len(self.usersData) + 1)

        if not number or number.isspace():
            self.setMessageLabel(lang.TEXT['emptyNumber'][self.langIndex], 3)
            self.txtNumberSubmit.setFocus()
            return

        if number in self.usersData:
            self.setMessageLabel(lang.TEXT['alreadyExistsSub'][self.langIndex], 4)
            self.txtNumberSubmit.setFocus()
            return

        self.usersData[number] = user.User(number, name)
        self.insertUserTabel(self.usersData[number])
        self.txtNumber.setText(number)
        self.txtNumberSubmit.clear()
        self.txtNameSubmit.clear()
        self.newUserPage.setVisible(False)
        self.startSession()

    def startSession(self):
        index = self.stackedWidget.indexOf(self.editUserPage)
        if self.stackedWidget.currentIndex() == index:
            numberEntered = self.userInfo.phoneNumber
        else:
            numberEntered = self.txtNumber.text()

        if not numberEntered or numberEntered.isspace():
            self.laserNoUser = True
        else:
            self.laserNoUser = False
            if not numberEntered in self.usersData:
                self.txtNumberSubmit.setText(numberEntered)
                self.txtNameSubmit.setFocus()
                self.changeAnimation('vertical')
                self.stackedWidget.setCurrentWidget(self.newUserPage)
                return

            self.user = self.usersData[numberEntered]
            self.user.setCurrentSession('started')
            self.txtCurrentUser.setText(self.user.name)
            self.txtCurrentSnumber.setText(str(self.user.sessionNumber))

        self.setKeyboard('hide')
        self.changeAnimation('horizontal')
        self.stackedWidget.setCurrentWidget(self.laserMainPage)
        self.mainPage.setVisible(False)
        communication.enterPage(communication.BODY_PART_PAGE)
        self.monitorSensorsTimer.start(500)
        self.monitorReceivingSensors.start(3000)

    def endSession(self):
        try:
            if not self.laserNoUser:
                self.user.setCurrentSession('finished')
                self.user.addSession()
                self.removeUserFromTabel(self.user.phoneNumber)
                self.insertUserTabel(self.user)
                self.saveUsers()
                self.monitorSensorsTimer.stop()
                self.monitorReceivingSensors.stop()
                self.txtCurrentUser.clear()
                self.txtCurrentSnumber.clear()

            self.user = None
            self.configs['TotalShotCounter'] += self.currentCounter
            self.configs['TotalShotCounterAdmin'] += self.currentCounter
            self.currentCounter = 0
            self.counterWidget.setValue(0)
            self.saveConfigs()
            self.resetCalibrationParameters()
        except Exception as e:
            utility.log('Function: endSession()', str(e) + '\n')

        finally:
            self.stackedWidget.setCurrentWidget(self.mainPage)
            self.stackedWidgetLaser.setCurrentIndex(0)
            self.btnBackLaser.setVisible(False)

    def resetCalibrationParameters(self):
        self.sliderEnergyCalib.setValue(2)
        self.lblEnergyValueCalib.setText('20')
        self.sliderPulseWidthCalib.setValue(20)
        self.lblPulseWidthValueCalib.setText('20')
        self.sliderFrequencyCalib.setValue(1)
        self.lblFrequencyValueCalib.setText('1')
        self.energy = 20
        self.pulseWidth = 20
        self.frequency = 1

    def setMessageLabel(self, text, sec=5):
        self.lblMsg.setText(text)
        self.lblMsg.adjustSize()
        w = 1920 / 2 
        w -= self.lblMsg.size().width() / 2
        self.lblMsg.move(int(w), 800)
        self.messageTimer.start(sec * 1000)
        timespan = 200
        if self.lblMsg.isVisible():
            timespan = 0
        self.lblMsg.setVisible(True)
        self.effect = QGraphicsOpacityEffect()
        self.lblMsg.setGraphicsEffect(self.effect)
        self.animation6 = QPropertyAnimation(self.effect, b"opacity")
        self.animation6.setDuration(timespan)
        self.animation6.setStartValue(0)
        self.animation6.setEndValue(1)
        self.animation6.start()

    def clearMessageLabel(self):
        self.messageTimer.stop()
        self.effect = QGraphicsOpacityEffect()
        self.lblMsg.setGraphicsEffect(self.effect)
        self.animation7 = QPropertyAnimation(self.effect, b"opacity")
        self.animation7.setDuration(400)
        self.animation7.setStartValue(1)
        self.animation7.setEndValue(0)
        self.animation7.finished.connect(self.lblMsg.clear)
        self.animation7.finished.connect(lambda: self.lblMsg.setVisible(False))
        self.animation7.start()

    def changeLanguage(self, lng):
        global app
        if (lng == 'fa' and self.langIndex == 1) or (lng == 'en' and self.langIndex == 0):
            return
        
        self.btnEnLang.setDisabled(True)
        self.btnFaLang.setDisabled(True)

        if lng == 'fa':
            app.setStyleSheet('*{font-family:"A Iranian Sans"}')
            self.lblEn.setStyleSheet("font-family:'Arial'")
            self.lblJouleCalib.setAlignment(Qt.AlignLeading|Qt.AlignRight|Qt.AlignVCenter)
            self.lblmSecCalib.setAlignment(Qt.AlignLeading|Qt.AlignRight|Qt.AlignVCenter)
            self.lblHzCalib.setAlignment(Qt.AlignLeading|Qt.AlignRight|Qt.AlignVCenter)
            self.userInfoFrame.setLayoutDirection(Qt.RightToLeft)
            self.nextSessionFrame.setLayoutDirection(Qt.RightToLeft)
            self.hwFrame.setLayoutDirection(Qt.RightToLeft)
            self.nsDateFrame.setLayoutDirection(Qt.LeftToRight)
            self.currentUserFrame.setLayoutDirection(Qt.RightToLeft)
            self.resetCounterMsgFrame.setLayoutDirection(Qt.RightToLeft)
            self.calibFrame0.setLayoutDirection(Qt.RightToLeft)
            self.futureSessionFrame.setLayoutDirection(Qt.RightToLeft)
            icon = QPixmap(paths.SELECTED_LANG_ICON)
            self.lblFaSelected.setPixmap(icon.scaled(70, 70))
            self.lblEnSelected.clear()
            self.configs['Language'] = 'fa'
            self.langIndex = 1
        else:
            app.setStyleSheet('*{font-family:"Arial"}')
            self.lblFa.setStyleSheet("font-family:'A Iranian Sans'")
            self.lblJouleCalib.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
            self.lblmSecCalib.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
            self.lblHzCalib.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
            self.userInfoFrame.setLayoutDirection(Qt.LeftToRight)
            self.nextSessionFrame.setLayoutDirection(Qt.LeftToRight)
            self.hwFrame.setLayoutDirection(Qt.LeftToRight)
            self.nsDateFrame.setLayoutDirection(Qt.LeftToRight)
            self.currentUserFrame.setLayoutDirection(Qt.LeftToRight)
            self.resetCounterMsgFrame.setLayoutDirection(Qt.LeftToRight)
            self.calibFrame0.setLayoutDirection(Qt.LeftToRight)
            self.futureSessionFrame.setLayoutDirection(Qt.LeftToRight)
            icon = QPixmap(paths.SELECTED_LANG_ICON)
            self.lblEnSelected.setPixmap(icon.scaled(70, 70))
            self.lblFaSelected.clear()
            self.configs['Language'] = 'en'
            self.langIndex = 0

        if not self.saveConfigs():
            self.setMessageLabel(lang.TEXT['saveConfigError'][self.langIndex], 4)

        self.txtLogs.setFont(QFont('Consolas', 18))
        self.ownerInfoSplash.adjustSize()
        txt = self.ownerInfoSplash.text()
        if txt and utility.isFarsi(txt):
            self.ownerInfoSplash.setStyleSheet(styles.OWNER_INFO_STYLE_FA)
        else:
            self.ownerInfoSplash.setStyleSheet(styles.OWNER_INFO_STYLE_EN)

        self.toolBox.setItemText(0, lang.TEXT['relaysBox'][self.langIndex])
        self.toolBox.setItemText(1, lang.TEXT['driverFunctionalityBox'][self.langIndex])
        self.toolBox.setItemText(2, lang.TEXT['sensorsBox'][self.langIndex])
        self.skinGradeWidget.label.setText(lang.TEXT['lblSkinGrade'][self.langIndex])
        self.skinGradeWidget.btnSave.setText(lang.TEXT['btnSaveInfo'][self.langIndex])
        self.energyWidget.lblParameter.setText(lang.TEXT['lblEnergy'][self.langIndex])
        self.frequencyWidget.lblParameter.setText(lang.TEXT['lblFrequency'][self.langIndex])
        self.pulseWidthWidget.lblParameter.setText(lang.TEXT['lblPulseWidth'][self.langIndex])
        self.energyWidget.lblUnit.setText(lang.TEXT['lblJoule'][self.langIndex])
        self.frequencyWidget.lblUnit.setText(lang.TEXT['lblHz'][self.langIndex])
        self.pulseWidthWidget.lblUnit.setText(lang.TEXT['lblmSec'][self.langIndex])
        self.counterWidget.lblParameter.setText(lang.TEXT['lblCounter'][self.langIndex])
        self.coolingWidget.lblParameter.setText(lang.TEXT['lblCooling'][self.langIndex])

        for lbl in self.findChildren(QLabel):
            if lbl.objectName() in lang.TEXT.keys():
                lbl.setText(lang.TEXT[lbl.objectName()][self.langIndex])

        for btn in self.findChildren(QPushButton):
            if btn.objectName() in lang.TEXT.keys():
                btn.setText(lang.TEXT[btn.objectName()][self.langIndex])

        for txt in self.findChildren(QLineEdit):
            if txt.objectName() in lang.TEXT.keys():
                txt.setPlaceholderText(lang.TEXT[txt.objectName()][self.langIndex])

        for i in range(8):
            self.userInfoTable.horizontalHeaderItem(i).setText(
                lang.TEXT[f'userInfoTable{i}'][self.langIndex]
            )
            if i < 4:
                self.tableFutureSessions.horizontalHeaderItem(i).setText(
                    lang.TEXT[f'tbFsessions{i}'][self.langIndex]
                )
                self.usersTable.horizontalHeaderItem(i).setText(
                    lang.TEXT[f'usersTable{i}'][self.langIndex]
                )
            if i < 3: 
                self.tableLock.horizontalHeaderItem(i).setText(
                    lang.TEXT[f'tableLock{i}'][self.langIndex]
                )            

        self.btnEnLang.setDisabled(False)
        self.btnFaLang.setDisabled(False)        
        
    def enterLogsPage(self):
        if os.path.isfile(paths.LOGS_PATH):
            utility.EncryptDecrypt(paths.LOGS_PATH, 15)
            with open(paths.LOGS_PATH, 'r') as f: 
                self.txtLogs.setText(f.read())
            utility.EncryptDecrypt(paths.LOGS_PATH, 15)

        self.hwStackedWidget.setCurrentWidget(self.systemLogPage)
        communication.enterPage(communication.OTHER_PAGE)
        self.txtLogs.verticalScrollBar().setValue(
            self.txtLogs.verticalScrollBar().maximum()
        )

    def deleteLogs(self):
        if os.path.isfile(paths.LOGS_PATH):
            os.remove(paths.LOGS_PATH)
        
        self.txtLogs.setText('')

    def saveUsers(self):
        try:
            with open(paths.USERS_DATA, 'wb') as f:
                pickle.dump(self.usersData, f)
            
        except Exception as e:
            print(e)
            utility.log('Saving Users Info', str(e) + '\n')
        
    def saveConfigs(self):
        try:
            with open(paths.CONFIG_FILE, 'wb') as f:
                pickle.dump(self.configs, f)

            utility.EncryptDecrypt(paths.CONFIG_FILE, 15)
            return True
        
        except Exception as e:
            print(e)
            utility.log('Saving Configs', str(e) + '\n')
            return False

    def findWord(self, findText, reverse=False):
        findText = findText.lower()
        if findText == '':
            return
        
        text = self.txtLogs.toPlainText().lower()
        
        if reverse:
            self.findIndex = text.lower().rfind(findText, 0, self.findIndex)
        else:
            self.findIndex = text.find(findText, self.findIndex + 1)
        
        if self.findIndex == -1:
            return
        
        textCursor = self.txtLogs.textCursor()
        textCursor.setPosition(self.findIndex)
        textCursor.setPosition(self.findIndex + len(findText), QTextCursor.KeepAnchor)
        self.txtLogs.setTextCursor(textCursor)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pixmap = QPixmap(paths.SPLASH_LOADING)
    splash = QSplashScreen(pixmap)
    splash.showFullScreen()
    app.processEvents()
    win = MainWin()
    win.showFullScreen()
    win.setFixedSize(QSize(1920, 1080))
    splash.finish(win)
    sys.exit(app.exec_())