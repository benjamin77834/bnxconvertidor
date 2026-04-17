#!/usr/bin/env python
# Example Python 2.7 code for refactoring test
from __future__ import print_function
from __future__ import unicode_literals

def process_data(data):
    print "Processing data..."
    
    # Unicode handling
    name = unicode('Benjamin Garcia')
    
    # Dict operations
    config = {'host': 'localhost', 'port': 3306}
    if config.has_key('host'):
        print "Host found:", config['host']
    
    for key, value in config.iteritems():
        print key, "=", value
    
    # Range
    for i in xrange(100):
        pass
    
    # Exception handling
    try:
        result = 10 / 3
    except Exception, e:
        print "Error:", e
    
    # Input
    user = raw_input("Enter name: ")
    
    # Type checks
    if isinstance(name, basestring):
        print "Is string"
    
    count = long(42)
    return count

if __name__ == "__main__":
    process_data(None)
