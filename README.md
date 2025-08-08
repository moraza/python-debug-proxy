# Python Web Proxy
This tool is designed to troubleshoot tools that try to connect to unknown URLs so these URLs can be identified. It acts as a web proxy for all process that connect to it.

To enable HTTPS support, run the following command to generate cert.pem and key.pem, and place them in the same folder where proxy.py sits:
```bash
openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem
```
