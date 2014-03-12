#!/usr/bin/python
""" The client controller for the playIT backend
by Horv and Eda - 2013, 2014

To add a new type of playback. Add a function called _play_TYPE(media_item)
and define how it's handled. It will be called automatically based on the
type parameter specified in the downloaded json

Requires Python >= 3.3
Depends on:
    1. mopidy -  for Spotify and Soundcloud playback.
            Note that you'll need both the spotify and soundcloud plugins
            Eg. aurget -S mopidy mopidy-spotify mopidy-soundcloud
    2. python-mpd2 (https://github.com/Mic92/python-mpd2)
    3. python-requests (python library) for popping and checking server status.
    4. mpv for video/YouTube playback. http://mpv.io/


"""
import threading
import requests
import time
import argparse
import queue
import sys
from shutil import which
import subprocess
from subprocess import call
from mpd import MPDClient

# Some settings and constants
POP_PATH = "/playIT/media/popQueue"
# Use verbose output
VERBOSE = True
MOPIDY_HOST = "localhost"
MOPIDY_PORT = 6600


def main():
    """ Init and startup goes here... """
    check_reqs()

    playit = PlayIt()
    vprint("Running main playback loop...")
    ploop = threading.Thread(target=playit.start_printloop)
    eloop = threading.Thread(target=playit.start_eventloop)

    ploop.daemon = True
    eloop.daemon = True

    ploop.start()
    eloop.start()

    playit.start_prompt()


def check_reqs():
    """ Verify that all dependencies exists. """
    depends = ["mopidy", "mpv"]
    failed = False

    for dep in depends:
        if which(dep) is None:
            print("Requirement", dep, "is missing (from PATH at least...)", file=sys.stderr)
            failed = True

    if failed:
        print("Resolve the above missing requirements", file=sys.stderr)
        exit(1)
    else:
        if not process_exists("mopidy"):
            print("mopidy does not seem to be running. Please launch it beforehand :)", file=sys.stderr)
            exit(2)


def process_exists(proc_name):
    """ http://stackoverflow.com/a/7008599 ."""

    import re
    ps = subprocess.Popen("ps ax -o pid= -o args= ",
                          shell=True, stdout=subprocess.PIPE)
    ps_pid = ps.pid
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    from os import getpid
    for line in output.decode().split("\n"):
        res = re.findall(r"(\d+) (.*)", line)
        if res:
            pid = int(res[0][0])
            if proc_name in res[0][1] and pid != getpid() and pid != ps_pid:
                return True
    return False


def _fix_server_adress(raw_server):
    """ Prepend http://  there. """
    if not raw_server.startswith("http://"):
        raw_server = "http://" + raw_server
    return raw_server


def check_connection(url):
    """ Checks the connection to the backend """
    resp = requests.head(url + POP_PATH)

    if resp.status_code != 200:
        print("Unable to find backend at:", url,
              file=sys.stderr)
        exit(4)


def vprint(msg):
    """ Verbose print """
    if VERBOSE:
        print(msg)


class PlayIt(object):
    """ Defines the interface between the backend and actual playback. """
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-m', '--monitor-number', dest="monitor_number",
                            type=int, default=1)
        parser.add_argument('-s', '--server',
                            default="http://hubben.chalmers.it:8080")
        #parser.add_argument('-v', '--verbose', action='store_true')
        args = parser.parse_args()

        if args.server is None:
            print("Please supply a server by: -s http://www.example.org:port",
                  file=sys.stderr)
            exit(3)
        else:
            self.server = _fix_server_adress(args.server)
            vprint("Server: " + self.server)
            check_connection(self.server)

        self.monitor_number = args.monitor_number

        self.cmd_queue = queue.Queue()
        self.print_queue = queue.Queue()
        self.el_quit_queue = queue.Queue()
        self.quit_queue = queue.Queue()

    def start_eventloop(self):
        """ Start the event-loop. """
        while True:
            # When the main thread wants to kill me, it sends
            # True to the eventloop quit queue.
            if self.el_quit_queue.qsize() > 0 and self.el_quit_queue.get_nowait():
                vprint("Quitting event loop")
                self.el_quit_queue.task_done()
                return

            #item = {"nick": "Eda", "artist": ["Awolnation"], "title":"Sail", "externalID": "22UQelxzCIskdmb8pIqq8U"}
            #self._play_spotify(item)
            #time.sleep(7)
            item = self._get_next()
            if len(item) > 0:
                # Dynamically call the play function based on the media type
                func_name = "_play_" + item['type'].lower()
                func = getattr(self, func_name)
                func(item)
            else:
                vprint("No item in queue, sleeping...")
                time.sleep(7)

    def _get_next(self):
        """ Get the next item in queue from the backend. """
        vprint("Popping next item in the queue")
        resp = requests.get(self.server + POP_PATH)
        return resp.json()

    def _play_youtube(self, item):
        """ Play the supplied youtube video with mpv. """
        self.print_queue.put("Playing youtube video: " + item['title']
                             + " requested by " + item['nick'])
        youtube_url = "https://youtu.be/" + item['externalID']

        cmd = ['mpv', '--fs', '--screen',
               str(self.monitor_number), youtube_url]
        call(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    def _play_spotify(self, item):
        """ Play the supplied spotify track using mopidy and mpc. """
        self.print_queue.put("Playing " + ", ".join(item['artist']) + " - "
                             + item['title'] + " requested by " + item['nick'])
        self._add_to_mopidy('spotify:track:' + item['externalID'])

    def _play_soundcloud(self, item):
        """ Play SoundCloud items """
        self.print_queue.put("Playing " + item['artist'] + " - "
                             + item['title'] + " requested by " + item['nick'])
        self._add_to_mopidy('soundcloud:song.' + item['externalID'])

    def _add_to_mopidy(self, track_id):
        """ Play a mopidy compatible track """
        client = MPDClient()
        client.connect(MOPIDY_HOST, MOPIDY_PORT)
        client.single(1)
        client.clear()
        client.add(track_id)
        client.play(0)

        done = False
        while not done:
            # Wait for either a command or idle interruption
            threading.Thread(target=self._wait_for_idle).start()
            notice = self.cmd_queue.get()

            if notice == "playback_changed":
                done = client.status()['state'] == "stop"
            elif notice == "pause":
                client.pause()
            elif notice == "play":
                client.play()
            elif notice == "stop":
                client.stop()
            elif notice == 'quit':
                print('Bye bye!')
                client.stop()
                from _thread import interrupt_main
                interrupt_main()
            self.cmd_queue.task_done()

        client.close()
        client.disconnect()

    def _wait_for_idle(self):
        """ Wait for some event from mopidy """
        # Since the client isn't thread safe we need a new connection.
        client = MPDClient()
        client.connect(MOPIDY_HOST, MOPIDY_PORT)

        # Only care about playback changes.
        event = []
        while 'player' not in event:
            event = client.idle()
        self.cmd_queue.put("playback_changed")

        client.close()
        client.disconnect()

    def start_prompt(self):
        """ Listen for user input (Like a shell) """
        try:
            cmd = ""
            while cmd != 'quit':
                self.print_queue.put('')
                cmd = input()

                if len(cmd) > 0:
                    self.cmd_queue.put(cmd)

            # Wait for queues to finish
            self.print_queue.join()
            self.cmd_queue.join()
        except KeyboardInterrupt:
            exit(1)
            return

    def start_printloop(self):
        """ Prints everything from the print queue """
        while True:
            msg = self.print_queue.get()
            if msg == "quit":
                vprint("Quitting print loop")
                self.print_queue.task_done()
                return
            if msg != '':
                msg = msg + '\n'

            print("\r" + msg + "> ", end='')
            self.print_queue.task_done()


if __name__ == "__main__":
    main()
