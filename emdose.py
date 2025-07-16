import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

# Global variable to store results
last_results = ""

def calculate():
    global last_results
    radionuclide = radionuclide_var.get()
    source_organ = organ_var.get()

    # Validate time input
    try:
        t_hours = float(time_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Time must be a number.")
        return

    # Phantom type prefix
    phantom_type = phantom_type_var.get()
    if phantom_type == "Adult Male":
        prefix = "am_" + radionuclide.lower()
    elif phantom_type == "Adult Female":
        prefix = "af_" + radionuclide.lower()
    else:
        messagebox.showerror("Selection Error", "Please select a valid phantom type.")
        return

    try:
        with open(f"{prefix}svalue_alpha.json") as f:
            s_alpha = json.load(f)["Svalues"]
        with open(f"{prefix}svalue_beta.json") as f:
            s_beta = json.load(f)["Svalues"]
        with open(f"{prefix}svalue_gamma.json") as f:
            s_gamma = json.load(f)["Svalues"]
        with open(f"{prefix}self_dose_matrix.json") as f:
            self_matrix = json.load(f)["SelfDoseMatrix"][source_organ]
    except Exception as e:
        messagebox.showerror("File Error", f"Problem reading data: {str(e)}")
        return

    # Calculation
    t = t_hours * 3600  # seconds
    A = 1  # MBq
    target_organs = list(self_matrix.keys())

    result_text.delete(1.0, tk.END)
    header = f"EMDOSE Estimated internal dosimetry  ({phantom_type})\n"
    header += f"Radionuclide: {radionuclide}, Source Organ: {source_organ}, Time: {t_hours} hours, Activity: 1 MBq\n\n"
    header += "Organ".ljust(40) + "Total(mGy/MBq)\tAlpha\tBeta\tGamma\n"
    header += "-" * 80 + "\n"
    result_text.insert(tk.END, header)
    last_results = header

    for organ in target_organs:
        try:
            s_a = float(s_alpha.get(source_organ, {}).get(organ, 0.0))
            s_b = float(s_beta.get(source_organ, {}).get(organ, 0.0))
            s_g = float(s_gamma.get(source_organ, {}).get(organ, 0.0))
            self_factor = float(self_matrix[organ])

            # Dose components
            dosea = s_a * t * A * self_factor
            dosea_cross = s_a * t * A * (1 - self_factor)
            doseb = s_b * t * A * self_factor
            doseb_cross = s_b * t * A * (1 - self_factor)
            doseg = s_g * t * A * self_factor
            doseg_cross = s_g * t * A * (1 - self_factor)

            total = dosea + dosea_cross + doseb + doseb_cross + doseg + doseg_cross
            alpha_dose = dosea + dosea_cross
            beta_dose = doseb + doseb_cross
            gamma_dose = doseg + doseg_cross

            line = f"{organ:<40}{total:.4f}\t{alpha_dose:.4f}\t{beta_dose:.4f}\t{gamma_dose:.4f}\n"
            result_text.insert(tk.END, line)
            last_results += line
        except Exception as e:
            line = f"{organ:<28}Error: {e}\n"
            result_text.insert(tk.END, line)
            last_results += line

def save_results():
    global last_results
    if not last_results.strip():
        messagebox.showinfo("Info", "No results to save.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text Files", "*.txt"), ("PDF Files", "*.pdf")])
    if file_path.endswith(".txt"):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(last_results)
        messagebox.showinfo("Success", f"Results saved to {file_path}")
    elif file_path.endswith(".pdf"):
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Courier", size=10)
            for line in last_results.splitlines():
                pdf.cell(200, 5, txt=line, ln=True)
            pdf.output(file_path)
            messagebox.showinfo("Success", f"Results saved to {file_path}")
        except ImportError:
            messagebox.showerror("Missing Library", "Please install fpdf:\n\npip install fpdf")

# ------------------ GUI Setup ------------------
root = tk.Tk()
root.title("EMDOSE Dosimetry (ICRP Phantom)")

# Phantom type selector
tk.Label(root, text="Phantom Type:").grid(row=0, column=0, sticky="e")
phantom_type_var = tk.StringVar()
ttk.Combobox(root, textvariable=phantom_type_var, values=["Adult Male", "Adult Female"]).grid(row=0, column=1)
phantom_type_var.set("Adult Male")

# Radionuclide selector
tk.Label(root, text="Radionuclide:").grid(row=1, column=0, sticky="e")
radionuclide_var = tk.StringVar()
ttk.Combobox(root, textvariable=radionuclide_var, values=["Lu177", "I131", "Ra223"]).grid(row=1, column=1)

# Source organ selector
tk.Label(root, text="Source Organ:").grid(row=2, column=0, sticky="e")
organ_var = tk.StringVar()
source_organs = [
    "Adipose tissue", "Adrenals", "Bone - cortical volume", "Bone - trabecular volume",
    "Brain", "Breast tissue", "Cartilage", "Esophagus wall", "Gallbladder content",
    "Heart content", "Heart wall", "Kidneys", "Liver", "Lungs", "Major blood vessels",
    "Muscle", "Oral mucosa", "Pancreas", "Pituitary gland", "Salivary glands", "Spleen",
    "Stomach content", "Thymus", "Thyroid", "Urinary bladder content"
]
ttk.Combobox(root, textvariable=organ_var, values=source_organs).grid(row=2, column=1)

# Time input
tk.Label(root, text="Time (hours):").grid(row=3, column=0, sticky="e")
time_entry = tk.Entry(root)
time_entry.grid(row=3, column=1)

# Buttons
tk.Button(root, text="Calculate", command=calculate).grid(row=4, column=0, columnspan=2, pady=5)
tk.Button(root, text="Save Results", command=save_results).grid(row=5, column=0, columnspan=2, pady=5)

# Results display
result_text = tk.Text(root, height=30, width=100)
result_text.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

root.mainloop()
