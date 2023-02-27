from typing import List, Tuple, Literal, TypeGuard, Optional, get_args

Command = Literal['ver', 'rem', 'row', 'cel', 'txt', 'hex']
POSSIBLE_COMMANDS = get_args(Command)

Cell = bytearray
Row = List[Cell]
Table = List[Row]


class ATBLParser:
    def __init__(self) -> None:
        self._table: Table = []
        self._cur_row: Optional[Row] = None
        self._cur_cell: Optional[Cell] = None

    def parse(self, input_: str) -> Table:
        if len(input_) == 0:
            raise ValueError('An ATBL input cannot be empty')

        lines = input_.split('\n')
        for n, line in enumerate(lines, start=1):
            if n == 1:
                self.validate_version(line)
                continue
            if len(line) == 0:
                continue

            command, arg = self.parse_line(line, n)
            if command == 'rem':
                continue
            elif command == 'ver':
                raise ValueError(f'Line {n}: Version command not in the first line of the input')
            elif command == 'row':
                self.handle_row()
            elif command == 'cel':
                self.handle_cel(n)
            elif command == 'txt':
                self.handle_txt(arg, n)
            elif command == 'hex':
                self.handle_hex(arg, n)

        self.finish_current_row()
        return self._table
                

    def validate_version(self, line: str) -> None:
        if line != 'ver 1':
            raise ValueError("Incorrect version specified on first line")

    def parse_line(self, line: str, lineno: int) -> Tuple[Command, str]:
        if len(line) < 3:
            raise ValueError(f'Line {lineno}: a command must be at least 3 characters in length')
        if line[:4] == '    ':
            return self.parse_line('txt \n' + line[4:], lineno)

        command = line[:3]
        if not is_command(command):
            raise ValueError(f'Line {lineno}: Unknown command {command}')
        
        return command, line[4:]

    def handle_row(self) -> None:
        if self._cur_row is not None:
            self.finish_current_row()
        self._cur_row = []

    def handle_cel(self, lineno: int) -> None:
        if self._cur_row is None:
            raise ValueError(f'Line {lineno}: Starting cell without first starting a row.')
        elif self._cur_cell is not None:
            self._cur_row.append(self._cur_cell)
        self._cur_cell = bytearray()

    def handle_txt(self, arg: str, lineno: int) -> None:
        if self._cur_cell is None:
            raise ValueError(f'Line {lineno}: Appending to a cell without initializing it.')
        self._cur_cell += bytearray(arg, 'utf-8')

    def handle_hex(self, arg: str, lineno: int) -> None:
        if self._cur_cell is None:
            raise ValueError(f'Line {lineno}: Appending to a cell without initializing it.')
        self._cur_cell += bytearray.fromhex(arg)

    def finish_current_row(self):
        if self._cur_cell is not None:
            self._cur_row.append(self._cur_cell)
            self._cur_cell = None
        self._table.append(self._cur_row)


def is_command(command: str) -> TypeGuard[Command]:
    return command in POSSIBLE_COMMANDS