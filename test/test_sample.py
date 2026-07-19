import logging
logger = logging.getLogger('foo')

def add(a, b):
    logger.info("hello from test sample file  and add function")
    return a + b

def test_add():
    assert add(2, 3) == 5
    logger.info("This is an info message")
    print("hello from test sample file ")


