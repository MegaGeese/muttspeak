pip install pystray Pillow pywinstyles pynput json threading requests sv_ttk tkinter pystray

python -m PyInstaller --onefile --noconsole --icon='./icon.ico' --add-data "icon.png:." -n muttspeak .\main.py