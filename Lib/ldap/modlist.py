"""
ldap.modlist - create add/modify modlist's

See https://www.python-ldap.org/ for details.

Python compability note:
This module is known to work with Python 2.0+ but should work
with Python 1.5.2 as well.
"""

from ldap import __version__

import string,ldap,ldap.cidict


lower = getattr(string, 'lower', lambda s: s.lower())

def list_dict(l,case_insensitive=0):
  """
  return a dictionary with all items of l being the keys of the dictionary

  If argument case_insensitive is non-zero ldap.cidict.cidict will be
  used for case-insensitive string keys
  """
  if case_insensitive:
    d = ldap.cidict.cidict()
  else:
    d = {}
  for i in l:
    d[i]=None
  return d


def addModlist(entry,ignore_attr_types=None):
  """Build modify list for call of method LDAPObject.add()"""
  ignore_attr_types = list_dict(map(lower,(ignore_attr_types or [])))
  modlist = []
  for attrtype in entry.keys():
    if lower(attrtype) in ignore_attr_types:
      # This attribute type is ignored
      continue
    # Eliminate empty attr value strings in list
    attrvaluelist = [item for item in entry[attrtype] if item is not None]
    if attrvaluelist:
      modlist.append((attrtype,entry[attrtype]))
  return modlist # addModlist()


def modifyModlist(
  old_entry,new_entry,ignore_attr_types=None,ignore_oldexistent=0,case_ignore_attr_types=None
):
  """
  Build differential modify list for calling LDAPObject.modify()/modify_s()

  old_entry
      Dictionary holding the old entry
  new_entry
      Dictionary holding what the new entry should be
  ignore_attr_types
      List of attribute type names to be ignored completely
  ignore_oldexistent
      If non-zero attribute type names which are in old_entry
      but are not found in new_entry at all are not deleted.
      This is handy for situations where your application
      sets attribute value to '' for deleting an attribute.
      In most cases leave zero.
  case_ignore_attr_types
      List of attribute type names for which comparison will be made
      case-insensitive
  """
  ignore_attr_types = list_dict(map(lower,(ignore_attr_types or [])))
  case_ignore_attr_types = list_dict(map(lower,(case_ignore_attr_types or [])))
  modlist = []
  attrtype_lower_map = {}
  for a in old_entry.keys():
    attrtype_lower_map[lower(a)]=a
  for attrtype in new_entry.keys():
    attrtype_lower = lower(attrtype)
    if attrtype_lower in ignore_attr_types:
      # This attribute type is ignored
      continue
    # Filter away null-strings
    new_value = [item for item in new_entry[attrtype] if item is not None]
    if attrtype_lower in attrtype_lower_map:
      old_value = old_entry.get(attrtype_lower_map[attrtype_lower],[])
      old_value = [item for item in old_value if item is not None]
      del attrtype_lower_map[attrtype_lower]
    else:
      old_value = []
    if not old_value and new_value:
      # Add a new attribute to entry
      modlist.append((ldap.MOD_ADD,attrtype,new_value))
    elif old_value and new_value:
      # Replace existing attribute
      replace_attr_value = len(old_value)!=len(new_value)
      if not replace_attr_value:
        case_insensitive = attrtype_lower in case_ignore_attr_types
        old_value_dict=list_dict(old_value,case_insensitive)
        new_value_dict=list_dict(new_value,case_insensitive)
        delete_values = []
        for v in old_value:
          if v not in new_value_dict:
            replace_attr_value = 1
            break
        add_values = []
        if not replace_attr_value:
          for v in new_value:
            if v not in old_value_dict:
              replace_attr_value = 1
              break
      if replace_attr_value:
        modlist.append((ldap.MOD_DELETE,attrtype,None))
        modlist.append((ldap.MOD_ADD,attrtype,new_value))
    elif old_value and not new_value:
      # Completely delete an existing attribute
      modlist.append((ldap.MOD_DELETE,attrtype,None))
  if not ignore_oldexistent:
    # Remove all attributes of old_entry which are not present
    # in new_entry at all
    for a in attrtype_lower_map.keys():
      if a in ignore_attr_types:
        # This attribute type is ignored
        continue
      attrtype = attrtype_lower_map[a]
      modlist.append((ldap.MOD_DELETE,attrtype,None))
  return modlist # modifyModlist()
