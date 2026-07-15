import os
import streamlit.components.v1 as components

_component_func = components.declare_component(
    "native_color_picker",
    path=os.path.dirname(os.path.abspath(__file__))
)

def native_color_picker(label="選擇顏色", default_color="#000000", key=None):
    component_value = _component_func(label=label, default_color=default_color, key=key, default=default_color)
    return component_value
