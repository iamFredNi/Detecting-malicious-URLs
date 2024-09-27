# Detecting-malicious-URLs

# Building a web application honeypot 

To detect URL-based attacks (such as malicious URLs, phishing attempts, or directory traversal attacks) in a honeypot, we can focus on deploying a web application honeypot that emulates vulnerable web services and captures incoming HTTP requests. The idea is to monitor and log all URL requests sent by attackers, which often contain attack vectors like SQL injection, cross-site scripting (XSS), or path traversal attempts

We will install a virtual machine on the host machine to make sure that all processes are isolated from the host and then using docker we will set up multiples containers which will act as honeypot

