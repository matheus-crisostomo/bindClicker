<div align="center">
  <img src="assets/logo.png" alt="BindClicker Logo" width="150"/>
  <h1>BindClicker</h1>
  <p><strong>A modern, open-source macro recording and automation tool.</strong></p>
</div>

---

## 📖 About
BindClicker is a powerful and lightweight application designed to record, edit, and replay keyboard and mouse actions with precision. Built in Python with a sleek modern UI (CustomTkinter), it allows you to automate repetitive tasks effortlessly. 

The application is completely standalone and works natively on Windows, with cross-device script sharing support.

## ✨ Features
- **Real-Time Recording**: Precisely capture mouse clicks and keyboard strokes, including their exact screen coordinates and timing.
- **Smart Playback Engine**: Replay your macros with customizable speed multipliers (0.25x to 4.0x), repeat loops, and a built-in "jitter" function to add randomized human-like delays.
- **Inline Script Editor**: A live table editor that lets you view, add, remove, and reorder actions manually.
- **Dynamic Hotkeys**: Fully customizable global hotkeys with an intuitive "Press any key..." capture system.
- **Shareable Scripts**: Easily export your binds as `.json` files to share with others or back up your workflows.
- **Execution History**: Built-in history panel to keep track of when scripts were run and how many times they looped.

## 🚀 Getting Started

### Using the Executable (No Python Required)
1. Download the latest `BindClicker.exe` from the releases.
2. Double-click to run! The app is fully portable. All data (scripts, logs, settings) will be automatically generated in a `data/` folder next to the executable.

### Running from Source
If you want to run BindClicker from the source code or contribute to its development:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/BindClicker.git
   cd BindClicker
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## 🛠️ Building the Executable
BindClicker comes with a built-in PyInstaller script to generate a single portable `.exe` file.
To build it yourself:
1. Ensure `pyinstaller` and `pillow` are installed.
2. Run the build script:
   ```bash
   python build.py
   ```
3. The standalone executable will be generated in `dist/BindClicker.exe`.

## ⚙️ How it Works
1. **Record**: Press the Record hotkey (Default: `F6`) to start a 3-second countdown. Once it finishes, perform the clicks and keypresses you want to automate. Press `F6` again to stop.
2. **Edit**: Select your new script on the sidebar to view it in the Script Editor. You can delete mistakes or adjust delays.
3. **Play**: Set your preferred speed and repetitions, then press the Execute hotkey (Default: `F7`) to run the macro.
4. **Stop**: Need to abort? Press the Emergency Stop hotkey (Default: `ESC`) to halt execution instantly.

## 📄 License
This project is open-source and available for everyone to use and modify.
