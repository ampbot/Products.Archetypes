import sys
import os.path
import types
import time, random, md5, socket
from inspect import getargs
from types import TupleType, ListType, StringType
from UserDict import UserDict as BaseDict

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from ExtensionClass import ExtensionClass
from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName

import Products.generator.i18n as i18n

try:
    _v_network = socket.gethostbyname(socket.gethostname())
except:
    _v_network = random.random() * 100000000000000000L

def fixSchema(schema):
    """Fix persisted schema from AT < 1.3 (UserDict-based)
    to work with the new fixed order schema."""
    from Products.Archetypes.Schema import Schemata
    if not hasattr(aq_base(schema), '_fields'):
        fields = schema.data.values()
        Schemata.__init__(schema, fields)
        del schema.data
    return schema

def make_uuid(*args):
    t = long(time.time() * 1000)
    r = long(random.random()*100000000000000000L)
    data = str(t)+' '+str(r)+' '+str(_v_network)+' '+str(args)
    data = md5.md5(data).hexdigest()
    return data


_marker = []

def mapply(method, *args, **kw):
    m = method
    if hasattr(m, 'im_func'):
        m = m.im_func
    code = m.func_code
    fn_args = getargs(code)
    call_args = list(args)
    if fn_args[1] is not None and fn_args[2] is not None:
        return method(*args, **kw)
    if fn_args[1] is None:
        if len(call_args) > len(fn_args[0]):
            call_args = call_args[:len(fn_args[0])]
    if len(call_args) < len(fn_args[0]):
        for arg in fn_args[0][len(call_args):]:
            value = kw.get(arg, _marker)
            if value is not _marker:
                call_args.append(value)
                del kw[arg]
    if fn_args[2] is not None:
        return method(*call_args, **kw)
    if fn_args[0]:
        return method(*call_args)
    return method()


def className(klass):
    if type(klass) not in [types.ClassType, ExtensionClass]:
        klass = klass.__class__
    return "%s.%s" % (klass.__module__, klass.__name__)

def productDir():
    module = sys.modules[__name__]
    return os.path.dirname(module.__file__)

def pathFor(path=None, file=None):
    base = productDir()
    if path:
        base = os.path.join(base, path)
    if file:
        base = os.path.join(base, file)

    return base

def capitalize(string):
    if string[0].islower():
        string = string[0].upper() + string[1:]
    return string

def findDict(listofDicts, key, value):
    #Look at a list of dicts for one where key == value
    for d in listofDicts:
        if d.has_key(key):
            if d[key] == value:
                return d
    return None


def basename(path):
    return path[max(path.rfind('\\'), path.rfind('/'))+1:]

def unique(s):
    """Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """
    # taken from ASPN Python Cookbook,
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u



class DisplayList:
    """Static display lists, can look up on
    either side of the dict, and get them in sorted order
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, data=None):
        self._keys = {}
        self._i18n_msgids = {}
        self._values = {}
        self._itor   = []
        self.index = 0
        if data:
            self.fromList(data)

    def __repr__(self):
        return '<DisplayList %s at %s>' % (self[:], id(self))

    def __str__(self):
        return str(self[:])

    def __call__(self):
        return self

    def fromList(self, lst):
        for item in lst:
            if isinstance(item, ListType):
                item = tuple(item)
            self.add(*item)

    def __len__(self):
        return self.index

    def __add__(self, other):
        a = tuple(self.items())
        if hasattr(other, 'items'):
            b = other.items()
        else: #assume a seq
            b = tuple(zip(other, other))

        msgids = self._i18n_msgids
        msgids.update(getattr(other, '_i18n_msgids', {}))

        v = DisplayList(a + b)
        v._i18n_msgids = msgids
        return v

    def index_sort(self, a, b):
        return  a[0] - b[0]

    def add(self, key, value, msgid=None):
        if type(key) is not StringType:
            raise TypeError('DisplayList keys must be strings')
        self.index +=1
        k = (self.index, key)
        v = (self.index, value)

        self._keys[key] = v
        self._values[value] = k
        self._itor.append(key)
        if msgid: self._i18n_msgids[key] = msgid


    def getKey(self, value, default=None):
        """get key"""
        v = self._values.get(value, None)
        if v: return v[1]
        for k, v in self._values.items():
            if repr(value) == repr(k):
                return v[1]
        return default

    def getValue(self, key, default=None):
        "get value"
        if type(key) is not StringType:
            raise TypeError('DisplayList keys must be strings')
        v = self._keys.get(key, None)
        if v: return v[1]
        for k, v in self._keys.items():
            if repr(key) == repr(k):
                return v[1]
        return default

##    def getIndex(self, key):
##        "get index from key"
##        v = self._keys.get(key, None)
##        if v: return v[0]
##        for k, v in self._keys.items():
##            if repr(key) == repr(k):
##                return v[0]
##                
##        return None
##        
##    def getIndexesFromKeys(self, keys):
##        "get indexes from keys (list or not)"
##        list_type = (type(keys) in (ListType, TupleType))
##        
##        if not list_type:
##            v = self._keys.get(keys, None)
##            if v: 
##               return [v[0]]
##            else:
##               return []
##        
##        indexes = []
##        
##        for k in keys:
##            v = self._keys.get(k, None)
##            if v:
##                indexes.append(v[0])
##                
##        return indexes
##        
##    def getKeysFromIndexes(self, indexes):
##        "get keys from indexes (list or not)"
##        list_type = (type(indexes) in (ListType, TupleType))
##        build_indexes = dict([(v[0], k) for k, v in self._keys.items()])
##        
##        if not list_type:
##            if build_indexes.has_key(indexes):
##                return build_indexes[indexes]
##            else:
##                return None
##            
##        keys = []
##        
##        for i in indexes:
##            if build_indexes.has_key(i):
##                keys.append(build_indexes[i])
##                
##        return keys

    def getMsgId(self, key):
        "get i18n msgid"
        if type(key) is not StringType:
            raise TypeError('DisplayList keys must be strings')
        if self._i18n_msgids.has_key(key):
            return self._i18n_msgids[key]
        else:
            return self._keys[key][1]

    def keys(self):
        "keys"
        kl = self._values.values()
        kl.sort(self.index_sort)
        return [k[1] for k in kl]

    def values(self):
        "values"
        vl = self._keys.values()
        vl.sort(self.index_sort)
        return [v[1] for v in vl]

    def items(self):
        """items"""
        keys = self.keys()
        return tuple([(key, self.getValue(key)) for key in keys])

    def sortedByValue(self):
        """return a new display list sorted by value"""
        def _cmp(a, b):
            return cmp(a[1], b[1])
        values = list(self.items())
        values.sort(_cmp)
        return DisplayList(values)

    def sortedByKey(self):
        """return a new display list sorted by key"""
        def _cmp(a, b):
            return cmp(a[0], b[0])
        values = list(self.items())
        values.sort(_cmp)
        return DisplayList(values)

    def __cmp__(self, dest):
        if not isinstance(dest, DisplayList):
            raise TypeError, 'Cant compare DisplayList to %s' % (type(dest))

        return cmp(self.sortedByKey()[:], dest.sortedByKey()[:])

    def __getitem__(self, key):
        #Ok, this is going to pass a number
        #which is index but not easy to get at
        #with the data-struct, fix when we get real
        #itor/generators
        return self._itor[key]

    def __getslice__(self,i1,i2):
        r=[]
        for i in xrange(i1,i2):
            try: r.append((self._itor[i], self.getValue(self._itor[i]),))
            except IndexError: return r
        return DisplayList(r)

    slice=__getslice__

InitializeClass(DisplayList)

class Vocabulary(DisplayList):
    """
    Wrap DisplayMist class and add internationalisation"""
    
    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')
    
    def __init__(self, display_list, instance, i18n_domain):
        self._keys = display_list._keys
        self._i18n_msgids = display_list._i18n_msgids
        self._values = display_list._values
        self._itor   = display_list._itor
        self.index = display_list.index
        self._instance = instance
        self._i18n_domain = i18n_domain
        
    def getValue(self, key, default=None):
        """
        Get i18n value
        """
        if type(key) is not StringType:
            raise TypeError('DisplayList keys must be strings')
        v = self._keys.get(key, None)
        value = default
        if v: 
            value = v[1]
        else:
            for k, v in self._keys.items():
                if repr(key) == repr(k):
                    value = v[1]
                    break
                    
        if self._i18n_domain and self._instance:
            msg = self._i18n_msgids.get(key, None) or value
        
            return i18n.translate(self._i18n_domain, msg,
                                  context=self._instance, default=value)
        else:
            return value

InitializeClass(Vocabulary)

class OrderedDict(BaseDict):
    """A wrapper around dictionary objects that provides an ordering for
       keys() and items()."""

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, dict=None):
        BaseDict.__init__(self, dict)
        if dict is not None:
            self._keys = self.data.keys()
        else:
            self._keys = []

    def __setitem__(self, key, item):
        if not self.data.has_key(key):
            self._keys.append(key)
        return BaseDict.__setitem__(self, key, item)

    def __delitem__(self, key):
        BaseDict.__delitem__(self, key)
        self._keys.remove(key)

    def clear(self):
        BaseDict.clear(self)
        self._keys = []

    def keys(self):
        return self._keys

    def items(self):
        return [(k, self.get(k)) for k in self._keys]

    def reverse(self):
        items = list(self.items())
        items.reverse()
        return items

    def values(self):
        return [self.get(k) for k in self._keys]

    def update(self, dict):
        for k in dict.keys():
            if not self.data.has_key(k):
                self._keys.append(k)
        return BaseDict.update(self, dict)

    def setdefault(self, key, failobj=None):
        if not self.data.has_key(key):
            self._keys.append(key)
        return BaseDict.setdefault(self, key, failobj)

    def popitem(self):
        if not self.data:
            raise KeyError, 'dictionary is empty'
        k = self._keys.pop()
        v = self.data.get(k)
        del self.data[k]
        return (k, v)

InitializeClass(OrderedDict)


def getRelPath(self, ppath):
    """take something with context (self) and a physical path as a
    tuple, return the relative path for the portal"""
    urlTool = getToolByName(self, 'portal_url')
    portal_path = urlTool.getPortalObject().getPhysicalPath()
    ppath = ppath[len(portal_path):]
    return ppath

def getRelURL(self, ppath):
    return '/'.join(getRelPath(self, ppath))

