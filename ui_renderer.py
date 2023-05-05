# import contextlib
# import dataclasses
# import datetime
# import inspect
# import json
# import mimetypes
# import os
# import re
# from collections import defaultdict
# from enum import Enum
# from pathlib import Path
# from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar
# from urllib.parse import urljoin

# import pandas as pd
# import streamlit as st
# from dp.launching.server.common.components.streamlit_borhium_select import \
#     st_machine_select
# # from streamlit_file_browser import st_file_browser
# from dp.launching.server.common.components.streamlit_file_browser_wrapper import \
#     st_file_browser
# from dp.launching.server.models import (Application, ApplicationManager,
#                                         Events, Job, JobManager, JobStatus,
#                                         User, UserManager, Version,
#                                         VersionManager, VersionStatus)
# from dp.launching.server.render import schema_utils
# from dp.launching.server.utils.components import (MACHINES_PATH,
#                                                   get_machine_type_options)
# from dp.launching.server.utils.session import (LoginType, access_from_labs,
#                                                get_web_origin)
# from dp.launching.typing.basic import BaseModel, ValidationError
# from dp.launching.typing.basic import json as pydantic_json
# from dp.launching.typing.basic import parse_obj_as
# from streamlit.runtime.state import SessionState
# from streamlit_antd.cascader import st_antd_cascader
# from streamlit_antd.steps import Item, st_antd_steps
# from streamlit_antd.table import st_antd_table
# from streamlit_antd.tabs import st_antd_tabs

# pydantic_encoder = pydantic_json.pydantic_encoder

# _OVERWRITE_STREAMLIT_KWARGS_PREFIX = "st_kwargs_"

# def mutator(origin: List[dict], rules: List[dict]) -> List[dict]:
#     if len(rules) == 0:
#         return origin
#     rule = rules[0]
#     key = rule["key"]
#     no_top = rule["no_top"] if "no_top" in rule else False
#     res = {key: {}}
#     for item in origin:
#         if key in item:
#             new_key = item[key]
#             new_key_mutated = None
#             if "operator" in rule and isinstance(rule["operator"], Callable):
#                 new_key = rule["operator"](item[key])
#             if "mutated" in rule and isinstance(rule["mutated"], Callable):
#                 new_key_mutated = rule["mutated"](new_key)
#             if (new_key_mutated or new_key) in res[key]:
#                 res[key][new_key_mutated or new_key].append(item)
#             else:
#                 res[key][new_key_mutated or new_key] = [item]
#             del item[key]

#     for _key, _value in res[key].items():
#         res[key][_key] = mutator(_value, rules[1:])

#     if no_top:
#         return res[key]
#     return res

# def includes_bohrium_options(schema: dict, cb: Optional[Callable] = None) -> bool:
#     flag = False
#     for item in schema.items():
#             item = item[1]
#             if 'format' in item and 'scope' in item:
#                 if item['scope'] == 'executor' and (
#                     item['format'] == 'bohrium_job_type' or
#                     item['format'] == 'bohrium_machine_type' or
#                     item['format'] == 'bohrium_platform'
#                 ):
#                     flag = True
#                     isinstance(cb, Callable) and cb(item, item['scope'], item['format'])
#     return flag

# def get_cascader_options(opts: dict):
#     res = []
#     for key, value in opts.items():
#         children = None
#         if isinstance(value, List):
#             children = []
#             for v in value:
#                 children.append({"value": v["skuName"], "label": v["skuName"]})
#         else:
#             children = get_cascader_options(value)
#         new_value = {
#             "value": key,
#             "label": key,
#             "children": children
#         }
#         if children == None:
#             children = [{"value": value["skuName"], "label": value["skuName"]}]
#             new_value["children"] = children
#         res.append(new_value)
#     return res


# def choose_from_workspace(key, ftypes):
#     root = ApplicationManager.get_applications_var_root()
#     is_super = st.session_state.get("super", False)
#     if is_super:
#         root = UserManager.get_users_var_root()
#         artifacts_prefix = 'users/'
#         patterns = ['*/application_data/*/**/*']
#     else:
#         artifacts_prefix = f'users/{st.session_state.user.email}/'
#         root = UserManager.get_user_data_root(st.session_state.user.email)
#         patterns = ['application_data/*/**/*']

#     # print("这里的 str(root) 是: ", str(root))
#     return root, st_file_browser(str(root),
#                            artifacts_site=urljoin(
#                                os.getenv('WEB_BASE', 'http://localhost:1024'), f'/artifacts/{artifacts_prefix}'),
#                            file_ignores=('**/secret.json', '**/job.log',),
#                            show_choose_file=True,
#                            extentions=[f'.{ft}' for ft in ftypes] if ftypes else [],
#                            show_download_file=True,
#                            artifacts_download_site=urljoin(
#                                os.getenv('WEB_BASE', 'http://localhost:1024'), f'/download/artifacts/{artifacts_prefix}'),
#                            glob_patterns=patterns,
#                            key=key,
#                            use_cache=os.getenv('FILE_BROWSER_CACHE', False))


# def _name_to_title(name: str) -> str:
#     """Converts a camelCase or snake_case name to title case."""
#     # If camelCase -> convert to snake case
#     name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
#     name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
#     # Convert to title case
#     return name.replace("_", " ").strip().title()


# def _function_has_named_arg(func: Callable, parameter: str) -> bool:
#     try:
#         sig = inspect.signature(func)
#         for param in sig.parameters.values():
#             if param.name == "input":
#                 return True
#     except Exception:
#         return False
#     return False


# def _has_output_ui_renderer(data_item: BaseModel) -> bool:
#     return hasattr(data_item, "render_output_ui")


# def _has_input_ui_renderer(input_class: Type[BaseModel]) -> bool:
#     return hasattr(input_class, "render_input_ui")


# def _is_compatible_audio(mime_type: str) -> bool:
#     return mime_type in ["audio/mpeg", "audio/ogg", "audio/wav"]


# def _is_compatible_image(mime_type: str) -> bool:
#     return mime_type in ["image/png", "image/jpeg"]


# def _is_compatible_video(mime_type: str) -> bool:
#     return mime_type in ["video/mp4"]


# def _get_current_ui_component(overwrite_kwargs, streamlit_app):
#     current_ui_attr_name = ""
#     if "ui_type" in overwrite_kwargs:
#         if type(overwrite_kwargs["ui_type"]) == str:
#             current_ui_attr_name = overwrite_kwargs["ui_type"]
#         del overwrite_kwargs["ui_type"]
#     if hasattr(streamlit_app, current_ui_attr_name) is not None:
#         return getattr(streamlit_app, current_ui_attr_name)
#     st.error(f'no such ui type {current_ui_attr_name}')
#     return None


# class GroupOptionalFieldsStrategy(str, Enum):
#     NO = "no"
#     EXPANDER = "expander"
#     SIDEBAR = "sidebar"


# class InputUI:
#     """Input UI renderer.

#     lazydocs: ignore
#     """
#     __internal__ = None

#     def __init__(
#         self,
#         key: str,
#         model: Type[BaseModel],
#         streamlit_container: Any = st,
#         group_optional_fields: GroupOptionalFieldsStrategy = "no",  # type: ignore
#         lowercase_labels: bool = False,
#         ignore_empty_values: bool = False,
#         session_state: SessionState = None,
#         **kwargs,
#     ):
#         self._key = key
#         self._session_state = session_state or st.session_state
#         if "filter" in kwargs and isinstance(kwargs["filter"], Callable):
#             self._type_filter = kwargs["filter"]
#             del kwargs["filter"]

#         if "default" in kwargs and isinstance(kwargs["default"], Callable):
#             self._type_default = kwargs["default"]
#             del kwargs["default"]

#         # Initialize Sessions State
#         if "run_id" not in st.session_state:
#             self._session_state.run_id = 0

#         self._session_input_key = self._key + "-data"
#         if self._session_input_key not in st.session_state:
#             self._session_state[self._session_input_key] = {}

#         self._lowercase_labels = lowercase_labels
#         self._group_optional_fields = group_optional_fields
#         self._streamlit_container = streamlit_container
#         self._ignore_empty_values = ignore_empty_values

#         if dataclasses.is_dataclass(model):
#             # Convert dataclasses
#             import pydantic

#             self._input_class = pydantic.dataclasses.dataclass(
#                 model).__pydantic_model__  # type: ignore
#         else:
#             self._input_class = model

#         self._schema_properties = self._input_class.schema(by_alias=True).get(
#             "properties", {}
#         ) if self._input_class else {}
#         self._schema_references = self._input_class.schema(by_alias=True).get(
#             "definitions", {}
#         ) if self._input_class else {}
#         self._required_properties = self._input_class.schema(by_alias=True).get(
#             "required", []
#         ) if self._input_class else []
#         # TODO: check if state has input data

#     def render_ui(self) -> Dict:
#         if _has_input_ui_renderer(self._input_class):
#             # The input model has a rendering function
#             # The rendering also returns the current state of input data
#             self._session_state[self._session_input_key] = self._input_class.render_input_ui(  # type: ignore
#                 self._streamlit_container, self._session_state[self._session_input_key]
#             ).dict()
#             return self._session_state[self._session_input_key]

#         required_properties = self._required_properties

#         properties_in_expander = []

#         # check if the input_class is an instance and build value dicts
#         if isinstance(self._input_class, BaseModel):
#             instance_dict = self._input_class.dict()
#             instance_dict_by_alias = self._input_class.dict(by_alias=True)
#         else:
#             instance_dict = None
#             instance_dict_by_alias = None

#         for property_key in self._schema_properties.keys():
#             streamlit_app = self._streamlit_container
#             if property_key not in required_properties:
#                 if self._group_optional_fields == "sidebar":
#                     streamlit_app = self._streamlit_container.sidebar
#                 elif self._group_optional_fields == "expander":
#                     properties_in_expander.append(property_key)
#                     # Render properties later in expander (see below)
#                     continue

#             property = self._schema_properties[property_key]

#             if hasattr(property, "get") and not property.get("title"):
#                 # Set property key as fallback title
#                 property["title"] = _name_to_title(property_key)

#             # if there are instance values, add them to the property dict
#             if instance_dict is not None:
#                 instance_value = instance_dict.get(property_key)
#                 if instance_value in [None, ""] and instance_dict_by_alias:
#                     instance_value = instance_dict_by_alias.get(property_key)
#                 if instance_value not in [None, ""]:
#                     property["init_value"] = instance_value
#                     # keep a reference of the original class to help with non-discriminated unions
#                     # TODO: This will not succeed for attributes that have an alias
#                     attr = getattr(self._input_class, property_key, None)
#                     if attr is not None:
#                         property["instance_class"] = str(type(attr))

#             try:
#                 value = self._render_property(
#                     streamlit_app, property_key, property)
#                 if not self._is_value_ignored(property_key, value):
#                     self._store_value(property_key, value)
#             except Exception as err:
#                 print(err)

#         if properties_in_expander:
#             # Render optional properties in expander
#             with self._streamlit_container.expander(
#                 "Optional Parameters", expanded=False
#             ):
#                 for property_key in properties_in_expander:
#                     property = self._schema_properties[property_key]

#                     if hasattr(property, "get") and not property.get("title"):
#                         # Set property key as fallback title
#                         property["title"] = _name_to_title(property_key)

#                     try:
#                         value = self._render_property(
#                             self._streamlit_container, property_key, property
#                         )

#                         if not self._is_value_ignored(property_key, value):
#                             self._store_value(property_key, value)

#                     except Exception:
#                         pass

#         state = self._session_state[self._session_input_key]
#         from dp.launching.server.render.schema import __NOT_HANDLE_BY_FORM__
#         new_state = {}
#         if isinstance(state, dict):
#             for key in state.keys():
#                 if isinstance(state[key], __NOT_HANDLE_BY_FORM__):
#                     continue
#                 new_state.update({key: state[key]})
#         return new_state

#     def _get_overwrite_streamlit_kwargs(self, key: str, property: Dict) -> Dict:

#         streamlit_kwargs: Dict = {}

#         for kwarg in property:
#             if kwarg.startswith(_OVERWRITE_STREAMLIT_KWARGS_PREFIX):
#                 streamlit_kwargs[
#                     kwarg.replace(_OVERWRITE_STREAMLIT_KWARGS_PREFIX, "")
#                 ] = property[kwarg]
#         return streamlit_kwargs

#     def _get_default_streamlit_input_kwargs(self, key: str, property: Dict) -> Dict:
#         label = property.get("title")
#         if label and self._lowercase_labels:
#             label = label.lower()

#         disabled = False
#         if property.get("readOnly"):
#             # Read only property -> only show value
#             disabled = True

#         streamlit_kwargs = {
#             "label": label + (f" ```({property.get('description')})```" if property.get('description') else ""),
#             "key": str(self._session_state.run_id) + "-" + str(self._key) + "-" + key,
#             "disabled": disabled
#             # "on_change": detect_change, -> not supported for inside forms
#             # "args": (key,),
#         }

#         if property.get("description"):
#             streamlit_kwargs["help"] = property.get("description")
#         elif property.get("help"):
#             # Fallback to help. Used more frequently with dataclasses
#             streamlit_kwargs["help"] = property.get("help")

#         return streamlit_kwargs

#     def _is_value_ignored(self, property_key: str, value: Any) -> bool:
#         """Returns `True` if the value should be ignored for storing in session.

#         This is the case if `ignore_empty_values` is activated and the value is empty and not already set/changed before.
#         """
#         return (
#             self._ignore_empty_values
#             and (
#                 type(value) == int or type(
#                     value) == float or isinstance(value, str)
#             )  # only for int, float or str
#             and not value
#             and self._get_value(property_key) is None
#         )

#     def _store_value_in_state(self, state: dict, key: str, value: Any) -> None:
#         key_elements = key.split(".")
#         for i, key_element in enumerate(key_elements):
#             if i == len(key_elements) - 1:
#                 # add value to this element
#                 state[key_element] = value
#                 return
#             if key_element not in state:
#                 state[key_element] = {}
#             state = state[key_element]

#     def _get_value_from_state(self, state: dict, key: str) -> Any:
#         key_elements = key.split(".")
#         for i, key_element in enumerate(key_elements):
#             if i == len(key_elements) - 1:
#                 # add value to this element
#                 if key_element not in state:
#                     return None
#                 return state[key_element]
#             if key_element not in state:
#                 state[key_element] = {}
#             state = state[key_element]
#         return None

#     def _store_value(self, key: str, value: Any) -> None:
#         return self._store_value_in_state(
#             self._session_state[self._session_input_key], key, value
#         )

#     def _get_value(self, key: str) -> Any:
#         return self._get_value_from_state(
#             self._session_state[self._session_input_key], key
#         )

#     def _render_single_datetime_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         if property.get("format") == "time":
#             if property.get("init_value"):
#                 streamlit_kwargs["value"] = property.get("init_value")
#             elif property.get("default"):
#                 with contextlib.suppress(Exception):
#                     streamlit_kwargs["value"] = datetime.time.fromisoformat(  # type: ignore
#                         property["default"]
#                     )
#             return streamlit_app.time_input(**{**streamlit_kwargs, **overwrite_kwargs})
#         elif property.get("format") == "date":
#             if property.get("init_value"):
#                 streamlit_kwargs["value"] = property.get("init_value")
#             elif property.get("default"):
#                 with contextlib.suppress(Exception):
#                     streamlit_kwargs["value"] = datetime.date.fromisoformat(  # type: ignore
#                         property["default"]
#                     )
#             return streamlit_app.date_input(**{**streamlit_kwargs, **overwrite_kwargs})
#         elif property.get("format") == "date-time":
#             if property.get("init_value"):
#                 streamlit_kwargs["value"] = property.get("init_value")
#             elif property.get("default"):
#                 with contextlib.suppress(Exception):
#                     streamlit_kwargs["value"] = datetime.datetime.fromisoformat(  # type: ignore
#                         property["default"]
#                     )
#             with self._streamlit_container.container():
#                 if hasattr(property, "get") and not property.get("is_item"):
#                     self._streamlit_container.subheader(
#                         streamlit_kwargs.get("label"))
#                 if streamlit_kwargs.get("description"):
#                     self._streamlit_container.text(
#                         streamlit_kwargs.get("description"))
#                 selected_date = None
#                 selected_time = None

#                 # columns can not be used within a collection
#                 if property.get("is_item"):
#                     date_col = self._streamlit_container.container()
#                     time_col = self._streamlit_container.container()
#                 else:
#                     date_col, time_col = self._streamlit_container.columns(2)
#                 with date_col:
#                     date_kwargs = {
#                         "label": "Date",
#                         "key": f"{streamlit_kwargs.get('key')}-date-input",
#                     }
#                     if streamlit_kwargs.get("value"):
#                         with contextlib.suppress(Exception):
#                             date_kwargs["value"] = streamlit_kwargs.get(  # type: ignore
#                                 "value"
#                             ).date()
#                     selected_date = self._streamlit_container.date_input(
#                         **date_kwargs)

#                 with time_col:
#                     time_kwargs = {
#                         "label": "Time",
#                         "key": f"{streamlit_kwargs.get('key')}-time-input",
#                     }
#                     if streamlit_kwargs.get("value"):
#                         with contextlib.suppress(Exception):
#                             time_kwargs["value"] = streamlit_kwargs.get(  # type: ignore
#                                 "value"
#                             ).time()
#                     selected_time = self._streamlit_container.time_input(
#                         **time_kwargs)

#                 return datetime.datetime.combine(selected_date, selected_time)
#         else:
#             streamlit_app.warning(
#                 "Date format is not supported: " + str(property.get("format"))
#             )

#     def _render_single_file_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         file_extension = None
#         if "mime_type" in property:
#             file_extension = mimetypes.guess_extension(property["mime_type"])

#         uploaded_file = streamlit_app.file_uploader(
#             **{
#                 "label_visibility": "collapsed",
#                 **streamlit_kwargs,
#                 "accept_multiple_files": False,
#                 "type": file_extension,
#                 **overwrite_kwargs,
#             }
#         )
#         if uploaded_file is None:
#             return None
#         bytes = uploaded_file.getvalue()

#         if property.get("mime_type"):
#             if _is_compatible_audio(property["mime_type"]):
#                 # Show audio
#                 streamlit_app.audio(bytes, format=property.get("mime_type"))
#             if _is_compatible_image(property["mime_type"]):
#                 # Show image
#                 streamlit_app.image(bytes)
#             if _is_compatible_video(property["mime_type"]):
#                 # Show video
#                 streamlit_app.video(bytes, format=property.get("mime_type"))
#         return (bytes, uploaded_file.name)
#         # return uploaded_file

#     def _render_single_string_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)
#         if property.get("init_value"):
#             streamlit_kwargs["value"] = property.get("init_value")
#         elif property.get("default"):
#             streamlit_kwargs["value"] = property.get("default")
#         elif property.get("example"):
#             # TODO: also use example for other property types
#             # Use example as value if it is provided
#             streamlit_kwargs["value"] = property.get("example")

#         if property.get("maxLength") is not None:
#             streamlit_kwargs["max_chars"] = property.get("maxLength")

#         if property.get("readOnly"):
#             # Read only property -> only show value
#             streamlit_kwargs["disabled"] = property.get("readOnly", False)

#         if property.get("format") == "multi-line" and hasattr(property, "get") and not property.get("writeOnly"):
#             # Use text area if format is multi-line (custom definition)
#             return streamlit_app.text_area(**{**streamlit_kwargs, **overwrite_kwargs})
#         else:
#             # Use text input for most situations
#             if property.get("writeOnly"):
#                 streamlit_kwargs["type"] = "password"
#             return streamlit_app.text_input(**{**streamlit_kwargs, **overwrite_kwargs})

#     def _render_multi_enum_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         select_options: List[str] = []
#         if property.get("items").get("enum"):  # type: ignore
#             # Using Literal
#             select_options = property.get("items").get("enum")  # type: ignore
#         else:
#             # Using Enum
#             reference_item = schema_utils.resolve_reference(
#                 property["items"]["$ref"], self._schema_references
#             )
#             select_options = reference_item["enum"]

#         if property.get("init_value"):
#             streamlit_kwargs["default"] = property.get("init_value")
#         elif property.get("default"):
#             try:
#                 streamlit_kwargs["default"] = property.get("default")
#             except Exception:
#                 pass

#         return streamlit_app.multiselect(
#             **{**streamlit_kwargs, "options": select_options, **overwrite_kwargs}
#         )

#     # FIXME: enum type can not memorize the value when user click the button of prev
#     def _render_single_enum_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         select_options: List[str] = []
#         if property.get("enum"):
#             select_options = property.get("enum")  # type: ignore
#         else:
#             reference_item = schema_utils.get_single_reference_item(
#                 property, self._schema_references
#             )
#             select_options = reference_item["enum"]

#         index_cache_key = key + "-index"
#         if index_cache_key in st.session_state:
#             streamlit_kwargs["index"] = st.session_state.get(index_cache_key)
#         else:
#             if property.get("init_value"):
#                 streamlit_kwargs["index"] = select_options.index(
#                     property.get("init_value")  # type: ignore
#                 )
#             elif property.get("default") is not None:
#                 try:
#                     streamlit_kwargs["index"] = select_options.index(
#                         property.get("default")  # type: ignore
#                     )
#                 except Exception:
#                     # Use default selection
#                     pass
#         st.session_state[index_cache_key] = streamlit_kwargs["index"] if "index" in streamlit_kwargs else 0

#         # if there is only one option then there is no choice for the user to be make
#         # so simply return the value (This is relevant for discriminator properties)
#         if len(select_options) == 1:
#             return select_options[0]
#         else:
#             try:
#                 current_component = _get_current_ui_component(
#                     overwrite_kwargs, streamlit_app)
#                 return current_component(
#                     **{**streamlit_kwargs, "options": select_options, **overwrite_kwargs}
#                 )
#             except Exception:
#                 pass

#             render_type = property.get("render_type", "selectbox")
#             if render_type == "radio":
#                 return streamlit_app.radio(
#                     **{**streamlit_kwargs, "options": select_options, "horizontal": True, **overwrite_kwargs}
#                 )
#             else:
#                 return streamlit_app.selectbox(
#                     **{**streamlit_kwargs, "options": select_options, **overwrite_kwargs}
#                 )

#     def _render_single_dict_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:

#         # Add title and subheader
#         streamlit_app.subheader(property.get("title"))
#         if property.get("description"):
#             streamlit_app.markdown(property.get("description"))

#         if self._session_state[self._session_input_key].get(key, None):
#             data_dict = self._session_state[self._session_input_key].get(key, {})
#         elif property.get("init_value"):
#             data_dict = property.get("init_value")
#         elif property.get("default"):
#             data_dict = property.get("default")
#             if not isinstance(data_dict, dict):
#                 data_dict = {}
#         else:
#             data_dict = {}

#         is_object = True if property["additionalProperties"].get(
#             "$ref") else False

#         add_col, clear_col, _ = streamlit_app.columns(3)

#         add_col = add_col.empty()

#         if self._clear_button_allowed(property):
#             data_dict = self._render_dict_add_button(key, add_col, data_dict)

#         if self._clear_button_allowed(property):
#             data_dict = self._render_dict_clear_button(
#                 key, clear_col, data_dict)

#         new_dict = {}

#         for index, input_item in enumerate(data_dict.items()):

#             updated_key, updated_value = self._render_dict_item(
#                 streamlit_app,
#                 key,
#                 input_item,
#                 index,
#                 property,
#             )

#             if updated_key is not None and updated_value is not None:
#                 new_dict[updated_key] = updated_value

#             if is_object:
#                 streamlit_app.markdown("---")

#         if not is_object:
#             streamlit_app.markdown("---")

#         return new_dict

#     def _render_single_reference(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         reference_item = schema_utils.get_single_reference_item(
#             property, self._schema_references
#         )
#         return self._render_property(streamlit_app, key, reference_item)

#     def _render_union_property(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         from dp.launching.server.render.schema import __NOT_HANDLE_BY_FORM__
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         reference_items = schema_utils.get_union_references(
#             property, self._schema_references
#         )

#         # special handling when there are instance values and a discriminator property
#         # to differentiate between object types
#         if property.get("init_value") and property.get("discriminator"):
#             disc_prop = property["discriminator"]["propertyName"]
#             # find the index where the discriminator is equal to the init_value
#             ref_index = next(
#                 i
#                 for i, x in enumerate(reference_items)
#                 if x["properties"][disc_prop]["enum"]
#                 == [property["init_value"][disc_prop]]
#             )

#             # add any init_value properties to the corresponding reference item
#             reference_items[ref_index]["init_value"] = property["init_value"]
#             streamlit_kwargs["index"] = ref_index
#         elif property.get("init_value") and property.get("instance_class"):
#             ref_index = next(
#                 i
#                 for i, x in enumerate(reference_items)
#                 if x["title"] in property["instance_class"]
#             )
#             reference_items[ref_index]["init_value"] = property["init_value"]
#             streamlit_kwargs["index"] = ref_index

#         name_reference_mapping: Dict[str, Dict] = {}

#         for reference in reference_items:
#             import dict_deep
#             discriminator_name = dict_deep.deep_get(property, 'discriminator.propertyName')
#             custom_name = dict_deep.deep_get(
#                 reference,
#                 f'properties.{discriminator_name}.name'
#             )
#             if custom_name:
#                 reference_title = custom_name
#             else:
#                 reference_title = _name_to_title(reference["title"])
#             name_reference_mapping[reference_title] = reference
#         if "label_visibility" not in property or property["label_visibility"] != "hidden":
#             streamlit_app.subheader(streamlit_kwargs["label"])  # type: ignore
#         if "help" in streamlit_kwargs:
#             streamlit_app.markdown(streamlit_kwargs["help"])

#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)
#         selected_reference = None
#         try:
#             current_component = _get_current_ui_component(
#                 overwrite_kwargs, streamlit_app)
#             selected_reference = current_component(
#                 **{
#                     **streamlit_kwargs,
#                     "label": streamlit_kwargs["label"] + " - Options",
#                     "options": name_reference_mapping.keys(),
#                 }
#             )
#         except Exception:
#             selected_reference = streamlit_app.selectbox(
#                 **{
#                     **streamlit_kwargs,
#                     "label": streamlit_kwargs["label"] + " - Options",
#                     "options": name_reference_mapping.keys(),
#                 }
#             )

#         key = key + "-" + selected_reference
#         prev_data = self._session_state[self._session_input_key].get(key, None)
#         if isinstance(prev_data, __NOT_HANDLE_BY_FORM__):
#             self._session_state[self._session_input_key][key] = prev_data.get_value()
#         input_data = self._render_object_input(
#                 streamlit_app, key, name_reference_mapping[selected_reference]
#             )
#         self._session_state[self._session_input_key][key] = __NOT_HANDLE_BY_FORM__(input_data)
#         streamlit_app.markdown("---")
#         return input_data

#     def _render_multi_file_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         file_extension = None
#         if "mime_type" in property:
#             file_extension = mimetypes.guess_extension(property["mime_type"])

#         uploaded_files = streamlit_app.file_uploader(
#             **{
#                 "label_visibility": "collapsed",
#                 **streamlit_kwargs,
#                 "accept_multiple_files": True,
#                 "type": file_extension,
#                 **overwrite_kwargs,
#             }
#         )
#         uploaded_files_bytes = []
#         if uploaded_files:
#             for uploaded_file in uploaded_files:
#                 uploaded_files_bytes.append(uploaded_file.read())
#         return uploaded_files_bytes

#     def _render_single_boolean_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         if property.get("init_value"):
#             streamlit_kwargs["value"] = property.get("init_value")
#         elif property.get("default"):
#             streamlit_kwargs["value"] = property.get("default")

#         # special formatting when rendering within a list/dict
#         if property.get("is_item"):
#             streamlit_app.markdown("##")

#         return streamlit_app.checkbox(**{**streamlit_kwargs, **overwrite_kwargs})

#     def _render_single_number_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         number_transform = int
#         if property.get("type") == "number":
#             number_transform = float  # type: ignore
#             streamlit_kwargs["format"] = "%f"

#         if "multipleOf" in property:
#             # Set stepcount based on multiple of parameter
#             streamlit_kwargs["step"] = number_transform(property["multipleOf"])
#         elif number_transform == int:
#             # Set step size to 1 as default
#             streamlit_kwargs["step"] = 1
#         elif number_transform == float:
#             # Set step size to 0.01 as default
#             # TODO: adapt to default value
#             streamlit_kwargs["step"] = 0.01

#         if "minimum" in property:
#             streamlit_kwargs["min_value"] = number_transform(
#                 property["minimum"])
#         if "exclusiveMinimum" in property:
#             streamlit_kwargs["min_value"] = number_transform(
#                 property["exclusiveMinimum"] + streamlit_kwargs["step"]
#             )
#         if "maximum" in property:
#             streamlit_kwargs["max_value"] = number_transform(
#                 property["maximum"])

#         if "exclusiveMaximum" in property:
#             streamlit_kwargs["max_value"] = number_transform(
#                 property["exclusiveMaximum"] - streamlit_kwargs["step"]
#             )

#         if self._session_state.get(streamlit_kwargs["key"]) is None:
#             if property.get("init_value") is not None:
#                 streamlit_kwargs["value"] = number_transform(
#                     property["init_value"])
#             elif property.get("default") is not None:
#                 streamlit_kwargs["value"] = number_transform(
#                     property["default"])  # type: ignore
#             else:
#                 if "min_value" in streamlit_kwargs:
#                     streamlit_kwargs["value"] = streamlit_kwargs["min_value"]
#                 elif number_transform == int:
#                     streamlit_kwargs["value"] = 0
#                 else:
#                     # Set default value to step
#                     streamlit_kwargs["value"] = number_transform(
#                         streamlit_kwargs["step"]
#                     )
#         else:
#             streamlit_kwargs["value"] = number_transform(
#                 self._session_state[streamlit_kwargs["key"]]
#             )

#         if "min_value" in streamlit_kwargs and "max_value" in streamlit_kwargs:
#             # TODO: Only if less than X steps
#             return streamlit_app.slider(**{**streamlit_kwargs, **overwrite_kwargs})
#         else:
#             return streamlit_app.number_input(
#                 **{**streamlit_kwargs, **overwrite_kwargs}
#             )

#     def _render_object_input(self, streamlit_app: Any, key: str, property: Dict) -> Any:
#         properties = property["properties"]
#         object_inputs = {}
#         for property_key in properties:
#             new_property = properties[property_key]
#             if not new_property.get("title"):
#                 # Set property key as fallback title
#                 new_property["title"] = _name_to_title(property_key)
#             # construct full key based on key parts -> required later to get the value
#             full_key = key + "." + property_key

#             if property.get("init_value"):
#                 new_property["init_value"] = property["init_value"].get(
#                     property_key)

#             new_property["readOnly"] = property.get("readOnly", False)

#             value = self._render_property(
#                 streamlit_app, full_key, new_property)
#             if not self._is_value_ignored(property_key, value):
#                 object_inputs[property_key] = value

#         return object_inputs

#     def _render_single_object_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         # Add title and subheader
#         title = property.get("title")
#         if property.get("is_item"):
#             streamlit_app.caption(title)
#         else:
#             streamlit_app.subheader(title)
#         if property.get("description"):
#             streamlit_app.markdown(property.get("description"))

#         object_reference = schema_utils.get_single_reference_item(
#             property, self._schema_references
#         )

#         object_reference["init_value"] = property.get("init_value", None)

#         object_reference["readOnly"] = property.get("readOnly", None)

#         return self._render_object_input(streamlit_app, key, object_reference)

#     def _render_list_item(
#         self,
#         streamlit_app: Any,
#         parent_key: str,
#         value: Any,
#         index: int,
#         property: Dict[str, Any],
#     ) -> Any:

#         label = "Item #" + str(index + 1)
#         new_key = self._key + "-" + parent_key + "." + str(index)
#         item_placeholder = streamlit_app.empty()

#         with item_placeholder:

#             input_col, button_col = streamlit_app.columns([8, 3])

#             button_col.markdown("##")

#             if self._remove_button_allowed(index, property):
#                 remove = False
#             else:
#                 remove = button_col.button("Remove", key=new_key + "-remove")

#             #  insert an input field when the remove button has not been clicked
#             if not remove:
#                 with input_col:
#                     new_property = {
#                         "title": label,
#                         "init_value": value if value else None,
#                         "is_item": True,
#                         "readOnly": property.get("readOnly"),
#                         **property["items"],
#                     }
#                     return self._render_property(streamlit_app, new_key, new_property)

#             else:
#                 # when the remove button is clicked clear the placeholder and return None
#                 item_placeholder.empty()
#                 return None

#     def _render_dict_item(
#         self,
#         streamlit_app: Any,
#         parent_key: str,
#         in_value: Tuple[str, Any],
#         index: int,
#         property: Dict[str, Any],
#     ) -> Any:

#         new_key = self._key + "-" + parent_key + "." + str(index)
#         item_placeholder = streamlit_app.empty()

#         with item_placeholder.container():

#             key_col, value_col, button_col = streamlit_app.columns([4, 4, 3])

#             dict_key = in_value[0]
#             dict_value = in_value[1]

#             dict_key_key = new_key + "-key"
#             dict_value_key = new_key + "-value"

#             button_col.markdown("##")

#             if self._remove_button_allowed(index, property):
#                 remove = False
#             else:
#                 remove = button_col.button("Remove", key=new_key + "-remove")

#             if not remove:
#                 with key_col:
#                     updated_key = streamlit_app.text_input(
#                         "Key",
#                         value=dict_key,
#                         key=dict_key_key,
#                         disabled=property.get("readOnly", False),
#                     )

#                 with value_col:
#                     new_property = {
#                         "title": "Value",
#                         "init_value": dict_value,
#                         "is_item": True,
#                         "readOnly": property.get("readOnly"),
#                         **property["additionalProperties"],
#                     }
#                     with value_col:
#                         updated_value = self._render_property(
#                             streamlit_app, dict_value_key, new_property
#                         )

#                     return updated_key, updated_value

#             else:
#                 # when the remove button is clicked clear the placeholder and return None
#                 item_placeholder.empty()
#                 return None, None

#     def _add_button_allowed(
#         self,
#         index: int,
#         property: Dict[str, Any],
#     ) -> bool:
#         add_allowed = not (
#             (property.get("readOnly", False) is True)
#             or ((index) >= property.get("maxItems", 1000))
#         )

#         return add_allowed

#     def _remove_button_allowed(
#         self,
#         index: int,
#         property: Dict[str, Any],
#     ) -> bool:
#         remove_allowed = (property.get("readOnly") is True) or (
#             (index + 1) <= property.get("minItems", 0)
#         )

#         return remove_allowed

#     def _clear_button_allowed(
#         self,
#         property: Dict[str, Any],
#     ) -> bool:
#         clear_allowed = not (
#             (property.get("readOnly", False) is True)
#             or (property.get("minItems", 0) > 0)
#         )

#         return clear_allowed

#     def _render_list_add_button(
#         self,
#         key: str,
#         streamlit_app: Any,
#         data_list: List[Any],
#     ) -> List[Any]:
#         if streamlit_app.button(
#             "Add Item",
#             key=self._key + "-" + key + "list-add-item",
#             use_container_width=True,
#         ):
#             data_list.append(None)

#         return data_list

#     def _render_list_clear_button(
#         self,
#         key: str,
#         streamlit_app: Any,
#         data_list: List[Any],
#     ) -> List[Any]:
#         if streamlit_app.button(
#             "Clear All",
#             key=self._key + "_" + key + "-list_clear-all",
#             use_container_width=True,
#         ):
#             data_list = []

#         return data_list

#     def _render_dict_add_button(
#         self, key: str, streamlit_app: Any, data_dict: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         if streamlit_app.button(
#             "Add Item",
#             key=self._key + "-" + key + "-add-item",
#             use_container_width=True,
#         ):
#             data_dict[str(len(data_dict) + 1)] = None

#         return data_dict

#     def _render_dict_clear_button(
#         self,
#         key: str,
#         streamlit_app: Any,
#         data_dict: Dict[str, Any],
#     ) -> Dict[str, Any]:
#         if streamlit_app.button(
#             "Clear All",
#             key=self._key + "-" + key + "-clear-all",
#             use_container_width=True,
#         ):
#             data_dict = {}

#         return data_dict

#     def _render_list_input(self, streamlit_app: Any, key: str, property: Dict) -> Any:

#         # Add title and subheader
#         streamlit_app.subheader(property.get("title"))
#         if property.get("description"):
#             streamlit_app.markdown(property.get("description"))

#         is_object = True if property["items"].get("$ref") else False

#         object_list = []

#         # Treat empty list as a session data "hit"
#         if self._session_state[self._session_input_key].get(key, None):
#             data_list = self._session_state[self._session_input_key].get(key, [])
#         elif property.get("init_value"):
#             data_list = property.get("init_value")
#         elif property.get("default"):
#             data_list = property.get("default")
#             if not isinstance(data_list, list):
#                 data_list = []
#         else:
#             data_list = []

#         add_col, clear_col, _ = streamlit_app.columns(3)

#         add_col = add_col.empty()

#         self._render_list_add_button(key, add_col, data_list)

#         if self._clear_button_allowed(property):
#             data_list = self._render_list_clear_button(
#                 key, clear_col, data_list)

#         if len(data_list) > 0:
#             for index, item in enumerate(data_list):
#                 output = self._render_list_item(
#                     streamlit_app,
#                     key,
#                     item,
#                     index,
#                     property,
#                 )
#                 if output is not None:
#                     object_list.append(output)

#                 if is_object:
#                     streamlit_app.markdown("---")

#             if not self._add_button_allowed(len(object_list), property):
#                 add_col = add_col.empty()

#             if not is_object:
#                 streamlit_app.markdown("---")

#         return object_list

#     def _internal_type_render(self, streamlit_app: Any, key: str, property: Dict):
#         if hasattr(self, "_type_filter"):
#             tmp = {
#                 "scope": "",
#                 "type": "",
#                 "format": "",
#             }
#             "scope" in property and tmp.update({"scope": property["scope"]})
#             "type" in property and tmp.update({"type": property["type"]})
#             "format" in property and tmp.update({"format": property["format"]})
#             try:
#                 bypass, default = self._type_filter(
#                     key, property, tmp["type"], tmp["format"], tmp["scope"])
#                 if bypass:
#                     return default

#             except Exception as err:
#                 ...

#         if hasattr(self, "_type_default"):
#             is_set, default = self._type_default(
#                 key, property, tmp["type"], tmp["format"], tmp["scope"])
#             is_set and default != None and property.setdefault('default', default)

#         if schema_utils.internal.is_bohrium_job_type_property(property):
#             return self._internal_render_bohrium_job_type_input(streamlit_app, key, property)

#         if schema_utils.internal.is_bohrium_platform_property(property):
#             return self._internal_render_bohrium_platform_input(streamlit_app, key, property)

#         if schema_utils.internal.is_bohrium_machine_type_property(property):
#             return self._internal_render_bohrium_machine_type_input(streamlit_app, key, property)

#         if schema_utils.internal.is_output_directory_property(property):
#             return self._internal_render_output_directory_input(streamlit_app, key, property)

#         if schema_utils.internal.is_single_file_with_name_property(property):
#             return self._internal_render_single_file_with_name_input(streamlit_app, key, property)

#         if schema_utils.internal.is_multi_file_with_name_property(property):
#             return self._internal_render_multi_file_with_name_input(streamlit_app, key, property)

#         if schema_utils.internal.is_datahub_datasets_select_property(property):
#             return self._internal_render_datahub_input('datasets', streamlit_app, key, property)

#         if schema_utils.internal.is_datahub_models_select_property(property):
#             return self._internal_render_datahub_input('models', streamlit_app, key, property)

#         return None

#     def _internal_render_bohrium_job_type_input(self, streamlit_app: Any, key: str, property: Dict):
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         from dp.launching.typing.bohrium import BohriumJobType
#         internale_default_value = BohriumJobType.__get_default_options__(
#             BohriumJobType)

#         default = internale_default_value[0]
#         index = 0
#         if property.get("default"):
#             default = property.get("default")
#             index = internale_default_value.index(default)

#         res = streamlit_app.selectbox(
#             **{**streamlit_kwargs, "options": internale_default_value, "index": index, **overwrite_kwargs}
#         )
#         return res

#     def _internal_render_bohrium_platform_input(self, streamlit_app: Any, key: str, property: Dict):
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         from dp.launching.typing.bohrium import BohriumPlatform
#         internale_default_value = BohriumPlatform.__get_default_options__(
#             BohriumPlatform)

#         default = internale_default_value[0]
#         index = 0
#         if property.get("default"):
#             default = property.get("default")
#             index = internale_default_value.index(default)

#         res = streamlit_app.selectbox(
#             **{**streamlit_kwargs, "options": internale_default_value, "index": index, **overwrite_kwargs}
#         )
#         return res

#     def _internal_render_bohrium_machine_type_input(self, streamlit_app: Any, key: str, property: Dict):
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         multiple = property.get("multiple", False)

#         default = "c2_m2_cpu"
#         if property.get("default"):
#             default = property.get("default")

#         st.write('Bohrium Machine Type')
#         res = st_machine_select(default=default, multiple=multiple, **{**streamlit_kwargs})
#         return res

#     def _internal_render_multi_file_with_name_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         file_extension = property["ftypes"] if "ftypes" in property else None
#         if "mime_type" in property:
#             file_extension = mimetypes.guess_extension(property["mime_type"])
#         uploaded_files = streamlit_app.file_uploader(
#             **{
#                 "label_visibility": "collapsed",
#                 **streamlit_kwargs,
#                 "accept_multiple_files": True,
#                 "type": file_extension,
#                 **overwrite_kwargs,
#             }
#         )
#         uploaded_files_arr = []
#         if uploaded_files:
#             for uploaded_file in uploaded_files:
#                 uploaded_files_arr.append(
#                     {"content": uploaded_file.read(), "name": uploaded_file.name})
#         # return uploaded_files_bytes
#         return uploaded_files_arr



#     def _internal_render_datahub_input(
#         self, type: str, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)

#         from dp.launching.server.common.components.streamlit_datahub_select import \
#             st_datahub_select
#         endpoint = 'https://datahub-gms.dp.tech'
#         token = os.getenv('DATAHUB_TOKEN')
#         rest = {}
#         'is_multi' in property and rest.update({'is_multi': property['is_multi']})
#         'count' in property and rest.update({'count': property['count']})
#         'show_size' in property and rest.update({'show_size': property['show_size']})
#         'show_type' in property and rest.update({'show_type': property['show_type']}) 
#         'default_tags' in property and rest.update({'default_tags': property['default_tags']})
#         'default_search' in property and rest.update({'default_search': property['default_search']})
#         'default_group' in property and rest.update({'default_group': property['default_group']})

#         st.write(f'*{key}*')
#         res = st_datahub_select(key, endpoint, token, type=type, **rest)
#         return res


#     def _internal_render_single_file_with_name_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         streamlit_kwargs = self._get_default_streamlit_input_kwargs(
#             key, property)
#         overwrite_kwargs = self._get_overwrite_streamlit_kwargs(key, property)
#         file_extension = property["ftypes"] if "ftypes" in property else None

#         if "mime_type" in property:
#             file_extension = mimetypes.guess_extension(property["mime_type"])

#         uploaded_file = streamlit_app.file_uploader(
#             **{
#                 "label_visibility": "collapsed",
#                 **streamlit_kwargs,
#                 "accept_multiple_files": False,
#                 "type": file_extension,
#                 **overwrite_kwargs,
#             }
#         )
#         if uploaded_file is None:
#             # return None
#             return {}
#         bytes = uploaded_file.getvalue()
#         if property.get("mime_type"):
#             if _is_compatible_audio(property["mime_type"]):
#                 # Show audio
#                 streamlit_app.audio(bytes, format=property.get("mime_type"))
#             if _is_compatible_image(property["mime_type"]):
#                 # Show image
#                 streamlit_app.image(bytes)
#             if _is_compatible_video(property["mime_type"]):
#                 # Show video
#                 streamlit_app.video(bytes, format=property.get("mime_type"))
#         return {"content": bytes, "name": uploaded_file.name}

#     def _internal_render_output_directory_input(
#         self, streamlit_app: Any, key: str, property: Dict
#     ) -> Any:
#         return './outputs'

#     def _render_property(self, streamlit_app: Any, key: str, property: Dict) -> Any:
#         internal_state = self._internal_type_render(
#             streamlit_app, key, property)
#         if internal_state != None:
#             return internal_state

#         if schema_utils.is_single_enum_property(property, self._schema_references):
#             return self._render_single_enum_input(streamlit_app, key, property)

#         if schema_utils.is_multi_enum_property(property, self._schema_references):
#             return self._render_multi_enum_input(streamlit_app, key, property)

#         if schema_utils.is_single_file_property(property):
#             return self._render_single_file_input(streamlit_app, key, property)

#         if schema_utils.is_multi_file_property(property):
#             return self._render_multi_file_input(streamlit_app, key, property)

#         if schema_utils.is_single_datetime_property(property):
#             return self._render_single_datetime_input(streamlit_app, key, property)

#         if schema_utils.is_single_boolean_property(property):
#             return self._render_single_boolean_input(streamlit_app, key, property)

#         if schema_utils.is_single_dict_property(property):
#             return self._render_single_dict_input(streamlit_app, key, property)

#         if schema_utils.is_single_number_property(property):
#             return self._render_single_number_input(streamlit_app, key, property)

#         if schema_utils.is_single_string_property(property):
#             return self._render_single_string_input(streamlit_app, key, property)

#         if schema_utils.is_single_object(property, self._schema_references):
#             return self._render_single_object_input(streamlit_app, key, property)

#         if schema_utils.is_object_list_property(property, self._schema_references):
#             return self._render_list_input(streamlit_app, key, property)

#         if schema_utils.is_property_list(property):
#             return self._render_list_input(streamlit_app, key, property)

#         if schema_utils.is_single_reference(property):
#             return self._render_single_reference(streamlit_app, key, property)

#         if schema_utils.is_union_property(property):
#             return self._render_union_property(streamlit_app, key, property)

#         streamlit_app.warning(
#             "The type of the following property is currently not supported: "
#             + str(property.get("title"))
#         )
#         raise Exception("Unsupported property")


# class SchemaInputUI(InputUI):

#     def __init__(
#         self,
#         key: str,
#         schema_properties: dict,
#         schema_references: dict,
#         required_properties: list,
#         streamlit_container: Any = st,
#         group_optional_fields: GroupOptionalFieldsStrategy = "no",  # type: ignore
#         lowercase_labels: bool = False,
#         ignore_empty_values: bool = False,
#         **kwargs,
#     ):
#         super().__init__(
#             key,
#             None,
#             streamlit_container,
#             group_optional_fields,
#             lowercase_labels,
#             ignore_empty_values,
#             **kwargs,
#         )
#         self._schema_properties = schema_properties
#         self._schema_references = schema_references
#         self._required_properties = required_properties


# class OutputUI:
#     """Output UI renderer.

#     lazydocs: ignore
#     """

#     def __init__(self, output_data: Any, input_data: Optional[Any] = None, **kwargs):
#         self._output_data = output_data
#         self._input_data = input_data

#     def render_ui(self) -> None:
#         try:
#             if isinstance(self._output_data, BaseModel):
#                 self._render_single_output(st, self._output_data)
#                 return
#             if type(self._output_data) == list:
#                 self._render_list_output(st, self._output_data)
#                 return
#         except Exception as ex:
#             from dp.launching.server.models.base import is_sso_login
#             if is_sso_login():
#                 st.exception(ex)
#             # TODO: Fallback to
#             # st.json(jsonable_encoder(self._output_data))

#     def _render_single_text_property(
#         self, streamlit: Any, property_schema: Dict, value: Any
#     ) -> None:
#         # Add title and subheader
#         streamlit.subheader(property_schema.get("title"))
#         if property_schema.get("description"):
#             streamlit.markdown(property_schema.get("description"))
#         if value is None or value == "":
#             streamlit.info("No value returned!")
#         else:
#             streamlit.code(str(value), language="plain")

#     def _render_single_file_property(
#         self, streamlit: Any, property_schema: Dict, value: Any
#     ) -> None:
#         # Add title and subheader
#         streamlit.subheader(property_schema.get("title"))
#         if property_schema.get("description"):
#             streamlit.markdown(property_schema.get("description"))
#         if value is None or value == "":
#             streamlit.info("No value returned!")
#         else:
#             # TODO: Detect if it is a FileContent instance
#             # TODO: detect if it is base64
#             file_extension = ""
#             if "mime_type" in property_schema:
#                 mime_type = property_schema["mime_type"]
#                 file_extension = mimetypes.guess_extension(mime_type) or ""

#                 if _is_compatible_audio(mime_type):
#                     streamlit.audio(value.as_bytes(), format=mime_type)
#                     return

#                 if _is_compatible_image(mime_type):
#                     streamlit.image(value.as_bytes())
#                     return

#                 if _is_compatible_video(mime_type):
#                     streamlit.video(value.as_bytes(), format=mime_type)
#                     return

#             filename = (
#                 (property_schema["title"] + file_extension)
#                 .lower()
#                 .strip()
#                 .replace(" ", "-")
#             )
#             streamlit.markdown(
#                 f'<a href="data:application/octet-stream;base64,{value}" download="{filename}"><input type="button" value="Download File"></a>',
#                 unsafe_allow_html=True,
#             )

#     def _render_single_complex_property(
#         self, streamlit: Any, property_schema: Dict, value: Any
#     ) -> None:
#         # Add title and subheader
#         streamlit.subheader(property_schema.get("title"))
#         if property_schema.get("description"):
#             streamlit.markdown(property_schema.get("description"))

#         streamlit.json(json.dumps(value, default=pydantic_encoder))

#     def _render_single_output(self, streamlit: Any, output_data: BaseModel) -> None:
#         try:
#             if _has_output_ui_renderer(output_data):
#                 # type: ignore
#                 if _function_has_named_arg(output_data.render_output_ui, "input"):
#                     # render method also requests the input data
#                     output_data.render_output_ui(
#                         streamlit, input=self._input_data)  # type: ignore
#                 else:
#                     output_data.render_output_ui(streamlit)  # type: ignore
#                 return
#         except Exception:
#             # TODO
#             pass
#             # Use default auto-generation methods if the custom rendering throws an exception
#             # logger.exception(
#             #    "Failed to execute custom render_output_ui function. Using auto-generation instead"
#             # )

#         model_schema = output_data.schema(by_alias=False)
#         model_properties = model_schema.get("properties")
#         definitions = model_schema.get("definitions")

#         if model_properties:
#             for property_key in output_data.__dict__:
#                 property_schema = model_properties.get(property_key)
#                 if not property_schema.get("title"):
#                     # Set property key as fallback title
#                     property_schema["title"] = property_key

#                 output_property_value = output_data.__dict__[property_key]

#                 if _has_output_ui_renderer(output_property_value):
#                     output_property_value.render_output_ui(
#                         streamlit)  # type: ignore
#                     continue

#                 if isinstance(output_property_value, BaseModel):
#                     # Render output recursivly
#                     streamlit.subheader(property_schema.get("title"))
#                     if property_schema.get("description"):
#                         streamlit.markdown(property_schema.get("description"))
#                     self._render_single_output(
#                         streamlit, output_property_value)
#                     continue

#                 if property_schema:
#                     if schema_utils.is_single_file_property(property_schema):
#                         self._render_single_file_property(
#                             streamlit, property_schema, output_property_value
#                         )
#                         continue

#                     if (
#                         schema_utils.is_single_string_property(property_schema)
#                         or schema_utils.is_single_number_property(property_schema)
#                         or schema_utils.is_single_datetime_property(property_schema)
#                         or schema_utils.is_single_boolean_property(property_schema)
#                     ):
#                         self._render_single_text_property(
#                             streamlit, property_schema, output_property_value
#                         )
#                         continue
#                     if definitions and schema_utils.is_single_enum_property(
#                         property_schema, definitions
#                     ):
#                         self._render_single_text_property(
#                             streamlit, property_schema, output_property_value.value
#                         )
#                         continue

#                     # TODO: render dict as table

#                     self._render_single_complex_property(
#                         streamlit, property_schema, output_property_value
#                     )
#             return

#         # Display single field in code block:
#         # if len(output_data.__dict__) == 1:
#         #     value = next(iter(output_data.__dict__.values()))

#         #     if type(value) in (int, float, str):
#         #         # Should not be a complex object (with __dict__) -> should be a primitive
#         #         # hasattr(output_data.__dict__[0], '__dict__')
#         #         streamlit.subheader("This is a test:")
#         #         streamlit.code(value, language="plain")
#         #         return

#         st.error("Cannot render output")
#         # TODO: Fallback to json output
#         # streamlit.json(jsonable_encoder(output_data))

#     def _render_list_output(self, streamlit: Any, output_data: List) -> None:
#         try:
#             data_items: List = []
#             for data_item in output_data:
#                 if _has_output_ui_renderer(data_item):
#                     # Render using the render function
#                     data_item.render_output_ui(streamlit)  # type: ignore
#                     continue
#                 data_items.append(data_item.dict())
#             # Try to show as dataframe
#             streamlit.table(pd.DataFrame(data_items))
#         except Exception:
#             st.error("Cannot render output list")
#             # TODO Fallback to
#             # streamlit.json(jsonable_encoder(output_data))


# def pydantic_input(
#     key: str,
#     model: Type[BaseModel],
#     group_optional_fields: GroupOptionalFieldsStrategy = "no",  # type: ignore
#     lowercase_labels: bool = False,
#     ignore_empty_values: bool = False,
#     **kwargs,
# ) -> Dict:
#     """Auto-generates input UI elements for a selected Pydantic class.

#     Args:
#         key (str): A string that identifies the form. Each form must have its own key.
#         model (Type[BaseModel]): The input model. Either a class or instance based on Pydantic `BaseModel` or Python `dataclass`.
#         group_optional_fields (str, optional): If `sidebar`, optional input elements will be rendered on the sidebar.
#             If `expander`,  optional input elements will be rendered inside an expander element. Defaults to `no`.
#         lowercase_labels (bool): If `True`, all input element labels will be lowercased. Defaults to `False`.
#         ignore_empty_values (bool): If `True`, empty values for strings and numbers will not be stored in the session state. Defaults to `False`.

#     Returns:
#         Dict: A dictionary with the current state of the input data.
#     """
#     state = InputUI(
#         key,
#         model,
#         group_optional_fields=group_optional_fields,
#         lowercase_labels=lowercase_labels,
#         ignore_empty_values=ignore_empty_values,
#         **kwargs,
#     ).render_ui()

#     return state


# def pydantic_input_by_schema(
#     key: str,
#     schema_properties: dict,
#     schema_references: dict,
#     required_properties: list,
#     group_optional_fields: GroupOptionalFieldsStrategy = "no",  # type: ignore
#     lowercase_labels: bool = False,
#     ignore_empty_values: bool = False,
#     **kwargs,
# ) -> Dict:
#     """Auto-generates input UI elements for a selected Pydantic class.

#     Args:
#         key (str): A string that identifies the form. Each form must have its own key.
#         model (Type[BaseModel]): The input model. Either a class or instance based on Pydantic `BaseModel` or Python `dataclass`.
#         group_optional_fields (str, optional): If `sidebar`, optional input elements will be rendered on the sidebar.
#             If `expander`,  optional input elements will be rendered inside an expander element. Defaults to `no`.
#         lowercase_labels (bool): If `True`, all input element labels will be lowercased. Defaults to `False`.
#         ignore_empty_values (bool): If `True`, empty values for strings and numbers will not be stored in the session state. Defaults to `False`.

#     Returns:
#         Dict: A dictionary with the current state of the input data.
#     """
#     return SchemaInputUI(
#         key,
#         schema_properties,
#         schema_references,
#         required_properties,
#         group_optional_fields=group_optional_fields,
#         lowercase_labels=lowercase_labels,
#         ignore_empty_values=ignore_empty_values,
#         **kwargs,
#     ).render_ui()


# def pydantic_output(output_data: Any, **kwargs) -> None:
#     """Auto-generates output UI elements for all properties of a (Pydantic-based) model instance.

#     Args:
#         output_data (Any): The output data.
#     """

#     OutputUI(output_data, **kwargs).render_ui()


# class PydanticRenderStepModelTypes:
#     def __init__(
#         self,
#         application=None, application_manager=None,
#         job=None, job_manager=None, job_status=None,
#         version=None, version_status=None, version_manager=None,
#         user=None, user_manager=None,
#         events=None,
#     ) -> None:
#         self.application = application
#         self.application_manager = application_manager
#         self.job = job
#         self.job_manager = job_manager
#         self.job_status = job_status
#         self.version = version
#         self.version_status = version_status
#         self.version_manager = version_manager
#         self.user = user
#         self.user_manager = user_manager
#         self.events = events


# def pydantic_input_steps(
#     schemas,
#     router=None,
#     sub_model=None,
#     session_prefix=None,
#     **kwargs,
# ):
#     invisible_fn = kwargs['invisible'] if 'invisible' in kwargs else lambda _, __: True
#     from streamlit_router import StreamlitRouter
#     router: StreamlitRouter = router

#     params: Dict = router.get_request_state('main_submit_form', defaultdict())
#     for i in range(3):
#         params.setdefault(i, defaultdict())
#     schema_properties = schemas.schema_properties
#     schema_references = schemas.schema_references
#     required_properties = schemas.required_properties
#     schemas_description = schemas.description

#     from copy import deepcopy
#     saved_schema_properties = deepcopy(schema_properties)
#     schemas = {
#         0: defaultdict(dict),
#         1: defaultdict(dict),
#         2: defaultdict(dict),
#     }
#     for key, schema in schema_properties.items():
#         if schema.get('scope') == 'io' or (schema.get('type') == 'array' and schema.get('items', {}).get('scope') == 'io'):
#             if key in params[0]:
#                 schema['default'] = params[0][key]
#             schemas[0][key] = schema
#     for key, schema in schema_properties.items():
#         if schema.get('scope') == 'executor' or (schema.get('type') == 'array' and schema.get('items', {}).get('scope') == 'executor'):
#             if key in params[2]:
#                 schema['default'] = params[2][key]
#             schemas[2][key] = schema
#     for key, schema in schema_properties.items():
#         if (not schema.get('scope') and schema.get('type') != 'array') or (schema.get('type') == 'array' and not schema.get('items', {}).get('scope')):
#             if key in params[1]:
#                 schema['default'] = params[1][key]
#             schemas[1][key] = schema

#     items = [
#         Item('IO Options', 'Configure job input files by upload from local or choose from workspace'),
#         Item('Job Options', 'Setting values for variables such as filters, algorithms, or model parameters'),
#         Item('System Options', 'Configure system-level parameters that affect the behavior of the application or platform being used to run the task'),
#         Item('Review', 'Summary of all the parameters you have configured so far'),
#     ]

#     def render_step(step: int):
#         ok_next = True
#         application = kwargs.get("application", None)
#         version = kwargs.get("version", None)
#         if step < 3:
#             if step == 2:
#                 is_access_from_labs = access_from_labs()
#                 exposed_versions_config = application.exposed_versions_config if is_access_from_labs and hasattr(application, 'exposed_versions_config') else None
#                 borhium_info = version and exposed_versions_config and hasattr(version, 'name') and (version.name in exposed_versions_config) and exposed_versions_config[version.name]
#                 borhium_info = borhium_info and (sub_model in borhium_info) and borhium_info[sub_model]
#                 borhium_basic_info = isinstance(borhium_info, dict) and 'basic' in borhium_info and borhium_info['basic']
#                 basic_machine_type = borhium_basic_info and 'machine_type' in borhium_basic_info and borhium_basic_info['machine_type']
#                 basic_job_type = borhium_basic_info and 'job_type' in borhium_basic_info and borhium_basic_info['job_type']
#                 basic_platform = borhium_basic_info and 'platform' in borhium_basic_info and borhium_basic_info['platform']
#                 borhium_dflow_info = isinstance(borhium_info, dict) and 'dflow' in borhium_info and borhium_info['dflow']
#                 # dflow_machine_type = borhium_dflow_info and 'machine_type' in borhium_dflow_info and borhium_dflow_info['machine_type']
#                 # dflow_job_type = borhium_dflow_info and 'job_type' in borhium_dflow_info and borhium_dflow_info['job_type']
#                 # dflow_platform = borhium_dflow_info and 'platform' in borhium_dflow_info and borhium_dflow_info['platform']
                
#                 st.markdown('##### Bohrium Options')
#                 from dp.launching.typing.bohrium import (BohriumJobType,
#                                                          BohriumMachineType,
#                                                          BohriumPlatform)

#                 # machine_options = BohriumMachineType().__get_default_options__()
#                 platform_options = BohriumPlatform().__get_default_options__()
#                 job_options = BohriumJobType().__get_default_options__()

#                 default_machine_type = (application and application.bohrium_machine_type_default) or 'c2_m2_cpu'
#                 saved_value = params[step].get('__SYSTEM_SUBMIT_BOHRIUM_MACHINE_TYPE__', default_machine_type)

#                 st.write("Bohrium Machine Type")
#                 bohrium_machine_type = st_machine_select(
#                     key=f"{session_prefix}-{sub_model}-{version and version.name}-bohrium-machine-type",
#                     default=basic_machine_type or saved_value if is_access_from_labs else saved_value,
#                     multiple=False,
#                     disabled=is_access_from_labs,
#                 )

#                 bohrium_platform_default = (application and application.bohrium_platform_default) or platform_options[0]
#                 saved_value = params[step].get('__SYSTEM_SUBMIT_BOHRIUM_PLATFORM__', bohrium_platform_default)
#                 index = platform_options.index(basic_platform) if is_access_from_labs and basic_platform in platform_options else \
#                     platform_options.index(saved_value) if saved_value else 0
            
#                 bohrium_platform = st.selectbox('Bohrium Platform', platform_options, disabled=is_access_from_labs, index=index, help="The platform on which bohrium runs, currently supports ali and paratera.",
#                                                 key=f'{session_prefix}-{sub_model}-{version and version.name}-bohrium-platform')

#                 bohrium_job_type_default = (application and application.bohrium_job_type_default) or job_options[0]
#                 saved_value = params[step].get('__SYSTEM_SUBMIT_BOHRIUM_JOB_TYPE__', bohrium_job_type_default)
#                 index = job_options.index(basic_job_type) if is_access_from_labs and basic_job_type in job_options else \
#                     job_options.index(saved_value) if saved_value else 0

#                 bohrium_job_type = st.selectbox('Bohrium Job Type', job_options, disabled=is_access_from_labs, index=index, help="The environment in which the job runs, currently supports containers and vm",
#                                                 key=f'{session_prefix}-{sub_model}-{version and version.name}-bohrium-jobtype')

#                 params[step].update({
#                     '__SYSTEM_SUBMIT_BOHRIUM_MACHINE_TYPE__': basic_machine_type or bohrium_machine_type if is_access_from_labs else bohrium_machine_type,
#                     '__SYSTEM_SUBMIT_BOHRIUM_PLATFORM__': basic_platform or bohrium_platform if is_access_from_labs else bohrium_platform,
#                     '__SYSTEM_SUBMIT_BOHRIUM_JOB_TYPE__': basic_job_type or bohrium_job_type if is_access_from_labs else bohrium_job_type
#                 })

#                 if len(schemas[step]) > 3:
#                     includes_bohrium_options(schemas[step]) and st.markdown('##### Dflow Options')
#                     is_access_from_labs and includes_bohrium_options(
#                         schemas[step],
#                         lambda item, _, format: print(item) or isinstance(item, dict) and item.update({
#                             'readOnly': True,
#                             'default': borhium_dflow_info.get(format.replace('bohrium_', ''), item.get('default', None)) if borhium_dflow_info else item.get('default', None)
#                         })
#                     )
                        
#             if step != 0:
#                 params[step].update(pydantic_input_by_schema(
#                     f'{session_prefix}-{step}-{sub_model}-{version and version.name}', schemas[step], schema_references, required_properties, **kwargs))
#             else: # step == 0
#                 mac_notify_shown = False
#                 for key, schema in schemas[step].items():
#                     if schema.get('format') == 'input_file_path' or (schema.get('type') == 'array' and schema.get('items', {}).get('format') == 'input_file_path'):
#                         if key in params[step] and params[step][key]:
#                             if schema.get('description') and schema.get('description_type', None) == 'markdown':
#                                 st.markdown(schema['title'])
#                                 st.markdown(schema['description'])
#                             else:
#                                 st.markdown(schema['title'] + (f" ```({schema.get('description')})```" if schema.get("description") else ""))

#                             b, a = st.columns([1, 20])
#                             tmp_res = params[step][key]
#                             if isinstance(tmp_res, list):

#                                 for item in tmp_res:
#                                     a.write(item.name if isinstance(item, Path) else (
#                                         item['name'] if isinstance(item, dict) else item))
#                             elif isinstance(tmp_res, Path):
#                                 a.write(tmp_res.name)
#                             elif isinstance(tmp_res, dict):
#                                 a.write(
#                                     tmp_res["name"] if "name" in tmp_res else "can not get file name.")
#                             if b.button(f'X', key=f'{session_prefix}-reset-{step}-{key}', type='secondary'):
#                                 del params[step][key]
#                                 st.experimental_rerun()

#                         else:
#                             if schema.get('description') and schema.get('description_type', None) == 'markdown':
#                                 st.markdown(schema['title'])
#                                 st.markdown(schema['description'])
#                             else:
#                                 st.markdown(schema['title'] + (f" ```({schema.get('description')})```" if schema.get("description") else ""))

#                             tab_event = st_antd_tabs([{'Label': 'Upload from local'}, {
#                                                      'Label': 'Choose from workspace'}], key=f'{session_prefix}-tabs-{step}-{key}')
#                             if tab_event and tab_event['Label'] == 'Choose from workspace':
#                                 root, event = choose_from_workspace(
#                                     key,
#                                     schema.get('ftypes', schema.get(
#                                         'items', {}).get('ftypes'))
#                                 )
#                                 if event and event['type'] == 'CHOOSE_FILE':
#                                     if schema['type'] == 'array':
#                                         input_data = {
#                                             key: [root / i['path'] for i in event['target']]}
#                                     else:
#                                         input_data = {key:
#                                                       root / event['target'][0]['path']}
#                                     params[step].update(input_data)
#                                     st.experimental_rerun()
#                             else:
#                                 from copy import deepcopy
#                                 schema = deepcopy(schema)
#                                 schema['title'] = None
#                                 schema["st_kwargs_on_change"] = lambda: params[step].pop(
#                                     key, None)
#                                 x = pydantic_input_by_schema(
#                                     f'{session_prefix}-{step}-{key}-{sub_model}-{version and version.name}',  {key: schema}, schema_references, required_properties, **kwargs)
#                                 if x[key]:
#                                     params[step].update({key: x[key]})
#                         if schema.get('format') == 'input_file_path':
#                             already_preview = False
#                             pockets = None
#                             for _key, _schema in schemas[step].items():
#                                 if _schema.get('format') == 'select_pocket' or (_schema.get('type') == 'array' and _schema.get('items', {}).get('format') == 'select_pocket'):
#                                     if _schema['ref'] != key:
#                                         continue
#                                     multi_select = _schema.get('type') == 'array'
#                                     if params[step].get(_schema['ref']):
#                                         ref_protein = params[step][_schema['ref']]
#                                         from streamlit_molstar.pocket import (
#                                             _get_file_type,
#                                             get_pockets_from_local_protein,
#                                             get_pockets_from_protein_content)
#                                         if not already_preview:
#                                             already_preview = True
#                                             if isinstance(ref_protein, Path):
#                                                 pockets = get_pockets_from_local_protein(str(ref_protein), key=f'{session_prefix}-{step}-{_key}')
#                                             else:
#                                                 pockets = get_pockets_from_protein_content(ref_protein['content'], _get_file_type(ref_protein['name']), key=f'{session_prefix}-{step}-{_key}')
#                                         if pockets:
#                                             if schema.get('description') and schema.get('description_type', None) == 'markdown':
#                                                 st.markdown(schema['title'])
#                                                 st.markdown(schema['description'])
#                                             else:
#                                                 st.markdown(schema['title'] + (
#                                                     f" ```({schema.get('description')})```" if schema.get("description") else ""))

#                                             if multi_select:
#                                                 selected_pockets = st.multiselect('Choose Pockets', pockets.keys(), format_func=lambda x: f"{x} | {pockets[x]}", key=f'{session_prefix}-{step}-{_key}-select-box')
#                                                 selected = [pockets[i] for i in selected_pockets]
#                                             else:
#                                                 selected_pocket = st.selectbox('Choose Pocket', pockets.keys(), format_func=lambda x: f"{x} | {pockets[x]}", key=f'{session_prefix}-{step}-{_key}-select-box')
#                                                 selected = pockets[selected_pocket]
#                                             params[step][_key] = selected
#                         from dp.launching.server.utils.session import \
#                             is_on_mac_chrome
#                         if is_on_mac_chrome() and not mac_notify_shown:
#                             mac_notify_shown = True
#                             with st.expander('Fail to open a file selection dialog?'):
#                                 st.markdown("""
# The upload button may fail to open a system dialog due to some Mac Chrome bug. There are three possible solutions:

# - Drag the file to upload
# - Upgrade Chrome to the latest version
# - Go to System Preferences > Security & Privacy > Privacy Tab > Full Disk Access > Press the lock symbol to unlock [bottom right of window]> Select Chrome and add it > Now restart Chrome.

# We found that the latest version of the Mac OS system has shrunk permissions. By default, no application has disk access permissions, and non-new versions of Chrome have not fixed this. Check [this issue](https://support.google.com/chrome/thread/134852610/since-latest-mac-os-can-no-longer-upload-any-files-in-chrome?hl=en) or [this video](https://www.youtube.com/watch?v=tbCcpcgdsso) for more detail.
# """)

#                     elif schema.get('format') == 'select_pocket' or (schema.get('type') == 'array' and schema.get('items', {}).get('format') == 'select_pocket'):
#                         pass
#                     elif schema.get('format') == 'datasets_select' or (schema.get('type') == 'array' and schema.get('items', {}).get('format') == 'datasets_select'):
#                         from dp.launching.server.common.components.streamlit_datahub_select import \
#                             st_datahub_select
#                         params[step].update(
#                             pydantic_input_by_schema(
#                                 f'{session_prefix}-{step}-{key}-{sub_model}-{version and version.name}', {key: schema}, schema_references, required_properties, **kwargs)
#                         )
#                     elif schema.get('format') == 'models_select' or (schema.get('type') == 'array' and schema.get('items', {}).get('format') == 'models_select'):
#                         from dp.launching.server.common.components.streamlit_datahub_select import \
#                             st_datahub_select
                        
#                         params[step].update(
#                             pydantic_input_by_schema(
#                                 f'{session_prefix}-{step}-{key}-{sub_model}-{version and version.name}', {key: schema}, schema_references, required_properties, **kwargs)
#                         )
#                     else:
#                         params[step].update(
#                             pydantic_input_by_schema(
#                                 f'{session_prefix}-{step}-{key}-{sub_model}-{version and version.name}', {key: schema}, schema_references, required_properties, **kwargs)
#                         )
#                     st.markdown('<br/>', unsafe_allow_html=True)
#                 st.markdown("""
#                     <style>
#                     div.stButton > button[kind="secondary"] {
#                     background: none!important;
#                     border: none;
#                     padding: 0!important;
#                     /*optional*/
#                     font-family: arial, sans-serif;
#                     /*input has OS specific font-family*/
#                     color: red;
#                     text-decoration: none;
#                     cursor: pointer;
#                     }
#                     </style>""", unsafe_allow_html=True)
#             required_ok = True
#             missing_keys = set()
#             ignore_format_keys = ('output_command_directory', 'output_directory', 'output_command_script')
#             for key, schema in schemas[step].items():
#                 if schema.get('scope') == 'executor':
#                     continue
#                 if key in params[step] and params[step][key] and "max_file_count" in schema:
#                     tmp_res = params[step][key]
#                     if isinstance(tmp_res, list) and len(tmp_res) > schema["max_file_count"]:
#                         st.error("Too many files uploaded in {}: {} files beyound {}".format(schema["title"], len(tmp_res),
#                                                                                           schema["max_file_count"]))
#                         ok_next = False
#                 if key in required_properties and (
#                     params[step].get(key) is None or
#                     params[step].get(key) == '' or
#                     params[step].get(key) == [] or
#                     params[step].get(key) == {}
#                 ):
#                     if (schemas[step].get(key) is not None and 'format' in schemas[step][key] and schemas[step][key]['format'] in ignore_format_keys):
#                         continue
#                     required_ok = False
#                     missing_keys.add(key)
#             if missing_keys:
#                 st.error(f'Required options: {", ".join(missing_keys)}')

#             return ok_next and required_ok
#         else:
#             def get_input_file_names(k, v):
#                 if not v:
#                     return ''
#                 schema = saved_schema_properties[k]
#                 if schema.get('format') == 'input_file_path':
#                     return v['name'] if isinstance(v, dict) else os.path.basename(str(v))
#                 return ', '.join(i['name'] if isinstance(i, dict) else os.path.basename(str(i)) for i in v)

#             data = [
#                 {
#                     'Index': i,
#                     'Step': {0: 'IO', 1: 'Job', 2: 'System'}[i],
#                     'Name': k,
#                     'Type': saved_schema_properties.get(k, {}).get('format', saved_schema_properties.get(k, {}).get('type', 'string')),
#                     'Configured Value': str(get_input_file_names(k, v) if i == 0 else v),
#                     'Default Value': str(saved_schema_properties.get(k, {}).get('default', 'No Default Value')),
#                     'Description': saved_schema_properties.get(k, {}).get('description', ''),
#                 } for i in params for k, v in params[i].items() if saved_schema_properties.get(k, {}).get('format') != 'output_directory' and invisible_fn(k, v)
#             ]

#             data = sorted(data, key=lambda x: (
#                 x['Index'], x['Step'], x['Name']), reverse=True)

#             df = pd.DataFrame(data)
#             st_antd_table(df, color_backgroud='#f9f6f1',
#                           hidden_columns=['Index'])
#         router.set_request_state('__INTERNAL_BOHRIUM_MACHINES_DUMPS_TYPE__', None)
#         return True
    
#     container = st.container()
#     ok_next = render_step(router.get_request_state('current_step', 0))
    
#     description = ''
#     debug_timeout = 0
#     debug_mode = False
#     job_prefix = ''
#     select_project_id = None
#     if router.get_request_state('current_step', 0) == len(items) - 1:
#         job_prefix = st.text_input('Job Prefix', value='',  key=f'{session_prefix}-job-prefix')
#         if job_prefix:
#             if len(job_prefix) > 20:
#                 ok_next = False
#                 st.error(f'Prefix should not longer than {20} chars')
#             elif not re.search(r'^(?=.{1,255}$)(?!-)[A-Za-z0-9\-]{1,63}(\.[A-Za-z0-9\-]{1,63})*\.?(?<!-)$', job_prefix) or re.search(r'[A-Z]', job_prefix):
#                 ok_next = False
#                 st.error('Prefix should conform to domain type and cannot contain uppercase.')

#         application = kwargs.get("application")
#         if application and application.properties.get("compulsory_owner_billing", False) or st.session_state.login_type in (LoginType.ANONYMOUS.value, LoginType.EPHEMERAL.value):
#             ...
#         # 非owner强制付费，并且是Bohrium用户登陆，才能选择project id和debug mode
#         elif st.session_state.login_type in (LoginType.BOHRIUM.value, LoginType.SSO.value):
#             from dp.launching.server.utils.bohrium import (
#                 get_bohrium_projects, get_bohrium_token)
#             from dp.launching.server.utils.security import decrypt

#             user = UserManager.get_user(st.session_state.user.email)
#             if not user or not user.encrypted_bohrium_password:
#                 st.error('Cannot find your bohrium password! Please re-login!')
#                 ok_next = False
                
#             token = get_bohrium_token(user.bohrium_username, decrypt(user.encrypted_bohrium_password))
#             if not token:
#                 st.error('Invalid email or password')
#                 ok_next = False

#             default_value = int(user.bohrium_project_id or 0)

#             projects = get_bohrium_projects(token)
#             if projects:
#                 project_ids = [p['id'] for p in projects]
#                 projects_d = {p['id']: p for p in projects}
#                 index = 0 if not default_value or default_value not in project_ids else project_ids.index(int(default_value))
#                 if st.checkbox('Show Balance', key=f'{session_prefix}-show-balance'):
#                     select_project_id = st.selectbox('Bohrium Project Id', project_ids, 
#                                                     format_func=lambda i: f'{projects_d[i]["name"]}(ID={projects_d[i]["id"]}, Creator={projects_d[i]["creatorEmail"]}, Remaining Budget={(projects_d[i]["costLimit"] - projects_d[i]["totalCost"]) / 100.0})',
#                                                     index=index, key='select_project_id')
#                 else:
#                     select_project_id = st.selectbox('Bohrium Project Id', project_ids, 
#                                                     format_func=lambda i: f'{projects_d[i]["name"]}(ID={projects_d[i]["id"]})',
#                                                     index=index, key='select_project_id')

#                 if (
#                     projects_d[select_project_id]["costLimit"] != 0 and \
#                     projects_d[select_project_id]["costLimit"] - projects_d[select_project_id]["userCost"] <= 0
#                 ):
#                     st.error("Insufficient account balance, please recharge.")
#                     ok_next = False
#             else:
#                 if projects is None:
#                     st.error('Invalid email or password')
#                 elif not projects:
#                     st.error('Bohrium account has no available projects configured, please ensure that there is at least one project.')
#                 ok_next = False

#             # debug mode
#             if not access_from_labs():
#                 debug_mode = st.checkbox('Debug mode', key=f'{session_prefix}-job-enable-debug')
#                 if debug_mode:
#                     debug_timeout = st.number_input('Debug timeout in Seconds', min_value=5*60, max_value=60*60*12, value=15*60, key=f'{session_prefix}-job-timeout')

#         description = st.text_area('Job Description (Optional)', key=f'{session_prefix}-job-desc', value=schemas_description)
#     prev_btn, next_btn = st.columns(2)
#     done = False

#     application = kwargs["application"] if "application" in kwargs else None

#     if st.session_state.login_type in (LoginType.ANONYMOUS.value, LoginType.EPHEMERAL.value):
#         if not application or not application.owner:
#             st.error(f"Unknown application({application.name}) or application's owner!({application.owner})")
#             ok_next = False
            
#         payment_user = UserManager.get_user(application.owner)
#         if payment_user is None or (not payment_user.encrypted_bohrium_password) or (not payment_user.bohrium_username) or (not application.bohrium_project_id_default):
#             st.error("Cannot find the owner's bohrium account!")
#             ok_next = False
#     elif st.session_state.login_type in (LoginType.BOHRIUM.value, LoginType.SSO.value):
#         payment_user = UserManager.get_user(st.session_state.user.email)
#         if payment_user is None or (not payment_user.encrypted_bohrium_password) or (not payment_user.bohrium_username):
#             st.error("Cannot find your bohrium account! Please re-login!")
#             ok_next = False
#     else:
#         st.error(f'Unknown login type: {st.session_state.login_type}')

#     if router.get_request_state('current_step', 0) < len(items) - 1:
#         if next_btn.button("Next", type="primary", disabled=not ok_next, use_container_width=True):
#             router.set_request_state('current_step', router.get_request_state('current_step', 0) + 1)
#             st.experimental_rerun()
#     elif router.get_request_state('current_step', 0) == len(items) - 1:
#         if access_from_labs():
#             from dp.launching.server.models import QuotaGateKeeper
#             gate = QuotaGateKeeper(st.session_state.login_type, application, st.session_state.user)
#             if gate.check():
#                 done = next_btn.button("Submit", type="primary", disabled=(not ok_next), use_container_width=True)
#                 if done:
#                     gate.add()
#             else:
#                 done = next_btn.button("Submit", type="primary", disabled=True, use_container_width=True)
#                 st.error("Quota exceed.")
#         else:
#             done = next_btn.button("Submit", type="primary", disabled=not ok_next, use_container_width=True)
#     if router.get_request_state('current_step', 0) > 0:
#         if prev_btn.button("Prev", use_container_width=True):
#             router.set_request_state('current_step', router.get_request_state('current_step', 0) - 1)
#             router.delete_request_state("show_result")
#             st.experimental_rerun()
#     with container:
#         st_antd_steps(items, router.get_request_state('current_step', 0), key=f"{session_prefix}-form-steps")

#     if done:
#         form = {}
#         for data in router.get_request_state('main_submit_form', {}).values():
#             form.update(data)
        
#         tmp_form = {}
#         for k, v in form.items():
#             invisible_fn(k, v) and tmp_form.update({ k: v })
#         form = tmp_form
#     else:
#         form = {}

#     more_options = {
#         'debug_mode': debug_mode,
#         'debug_timeout': debug_timeout,
#         'job_prefix': job_prefix,
#         'bohrium_project_id': str(select_project_id),
#     }
#     return form, description, more_options, done


# # Define generic type to allow autocompletion for the model fields
# T = TypeVar("T", bound=BaseModel)


# def pydantic_form(
#     key: str,
#     model: Type[T],
#     submit_label: str = "Submit",
#     clear_on_submit: bool = False,
#     group_optional_fields: GroupOptionalFieldsStrategy = "no",  # type: ignore
#     lowercase_labels: bool = False,
#     ignore_empty_values: bool = False,
#     **kwargs,
# ) -> Optional[T]:
#     """Auto-generates a Streamlit form based on the given (Pydantic-based) input class.

#     Args:
#         key (str): A string that identifies the form. Each form must have its own key.
#         model (Type[BaseModel]): The input model. Either a class or instance based on Pydantic `BaseModel` or Python `dataclass`.
#         submit_label (str): A short label explaining to the user what this button is for. Defaults to “Submit”.
#         clear_on_submit (bool): If True, all widgets inside the form will be reset to their default values after the user presses the Submit button. Defaults to False.
#         group_optional_fields (str, optional): If `sidebar`, optional input elements will be rendered on the sidebar.
#             If `expander`,  optional input elements will be rendered inside an expander element. Defaults to `no`.
#         lowercase_labels (bool): If `True`, all input element labels will be lowercased. Defaults to `False`.
#         ignore_empty_values (bool): If `True`, empty values for strings and numbers will not be stored in the session state. Defaults to `False`.

#     Returns:
#         Optional[BaseModel]: An instance of the given input class,
#             if the submit button is used and the input data passes the Pydantic validation.
#     """

#     with st.form(key=key, clear_on_submit=clear_on_submit):
#         input_state = pydantic_input(
#             key,
#             model,
#             group_optional_fields=group_optional_fields,
#             lowercase_labels=lowercase_labels,
#             ignore_empty_values=ignore_empty_values,
#             **kwargs,
#         )
#         submit_button = st.form_submit_button(label=submit_label)

#         if submit_button:
#             try:
#                 return parse_obj_as(model, input_state)
#             except ValidationError as ex:
#                 error_text = "**Whoops! There were some problems with your input:**"
#                 for error in ex.errors():
#                     if "loc" in error and "msg" in error:
#                         location = ".".join(error["loc"]).replace(
#                             "__root__.", "")  # type: ignore
#                         error_msg = f"**{location}:** " + error["msg"]
#                         error_text += "\n\n" + error_msg
#                     else:
#                         # Fallback
#                         error_text += "\n\n" + str(error)
#                 st.error(error_text)
#                 return None
#     return None


# def pydantic_form_by_schema(
#     key: str,
#     schema_properties: dict,
#     schema_references: dict,
#     required_properties: list,
#     submit_label: str = "Submit",
#     clear_on_submit: bool = False,
#     group_optional_fields: GroupOptionalFieldsStrategy = "no",  # type: ignore
#     lowercase_labels: bool = False,
#     ignore_empty_values: bool = False,
#     **kwargs,
# ) -> Optional[T]:
#     """Auto-generates a Streamlit form based on the given (Pydantic-based) input class.

#     Args:
#         key (str): A string that identifies the form. Each form must have its own key.
#         model (Type[BaseModel]): The input model. Either a class or instance based on Pydantic `BaseModel` or Python `dataclass`.
#         submit_label (str): A short label explaining to the user what this button is for. Defaults to “Submit”.
#         clear_on_submit (bool): If True, all widgets inside the form will be reset to their default values after the user presses the Submit button. Defaults to False.
#         group_optional_fields (str, optional): If `sidebar`, optional input elements will be rendered on the sidebar.
#             If `expander`,  optional input elements will be rendered inside an expander element. Defaults to `no`.
#         lowercase_labels (bool): If `True`, all input element labels will be lowercased. Defaults to `False`.
#         ignore_empty_values (bool): If `True`, empty values for strings and numbers will not be stored in the session state. Defaults to `False`.

#     Returns:
#         Optional[BaseModel]: An instance of the given input class,
#             if the submit button is used and the input data passes the Pydantic validation.
#     """

#     with st.form(key=key, clear_on_submit=clear_on_submit):
#         input_state = pydantic_input_by_schema(
#             key,
#             schema_properties,
#             schema_references,
#             required_properties,
#             group_optional_fields=group_optional_fields,
#             lowercase_labels=lowercase_labels,
#             ignore_empty_values=ignore_empty_values,
#             **kwargs,
#         )
#         submit_button = st.form_submit_button(label=submit_label)

#         if submit_button:
#             return input_state
#     return None
