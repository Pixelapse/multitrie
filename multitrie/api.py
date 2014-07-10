import logging
from collections import deque
# Not thread-safe, use from one thread only or obtain a lock!

from itertools import chain, izip

logger = logging.getLogger(__name__)


class Node(object):
  """Trie node class.

  :ivar values: The values associated with the key corresponding this node
  :ivar children: A ``{key-part : child-node}`` mapping.
  """
  __slots__ = ('values', 'children')

  def __init__(self, values=()):
    self.values = deque(values)
    self.children = dict()

  def __nonzero__(self):
    return len(self.values) or len(self.children)

  def __unicode__(self):
    return self.values.__unicode__() + u' ' + dict.__unicode__(self.children)

  def __str__(self):
    return unicode(self).encode('ascii', 'replace')


class MultiTrie(object):
  to_parts = tuple
  to_key = tuple

  def __init__(self):
    self.root = Node()

  def __iter__(self):
    return self.iterkeys()

  def force_parts(self, key=None, parts=None):
    if parts:
      return parts
    else:
      return self.to_parts(key)

  ##############################################################################
  # Mapping API methods
  ##############################################################################

  # Node iterators
  def niterkeys(self, node, parts=None):
    parts = parts or []
    return chain([self.to_key(parts)] if node.values else (), chain.from_iterable(self.niterkeys(child, parts + [part]) for (part, child) in node.children.iteritems()))

  def nitervalues(self, node):
    return chain(node.values, chain.from_iterable(self.nitervalues(child) for child in node.children.itervalues()))

  def niteritems(self, node, parts=None):
    parts = parts or []
    key = self.to_key(parts)
    return chain(((key, value) for value in node.values), chain.from_iterable(self.niteritems(child, parts + [part]) for (part, child) in node.children.iteritems()))

  # Iterative versions
  def iterkeys(self, prefix=None, parents=False):
    if prefix is None:
      node = self.root
      parts = []
    elif parents:
      parts = self.to_parts(prefix)
      node, pitems = self._find_parents(parts=parts, error=False)
      return chain((key for (key, parent) in pitems if parent.values), self.niterkeys(node, parts) if node else [])
    else:
      try:
        node = self._find(prefix)
      except KeyError:
        return iter([])

      parts = self.to_parts(prefix)

    return self.niterkeys(node, parts)

  def itervalues(self, prefix=None, parents=False):
    if prefix is None:
      node = self.root
    elif parents:
      parts = self.to_parts(prefix)
      node, pitems = self._find_parents(parts=parts, error=False)
      return chain((value for (key, parent) in pitems for value in parent.values), self.nitervalues(node) if node else [])
    else:
      try:
        node = self._find(prefix)
      except KeyError:
        return iter([])

    return self.nitervalues(node)

  def iteritems(self, prefix=None, parents=False):
    if prefix is None:
      node = self.root
      parts = []
    elif parents:
      parts = self.to_parts(prefix)
      node, pitems = self._find_parents(parts=parts, error=False)
      return chain(((key, value) for (key, parent) in pitems for value in parent.values), self.niteritems(node, parts) if node else [])
    else:
      try:
        node = self._find(prefix)
      except KeyError:
        return iter([])

      parts = self.to_parts(prefix)

    return self.niteritems(node, parts)

  # List versions
  def keys(self, prefix=None, parents=False):
    return list(self.iterkeys(prefix, parents))

  def values(self, prefix=None, parents=False):
    return list(self.itervalues(prefix, parents))

  def items(self, prefix=None, parents=False):
    return list(self.iteritems(prefix, parents))

  ##############################################################################
  # Basic operations
  ##############################################################################

  def _find(self, key=None, parts=None, error=True):
    """
    Find the node at the key and raise KeyError if not found
    """
    node = self.root

    for part in self.force_parts(key, parts):
      try:
        node = node.children[part]
      except KeyError:
        if error:
          raise KeyError(key)
        else:
          return None

    return node

  def __getitem__(self, key):
    node = self._find(key)
    return node.values

  def has_ancestor(self, key=None, parts=None):
    """
    Returns:
      True if an ancestor exists (has to have a value), False if otherwise
    """
    node = self.root
    found = False

    for part in self.force_parts(key, parts):
      try:
        if len(node.values):
          found = True
          break

        node = node.children[part]
      except KeyError:
        break

    return found

  def _find_parents(self, key=None, parts=None, error=True):
    """
    Returns:
      node: node specified by key or parts and
      pitems: list of (key, node) tuples for the parents
    """
    # logger.info(u'Find parents called with key: %s parts: %s' % (key, parts))
    partial = []
    pitems = []

    node = self.root

    for part in self.force_parts(key, parts):
      pitems.append((self.to_key(partial), node))
      partial.append(part)

      try:
        node = node.children[part]
      except KeyError:
        if error:
          raise KeyError(u'Node children: %s %s does not exist' % (node.children, part))
        else:
          node = None
          break

    return node, pitems

  def _add_node(self, key=None, parts=None):
    node = self.root

    for part in self.force_parts(key, parts):
      try:
        node = node.children[part]
      except KeyError:
        new_node = Node()
        node.children[part] = new_node
        node = new_node

    return node

  def _add_node_parents(self, key=None, parts=None):
    partial = []
    parents = []

    node = self.root

    for part in self.force_parts(key, parts):
      parents.append((self.to_key(partial), node))
      partial.append(part)

      try:
        node = node.children[part]
      except KeyError:
        new_node = Node()
        node.children[part] = new_node
        node = new_node

    return node, parents

  def add(self, key, obj):
    """
    Inserts obj into the record at key
    """
    node = self._add_node(key)

    node.values.append(obj)

  def cleanup(self, node, key=None, parts=None, parents=None, pitems=None):
    if not parents:
      parents = [parent for (key_item, parent) in pitems]

    parts = self.force_parts(key, parts)

    for parent, part in izip(reversed(parents), reversed(parts)):
      if not node:
        del parent.children[part]
      else:
        break

      node = parent

  def remove(self, key, obj):
    """
    Removes an object from the record at key, and cleans up empty nodes on the way up
    """
    parts = self.to_parts(key)

    node, pitems = self._find_parents(parts=parts, error=True)

    # Throws KeyError, ValueError if object does not exist
    node.values.remove(obj)

    self.cleanup(node, parts=parts, pitems=pitems)

  def merge_move(self, src_node, dest_node):
    if src_node != dest_node:
      dest_node.values.extend(src_node.values)
      src_node.values.clear()

      for (key, child) in src_node.children:
        if key in dest_node.children:
          self.merge_move(child, dest_node.children[key])
        else:
          dest_node.children[key] = child

      src_node.children.clear()

  def merge_move_with_pred(self, src_node, dest_node, src_parts, dest_parts, pred):
    if src_node != dest_node:
      src_key = self.to_key(src_parts)
      dest_key = self.to_key(dest_parts)

      for value in tuple(src_node.values):
        if pred(src_key, dest_key, value):
          dest_node.values.append(value)
          src_node.values.remove(value)

      for (key, child) in tuple(src_node.children.items()):
        if key in dest_node.children:
          node = dest_node.children[key]
        else:
          node = Node()

        self.merge_move_with_pred(child, dest_node.children[key], src_parts + key, dest_parts + key, pred)

        if not child:
          del src_node.children[key]

        if node:
          dest_node.children[key] = node

  def move(self, src, dest, pred=None):
    src_parts = self.to_parts(src)

    try:
      src_node, pitems = self._find_parents(parts=src_parts)
    except KeyError:
      return

    dest_parts = self.to_parts(dest)
    dest_node = self._add_node(parts=dest_parts)

    if pred:
      self.merge_move_with_pred(src_node, dest_node, src_parts, dest_parts, pred)
    else:
      self.merge_move(src_node, dest_node)

    # Cleanup src_node if it is now empty
    self.cleanup(src_node, parts=src_parts, pitems=pitems)

  ##############################################################################
  # Whole object operations
  ##############################################################################
  def clear(self):
    self.root.children.clear()
    self.root.values.clear()

