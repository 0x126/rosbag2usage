#!/bin/env python3

import numpy as np
import plotly
import argparse
import pathlib

from rosbag2_py import ConverterOptions
from rosbag2_py import SequentialReader
from rosbag2_py import StorageOptions

def analyze(bag_name):
    def create_reader(bag_dir: str) -> SequentialReader:
        storage_options = StorageOptions(
            uri=bag_dir,
            storage_id="sqlite3",
        )
        converter_options = ConverterOptions(
            input_serialization_format="cdr",
            output_serialization_format="cdr",
        )

        reader = SequentialReader()
        reader.open(storage_options, converter_options)
        return reader

    reader = create_reader(str(bag_name))
    type_map = {}
    for topic_type in reader.get_all_topics_and_types():
        type_map[topic_type.name] = topic_type.type

    size_dict = {}
    while reader.has_next():
        (topic, data, stamp) = reader.read_next()
        if topic in size_dict:
            size_dict[topic] += np.int64(len(data))
        else:
            size_dict[topic] = np.int64(len(data))
    return size_dict

def visualize(size_dict):
    temp = {}
    def register(name, size):
        parent = name.rsplit('/',1)[0]
        child = name
        if child in temp:
            temp[child]['size'] += np.int64(size)
        else:
            temp[child] = {'parent': parent, 'size': np.int64(size)}
        if parent:
            register(parent, size)
        else:
            return

    for topic, size in size_dict.items():
        register(topic, size)

    def sizeof_fmt(num):
        for unit in ["", "KB", "MB", "GB"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}"
            num /= 1024.0
        return f"{num:.1f}TB"
    name=[]
    parent=[]
    size=[]
    label=[]
    text=[]
    for topic, data in temp.items():
        name.append(topic)
        parent.append(data['parent'])
        size.append(data['size'])
        label.append(topic.rsplit('/',1)[1])
        text.append(sizeof_fmt(data['size']))

    fig = plotly.graph_objs.Figure()
    fig.add_trace(plotly.graph_objs.Treemap(
    ids = name,
    labels = label,
    parents = parent,
    values = size,
    hovertext=text,
    tiling=plotly.graph_objects.treemap.Tiling(packing='squarify') #[‘squarify’, ‘binary’, ‘dice’, ‘slice’, ‘slice-dice’, ‘dice-slice’]
    ))
    fig.show()

def main():
    parser = argparse.ArgumentParser(description="Visualize the capacity of each topic. ")
    parser.add_argument("input_bag", help="input bag stored path")

    args = parser.parse_args()
    input_path = pathlib.Path(args.input_bag)
    if not input_path.exists():
        raise FileNotFoundError("Input bag folder '{}' is not found.".format(input_path))

    size_dict = analyze(input_path)
    visualize(size_dict)

if __name__ == "__main__":
    main()
