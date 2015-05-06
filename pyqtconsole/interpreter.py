# -*- coding: utf-8 -*-
import sys
import os

try:
    import jedi
except ImportError as ex:
    print(ex.message)
    print('No completion available')

from code import InteractiveConsole

class PythonConsoleProxy(InteractiveConsole):
    def __init__(self, stdin, stdout, local = {}):
        InteractiveConsole.__init__(self, local)
        self.local_ns = local
        self.stdin = stdin
        self.stdout = stdout

        self._running = False
        self._last_input = ''
        self._more = False
        self._current_line = 0
        self._current_eval_buffer = ''

        self._inp = 'IN [%s]: '
        self._morep = '   ...:'
        self._outp = 'OUT[%s]: '
        self._p = self._inp % self._current_line
        self._print_in_prompt()

    def _redirect_io(self):
        sys.stdout = self.stdout
        sys.stderr = self.stdout

    def _reset_io(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def _update_in_prompt(self, _more, _input):
        if not _more:
            if _input != os.linesep:
                self._current_line += 1

            self._p = self._inp % self._current_line
        else:
            self._p = self._morep

    def _print_in_prompt(self):
        self.stdout.write(self._p)

    def _format_result(self):
        # Are we at the end of a code block, not a very elegant check
        # but it works for now
        eof_cblock = self._last_input == os.linesep and self._more == True

        if self._last_input != os.linesep or eof_cblock: 
            self.stdout.write(os.linesep)

    def push(self, line):
        return InteractiveConsole.push(self, line)

    def runcode(self, code):
        self.stdout.write(os.linesep)
        # Redirect IO, this is the only place were we redirect IO, since we
        # don't how IO is handled within the code we are running
        self._redirect_io()
        exec_res = InteractiveConsole.runcode(self, code)
        self._reset_io()
        return exec_res

    def raw_input(self, prompt=None, timeout=None):
        line = self.stdin.readline(timeout)

        if line != os.linesep:
            line = line.strip(os.linesep)

        return line

    def write(self, data):
        self.stdout.write(data)

    def interact(self, banner=None):
        return InteractiveConsole.interact(self, '')

    def _rep_line(self, timeout = None):
        line = self.raw_input(timeout = timeout)

        if line:
            self._last_input = line

            if line == 'exit' or line == 'exit()':
                self._running = False
            elif line == 'eval_buffer':
                line = self.eval_buffer()
            else:
                self._more = self.push(line)

            self._update_in_prompt(self._more, self._last_input)
            self.stdout.write(os.linesep)
            self._print_in_prompt()

    def repl(self):
        self._running = True

        while self._running:
            self._rep_line()

    def repl_nonblock(self):
        self._rep_line(timeout = 0)

    def exit(self):
        self.stdin.write('exit\n')

    def eval_buffer(self):
        if self._current_eval_buffer:
            try:
                code = compile(self._current_eval_buffer,'<string>', 'exec')
            except (OverflowError, SyntaxError):
                InteractiveConsole.showsyntaxerror(self)
            else:
                self.runcode(code)

        return False

    def set_buffer(self, _buffer):
        self._current_eval_buffer = _buffer.strip(os.linesep)

    def get_completions(self, line):
        script = jedi.Interpreter(line, [self.local_ns])
        words = []
        
        for completion in script.completions():
            words.append(completion.name)

        return words
