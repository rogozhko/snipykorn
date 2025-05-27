import os
import PyInstaller.__main__

icon_path = os.path.abspath("icons/asterisk.ico")
script_path = os.path.abspath("snipykorn.py")
style_path = os.path.abspath("style.qss")

PyInstaller.__main__.run([
    script_path,
    '--clean',
    '--noconfirm',
    f'--icon={icon_path}',
    f'--add-data={icon_path}:icons',
    f'--add-data={style_path}:.',
    '--onefile',
    '--noconsole',
    '--name=snipykorn',
])
