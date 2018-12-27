# -*- coding: cp949 -*-

import os
import binascii # Module for converting binary values to hex values
import sys
from tkinter import *
import tkinter as tk
import tkinter.ttk
from tkinter import filedialog
import time

file_count = 0
dir_count = 0
disk_location = 0
partition_count = 0

#List of starting addresses (decimal, byte units) for each partition are stored
partition_start=[]
partition_Directory_Entry_Analysis=[]

# List of deleted files in all partitions
file_data_address = []
file_data_size=[]
file_extension = []

# List of deleted directories of all partitions
dir_data_address = []
dir_into_partition_num = []

def start(diskname,dir_path):
    #open file read / binary mode
    disk = open(diskname,'rb+')

    get_Partition_info(disk)
    
    #get Directory Entry Analysis info
    get_Directory_Entry_Analysis_info(disk)
    
    for i in range(partition_count):
        get_file_info(disk,i)
   
    for i in range(dir_count):
        print(i)
        get_file_info_in_DIR(disk,i,dir_into_partition_num[i])

    File_Recover(disk,dir_path)
    
    disk.close()
 
    del partition_start[:]
    del partition_Directory_Entry_Analysis[:]
    del file_data_address[:]
    del file_data_size[:]
    del file_extension[:]

# Convert the readings to a value and return them in decimal form (sector units)
def get_value(value):
    
    # It's in the form of Little Endian, so turn it upside down to check.
    value.reverse()

    # 16 Put the letter '0x' on it to make it into the essence.
    value = "0x"+"".join(value)

    # The hexadecimal value in string form is converted to actual hexadecimal number. "0x00000080" (string) -> 0x00000080 (true number)
    value = int(value,16)

    return value

# Store the starting address of the partition in MBR.         After examining the MBR/GPT method, obtain the start address of each partition with the other two functions.
#                                                             If the MBR method is used, the start address of each partition is obtained as a function.
def get_Partition_info(disk):

    global disk_location
    global partition_count
    global partition_start

# This information is 1 0 x be 446, and to gain access to the partition information 
# because I have to take one from addresses in 16 byte byte should move.

    disk.seek(0)
    disk.read(446)
    disk_location = disk.tell()
    #get Partition count
    while disk_location < 510 :
        partition = disk.read(16)
        if binascii.hexlify(partition) != b'00000000000000000000000000000000':

            address_temp = get_partition_start_location(disk,disk_location)

            # If the start address is sector #1, it is a GPT partition.
            # Sector 1 contains GPT information, and the address of the GPT Partition Entry,
            # which contains information about each partition.
            
            if address_temp == 1:
                Partition_Entry_address = get_GPT_Partition_Entry_address(disk)
                get_GPT_Partition_info(disk,Partition_Entry_address)
                break;

            partition_start.append(address_temp)
            partition_count+=1

        disk_location = disk.tell()

#------ Used for GPT Partition------#
#If the GPT method is not MBR method, return the address of the GPT Partition Entry
#that stores the information for each partition in the GPT setup information (sector 1) as a function.

def get_GPT_Partition_Entry_address(disk):
    disk.seek(512)
    disk.read(72)
    #disk.seek(584)

    address = []

    for i in range(8):
        address.append(binascii.hexlify(disk.read(1)).decode())
    
    return get_value(address)

#------ Used for GPT Partition------#
# Save the start address of each partition in the GPT Partition Entry.                      
def get_GPT_Partition_info(disk,Partition_Entry_address):
    global partition_count
    global partition_start

    address = []

    temp = 0

    while 1:
        disk.seek(512 * Partition_Entry_address)
        disk.read(temp * 128)

        if binascii.hexlify(disk.read(16)) == b'00000000000000000000000000000000':
            break;
        else:
            disk.seek(512 * Partition_Entry_address)
            disk.read(temp * 128 + 32)

            for i in range(8):
                address.append(binascii.hexlify(disk.read(1)).decode())

            partition_start.append(get_value(address))

            partition_count += 1

            temp += 1

#------ Used for MBR Partition------#
#Store the start address of each partition within the get_partition_info function.
def get_partition_start_location(disk,partition_one):
    global partition_count

    # Information bytes the 9th of the (16) - the 12th one partition tool that partition is the beginning of the sector
    # since it is storing the information to that location.Please go.
    location = partition_one + 8

   # Temporary list to get partition start address
    address = []

    # Could you move.
    disk.seek(0)
    disk.read(partition_one + 8)
    #disk.seek(location)

    # Receives the starting address in the form of a string.  ex) 80 00 00 00 -> "0x00000080"
    for i in range(4):
        temp = disk.read(1)
        address.append(binascii.hexlify(temp).decode())
        disk.tell()

    address = get_value(address)

    #Go to the next partition information location.
    disk.seek(partition_one+16)

    # Return to one sector unit
    return address

# Obtain and save the root directory start address for each partition.
def get_Directory_Entry_Analysis_info(disk):
    global partition_start

    # Temporary list of RS , FAT32 values
    RS = []
    FAT32 = []

    for i in range(partition_count):
        
        # RS values are stored as much as 2BYTE from each partition's start address + 14 byte address.
        print(partition_start[i] * 512)
        disk.seek(partition_start[i] * 512)
        disk.read(14)

        for t in range(2):
            RS.append(binascii.hexlify(disk.read(1)).decode())
            disk.tell()

        # FAT32 values are stored as much as 4BYTE from each partition start address + 36 byte address.
        disk.seek(partition_start[i] * 512)
        disk.read(36)

        for t in range(4):
            FAT32.append(binascii.hexlify(disk.read(1)).decode())
            disk.tell()

        # Import values in the form of Little Endian into decimal values using a function.
        RS = get_value(RS)
        FAT32 = get_value(FAT32)

        # Root directory address = partition start address (sector unit) + RS (in decimal) + (FAT32 (decimal) * 2)
        address = (partition_start[i]) + RS + (FAT32 * 2)

        # Save the root directory address of the partition to the list.
        partition_Directory_Entry_Analysis.append(int(address))    

# Obtain information from files from the root directory of each partition. -> Physical data storage address , file extension , file size
def get_file_info(disk,partition_num):

    # A list containing information from the root directory of each partition
    global partition_Directory_Entry_Analysis

    # List of files on all partitions
    global file_extension
    global file_data_address
    global file_data_size

    # Number of files recoverable
    global file_count
    global dir_count
    
    # Since it's sector unit, multiply by 512 to get the actual address byte.
    disk.seek(partition_Directory_Entry_Analysis[partition_num] * 512)

    # List of temporary storage of information in each file
    FILE_EXTENSION = []
    Cluster_H = []
    Cluster_L = []
    FILE_SIZE = []
    
    # Temporary variable for byte movement
    temp = 0
    
    #Delete file is correct
    file_type = binascii.hexlify(disk.read(1))
    
    # Until file attribute value is not 00
    while file_type != b'00':

        # When the file is deleted
        if file_type == b'e5':

            # Go to a location that represents a file property
            disk.read(10)
            Attr = disk.read(1)

            # When a file is a regular file
            if binascii.hexlify(Attr) == b'20':

                # Save file type
                disk.seek(partition_Directory_Entry_Analysis[partition_num] * 512)
                disk.read(temp * 32 + 8)

                # Reads bytes that store extensions
                for i in range(4):
                    ex = binascii.hexlify(disk.read(1)).decode()
                    ex = int(ex,16)

                    # Only numbers, uppercase and lowercase letters that can be extended are allowed.
                    if ex >= 48 and ex <= 57:
                        ex = chr(ex)
                        FILE_EXTENSION.append(ex)
                    elif ex >= 65 and ex <= 90:
                        ex = chr(ex)
                        FILE_EXTENSION.append(ex)
                    elif ex >= 97 and ex <= 122:
                        ex = chr(ex)
                        FILE_EXTENSION.append(ex)

                # Save file extension information to the list.
                FILE_EXTENSION = "".join(FILE_EXTENSION)
                file_extension.append(FILE_EXTENSION)                   

                disk.seek(partition_Directory_Entry_Analysis[partition_num] * 512)
                disk.read(temp * 32 + 20)

                # Finding the Starting Cluster Hi
                for i in range(2):
                    Cluster_H.append(binascii.hexlify(disk.read(1)).decode())

                # Go to Starting Cluster Low
                disk.seek(partition_Directory_Entry_Analysis[partition_num] * 512)
                disk.read(temp * 32 + 26)

                # Finding the Starting Cluster Low
                for i in range(2):
                    Cluster_L.append(binascii.hexlify(disk.read(1)).decode())

                # Obtain the actual starting address (in sectors) of the file.
                FILE_data_start = partition_Directory_Entry_Analysis[partition_num] + (get_value(Cluster_H) + get_value(Cluster_L) - 2) * 8

                # Save the actual data start address to the list.
                file_data_address.append(FILE_data_start)

                # Move the actual size of the file data to where it is stored
                disk.seek(partition_Directory_Entry_Analysis[partition_num] * 512)
                disk.read(temp * 32 + 28)

                # Save File Size
                for i in range(4):
                    FILE_SIZE.append(binascii.hexlify(disk.read(1)).decode())

                #Save the actual size of the data in the file (in bytes).
                file_data_size.append(get_value(FILE_SIZE))

                # Replace the file extension string with the list format again before initializing it.
                FILE_EXTENSION = FILE_EXTENSION.split()

                # Initialize used list to empty space to contain information on the following files:
                del FILE_EXTENSION[:]
                del Cluster_H[:]
                del Cluster_L[:]
                del FILE_SIZE[:]

                if file_data_size[-1] == 0:
                    del file_extension[-1]
                    del file_data_address[-1]
                    del file_data_size[-1]
                else:
                    file_count += 1

            elif binascii.hexlify(Attr) == b'10':

                disk.seek(partition_Directory_Entry_Analysis[partition_num] * 512)
                disk.read(temp * 32 + 20)

                # Finding the Starting Cluster Hi
                for i in range(2):
                    Cluster_H.append(binascii.hexlify(disk.read(1)).decode())

                # Go to Starting Cluster Low
                disk.seek(partition_Directory_Entry_Analysis[partition_num] * 512)
                disk.read(temp * 32 + 26)

                # Finding the Starting Cluster Low
                for i in range(2):
                    Cluster_L.append(binascii.hexlify(disk.read(1)).decode())

                # Obtain the actual starting address (in sectors) of the file.
                DIR_data_start = partition_Directory_Entry_Analysis[partition_num] + (get_value(Cluster_H) + get_value(Cluster_L) - 2) * 8

                # Save the actual data start address to the list.
                dir_data_address.append(DIR_data_start)
                dir_into_partition_num.append(partition_num)
                
                # Initialize used list to empty space to contain information on the following files:
                del Cluster_H[:]
                del Cluster_L[:]

                dir_count += 1

        #If not, transfer to the following file information
        else:
            pass
        
        temp += 1

        # Go to the location where you have the following file information
        disk.seek(partition_Directory_Entry_Analysis[partition_num] * 512)
        disk.read(temp * 32)
        file_type = binascii.hexlify(disk.read(1))

def get_file_info_in_DIR(disk,dir_num,partition_num):

    global partition_Directory_Entry_Analysis
    global dir_data_address
    
    # List of files on all partitions
    global file_extension
    global file_data_address
    global file_data_size

    # Number of files recoverable
    global file_count
    global dir_count

    disk.seek(dir_data_address[dir_num] * 512)

    # List of temporary storage of information in each file
    FILE_EXTENSION = []
    Cluster_H = []
    Cluster_L = []
    FILE_SIZE = []

    # Temporary variable for byte movement
    temp = 0
    
    #Delete file is correct
    file_type = binascii.hexlify(disk.read(1))
    
    # Until file attribute value is not 00
    while file_type != b'00':

        # When the file is deleted
        if file_type == b'e5':
            # 파일 속성을 나타내는 위치로 이동
            disk.read(10)
            Attr = disk.read(1)

            # When a file is a regular file
            if binascii.hexlify(Attr) == b'20':

                # Save file type
                disk.seek(dir_data_address[dir_num] * 512)
                disk.read(temp * 32 + 8)

                # Reads bytes that store extensions
                for i in range(4):
                    ex = binascii.hexlify(disk.read(1)).decode()
                    ex = int(ex,16)

                    # Only numbers, uppercase and lowercase letters that can be extended are allowed.
                    if ex >= 48 and ex <= 57:
                        ex = chr(ex)
                        FILE_EXTENSION.append(ex)
                    elif ex >= 65 and ex <= 90:
                        ex = chr(ex)
                        FILE_EXTENSION.append(ex)
                    elif ex >= 97 and ex <= 122:
                        ex = chr(ex)
                        FILE_EXTENSION.append(ex)

                # Save file extension information to the list.
                FILE_EXTENSION = "".join(FILE_EXTENSION)
                file_extension.append(FILE_EXTENSION)                   

                disk.seek(dir_data_address[dir_num] * 512)
                disk.read(temp * 32 + 20)

                # Finding the Starting Cluster Hi
                for i in range(2):
                    Cluster_H.append(binascii.hexlify(disk.read(1)).decode())

                # Go to Starting Cluster Low
                disk.seek(dir_data_address[dir_num] * 512)
                disk.read(temp * 32 + 26)

                # Finding the Starting Cluster Low
                for i in range(2):
                    Cluster_L.append(binascii.hexlify(disk.read(1)).decode())

                # Obtain the actual starting address (in sectors) of the file.
                FILE_data_start = partition_Directory_Entry_Analysis[partition_num] + (get_value(Cluster_H) + get_value(Cluster_L) - 2) * 8

                # Save the actual data start address to the list.
                file_data_address.append(FILE_data_start)

                # Move the actual size of the file data to where it is stored
                disk.seek(dir_data_address[dir_num] * 512)
                disk.read(temp * 32 + 28)

                # Save File Size
                for i in range(4):
                    FILE_SIZE.append(binascii.hexlify(disk.read(1)).decode())

                #Save the actual size of the data in the file (in bytes).
                file_data_size.append(get_value(FILE_SIZE))

                # Replace the file extension string with the list format again before initializing it.
                FILE_EXTENSION = FILE_EXTENSION.split()

                # Initialize used list to empty space to contain information on the following files:
                del FILE_EXTENSION[:]
                del Cluster_H[:]
                del Cluster_L[:]
                del FILE_SIZE[:]

                file_count += 1

            elif binascii.hexlify(Attr) == b'10':

                disk.seek(dir_data_address[dir_num] * 512)
                disk.read(temp * 32 + 20)

                # Finding the Starting Cluster Hi
                for i in range(2):
                    Cluster_H.append(binascii.hexlify(disk.read(1)).decode())

                # Go to Starting Cluster Low
                disk.seek(dir_data_address[dir_num] * 512)
                disk.read(temp * 32 + 26)

                # Finding the Starting Cluster Low
                for i in range(2):
                    Cluster_L.append(binascii.hexlify(disk.read(1)).decode())

                # Finding the actual starting address (in sectors) of the file.
                DIR_data_start = dir_data_address[dir_num] + (get_value(Cluster_H) + get_value(Cluster_L) - 2) * 8

                # Save the actual data start address to the list.
                dir_data_address.append(DIR_data_start)

                # 파일 실제 데이터의 크기가 저장된 위치로 이동
                disk.seek(dir_data_address[dir_num] * 512)
                disk.read(temp * 32 + 28)

                # Initialize used list to empty space to contain information on the following files:
                del Cluster_H[:]
                del Cluster_L[:]
                    
                dir_count += 1

        #If not, transfer to the following file information
        else:
            pass

        temp += 1

        disk.seek(dir_data_address[dir_num] * 512)
        disk.read(temp * 32)
        file_type = binascii.hexlify(disk.read(1))

# Restore files with information from files obtained.
def File_Recover(disk,dir_path):
    global file_data_address
    global file_data_size
    global file_extension

    global file_count

    # Repeat by number of files
    for i in range(file_count):

        # Set file name to sector number
        output_file=open(dir_path+"//"+str(file_data_address[i])+"."+file_extension[i],"wb")

        # Go to the location that contains actual data for deleted files
        disk.seek(file_data_address[i] * 512)

        # Reads data by the size of the file.
        left_size = file_data_size[i]

        DATA_SEARCH = disk.read(file_data_size[i])
        disk.seek(file_data_address[i] * 512)

        while left_size >512:
            DATA = disk.read(512)
            # 읽어온 데이터를 파일에 써준다.
            output_file.write(DATA)

            left_size -= 512

        if left_size > 0:
            DATA = disk.read(left_size)
            output_file.write(DATA)
        
        print("About the" + str(i + 1) + "file")
        print("Data start sector number : " + str(file_data_address[i]) + "Sector")
        print("File extension : " + file_extension[i])
        print("File Size : " + str(file_data_size[i]) + "Byte\n")
        print()

        output_file.close()
    
    tkinter.messagebox.showinfo("Completion","Recovery completed!")