# make undo function follow cv2 module
# added ThemedTk for make GUI look more modern
# adjust the algorithm of red line: the red line starts at the middle edge of epro image
# added description
from math import sqrt
import cv2
import tkinter as tk
from tkinter import filedialog, StringVar, PhotoImage, IntVar
from PIL import ImageTk, Image
from io import BytesIO
import win32clipboard
from ttkthemes import ThemedTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


# Variables to track rectangle coordinates
start_x, start_y = -1, -1
start_x_list = []
start_y_list = []
red_line_status = False
end_x, end_y = -1, -1
image_stack = []
epro_status = False
drawing = False
undo_image = None
epro_position = [[],[]]
rectangles = [[], []]  # List to store previous rectangles
threshold = 5
order = ['empty']
key = cv2.waitKey(1) & 0xFF


# Mouse callback function
def draw_rectangle(event, x, y, flags, param):
    global start_x, start_y, end_x, end_y, drawing, undo_image, rectangles, epro_img, epro_status, epro_position, \
        start_y_list,start_x_list, red_line_status, order, image, key

    if event == cv2.EVENT_LBUTTONDOWN:
        red_line_status = False
        drawing = True
        start_x, start_y = x, y
        undo_image = image.copy()


    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            image_temp = undo_image.copy()
            end_x, end_y = x, y
            selected_color = color_var.get()
            fill_color = colors[selected_color]
            outline_color = (0, 0, 0)  # Black outline color
            thickness = 2  # Outline thickness
            image_temp_overlay = image_temp.copy()
            if filled_var.get() == 0:  # Filled rectangle
                cv2.rectangle(image_temp_overlay, (start_x, start_y), (end_x, end_y), fill_color, -1)
                cv2.rectangle(image_temp, (start_x, start_y), (end_x, end_y), outline_color, thickness)
                opacity = 0.5  # Adjust the opacity as desired
                cv2.addWeighted(image_temp_overlay, opacity, image_temp, 1 - opacity, 0, image_temp)
            else:  # Outline only
                cv2.rectangle(image_temp, (start_x, start_y), (end_x, end_y), fill_color, thickness)
            # Draw reference lines for previous rectangles

            cv2.imshow("Image", image_temp)

    elif event == cv2.EVENT_LBUTTONUP:
        red_line_status = False
        drawing = False
        end_x, end_y = x, y
        selected_color = color_var.get()
        fill_color = colors[selected_color]
        outline_color = (0, 0, 0)  # Black outline color
        thickness = 1  # Outline thickness
        overlay = image.copy()

        if abs(start_x - end_x) < 5 and abs(start_y - end_y) < 5:
            epro_img = cv2.imread("epro.jpg")
            epro_img = cv2.resize(epro_img, (int(epro_img.shape[1] * 25 / 100), int(epro_img.shape[0] * 25 / 100)))

            # image[start_x:start_x+epro_img.shape[0],start_y:start_y+epro_img.shape[1]] = epro_img
            image[start_y:start_y + epro_img.shape[0], start_x:start_x + epro_img.shape[1]] = epro_img
            order.append('epro')
            epro_status = True
            epro_position[1].extend((start_x, start_x + epro_img.shape[1]))
            epro_position[0].extend((start_y, start_y + epro_img.shape[0]))
            # adding a line from epro to the position where i click

        else:
            for i in rectangles[0]:
                if abs(i - start_x) < threshold:
                    start_x = i
                if abs(i - end_x) < threshold:
                    end_x = i

            for i in rectangles[1]:
                if abs(i - start_y) < threshold:
                    start_y = i
                if abs(i - end_y) < threshold:
                    end_y = i

            if filled_var.get() == 0:  # Filled rectangle
                cv2.rectangle(overlay, (start_x, start_y), (end_x, end_y), fill_color, -1)
                cv2.rectangle(image, (start_x, start_y), (end_x, end_y), outline_color, thickness)
                opacity = 0.6  # Adjust the opacity as desired
                cv2.addWeighted(overlay, opacity, image, 1 - opacity, 0, image)
            else:
                cv2.rectangle(image, (start_x, start_y), (end_x, end_y), fill_color, 3)
            rectangles[0].extend((start_x, end_x))
            rectangles[1].extend((start_y, end_y))
            order.append('rectangle')
        cv2.imshow("Image", image)
        image_stack.append(image.copy())


    elif event == cv2.EVENT_RBUTTONDOWN and (order[-1] == 'epro' or order[-1] == 'r_line'):
        end_x, end_y = x, y
        start_x_list = epro_position[1][-2:]
        start_y_list = epro_position[0][-2:]

        if abs(start_x_list[0] - end_x) > abs(start_x_list[1] - end_x):
            start_x = start_x_list[1]
        else:
            start_x = start_x_list[0]

        if abs(start_y_list[0] - end_y) > abs(start_y_list[1] - end_y):
            start_y = start_y_list[1]
        else:
            start_y = start_y_list[0]
        if sqrt((end_x-((start_x_list[0]+start_x_list[1])/2))**2 + (end_y-start_y)**2) > \
                sqrt((end_y-((start_y_list[0]+start_y_list[1])/2))**2 + (end_x-start_x)**2):
            start_y = int((start_y_list[0]+start_y_list[1])/2)
        else:
            start_x = int((start_x_list[0]+start_x_list[1])/2)
        cv2.line(image, (start_x, start_y), (end_x, end_y), (0, 0, 255), 1)
        order.append('r_line')
        red_line_status = True
        epro_status = False
        cv2.imshow("Image", image)
        image_stack.append(image.copy())
    elif event == cv2.EVENT_MBUTTONDOWN and image_stack:
        image_stack.pop()
        if order[-1] == 'epro':
            epro_position[0] = epro_position[0][:-2]
            epro_position[1] = epro_position[1][:-2]
            order.pop()
        elif order[-1] == 'r_line':
            epro_status = True
            red_line_status = False
            order.pop()
        elif order[-1] == 'rectangle':
            rectangles[0] = rectangles[0][:-2]
            rectangles[1] = rectangles[1][:-2]
            order.pop()
        else:
            pass

        if image_stack:
            image = image_stack[-1].copy()
        else:
            image = original_image.copy()
        cv2.imshow("Image", image)


def send_to_clipboard(clip_type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()


# Function to save the modified image
def save_image():
    file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg")])
    if file_path:
        cv2.imwrite(file_path, image)
        print("Image saved!")


def copy_image():
    temp_path = "temp_image.jpg"
    cv2.imwrite(temp_path, image)
    image_pil = Image.open(temp_path)
    # image_pil = image_pil.convert("RGB")

    output = BytesIO()
    image_pil.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    send_to_clipboard(win32clipboard.CF_DIB, data)
    print("Image copied and ready to paste!")


# Function to undo the last step
def undo_last_step(event):
    global image, image_stack, rectangles,epro_position,epro_status,red_line_status, order
    if event.state == 12 and image_stack:  # Ctrl + Z and image stack is not empty
        image_stack.pop()
        if order[-1] == 'epro':
            epro_position[0] = epro_position[0][:-2]
            epro_position[1] = epro_position[1][:-2]
            order.pop()
        elif order[-1] == 'r_line':
            epro_status = True
            red_line_status = False
            order.pop()
        elif order[-1] == 'rectangle':
            rectangles[0] = rectangles[0][:-2]
            rectangles[1] = rectangles[1][:-2]
            order.pop()
        else:
            pass

        if image_stack:
            image = image_stack[-1].copy()
        else:
            image = original_image.copy()
        cv2.imshow("Image", image)


# Create a Tkinter window
# window = ThemedTk(theme='Equilux')
# window = tk.Tk()
window = ttk.Window(themename="minty")
window.title("EB FAE Drawing")
window.geometry("450x550")


# Create a canvas to display the image
canvas = tk.Canvas(window, width=400, height=100)
canvas.pack()
logo = Image.open("logo.png")
aspect_ratio = logo.width / logo.height
canvas_width = 400
canvas_height = 100
canvas_ratio = canvas_width / canvas_height

if aspect_ratio > canvas_ratio:
    new_width = canvas_width
    new_height = int(new_width / aspect_ratio)
else:
    new_height = canvas_height
    new_width = int(new_height * aspect_ratio)

# Resize the image
logo = logo.resize((new_width, new_height))
photo = ImageTk.PhotoImage(logo)

# Add the image to the Canvas
canvas.create_image(0, 10, anchor=tk.NW, image=photo)

description = ttk.Label(window, text=
                        'This is a app in purpose of marking E&M drawing \n quicker with the location of CT and Epro.\n'
                        'Here is the instruction: \n1. left click down and up will create a rectangle \n'
                        '   representing the start point and the end point\n2. if the rectangle is less than 5 pixels,'
                        ' an epro \n   image will be pasted on where you clicked first\n3. After an epro pasted, you can right'
                        ' click anywhere\n   to drawing a red line starting from epro image \n4. Undo when you click '
                        'middle button down'


                        )
description.pack()

# Function to open an image file
def open_image():
    global image, original_image, image_stack, rectangles
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    rectangles = [[], []]
    if file_path:
        image = cv2.imread(file_path)
        original_image = image.copy()
        image_stack = [original_image.copy()]

        # Check image size and set the named window accordingly
        if image.shape[0] > window.winfo_screenheight() or image.shape[1] > window.winfo_screenwidth():
            cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
        else:
            cv2.namedWindow("Image", cv2.WINDOW_AUTOSIZE)

        cv2.imshow("Image", image)
        cv2.setMouseCallback("Image", draw_rectangle)


# Button to open an image file
open_button = ttk.Button(window, text="Open Image", command=open_image, bootstyle=(INFO, OUTLINE))
open_button.pack(pady=10)

# Color options for the filled rectangle
colors = {"30A spiderCT": (0, 0, 255), "50A spiderCT": (106, 154, 255), "100A spiderCT": (255, 188, 157),
          "200A spiderCT": (65, 172, 247), "400A spiderCT": (235, 245, 119), "100A EnergyCT": (209, 178, 249),
          "200A EnergyCT": (0, 186, 199), "400A EnergyCT": (188, 245, 181)}

# Dropdown menu for selecting fill color
color_label = ttk.Label(window, text="Fill Color:")
color_label.pack()

color_var = StringVar(window)
color_var.set("30A spiderCT")
color_menu = ttk.OptionMenu(window, color_var,list(colors.keys())[0], *colors.keys(), bootstyle=(INFO, OUTLINE))
color_menu.pack()
# Checkbox for selecting filled rectangle or not
filled_var = IntVar()
filled_checkbox = ttk.Checkbutton(window, text="Only outline", variable=filled_var)
filled_checkbox.pack(pady=5)

# Button to save the modified image
save_button = ttk.Button(window, text="Save Image", command=save_image, bootstyle=(INFO, OUTLINE))
save_button.pack(pady=5)

# Button to copy the modified image
copy_button = ttk.Button(window, text="Copy Image", command=copy_image, bootstyle=(INFO, OUTLINE))
copy_button.pack(pady=5)

# Bind Ctrl + Z to the undo_last_step function
window.bind("<KeyPress>", undo_last_step)
# Run the Tkinter event loop
window.mainloop()

# Close all windows
cv2.destroyAllWindows()