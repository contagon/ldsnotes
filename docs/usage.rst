=====
Usage
=====

Basic note grabbing would go something like this::

    from pprint import pprint
    from ldsnotes import Notes
    
    n = Notes("username", "password")

    pprint(n[:10])

LDS Notes using selenium to login in to churchofjesuschrist.org. Basically
a browser opens in the background and logs you in. This can taken ~5 seconds
and is slow to do everytime you need to run your script. Alternatively, you can save
your token and reuse it (they seem to be good for a couple of hours).

I generally do the best of both worlds by saving my token to a file locally::

    try:
        file  = open(".token", 'r')
        token = file.read()
        file.close()
        n = Notes(token=token)
        # try to grab something with token
        n[0]
    except:
        print("Refetching token...")
        n = Notes("username", "password")
        file = open(".token", "w")
        file.write(n.token)
        file.close()

You can also search specifically for what you need::

    notes = n.search(keyword="hope", folder="Studying", annot_type="reference", start=1, stop=100)

See :ref:`API Reference <api>` for more specifics.
