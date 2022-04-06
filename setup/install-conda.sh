sudo apt-get update --fix-missing
sudo apt-get install -y libgl1-mesa-glx libegl1-mesa \
  libxrandr2 libxrandr2 libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6

wget --quiet https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh -O anaconda.sh
bash anaconda.sh -u
rm anaconda.sh
. ~/anaconda3/bin/activate
conda init
. ~/.bashrc
