#!/usr/bin/env python
# encoding: utf-8

from subprocess import Popen, PIPE, STDOUT
import Queue
import select
import os
import shutil
import sys
import tempfile
import time

import watchdog.events
import watchdog.observers
from colorama import Fore, Back, Style, init as colorama_init

class _EventHandler(watchdog.events.FileSystemEventHandler):
    """A simple handler that just stuffs everything it sees into a Queue"""

    def __init__(self, queue):
        watchdog.events.FileSystemEventHandler.__init__(self)
        self._q = queue

    def on_modified(self, event):
        self.on_created(event)

    def on_created(self, event):
        self._q.put(event)

class WorkItem(object):
    name = "unnamed item"
    command = lambda self, files: []
    start_delay = 5
    path_matcher = staticmethod(lambda fn: True)
    output_file = None
    output_copy = False
    output_stream = None
    cwd = None
    on_success = None

    def __init__(self):
        self.rv = None
        self.reschedule()
        self._paths = set()

    def reschedule(self):
        self.run_at = time.time() + self.start_delay

    def report_launch(self):
        sys.stdout.write(Fore.BLUE + "Begin: " + self.name + Fore.RESET + "\n"); sys.stdout.flush()

    def report_finish(self):
        took = time.time() - self._start_time

        sys.stdout.write(self.name + " ... ");
        if self.rv == 0:
            sys.stdout.write(Fore.GREEN + "Success." + Fore.RESET)
        else:
            sys.stdout.write(Fore.RED + "Failed: %i." % self.rv + Fore.RESET)

        sys.stdout.write(" (%.2f sec)" % took)
        sys.stdout.write("\n")
        sys.stdout.flush()

    def launch(self):
        self.report_launch()

        self._start_time = time.time()

        self._running_cmd = Popen(
            self.command(self._paths), stderr=STDOUT, stdout=PIPE, cwd=self.cwd
        )

        self._logfile = None
        self._stream = None
        if self.output_file is not None:
            self._logfile = tempfile.NamedTemporaryFile("w", delete=False)
        if self.output_stream is not None:
            self._stream = open(self.output_stream, "w")


    def _pump_output(self):
        while select.select([self._running_cmd.stdout], [], [], 0.05)[0]:
            line = self._running_cmd.stdout.readline()
            if not line:
                break
            line = line.rstrip().replace("[?1034h", "")  # hack. needed on mac
            if self._logfile:
                self._logfile.write(line + "\n")
                self._logfile.flush()
            if self._stream:
                self._stream.write(line + "\n")
                self._stream.flush()


    def still_running(self):
        self._pump_output()

        if self._running_cmd.poll() is not None:
            self._running_cmd.communicate()

            if self._stream:
                self._stream.close()
                self._stream = None

            if self._logfile:
                self._logfile.close()
                shutil.copyfile(self._logfile.name, self.output_file)
                os.unlink(self._logfile.name)
                self._logfile = None
            return False

        return True


    def finish(self):
        self.rv = self._running_cmd.wait()

        self.report_finish()


class Executor(object):
    def __init__(self):
        colorama_init()

        self._q = Queue.Queue()
        self._work_items = set()
        self._scheduled = []
        self._running = []

        self._observer = watchdog.observers.Observer()
        self._observer.schedule(_EventHandler(self._q), ".", recursive=True)
        self._observer.start()


    def run(self):
        try:
            while True:
                time.sleep(.25)
                self._check_for_work()
        except KeyboardInterrupt:
            self._observer.stop()
        self._observer.join()

    def add_item(self, item):
        self._work_items.add(item)

    def _run_scheduled(self):
        now = time.time()
        for item in self._scheduled:
            if now > item.run_at and not self._is_running(item.__class__):
                item.launch()
                self._scheduled.remove(item)
                self._running.append(item)
                return self._run_scheduled()

    def _cleanup_running(self):
        if not self._running: return
        for idx in range(len(self._running)):
            if not self._running[idx].still_running():
                item = self._running[idx]
                item.finish()
                if item.rv == 0 and item.on_success:
                    if (not self.is_scheduled(item.__class__, "") and
                        not self.is_scheduled(item.on_success, "")):
                        self._scheduled.append(item.on_success())
                del self._running[idx]

                return self._cleanup_running()

    def is_scheduled(self, item_type, path):
        for a in self._scheduled:
            if a.__class__ is item_type:
                a.reschedule()
                if path:
                    a._paths.add(path)
                return True
        return False

    def _is_running(self, item_type):
        for item in self._running:
            if item.__class__ == item_type:
                return True
        return False


    def _check_for_work(self):
        self._run_scheduled()
        self._cleanup_running()

        events = []
        while not self._q.empty():
            events.append(self._q.get())

        for item_type in self._work_items:
            for ev in events:
                if not item_type.path_matcher(ev.src_path):
                    continue
                if self.is_scheduled(item_type, ev.src_path):
                    continue
                new_item = item_type()
                new_item._paths.add(ev.src_path)
                self._scheduled.append(new_item)


