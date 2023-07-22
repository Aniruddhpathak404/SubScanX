import subprocess
import asyncio
import time

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

def print_progress(processed, total, start_time):
    progress = (processed / total) * 100
    elapsed_time = time.time() - start_time
    estimated_time = (elapsed_time / processed) * (total - processed)
    print(f"\rProgress: {progress:.2f}% | Estimated Time Remaining: {estimated_time:.2f}s", end='', flush=True)

async def main(subdomain_file, output_file):
    with open(subdomain_file, 'r') as file:
        subdomains = [line.strip() for line in file]

    total_subdomains = len(subdomains)
    processed_count = 0

    # Limiting the concurrency to 10 tasks at a time (adjust as needed)
    semaphore = asyncio.Semaphore(10)

    tasks = [check_subdomain(semaphore, subdomain) for subdomain in subdomains]
    scan_results = []

    print("\nScanning in progress...")
    start_time = time.time()

    for coroutine in asyncio.as_completed(tasks):
        subdomain, status = await coroutine
        scan_results.append([subdomain, status])

        processed_count += 1
        print_progress(processed_count, total_subdomains, start_time)

    print("\nScan complete.")
    return scan_results

if __name__ == '__main__':
    input_file = input("Enter the path to the text file containing subdomains: ")
    output_file = input("Enter the file name to save the scan results in HTML format (e.g., result): ")

    # Ensure that the output_file has the .html extension
    if not output_file.lower().endswith('.html'):
        output_file += '.html'

    try:
        loop = asyncio.get_event_loop()
        scan_results = loop.run_until_complete(main(input_file, output_file))
        loop.close()

        with open(output_file, 'w') as html_file:
            # Write the HTML header and start the table
            html_file.write('<!DOCTYPE html>\n')
            html_file.write('<html>\n')
            html_file.write('<head>\n')
            html_file.write('<title>Subdomain Scan Results</title>\n')
            html_file.write('</head>\n')
            html_file.write('<body>\n')
            html_file.write('<table border="1">\n')  # Adding border for clarity

            # Write the table header
            html_file.write('<tr>\n')
            html_file.write('<th>Subdomain</th>\n')
            html_file.write('<th>Status</th>\n')
            html_file.write('</tr>\n')

            # Write the table rows
            for subdomain, status in scan_results:
                status_color = 'red' if status == 'Unresponsive' else 'blue'  # Set 'Unresponsive' to red, everything else to blue
                html_file.write('<tr>\n')
                html_file.write(f'<td><a href="http://{subdomain}" target="_blank">{subdomain}</a></td>\n')
                html_file.write(f'<td style="color: {status_color};">{status}</td>\n')
                html_file.write('</tr>\n')

            # Close the table and add the HTML footer
            html_file.write('</table>\n')
            html_file.write('</body>\n')
            html_file.write('</html>\n')

        print(f"\nScan results saved in {output_file}")
    except FileNotFoundError:
        print("Error: File not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

