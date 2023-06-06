#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from xml.etree import ElementTree
import yaml
import os, sys
import glob

sys.path.insert(1, '../')
import Settings as cfg


def load_mapping(yaml_file):
    with open(yaml_file) as f:
        _mapping = yaml.safe_load(f)
    return _mapping


def load_template(xml_file):
    tree = ElementTree.parse(xml_file)
    return tree


def get_project_name(org_name):
    proj_name = org_name
    try:
        proj_name = org_name.split('/')[1]
    except IndexError:
        pass
    return proj_name


def load_transitions(csv_file):
    _transitions = dict()
    # Project A_to_A A_to_NC A_to_I NC_to_A	NC_to_NC NC_to_I I_to_A	I_to_NC	I_to_I	I_to_G	G_to_A	G_to_NC	G_to_G
    with open(csv_file) as f:
        csv_reader = csv.reader(f, delimiter=';')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                _header = row
                line_count += 1
            else:
                project = get_project_name(row[0])
                project_transitions = dict()
                for j in range(1, len(_header)):
                    project_transitions.update({_header[j]: round(float(row[j]), 2)})
                _transitions.update({project: project_transitions})
                line_count += 1
    return _transitions


def update_diagram(_header_mapping, _transitions, _node_mapping, _outputFolder):
    for proj_name, proj_transitions in _transitions.items():
        xml_tree = load_template(os.path.join('diagram_model', 'template.xml'))
        for column_header, (from_node, to_node) in _header_mapping.items():
            node_id = _node_mapping[from_node][to_node].strip()
            node = xml_tree.findall(".//mxCell[@id='{0}']".format(node_id))[0]
            value = proj_transitions[column_header]
            node.attrib['value'] = "{}%".format(value)
            if value == float(0):  # if label is 0.0, use dashed style for the edge
                parent_node = xml_tree.findall(".//mxCell[@id='{0}']".format(node.attrib['parent']))[0]
                style = parent_node.attrib['style']
                parent_node.attrib['style'] = '{}{}'.format(style, _node_mapping['edge']['style'])
        # create a new XML file with the transition values
        serialized_tree = ElementTree.tostring(xml_tree.getroot())
        with open(os.path.join(_outputFolder, "{}_diagram.xml".format(proj_name)), "w") as diagramf:
            diagramf.write(serialized_tree.decode("utf-8"))

    remove_zero_labels()

def remove_zero_labels():
    for filename in glob.glob(os.path.join('diagrams', '*.xml')):
        xml_file = open(filename, 'r')
        tree = ElementTree.parse(xml_file)
        xml_file.close()
        node_parent = tree.findall(".//root")[0]
        for child in node_parent:
            try:
                if child.attrib['value'] == '0.0%':
                    node_parent.remove(child)
            except KeyError:
                pass

        with open(filename, 'w') as xml_file:
            xml_file.write(ElementTree.tostring(tree.getroot()).decode('utf-8'))


if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    # python script.py gitCloneURL
    print('Arguments: {} --> {}'.format(len(sys.argv), str(sys.argv)))
    mode = sys.argv[1]
    if mode.lower() not in cfg.supported_modes:
        print('ERROR: Not valid mode! ({})'.format(cfg.supported_modes))
        sys.exit(0)
    print('Selected Mode: ', mode.upper())

    sourceFile = os.path.join(cfg.main_folder, mode.upper(), 'organizations_chains_list.csv')

    outputFolder = os.path.join(cfg.main_folder, mode.upper(), 'diagrams')
    os.makedirs(outputFolder, exist_ok=True)

    node_mapping = load_mapping(os.path.join('diagram_model', 'drawio-mapping.yml'))
    header = load_mapping(os.path.join('diagram_model', 'result_mapping.yml'))

    transitions = load_transitions(sourceFile)
    update_diagram(header, transitions, node_mapping, outputFolder)
