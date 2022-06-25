#!/usr/bin/env python3

import numpy as np
from scipy.io.wavfile import read, write


from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPixmap
from pyqtgraph import PlotWidget
import pyqtgraph as pg

from graphics import *
from exec import *
from scipy.fft import fft
import os


SUPPORTED_IMG_FORMATS = "*.png *.bmp *.jpg *.jpeg"
SUPPORTED_AUDIO_FORMATS = "*.wav"


IMGNAME = ""
AUDIONAME = ""
OUT_FOLDER = "./output/"
SPECTRUM_NAME = "foo.png" # must be png
IMG_AUDIO_NAME = ""

def cur_sts(sts:str):
    ui.status_label.setText(sts)

def load_imgname():
    fname = QFileDialog.getOpenFileName(caption="Open file", filter=SUPPORTED_IMG_FORMATS)
    # file_name = os.path.basename(fname[0])
    global IMGNAME
    IMGNAME = fname[0]
    
    try:
        Image.open(IMGNAME)
    except:
        cur_sts("Wrong or absent imagefilename:(")
        return

    ui.img_name_line.setText(IMGNAME)
    pixmap = QPixmap(IMGNAME)
    
    old_width = pixmap.size().width()
    old_height = pixmap.size().height()
    
    new_height = ui.img_preview_label.size().height()
    new_width = int(old_width * new_height / old_height)
    
    if new_width > ui.img_preview_label.size().width():
        new_width = ui.img_preview_label.size().width()
    
    ui.img_preview_label.setPixmap(pixmap.scaled(new_width, new_height))

def print_fft(dataset, sr, graph):
    
    if len(dataset.shape) > 1:
        mono = dataset[:, 0]
    else:
        mono = dataset
    
    sp = fft(mono)
    abs_sp = abs(sp)
    
    N = len(abs_sp)
    n = np.arange(N)
    T = N/sr
    freq = n / T
    n_oneside = int(N / 2)
    f_oneside = freq[:n_oneside]

    X_oneside = abs_sp[:n_oneside] / n_oneside
    
    graph.clear()
    graph.plot(f_oneside, X_oneside)

def load_audioname():
    
    cur_sts("Please, wait a bit...")
    
    fname = QFileDialog.getOpenFileName(caption="Open file", filter=SUPPORTED_AUDIO_FORMATS)

    global AUDIONAME 
    AUDIONAME = fname[0]
    try:
        audio_sr, audio_data = read(AUDIONAME)
    except:
        cur_sts("Wrong or absent audiofilename:(")
        return
    
    ui.audio_name_line.setText(AUDIONAME)


    print_fft(audio_data, audio_sr, ui.audiofft_graph)
    cur_sts("Ready to work:)")
    
def exe():
    
    cur_sts("Please, wait a bit...")
    max_freq = int(ui.max_freq_line.text())
    min_freq = int(ui.min_freq_line.text())
    duration = float(ui.img_dur_line.text())

    steps = int(ui.spectrum_step_combo.currentText())
    sr = int(ui.sr_line.text())
    invert = ui.invert_check.checkState() != 0 and True or False
    contrast = ui.contrast_check.checkState() != 0 and True or False

    global OUT_FOLDER
    global IMG_AUDIO_NAME
    IMG_AUDIO_NAME = ui.audio_img_name_line.text() + ".wav"

    if min_freq > max_freq or max_freq <= 0 or min_freq < 0:
        cur_sts("Wrong frequency limits:(")
        return
    
    if duration <= 0:
        cur_sts("Duration must be grater than 0:(")
        return
    
    if sr <= 1000:
        cur_sts("SampleRate must be grater than or equal 1000")

    global IMGNAME
    genSoundFromImage(IMGNAME, output=OUT_FOLDER + IMG_AUDIO_NAME, bar=ui.prog_bar, duration=duration,
                      steppingSpectrum=steps, sampleRate=sr, intensityFactor=1, min_freq=min_freq,
                      max_freq=max_freq, invert=invert, contrast=contrast, highpass=False, verbose=False)
    
    ims = plotstft(OUT_FOLDER + IMG_AUDIO_NAME, binsize=steps, plotpath=OUT_FOLDER + SPECTRUM_NAME)
    pixmap = QPixmap(OUT_FOLDER + SPECTRUM_NAME)
    ui.picture.setPixmap(pixmap)

    tmp_sr, tmp_data = read(OUT_FOLDER + IMG_AUDIO_NAME)
    print_fft(tmp_data, tmp_sr, ui.imgfft_graph)
    
    cur_sts("Done:)")

def compile_audio():
    
    cur_sts("")
    
    intensity = float(ui.intensity_line.text())
    if intensity < 1:
        cur_sts("Intensity must be grater than 1:(")
        return
    
    audioname = ui.audio_name_line.text()
    
    global OUT_FOLDER
    global IMG_AUDIO_NAME
    
    try:
        audio_sr, audio_data = read(audioname)
    except:
        cur_sts("Wrong or absent audiofilename:(")
        return
    
    try:
        img_sr, img_data = read(OUT_FOLDER + IMG_AUDIO_NAME)
    except:
        cur_sts("Can not open the file:" + "'" + IMG_AUDIO_NAME + "'")
        return

    single = audio_data[:, 0]
    
    img_shape = np.shape(img_data)
    audio_shape = np.shape(single)
    padded = np.zeros(audio_shape)
    padded[:img_shape[0]] = img_data
    
    res_data = single + padded
    
    padded *= intensity
    
    res_audioname = ui.audio_sum_name_line.text() + ".wav"
    
    write(OUT_FOLDER + res_audioname, audio_sr, res_data)
    cur_sts("Compiled:)")



if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    ui = uic.loadUi("ui.ui")

    try:
        os.mkdir(OUT_FOLDER)
    except:
        cur_sts(OUT_FOLDER + " is currently exist")

    ui.browse_img_but.clicked.connect(load_imgname)
    ui.browse_audio_but.clicked.connect(load_audioname)
    ui.exe_but.clicked.connect(exe)
    ui.prog_bar.setVisible(False)
    ui.exec_audio_btn.clicked.connect(compile_audio)

    ui.show()
    app.exec()
