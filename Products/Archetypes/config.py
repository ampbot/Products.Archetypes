PKG_NAME = "Archetypes"
SKIN_NAME = "archetypes"
TOOL_NAME = "archetype_tool" ## Name the tool will be installed under

UID_CATALOG = "uid_catalog"

REGISTER_DEMO_TYPES = 1 ##Initialize the demo types
INSTALL_DEMO_TYPES = 1 ##Install the demo types
DEBUG = 1  ## See debug messages

##Reference Engine bits
REFERENCE_CATALOG = "reference_catalog"
UUID_ATTR = "_at_uid"
REFERENCE_ANNOTATION = "at_references"

##ordered folder handling
##implement the old style ordered folder?
##for backward compatibility reasons only
USE_OLD_ORDEREDFOLDER_IMPLEMENTATION = 0

## In zope 2.6.3+ and 2.7.0b4+ a lines field returns a tuple not a list. Per
## default archetypes returns a tuple, too. If this breaks your software you
## can disable the change.
## See http://zope.org/Collectors/Zope/924
ZOPE_LINES_IS_TUPLE_TYPE = 1

## MYSQL SQLStorage Table Type
## To use connections with ACID transactions you should define it as
## INNODB. The MySQL default table type is MyISAM.
MYSQL_SQLSTORAGE_TABLE_TYPE = 'INNODB'

## Debug security settings of Fields, Widgets and Storages?
DEBUG_SECURITY=False
#DEBUG_SECURITY=True


## If you have graphviz http://www.research.att.com/sw/tools/graphviz/
## and its frontend "dot" installed on your system set this to True
GRAPHVIZ_BINARY = "/usr/bin/dot"
# XXX: add autodetect code?
HAS_GRAPHVIZ = False
#HAS_GRAPHVIZ = True


