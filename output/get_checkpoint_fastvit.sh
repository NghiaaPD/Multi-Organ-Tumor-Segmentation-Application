# Download from Google Drive using wget (manual method)
FILEID="1yIp3qh0K8z-ZhmqBQBRaZdbbEU1z1FNh"
FILENAME="fastvit_checkpoint.zip"

# Get confirmation token and download file
CONFIRM=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate \
  "https://docs.google.com/uc?export=download&id=${FILEID}" -O- | \
  sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')

wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=${CONFIRM}&id=${FILEID}" \
     -O ${FILENAME} && rm -rf /tmp/cookies.txt
