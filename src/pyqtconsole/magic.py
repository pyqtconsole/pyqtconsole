# -*- coding: utf-8 -*-
import os
import subprocess
import platform

LS_CMD = 'dir' if platform.system() == 'Windows' else 'ls'


class MagicCmds():

    """Base class for implementing the magic commands."""

    def __init__(self, parent):
        """
        :param parent: Parent widget (an instance of PythonConsole)
            to which this MagicCmds instance is attached.
        :type parent: PythonConsole
        """
        self.parent = parent

        self.MAGIC_COMMANDS = {
            'pwd': self._PWD,
            'cd': self._CD,
            'ls': self._LS,
            'help': self._HELP,
            'clear': self._CLEAR,
            'who': self._WHO,
            'whos': self._WHOS,
            'timeit': self._TIMEIT,
            'run': self._RUN,
        }  # magic command name (without %) -> function(args) mapping

    def _PWD(self, args=None):
        """Return current working directory."""
        return os.getcwd() + '\n'

    def _CD(self, args=None):
        """Change current working directory, with optional
        argument for target directory."""
        if args:
            os.chdir(os.path.expanduser(args))
        return os.getcwd() + '\n'

    def _LS(self, args=None):
        """Directory listing, with optional arguments (e.g. -l, -a)"""
        result = subprocess.run(
            f'{LS_CMD} {args}' if args else LS_CMD,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout if result.stdout else result.stderr

    def _CLEAR(self, args=None):
        """Clear the console display."""
        self.parent.clear()
        return ''

    def _WHO(self, args=None):
        """List variable names"""
        vars_list = [name for name in self.parent.interpreter.locals.keys()
                     if not name.startswith('_')]
        return '  '.join(sorted(vars_list)) + '\n' \
            if vars_list else 'No variables\n'

    def _WHOS(self, args=None):
        """Detailed variable listing"""
        lines = ['Variable   Type         Data/Info\n']
        lines.append('-' * 50 + '\n')
        for name in sorted(self.parent.interpreter.locals.keys()):
            if not name.startswith('_'):
                obj = self.parent.interpreter.locals[name]
                obj_type = type(obj).__name__
                try:
                    obj_repr = repr(obj)
                    if len(obj_repr) > 40:
                        obj_repr = obj_repr[:37] + '...'
                except Exception:
                    obj_repr = '<repr failed>'
                lines.append(f'{name:<10} {obj_type:<12} {obj_repr}\n')
        return ''.join(lines) if len(lines) > 2 else 'No variables\n'

    def _TIMEIT(self, args=None):
        """Simple timeit implementation"""
        if not args:
            return 'Usage: %timeit <statement>\n'
        import timeit
        try:
            num = 10000  # number of executions to average over
            per_loop = timeit.Timer(
                args, globals=self.parent.interpreter.locals).timeit(num) / num
            for threshold, scale, unit in [(1e-6, 1e9, 'ns'),
                                           (1e-3, 1e6, 'µs'),
                                           (1, 1e3, 'ms')]:
                if per_loop < threshold:
                    return f'{per_loop * scale:.1f} {unit} ± per loop ' \
                           f'(mean of {num} runs)\n'
            return f'{per_loop:.3f} s ± per loop (mean of {num} runs)\n'
        except Exception as e:
            return f'Error timing code: {str(e)}\n'

    def _RUN(self, args):
        """Execute a Python script"""
        if not args:
            return 'Usage: %run <script.py>\n'
        import runpy
        try:
            script_path = os.path.expanduser(args.strip())
            runpy.run_path(
                script_path,
                init_globals=self.parent.interpreter.locals,
                run_name='__main__')
            return ''
        except FileNotFoundError:
            return f'File not found: {args}\n'
        except Exception as e:
            return f'Error running script: {str(e)}\n'

    def _HELP(self, args=None):
        """help message for magic commands"""
        available_cmds = ', '.join(
            [f'%{c}' for c in sorted(self.MAGIC_COMMANDS.keys())])
        return f'Available magic commands: {available_cmds}\n'

    def run(self, cmd, args):
        """Public method to run a magic command."""
        if cmd in self.MAGIC_COMMANDS:
            return self.MAGIC_COMMANDS[cmd](args)
        else:
            return f'Unknown magic command: %{cmd}\n' + self._HELP()

    def add_magic_command(self, name, func):
        """Add a custom magic command.

        :param name: Name of the magic command (without %)
        :type name: str
        :param func: Function to execute for this magic command. It should
            take a single string argument (the args) and return a string
            output.
        :type func: callable
        """
        self.MAGIC_COMMANDS[name] = func
