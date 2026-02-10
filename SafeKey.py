# Libraries

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from PIL import Image, ImageTk
import sys
import os

# External files path correction ----------

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)


# Connection and DB creation ------------

def connect_db():
        try:
            connection = sqlite3.connect('SafeKey_DB.db')
            print('Database connection successfully')
            return connection
        except sqlite3.Error as error:
            print(f'There was a problem connecting with the database: {error}')
            return None

# Table creation function
def create_table():
    conn = connect_db()
    if conn is None:
        return

    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 'Your Passwords' (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Platform TEXT,
            Email TEXT,
            Username TEXT,
            Password TEXT,
            Last_modified TEXT
        )
    ''')

    conn.commit()
    conn.close()

create_table()

# Interface --------------------

# Main window
root = tk.Tk()
root.title('SafeKey')
root.geometry('900x900')
root.resizable(True, True)
root.iconbitmap(resource_path('SafeKey_icon.ico'))
root.config(bg='gray')
root.attributes('-alpha',1)

# Title
title_label = tk.Label(root,text='SafeKey',font=('Cascadia Code Semibold', 30, 'bold'), bg='gray', padx=20)
title_label.pack(pady=30)

# Logo
logocrude = Image.open(resource_path('SafeKey_logo.png'))
logocrude=logocrude.resize((100,100))
logo = ImageTk.PhotoImage(logocrude)
logolabel=tk.Label(root, image=logo, bg='gray')
logolabel.pack(pady=0)

# Search box
search_frame = tk.Frame(root, bg='gray')
search_frame.pack(padx=20, pady=40)

search_entry = tk.Entry(search_frame, width=50, font=('Cascadia Code SemiLight', 12), bd=5)
search_entry.pack(side='left', padx=(0, 10))

search_button = tk.Button(search_frame, text='Search', font=('Cascadia Code Semibold', 12, 'italic'))
search_button.pack(side='left')

new_button = tk.Button(search_frame, text='New', font=('Cascadia Code Semibold', 12, 'italic'), padx=5)
new_button.pack(side='left')

# Results table
columns = ('ID', 'Platform', 'Email', 'Username', 'Password', 'Last modified')

tree = ttk.Treeview(root, columns=columns, show='headings')
tree.heading('ID', text='ID')
tree.column('ID', width=0, stretch=False)
for col in columns[1:]:
    tree.heading(col, text=col)
    tree.column(col, width=140)

tree.pack(fill='both', expand=True, padx=20, pady=10)

# Functions -----------------

# Search function
def search():
    keyword = search_entry.get()
    conn = connect_db()
    cursor = conn.cursor()

    query = '''
    SELECT * FROM 'Your Passwords'
    WHERE Platform LIKE ?
       OR Email LIKE ?
       OR Username LIKE ?
       OR Password LIKE ?
    '''

    like = f'%{keyword}%'
    cursor.execute(query, (like, like, like, like))
    results = cursor.fetchall()

    tree.delete(*tree.get_children())
    for row in results:
        tree.insert('', 'end', values=row)

    conn.close()

search_button.config(command=search)
search_entry.bind('<Return>', lambda event: search())

# Edit function
def edit_cell(event):
    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    if not item:
        return

    col_index = int(column[1:])-1
    column_name = columns[col_index]

        # Block ID and Last modified
    if column_name in ('ID','Last modified'):
        return
    
        # Entry creation above the selected cell
    x, y, width, height = tree.bbox(item, column)
    value = tree.set(item, column)
    entry = tk.Entry(tree)
    entry.place(x=x, y=y, width=width, height=height)
    entry.insert(0, value)
    entry.focus()

    # Cascade menu creation function
    create_entry_context_menu(entry)

    # Editing the cell
    def on_enter(event):
        new_value=entry.get()
        confirm_save(item, column, new_value)
        entry.destroy()

    def on_focus_out(event):
        entry.destroy()

    entry.bind('<Return>', on_enter)
    entry.bind('<FocusOut>', on_focus_out)

tree.bind('<Double-1>', edit_cell)


# Confirm changes message
def confirm_save(item, column, new_value):
    if not messagebox.askokcancel('Confirm','Are you sure you want to save the changes?'):
        return
    
    # Saving the changes to the DB
    record_id = tree.item(item)['values'][0]
    field = columns[int(column[1:])-1]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"UPDATE 'Your Passwords' SET {field}=?, Last_modified=? WHERE ID=?",(new_value, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), record_id))
    
    conn.commit()
    conn.close()
    search()
    
# Cascade menu delete password
menu_delete = tk.Menu(root, tearoff=0)
menu_delete.add_command(label='Delete password', command=lambda: delete_record())

def show_menu_delete(event):
    item = tree.identify_row(event.y)
    if not item:
        return
    menu_delete.post(event.x_root, event.y_root)

tree.bind('<Button-3>', show_menu_delete)

def delete_record():
    selected = tree.focus()
    if not selected:
        return

    if not messagebox.askokcancel('Confirm','Are you sure you want to delete the password?'):
        return

    record_id = tree.item(selected)['values'][0]

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM 'Your Passwords' WHERE ID=?", (record_id,))
    conn.commit()
    conn.close()
    search()

# Edit entry cascade menu
def create_entry_context_menu(entry):
    menu = tk.Menu(entry, tearoff=0)

    menu.add_command(label='Copy', command=lambda: entry.event_generate('<<Copy>>'))
    menu.add_command(label='Cut', command=lambda: entry.event_generate('<<Cut>>'))
    menu.add_command(label='Paste', command=lambda: entry.event_generate('<<Paste>>'))

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    entry.bind('<Button-3>', show_menu)


# New pasword function
def new_password():
    new_win = tk.Toplevel(root)
    new_win.iconbitmap(resource_path('SafeKey_icon.ico'))
    new_win.title('New password')
    new_win.config(bg='gray')
    new_win.geometry('350x300')

    fields = ['Platform', 'Email', 'Username', 'Password']
    entries = {}

    tk.Label(new_win, text='New password', bg='gray', font=('Cascadia Code Semibold', 20, 'bold')).pack(pady=10)

    for f in fields:
        frame = tk.Frame(new_win, bg='gray')
        frame.pack(pady=5)
        tk.Label(frame, text=f+':', width=10,bg='gray', font=('Cascadia Code Semibold', 12), anchor='e').pack(side='left')
        ent = tk.Entry(frame, width=25)
        ent.pack(side='left')
        entries[f] = ent

    def save():
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO 'Your Passwords'
            (Platform, Email, Username, Password, Last_modified)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            entries['Platform'].get(),
            entries['Email'].get(),
            entries['Username'].get(),
            entries['Password'].get(),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        conn.close()
        new_win.destroy()
        search()

    btn_frame = tk.Frame(new_win, bg='gray')
    btn_frame.pack(pady=15)

    tk.Button(btn_frame, text='Save', font=('Cascadia Code Semibold', 10, 'bold'), command=save).pack(side='left', padx=10)
    tk.Button(btn_frame, text='Cancel', font=('Cascadia Code Semibold', 10, 'bold'), command=new_win.destroy).pack(side='left')

new_button.config(command=new_password)


root.mainloop()