
git clone https://github.com/POSTECH-CVLab/PyTorch-StudioGAN.git
git clone https://github.com/OmidPoursaeed/Generative_Adversarial_Perturbations.git

git config --global user.email gokkulnath@gmail.com
git config --global user.email Gokkulnath

#pip install -r requirements.txt

# Download Data from Internet Archive ?
#curl -LOs https://archive.org/download/ia-pex/ia && chmod +x ia
#./ia download Imagenet_NAG

#wget https://archive.org/download/Imagenet_NAG/train.zip
#wget https://archive.org/download/Imagenet_NAG/valid.zip
#wget https://archive.org/download/Imagenet_NAG/LOC_val_solution.csv
#wget https://archive.org/download/Imagenet_NAG/LOC_synset_mapping.txt

nohup curl 'https://storage.googleapis.com/kaggle-data-sets/585413/1534162/bundle/archive.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20210123%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20210123T184300Z&X-Goog-Expires=259199&X-Goog-SignedHeaders=host&X-Goog-Signature=6c01fb577d7226fa835049585ccd0a3be2bb3c169dac218abf72c54b426f73e77e5c24fbfc0663d603e6b45a2c776f0644d3861b50e3dc7fe265e03b943a11b028cfff3eb81c0f589876f6ead252eb560a64a4490125b1779e1e5395fbfe5198972c3bae6c50f4055a2068346d149c54100c9162527eadb1b78154094b554fe1dd01de2a26d9ecdf4faa76d56d533477bde7f1b3af693b9ded4d88094ad26eb8991021427cdb263fec4cd51fb02dd2db2e2807dca317792f6ebf8f9cd94347533b838639258791c58605b269348cfc77dcc77ba499d64970215620e568975394209a292de6b530be85b5d847b24c2deefb9316668ac4be8ac74c769e69c8f63f'   -H 'authority: storage.googleapis.com'   -H 'upgrade-insecure-requests: 1'   -H 'dnt: 1'   -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'   -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'   -H 'sec-fetch-site: cross-site'   -H 'sec-fetch-mode: navigate'   -H 'sec-fetch-user: ?1'   -H 'sec-fetch-dest: document'   -H 'referer: https://www.kaggle.com/'   -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' --compressed -o archive.zip &
