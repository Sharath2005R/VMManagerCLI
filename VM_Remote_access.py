import subprocess
import shutil
import os
import time

# Vbox executable file
VBoxManage_path = r"" #exe file for vbox

# Predefined ISO path(Not needed)
default_iso_path = r"" #Virtual Machine iso path


# funtion to list all the vm
def list_vms():
    """List all registered virtual machines with numbering."""
    print("\nRegistered Virtual Machines:")
    result = subprocess.run([VBoxManage_path, 'list', 'vms'], capture_output=True, text=True)
    vms = result.stdout.strip().splitlines()
    
    if vms:
        for index, vm in enumerate(vms, start=1):
            print(f"{index}. {vm.split(' ')[0].strip('\"')}")  # Display only the VM name
    else:
        print("No VMs found.")

    return vms

# Function to copy the vm file and paste it in specific folder
def copy_directory(source_dir, destination_dir, vdi_name):
    """Copy the entire directory to the destination and change the UUID of the .vdi file."""
    if os.path.exists(source_dir):
        try:
            # Copy the full directory tree to the destination
            shutil.copytree(source_dir, destination_dir)
            print(f"Directory copied successfully from: {source_dir} to {destination_dir}")

            # Path to the .vdi file in the destination directory
            vdi_path = os.path.join(destination_dir, vdi_name)

            if os.path.exists(vdi_path):
                # Change the UUID of the .vdi file to avoid conflicts
                print(f"Changing UUID for {vdi_name} at {vdi_path}...")
                subprocess.run([VBoxManage_path, 'internalcommands', 'sethduuid', vdi_path])
                print(f"UUID successfully changed for {vdi_name}.")
            else:
                print(f"Error: .vdi file not found at {vdi_path}. UUID change skipped.")
        except FileExistsError:
            print(f"Destination directory already exists at: {destination_dir}")
        except Exception as e:
            print(f"Error copying directory: {e}")
    else:
        print(f"Source directory not found at: {source_dir}")


def enable_vrde(vm_name):
    """Enable VRDE for the specified virtual machine."""
    print(f"Enabling VRDE for VM '{vm_name}'...")
    subprocess.run([VBoxManage_path, 'modifyvm', vm_name, '--vrde', 'on'])
    print(f"VRDE enabled for VM '{vm_name}'.")

def access_vm_vrde(vm_name):
    """Access the VM console using VRDE."""
    enable_vrde(vm_name)
    subprocess.run([VBoxManage_path, 'startvm', vm_name, '--type', 'headless'])
    print(f"VM '{vm_name}' is running with VRDE enabled. Connect using a remote desktop client.")
    
    # Wait for 30 seconds to allow the VM to boot up completely
    time.sleep(30)

    # Now call the function to get and print the IP address
    get_vm_ip(vm_name)


def get_vm_ip(vm_name):
    """Get the IP address of the specified virtual machine."""
    print(f"Retrieving IP address for VM '{vm_name}'...")
    
    # Wait for 30 seconds to ensure the VM is fully booted
    time.sleep(30)  

    result = subprocess.run([VBoxManage_path, 'guestproperty', 'get', vm_name, '/VirtualBox/GuestInfo/Net/0/V4/IP'], capture_output=True, text=True)

    if result.returncode == 0:
        ip_address = result.stdout.strip().split(':')[-1].strip()
        print(f"IP Address of '{vm_name}': {ip_address}")
    else:
        print(f"Failed to retrieve IP address. Error: {result.stderr.strip()}")


def create_vm(vm_name, memory_mb, cpus, vdi_path, network_mode, cloud_init_iso_path):
    """Create a new virtual machine using the provided vdi path and mount cloud-init ISO."""
    
    # Step 1: Create the VM
    subprocess.run([VBoxManage_path, 'createvm', '--name', vm_name, '--register'])
    
    # Step 2: Modify VM settings
    subprocess.run([VBoxManage_path, 'modifyvm', vm_name, '--memory', str(memory_mb), '--cpus', str(cpus), '--ostype', 'Debian_64'])
    
    # Step 3: Add storage controller for HDD
    subprocess.run([VBoxManage_path, 'storagectl', vm_name, '--name', 'SATA Controller', '--add', 'sata', '--controller', 'IntelAhci'])
    
    # Step 4: Attach the VDI as the primary hard disk
    subprocess.run([VBoxManage_path, 'storageattach', vm_name, '--storagectl', 'SATA Controller', '--port', '0', '--device', '0', '--type', 'hdd', '--medium', vdi_path])
    
    # Step 5: Add storage controller for DVD (for mounting cloud-init ISO)
    subprocess.run([VBoxManage_path, 'storagectl', vm_name, '--name', 'IDE Controller', '--add', 'ide'])
    
    # Step 6: Attach the cloud-init ISO (seed.iso)
    subprocess.run([VBoxManage_path, 'storageattach', vm_name, '--storagectl', 'IDE Controller', '--port', '1', '--device', '0', '--type', 'dvddrive', '--medium', cloud_init_iso_path])

    # Step 7: Configure network settings (bridge, NAT, etc.)
    if network_mode == 'bridged':
        print(f"Configuring bridged networking on VM '{vm_name}' with the Wi-Fi adapter...")
        subprocess.run([VBoxManage_path, 'modifyvm', vm_name, '--nic1', 'bridged', '--bridgeadapter1', 'Intel(R) Wi-Fi 6 AX201 160MHz'])
        print(f"Network configured successfully for VM '{vm_name}'.")

    elif network_mode == 'nat':
        print(f"Configuring NAT networking on VM '{vm_name}'...")
        subprocess.run([VBoxManage_path, 'modifyvm', vm_name, '--nic1', 'nat'])
        print(f"NAT configured successfully for VM '{vm_name}'.")

    print(f"VM '{vm_name}' created successfully with cloud-init ISO attached.")


def start_vm(vm_name):
    """Start the specified virtual machine in headless mode."""
    print(f"Starting VM '{vm_name}' in headless mode...")
    subprocess.run([VBoxManage_path, 'startvm', vm_name, '--type', 'headless'])
    print(f"VM '{vm_name}' is starting... Please wait a moment.")

def stop_vm(vm_name):
    """Stop the specified virtual machine."""
    print(f"Stopping VM '{vm_name}'...")
    subprocess.run([VBoxManage_path, 'controlvm', vm_name, 'poweroff'])
    print(f"VM '{vm_name}' has been stopped.")

def delete_vm(vm_name):
    """Delete the specified virtual machine."""
    confirm = input(f"Are you sure you want to delete the VM '{vm_name}'? This action cannot be undone. (yes/no): ").strip().lower()
    if confirm == 'yes':
        subprocess.run([VBoxManage_path, 'unregistervm', vm_name, '--delete'])
        print(f"VM '{vm_name}' has been deleted.")
    else:
        print("VM deletion cancelled.")

def select_vm(vms):
    """Allow user to select a VM based on its index or go back."""
    while True:
        try:
            index = input("Enter the number of the VM you want to select (or 'back' to return): ")
            if index.lower() == 'back':
                return None  # Return None to indicate going back
            index = int(index) - 1
            if 0 <= index < len(vms):
                return vms[index].split(' ')[0].strip('\"')  # Return the VM name only
            else:
                print(f"Please enter a number between 1 and {len(vms)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")



def main_menu():
    """Display the main menu and handle user input."""
    while True:
        # Menu driven
        print("\n--- Virtual Machine Manager ---")
        print("1. List Virtual Machines")
        print("2. Create New Virtual Machine")
        print("3. Start a Virtual Machine")
        print("4. Stop a Virtual Machine")
        print("5. Delete a Virtual Machine")
        print("6. Access VM Console via SSH")  
        print("7. Exit")
        
        choice = input("Select an option (1-7): ")
        
        # 1st choice to list all the vm
        if choice == '1':
            list_vms()
        
        # 2nd choice to create new vm    
        elif choice == '2':
            # User-defined parameters for new VM creation
            vm_name = input("Enter VM name: ")
            memory_mb = input("Enter memory size in MB (e.g., 4096 for 4 GB): ")
            cpus = input("Enter number of CPUs (e.g., 2): ")

            # Select network configuration
            print("Network modes: [1] NAT, [2] Bridged")
            network_choice = input("Choose network mode (1 or 2): ")
            if network_choice == '1':
                network_mode = 'nat'
            elif network_choice == '2':
                network_mode = 'bridged'
            else:
                print("Invalid choice, defaulting to NAT.")
                network_mode = 'nat'

            # Source and destination directory of the vm files
            source_dir = r"" #source VM
            destination_dir = r"".format(vm_name)  # Destination folder for the copied directory
            
            # Copy the full directory
            copy_directory(source_dir, destination_dir,"kali-linux-2024.3-virtualbox-amd64.vdi")
            
            # Path to the copied .vdi file
            vdi_path = os.path.join(destination_dir, "kali-linux-2024.3-virtualbox-amd64.vdi")   # Adjust as per actual .vdi file name

            # Prompt for cloud-init ISO path
            cloud_init_iso_path = r"" #ISO path

            # Check if the .vdi file exists
            if os.path.exists(vdi_path):
                # Create the VM using the copied .vdi file and mount VBoxGuestAdditions ISO
                create_vm(vm_name, memory_mb, cpus, vdi_path, network_mode, cloud_init_iso_path)
                
                # Start the VM immediately after creation
                start_vm(vm_name)

                
            else:
                print(f"Error: .vdi file not found at {vdi_path}. Check the file name or path.")

        # 3rd choice to just start the vm 
        elif choice == '3':
            vms = list_vms()
            if vms:  # Ensure there are VMs to start
                vm_name = select_vm(vms)
                if vm_name:  # Only start if a valid VM name was returned
                    start_vm(vm_name)
                else:
                    print("Returning to main menu...")
                    
        # 4th choice to stop the vm            
        elif choice == '4':
            vms = list_vms()
            if vms:  # Ensure there are VMs to stop
                vm_name = select_vm(vms)
                if vm_name:  # Only stop if a valid VM name was returned
                    stop_vm(vm_name)
                else:
                    print("Returning to main menu...")
                    
        # 5th choice to delete the vm            
        elif choice == '5':
            vms = list_vms()
            if vms:  # Ensure there are VMs to delete
                vm_name = select_vm(vms)
                if vm_name:  # Only delete if a valid VM name was returned
                    delete_vm(vm_name)
                else:
                    print("Returning to main menu...")
                    
        # 6th choice to access vm by ssh            
        elif choice == '6':
            vms = list_vms()
            if vms:  # Ensure there are VMs to access
                vm_name = select_vm(vms)
                if vm_name:  # Only access if a valid VM name was returned
                    access_vm_vrde(vm_name)  # Call the VRDE method
                else:
                    print("Returning to main menu...")
                    
        # 7th choice is to exit menu driven program            
        elif choice == '7':
            print("Exiting Virtual Machine Manager.")
            break
        
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main_menu()
