import builtins
import copy
import json
import keyword
import os
import random
import shutil
from datetime import datetime as date
from datetime import timedelta
from tkinter import *
from tkinter import colorchooser, font, filedialog, ttk


# MacOS FIX -- Provides a cleaned listdir (removing hidden files like .DS_STORE)
def get_dir(path):
    return sorted([i for i in os.listdir(path) if i[0] != '.'])


class GUI(Tk):

    def __init__(self):
        super().__init__()
        self.title("MTAssist Questions")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close)

        # Reads in config values
        self.read_config()

        # Sets the width and height based on the config
        self.geometry(self.centre(*self.get_dimensions('win_q')))
        self.w = self.config['win_q_w']
        self.h = self.config['win_q_h']

        # Defines the list of strings that should be highlighted
        self.keywords = tuple([[r"""'[^']*'""", r'''"[^"]*"'''], [r'(-)?\d+(\.\d+)?'], keyword.kwlist, dir(builtins)])
        self.kwsections = ['strings', 'numbers', 'keywords', 'builtins']

        # Sets default values for variables required later
        self.question = ''
        self.session_id = ''
        self.settings_window = None
        self.student_window = None
        self.time = None

        # If no questions exists, reads them in
        if not os.path.exists('./questions/') or not get_dir('./questions/'):
            self.import_questions()

        # Ensure an appropriate file is being used to import
        while not self.get_dir_size():
            print("An Fatal Error Occurred While Loading Questions!")
            print(f'Perhaps {self.config["import_path"]} is not the right file?')
            self.config['import_path'] = input('Please enter an appropriate input file: ')
            self.import_questions()

        # Creates the main window's widgets
        self.create_widgets()

    # Searches for session id or adds a placeholder to the search box if empty
    def _focus_out(self, e):
        if self.search.get() == " Search Question ID":
            return
        elif self.search.get() == "":
            self.search.set(" Search Question ID")
            self.searchbox.config(fg=self.colours['placeholder_fg'])
        else:
            print('opening q')
            self.open_question()
            self.search.set(self.session_id)

        self.focus()

    # Deletes current entry in search box
    def _focus_in(self, e):
        self.search.set("")
        self.searchbox.config(fg=self.colours['textbox'][0])

    # Adds a new student to the student window
    def add_student(self):
        # Must have a question loaded before adding a student
        if self.question == '':
            self.print_debug('Please select a mastery (or enter id) for this student first.',
                             colour=self.colours['error_fg'])
            return

        # Generate a session id if one doesn't already exist (i.e. if the question has not yet been copied)
        if self.session_id == '':
            self.session_id = self.encode_id(self.question_list)

        # Use an EntryPopup to ask for the student's name
        popup = EntryPopup(self, "Enter a Student Name")
        popup.e.focus()
        self.wait_window(popup)
        if popup.value != '':
            # If the student's window is currently closed, instantiate a new one
            if self.student_window is None:
                self.student_window = StudentWindow(self)

            # Add the student
            self.student_window.add(popup.value.title(), self.decode_id(self.session_id)[-1][0], self.session_id)
            self.student_window.focus()

        self.session_id = ''

    # Returns a geometry string centred around the middle of the screen, rather than the top left
    def centre(self, w, h, offset_x=0, offset_y=0):
        return "{}x{}+{}+{}".format(w, h, (self.winfo_screenwidth() - w) // 2 - offset_x,
                                    (self.winfo_screenheight() - h) // 2 - offset_y)

    # Checks all newly imported questions to see if any question files have been generated without content
    # Note: this happens because the input file was out of order, thus I needed to make a new file for each
    # variation number leading up to the provided one to avoid errors with selecting files based on the index
    # within the list of all files int he directory. Notably, MT12, C2 originally had no V1, only V2
    def check_empty(self, g):
        for i in range(len(g)):
            for j in range(len(g[i])):
                for k in range(len(g[i][j])):
                    if len(g[i][j][k]) == 0:
                        self.print_debug(
                            f'No question in input file at MT{i + 1:02} Cat{j + 1:02} Var{k + 1:02}! Please Fix!',
                            colour=self.colours['error_fg'])

    # Checks all newly imported questions to see if they are actually readable.
    # Note: this occurs when non-UTF8 chars are present in the file, which for some reason did not cause an
    # error when being read in from the input file (not sure why). This helps to identify which files they reside in.
    def check_readable(self, g):
        for q in get_dir('./questions'):
            for c in get_dir(f'./questions/{q}'):
                for v in get_dir(f'./questions/{q}/{c}'):
                    with open(f'./questions/{q}/{c}/{v}', 'r', encoding='utf-8') as file:
                        try:
                            file.read()
                        except:
                            self.print_debug(f"Reading error in './questions/{q}/{c}/{v}'",
                                             colour=self.colours['error_fg'])
                            raise

    # If there is a question to be copied, this generates a session id and copies them both to the clipboard
    def copy(self):
        if self.question == '':
            self.print_debug('Nothing to copy!', colour=self.colours['error_fg'])
            return

        self.session_id = self.encode_id(self.question_list)
        if self.config['include_session_ids']:
            self.question += f"\n\nSession ID: {self.session_id}\n"

        self.print_debug('Copied to clipboard.', colour=self.colours['copy_fg'], always_print=True)
        self.clipboard_clear()
        self.clipboard_append(self.question)

    # Ensures the program is closed properly, by calling close on the other windows first.
    # This allows them to write their data to file, if necessary.
    def close(self):
        if self.student_window is not None:
            self.student_window.close()

        if self.settings_window is not None:
            self.settings_window.close()

        self.destroy()

    # Creates and places all widgets for this window
    def create_widgets(self):
        # Generate Question Buttons
        self.num_progressions = len(get_dir('./questions'))
        self.progress_buttons = []
        for i in range(self.num_progressions):
            self.progress_buttons += [
                Button(self, text=f'{i + 1:02}', width=1, command=lambda j=i: self.get_questions(j))]
            self.progress_buttons[i].place(x=20 + ((self.w - 200) / self.num_progressions) * i, y=10)

        # Copy Button
        self.copy_button = Button(self, text='Copy Qs', width=10, command=self.copy)
        self.copy_button.place(x=self.w - 100, y=self.h - 105)

        # Add Student Button
        self.add_button = Button(self, text='Add', command=self.add_student)
        self.add_button.place(x=self.w - 110, y=self.h - 75, width=40)
        self.students_button = Button(self, text='Students', command=self.open_student_window)
        self.students_button.place(x=self.w - 70, y=self.h - 75, width=60)

        # Settings Button
        self.settings_button = Button(self, text='Settings', width=10, command=self.open_settings)
        self.settings_button.place(x=self.w - 100, y=self.h - 45)

        # Question Display
        self.question_field = Text(self)
        self.question_field.place(x=20, y=50, width=self.w - 40, height=self.h - 172)

        # Error Log
        self.output_log = Text(self)
        self.output_log.place(x=20, y=self.h - 104, width=self.w - 140, height=85)

        # Search for ID field
        self.search = StringVar()
        self.search.set(" Search Question ID")
        self.searchbox = Entry(self, textvariable=self.search)
        self.searchbox.place(x=self.w - 160, y=10, width=140, height=25)
        self.searchbox.bind('<FocusIn>', self._focus_in)
        self.searchbox.bind('<FocusOut>', self._focus_out)
        self.searchbox.bind('<Return>', self._focus_out)

        self.update_widgets()

    # Takes a session id and reverts it back to the time and question indexes within the file structure
    def decode_id(self, s):
        if len(s) not in (8, 10, 12):
            self.print_debug(f"'{s}' is an incorrect length! ({len(s)})", colour=self.colours['error_fg'])
            self.searchbox.config(bg=self.colours['bad'][1])
            return None

        try:
            s = str(int(s, 16))
            now = date.now()
            data = [date(now.year, now.month, now.day, *[int(s[2 * i:2 * i + 2]) - [18, 37, 29][i] for i in range(3)])]
            q_num = int(s[-2:])
            s = s[6:-2]

            for i in range(len(s) // 2):
                v_num = int(s[2 * i:2 * i + 2])
                data.append((q_num, i, v_num))

        except ValueError:
            self.print_debug(f"'{s}' cannot be converted to hexadecimal!", colour=self.colours['error_fg'])
            self.searchbox.config(bg=self.colours['bad'][1])
            return None

        self.print_debug(
            f'Decoded ID {str(data[0])[11:19]} MT{q_num + 1:02} ' + ', '.join([f'Var {i[2] + 1:02}' for i in data[1:]]))
        return data

    # Takes the current time and 1-3 tuples indicating the index of the MT, Category & Variation within the
    # ./questions/ directory
    def encode_id(self, question_list):
        self.time = date.now()
        t = str(self.time)[11:19].split(':')
        session_id = hex(int(''.join(
            [str(int(t[i]) + [18, 37, 29][i]) for i in range(3)] + [f"{i[2]:02}" for i in question_list] + [
                f"{question_list[0][0]:02}"])))[2:].upper()

        self.print_debug(f'Encoded ID {str(self.time)[11:19]} MT{question_list[0][0] + 1:02} ' + ', '.join(
            [f'Var {i[2] + 1:02}' for i in question_list]))
        self.print_debug('Session ID: ' + session_id)

        return session_id

    # Looks for a needle in a haystack (or rather, the nth occurrence of char needle)
    def findnth(self, haystack, needle='\t', n=4):
        return haystack.replace(needle, ' ', n - 1).find(needle)

    # Returns a tuple of the current offsets and/or dimensions for each window based on the config
    def get_dimensions(self, key):
        if key == 'win_q':
            return self.config['win_q_w'], self.config['win_q_h'], self.config['win_q_ox'], self.config['win_q_oy']
        else:
            return self.config[f'{key}_ox'], self.config[f'{key}_oy']

    # Returns a font tuple using the values defined in the config
    def get_font(self, n):
        return self.config[f'font{n}_face'], self.config[f'font{n}_size']

    # Creates a list containing the total number of variations under each category for each progression
    # This makes it easier to write code that needs to check the max length and iterate over the directories
    # to find files, without needing to use os.listdir() all the time
    def get_dir_size(self):
        try:
            self.num_q = [[
                len(get_dir(f'./questions/{prog}/{cat}'))
                for cat in get_dir(f'./questions/{prog}')
            ] for prog in get_dir('./questions/')]

            return True
        except:
            return False

    # Probably not the best named function. This function reads in the input file and returns a list
    # of each line for all the questions. It also does some formatting, such as removing non-UTF8 "/'
    # and the \t caused by the cell column in the excel spreadsheet.
    def gen_list(self):
        filename = self.config['import_path']

        questions = []
        q_num = 0
        c_num = 0
        v_num = 0
        req = ''
        n = 0

        with open(filename, 'r', encoding='utf-8') as file:
            all_lines = file.read().split('\n')

        try:
            for line in all_lines:
                # Removes all non-utf8 characters so that they don't mess up file reading later
                line = line.replace("‘", "'").replace("’", "'").replace('”', '"').replace('“', '"')

                if line[:4] == "\t\t\t\t":
                    questions[q_num][c_num][v_num] += [line[4:]]
                else:
                    n = self.findnth(line)
                    details = line[:n].split('\t')
                    q_num = int(details[0]) - 1
                    c_num = int(details[1]) - 1
                    v_num = int(details[2]) - 1
                    req = details[3]

                    if len(questions) <= q_num:
                        questions += [[]]
                    if len(questions[q_num]) <= c_num:
                        questions[q_num] += [[]]
                    while len(questions[q_num][c_num]) <= v_num:
                        questions[q_num][c_num] += [[]]

                    if req != '':
                        questions[q_num][c_num][v_num] += ['Requires File: ' + req + '\n']
                    questions[q_num][c_num][v_num] += [line[n + 1:]]
        except ValueError:
            self.print_debug('This file does not match the designed import script! Is it the wrong file?',
                             colour=self.colours['error_fg'])

        return questions

    # Called when a MT number button is clicked. Randomly selects a variation for each
    # category in that mastery level, and creates string containg all necessary details
    # and the announcement message for the student. This string is then placed in the
    # question field.
    def get_questions(self, n):
        # self.update_widgets()
        self.session_id = ''
        self._focus_out(None)
        self.print_debug(f"\n>>Selected MT{n + 1:02} ({len(self.num_q[n])} categories).")
        self.question = f"========== Mastery Test {n + 1} ==========\n"

        self.question_list = []
        require = []
        for i in range(len(self.num_q[n])):
            r = random.randint(1, self.num_q[n][i])
            path = f'./questions/Progression {n + 1:02}/Category {i + 1:02}/Variation {r:02}.txt'

            if not os.path.exists(path):
                self.print_debug(f"'{path}' does not exist!", colour=self.colours['error_fg'])
                return

            self.question_list.append((n, i, r - 1))
            with open(path, 'r', encoding='utf8') as file:
                f = file.read()

            self.question += f"Question {i + 1}:\n{f}\n"
            if 'Requires File: ' in f:
                require.append(f[15: f.index('\n')])

        # Add announcement message
        with open('./resources/announcement.txt', 'r', encoding='utf8') as file:
            self.question += f"\n================================\n{file.read()}\n"

        self.print_debug('Selected {}.'.format(', '.join(
            [f'Var {self.question_list[i][2] + 1:02}({self.num_q[n][i]:02})' for i in range(len(self.question_list))])))

        # Print out required files if necessary
        if require:
            self.print_debug('MT{:02} Requires Files: {}'.format(n + 1, ', '.join(require)),
                             colour=self.colours['require_fg'], always_print=True)

        # Update question field
        # Note: '1.0' means line 1, character 0
        self.question_field.delete('1.0', END)
        self.question_field.insert('1.0', self.question.strip() + '\n\n')
        self.update_widgets()

    # Scans over the question field and attempts to highlight any
    # strings, numbers, Python keywords or built in functions
    def highlight_keywords(self):
        if not self.config['highlighting']:
            self.question_field.tag_remove('strings', '1.0', END)
            self.question_field.tag_remove('numbers', '1.0', END)
            self.question_field.tag_remove('keywords', '1.0', END)
            self.question_field.tag_remove('builtins', '1.0', END)
            return

        for i in range(len(self.keywords)):
            for pattern in self.keywords[i]:
                if self.kwsections[i] == 'numbers':
                    p = fr'\W({pattern})\W'
                elif self.kwsections[i] == 'keywords':
                    p = fr'\W({pattern})[^a-zA-Z0-9_]'
                elif self.kwsections[i] == 'builtins':
                    p = fr'\s({pattern})[ (:]'
                else:
                    p = pattern

                start = self.question_field.index('1.0')
                end = self.question_field.index(END)
                self.question_field.mark_set("matchStart", start)
                self.question_field.mark_set("matchEnd", start)
                self.question_field.mark_set("searchLimit", end)

                count = IntVar()
                index = self.question_field.search(p, "matchEnd", "searchLimit", count=count, regexp=True)
                while index != '':
                    # index = self.question_field.search(f"({pattern})", "matchEnd", "searchLimit", count=count, regexp=True)
                    self.question_field.mark_set("matchStart", index)
                    self.question_field.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
                    self.question_field.tag_add(self.kwsections[i], "matchStart", "matchEnd")
                    index = self.question_field.search(p, "matchEnd", "searchLimit", count=count, regexp=True)

    # Wrapper function just to manage the import and checks from input.txt
    def import_questions(self):
        if self.settings_window is not None:
            self.settings_window.apply()

        if os.path.exists('./questions/'):
            self.print_debug("Deleted './questions/' directory for clean import.", colour=self.colours['require_fg'])
            shutil.rmtree('./questions/')

        g = self.gen_list()
        self.check_empty(g)
        self.write_questions(g)

        if get_dir('./questions/'):
            self.check_readable(g)
            self.print_debug('Import complete!', colour=self.colours['copy_fg'], always_print=True)

    # If Settings window is closed, create a new instance and focus
    def open_settings(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
        self.settings_window.focus()

    # If Students window is closed, create a new instance and focus
    def open_student_window(self):
        if self.student_window is None:
            if not os.path.exists('./marks/') or len(get_dir('./marks/')) == 0:
                self.print_debug('No marking file to read in was found.')
                return

            self.student_window = StudentWindow(self)
        self.student_window.focus()

    # Similar to get_question above, however this one loads up specific questions
    # (and only those questions) based on a provided session id.
    def open_question(self, s=None):
        # Id can be passed either by the 'View' button OR the search field
        if s is None:
            s = self.search.get()
        self.print_debug(f"\n>>Loading questions with ID '{s}'")
        self.session_id = s

        # Decode the id to get question indexes
        result = self.decode_id(s)
        if result is None:
            return

        # Discard the time, as it is unnecessary
        self.time = result.pop(0)
        # Add 1 since names are all 01-12 not 00-11
        result = [tuple([i + 1 for i in j]) for j in result]

        # Open question files and generate string
        self.print_debug(f'Opening MT{result[0][0]:02} ' + ', '.join([f'Var {i[2]:02}' for i in result]))
        self.question = f"========== Mastery Test {result[0][0]} ==========\n"
        for i in range(len(result)):
            try:
                with open('./questions/Progression {:02}/Category {:02}/Variation {:02}.txt'.format(*result[i]), 'r',
                          encoding='utf-8') as file:
                    self.question += f"Question {i + 1}:\n{file.read()}\n\n\n"

            except FileNotFoundError:
                self.print_debug("File for MT{:02}, Cat {:02}, Var {:02} could not be found!".format(*result[i]),
                                 colour=self.colours['error_fg'])
                self.searchbox.config(bg=self.colours['bad'][1])
                return

        # Update question field contents
        # '1.0' means line 1, character 0
        self.question_field.delete('1.0', END)
        self.question_field.insert('1.0', self.question.strip() + '\n\n')
        self.update_widgets()

    # Checks if a directory exists, and if not makes it so
    def path_check(self, cwd, d):
        path = cwd + '/' + d

        if not os.path.exists(path):
            os.mkdir(path)

        return path

    # Program outputs to the output log, or the terminal
    def print_debug(self, s, colour=None, always_print=False):
        try:
            self.output_log.config()
            if colour is None:
                colour = self.colours['textbox'][0]

            if self.config['verbose_output'] or colour == self.colours['error_fg'] or always_print:
                print(s)

                self.output_log.insert(END, '\n>>' + s, colour)
                self.output_log.see(END)

                self.output_log.tag_config(colour, foreground=colour)

                if colour == self.colours['error_fg']:
                    self.output_log.config(bg=self.colours['bad'][1])
                    self.after(500, lambda: self.output_log.config(bg=self.colours['textbox'][1]))
                elif colour == self.colours['require_fg']:
                    self.output_log.config(bg=self.colours['alert_bg'])
                    self.after(500, lambda: self.output_log.config(bg=self.colours['textbox'][1]))
        except:
            print(s)

    # Reads in the current config file and sets values within the program
    # or, if it doesn't exist, sets those value to their default
    def read_config(self):
        if os.path.exists('./config.json'):
            self.print_debug('Reading configuration from file.')

            # Reads config from JSON file
            with open('./config.json', 'r') as file:
                data = json.load(file)

            self.config = data['config']
            self.colours = data['colours']
            return

        self.print_debug('No configuration file found. Initialising from defaults.')

        # Default config values
        self.config = {
            'font1_face': "Times New Roman",
            'font2_face': "Times New Roman",
            'import_path': './input.txt',
            'font1_size': 10,
            'font2_size': 12,
            'time_limit': 45,
            'time_offset': 34,
            'win_q_w': 512,
            'win_q_h': 768,
            'win_q_ox': 0,
            'win_q_oy': 30,
            'win_stu_ox': 500,
            'win_stu_oy': 200,
            'win_set_ox': -420,
            'win_set_oy': 200,
            'highlighting': True,
            'include_session_ids': True,
            'verbose_output': True,
            'wrap_text': True
        }

        # Default colour values
        self.colours = {
            'textbox': ['black', 'white'],
            'interface': ['black', '#F0F0ED'],
            'buttons': ['black', '#F0F0ED'],
            'active_button': ['black', '#FFFFFF'],
            'good': ['black', 'lawn green'],
            'bad': ['black', 'tomato'],
            'good_time': ['white', 'green'],
            '15_time': ['black', 'orange'],
            'bad_time': ['white', 'red'],
            'finished': ['black', 'sky blue'],
            'strings': ['chartreuse4', 'white'],
            'numbers': ['goldenrod', 'white'],
            'keywords': ['purple', 'white'],
            'builtins': ['steel blue', 'white'],
            'alert_bg': 'yellow',
            'copy_fg': 'green',
            'error_fg': 'red',
            'placeholder_fg': 'grey',
            'require_fg': 'orange',
        }

        # Since a config file doesn't exist, write a new one
        self.write_config()

    # Ensures all widgets in this window are using the current configuration of dimensions,
    # fonts and colours, then call's on the other windows, if they exist, to do the same
    def update_widgets(self):
        # Update Window Dimensions
        self.geometry(self.centre(*self.get_dimensions('win_q')))

        # Get Fonts
        f1 = self.get_font(1)
        f2 = self.get_font(2)

        # Interface Elements
        self.configure(bg=self.colours['interface'][1])
        fg, bg = self.colours['buttons']
        afg, abg = self.colours['active_button']
        self.copy_button.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        self.add_button.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        self.students_button.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        self.settings_button.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        for b in self.progress_buttons:
            b.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)

        # Textbox Elements
        fg, bg = self.colours['textbox']
        self.searchbox.config(font=f1, fg=self.colours['placeholder_fg'], bg=bg)
        self.question_field.config(font=f2, fg=fg, bg=bg, wrap=WORD if self.config['wrap_text'] else NONE)
        self.output_log.config(font=f2, fg=fg, bg=bg)

        # Tags
        self.question_field.tag_config("strings", foreground=self.colours['strings'][0],
                                       background=self.colours['strings'][1])
        self.question_field.tag_config("numbers", foreground=self.colours['numbers'][0],
                                       background=self.colours['numbers'][1])
        self.question_field.tag_config("keywords", foreground=self.colours['keywords'][0],
                                       background=self.colours['keywords'][1], font=(f2[0], f2[1], "bold"))
        self.question_field.tag_config("builtins", foreground=self.colours['builtins'][0],
                                       background=self.colours['builtins'][1])
        self.highlight_keywords()

        # Update Widgets in Settings Window
        if self.settings_window is not None:
            self.settings_window.update_widgets()

        # Update Widgets in Students Window
        if self.student_window is not None:
            self.student_window.update_widgets()

    # Write the current configuration settings to a JSON file
    def write_config(self):
        data = {'config': self.config, 'colours': self.colours}

        with open('config.json', 'w') as file:
            json.dump(data, file)

    # Writes each of the imported questions to it's own file
    def write_questions(self, questions):
        p = self.path_check('.', 'questions')
        for q in range(len(questions)):

            p = self.path_check(p, 'Progression {:02}'.format(q + 1))
            for c in range(len(questions[q])):

                p = self.path_check(p, 'Category {:02}'.format(c + 1))
                for v in range(len(questions[q][c])):
                    with open('{}/Variation {:02}{}'.format(p, v + 1, '.txt'), 'w') as file:
                        file.write('\n'.join(questions[q][c][v]))
                p = './questions/Progression {:02}'.format(q + 1)
            p = './questions/'


# Popup window for entering the student's name
class EntryPopup(Toplevel):

    def __init__(self, parent, prompt):
        super().__init__(master=parent)
        self.parent = parent

        self.title(prompt)
        self.geometry(self.parent.centre(380, 50))
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.config(bg=self.parent.colours['interface'][1])

        self.s = StringVar()
        self.s.set(prompt)
        self.e = Entry(self, textvariable=self.s, font=self.parent.get_font(2),
                       fg=self.parent.colours['placeholder_fg'], bg=self.parent.colours['textbox'][1])
        self.e.place(x=20, y=12.5, width=260, height=25)
        self.e.bind('<FocusIn>', self._focus_in)
        self.e.bind('<Return>', self.close)

        self.confirm = Button(self, text='Confirm', command=self.close)
        self.confirm.config(font=self.parent.get_font(1), fg=self.parent.colours['buttons'][0],
                            bg=self.parent.colours['buttons'][1])
        self.confirm.config(activeforeground=self.parent.colours['active_button'][0],
                            activebackground=self.parent.colours['active_button'][1])
        self.confirm.place(x=300, y=12.5, width=60, height=25)

    # Remove the placeholder text (although I think it focuses in  automatically now, so this probably happens
    # immediately)
    def _focus_in(self, e):
        self.s.set("")
        self.e.config(fg=self.parent.colours['textbox'][0], bg=self.parent.colours['textbox'][1])

    # On close update the value so that it can be returned
    def close(self, e=None):
        self.value = self.s.get()
        self.destroy()


# Window for managing settings of the program
class SettingsWindow(Toplevel):

    def __init__(self, parent):
        super().__init__(master=parent)
        self.parent = parent

        self.title("MTAssist Settings")
        self.w = 300
        self.h = 400
        self.geometry(self.parent.centre(self.w, self.h, *self.parent.get_dimensions('win_set')))
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close)

        # Copies the current config and colour values, so that they can be edited
        # locally, without impacting the whole program.
        self.cfg = copy.copy(self.parent.config)
        self.col = copy.deepcopy(self.parent.colours)

        # Adding styles so help configure the ttk elements' appearance
        self.style = ttk.Style()
        self.notebook = ttk.Notebook(self, style="TNotebook")
        self.tabs = (ttk.Frame(self.notebook, style="TFrame"), ttk.Frame(self.notebook, style="TFrame"),
                     ttk.Frame(self.notebook, style="TFrame"))

        # Appends the tabs tot he notebook
        self.notebook.add(self.tabs[0], text="General")
        self.notebook.add(self.tabs[1], text="Window")
        self.notebook.add(self.tabs[2], text="Aesthetics")

        self.notebook.pack(expand=1, fill='both')

        self.draw()

    # Copies the current settings back to the main program,
    # updates all widgets and writes these new settings to file
    def apply(self):
        # This section just ensures that if you haven't edited the bg
        # of the highlighted keywords, then it is instead updated to
        # match that of the textbox bg (i.e. so you don't end up with
        # white squares around all the highlighted words)
        if self.col['strings'][1] == self.parent.colours['textbox'][1]:
            self.col['strings'][1] = self.col['textbox'][1]
        if self.col['numbers'][1] == self.parent.colours['textbox'][1]:
            self.col['numbers'][1] = self.col['textbox'][1]
        if self.col['keywords'][1] == self.parent.colours['textbox'][1]:
            self.col['keywords'][1] = self.col['textbox'][1]
        if self.col['builtins'][1] == self.parent.colours['textbox'][1]:
            self.col['builtins'][1] = self.col['textbox'][1]

        self.parent.config = copy.copy(self.cfg)
        self.parent.colours = copy.deepcopy(self.col)
        self.parent.update_widgets()
        self.parent.write_config()

    # A shorthand function to convert the colour name as displayed
    # back into the colour key so that it can be referenced
    def ctk(self, colour):
        return '_'.join(colour.split(' ')).lower()

    # Ensures the window closes properly. Does NOT write to file!
    def close(self):
        self.parent.settings_window = None
        self.parent.focus()
        self.destroy()

    # Creates all the widgets and places them
    def draw(self):
        # Load config values into StringVar()s, IntVar()s, and BooleanVar()s
        # So that they can be used as default values.
        self.vars = dict()
        for key in self.cfg.keys():
            # Creates appropriate Var() wrapper
            if type(self.cfg[key]) == str:
                self.vars.update({key: StringVar()})
            elif type(self.cfg[key]) == int:
                self.vars.update({key: IntVar()})
            elif type(self.cfg[key]) == bool:
                self.vars.update({key: BooleanVar()})

            # Sets the default value
            self.vars[key].set(self.cfg[key])
            # Adds a trace, which calls a function whenever the Var() is updated!
            self.vars[key].trace_add("write", lambda name, index, mode, k=key: self.update_val(k))

        # Labels
        self.labels = [
            (Label(self.tabs[0], text='Import File:'), (10, 20, 100, 20)),
            (Label(self.tabs[0], text='MT Length (mins)', anchor=W), (30, 128, 100, 20)),
            (Label(self.tabs[0], text='Start Time Offset (secs)', anchor=W), (30, 148, 130, 20)),
            (Label(self.tabs[1], text='Question Window', anchor=W), (43, 20, 110, 20)),
            (Label(self.tabs[1], text=' width\t height\t offset x\t offset y', anchor=W), (43, 40, 200, 20)),
            (
                Label(self.tabs[1],
                      text='Note: may need to restart program to update widget dimensions within the window.',
                      wraplength=self.w - 50), (25, 90, self.w - 50, 40)),
            (Label(self.tabs[1], text='Students Window\tSettings Window', anchor=W), (18, 160, 250, 20)),
            (Label(self.tabs[1], text=' offset x\t offset y\t\t offset x\toffset y', anchor=W), (18, 180, 250, 20)),
            (Label(self.tabs[2], text='Interface Font', anchor=W), (20, 20, self.w - 40, 20)),
            (Label(self.tabs[2], text='Textbox Font', anchor=W), (20, 90, self.w - 40, 20)),
            (Label(self.tabs[2], text='Text Colours', anchor=W), (20, 200, self.w - 40, 20)),
        ]
        # Place the labels, wherever defined by the tuples above
        for l in self.labels:
            l[0].place(x=l[1][0], y=l[1][1], width=l[1][2], height=l[1][3])

        # Cancel & Apply Buttons (for each tab)
        self.ctrl_btns = []
        for i in range(len(self.tabs)):
            self.ctrl_btns += [Button(self.tabs[i], text='Cancel', command=self.close, relief=RIDGE)]
            self.ctrl_btns += [Button(self.tabs[i], text='Apply', command=self.apply, relief=RIDGE)]
            self.ctrl_btns[2 * i].place(x=10, y=self.h - 55, width=self.w // 2 - 15, height=25)
            self.ctrl_btns[2 * i + 1].place(x=self.w // 2 + 5, y=self.h - 55, width=self.w // 2 - 15, height=25)

        # Questions Tab
        # Entries
        self.import_entry = Entry(self.tabs[0], textvariable=self.vars['import_path'], justify=RIGHT)
        self.test_length_entry = Entry(self.tabs[0], textvariable=self.vars['time_limit'], justify=RIGHT)
        self.timer_offset_entry = Entry(self.tabs[0], textvariable=self.vars['time_offset'], justify=RIGHT)

        # Buttons
        self.select_file_btn = Button(self.tabs[0], text='...', command=self.select_file)
        self.import_btn = Button(self.tabs[0], text='Reimport', command=self.parent.import_questions)
        self.toggle_btns = []
        for key in self.cfg.keys():
            if type(self.cfg[key]) == bool:
                i = len(self.toggle_btns)
                self.toggle_btns.append(
                    Checkbutton(self.tabs[0], text=' '.join(key.split('_')).title(), variable=self.vars[key], anchor=W))
                self.toggle_btns[i].place(x=(self.w - 130) // 2, y=200 + 30 * i, width=130, height=25)

        # Placement
        self.import_entry.place(x=23, y=40, width=self.w - 100, height=25)
        self.select_file_btn.place(x=self.w - 70, y=39, width=40, height=25)
        self.import_btn.place(x=22, y=70, width=self.w - 52, height=25)
        self.test_length_entry.place(x=self.w - 70, y=128, width=30, height=20)
        self.timer_offset_entry.place(x=self.w - 70, y=148, width=30, height=20)

        # Window Tab
        # Entries
        self.win_xy_entries = []
        keys = list(filter(lambda x: 'win' in x, self.cfg.keys()))
        for i in range(8):
            self.win_xy_entries.append(Entry(self.tabs[1], textvariable=self.vars[keys[i]], justify=RIGHT))
            offset = 0
            if i < 4:
                offset += 25
            elif i > 5:
                offset += 45
            self.win_xy_entries[i].place(x=20 + 50 * (i % 4) + offset, y=60 + 140 * (i // 4), width=40, height=25)

        # Aesthetics Tab
        # List of colour keys for each usage (i.e. textbox fg/bg, etc)
        colours = [' '.join(i.split('_')).title() for i in self.col.keys()]
        self.sel_colour = StringVar()
        self.sel_colour.set(colours[0])

        # List of available fonts
        fonts = font.families()

        # Font size entries
        self.font1_size_entry = Entry(self.tabs[2], textvariable=self.vars['font1_size'], justify=RIGHT)
        self.font2_size_entry = Entry(self.tabs[2], textvariable=self.vars['font2_size'], justify=RIGHT)

        # Option Menus
        self.font1_menu = OptionMenu(self.tabs[2], self.vars['font1_face'], *fonts)
        self.font2_menu = OptionMenu(self.tabs[2], self.vars['font2_face'], *fonts)
        self.colour_menu = OptionMenu(self.tabs[2], self.sel_colour, *colours, command=self.set_colour_name)
        # Getting rid of weird border
        self.font1_menu['highlightthickness'] = 0
        self.font2_menu['highlightthickness'] = 0
        self.colour_menu['highlightthickness'] = 0

        # Buttons
        self.fg_btn = Button(self.tabs[2], text='Foreground', command=self.set_fg, relief=RIDGE)
        self.bg_btn = Button(self.tabs[2], text='Background', command=self.set_bg, relief=RIDGE)

        # Placement
        self.font1_size_entry.place(x=self.w - 50, y=22, width=20, height=15)
        self.font2_size_entry.place(x=self.w - 50, y=92, width=20, height=15)
        self.font1_menu.place(x=23, y=40, width=self.w - 46, height=30)
        self.font2_menu.place(x=23, y=110, width=self.w - 46, height=30)
        self.colour_menu.place(x=20, y=220, width=self.w - 40, height=30)
        self.fg_btn.place(x=30, y=260, width=self.w // 2 - 40, height=20)
        self.bg_btn.place(x=self.w // 2, y=260, width=self.w // 2 - 30, height=20)

        # Update widgets with appropriate colours
        self.update_widgets()

    # Enables / disables / alters colours of the fg and bg buttons
    # as according to the selected colour name from the option menu
    def set_colour_name(self, name):
        key = self.ctk(name)
        if type(self.col[key]) == list:
            self.fg_btn.config(state=NORMAL, fg=self.col[key][0], bg=self.col[key][1])
            self.bg_btn.config(state=NORMAL, fg=self.col[key][0], bg=self.col[key][1])
        elif 'fg' in key:
            self.fg_btn.config(state=NORMAL, fg=self.col[key], bg=self.col['textbox'][1])
            self.bg_btn.config(state=DISABLED, fg=self.col[key], bg=self.colour_menu.cget('bg'))
        else:
            self.fg_btn.config(state=DISABLED, fg=self.col['textbox'][0], bg=self.colour_menu.cget('bg'))
            self.bg_btn.config(state=NORMAL, fg=self.col['textbox'][0], bg=self.col[key])

    # Loads the colour picker window to define a new bg colour
    def set_bg(self):
        current = self.bg_btn.cget('bg')
        rgb, col_string = colorchooser.askcolor(parent=self, title='New Background Colour:', initialcolor=current)

        if col_string and col_string != current:
            self.col[self.ctk(self.sel_colour.get())][1] = col_string
            self.fg_btn.config(bg=col_string)
            self.bg_btn.config(bg=col_string)

    # Loads the colour picker window to define a new fg colour
    def set_fg(self):
        current = self.fg_btn.cget('fg')
        rgb, col_string = colorchooser.askcolor(parent=self, title='New Foreground Colour:', initialcolor=current)

        if col_string and col_string != current:
            self.col[self.ctk(self.sel_colour.get())][0] = col_string
            self.fg_btn.config(fg=col_string)
            self.bg_btn.config(fg=col_string)

    # Loads the file dialogue window to select a new file to import from
    def select_file(self):
        self.vars['import_path'].set(filedialog.askopenfilename())
        # Moves to the right side of the path
        self.import_entry.xview_moveto(1)

    # Takes any traced Var() value that has been updated and sets the relevant config with that value
    def update_val(self, key):
        try:
            self.parent.print_debug(f"Setting '{key}'  |  {self.cfg[key]} -> {self.vars[key].get()}")
            self.cfg[key] = self.vars[key].get()
            self.update_widgets()
        except TclError:
            return  # Ignore if empty

    # Update all widgets in this window to meet the current LOCAL colour
    # configuration (so you can preview, of sorts)
    def update_widgets(self):
        # Update Window Dimensions
        self.geometry(self.parent.centre(self.w, self.h, *self.parent.get_dimensions('win_set')))

        # Get Fonts
        f1 = self.parent.get_font(1)
        f2 = self.parent.get_font(2)

        # TopLevel (self), ttk.Frame, and ttk.Notebook
        fg, bg = self.col['interface']
        self.config(bg=bg)
        self.style.configure('TNotebook', background=bg)
        self.style.configure('TFrame', background=bg)

        # Labels
        for l in self.labels:
            l[0].config(font=f1, fg=fg, bg=bg)

        # Entry Widgets
        fg, bg = self.col['textbox']
        self.import_entry.config(font=f1, fg=fg, bg=bg)
        self.test_length_entry.config(font=f1, fg=fg, bg=bg)
        self.timer_offset_entry.config(font=f1, fg=fg, bg=bg)
        self.font1_size_entry.config(font=f1, fg=fg, bg=bg)
        self.font2_size_entry.config(font=f1, fg=fg, bg=bg)
        for e in self.win_xy_entries:
            e.config(font=f1, fg=fg, bg=bg)

        # Buttons & Option Menus
        fg, bg = self.col['buttons']
        afg, abg = self.col['active_button']
        self.select_file_btn.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        self.import_btn.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        self.font1_menu.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        self.font2_menu.config(font=f2, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        self.colour_menu.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)
        for b in self.ctrl_btns:
            b.config(font=f1, fg=fg, bg=bg, activeforeground=afg, activebackground=abg)

        fg, bg = self.col[self.ctk(self.sel_colour.get())]
        self.fg_btn.config(fg=fg, bg=bg, activeforeground=fg, activebackground=bg)
        self.bg_btn.config(fg=fg, bg=bg, activeforeground=fg, activebackground=bg)

        fg, bg = self.col['interface']
        for b in self.toggle_btns:
            b.config(font=f1, fg=fg, bg=bg, activeforeground=fg, activebackground=bg)


# Window for managing students being tested
class StudentWindow(Toplevel):

    def __init__(self, parent):
        super().__init__(master=parent)
        self.parent = parent

        # Basic window stuff
        self.title("MTAssist Students")
        self.w = 400
        self.h = 45
        self.geometry(self.parent.centre(self.w, self.h, *self.parent.get_dimensions('win_stu')))
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close)

        # Defines some variables for later
        self.saved = False
        self.students = []
        self.marks = ['N/A', 'PASS', 'FAIL']
        self.set_time_limit(self.parent.config['time_limit'])
        self.timer_offset = timedelta(seconds=self.parent.config['time_offset'])
        self.num_complete = 0

        # Read in old records, draw widgets, and start the clock
        self.read()
        self.draw()
        self.tick()

        # Try to close the window after 100ms
        self.after(100, self.try_close)

    # Adds a new student to the students list (including relevant deatils AND objects used to display)
    def add(self, name, progression, session_id, mark=None, start_time=None, elapsed_time=None):
        s = {
            'name': name,
            'mt_num': progression,
            'session_id': session_id,
            'mark': 0 if mark is None else mark,
            'start': self.parent.time + self.timer_offset if start_time is None else start_time,
            'end': date.now() if start_time is None or mark == 0 else start_time + elapsed_time,
            'name_label': Label(self, text=name, anchor=W),
            'elapsed_time': StringVar(),
            'timer': None,
            'btn_text': StringVar(),
            'mark_btn': None,
            'view_btn': None
        }
        s['timer'] = Label(self, textvariable=s['elapsed_time'])
        s['mark_btn'] = Button(self, textvariable=s['btn_text'], command=lambda x=s: self.next_mark(x))
        s['view_btn'] = Button(self, text='View', command=lambda x=s: self.parent.open_question(x['session_id']))
        s['btn_text'].set(self.marks[s['mark']])
        self.students.insert(0, s)

        if elapsed_time is not None:
            s['elapsed_time'].set(str(s['end'] - s['start'])[:7])

        self.update_position()
        self.draw()

    # Autosave records every 15 minutes, without needing to close
    def autosave(self):
        n = date.now()

        # If not already saved, and 14, 29, 44, or 59 minutes, save.
        # Note, I used one minute before to get accurate measure of current lab start
        if not (self.saved or (n.minute + 1) % 15):
            self.write()
            self.parent.print_debug("Autosave Complete.", colour=self.parent.colours['copy_fg'])
            self.saved = True

        # Resets the saved boolean for next time (after the save minute has passed)
        elif not n.minute % 15:
            self.saved = False

    # Closes the window appropriately
    # This INCLUDES writing both to JSON and exporting to a nice human-readable .txt
    def close(self):
        self.write()
        self.export()
        self.parent.student_window = None
        self.parent.focus()
        self.destroy()

    # Draws all relevant widgets, per student in the student's list
    def draw(self):

        # Update the height of the window according to the number of students
        self.geometry(
            self.parent.centre(self.w, self.h + 30 * (len(self.students) - 1), *self.parent.get_dimensions('win_stu')))

        for i in range(len(self.students)):
            s = self.students[i]

            # Forget the old placement as position may have changed
            s['timer'].pack_forget()
            s['name_label'].pack_forget()
            s['mark_btn'].pack_forget()
            s['view_btn'].pack_forget()

            # Place in new position
            s['timer'].place(x=self.w - 150, y=10 + 30 * i, width=50, height=25)
            s['name_label'].place(x=10, y=10 + 30 * i, width=self.w - 150, height=25)
            s['mark_btn'].place(x=self.w - 100, y=10 + 30 * i, width=40, height=25)
            s['view_btn'].place(x=self.w - 50, y=10 + 30 * i, width=40, height=25)

        self.update_widgets()

    # Uses the JSON filename to create a string of the datetime info
    # which is used as the header for that lab in the exported .txt
    def date_string(self, filename):
        t = filename.split('-')
        t.remove('')
        t[-1] = t[-1][:2]
        d = date(*[int(i) for i in t])
        wkd = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][d.weekday()]
        return f'{d.year}-{d.month}-{d.day}\t\t{d.hour}:00-{d.hour + 2}:00\t{wkd}\n'

    # Reads all ./marks/*.json files and aggregates them into a single, human-readable .txt
    def export(self):
        if not os.path.exists('./marks/'):
            return

        data = []
        for filename in get_dir('./marks/'):
            with open(f'./marks/{filename}', 'r') as file:
                data.append({'filename': filename, 'data': json.load(file)})

        s = ''
        for lab in data:
            if not lab['data']:
                continue

            s += self.date_string(lab['filename'])

            for student in lab['data']:
                s += f'{student["name"]:<16}\t'
                s += f'MT{student["mt_num"] + 1:02}\t'
                s += f'{self.marks[student["mark"]]}\t'
                s += str(student["start_time"])[11:19] + '\t'
                s += str(eval(student["elapsed_time"]))[:7] + ' \t'
                s += f'{student["session_id"]}\n'

            s += '\n'

        with open('./marks.txt', 'w') as file:
            file.write(s)

    # Uses the current time and date to work out what the JSON file should be called
    def get_json_filename(self):
        n = date.now()
        return f'./marks/{n.year}-{n.month}-{n.day}--{self.get_lab_start(n)}00.json'

    # Based on our work schedule, this function returns the starting time of the current lab
    def get_lab_start(self, n):
        return n.hour - 1 if (n.weekday() > 1 and n.hour % 2) or (n.weekday() <= 1 and not n.hour % 2) else n.hour

    # Cycles the student's mark through 0->1->2->0 etc.
    # Triggers update position after 5 seconds so that unmarked students
    # appear at the top, and marked students at the bottom.
    def next_mark(self, student):
        student['mark'] = (student['mark'] + 1) % len(self.marks)
        student['btn_text'].set(self.marks[student['mark']])
        self.num_complete += 1 if student['mark'] > 0 else -1
        self.draw()

        # Note: 5s was used so that the position did not update too
        # soon while the mark is being edited, so that it wouldn't
        # confuse the marker or make them mis-click.
        self.after(5000, self.update_position)

    # Reads in any relevant student data for the current lab period from JSON file
    def read(self):
        path = self.get_json_filename()
        if not os.path.exists(path):
            self.parent.print_debug('No marking file to read in was found.')
            return

        with open(path, 'r') as file:
            data = json.load(file)

        for s in data:
            self.add(s['name'], s['mt_num'], s['session_id'], s['mark'], date.fromisoformat(s['start_time']),
                     eval(s['elapsed_time']))

    # Redefines the time limit, and hence, also when the last 15 minutes is about to begin
    def set_time_limit(self, limit):
        self.time_limit = timedelta(minutes=limit)
        self.final_15 = self.time_limit - timedelta(minutes=15)

    # Clock increases the student's timer at a rate of 1 second per second
    def tick(self):
        for s in self.students:
            if s['mark'] > 0:
                continue

            s['end'] = date.now()
            elapsed_time = s['end'] - s['start']

            if elapsed_time < timedelta(seconds=0):
                s['elapsed_time'].set('-' + str(s['start'] - s['end'])[:7])
                continue

            s['elapsed_time'].set(str(elapsed_time)[:7])

        self.autosave()
        self.update_widgets()
        self.after(1000, self.tick)

    # Tries to close if students list remains empty
    def try_close(self):
        if len(self.students) == 0:
            self.close()

    # Updates the displayed position of students in the window
    # Unmarked students should appear higher than marked students
    def update_position(self):
        # Creates a list segregated by mark
        sorting = [[], [], []]
        for s in self.students:
            sorting[s['mark']].append((s['end'] - s['start'], s))

        # Sorts each sublist by the elapsed_time and flattens to a single list
        self.students = [student[1] for sublist in sorting for student in sorted(sublist)[::-1]]
        self.draw()

    # Updates all colour and configuration settings to keep in line with what has been defined
    def update_widgets(self):
        # Update Window Dimensions
        self.config(bg=self.parent.colours['interface'][1])
        self.geometry(
            self.parent.centre(self.w, self.h + 30 * (len(self.students) - 1), *self.parent.get_dimensions('win_stu')))

        # Presets
        f1 = self.parent.get_font(1)
        b = self.parent.colours['buttons']
        ab = self.parent.colours['active_button']
        fin = self.parent.colours['finished']
        t1 = self.parent.colours['good_time']
        t2 = self.parent.colours['15_time']
        t3 = self.parent.colours['bad_time']

        # Update Times
        self.set_time_limit(self.parent.config['time_limit'])
        self.timer_offset = timedelta(seconds=self.parent.config['time_offset'])

        # Update Colours & Fonts for Each Student's Widgets
        for s in self.students:
            elapsed_time = s['end'] - s['start']

            # Unconditional Attributes
            s['name_label'].config(font=f1)
            s['timer'].config(font=f1, bg=self.parent.colours['interface'][1])
            s['mark_btn'].config(font=f1)
            s['view_btn'].config(font=f1, fg=b[0], bg=b[1], activeforeground=ab[0], activebackground=ab[1])

            # Conditional Attributes
            if s['mark'] > 0:
                c = self.parent.colours['good'] if s['mark'] == 1 else self.parent.colours['bad']
                s['name_label'].config(fg=fin[0], bg=fin[1])
                s['timer'].config(fg=fin[0])
                s['mark_btn'].config(fg=c[0], bg=c[1], activeforeground=c[0], activebackground=c[1])
                continue

            s['mark_btn'].config(fg=b[0], bg=b[1], activeforeground=b[0], activebackground=b[1])

            if elapsed_time < timedelta(seconds=0):
                s['timer'].config(fg=t3[1])
                s['name_label'].config(fg=t1[0], bg=t1[1])
            elif elapsed_time > self.time_limit:
                s['timer'].config(fg=t3[1])
                s['name_label'].config(fg=t3[0], bg=t3[1])
            elif elapsed_time > self.final_15:
                s['timer'].config(fg=t2[1])
                s['name_label'].config(fg=t2[0], bg=t2[1])
            else:
                s['timer'].config(fg=t1[1])
                s['name_label'].config(fg=t1[0], bg=t1[1])

    # Writes the current lab data to JSON
    def write(self):
        # Don't bother writing if empty
        if not len(self.students):
            return

        # Creates a list of dictionaries for each student
        data = []
        for s in self.students:
            elapsed_time = s['end'] - s['start'] if s["end"] - s["start"] > timedelta(0) else timedelta(0)
            data.append({
                'name': s['name'],
                'mt_num': s['mt_num'],
                'mark': s['mark'],
                'start_time': str(s['start']),
                'elapsed_time': repr(elapsed_time)[9:],
                'session_id': s['session_id']
            })

        # If the directory doesn't exist, make it
        if not os.path.exists('./marks/'):
            os.mkdir('./marks/')

        # Write JSON to file
        with open(self.get_json_filename(), 'w') as file:
            json.dump(data, file)


# Starts the program mainloop
if __name__ == "__main__":
    GUI().mainloop()
