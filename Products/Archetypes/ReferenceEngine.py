from AccessControl import ClassSecurityInfo
from Products.ZCatalog.ZCatalog import ZCatalog

from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import UniqueObject
#from Products.BTree2Folder.BTree2Folder import BTree2Folder

from debug import log, log_exc

from interfaces.referenceable import IReferenceable
from utils import unique, make_uuid
from types import StringType, UnicodeType
from config import UID_CATALOG, REFERENCE_CATALOG, UUID_ATTR
from exceptions import ReferenceException

from Globals import InitializeClass


STRING_TYPES = (StringType, UnicodeType)

class Reference(SimpleItem):
    def __init__(self, id, sid, tid, relationship, **kwargs):
        self.id = id
        self.sourceUID = sid
        self.targetUID = tid
        self.relationship = relationship
        self.__dict__.update(kwargs)

    def __repr__(self):
        return "<Reference sid:%s tid:%s rel:%s>" %(self.sourceUID, self.targetUID, self.relationship)
    
        
    ###
    # Convience methods
    def getSourceObject(self):
        tool = getToolByName(self, UID_CATALOG)
        brains = tool(UID=self.sourceUID)
        return brains[0].getObject()

    def getTargetObject(self):
        tool = getToolByName(self, UID_CATALOG)
        brains = tool(UID=self.targetUID)
        return brains[0].getObject()

    ###
    # Catalog support
    def targetId(self):
        target = self.getTargetObject()
        return target.getId()
    
    def targetTitle(self):
        target = self.getTargetObject()
        return target.Title()
    
    ###
    # Policy hooks, subclass away
    def addHook(self, tool, sourceObject=None, targetObject=None):
        #to reject the reference being added raise a ReferenceException
        pass
    
    def delHook(self, tool, sourceObject=None, targetObject=None):
        #to reject the delete raise a ReferenceException
        pass

        
        

##class ReferenceCatalog(UniqueObject, BTree2Folder, ZCatalog):
class ReferenceCatalog(UniqueObject, ZCatalog):
    id = REFERENCE_CATALOG
    security = ClassSecurityInfo()
    
    ###
    ## Public API
    def addReference(self, source, target, relationship=None, referenceObject=None, **kwargs):        
        sID, sobj = self._uidFor(source)
        tID, tobj = self._uidFor(target)

        brains = self._queryFor(sID, tID, relationship)
        if brains:
            #we want to update the existing reference
            #XXX we might need to being a subtransaction here to
            #    do this properly, and close it later
            existingId = brains[0].getObject().id
            self._delObject(existingId)

        rID = make_uuid(sID, tID)
        rID = "ref_%s" % rID
        if not referenceObject:
            referenceObject = Reference(rID, sID, tID, relationship, **kwargs)

        try:
            referenceObject.addHook(self, sobj, tobj)
        except ReferenceException:
            pass
        else:
            self._setObject(rID, referenceObject)
            referenceObject = getattr(self, rID)
            # XXX should second arg be rID or a pretty name, lets try a name
            self.catalog_object(referenceObject, rID)

    def deleteReference(self, source, target, relationship=None):
        sID, sobj = self._uidFor(source)
        tID, tobj = self._uidFor(target)

        brains = self._queryFor(sID, tID, relationship)
        if brains:
            self._deleteReference(brains[0])

    def deleteReferences(self, object, relationship=None):
        """delete all the references held by an object"""
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(sid=sID, relationship=relationship)
        if brains:
            [self._deleteReference(b) for b in brains]
            
    def getReferences(self, object, relationship=None):
        """return a collection of reference objects"""
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(sid=sID, relationship=relationship)
        return self._resolveBrains(brains)

    def getBackReferences(self, object, relationship=None):
        """return a collection of reference objects"""
        # Back refs would be anything that target this object
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(tid=sID, relationship=relationship)
        return self._resolveBrains(brains)

    def hasRelationshipTo(self, source, target, relationship):
        sID, sobj = self._uidFor(source)
        tID, tobj = self._uidFor(target)

        brains = self._queryFor(sID, tID, relationship)
        result = False
        if brains:
            referenceObject = brains[0].getObject()
            result = True

        return result

    def getRelationships(self, object):
        """Get all relationship types this object has to other objects"""
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(sid=sID)
        res = {}
        for b in brains:
            res[b.relationship]=1

        return res.keys()
        

    def isReferenceable(self, object):
        return IReferenceable.isImplementedBy(object) or hasattr(object, 'isReferenceable')

    def reference_url(self, object):
        """return a url to an object that will resolve by reference"""
        sID, sobj = self._uidFor(object)
        return "%s/lookupObject?uuid=%s" % (self.absolute_url(), sID)
    
    def lookupObject(self, uuid):
        """Lookup an object by its uuid"""
        return self._objectByUUID(uuid)


    #####
    ## Protected
    ## XXX: do security
    def registerObject(self, object):
        self._uidFor(object)

    def unregisterObject(self, object):
        self.deleteReferences(object)
        
        
    ######
    ## Private/Internal
    def _objectByUUID(self, uuid):
        tool = getToolByName(self, UID_CATALOG)
        brains = tool(UID=uuid)
        return brains[0].getObject()
        
    def _queryFor(self, sid=None, tid=None, relationship=None, merge=1):
        """query reference catalog for object matching the info we are
        given, returns brains"""

        q = {}
        if sid: q['sourceUID'] = sid
        if tid: q['targetUID'] = tid
        if relationship: q['relationship'] = relationship
        brains = self.search(q, merge=merge) 
        return brains
             
            
    def _uidFor(self, object):
        # We should really check for the interface but I have an idea
        # about simple annotated objects I want to play out
        if type(object) not in STRING_TYPES:
            object = object.aq_base
            if not self.isReferenceable(object):
                raise ReferenceException
            
            if not hasattr(object, UUID_ATTR):
                uuid = self._getUUIDFor(object)
            else:
                uuid = getattr(object, UUID_ATTR)
        else:
            uuid = object
            #and we look up the object
            uid_catalog = getToolByName(self, UID_CATALOG)
            brains = uid_catalog(UUID=uuid)
            object = brains[0].getObject()

        return uuid, object
    
    def _getUUIDFor(self, object):
        """generate and attach a new uid to the object returning it"""
        uuid = make_uuid(object.title_and_id())
        setattr(object, UUID_ATTR, uuid)
        #uid_catalog = getToolByName(self, UID_CATALOG)
        #uid_catalog.catalog_object(object, uuid)
        return uuid
    
    def _deleteReference(self, brain):
        referenceObject = brain.getObject()
        try:
            referenceObject.delHook(self, referenceObject.getSourceObject(), referenceObject.getTargetObject())
        except ReferenceException:
            pass
        else:
            self._delObject(referenceObject.getId())

    def _resolveBrains(self, brains):
        objects = None
        if brains:
            objects = [b.getObject() for b in brains]
            objects = [b for b in objects if b]
        return objects

def manage_addReferenceCatalog(self, id, title,
                               vocab_id=None, # Deprecated
                               REQUEST=None):
    """Add a ReferenceCatalog object
    """
    id=str(id)
    title=str(title)
    c=ReferenceCatalog(id, title, vocab_id, self)
    self._setObject(id, c)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST,update_menu=1)

        
InitializeClass(ReferenceCatalog)
