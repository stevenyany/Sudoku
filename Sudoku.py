from tkinter import messagebox
from tkinter import filedialog
from tkinter import *

class SudokuCell(Label):
    '''represents a Sudoku cell'''

    def __init__(self,master):
        '''SudokuCell(master) -> SudokuCell
        creates a new blank SudokuCell'''
        Label.__init__(self,master,height=1,width=2,text='',\
                       bg='white',font=('Arial',24))
        self.number = 0  # 0 represents an empty cell
        self.readOnly = False     # starts as changeable
        self.highlighted = False  # starts unhighlighted
        self.possibles = {1,2,3,4,5,6,7,8,9}   # set of possible fills
        # set up listeners
        self.bind('<Button-1>',self.highlight)
        self.bind('<Key>',self.change)

    def get_cell(self):
        '''SudokoCell.get_cell() -> int
        returns the number in the cell (0 if empty)'''
        return self.number

    def is_read_only(self):
        '''SudokuCell.is_read_only() -> boolean
        returns True if the cell is read-only, False if not'''
        return self.readOnly

    def is_highlighted(self):
        '''SudokuCell.is_highlighted() -> boolean
        returns True if the cell is highlighted, False if not'''
        return self.highlighted

    def set_cell(self,value,readOnly=False):
        '''SudokuCell.set_cell(value,[readonly])
        sets the number in the cell and unhighlights
        readOnly=True sets the cell to be read-only'''
        self.number = value
        self.readOnly = readOnly
        self.unhighlight()  # unhighlight the cell after setting it
        # update the cell and check if we created any bad cells
        self.master.update_cells()

    def update_cell(self,badCell=False):
        '''SudokuCell.update_cell()
        displays the number in the cell
        displays as:
          empty if its value is 0
          black if user-entered and legal
          gray if read-only and legal
          red when badCell is True'''
        if self.number == 0:  # cell is empty
            self['text'] = ''
        else:  # cell has a number
            self['text'] = str(self.number)  # display the number
            # set the color
            if badCell:
                self['fg'] = 'red'
            elif self.readOnly:
                self['fg'] = 'dim gray'
            else:
                self['fg'] = 'black'

    def highlight(self,event):
        '''SudokuCell.highlight(event)
        handler function for mouse click
        highlights the cell if it can be edited (non-read-only)'''
        if not self.readOnly:  # only act on non-read-only cells
            self.master.unhighlight_all()  # unhighlight any other cells
            self.focus_set()  # set the focus so we can capture key presses
            self.highlighted = True
            self['bg'] = 'lightgrey'

    def unhighlight(self):
        '''SudokuCell.unhighlight()
        unhighlights the cell (changes background to white)'''
        self.highlighted = False
        self['bg'] = 'white'

    def change(self,event):
        '''SudokuCell.change(event)
        handler function for key press
        only works on editable (non-read-only) and highlighted cells
        if a number key was pressed: sets cell to that number
        if a backspace/delete key was pressed: deletes the number'''
        # only act if the cell is editable and highlighted
        if not self.readOnly and self.highlighted:
            if '1' <= event.char <= '9':  # number press -- set the cell
                self.set_cell(int(event.char))
            elif event.keysym in ['BackSpace','Delete','KP_Delete']:
                # delete the cell's contents by setting it to 0
                self.set_cell(0)

    def set_possibles(self,value):
        '''SudokuCell.set_possibles()
        sets the set of possible fills'''
        self.possibles = value

    def get_possibles(self):
        '''SudokuCell.get_possibles()
        gets the set of possible fills'''
        return self.possibles

    def is_bad(self):
        '''SudokuCell.is_bad() -> boolean
        returns True if the cell is bad, False otherwise'''
        return self['fg'] == 'red'


class SudokuGrid(Frame):
    '''object for a Sudoku grid'''

    def __init__(self,master):
        '''SudokuGrid(master)
        creates a new blank Sudoku grid'''
        # initialize a new Frame
        Frame.__init__(self,master,bg='black')
        self.grid()
        # put in lines between the cells
        # (odd numbered rows and columns in the grid)
        for n in range(1,17,2):
            self.rowconfigure(n,minsize=1)
            self.columnconfigure(n,minsize=1)
        # thicker lines between 3x3 boxes and at the bottom
        self.columnconfigure(5,minsize=3)
        self.columnconfigure(11,minsize=3)
        self.rowconfigure(5,minsize=3)
        self.rowconfigure(11,minsize=3)
        self.rowconfigure(17,minsize=1) # space at the bottom
        # create buttons
        self.buttonFrame = Frame(self,bg='white')  # new frame to hold buttons
        Button(self.buttonFrame,text='Load Grid',command=self.load_grid).grid(row=0,column=0)
        Button(self.buttonFrame,text='Save Grid',command=self.save_grid).grid(row=0,column=1)
        Button(self.buttonFrame,text='Solve',command=self.solve).grid(row=0,column=2)
        Button(self.buttonFrame,text='Reset',command=self.reset).grid(row=0,column=3)
        self.buttonFrame.grid(row=18,column=0,columnspan=17)
        # create the cells
        self.cells = {}  # set up dictionary for cells
        for row in range(9):
            for column in range(9):
                self.cells[(row,column)] = SudokuCell(self)
                # cells go in even-numbered rows/columns of the grid
                self.cells[(row,column)].grid(row=2*row,column=2*column)
        # set up boxes (the 3x3 regions)
        self.boxes = []  # list to store the boxes
        # boxes start at rows/columns that are multiples of 3
        #  each box is a list of 9 cells
        for row in [0,3,6]:
            for column in [0,3,6]:
                boxList = []  # list to store the coordinates of the cells in the box
                # loop over a 3x3 region
                for i in range(3):
                    for j in range(3):
                        boxList.append((row+i,column+j)) # add box to list
                self.boxes.append(boxList) # add the box to the master list of boxes

    def unhighlight_all(self):
        '''SudokuGrid.unhighlight_all()
        unhighlight all the cells in the grid'''
        for cell in self.cells:
            self.cells[cell].unhighlight()

    def update_cells(self):
        '''SudokuGrid.update_cells()
        check for good/bad cells and update their color'''
        for row in range(9):
            for column in range(9):
                foundBad = False
                number = self.cells[(row,column)].get_cell()
                if number > 0:  # only need to check non-empty cells
                    # check all other cells in the same row and column
                    for n in range(9):
                        if n != column:  # look at all other cells in the row
                            if self.cells[(row,n)].get_cell() == number:
                                foundBad = True
                        if n != row:  # look at all other cells in the column
                            if self.cells[(n,column)].get_cell() == number:
                                foundBad = True
                    # find box and check other cells in box
                    box = self.find_box(row,column)
                    # check other cells in box
                    for cell in box:
                        if cell != (row,column):
                            if self.cells[cell].get_cell() == number:
                                foundBad = True
                # update the cell
                self.cells[(row,column)].update_cell(foundBad)

    def load_grid(self):
        '''SudokuGrid.load_grid()
        loads a Sudoku grid from a file'''
        # get filename using tkinter's open file pop-up
        filename = filedialog.askopenfilename(defaultextension='.txt')
        # make sure they chose a file and didn't click "cancel"
        if filename:
            # open the file and read rows into a list
            with open(filename,'r') as sudokufile:
                rowList = sudokufile.readlines()
            # process file data
            for row in range(9):
                for column in range(9):
                    # get column'th character from line row
                    value = int(rowList[row][column])
                    # set the cell
                    # if value is nonzero, cell is read-only
                    self.cells[(row,column)].set_cell(value, value != 0)

    def save_grid(self):
        '''SudokuGrid.save_grid()
        saves the Sudoku grid to a file'''
        # get filename using tkinter's save file pop-up
        filename = filedialog.asksaveasfilename(defaultextension='.txt')
        # make sure they chose a file and didn't click "cancel"
        if filename:
            with open(filename,'w') as sudokufile: # open file for writing
                for row in range(9):
                    for column in range(9):
                        # add cell to file
                        sudokufile.write(str(self.cells[(row,column)].get_cell()))
                    sudokufile.write('\n')  # new row

    def reset(self):
        '''SudokuGrid.reset()
        clears all non-read-only cells'''
        for cell in self.cells:
            # only clear non-read-only cells
            if not self.cells[cell].is_read_only():
                self.cells[cell].set_cell(0)

    def solve(self):
        '''SudokuGrid.solve()
        solves the Sudoku grid (if possible)
        pops up dialog box at the end indicating the solved status'''
        makingProgress = True
        while makingProgress:
            makingProgress = self.fill_in_no_brainers() or self.fill_in_only_possibles()
        # we've solved as much as we can
        # check to see if we've solved completely or if the grid is broken
        isBroken = False
        isSolved = True
        for row in range(9):
            for column in range(9):
                cell = self.cells[(row,column)]
                if cell.get_cell() == 0:  # an empty cell means we haven't solved
                    isSolved = False
                    if len(cell.get_possibles()) == 0:
                        # an empty cell with an empty possibles list means the grid is broken
                        isBroken = True
                elif cell.is_bad():
                    # bad cell
                    isBroken = True
        # show the appropriate message in a dialog box
        if isBroken:
            messagebox.showerror('Sudoku','This grid is impossible to solve.',parent=self)
        elif isSolved:
            messagebox.showinfo('Sudoku','Yay! I solved the grid.',parent=self)
        else:
            messagebox.showinfo('Sudoku','This is the best I could do.',parent=self)

    def find_box(self,row,column):
        '''SudokuGrid.find_box(row,column) -> list
        given cell coordinates, returns the box that the cell is in
          (as a list of coordinates)'''
        for box in self.boxes:
            if (row,column) in box:
                return box

    def fill_in_no_brainers(self):
        '''SudokuGrid.fill_in_no_brainers() -> boolean
        fills in all the "no-brainer" squares: those squares can that
          take only one possible number
        returns True if any get filled in, False if none get filled in.'''
        makingProgress = False # will get set to True if we fill something
        # set the possibles for each cell
        self.set_possibles()
        # loop through grid
        for row in range(9):
            for column in range(9):
                # only consider blank cells
                if self.cells[(row,column)].get_cell() == 0:
                    possibles = self.cells[(row,column)].get_possibles()
                    # check if only one number
                    if len(possibles) == 1:
                        num = possibles.pop()  # get the number
                        # set the cell
                        self.cells[(row,column)].set_cell(num)
                        makingProgress = True  # we've made progress!
        return makingProgress
        
    def set_possibles(self):
        '''SudokuGrid.set_possibles()
        sets the possibles set for each cell'''
        # loop through the grid
        for row in range(9):
            for column in range(9):
                # only consider blank cells
                if self.cells[(row,column)].get_cell() == 0:
                    otherNumbers = set()  # track other numbers
                    for n in range(9): # numbers in row and column
                        otherNumbers.add(self.cells[(row,n)].get_cell())
                        otherNumbers.add(self.cells[(n,column)].get_cell())
                    box = self.find_box(row,column)
                    for cell in box:  # numbers in box
                        otherNumbers.add(self.cells[cell].get_cell())
                    # numbers not found are possible
                    possibleNumbers = set()
                    for num in range(1,10):
                        if num not in otherNumbers:
                            possibleNumbers.add(num)
                    self.cells[(row,column)].set_possibles(possibleNumbers)

    def fill_in_only_possibles(self):
        '''SudokuGrid.fill_in_only_possibles() -> boolean
        fills in any cell with only one possible number
        returns True if any get filled in, False if none get filled in'''
        makingProgress = False # will get set to True if we fill something
        # set the possibles for each cell
        self.set_possibles()
        # loop through rows
        for row in range(9):
            # look for a number that's only possible in one square of the row
            for number in range(1,10):
                possibleColumns = []
                for column in range(9):
                    # look at possible list for blank cells
                    if self.cells[(row,column)].get_cell() == 0 and \
                       number in self.cells[(row,column)].get_possibles():
                        possibleColumns.append(column)
                # see if we got only one column
                if len(possibleColumns) == 1:
                    # place the number!
                    self.cells[(row,possibleColumns[0])].set_cell(number)
                    makingProgress = True  # we're making progress!
        # update possibles
        self.set_possibles()
        # loop through columns
        for column in range(9):
            # look for a number that's only possible in one square of the column
            for number in range(1,10):
                possibleRows = []
                for row in range(9):
                    # look at possible list for blank cells
                    if self.cells[(row,column)].get_cell() == 0 and \
                       number in self.cells[(row,column)].get_possibles():
                        possibleRows.append(row)
                # see if we got only one column
                if len(possibleRows) == 1:
                    # place the number!
                    self.cells[(possibleRows[0],column)].set_cell(number)
                    makingProgress = True  # we're making progress!
        # update possibles
        self.set_possibles()
        # loop through boxes
        for box in self.boxes:
            # look for a number that's only possible in one square of the box
            for number in range(1,10):
                possibleCells = []
                for cell in box:
                    # look at possible list for blank cells
                    if self.cells[cell].get_cell() == 0 and \
                       number in self.cells[cell].get_possibles():
                        possibleCells.append(cell)
                # see if we got only one cell
                if len(possibleCells) == 1:
                    # place the number!
                    self.cells[possibleCells[0]].set_cell(number)
                    makingProgress = True  # we're making progress!
        return makingProgress
        

# main loop for the game
def sudoku():
    '''sudoku()
    plays sudoku'''
    root = Tk()
    root.title('Sudoku')
    SudokuGrid(root)
    root.mainloop()

sudoku()