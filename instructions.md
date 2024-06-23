# Server side test
python3 ./dccnet-xfer.py -s 51556 server_input.in server_output.out

# Client side test
python3 ./dccnet-xfer.py -c localhost:51556 client_input.in client_output.out
