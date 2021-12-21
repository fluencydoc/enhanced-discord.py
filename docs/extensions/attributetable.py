from sphinx.util.docutils import SphinxDirective
from sphinx.locale import _
from docutils import nodes
from sphinx import addnodes

from collections import OrderedDict, namedtuple
import importlib
import inspect
import os
import re


class attributetable(nodes.General, nodes.Element):
    pass


class attributetablecolumn(nodes.General, nodes.Element):
    pass


class attributetabletitle(nodes.TextElement):
    pass


class attributetableplaceholder(nodes.General, nodes.Element):
    pass


class attributetablebadge(nodes.TextElement):
    pass


class attributetable_item(nodes.Part, nodes.Element):
    pass


def visit_attributetable_node(self, node):
    class_ = node["python-class"]
    self.body.append(f'<div class="py-attribute-table" data-move-to-id="{class_}">')


def visit_attributetablecolumn_node(self, node):
    self.body.append(self.starttag(node, "div", CLASS="py-attribute-table-column"))


def visit_attributetabletitle_node(self, node):
    self.body.append(self.starttag(node, "span"))


def visit_attributetablebadge_node(self, node):
    """
    .. function_name: visit_attributetablebadge_node
       :synopsis: Creates a
    span element with the class py-attribute-table-badge and adds it to the
    body.
    """
    attributes = {
        "class": "py-attribute-table-badge",
        "title": node["badge-type"],
    }
    self.body.append(self.starttag(node, "span", **attributes))


def visit_attributetable_item_node(self, node):
    self.body.append(self.starttag(node, "li", CLASS="py-attribute-table-entry"))


def depart_attributetable_node(self, node):
    self.body.append("</div>")


def depart_attributetablecolumn_node(self, node):
    self.body.append("</div>")


def depart_attributetabletitle_node(self, node):
    self.body.append("</span>")


def depart_attributetablebadge_node(self, node):
    self.body.append("</span>")


def depart_attributetable_item_node(self, node):
    self.body.append("</li>")


_name_parser_regex = re.compile(r"(?P<module>[\w.]+\.)?(?P<name>\w+)")


class PyAttributeTable(SphinxDirective):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def parse_name(self, content):
        """
        Parse a name into its module and object names.

        Given a string like
        ``some.module:name``, return the module name (e.g., ``some.module``) and
        the object name (e.g., ``name``). If no module is given, use the current
        document's current module as default; if there is no current document
        either, raise an error.
        """
        path, name = _name_parser_regex.match(content).groups()
        if path:
            modulename = path.rstrip(".")
        else:
            modulename = self.env.temp_data.get("autodoc:module")
            if not modulename:
                modulename = self.env.ref_context.get("py:module")
        if modulename is None:
            raise RuntimeError("modulename somehow None for %s in %s." % (content, self.env.docname))

        return modulename, name

    def run(self):
        """If you're curious on the HTML this is meant to generate:

        <div class="py-attribute-table">
            <div class="py-attribute-table-column">
                <span>_('Attributes')</span>
                <ul>
                    <li>
                        <a href="...">
                    </li>
                </ul>
            </div>
            <div class="py-attribute-table-column">
                <span>_('Methods')</span>
                <ul>
                    <li>
                        <a href="..."></a>
                        <span class="py-attribute-badge" title="decorator">D</span>
                    </li>
                </ul>
            </div>
        </div>

        However, since this requires the tree to be complete
        and parsed, it'll need to be done at a different stage and then
        replaced.
        """
        content = self.arguments[0].strip()
        node = attributetableplaceholder("")
        modulename, name = self.parse_name(content)
        node["python-doc"] = self.env.docname
        node["python-module"] = modulename
        node["python-class"] = name
        node["python-full-name"] = f"{modulename}.{name}"
        return [node]


def build_lookup_table(env):
    """
    Build a lookup table mapping class names to their child attributes.

    :param
    env: The Sphinx environment.
    :returns: A dictionary mapping class names to
    lists of attribute strings.

        For example, ``{"Foo": ["bar", "baz"]}``
    indicates that the ``Foo`` class has two child attributes named ``bar`` and
    ``baz``, respectively. If a given object type does not have any children
    (e.g., functions), it will be absent from 
        the returned dictionary
    entirely; if a given object type has no children with documentation pages
    (e.g., undocumented 
        functions), its list of children will be empty but
    present in the returned dictionary regardless of whether there is
    documentation for those objects or not (for consistency).

         This
    function is used by :func`build_reference`. It should generally not need to
    be called directly by anything else.
    """
    # Given an environment, load up a lookup table of
    # full-class-name: objects
    result = {}
    domain = env.domains["py"]

    ignored = {
        "data",
        "exception",
        "module",
        "class",
    }

    for (fullname, _, objtype, docname, _, _) in domain.get_objects():
        if objtype in ignored:
            continue

        classname, _, child = fullname.rpartition(".")
        try:
            result[classname].append(child)
        except KeyError:
            result[classname] = [child]

    return result


TableElement = namedtuple("TableElement", "fullname label badge")


def process_attributetable(app, doctree, fromdocname):
    """
    Builds a table of class attributes, grouped by type.

    :param lookup: A
    dictionary mapping fully qualified Python names to
    :class:`~sphinxcontrib.napoleon.docstring.GoogleDocstring` objects
    :type
    lookup: dict(str, sphinxcontrib-napoleon_google_docstring)
    """
    env = app.builder.env

    lookup = build_lookup_table(env)
    for node in doctree.traverse(attributetableplaceholder):
        modulename, classname, fullname = node["python-module"], node["python-class"], node["python-full-name"]
        groups = get_class_results(lookup, modulename, classname, fullname)
        table = attributetable("")
        for label, subitems in groups.items():
            if not subitems:
                continue
            table.append(class_results_to_node(label, sorted(subitems, key=lambda c: c.label)))

        table["python-class"] = fullname

        if not table:
            node.replace_self([])
        else:
            node.replace_self([table])


def get_class_results(lookup, modulename, name, fullname):
    """
    Get a table of attributes and methods for the given class.

    :param lookup:
    A mapping from fully qualified names to members.
    :type lookup: dict[str,
    list[str]]
    """
    module = importlib.import_module(modulename)
    cls = getattr(module, name)

    groups = OrderedDict(
        [
            (_("Attributes"), []),
            (_("Methods"), []),
        ]
    )

    try:
        members = lookup[fullname]
    except KeyError:
        return groups

    for attr in members:
        attrlookup = f"{fullname}.{attr}"
        key = _("Attributes")
        badge = None
        label = attr
        value = None

        for base in cls.__mro__:
            value = base.__dict__.get(attr)
            if value is not None:
                break

        if value is not None:
            doc = value.__doc__ or ""
            if inspect.iscoroutinefunction(value) or doc.startswith("|coro|"):
                key = _("Methods")
                badge = attributetablebadge("async", "async")
                badge["badge-type"] = _("coroutine")
            elif isinstance(value, classmethod):
                key = _("Methods")
                label = f"{name}.{attr}"
                badge = attributetablebadge("cls", "cls")
                badge["badge-type"] = _("classmethod")
            elif inspect.isfunction(value):
                if doc.startswith(("A decorator", "A shortcut decorator")):
                    # finicky but surprisingly consistent
                    badge = attributetablebadge("@", "@")
                    badge["badge-type"] = _("decorator")
                    key = _("Methods")
                else:
                    key = _("Methods")
                    badge = attributetablebadge("def", "def")
                    badge["badge-type"] = _("method")

        groups[key].append(TableElement(fullname=attrlookup, label=label, badge=badge))

    return groups


def class_results_to_node(key, elements):
    """
    Returns a reStructuredText node containing an attribute table for the given
    key and elements.

    The attribute table will have one column with a title
    that is the given key,
    and each row will contain an element from `elements`
    as its first item.
    If any of those elements has a badge associated with it,
    then the badge is used in place of the element's label.

    :param str key:
    The name to use for this column's title (the same string passed to
    `attributetabletitle`).
        This should be something like "Classes" or
    "Functions".
        It can also be None if no title should be displayed at all
    (but in that case you must pass an empty string as `title`).

        .. note:
    If you want to display two columns without titles, then pass ``None`` twice
    instead of passing ``""`` twice!

            For example:
    ``attributetablecolumn(None, None)`` vs. ``attributetablecolumn("", "")`` .
    In addition to being more concise than using two separate calls to this
    function (which would look like this): ::
    attributetablecolumn("", "") #
    """
    title = attributetabletitle(key, key)
    ul = nodes.bullet_list("")
    for element in elements:
        ref = nodes.reference(
            "", "", internal=True, refuri="#" + element.fullname, anchorname="", *[nodes.Text(element.label)]
        )
        para = addnodes.compact_paragraph("", "", ref)
        if element.badge is not None:
            ul.append(attributetable_item("", element.badge, para))
        else:
            ul.append(attributetable_item("", para))

    return attributetablecolumn("", title, ul)


def setup(app):
    """
    Adds a directive to the Sphinx documentation system that allows for the
    creation of tables with badges.
    """
    app.add_directive("attributetable", PyAttributeTable)
    app.add_node(attributetable, html=(visit_attributetable_node, depart_attributetable_node))
    app.add_node(attributetablecolumn, html=(visit_attributetablecolumn_node, depart_attributetablecolumn_node))
    app.add_node(attributetabletitle, html=(visit_attributetabletitle_node, depart_attributetabletitle_node))
    app.add_node(attributetablebadge, html=(visit_attributetablebadge_node, depart_attributetablebadge_node))
    app.add_node(attributetable_item, html=(visit_attributetable_item_node, depart_attributetable_item_node))
    app.add_node(attributetableplaceholder)
    app.connect("doctree-resolved", process_attributetable)
