# -*- coding: cp949 -*-
import os
import binascii
import wmi
import pytsk3

import tkinter
from tkinter import filedialog
from tkinter import messagebox
from tkinter import *
import tkinter.ttk

import FAT32
#import NTFS

# 가장 상위 레벨의 윈도우 창을 실행시킬 수 있다.
window = tkinter.Tk()

# 제목 지정
window.title("File Recovery Program")

# ("너비x높이+x좌표+y좌표")
window.geometry("600x200+500+400")

# (상하,좌우) -> 창 크기 조절 가능 여부
# True(1) : 조절 가능
# False(0) : 조절 불가능
window.resizable(False,False)

v = StringVar()
value = []
checkbox1_state = FALSE
checkbox2_state = FALSE

def FRAME():
    global process_value
    global checkbox1_state
    global checkbox2_state
    i=0
    total=0
    while 1:
        filename = "\\\\.\\PhysicalDrive"+str(i)
        try:
            f = open(filename,'rb')
            value.append(filename)
            f.close()
            i+=1
        except:
            break

    labelframe1=tkinter.LabelFrame(window,width=370,height=55,text="Setting file storage folder")
    labelframe1.place(x=10,y=5)

    button = tkinter.Button(window,width=5,command=select_DIR, repeatdelay=1000, repeatinterval=100,text="...")
    button.place(x=315,y=25)

    entry=tkinter.Entry(window,width = 40,state="readonly",textvariable=v)
    entry.place(x=20,y=30)

    labelframe2=tkinter.LabelFrame(window,width=275,height=55,text="Recovery Disk Settings")
    labelframe2.place(x=10,y=65)
    
    labelframe3=tkinter.LabelFrame(window,width=275,height=55,text="File System Settings")
    labelframe3.place(x=10,y=130)

    checkbutton1=tkinter.Checkbutton(window, text="NTFS", command=lambda:value_check(checkbutton2,1))
    checkbutton2=tkinter.Checkbutton(window, text="FAT32",command=lambda:value_check(checkbutton1,2))

    checkbutton1.place(x=30,y=150)
    checkbutton2.place(x=150,y=150)

    combobox = tkinter.ttk.Combobox(window,width=33,height=15,values=value)
    combobox.set("Select DISK")
    combobox.configure(state="readonly")
    combobox.place(x=20,y = 85)

    start_button = tkinter.Button(window,width=10,height=2,command=lambda:check_before_Recover(combobox,checkbutton1,checkbutton2),text="Start Recovery")
    start_button.place(x=300,y = 75)

    window.mainloop()

def select_DIR():
    global v
    dirname=filedialog.askdirectory();
    v.set(dirname)
def check_before_Recover(combobox,checkbutton1,checkbutton2):
    global v
    global checkbox1_state
    global checkbox2_state
    
    if v.get() == "" or combobox.get() == "Select DISK":
        messagebox.showerror("Warning", "Please make sure that you have selected the folder to store the recovery files and the disk to recover.")
    elif checkbox1_state == FALSE and checkbox2_state == FALSE:
        messagebox.showerror("Warning","Please select a file system.")
    else:
        Ask = messagebox.askquestion("Warning","Unmounting or manipulating the disk during a recovery can cause problems in the recovery process.\nDo you want to proceed with the recovery operation?")

        if Ask == 'yes':
            if checkbox1_state == 1:
                NTFS.start(combobox.get(),v.get())
            elif checkbox2_state == 1:
                FAT32.start(combobox.get(),v.get())
            else:
                pass
        else:
            combobox.set("Select DISK")
            v.set("")
            checkbox1_state = FALSE
            checkbox2_state = FALSE
            checkbutton1.deselect()
            checkbutton2.deselect()
            messagebox.showinfo("Cancle","Operation canceled. Please proceed with the recovery setup again.")

    combobox.set("Select DISK")
    v.set("")

def value_check(checkbox,box_num):

    global checkbox1_state
    global checkbox2_state

    checkbox.deselect()

    if box_num == 1:
        checkbox1_state = TRUE
        checkbox2_state = FALSE
    elif box_num == 2:
        checkbox2_state = TRUE
        checkbox1_state = FALSE
    else:
        pass

FRAME()