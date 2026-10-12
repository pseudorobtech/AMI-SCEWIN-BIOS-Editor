# AMI-SCEWIN-BIOS-Editor

========================================================================
             AMI SCEWIN BIOS EDITOR — QUICK START GUIDE
========================================================================
Author: RobTech
Platform Requirements: Windows 10 / 11 (64-bit Only)
Privilege Context: Administrative Access Required

This visual dashboard tool allows you to safely read, modify, and write 
back AMI firmware configurations using a clean interface instead of typing
complex command-line strings.

------------------------------------------------------------------------
1. CRITICAL FILES SETUP (Do this first!)
------------------------------------------------------------------------
For the program to communicate with your motherboard, you must manually 
place your copy of the core AMI SCEWIN files into the EXACT SAME FOLDER 
where you extracted this tool. 

Your folder MUST look like this before running the application:

  📁 Your Folder Name/
   ├── AMI SCEWIN BIOS Editor - by RobTech.exe (The Editor)
   ├── scewin_64.exe         (The core AMI flash binary)
   └── amifldrv64.sys        (The core AMI ring-0 motherboard driver)

If 'scewin_64.exe' or 'amifldrv64.sys' are missing or located in a 
different folder, the "Read from BIOS" and "Write to BIOS" features will 
refuse to execute.

------------------------------------------------------------------------
2. HOW TO LAUNCH SAFELY
------------------------------------------------------------------------
Because flashing motherboard registers requires direct kernel-level memory 
communication, Windows will block the tool from communicating with your live
hardware unless it has administrative rights.

  1. Right-click on 'AMI SCEWIN BIOS Editor - by RobTech.exe'.
  2. Select "Run as Administrator".
  3. Click "Yes" on the Windows User Account Control (UAC) alert pop-up.

------------------------------------------------------------------------
3. STANDARD WORKFLOW OPERATION
------------------------------------------------------------------------

STEP A: LOAD CURRENT BASELINE
  Click the [Read from BIOS] button on the top bar. This instructs the AMI 
  engine to dump your current active NVRAM settings into two local file maps:
  'BIOSData.txt' and 'BIOSData.db'. The editor will load them automatically.

STEP B: EDIT PARAMS & OVERCLOCKING PARAMETERS
  - Browse settings categories using the side navigation lists or use the 
    top search box to instantly isolate specific voltage or frequency limits.
  - Value translations (Hexadecimal ⇄ Decimal) are performed natively. 
    Type normal numbers inside value boxes; the editor formats them cleanly 
    for the flasher automatically.
  - Any parameter you modify will instantly turn GOLD with an alert badge,
    and a summary grid of your pending changes is built dynamically under 
    the right-most tab header.

STEP C: COMPILE PROPOSED CHANGES
  Click the [Save Changes] button to compile your modifications into a safe 
  local text configuration named 'BIOSData_Modified.txt'.

STEP D: LIVE NVRAM HARDWARE FLASH
  Click the [Write to BIOS] button to push your custom text configuration 
  back onto your live motherboard. A system restart is required afterward 
  to cleanly apply your modifications.

------------------------------------------------------------------------
4. 🚨 CRITICAL VOLTAGE AND SAFE STABILITY disclaimers
------------------------------------------------------------------------
* Changing motherboard values can impact system stability. Never alter 
  unknown parameters or lock massive clock limits blindly.
* Always execute a fresh [Read from BIOS] dump right before any flashing pass
  to ensure your structural HII maps match your current firmware state perfectly.
* Never close the program or shut down power while an active [Write to BIOS] 
  operation cycle is processing.

========================================================================
                   Thank you for utilizing this toolkit!
========================================================================
