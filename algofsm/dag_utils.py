# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
from . import utils


# --------------------------------------------------------------------
# perform some conversions on the sytax tree, eg. for into while loops
# --------------------------------------------------------------------
def expand_tree_structs(parser, root, node, ind, sm_num, dbg):
    return _expand_tree_structs(parser, root, node, ind, sm_num, dbg, [0])


def _expand_tree_structs(parser, root, node, ind, sm_num, dbg, cnt):
    while node:
        org_nxt = node.nxt
        expanded = False

        if parser.has_tick(node):
            if node.typ == "cs":
                utils.error("case with `tick inside are not supported yet")
            elif node.typ == "do":
                body = node.child[1]
                _expand_tree_structs(parser, root, body, ind, sm_num, dbg, cnt)
            elif node.typ == "fo":
                try:
                    init, cond, post = node.code.split(";")
                except ValueError:
                    utils.error("syntax error in for estatement for ({node.code})")

                body = node.child[1]

                # convert:    for (init; cond; post)
                #                 BODY
                # into:       init
                #             while(cond)
                #                 BODY
                #                 post

                # node that takes care of the variable initialization in for loop
                init_node = parser.node_add(
                    "sn", code=init, nxt=node, child=[None, None, None]
                )
                parser.node_preinsert(init_node, node)

                # repurpose the 'for' node into a 'while' node (keeps body)
                node.typ = "wh"
                node.code = cond

                # node that goes after the body of the while is linked to 'post' node
                post_node = parser.node_add(
                    "sn", code=post, nxt=None, child=[None, None, None]
                )
                ending_node = parser.node_find_last(body)
                if ending_node:
                    ending_node.nxt = post_node

                # expand for block, given post_node as nxt
                _expand_tree_structs(parser, root, body, ind, sm_num, dbg, cnt)
                expanded = True
            elif node.typ == "if":
                _expand_tree_structs(
                    parser, root, node.child[1], ind, sm_num, dbg, cnt
                )
                _expand_tree_structs(
                    parser, root, node.child[2], ind, sm_num, dbg, cnt
                )
            elif node.typ == "wh":
                _expand_tree_structs(
                    parser, root, node.child[1], ind, sm_num, dbg, cnt
                )
            elif node.typ == "eif":
                assert False, "unexpected typ eif in _expand_tree_structs"
        else:
            node.nxt = org_nxt
        #end if parser.has_tick(node)

        if expanded and dbg > 1:
            parser.st_show_from_node(
                f"{sm_num}_01_during_expand_structs{cnt[0]}", root
            )
            parser.dump_dot(
                f"{sm_num}_01_during_expand_structs{cnt[0]}",
                root,
                f"{node} expanded",
            )
            cnt[0] += 1

        node = org_nxt
    # end while(node)


# --------------------------------------------------------------------
# Convert syntax tree in a DAG
# --------------------------------------------------------------------
def convert_to_dag(parser, root, node, ind, sm_num, dbg):
    _convert_to_dag(parser, root, node, ind, None, sm_num, dbg, [0])


def _convert_to_dag(parser, root, node, ind, top_nxt, sm_num, dbg, cnt):
    while node:
        org_nxt = node.nxt
        nxt = org_nxt or top_nxt
        expanded = False

        if parser.has_tick(node):
            if node.typ == "do":
                body = node.child[1]
                eif_node = parser.node_add(
                    "eif",
                    code=node.code,
                    nxt=None,
                    child=[None, None, None],
                )
                # refill node with the original body block
                node.copy_flds_from(body)
                parser.node_rm(body)  # this node got copied, now removed
                _convert_to_dag(
                    parser, root, node, ind, eif_node, sm_num, dbg, cnt
                )
                # eif_node links are filled up afterwards to avoid an
                # infinite loop in the recursive call above
                eif_node.child = [None, node, nxt]
                expanded = True
            elif node.typ == "if":
                i = node.child[1]
                _convert_to_dag(parser, root, i, ind, nxt, sm_num, dbg, cnt)
                i = node.child[2]
                _convert_to_dag(parser, root, i, ind, nxt, sm_num, dbg, cnt)
                if i is None:
                    node.child[2] = nxt
                node.typ = "eif"
                node.nxt = None
                expanded = True
            elif node.typ == "wh":
                i = node.child[1]
                _convert_to_dag(parser, root, i, ind, node, sm_num, dbg, cnt)
                node.child[2] = nxt
                node.typ = "eif"
                node.nxt = None
                expanded = True
            elif node.typ in ["fo", "cs"]:
                utils.error(
                    f"internal '{node.typ}' is expected to be pre-expanded "
                    "in _expand_tree_structs"
                )
            else:
                node.child[1] = nxt
                node.nxt = None
        else:
            node.nxt = nxt
        #end if parser.has_tick(node)

        if expanded and dbg > 1:
            parser.st_show_from_node(
                f"{sm_num}_03_during_convert_to_dag{cnt[0]}", root
            )
            parser.dump_dot(
                f"{sm_num}_03_during_convert_to_dag{cnt[0]}",
                root,
                f"{node} expanded",
            )
            cnt[0] += 1

        node = org_nxt
    # end while(node)
