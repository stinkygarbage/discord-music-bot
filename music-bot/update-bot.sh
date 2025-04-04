#!/bin/bash

cd /root/music-bot || exit
git pull origin master
pip3 install -r requirements.txt
systemctl restart music-bot
echo "✅ Bot updated and restarted."
