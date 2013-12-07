#!/usr/bin/python
# -*- coding: utf-8 -*-

import pyaudio
import wave
import audioop
from collections import deque 
from pprint import pprint
import os
import urllib2
import urllib
import time

#config
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
THRESHOLD = 180 #The threshold intensity that defines silence signal (lower than).
SILENCE_LIMIT = 2 #Silence limit in seconds. The max ammount of seconds where only silence is recorded. When this time passes the recording finishes and the file is delivered.

def listen_for_speech():
    """
    Does speech recognition using Google's speech  recognition service.
    Records sound from microphone until silence is found and save it as WAV and then converts it to FLAC. Finally, the file is sent to Google and the result is returned.
    """

    #open stream
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print "* listening. CTRL+C to finish."
    all_m = []
    data = ''
    rel = RATE/CHUNK
    slid_win = deque(maxlen=SILENCE_LIMIT*rel)
    started = False
    
    while (True):
        
        data = stream.read(CHUNK)
        slid_win.append (abs(audioop.avg(data, 2)))

        if(True in [ x>THRESHOLD for x in slid_win]):
            if(not started):
                print "starting record"
            started = True
            all_m.append(data)
        elif (started==True):
            print "finished"
            #the limit was reached, finish capture and deliver
            filename = save_speech(all_m,p)
            print filename
            stt_google_wav(filename)
            #reset all
            data = ''
            started = False
            slid_win = deque(maxlen=SILENCE_LIMIT*rel)
            all_m= []
            print "listening ..."

    print "* done recording"
    stream.close()
    p.terminate()


def save_speech(data, p):
    filename = 'output_'+str(int(time.time()))
    # write data to WAVE file
    data = b''.join(data)
    wf = wave.open(filename+'.wav', 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(44100)
    wf.writeframes(data)
    wf.close()

    return filename


def stt_google_wav(filename):
    os.system('sox '+filename+'.wav -r 16000 '+filename+'_resampled.wav')
    os.remove(filename+'.wav')
    os.system('flac '+filename+'_resampled.wav')
    f = open(filename+'_resampled.flac','rb')
    flac_cont = f.read()
    f.close()

    #post it
    lang_code='ru-RU'
    googl_speech_url = 'https://www.google.com/speech-api/v1/recognize?xjerr=1&client=chromium&pfilter=2&lang=%s&maxresults=6'%(lang_code)
    hrs = {"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7",'Content-type': 'audio/x-flac; rate=16000'}
    req = urllib2.Request(googl_speech_url, data=flac_cont, headers=hrs)
    p = urllib2.urlopen(req)

    res = eval(p.read())
    status = res['status']
    hypotheses = res['hypotheses']
    
    if status == 5:
        speak(text='Ошибка распознавания')
        map(os.remove, (filename+'_resampled.flac', filename+'_resampled.wav'))
    if status == 0:
        for current in range(len(hypotheses)):
            phrase = hypotheses[current]['utterance']
            speak(text='Вы сказали: '+phrase)
            map(os.remove, (filename+'_resampled.flac', filename+'_resampled.wav'))
            break
    


def speak(text='Привет кот, как дела?', lang='ru', fname='result.wav', player='mplayer'):
    """ Send text to Google's text to speech service
    and returns created speech (wav file). """

    limit = min(100, len(text))#100 characters is the current limit.
    text = text[0:limit]
    print "Text to speech:", text
    url = "http://translate.google.com/translate_tts"
    values = urllib.urlencode({"q": text, "textlen": len(text), "tl": lang})
    hrs = {"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7"}
    #TODO catch exceptions
    req = urllib2.Request(url, data=values, headers=hrs)
    p = urllib2.urlopen(req)
    f = open(fname, 'wb')
    f.write(p.read())
    f.close()
    print "Speech saved to:", fname
    play_wav(fname, player)
    os.remove(fname)


def play_wav(filep, player='mplayer'):
    print "Playing %s file using %s" % (filep, player)
    os.system(player + " " + filep)

if(__name__ == '__main__'):
    listen_for_speech()
