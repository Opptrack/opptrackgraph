

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt

#open interpreter
python 
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('maxent_ne_chunker_tab')

sudo apt install texlive-latex-base
sudo apt-get update
sudo apt-get install texlive-latex-extra

sudo apt-get install tesseract-ocr poppler-utils  # if you're on Linux

sudo docker network create   --ipv6   --subnet=fd00:dead:bead::/64   custom_ipv6_net

sudo docker run --rm --net custom_ipv6_net busybox ip -6 addr

sudo docker build -t opptrackgraph .

(venv) oz@Dagon:~/OppTrackGraph$ sudo docker run \
  --rm \
  --net custom_ipv6_net \
  --env-file .env \
  -p 8080:8080 \
opptrackgraph