screen -XS VirtualizorPanel quit
pkill -f "telegrambot.py"

mkdir /var/tmp/VP-Backup

mv /root/VirtualizorPanel/config.env /var/tmp/VP-Backup/config.env
mv /root/VirtualizorPanel/database.pkl /var/tmp/VP-Backup/database.pkl
rm -rf /root/VirtualizorPanel

apt-get update -y
apt-get upgrade -y

cd
git clone https://github.com/Ashaxer/VirtualizorPanel
cd VirtualizorPanel

apt-get install python3
apt-get install python3-pip
pip install -r requirements.txt

cp /var/tmp/VP-Backup/config.env /root/VirtualizorPanel/config.env
cp /var/tmp/VP-Backup/database.pkl /root/VirtualizorPanel/database.pkl

screen -dmS VirtualizorPanel sh -c 'cd /root/VirtualizorPanel/ && /usr/bin/python3 telegrambot.py'
