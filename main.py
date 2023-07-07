import customtkinter
from tkinter import filedialog, Toplevel

from typing import Optional

import usb
from pyfu_usb import download, _get_dfu_devices

# VID/PID
__VID = 0x0483
__PID = 0xdf11
__LOAD_ADDR = 0x8000000
__INTERFACE_DFLT = 0

sw_filename = ""


def get_devices_list(vid: Optional[int] = None, pid: Optional[int] = None) -> []:
    devices_list = []

    for device in list(usb.core.find(find_all=True, idProduct=22315)):
        dev_name = "Keyboard: Bus {} Device {:03d}: ID {:04x}:{:04x}".format(
            device.bus, device.address, device.idVendor, device.idProduct
        )
        devices_list.append(dev_name)

    for device in _get_dfu_devices(vid=vid, pid=pid):
        dev_name = "Keyboard DFU: Bus {} Device {:03d}: ID {:04x}:{:04x}".format(
            device.bus, device.address, device.idVendor, device.idProduct
        )
        devices_list.append(dev_name)

    return devices_list


def download_bin(file_path) -> str:
    # Download file to DFU device
    print(file_path)
    try:
        if file_path:
            download(
                file_path,
                interface=__INTERFACE_DFLT,
                vid=__VID,
                pid=__PID,
                address=__LOAD_ADDR,
            )
        else:
            return "Failed. No such file or directory"
    except (
            RuntimeError,
            ValueError,
            FileNotFoundError,
            IsADirectoryError,
            usb.core.USBError,
    ) as err:
        return "An error occurred during the flashing"

    return "Success!"


def create_popup_window(title: str, geometry: str):
    popup = Toplevel(root)
    popup.title(title)

    # Use the same color as main window
    popup.configure(bg='#212121')
    popup.geometry(geometry)
    popup.resizable(False, False)
    # Calculate the coordinates to position the popup in the center of the main window
    root.update_idletasks()
    main_x = root.winfo_rootx()
    main_y = root.winfo_rooty()
    main_width = root.winfo_width()
    main_height = root.winfo_height()
    popup_width = int(geometry.split("x")[0])
    popup_height = int(geometry.split("x")[1])
    popup_x = main_x + (main_width - popup_width) // 2
    popup_y = main_y + (main_height - popup_height) // 2
    popup.geometry(f"+{popup_x}+{popup_y}")
    popup.transient(root)
    popup.grab_set()
    popup.focus_set()

    return popup


def add_message_label(popup, text: str, pady=1, padx=1, wraplength=250):
    message_label = customtkinter.CTkLabel(master=popup, text=text, justify="left", wraplength=wraplength)
    message_label.pack(pady=pady, padx=padx)


def add_filename_label(popup, text: str, pady=1, padx=1, wraplength=250):
    filename_label = customtkinter.CTkLabel(master=popup, text=text, justify="left", wraplength=wraplength)
    filename_label.pack(pady=pady, padx=padx)


def add_warning_label(popup, text: str, pady=1, padx=1):
    warning_label = customtkinter.CTkLabel(master=popup, text=text, justify="left")
    warning_label.pack(pady=pady, padx=padx)


def add_yes_button(popup, text: str, width: int, pady=5, padx=40):
    yes_button = customtkinter.CTkButton(master=popup, text=text, command=lambda: do_flashing(popup), width=width)
    yes_button.pack(side="left", pady=pady, padx=padx)


def add_no_button(popup, text: str, width: int, pady=5, padx=10):
    no_button = customtkinter.CTkButton(master=popup, text=text, command=popup.destroy, width=width)
    no_button.pack(side="left", pady=pady, padx=padx)


def add_exit_button(popup, text: str, pady=20, padx=40):
    exit_button = customtkinter.CTkButton(master=popup, text=text, command=popup.destroy)
    exit_button.pack(pady=pady, padx=padx)


def make_download_popup(title: str, geometry: str):
    popup = create_popup_window(title, geometry)

    if sw_filename:
        add_message_label(popup, "Selected firmware to update:")
        add_filename_label(popup, sw_filename)
        add_warning_label(popup, "Are you sure?")

        add_yes_button(popup, "Yes", width=60)
        add_no_button(popup, "No", width=60)
    else:
        add_message_label(popup, "File is not selected", pady=15)
        add_exit_button(popup, "Exit", pady=5)


def flash_sw():
    make_download_popup(title="Firmware update", geometry="250x150")


def make_download_updating_popup(title: str, geometry: str):
    popup = create_popup_window(title, geometry)

    add_message_label(popup, "Firmware update in progress...")

    return popup


def make_download_done_popup(in_progress_popup, title: str, geometry: str, result_str: str):
    in_progress_popup.destroy()
    popup = create_popup_window(title, geometry)

    add_message_label(popup, "Firmware update finished!")
    add_message_label(popup, "Result: " + result_str)

    no_button = customtkinter.CTkButton(master=popup, text="OK", command=popup.destroy)
    no_button.pack(pady=5, padx=10)

    return popup


def do_flashing(popup):
    global sw_filename
    upd_popup = make_download_updating_popup(title="Firmware update", geometry="250x100")
    result_str = download_bin(sw_filename)
    make_download_done_popup(upd_popup, title="Firmware update", geometry="250x100", result_str=result_str)
    popup.destroy()


def dev_list():
    devices = get_devices_list()

    if devices:
        device_list = "\n".join(devices)
        message = device_list
    else:
        message = "No devices found."

    popup = create_popup_window("Devices list", "250x100")

    add_message_label(popup, message)
    add_exit_button(popup, "Ok")


def is_valid_filename(filename):
    return filename.lower().endswith('.bin') \
        or filename.lower().endswith('.hex')


def browse_files():
    global sw_filename
    file_path = filedialog.askopenfilename(
        initialdir="/",
        title="Select a File",
        filetypes=(("Device firmware", "*.bin *.hex"),)
    )

    if file_path and is_valid_filename(file_path):
        sw_filename = file_path


def firmware_update_popup(title: str, geometry: str):
    popup = create_popup_window(title, geometry)

    browse_button = customtkinter.CTkButton(master=popup, text="Browse a file", command=browse_files)
    browse_button.pack(pady=12, padx=10)

    flash_button = customtkinter.CTkButton(master=popup, text="Flash device", command=flash_sw)
    flash_button.pack(pady=12, padx=10)

    exit_button = customtkinter.CTkButton(master=popup, text="Exit", command=popup.destroy)
    exit_button.pack(pady=12, padx=10)


def update_sw():
    firmware_update_popup(title="Update Firmware", geometry="250x150")


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

root = customtkinter.CTk()
root.title("Keyboard SW-flasher")

# Calculate the coordinates to position the window in the middle of the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 250
window_height = 200
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

frame = customtkinter.CTkFrame(master=root)
frame.pack(pady=10, padx=10, fill="both", expand="True")

buttons_pad_y = 14
buttons_pad_x = 10

list_button = customtkinter.CTkButton(master=frame, text="List devices", command=dev_list)
list_button.pack(pady=buttons_pad_y, padx=buttons_pad_x)

download_button = customtkinter.CTkButton(master=frame, text="Update Firmware", command=update_sw)
download_button.pack(pady=buttons_pad_y, padx=buttons_pad_x)

exit_button = customtkinter.CTkButton(master=frame, text="Exit", command=root.destroy)
exit_button.pack(pady=buttons_pad_y, padx=buttons_pad_x)

root.mainloop()
