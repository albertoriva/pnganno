# pnganno
Manage text annotations in PNG files

## Introduction

Pnganno is a Python command-line tool to store text annotations in a PNG file.
This may be useful to store image meta-data, for example to describe how the
image was generated, the command that produced it, or graphical parameters.

Annotations consist of a key (a string shorter than 80 characters) and an
associated text (of any length). Any number of annotations can be added to a PNG
file. The [PNG standard](https://www.w3.org/TR/2003/REC-PNG-20031110/) defines a set of semi-standard keys:

Key           | Meaning
--------------|--------------------------
Title         | Short (one line) title or caption for image
Author        | Name of image's creator
Description   | Description of image (possibly long)
Copyright     | Copyright notice
Creation Time | Time of original image creation
Software      | Software used to create the image
Disclaimer    | Legal disclaimer
Warning       | Warning of nature of content
Source        | Device used to create the image
Comment       | Miscellaneous comment

You are free to use any other key as appropriate for your application.

## Syntax

```python
pnganno.py [options] PNGfile.png
```

where options are:

Option | Description
-------|------------
  -o O | Write output to file O. This will be a PNG file for the -a and -f commands.
  -a A | Add comment A to the PNG file. A should have the form key,text. This option can be repeated on the command line.
  -f F | Add comments reading them from file F. F should be tab-delimited with two columns containing key and text respectively.
  -r R | Retrieve the text associated with one or more keys R. For every key present in the PNG file, the corresponding text is printed to the output. Please note that the text may span more than one line. This option can be repeated on the command line, or multiple keys can be supplied, separated by commas.
  -d D | Delete the text associated with key D.
  -O   | When using -a, -f, or -d, overwrite existing PNG file instead of writing new one.

# Usage

When called with no options, the command prints the list of keys found in the PNG file. For example,
using the PNG file provided in the `example` directory:

```
$ pnganno.py PNGfile.png
url
```

Let's add two more entries, creating a new PNG file:

```
$ pnganno.py -a "source,pnganno documentation" \
             -a "purpose,demonstrate how pnganno wokrs" \
	     -o PNGfile-new.png PNGfile.png
```

Verify that the keys were added:

```
$ pnganno.py PNGfile-new.png
url
source
purpose
```

We made a typo when adding the `purpose` entry, let's fix it overwriting the PNG file:

```
$ pnganno.py -a "purpose,demonstrate how pnganno works" -O PNGfile-new.png
```

Let's retrieve the two comments we added:

```
$ pnganno.py -r purpose,source PNGfile-new.png
#purpose
demonstrate how pnganno works
#source
pnganno documentation
```

An alternative form of the same command:

```
$ pnganno.py -r purpose -r source PNGfile-new.png
#purpose
demonstrate how pnganno works
#source
pnganno documentation
```

Finally, we delete one of the two comments, again overwriting the file,
and we verify that it's gone:

```
$ pnganno.py -d source -O PNGfile-new.png
$ pnganno.py PNGfile-new.png
url
purpose
```

## Credits
(c) 2020, A.Riva, ICBR Bioinformatics Core, University of Florida
