# pip install kaggle pandas numpy

import os

# kaggle.json must be in ~/.kaggle/kaggle.json (Mac/Linux)
# or C:\Users\<you>\.kaggle\kaggle.json (Windows)
os.system("kaggle datasets download -d nikdavis/steam-store-games -f steam.csv -p ./data --unzip")