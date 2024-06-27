apt-get update -y
apt-get upgrade -y
cd
git clone https://github.com/Ashaxer/VirtualizorPanel
cd VirtualizorPanel
apt-get install python3
apt-get install python3-pip
pip install -r requirements.txt

while [[ -z "$tk" ]]; do
    echo "Bot token: "
    read -r tk
    if [[ $tk == $'\0' ]]; then
        echo "Invalid input. Token cannot be empty."
        unset tk
    fi
done

while [[ -z "$px" ]]; do
    echo "Proxy (optional): "
    read -r px
    break
done


while [[ -z "$crontabs" ]]; do
    echo "Would you like to cereate a cronjob task on every reboot? [y/n] : "
    read -r crontabs
    if [[ $crontabs == $'\0' ]]; then
        echo "Invalid input. Please choose y or n."
        unset crontabs
    elif [[ ! $crontabs =~ ^[yn]$ ]]; then
        echo "${crontabs} is not a valid option. Please choose y or n."
        unset crontabs
    fi
done

cat > "/root/VirtualizorPanel/config.env" <<EOL
TELEGRAM_BOT_TOKEN = ${tk}
TELEGRAM_PROXY = ${px}
# EXAMPLE SOCKS5 PROXY: socks5://127.0.0.1:2080
# EXAMPLE HTTP PROXY:   http://127.0.0.1:2081
EOL

if [[ "$crontabs" == "y" ]]; then
    # create crontabs
    { crontab -l -u root; echo "@reboot /bin/bash screen -dmS VirtualizorPanel sh -c 'cd /root/VirtualizorPanel/ && /usr/bin/python3 telegrambot.py' >/dev/null 2>&1"; } | crontab -u root -
fi

screen -dmS VirtualizorPanel sh -c 'cd /root/VirtualizorPanel/ && /usr/bin/python3 telegrambot.py'
