import serial
import tkinter as tk
import math
import time
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import sys
from read_serial import ArduinoData
import csv  # Add for CSV saving
from datetime import datetime  # For timestamped filenames

class PullMachineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Exercise Pull Machine Simulator")
        self.root.geometry("900x700")  # Set a larger default window size
        self.root.minsize(600, 500)    # Set a minimum size
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Machine geometry
        self.arm_length = 260  # pixels (was 200)
        self.piston_attach_ratio = 0.5
        self.angle_deg = 45

        # Data for plotting
        self.time_window = 30  # seconds
        self.angle_window = deque(maxlen=5)  # For smoothing
        self.time_window_vals = deque(maxlen=5)
        self.vel_history = deque()
        self.time_history = deque()
        self.pistonlen_window = deque(maxlen=5)  # For smoothing piston length
        self.piston_vel_history = deque()
        self.power_history = deque()
        self.start_time = time.time()

        # Canvas
        self.canvas = tk.Canvas(root, width=500, height=500, bg='white')  # was 400x400
        self.canvas.pack(fill=tk.BOTH, expand=True)  # Make canvas resizable
        self.canvas.bind("<Configure>", self.on_canvas_resize)  # Bind resize event

        self.scaling = 1.0  # Initial scaling factor
        self.base_canvas_size = 500  # Reference size for scaling

        # Controls
        control_frame = tk.Frame(root)
        control_frame.pack(fill=tk.X, expand=False)

        btn_font = ("Arial", 16, "bold")  # Larger font for buttons

        # Use fixed-width font for value labels to prevent shifting
        value_font = ("Courier New", 16, "bold")

        self.angle_label = tk.Label(control_frame, text="Angle α:", font=btn_font, width=10, anchor="e")
        self.angle_label.grid(row=0, column=0, padx=(16,2), pady=4, sticky="e")
        self.angle_value = tk.Label(control_frame, text=f"{self.angle_deg:7.2f}°", font=value_font, width=8, anchor="w")
        self.angle_value.grid(row=0, column=1, padx=(0,16), pady=4, sticky="w")

        self.piston_label = tk.Label(control_frame, text="Piston power:", font=btn_font, width=16, anchor="e")
        self.piston_label.grid(row=0, column=2, padx=(0,2), pady=4, sticky="e")
        self.piston_value = tk.Label(control_frame, text="  0.00 W", font=value_font, width=13, anchor="w")
        self.piston_value.grid(row=0, column=3, padx=(0,16), pady=4, sticky="w")

        self.pressure_label = tk.Label(control_frame, text="Pressure:", font=btn_font, width=10, anchor="e")
        self.pressure_label.grid(row=0, column=4, padx=(0,2), pady=4, sticky="e")
        self.pressure_value = tk.Label(control_frame, text="  0.00 bar", font=value_font, width=13, anchor="w")
        self.pressure_value.grid(row=0, column=5, padx=(0,16), pady=4, sticky="w")

        self.pistonlen_label = tk.Label(control_frame, text="Piston length:", font=btn_font, width=14, anchor="e")
        self.pistonlen_label.grid(row=0, column=6, padx=(0,2), pady=4, sticky="e")
        self.pistonlen_value = tk.Label(control_frame, text="  0.000 m", font=value_font, width=10, anchor="w")
        self.pistonlen_value.grid(row=0, column=7, padx=(0,16), pady=4, sticky="w")

        self.recording = False
        self.recorded_data = []
        self.record_btn = tk.Button(
            control_frame,
            text="Start Recording",
            command=self.toggle_recording,
            font=btn_font,
            padx=16,
            pady=8,
            bg="green",
            fg="white",
            width=14
        )
        self.record_btn.grid(row=0, column=8, padx=(10,10), pady=4, sticky="w")

        # Matplotlib Figure for angle plot
        self.fig, self.ax = plt.subplots(figsize=(4, 2), dpi=100)
        self.ax.set_title("Piston Power over Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Piston Power (W)")
        self.line, = self.ax.plot([], [], color='blue')
        self.ax.set_xlim(0, self.time_window)
        self.ax.set_ylim(-50, 50)  # Adjusted for angular velocity range
        self.fig.tight_layout()

        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # Make plot resizable

        self.ardata = ArduinoData()
        self.ardata.start()

        self.draw_machine()
        self.after_id = None  # Track after callback id
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close
        self.update_from_serial()  # Start serial update loop

    def on_canvas_resize(self, event):
        # Update scaling factor based on the smallest dimension
        size = min(event.width, event.height)
        self.scaling = size / self.base_canvas_size
        self.draw_machine()

    def draw_machine(self):
        self.canvas.delete("all")

        # Get current canvas size and scaling
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        scale = self.scaling

        # Base point (center bottom, scaled)
        pivot_x = int(250 * scale)
        pivot_y = int(420 * scale)

        # Arm length and piston attach ratio, scaled
        arm_length = self.arm_length * scale
        piston_attach_ratio = self.piston_attach_ratio

        # Arm endpoint
        angle_rad = math.radians(self.angle_deg)
        arm_end_x = pivot_x - int(70 * scale) + arm_length * math.cos(angle_rad)
        arm_end_y = pivot_y - arm_length * math.sin(angle_rad)

        # Piston attach point (middle of arm)
        mid_x = pivot_x - int(70 * scale) + arm_length * piston_attach_ratio * math.cos(angle_rad)
        mid_y = pivot_y - arm_length * piston_attach_ratio * math.sin(angle_rad)

        # Draw base
        self.canvas.create_line(
            pivot_x - int(100 * scale), pivot_y,
            pivot_x + int(100 * scale), pivot_y,
            width=int(16 * scale), fill='black'
        )

        # Draw arm
        self.canvas.create_line(
            pivot_x - int(70 * scale), pivot_y,
            arm_end_x, arm_end_y,
            width=int(12 * scale), fill='blue'
        )

        # Draw piston
        self.canvas.create_line(
            pivot_x + int(70 * scale), pivot_y,
            mid_x, mid_y,
            width=int(8 * scale), fill='red'
        )

        # Calculate piston length using law of cosine
        b = 0.522  # meters
        c = 0.6    # meters
        piston_length = math.sqrt(b**2 + c**2 - 2 * b * c * math.cos(angle_rad))

        piston_vel = self.piston_vel_history[-1] if self.piston_vel_history else 0.0
        pressure = self.last_pressure if hasattr(self, 'last_pressure') else 0.0
        power = self.power_history[-1] if self.power_history else 0.0

        # Update value labels (fixed width, so numbers don't shift)
        self.angle_value.config(text=f"{self.angle_deg:7.2f}°")
        self.piston_value.config(text=f"{power:8.2f} W")
        self.pressure_value.config(text=f"{pressure:7.2f} bar")
        self.pistonlen_value.config(text=f"{piston_length:8.3f} m")

    def update_plot(self):
        # Update plot data
        if not self.root.winfo_exists():
            return  # Window destroyed, do not update or schedule again
        if self.time_history:
            t0 = self.time_history[0]
            times = [t - t0 for t in self.time_history]
            self.line.set_data(times, list(self.power_history))
            self.ax.set_xlim(0, max(self.time_window, times[-1] if times else self.time_window))
            # Auto-scale y-axis to fit all data
            if self.power_history:
                min_y = min(self.power_history)
                max_y = max(self.power_history)
                if min_y == max_y:
                    min_y -= 1e-2
                    max_y += 1e-2
                margin = 0.1 * (max_y - min_y)
                self.ax.set_ylim(min_y - margin, max_y + margin)
        else:
            self.line.set_data([], [])
        self.canvas_plot.draw()

    def toggle_recording(self):
        if not self.recording:
            # Start recording
            self.recorded_data = []
            self.recording = True
            self.record_btn.config(text="Stop Recording", bg="red")
        else:
            # Stop recording and save to CSV
            self.recording = False
            self.record_btn.config(text="Start Recording", bg="green")
            if self.recorded_data:
                filename = f"pullmachine_record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                with open(filename, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "angle_deg", "pressure"])
                    writer.writerows(self.recorded_data)

    def update_from_serial(self):
        if not self.root.winfo_exists():
            return
        try:
            angle = self.ardata.get()[0]
            pressure = self.ardata.get()[1]
            angle = angle + 49.78  # Calibration/offset as before
        except Exception:
            angle = self.angle_deg  # fallback to last angle
            pressure = 0.0

        self.last_pressure = pressure  # Store for label update

        now = time.time() - self.start_time

        # Calculate piston length
        b = 0.522
        c = 0.6
        angle_rad = math.radians(angle)
        piston_length = math.sqrt(b**2 + c**2 - 2 * b * c * math.cos(angle_rad))

        self.angle_window.append(angle)
        self.time_window_vals.append(now)
        self.pistonlen_window.append(piston_length)

        # Calculate piston velocity (smoothed)
        if len(self.pistonlen_window) >= 2:
            dt = self.time_window_vals[-1] - self.time_window_vals[0]
            if dt > 0:
                piston_vel = (self.pistonlen_window[-1] - self.pistonlen_window[0]) / dt
            else:
                piston_vel = 0.0
        else:
            piston_vel = 0.0

        # Calculate force: F = (pressure in bar) / 10 * (surface area in mm^2)
        surface_area_mm2 = 1055
        force = (pressure / 10.0) * surface_area_mm2  # Newtons

        # Calculate power: P = F * v
        power = force * piston_vel  # Watts

        self.angle_deg = angle  # For drawing

        # Record power and time for plotting
        self.time_history.append(now)
        self.piston_vel_history.append(piston_vel)
        self.power_history.append(power)
        # Remove old data
        while self.time_history and now - self.time_history[0] > self.time_window:
            self.time_history.popleft()
            self.piston_vel_history.popleft()
            self.power_history.popleft()

        # Data recording
        if self.recording:
            self.recorded_data.append([now, angle, pressure])

        self.draw_machine()
        self.update_plot()
        self.after_id = self.root.after(50, self.update_from_serial)  # 0.1s

    def calc_force(self, angle, pressure):
        # angle in degrees, pressure in bar
        return 0.0

    def on_close(self):
        # Cancel scheduled update_plot callback if it exists
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        try:
            self.ardata.stop()
        except Exception:
            pass
        self.root.destroy()
        sys.exit(0)  # Ensure process exits

if __name__ == '__main__':
    # Run the app
    root = tk.Tk()
    app = PullMachineApp(root)
    root.mainloop()
