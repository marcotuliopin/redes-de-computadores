# Server side test
python3 ./dccnet-xfer.py -s 51556 server_input.txt server_output.txt

# Client side test
python3 ./dccnet-xfer.py -c localhost:51556 client_input.txt client_output.txt
