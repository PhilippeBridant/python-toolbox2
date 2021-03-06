# -*- coding: utf-8 -*-

import os
import fcntl
import subprocess
import select
import signal


class CommandException(Exception):
    pass


class Command(object):

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.process = None

    def _reset_sigpipe_handler(self):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    def run(self, args):
        if (os.path.isdir(self.base_dir) == False):
            os.makedirs(self.base_dir)

        self.process = subprocess.Popen(args,
                                        cwd=self.base_dir,
                                        bufsize=-1,
                                        close_fds=True,
                                        preexec_fn=self._reset_sigpipe_handler,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

        fl = fcntl.fcntl(self.process.stdout, fcntl.F_GETFL)
        fcntl.fcntl(self.process.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        fl = fcntl.fcntl(self.process.stderr, fcntl.F_GETFL)
        fcntl.fcntl(self.process.stderr, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def wait(self, callback=None, read=4096, timeout=3600, loop=True):

        while self.process.returncode is None:

            self.process.poll()

            fd_r, fd_w, fd_x, = select.select([self.process.stdout, self.process.stderr],
                                              [],
                                              [],
                                              timeout)

            if not fd_r and not fd_w and not fd_x:
                self.process.kill()
                raise CommandException('Process (pid = %s) has timed out' %
                                        (self.process.pid))
            else:
                stdout = ''
                stderr = ''
                for fd in fd_r:
                    if fd == self.process.stdout:
                        stdout = fd.read(read)
                    elif fd == self.process.stderr:
                        stderr = fd.read(read)
                    if stdout != '' or stderr != '':
                        if callback:
                            callback(stdout, stderr)
            if not loop:
                break

        return self.process.returncode
