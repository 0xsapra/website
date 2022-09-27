---
title: "Java challs - 0CTF 2022"
date: 2022-09-27 13:37:31
description: Java challs - 0CTF 2022
---

I played 0ctf with Super Guesser and mainly focused on 4 web challs out of which I was able to solve 2 of them but couldnt solve the other 2 JAVA challs, so I thought this could be a good time to solve the leftover challs and learn JAVA alongside. This is writeup of 2 JAVA challs from 0ctf namely
1. hessian-onlyJdk 
2. 3rm1

## hessian-onlyJdk

### Introduction & Setup

We were given a java application [Source code with docker attached](/website/assets/source/0ctf-hessian-onlyJdk) which takes user input as POST body and uses the `hessian` Library to parse the POST Input. The Vulnerability was straight forward to discover from the source : `Index.java`
```java
try {
    final InputStream is = t.getRequestBody(); // `is` is POST body
    final Hessian2Input input = new Hessian2Input(is); 
    input.readObject();
}
catch (Exception e) {
    e.printStackTrace();
    response = "oops! something is wrong";
}
```

here, `input.readObject()` is vulnerable to Insecure deserialization and our goal was to find exploit(Java Gadget chain), send it as POST body and achieve RCE. We can try to use gadget chains from ysoserial and other places but none worked, so we will have to create our own gadget chain now.


### Learning JAVA to find Gadget chain

First step was to understand how JAVA deserialization works. I came accorss this nice talk from [blackhat](https://www.youtube.com/watch?v=wPbW6zQ52w8)

The basic idea of deserialization is follows:

1. The code `input.readObject()` means, whatever `Object` we send in the POST body, it will call `readObject` method of it and we as attacker wanna make sure we achive rce when code calls this method. 
Now we cannot send any object ofcourse, the Object we are sending should exist in classPath of the running code. ClassPath is nothing but list of available classes. 

Example, suppose there is a class myClass.java somewhere in the code like this

```java

import java.io.ObjectInputStream;
import java.io.IOException;
import java.io.Serializable;

public class StartVuln {
    Vulnclass m;

    public void readObj(ObjectInputStream s) {
        try {
            m = (Vulnclass) s.readObject();
            m.hax();
        }catch (Exception e) {
            System.out.println(e);
        }
    }
}

public class Vulnclass implements Serializable {

    String cmd = "whoami";
    public void hax() throws IOException {
        System.out.println("Executing" + this.cmd.toString());
        System.out.println(Runtime.getRuntime().exec(this.cmd));
    }
}
```

Now if the main program either belongs to same package or this class included while running the JAVA application, we should be able to access this Class, otherwise we wont be able to access it. Lets say this class is included in classpath while runing the program like:

```bash
$ java -classpath=/path/to/above.jar -jar main.jar
```

we can create a payload like below to get RCE

```kotlin

package com.test;

import Vulnclass
import StartVuln
import org.joor.Reflect
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.ObjectInputStream
import java.io.ObjectOutputStream


fun main(args: Array<String>) {
    println("Start")

    var gadget = createGadget() // This is the ain gadget

    // Rest of the code below
    // is just wrapper to convert the object to `objectInputStream`

    var baos = ByteArrayOutputStream();
    var oos = ObjectOutputStream(baos);

    oos.writeObject(gadget);

    oos.flush();
    oos.close();

    var byteArrayInputStream = ByteArrayInputStream(baos.toByteArray());
    var objectInputStream = ObjectInputStream(byteArrayInputStream);


    // Vulnerablity exploit start here
    StartVuln().readObj(objectInputStream);

}

fun createGadget() : Any {
    return Reflect.onClass("Vulnclass").create().set("cmd", "open /").get();
}
```

Since `Vulnclass` has Serialiable implemented, we should be able to serialize this class. When any code runs `readobject` on it, the code should be able to recover the Object of this class with instance variables(public/private) set to what we wanted it to be.


### Finding Gadget chain to exploit Hessian Library

As seen above, now we know how to create Gadget chain , next step is to find which code to look the Gadget chain at. Like I said , all the `Serializable` class's accessible to the application are possible victim, this includes

1. Entire JAVA JDK
2. Classe's in classpath's included while running app (libraries, jar files etc.)

The application above uses quite few libraries and JDK version 1.8(also known as [JDK 8](https://github.com/frohoff/jdk8u-jdk/))

## 3rm1