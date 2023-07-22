
import subprocess
import asyncio
import time
import tkinter as tk
from tkinter import filedialog, messagebox

async def check_subdomain(semaphore, subdomain):
    try:
        async with semaphore:
            result = await asyncio.create_subprocess_shell(
                f'ping -c 1 {subdomain}',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            _, stderr = await result.communicate()

            if result.returncode == 0:
                return subdomain, 'Responsive'
            else:
                return subdomain, 'Unresponsive'
    except asyncio.TimeoutError:
        return subdomain, 'Timeout'

def update_progress_label(processed, total, start_time):
    progress = (processed / total) * 100
    elapsed_time = time.time() - start_time
    estimated_time = (elapsed_time / processed) * (total - processed)
    progress_label.config(text=f"Progress: {progress:.2f}% | Estimated Time Remaining: {estimated_time:.2f}s")
    root.update()

async def main(subdomain_file, output_file):
    with open(subdomain_file, 'r') as file:
        subdomains = [line.strip() for line in file]

    total_subdomains = len(subdomains)
    processed_count = 0

    semaphore = asyncio.Semaphore(10)

    tasks = [check_subdomain(semaphore, subdomain) for subdomain in subdomains]
    scan_results = []

    print("\nScanning in progress...")
    progress_label.config(text="Scanning in progress...")
    start_time = time.time()

    for coroutine in asyncio.as_completed(tasks):
        subdomain, status = await coroutine
        scan_results.append([subdomain, status])

        processed_count += 1
        update_progress_label(processed_count, total_subdomains, start_time)

    print("\nScan complete.")
    progress_label.config(text="Scan complete.")
    return scan_results

# GUI Implementation
def browse_input_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    input_file_entry.delete(0, tk.END)
    input_file_entry.insert(0, file_path)

def browse_output_file():
    file_path = filedialog.asksaveasfilename(defaultextension='.html', filetypes=[("HTML Files", "*.html")])
    output_file_entry.delete(0, tk.END)
    output_file_entry.insert(0, file_path)

def start_scan():
    input_file = input_file_entry.get()
    output_file = output_file_entry.get()

    if not input_file or not output_file:
        messagebox.showwarning("Error", "Please select both input and output files.")
        return

    if not output_file.lower().endswith('.html'):
        output_file += '.html'

    try:
        loop = asyncio.get_event_loop()
        scan_results = loop.run_until_complete(main(input_file, output_file))
        loop.close()

        with open(output_file, 'w') as html_file:
            html_file.write('<!DOCTYPE html>\n')
            html_file.write('<html>\n')
            html_file.write('<head>\n')
            html_file.write('<title>Subdomain Scan Results</title>\n')
            html_file.write('</head>\n')
            html_file.write('<body>\n')
            html_file.write('<table border="1">\n')

            html_file.write('<tr>\n')
            html_file.write('<th>Subdomain</th>\n')
            html_file.write('<th>Status</th>\n')
            html_file.write('</tr>\n')

            for subdomain, status in scan_results:
                status_color = 'red' if status == 'Unresponsive' else 'blue'
                html_file.write('<tr>\n')
                html_file.write(f'<td><a href="http://{subdomain}" target="_blank">{subdomain}</a></td>\n')
                html_file.write(f'<td style="color: {status_color};">{status}</td>\n')
                html_file.write('</tr>\n')

            html_file.write('</table>\n')
            html_file.write('</body>\n')
            html_file.write('</html>\n')

        messagebox.showinfo("Scan Complete", f"Scan results saved in {output_file}")
    except FileNotFoundError:
        messagebox.showerror("Error", "Input file not found.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Create the GUI window
root = tk.Tk()
root.title("SubScanX")

# Input File Section
input_file_label = tk.Label(root, text="Enter your subdomain list:")
input_file_label.grid(row=0, column=0, padx=5, pady=5)
input_file_entry = tk.Entry(root, width=50)
input_file_entry.grid(row=0, column=1, padx=5, pady=5)
browse_input_button = tk.Button(root, text="Browse", command=browse_input_file)
browse_input_button.grid(row=0, column=2, padx=5, pady=5)

# Output File Section
output_file_label = tk.Label(root, text="Output File:")
output_file_label.grid(row=1, column=0, padx=5, pady=5)
output_file_entry = tk.Entry(root, width=50)
output_file_entry.grid(row=1, column=1, padx=5, pady=5)
browse_output_button = tk.Button(root, text="Browse", command=browse_output_file)
browse_output_button.grid(row=1, column=2, padx=5, pady=5)

# Start Scan Button
start_scan_button = tk.Button(root, text="Start Scan", command=start_scan)
start_scan_button.grid(row=2, column=1, padx=5, pady=10)

# Progress Label
progress_label = tk.Label(root, text="Ready to start.")
progress_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

root.mainloop()
