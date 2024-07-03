import tkinter as tk
from tkinter import ttk, messagebox
import requests
import pyautogui
from PIL import Image
import psutil
import schedule
import time
import threading
import cloudinary
import cloudinary.uploader
import cloudinary.api
import pytz
from datetime import datetime, timedelta
import socket

# Cloudinary configuration
cloudinary.config(
    cloud_name='du0vb79mg',
    api_key='653838984145584',
    api_secret='f3V5J_bW3d0pebFOkDtZDv697OU'
)

TOKEN = None
USERNAME = None
USER_ID = None
TASKS = []
STAFF_IN_TIME = None
RUNNING_TASKS = {}
ENDED_TASKS = []
TASK_ID_MAP = {}  # To map task names to their IDs

def login(username, password):
    url = "https://localhost:7045/api/Auth/login"
    data = {"username": username, "password": password}
    try:
        response = requests.post(url, json=data, verify=False)
        if response.status_code == 200:
            response_json = response.json()
            if response_json.get("message") == "Login successful":
                print("Login successful")
                global TOKEN, USERNAME, USER_ID
                TOKEN = response_json.get("token")  # Save the token
                USERNAME = response_json.get("username")
                USER_ID = response_json.get("userId")  # Fetch UserId from response
                print(f"UserId fetched: {USER_ID}")
                return USERNAME, USER_ID  # Return USER_ID along with USERNAME
            else:
                print(f"Unexpected response: {response_json}")
                return None, None
        else:
            print(f"Login failed with status code: {response.status_code}, response: {response.text}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return None, None

def fetch_tasks():
    url = "https://localhost:7045/api/Data/gettasks"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            tasks = response.json()
            for task in tasks:
                TASK_ID_MAP[task['name']] = task['id']
            return tasks
        else:
            print(f"Failed to fetch tasks: {response.status_code}, response: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return []

def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png", quality=20, optimize=True)
    image_url = upload_to_cloudinary("screenshot.png")
    if image_url:
        system_info = get_system_info()
        activity_log = get_activity_log()
        upload_data(image_url, system_info, activity_log)
    else:
        print("Failed to upload screenshot to Cloudinary")

def upload_to_cloudinary(image_path):
    try:
        response = cloudinary.uploader.upload(image_path, upload_preset="ml_default")
        print(f"Cloudinary response: {response}")  # Print the entire response for debugging

        if 'url' in response:
            return response['url']
        else:
            print(f"Error: 'url' not found in the response. Full response: {response}")
            return None
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None

def get_system_info():
    system_info = psutil.virtual_memory()
    system_name = socket.gethostname()  # Get the system name using socket.gethostname()
    return f"System Info: {system_info}, System Name: {system_name}"

def get_activity_log():
    # Implement activity log tracking here
    return "Activity Log"

def upload_data(image_url, system_info, activity_log):
    kolkata_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(kolkata_tz).isoformat()  # Ensure ISO 8601 format
    system_name = socket.gethostname()  # Get the system name using socket.gethostname()

    url = "https://localhost:7045/api/Data/upload"
    data = {
        "ImageUrl": image_url,
        "SystemInfo": system_info,
        "ActivityLog": activity_log,
        "Timestamp": current_time,  # Include the timestamp from the Python code in ISO 8601 format
        "SystemName": system_name,  # Include the system name in the data
        "Username": USERNAME  # Include the username in the data
    }
    try:
        response = requests.post(url, json=data, verify=False)
        if response.status_code == 200:
            print("Data uploaded successfully")
        else:
            print(f"Failed to upload data: {response.status_code}, response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")

def start_scheduled_tasks():
    schedule.every(2).minutes.do(take_screenshot)
    while True:
        schedule.run_pending()
        time.sleep(1)

def on_login_click():
    global TOKEN, USERNAME, USER_ID
    username = username_entry.get()
    password = password_entry.get()
    USERNAME, USER_ID = login(username, password)
    if USERNAME:
        show_task_management_screen(USERNAME, USER_ID)
        threading.Thread(target=start_scheduled_tasks).start()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

def show_task_management_screen(username, user_id):
    for widget in root.winfo_children():
        widget.destroy()

    # Staff in/out and time display section
    staff_buttons_frame = tk.Frame(root, bg="#2c3e50")
    staff_buttons_frame.grid(row=0, column=0, columnspan=5, pady=10)

    staff_in_button = tk.Button(staff_buttons_frame, text="Staff In", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12), command=staff_in)
    staff_in_button.pack(side="left", padx=10)
    staff_out_button = tk.Button(staff_buttons_frame, text="Staff Out", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12), command=staff_out)
    staff_out_button.pack(side="left", padx=10)

    staff_in_time_label = tk.Label(staff_buttons_frame, text="Staff In Time: Not Logged In", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12))
    staff_in_time_label.pack(side="left", padx=10)

    global staff_in_button_reference, staff_in_time_label_reference
    staff_in_button_reference = staff_in_button
    staff_in_time_label_reference = staff_in_time_label

    # Welcome label
    welcome_label = tk.Label(root, text=f"Welcome, {username}!", font=("Helvetica", 16, "bold"), bg="#2c3e50", fg="#ecf0f1")
    welcome_label.grid(row=1, column=0, columnspan=5, pady=20)

    # Fetch tasks from the API
    tasks = fetch_tasks()
    task_names = [task["name"] for task in tasks] + ["Other"]

    # Task input section
    tk.Label(root, text="Task Type:", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12)).grid(row=2, column=0, padx=10)
    task_type_combobox = ttk.Combobox(root, values=task_names, font=("Helvetica", 12))
    task_type_combobox.grid(row=2, column=1, padx=10)
    task_type_combobox.bind("<<ComboboxSelected>>", lambda event: on_task_selected(task_type_combobox, task_type_entry))
    task_type_combobox.set("Select Task Type")  # Set default text

    task_type_entry = tk.Entry(root, font=("Helvetica", 12))
    task_type_entry.grid(row=2, column=2, padx=10)
    task_type_entry.grid_remove()

    tk.Label(root, text="Comment:", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12)).grid(row=3, column=0, padx=10)
    comment_entry = tk.Entry(root, font=("Helvetica", 12))
    comment_entry.grid(row=3, column=1, padx=10)

    tk.Button(root, text="Start Task", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12), command=lambda: start_task(task_type_combobox, task_type_entry, comment_entry)).grid(row=2, column=3, padx=10, rowspan=2)

    # Running task list section
    tk.Label(root, text="Running Tasks", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12)).grid(row=4, column=0, columnspan=5, pady=10)
    running_task_list_frame = tk.Frame(root, bg="#ecf0f1", bd=10)
    running_task_list_frame.grid(row=5, column=0, columnspan=5, padx=10, pady=10)

    running_columns = ("staff_name", "task_type", "comment", "start_time", "working_time", "end_task")
    running_task_list_treeview = ttk.Treeview(running_task_list_frame, columns=running_columns, show="headings", height=10)
    running_task_list_treeview.pack(side="left", fill="both")

    for col in running_columns:
        running_task_list_treeview.heading(col, text=col.replace("_", " ").title())
        running_task_list_treeview.column(col, width=100, anchor='center')

    running_task_list_treeview.column("staff_name", width=150)
    running_task_list_treeview.column("task_type", width=150)
    running_task_list_treeview.column("comment", width=200)
    running_task_list_treeview.column("start_time", width=150)
    running_task_list_treeview.column("working_time", width=150)
    running_task_list_treeview.column("end_task", width=150)

    running_task_listbox_scrollbar = tk.Scrollbar(running_task_list_frame)
    running_task_listbox_scrollbar.pack(side="right", fill="y")
    running_task_list_treeview.config(yscrollcommand=running_task_listbox_scrollbar.set)
    running_task_listbox_scrollbar.config(command=running_task_list_treeview.yview)

    global running_task_list_treeview_reference
    running_task_list_treeview_reference = running_task_list_treeview

    # Ended task list section
    tk.Label(root, text="Ended Tasks", bg="#2c3e50", fg="#ecf0f1", font=("Helvetica", 12)).grid(row=6, column=0, columnspan=5, pady=10)
    ended_task_list_frame = tk.Frame(root, bg="#ecf0f1", bd=10)
    ended_task_list_frame.grid(row=7, column=0, columnspan=5, padx=10, pady=10)

    ended_columns = ("staff_name", "task_type", "comment", "start_time", "working_time")
    ended_task_list_treeview = ttk.Treeview(ended_task_list_frame, columns=ended_columns, show="headings", height=10)
    ended_task_list_treeview.pack(side="left", fill="both")

    for col in ended_columns:
        ended_task_list_treeview.heading(col, text=col.replace("_", " ").title())
        ended_task_list_treeview.column(col, width=100, anchor='center')

    ended_task_list_treeview.column("staff_name", width=150)
    ended_task_list_treeview.column("task_type", width=150)
    ended_task_list_treeview.column("comment", width=200)
    ended_task_list_treeview.column("start_time", width=150)
    ended_task_list_treeview.column("working_time", width=150)

    ended_task_listbox_scrollbar = tk.Scrollbar(ended_task_list_frame)
    ended_task_listbox_scrollbar.pack(side="right", fill="y")
    ended_task_list_treeview.config(yscrollcommand=ended_task_listbox_scrollbar.set)
    ended_task_listbox_scrollbar.config(command=ended_task_list_treeview.yview)

    global ended_task_list_treeview_reference
    ended_task_list_treeview_reference = ended_task_list_treeview

    update_task_list()

def on_task_selected(task_type_combobox, task_type_entry):
    selected_task = task_type_combobox.get()
    if selected_task == "Other":
        task_type_entry.grid()
    else:
        task_type_entry.grid_remove()

def start_task(task_type_combobox, task_type_entry, comment_entry):
    global TASKS
    if STAFF_IN_TIME is None:
        staff_in()
    task_type = task_type_combobox.get()
    if task_type == "Other":
        task_type = task_type_entry.get()
    comment = comment_entry.get()

    task_id = TASK_ID_MAP.get(task_type, 1)  # Get the TaskId for the selected task or default to 1 if not found
    task = {"task_type": task_type, "comment": comment, "start_time": datetime.now(), "task_id": task_id}
    TASKS.append(task)
    save_task(task)

    task_id = len(TASKS) - 1
    start_task_record(task_id)
    task_type_combobox.set("Select Task Type")  # Reset combobox text
    task_type_entry.delete(0, tk.END)
    comment_entry.delete(0, tk.END)
    update_task_list()

def save_task(task):
    url = "https://localhost:7045/api/Data/uploadTaskTimer"
    data = {
        "UserId": USER_ID,  # Use the fetched UserId
        "TaskId": task["task_id"],  # Use the selected TaskId from TASK_ID_MAP
        "TaskComment": task["comment"],
        "StaffInTime": task["start_time"].isoformat(),
        "StaffOutTime": task["start_time"].isoformat()  # This needs to be updated properly later
    }
    try:
        response = requests.post(url, json=data, verify=False)
        if response.status_code == 200:
            print("Task saved successfully")
        else:
            print(f"Failed to save task: {response.status_code}, response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")

def start_task_record(task_id):
    task = TASKS[task_id]
    start_time = task["start_time"]
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    RUNNING_TASKS[task_id] = {
        "staff_name": USERNAME,
        "task_type": task["task_type"],
        "comment": task["comment"],
        "start_time": start_time_str,
        "working_time": "00:00:00"
    }

def end_task(task_id):
    task = RUNNING_TASKS.pop(task_id)
    task["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_time = datetime.strptime(task["start_time"], "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(task["end_time"], "%Y-%m-%d %H:%M:%S")
    task["working_time"] = str(end_time - start_time).split(".")[0]  # Calculate total working time
    ENDED_TASKS.append(task)
    update_task_list()

def update_task_list():
    # Update running tasks
    for task_id, task in RUNNING_TASKS.items():
        if "end_time" not in task:
            start_time = datetime.strptime(task["start_time"], "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            working_time = current_time - start_time
            task["working_time"] = str(working_time).split(".")[0]

    running_task_list_treeview_reference.delete(*running_task_list_treeview_reference.get_children())
    for task_id, task in RUNNING_TASKS.items():
        values = (
            task["staff_name"],
            task["task_type"],
            task["comment"],
            task["start_time"],
            task["working_time"],
            "End Task"  # Add "End Task" button label
        )
        running_task_list_treeview_reference.insert("", tk.END, values=values)
        running_task_list_treeview_reference.set(values=values, tags=(task_id, "end_task"))

    for task_id in RUNNING_TASKS.keys():
        running_task_list_treeview_reference.tag_bind(task_id, "<Double-1>", lambda e, t_id=task_id: end_task(t_id))

    # Update ended tasks
    ended_task_list_treeview_reference.delete(*ended_task_list_treeview_reference.get_children())
    for task in ENDED_TASKS:
        values = (
            task["staff_name"],
            task["task_type"],
            task["comment"],
            task["start_time"],
            task["working_time"]
        )
        ended_task_list_treeview_reference.insert("", tk.END, values=values)

    root.after(1000, update_task_list)

def staff_in():
    global STAFF_IN_TIME
    STAFF_IN_TIME = datetime.now()
    staff_in_time_label_reference.config(text=f"Staff In Time: {STAFF_IN_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    staff_in_button_reference.config(state=tk.DISABLED)
    print(f"Staff in at {STAFF_IN_TIME}")

def staff_out():
    if STAFF_IN_TIME is None:
        print("Staff in time not recorded.")
        return
    
    staff_out_time = datetime.now()
    working_time = staff_out_time - STAFF_IN_TIME
    print(f"Staff out at {staff_out_time}, total working time: {working_time}")

root = tk.Tk()
root.title("Workforce Management System")
root.geometry("900x600")
root.configure(bg="#2c3e50")

# Login screen
login_frame = tk.Frame(root, bg="#2c3e50")
login_frame.pack(pady=20)

username_label = tk.Label(login_frame, text="Username:", font=("Helvetica", 12), bg="#2c3e50", fg="#ecf0f1")
username_label.grid(row=0, column=0, pady=5)
username_entry = tk.Entry(login_frame, font=("Helvetica", 12))
username_entry.grid(row=0, column=1, pady=5)

password_label = tk.Label(login_frame, text="Password:", font=("Helvetica", 12), bg="#2c3e50", fg="#ecf0f1")
password_label.grid(row=1, column=0, pady=5)
password_entry = tk.Entry(login_frame, font=("Helvetica", 12), show="*")
password_entry.grid(row=1, column=1, pady=5)

login_button = tk.Button(login_frame, text="Login", font=("Helvetica", 12), bg="#2c3e50", fg="#ecf0f1", command=on_login_click)
login_button.grid(row=2, column=0, columnspan=2, pady=10)

root.mainloop()
