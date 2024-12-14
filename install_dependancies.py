import subprocess  
import sys  
  
def install_dependencies():  
   print("Installing dependencies...")  
  
   # Install Python dependencies  
   print("Installing Python dependencies...")  
   subprocess.run(['pip', 'install',  
           'pyautogui',  
           'pytesseract',  
           'requests',  
           'configparser',
           'mss',
           'opencv-python',
           'numpy' 
          ])  
  
   # Provide instructions for installing Tesseract OCR  
   print("Please install Tesseract OCR engine manually:")  
   if sys.platform == 'win32':  
      print("1. Visit the instructions file for more information.")  
   elif sys.platform == 'darwin':  # macOS  
      print("1. Open the Terminal app on your Mac.")  
      print("2. Run the command `brew install tesseract` to install Tesseract OCR using Homebrew.")  
   else:  # Linux  
      print("1. Open the Terminal app on your Linux system.")  
      print("2. Run the command `sudo apt-get install tesseract-ocr` to install Tesseract OCR.")  
  
if __name__ == "__main__":  
   install_dependencies()
