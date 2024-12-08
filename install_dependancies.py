import subprocess  
import sys  
  
def install_dependencies():  
   print("Installing dependencies...")  
    
   # Install Python dependencies  
   print("Installing Python dependencies...")  
   subprocess.run(['pip', 'install', 'pyautogui', 'pytesseract', 'Pillow', 'requests', 'tk', 'configparser', 'pyinstaller', 'json', 'datetime', 'logging', 'io'])  
  
   # Provide instructions for installing Tesseract OCR  
   print("Please install Tesseract OCR engine manually:")  
   if sys.platform == 'win32':  
      print("1. Go to https://github.com/tesseract-ocr/tesseract and download the latest version of Tesseract OCR for Windows.")  
      print("2. Follow the installation instructions to install Tesseract OCR.")  
   elif sys.platform == 'darwin':  # macOS  
      print("1. Open the Terminal app on your Mac.")  
      print("2. Run the command `brew install tesseract` to install Tesseract OCR using Homebrew.")  
   else:  # Linux  
      print("1. Open the Terminal app on your Linux system.")  
      print("2. Run the command `sudo apt-get install tesseract-ocr` to install Tesseract OCR.")  
  
if __name__ == "__main__":  
   install_dependencies()
